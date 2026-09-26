import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.database import db
from app.adapters.graph8_client import graph8_client
from app.services.sse_manager import sse_manager

logger = logging.getLogger("scheduler_service")

class SchedulerService:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def process_daily_batch(self, campaign_id: str) -> Dict[str, Any]:
        """
        Pushes the next daily quota of remaining 'new' prospects into the campaign's active sequence.
        Matches the Graph8 daily pacing and automated scheduler spec.
        """
        campaign = await db.get_campaign(campaign_id)
        if not campaign:
            return {"status": "error", "message": f"Campaign {campaign_id} not found"}

        if campaign.get("status") != "active":
            return {"status": "skipped", "message": f"Campaign is {campaign.get('status')}, batch not dispatched."}

        # Check if first-send approval is still pending (HITL Gate)
        approvals = await db.get_approvals("pending")
        camp_pending_approvals = [
            a for a in approvals 
            if a.get("type") in ("send_new_variant", "send_replacement_variant") 
            and a.get("payload", {}).get("campaign_id") == campaign_id
        ]
        if camp_pending_approvals:
            logger.info(f"[Scheduler] Campaign {campaign_id} has pending HITL approval. Waiting for human sign-off.")
            return {"status": "held", "message": "First send requires Human-in-the-Loop approval in Governance Queue."}

        daily_limit = campaign.get("daily_limit", 50)
        sent_today = campaign.get("sent_today", 0)

        # Get active variants
        variants = await db.get_variants(campaign_id)
        active_variants = [v for v in variants if v.get("status") == "active"]
        if not active_variants:
            return {"status": "error", "message": "No active variants configured for this campaign"}

        # Get pending prospects (status == 'new')
        all_contacts = await db.get_contacts(campaign_id)
        new_contacts = [c for c in all_contacts if c.get("status") == "new"]

        if not new_contacts:
            logger.info(f"[Scheduler] All discovered prospects for campaign {campaign_id} have already been enrolled!")
            decision = await db.create_decision({
                "campaign_id": campaign_id,
                "decision_type": "campaign_completed_all_prospects",
                "reasoning": f"All {len(all_contacts)} target prospects discovered for this campaign have completed daily enrollment into sequences.",
                "before_state": {"pending_prospects": 0},
                "after_state": {"all_enrolled": True},
                "requires_approval": False
            })
            await sse_manager.broadcast("agent_decision", decision)
            return {"status": "completed", "message": "All target prospects for this campaign are already enrolled."}

        # Take next daily batch
        batch = new_contacts[:daily_limit]
        enrolled_count = 0

        for i, contact in enumerate(batch):
            # Dynamic A/B allocation
            if len(active_variants) == 1:
                variant = active_variants[0]
            else:
                total_alloc = sum([v.get("allocation_percentage", 50.0) for v in active_variants]) or 100.0
                threshold = (active_variants[0].get("allocation_percentage", 50.0) / total_alloc) * 100.0
                bucket = (i * 37) % 100
                variant = active_variants[0] if bucket < threshold else active_variants[1]

            custom_subj = variant["subject"].replace("{company}", contact.get("company", "your company")).replace("{name}", contact.get("name", "there"))
            custom_body = variant["body_template"].replace("{company}", contact.get("company", "your company")).replace("{name}", contact.get("name", "there")).replace("{title}", contact.get("title", "leader"))

            # 1. Sync prospect to Graph8 audience with tags
            await graph8_client.sync_prospect({
                "id": contact["id"],
                "email": contact.get("email"),
                "name": contact.get("name"),
                "company": contact.get("company"),
                "title": contact.get("title"),
                "tags": ["Daily-Dashboard-Sync", f"camp-{campaign_id[:8]}"],
                "status": "active"
            })

            # 2. Add contact to sequence
            await graph8_client.add_contacts_to_sequence("seq_auto_01", contact["id"], custom_subj, custom_body)

            # 3. Update status & increment metric
            await db.update_contact_status(contact["id"], "enrolled", step=1)
            await db.increment_variant_metric(variant["id"], "sends_count", 1)

            # 4. Log event
            event = await db.create_event({
                "campaign_id": campaign_id,
                "contact_id": contact["id"],
                "variant_id": variant["id"],
                "event_type": "sent",
                "raw_payload": {"subject": custom_subj, "variant_id": variant["id"]}
            })
            await sse_manager.broadcast("new_event", event)
            enrolled_count += 1

        # Update campaign pacing
        await db.update_campaign_pacing(campaign_id, enrolled_count)

        remaining_count = len(new_contacts) - enrolled_count
        decision = await db.create_decision({
            "campaign_id": campaign_id,
            "decision_type": "daily_batch_dispatched",
            "reasoning": f"Pushed daily batch of {enrolled_count} prospects into sequence across active A/B variants. Remaining pending prospects: {remaining_count}.",
            "before_state": {"pending_before": len(new_contacts)},
            "after_state": {"enrolled_in_batch": enrolled_count, "remaining_pending": remaining_count},
            "requires_approval": False
        })

        await sse_manager.broadcast("agent_decision", decision)
        await sse_manager.broadcast("campaign_batch_dispatched", {
            "campaign_id": campaign_id,
            "enrolled_count": enrolled_count,
            "remaining_count": remaining_count
        })

        return {
            "status": "success",
            "enrolled_count": enrolled_count,
            "remaining_count": remaining_count,
            "daily_limit": daily_limit
        }

    async def start(self):
        """Starts the background scheduler loop for recurring daily pacing checks."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("[Scheduler] Daily pacing automated scheduler service started.")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _scheduler_loop(self):
        while self._running:
            try:
                campaigns = await db.get_campaigns()
                now = datetime.now(timezone.utc)

                for camp in campaigns:
                    if camp.get("status") != "active":
                        continue

                    last_run = camp.get("last_batch_run_at")
                    should_run = False
                    if not last_run:
                        # Never run yet, check if there are contacts
                        should_run = True
                    else:
                        try:
                            last_dt = datetime.fromisoformat(last_run)
                            # If more than 24 hours passed, reset daily quota and run batch
                            if (now - last_dt) >= timedelta(hours=24):
                                should_run = True
                        except Exception:
                            pass

                    if should_run:
                        await self.process_daily_batch(camp["id"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[SchedulerLoop] Error in cycle: {e}")

            # Sleep 60 seconds between liveness checks
            await asyncio.sleep(60)

scheduler_service = SchedulerService()
