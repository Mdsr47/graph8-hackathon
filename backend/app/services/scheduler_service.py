import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.database import db
from app.adapters.graph8_client import graph8_client
from app.services.sse_manager import sse_manager

logger = logging.getLogger("scheduler_service")

def allocate_prospect_to_variant(active_variants: List[Dict[str, Any]], current_counts: Dict[str, int]) -> Dict[str, Any]:
    """
    Deterministically allocates a prospect to the variant furthest behind its target quota.
    Ensures exact proportional distribution:
    - 50/50 on a batch of 7 produces exactly 4 and 3, and across 14 produces exactly 7 and 7.
    - 80/20 produces exactly 80% to Champion and 20% to Challenger.
    """
    if len(active_variants) == 1:
        return active_variants[0]

    total_assigned = sum(current_counts.get(v["id"], 0) for v in active_variants)
    total_weight = sum(v.get("allocation_percentage", 50.0) for v in active_variants) or 100.0

    best_variant = active_variants[0]
    max_deficit = -float("inf")

    for v in active_variants:
        target_pct = (v.get("allocation_percentage", 50.0) / total_weight)
        target_count = (total_assigned + 1) * target_pct
        current_count = current_counts.get(v["id"], 0)
        deficit = target_count - current_count
        if deficit > max_deficit:
            max_deficit = deficit
            best_variant = v

    return best_variant

class SchedulerService:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def process_daily_batch(self, campaign_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Pushes the next daily quota of remaining 'new' prospects into the campaign's active sequence.
        Strictly enforces daily_limit unless force=True (manual user trigger).
        Allocates variants using strict deterministic proportional balancing (no modulo hashing).
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

        # Enforce daily pacing limit
        if not force:
            quota_remaining = max(0, daily_limit - sent_today)
            if quota_remaining <= 0:
                logger.info(f"[Scheduler] Campaign {campaign_id} already reached daily limit of {daily_limit} today ({sent_today}/{daily_limit} sent).")
                return {
                    "status": "quota_reached",
                    "message": f"Daily limit of {daily_limit} already reached today ({sent_today}/{daily_limit} sent). Next batch runs tomorrow.",
                    "sent_today": sent_today,
                    "daily_limit": daily_limit
                }
            batch_size = quota_remaining
        else:
            batch_size = daily_limit

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

        # Take next daily batch up to batch_size
        batch = new_contacts[:batch_size]
        enrolled_count = 0

        # Maintain cumulative counts for exact proportional allocation
        current_counts = {v["id"]: v.get("sends_count", 0) for v in active_variants}

        for contact in batch:
            variant = allocate_prospect_to_variant(active_variants, current_counts)
            current_counts[variant["id"]] += 1

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
        new_sent_today = sent_today + enrolled_count

        decision = await db.create_decision({
            "campaign_id": campaign_id,
            "decision_type": "daily_batch_dispatched",
            "reasoning": f"Pushed daily batch of {enrolled_count} prospects into sequence across active A/B variants. Daily quota used: {new_sent_today}/{daily_limit}. Remaining pending prospects: {remaining_count}.",
            "before_state": {"pending_before": len(new_contacts), "sent_today_before": sent_today},
            "after_state": {"enrolled_in_batch": enrolled_count, "remaining_pending": remaining_count, "sent_today_after": new_sent_today},
            "requires_approval": False
        })

        await sse_manager.broadcast("agent_decision", decision)
        await sse_manager.broadcast("campaign_batch_dispatched", {
            "campaign_id": campaign_id,
            "enrolled_count": enrolled_count,
            "remaining_count": remaining_count,
            "sent_today": new_sent_today,
            "daily_limit": daily_limit
        })

        return {
            "status": "success",
            "enrolled_count": enrolled_count,
            "remaining_count": remaining_count,
            "sent_today": new_sent_today,
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
                    sent_today = camp.get("sent_today", 0)
                    should_run = False

                    if not last_run:
                        # Only run if no sends today and campaign has never been run
                        if sent_today == 0:
                            should_run = True
                    else:
                        try:
                            last_dt = datetime.fromisoformat(last_run)
                            # If 24 hours passed or calendar date has rolled over UTC
                            if (now - last_dt) >= timedelta(hours=24) or now.date() > last_dt.date():
                                # Reset sent_today for the new day
                                await db.reset_campaign_daily_pacing(camp["id"])
                                should_run = True
                        except Exception as e:
                            logger.warning(f"Error parsing last_batch_run_at: {e}")

                    if should_run:
                        await self.process_daily_batch(camp["id"], force=False)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[SchedulerLoop] Error in cycle: {e}")

            # Sleep 60 seconds between liveness checks
            await asyncio.sleep(60)

scheduler_service = SchedulerService()
