import os
import json
import uuid
import aiosqlite
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.config import settings

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "graph8_agent.db")

class Database:
    def __init__(self):
        self.supabase = None
        if settings.SUPABASE_URL and settings.SUPABASE_KEY and "your-project" not in settings.SUPABASE_URL:
            try:
                from supabase import create_client
                self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                print(f"[DB] Connected to Supabase at {settings.SUPABASE_URL}")
            except Exception as e:
                print(f"[DB] Failed to initialize Supabase ({e}), falling back to SQLite.")
                self.supabase = None

    async def init_db(self):
        """Initializes tables in SQLite for local development & fallback."""
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                icp_filters TEXT NOT NULL DEFAULT '{}',
                reference_email_ids TEXT NOT NULL DEFAULT '[]',
                daily_limit INTEGER DEFAULT 50,
                sent_today INTEGER DEFAULT 0,
                last_batch_run_at TEXT,
                created_at TEXT NOT NULL,
                org_id TEXT
            )""")

            # Safe schema migrations for campaigns & variants
            try:
                await db.execute("ALTER TABLE campaigns ADD COLUMN reference_email_ids TEXT NOT NULL DEFAULT '[]'")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE campaigns ADD COLUMN daily_limit INTEGER DEFAULT 50")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE campaigns ADD COLUMN target_contacts_limit INTEGER DEFAULT 50")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE campaigns ADD COLUMN sent_today INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE campaigns ADD COLUMN last_batch_run_at TEXT")
            except Exception:
                pass

            await db.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                graph8_contact_id TEXT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                title TEXT,
                company TEXT,
                intent_score INTEGER DEFAULT 0,
                current_step INTEGER DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'new',
                enriched_data TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS variants (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT 'email',
                subject TEXT NOT NULL,
                body_template TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                sends_count INTEGER DEFAULT 0,
                opens_count INTEGER DEFAULT 0,
                replies_count INTEGER DEFAULT 0,
                positive_replies_count INTEGER DEFAULT 0,
                meetings_count INTEGER DEFAULT 0,
                score REAL DEFAULT 0.0,
                allocation_percentage REAL DEFAULT 50.0,
                created_at TEXT NOT NULL,
                killed_at TEXT
            )""")

            try:
                await db.execute("ALTER TABLE variants ADD COLUMN score REAL DEFAULT 0.0")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE variants ADD COLUMN allocation_percentage REAL DEFAULT 50.0")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE variants ADD COLUMN bounces_count INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE variants ADD COLUMN clicks_count INTEGER DEFAULT 0")
            except Exception:
                pass

            await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                campaign_id TEXT,
                contact_id TEXT,
                variant_id TEXT,
                event_type TEXT NOT NULL,
                raw_payload TEXT DEFAULT '{}',
                sentiment TEXT,
                created_at TEXT NOT NULL
            )""")

            try:
                await db.execute("ALTER TABLE events ADD COLUMN campaign_id TEXT")
            except Exception:
                pass

            # Relational Indices for performance and structured querying
            await db.execute("CREATE INDEX IF NOT EXISTS idx_contacts_campaign ON contacts(campaign_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_variants_campaign ON variants(campaign_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_events_campaign ON events(campaign_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_events_contact ON events(contact_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_events_variant ON events(variant_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_decisions_campaign ON agent_decisions(campaign_id)")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                before_state TEXT DEFAULT '{}',
                after_state TEXT DEFAULT '{}',
                requires_approval INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                decision_id TEXT,
                type TEXT NOT NULL,
                payload TEXT DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                resolved_at TEXT
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS reference_emails (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                style_notes TEXT,
                created_at TEXT NOT NULL
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS mailbox_status (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL DEFAULT 'gmail',
                graph8_mailbox_id TEXT,
                connected_at TEXT,
                status TEXT NOT NULL DEFAULT 'active'
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS mailbox_settings (
                id TEXT PRIMARY KEY,
                provider TEXT DEFAULT 'gmail',
                smtp_host TEXT,
                smtp_port INTEGER DEFAULT 587,
                smtp_username TEXT,
                smtp_password TEXT,
                smtp_use_tls INTEGER DEFAULT 1,
                smtp_use_ssl INTEGER DEFAULT 0,
                imap_host TEXT,
                imap_port INTEGER DEFAULT 993,
                imap_username TEXT,
                imap_password TEXT,
                imap_use_ssl INTEGER DEFAULT 1,
                from_name TEXT,
                from_email TEXT,
                status TEXT DEFAULT 'disconnected',
                last_synced_at TEXT,
                updated_at TEXT
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS inbox_messages (
                id TEXT PRIMARY KEY,
                contact_id TEXT,
                contact_name TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                company TEXT,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                sentiment TEXT DEFAULT 'neutral',
                status TEXT DEFAULT 'unread',
                message_id TEXT,
                received_at TEXT NOT NULL,
                ai_draft_reply TEXT,
                created_at TEXT NOT NULL
            )""")

            await db.commit()

        # Seed initial defaults if needed
        await self._seed_defaults_if_empty()

    async def _seed_defaults_if_empty(self):
        emails = await self.get_reference_emails()
        if not emails:
            await self.create_reference_email({
                "subject": "Quick question regarding outbound pipeline at {company}",
                "body": "Hi {name},\n\nNoticed {company} is scaling revenue operations this quarter. Most sales leaders we talk to struggle with burning outbound domains on cold lists.\n\nWe built an autonomous self-healing agent that monitors buyer intent and auto-calibrates pitch angles in real-time.\n\nOpen to a brief 10-min peek this Thursday?\n\nBest,\nAlex",
                "style_notes": "Short, peer-to-peer tone, sharp pain point observation, low-friction ask."
            })
            await self.create_reference_email({
                "subject": "Solving intent drop-off for {company}",
                "body": "Hi {name},\n\nSaw high intent activity on {topic} from your team recently.\n\nTraditional sequences keep sending generic copy even after interest signals shift. Our self-healing engine dynamically rewires email variants based on open and sentiment telemetry.\n\nWould you be against seeing a 2-minute interactive demo?\n\nCheers,\nAlex",
                "style_notes": "Intent-driven hook, contrasting static sequences vs dynamic self-healing."
            })

        # Ensure mailbox record exists
        mb = await self.get_mailbox_status()
        if not mb:
            await self.set_mailbox_status({
                "provider": "gmail",
                "graph8_mailbox_id": "mb_g8_demo_01",
                "status": "active"
            })

    async def reset_db(self):
        """Wipes all transactional data and re-seeds fresh default reference emails."""
        if self.supabase:
            for tbl in ["events", "approvals", "agent_decisions", "variants", "contacts", "campaigns", "reference_emails", "mailbox_status"]:
                try:
                    self.supabase.table(tbl).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                except Exception:
                    pass
            await self._seed_defaults_if_empty()
            return

        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("DELETE FROM events")
            await db.execute("DELETE FROM approvals")
            await db.execute("DELETE FROM agent_decisions")
            await db.execute("DELETE FROM variants")
            await db.execute("DELETE FROM contacts")
            await db.execute("DELETE FROM campaigns")
            await db.execute("DELETE FROM reference_emails")
            await db.execute("DELETE FROM settings")
            await db.execute("DELETE FROM mailbox_status")
            await db.execute("DELETE FROM inbox_messages")
            await db.commit()
            await db.execute("VACUUM")
        await self._seed_defaults_if_empty()

    # --- CAMPAIGNS ---
    async def get_campaigns(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM campaigns ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "name": r["name"],
                "status": r["status"],
                "icp_filters": json.loads(r["icp_filters"] or "{}"),
                "reference_email_ids": json.loads(r["reference_email_ids"] or "[]") if "reference_email_ids" in r.keys() and r["reference_email_ids"] else [],
                "daily_limit": r["daily_limit"] if "daily_limit" in r.keys() else 50,
                "target_contacts_limit": r["target_contacts_limit"] if "target_contacts_limit" in r.keys() else 50,
                "sent_today": r["sent_today"] if "sent_today" in r.keys() else 0,
                "last_batch_run_at": r["last_batch_run_at"] if "last_batch_run_at" in r.keys() else None,
                "created_at": r["created_at"],
                "org_id": r["org_id"]
            } for r in rows]

    async def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            r = await cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "name": r["name"],
                "status": r["status"],
                "icp_filters": json.loads(r["icp_filters"] or "{}"),
                "reference_email_ids": json.loads(r["reference_email_ids"] or "[]") if "reference_email_ids" in r.keys() and r["reference_email_ids"] else [],
                "daily_limit": r["daily_limit"] if "daily_limit" in r.keys() else 50,
                "target_contacts_limit": r["target_contacts_limit"] if "target_contacts_limit" in r.keys() else 50,
                "sent_today": r["sent_today"] if "sent_today" in r.keys() else 0,
                "last_batch_run_at": r["last_batch_run_at"] if "last_batch_run_at" in r.keys() else None,
                "created_at": r["created_at"],
                "org_id": r["org_id"]
            }

    async def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cid = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        icp = json.dumps(data.get("icp_filters", {}))
        ref_ids = json.dumps(data.get("reference_email_ids", []))
        daily_lim = data.get("daily_limit", 50)
        target_contacts = data.get("target_contacts_limit", 50)
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                """INSERT INTO campaigns 
                (id, name, status, icp_filters, reference_email_ids, daily_limit, target_contacts_limit, sent_today, created_at, org_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cid, data["name"], data.get("status", "draft"), icp, ref_ids, daily_lim, target_contacts, 0, created_at, data.get("org_id"))
            )
            await db.commit()
        return await self.get_campaign(cid)

    async def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("UPDATE campaigns SET status = ? WHERE id = ?", (status, campaign_id))
            await db.commit()
            return True

    async def update_campaign_pacing(self, campaign_id: str, added_sends: int) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                "UPDATE campaigns SET sent_today = sent_today + ?, last_batch_run_at = ? WHERE id = ?",
                (added_sends, now, campaign_id)
            )
            await db.commit()
            return True

    # --- CONTACTS ---
    async def get_contacts(
        self,
        campaign_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT c.*, cmp.name as campaign_name 
                FROM contacts c
                LEFT JOIN campaigns cmp ON c.campaign_id = cmp.id
                WHERE 1=1
            """
            params = []
            if campaign_id:
                query += " AND c.campaign_id = ?"
                params.append(campaign_id)
            if status:
                query += " AND c.status = ?"
                params.append(status)
            if search:
                query += " AND (c.name LIKE ? OR c.email LIKE ? OR c.company LIKE ? OR c.title LIKE ?)"
                pattern = f"%{search}%"
                params.extend([pattern, pattern, pattern, pattern])

            query += " ORDER BY c.intent_score DESC, c.created_at DESC"
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "campaign_id": r["campaign_id"],
                "campaign_name": r["campaign_name"] or "Outbound Campaign",
                "graph8_contact_id": r["graph8_contact_id"],
                "name": r["name"],
                "email": r["email"],
                "title": r["title"],
                "company": r["company"],
                "intent_score": r["intent_score"],
                "current_step": r["current_step"],
                "status": r["status"],
                "enriched_data": json.loads(r["enriched_data"] or "{}"),
                "created_at": r["created_at"]
            } for r in rows]

    async def count_contacts(
        self,
        campaign_id: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            query = "SELECT COUNT(*) FROM contacts c WHERE 1=1"
            params = []
            if campaign_id:
                query += " AND c.campaign_id = ?"
                params.append(campaign_id)
            if status:
                query += " AND c.status = ?"
                params.append(status)
            if search:
                query += " AND (c.name LIKE ? OR c.email LIKE ? OR c.company LIKE ? OR c.title LIKE ?)"
                pattern = f"%{search}%"
                params.extend([pattern, pattern, pattern, pattern])
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def create_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cid = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        enriched = json.dumps(data.get("enriched_data", {}))
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                """INSERT INTO contacts 
                (id, campaign_id, graph8_contact_id, name, email, title, company, intent_score, current_step, status, enriched_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cid, data["campaign_id"], data.get("graph8_contact_id"), data["name"], data["email"],
                 data.get("title"), data.get("company"), data.get("intent_score", 0), data.get("current_step", 1),
                 data.get("status", "new"), enriched, created_at)
            )
            await db.commit()
        data["id"] = cid
        data["created_at"] = created_at
        return data

    async def update_contact_status(self, contact_id: str, status: str, step: Optional[int] = None):
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            if step is not None:
                await db.execute("UPDATE contacts SET status = ?, current_step = ? WHERE id = ?", (status, step, contact_id))
            else:
                await db.execute("UPDATE contacts SET status = ? WHERE id = ?", (status, contact_id))
            await db.commit()

    async def update_contact_enrichment(self, contact_id: str, enriched_data: Dict[str, Any]):
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                "UPDATE contacts SET enriched_data = ? WHERE id = ?",
                (json.dumps(enriched_data), contact_id)
            )
            await db.commit()

    # --- VARIANTS ---
    async def get_variants(self, campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            if campaign_id:
                cursor = await db.execute("SELECT * FROM variants WHERE campaign_id = ? ORDER BY created_at ASC", (campaign_id,))
            else:
                cursor = await db.execute("SELECT * FROM variants ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "campaign_id": r["campaign_id"],
                "channel": r["channel"],
                "subject": r["subject"],
                "body_template": r["body_template"],
                "status": r["status"],
                "sends_count": r["sends_count"],
                "opens_count": r["opens_count"],
                "replies_count": r["replies_count"],
                "positive_replies_count": r["positive_replies_count"],
                "meetings_count": r["meetings_count"],
                "bounces_count": r["bounces_count"] if "bounces_count" in r.keys() and r["bounces_count"] else 0,
                "clicks_count": r["clicks_count"] if "clicks_count" in r.keys() and r["clicks_count"] else 0,
                "score": r["score"] if "score" in r.keys() else 0.0,
                "allocation_percentage": r["allocation_percentage"] if "allocation_percentage" in r.keys() else 50.0,
                "created_at": r["created_at"],
                "killed_at": r["killed_at"]
            } for r in rows]

    async def get_variant(self, variant_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM variants WHERE id = ?", (variant_id,))
            r = await cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "campaign_id": r["campaign_id"],
                "channel": r["channel"],
                "subject": r["subject"],
                "body_template": r["body_template"],
                "status": r["status"],
                "sends_count": r["sends_count"],
                "opens_count": r["opens_count"],
                "replies_count": r["replies_count"],
                "positive_replies_count": r["positive_replies_count"],
                "meetings_count": r["meetings_count"],
                "bounces_count": r["bounces_count"] if "bounces_count" in r.keys() and r["bounces_count"] else 0,
                "clicks_count": r["clicks_count"] if "clicks_count" in r.keys() and r["clicks_count"] else 0,
                "score": r["score"] if "score" in r.keys() else 0.0,
                "allocation_percentage": r["allocation_percentage"] if "allocation_percentage" in r.keys() else 50.0,
                "created_at": r["created_at"],
                "killed_at": r["killed_at"]
            }

    async def create_variant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        vid = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        score = data.get("score", 0.0)
        alloc = data.get("allocation_percentage", 50.0)
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                """INSERT INTO variants 
                (id, campaign_id, channel, subject, body_template, status, sends_count, opens_count, replies_count, positive_replies_count, meetings_count, bounces_count, clicks_count, score, allocation_percentage, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (vid, data["campaign_id"], data.get("channel", "email"), data["subject"], data["body_template"],
                 data.get("status", "active"), data.get("sends_count", 0), data.get("opens_count", 0),
                 data.get("replies_count", 0), data.get("positive_replies_count", 0), data.get("meetings_count", 0),
                 data.get("bounces_count", 0), data.get("clicks_count", 0), score, alloc, created_at)
            )
            await db.commit()
        data["id"] = vid
        data["score"] = score
        data["allocation_percentage"] = alloc
        return data

    async def update_variant_reinforcement(self, variant_id: str, score: float, allocation_percentage: float):
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                "UPDATE variants SET score = ?, allocation_percentage = ? WHERE id = ?",
                (score, allocation_percentage, variant_id)
            )
            await db.commit()

    async def increment_variant_metric(self, variant_id: str, metric: str, amount: int = 1):
        allowed_metrics = ["sends_count", "opens_count", "replies_count", "positive_replies_count", "meetings_count", "bounces_count", "clicks_count"]
        if metric not in allowed_metrics:
            return
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(f"UPDATE variants SET {metric} = {metric} + ? WHERE id = ?", (amount, variant_id))
            await db.commit()

    async def update_variant(self, variant_id: str, status: Optional[str] = None, subject: Optional[str] = None, body_template: Optional[str] = None, allocation_percentage: Optional[float] = None):
        fields = []
        params = []
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if subject is not None:
            fields.append("subject = ?")
            params.append(subject)
        if body_template is not None:
            fields.append("body_template = ?")
            params.append(body_template)
        if allocation_percentage is not None:
            fields.append("allocation_percentage = ?")
            params.append(allocation_percentage)
        if not fields:
            return
        params.append(variant_id)
        query = f"UPDATE variants SET {', '.join(fields)} WHERE id = ?"
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(query, tuple(params))
            await db.commit()

    async def kill_variant(self, variant_id: str):
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("UPDATE variants SET status = 'killed', killed_at = ? WHERE id = ?", (now, variant_id))
            await db.commit()

    async def get_analytics_data(self, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """Provides full variant analytics, open/reply/bounce metrics, and intent breakdown."""
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row

            if campaign_id:
                c_cursor = await db.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            else:
                c_cursor = await db.execute("SELECT * FROM campaigns ORDER BY created_at DESC")
            camp_rows = await c_cursor.fetchall()

            if campaign_id:
                v_cursor = await db.execute(
                    "SELECT v.*, c.name as campaign_name FROM variants v LEFT JOIN campaigns c ON v.campaign_id = c.id WHERE v.campaign_id = ? ORDER BY v.created_at ASC",
                    (campaign_id,)
                )
            else:
                v_cursor = await db.execute(
                    "SELECT v.*, c.name as campaign_name FROM variants v LEFT JOIN campaigns c ON v.campaign_id = c.id ORDER BY v.created_at DESC"
                )
            var_rows = await v_cursor.fetchall()

            if campaign_id:
                cnt_cursor = await db.execute("SELECT intent_score, status FROM contacts WHERE campaign_id = ?", (campaign_id,))
            else:
                cnt_cursor = await db.execute("SELECT intent_score, status FROM contacts")
            contacts_data = await cnt_cursor.fetchall()

        variant_analytics = []
        tot_sends = 0
        tot_opens = 0
        tot_replies = 0
        tot_positive = 0
        tot_bounces = 0
        tot_clicks = 0
        tot_meetings = 0

        for r in var_rows:
            sends = r["sends_count"] or 0
            opens = r["opens_count"] or 0
            replies = r["replies_count"] or 0
            pos = r["positive_replies_count"] or 0
            bounces = r["bounces_count"] if "bounces_count" in r.keys() and r["bounces_count"] else 0
            clicks = r["clicks_count"] if "clicks_count" in r.keys() and r["clicks_count"] else 0
            meetings = r["meetings_count"] or 0

            delivered = max(0, sends - bounces)
            deliv_rate = round((delivered / sends) * 100, 1) if sends > 0 else 100.0
            open_rate = round((opens / sends) * 100, 1) if sends > 0 else 0.0
            reply_rate = round((replies / sends) * 100, 1) if sends > 0 else 0.0
            pos_rate = round((pos / sends) * 100, 1) if sends > 0 else 0.0
            bounce_rate = round((bounces / sends) * 100, 1) if sends > 0 else 0.0
            click_rate = round((clicks / sends) * 100, 1) if sends > 0 else 0.0

            tot_sends += sends
            tot_opens += opens
            tot_replies += replies
            tot_positive += pos
            tot_bounces += bounces
            tot_clicks += clicks
            tot_meetings += meetings

            variant_analytics.append({
                "variant_id": r["id"],
                "campaign_id": r["campaign_id"],
                "campaign_name": r["campaign_name"] or "Campaign",
                "channel": r["channel"],
                "subject": r["subject"],
                "body_template": r["body_template"],
                "status": r["status"],
                "score": r["score"] if "score" in r.keys() else 0.0,
                "allocation_percentage": r["allocation_percentage"] if "allocation_percentage" in r.keys() else 50.0,
                "metrics": {
                    "sent": sends,
                    "delivered": delivered,
                    "deliveryRate": deliv_rate,
                    "opens": opens,
                    "openRate": open_rate,
                    "clicks": clicks,
                    "clickRate": click_rate,
                    "replies": replies,
                    "replyRate": reply_rate,
                    "positiveReplies": pos,
                    "positiveReplyRate": pos_rate,
                    "bounces": bounces,
                    "bounceRate": bounce_rate,
                    "meetings": meetings
                }
            })

        intent_buckets = {"tier_1_hot": 0, "tier_2_warm": 0, "tier_3_mild": 0}
        for c in contacts_data:
            score = c["intent_score"] or 0
            if score >= 90:
                intent_buckets["tier_1_hot"] += 1
            elif score >= 80:
                intent_buckets["tier_2_warm"] += 1
            else:
                intent_buckets["tier_3_mild"] += 1

        overall_deliv = max(0, tot_sends - tot_bounces)
        return {
            "summary": {
                "total_sends": tot_sends,
                "total_delivered": overall_deliv,
                "delivery_rate": round((overall_deliv / tot_sends) * 100, 1) if tot_sends > 0 else 100.0,
                "total_opens": tot_opens,
                "open_rate": round((tot_opens / tot_sends) * 100, 1) if tot_sends > 0 else 0.0,
                "total_clicks": tot_clicks,
                "click_rate": round((tot_clicks / tot_sends) * 100, 1) if tot_sends > 0 else 0.0,
                "total_replies": tot_replies,
                "reply_rate": round((tot_replies / tot_sends) * 100, 1) if tot_sends > 0 else 0.0,
                "total_positive": tot_positive,
                "positive_reply_rate": round((tot_positive / tot_sends) * 100, 1) if tot_sends > 0 else 0.0,
                "total_bounces": tot_bounces,
                "bounce_rate": round((tot_bounces / tot_sends) * 100, 1) if tot_sends > 0 else 0.0,
                "total_meetings": tot_meetings,
                "total_prospects": len(contacts_data),
                "total_variants": len(variant_analytics)
            },
            "variants": variant_analytics,
            "intent_distribution": intent_buckets,
            "campaigns": [{
                "id": c["id"],
                "name": c["name"],
                "status": c["status"],
                "daily_limit": c["daily_limit"] if "daily_limit" in c.keys() else 50,
                "target_contacts_limit": c["target_contacts_limit"] if "target_contacts_limit" in c.keys() else 50,
                "sent_today": c["sent_today"] if "sent_today" in c.keys() else 0,
                "last_batch_run_at": c["last_batch_run_at"] if "last_batch_run_at" in c.keys() else None
            } for c in camp_rows]
        }

    # --- EVENTS ---
    async def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "contact_id": r["contact_id"],
                "variant_id": r["variant_id"],
                "event_type": r["event_type"],
                "raw_payload": json.loads(r["raw_payload"] or "{}"),
                "sentiment": r["sentiment"],
                "created_at": r["created_at"]
            } for r in rows]

    async def create_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        eid = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        payload = json.dumps(data.get("raw_payload", {}))
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                "INSERT INTO events (id, contact_id, variant_id, event_type, raw_payload, sentiment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (eid, data.get("contact_id"), data.get("variant_id"), data["event_type"], payload, data.get("sentiment"), created_at)
            )
            await db.commit()
        data["id"] = eid
        return data

    # --- AGENT DECISIONS ---
    async def get_decisions(self, campaign_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            if campaign_id:
                cursor = await db.execute("SELECT * FROM agent_decisions WHERE campaign_id = ? ORDER BY created_at DESC LIMIT ?", (campaign_id, limit))
            else:
                cursor = await db.execute("SELECT * FROM agent_decisions ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "campaign_id": r["campaign_id"],
                "decision_type": r["decision_type"],
                "reasoning": r["reasoning"],
                "before_state": json.loads(r["before_state"] or "{}"),
                "after_state": json.loads(r["after_state"] or "{}"),
                "requires_approval": bool(r["requires_approval"]),
                "created_at": r["created_at"]
            } for r in rows]

    async def create_decision(self, data: Dict[str, Any]) -> Dict[str, Any]:
        did = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        before_s = json.dumps(data.get("before_state", {}))
        after_s = json.dumps(data.get("after_state", {}))
        req_app = 1 if data.get("requires_approval") else 0
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                """INSERT INTO agent_decisions 
                (id, campaign_id, decision_type, reasoning, before_state, after_state, requires_approval, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (did, data["campaign_id"], data["decision_type"], data["reasoning"], before_s, after_s, req_app, created_at)
            )
            await db.commit()
        data["id"] = did
        return data

    # --- APPROVALS ---
    async def get_approvals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            if status:
                cursor = await db.execute("SELECT * FROM approvals WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cursor = await db.execute("SELECT * FROM approvals ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "decision_id": r["decision_id"],
                "type": r["type"],
                "payload": json.loads(r["payload"] or "{}"),
                "status": r["status"],
                "created_at": r["created_at"],
                "resolved_at": r["resolved_at"]
            } for r in rows]

    async def create_approval(self, data: Dict[str, Any]) -> Dict[str, Any]:
        aid = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        payload = json.dumps(data.get("payload", {}))
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                "INSERT INTO approvals (id, decision_id, type, payload, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (aid, data.get("decision_id"), data["type"], payload, data.get("status", "pending"), created_at)
            )
            await db.commit()
        data["id"] = aid
        return data

    async def resolve_approval(self, approval_id: str, status: str, edited_payload: Optional[Dict[str, Any]] = None) -> bool:
        resolved_at = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            if edited_payload is not None:
                await db.execute("UPDATE approvals SET status = ?, resolved_at = ?, payload = ? WHERE id = ?",
                                 (status, resolved_at, json.dumps(edited_payload), approval_id))
            else:
                await db.execute("UPDATE approvals SET status = ?, resolved_at = ? WHERE id = ?",
                                 (status, resolved_at, approval_id))
            await db.commit()
            return True

    # --- REFERENCE EMAILS ---
    async def get_reference_emails(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM reference_emails ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "subject": r["subject"],
                "body": r["body"],
                "style_notes": r["style_notes"],
                "created_at": r["created_at"]
            } for r in rows]

    async def create_reference_email(self, data: Dict[str, Any]) -> Dict[str, Any]:
        rid = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                "INSERT INTO reference_emails (id, subject, body, style_notes, created_at) VALUES (?, ?, ?, ?, ?)",
                (rid, data["subject"], data["body"], data.get("style_notes"), created_at)
            )
            await db.commit()
        data["id"] = rid
        return data

    async def delete_reference_email(self, email_id: str) -> bool:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("DELETE FROM reference_emails WHERE id = ?", (email_id,))
            await db.commit()
            return True

    # --- SETTINGS ---
    async def get_settings(self) -> Dict[str, str]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT key, value FROM settings")
            rows = await cursor.fetchall()
            return {r["key"]: r["value"] for r in rows}

    async def set_setting(self, key: str, value: str):
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
            await db.commit()

    # --- MAILBOX STATUS ---
    async def get_mailbox_status(self) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM mailbox_status LIMIT 1")
            r = await cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "provider": r["provider"],
                "graph8_mailbox_id": r["graph8_mailbox_id"],
                "connected_at": r["connected_at"],
                "status": r["status"]
            }

    async def set_mailbox_status(self, data: Dict[str, Any]):
        mid = data.get("id") or str(uuid.uuid4())
        connected_at = data.get("connected_at") or datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("DELETE FROM mailbox_status")
            await db.execute(
                "INSERT INTO mailbox_status (id, provider, graph8_mailbox_id, connected_at, status) VALUES (?, ?, ?, ?, ?)",
                (mid, data.get("provider", "gmail"), data.get("graph8_mailbox_id"), connected_at, data.get("status", "active"))
            )
            await db.commit()

    # --- MAILBOX SETTINGS (SMTP & IMAP) ---
    async def get_mailbox_settings(self) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM mailbox_settings LIMIT 1")
            r = await cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "provider": r["provider"],
                "smtp_host": r["smtp_host"],
                "smtp_port": r["smtp_port"],
                "smtp_username": r["smtp_username"],
                "smtp_password": r["smtp_password"],
                "smtp_use_tls": bool(r["smtp_use_tls"]),
                "smtp_use_ssl": bool(r["smtp_use_ssl"]),
                "imap_host": r["imap_host"],
                "imap_port": r["imap_port"],
                "imap_username": r["imap_username"],
                "imap_password": r["imap_password"],
                "imap_use_ssl": bool(r["imap_use_ssl"]),
                "from_name": r["from_name"],
                "from_email": r["from_email"],
                "status": r["status"],
                "last_synced_at": r["last_synced_at"],
                "updated_at": r["updated_at"]
            }

    async def save_mailbox_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        mid = "default_mailbox"
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("DELETE FROM mailbox_settings")
            await db.execute(
                """INSERT INTO mailbox_settings (
                    id, provider, smtp_host, smtp_port, smtp_username, smtp_password,
                    smtp_use_tls, smtp_use_ssl, imap_host, imap_port, imap_username, imap_password,
                    imap_use_ssl, from_name, from_email, status, last_synced_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    mid, data.get("provider", "gmail"),
                    data.get("smtp_host", "smtp.gmail.com"), int(data.get("smtp_port", 587)),
                    data.get("smtp_username", ""), data.get("smtp_password", ""),
                    1 if data.get("smtp_use_tls", True) else 0, 1 if data.get("smtp_use_ssl", False) else 0,
                    data.get("imap_host", "imap.gmail.com"), int(data.get("imap_port", 993)),
                    data.get("imap_username", ""), data.get("imap_password", ""),
                    1 if data.get("imap_use_ssl", True) else 0,
                    data.get("from_name", "RevOps Agent"), data.get("from_email", data.get("smtp_username", "")),
                    data.get("status", "connected"), now, now
                )
            )
            await db.commit()
        return await self.get_mailbox_settings()

    async def update_mailbox_sync(self, status: str, last_synced_at: str):
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                "UPDATE mailbox_settings SET status = ?, last_synced_at = ?",
                (status, last_synced_at)
            )
            await db.commit()

    # --- INBOX MESSAGES ---
    async def get_inbox_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM inbox_messages ORDER BY received_at DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "contact_id": r["contact_id"],
                "contact_name": r["contact_name"],
                "contact_email": r["contact_email"],
                "company": r["company"],
                "subject": r["subject"],
                "body": r["body"],
                "sentiment": r["sentiment"],
                "status": r["status"],
                "message_id": r["message_id"],
                "received_at": r["received_at"],
                "ai_draft_reply": r["ai_draft_reply"],
                "created_at": r["created_at"]
            } for r in rows]

    async def save_inbox_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        msg_id = data.get("message_id")
        now = datetime.now(timezone.utc).isoformat()
        mid = data.get("id") or str(uuid.uuid4())
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            if msg_id:
                cursor = await db.execute("SELECT id FROM inbox_messages WHERE message_id = ?", (msg_id,))
                existing = await cursor.fetchone()
                if existing:
                    return {"id": existing[0], "already_exists": True}

            await db.execute(
                """INSERT INTO inbox_messages (
                    id, contact_id, contact_name, contact_email, company, subject, body,
                    sentiment, status, message_id, received_at, ai_draft_reply, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    mid, data.get("contact_id"), data["contact_name"], data["contact_email"],
                    data.get("company", "Enterprise Account"), data["subject"], data["body"],
                    data.get("sentiment", "neutral"), data.get("status", "unread"),
                    msg_id, data.get("received_at", now), data.get("ai_draft_reply"), now
                )
            )
            await db.commit()
        data["id"] = mid
        return data

    async def update_inbox_message_draft(self, item_id: str, draft: str):
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("UPDATE inbox_messages SET ai_draft_reply = ? WHERE id = ?", (draft, item_id))
            await db.commit()

    async def update_inbox_message_status(self, item_id: str, status: str):
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("UPDATE inbox_messages SET status = ? WHERE id = ?", (status, item_id))
            await db.commit()

    # --- REAL OVERVIEW STATS ---
    async def get_overview_stats(self) -> Dict[str, Any]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            # 1. Total contacts
            c1 = await db.execute("SELECT COUNT(*) FROM contacts")
            total_contacts = (await c1.fetchone())[0]

            # 2. Variants aggregate sends, replies, positive, meetings
            c2 = await db.execute("""
                SELECT 
                    COALESCE(SUM(sends_count), 0),
                    COALESCE(SUM(replies_count), 0),
                    COALESCE(SUM(positive_replies_count), 0),
                    COALESCE(SUM(meetings_count), 0)
                FROM variants
            """)
            var_row = await c2.fetchone()
            total_sends = var_row[0]
            var_replies = var_row[1]
            var_pos = var_row[2]
            total_meetings = var_row[3]

            # 3. Real inbound replies from inbox_messages or events
            c3 = await db.execute("SELECT COUNT(*) FROM inbox_messages")
            inbox_count = (await c3.fetchone())[0]

            c4 = await db.execute("SELECT COUNT(*) FROM events WHERE event_type = 'replied'")
            replied_events = (await c4.fetchone())[0]

            c5 = await db.execute("SELECT COUNT(*) FROM inbox_messages WHERE sentiment = 'positive'")
            pos_inbox = (await c5.fetchone())[0]

            c6 = await db.execute("SELECT COUNT(*) FROM approvals WHERE status = 'pending'")
            pending_approvals = (await c6.fetchone())[0]

            total_replies = max(var_replies, inbox_count, replied_events)
            total_positive = max(var_pos, pos_inbox)

            return {
                "prospects_enriched": total_contacts,
                "outbound_sends": total_sends,
                "total_inbound_replies": total_replies,
                "positive_sentiment": total_positive,
                "meetings_booked": total_meetings,
                "pending_approvals": pending_approvals
            }

db = Database()
