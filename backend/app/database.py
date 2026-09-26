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
                created_at TEXT NOT NULL,
                org_id TEXT
            )""")

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
                created_at TEXT NOT NULL,
                killed_at TEXT
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                contact_id TEXT,
                variant_id TEXT,
                event_type TEXT NOT NULL,
                raw_payload TEXT DEFAULT '{}',
                sentiment TEXT,
                created_at TEXT NOT NULL
            )""")

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
                "created_at": r["created_at"],
                "org_id": r["org_id"]
            }

    async def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cid = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        icp = json.dumps(data.get("icp_filters", {}))
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                "INSERT INTO campaigns (id, name, status, icp_filters, created_at, org_id) VALUES (?, ?, ?, ?, ?, ?)",
                (cid, data["name"], data.get("status", "draft"), icp, created_at, data.get("org_id"))
            )
            await db.commit()
        return await self.get_campaign(cid)

    async def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("UPDATE campaigns SET status = ? WHERE id = ?", (status, campaign_id))
            await db.commit()
            return True

    # --- CONTACTS ---
    async def get_contacts(self, campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            if campaign_id:
                cursor = await db.execute("SELECT * FROM contacts WHERE campaign_id = ? ORDER BY intent_score DESC", (campaign_id,))
            else:
                cursor = await db.execute("SELECT * FROM contacts ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [{
                "id": r["id"],
                "campaign_id": r["campaign_id"],
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
                "created_at": r["created_at"],
                "killed_at": r["killed_at"]
            }

    async def create_variant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        vid = data.get("id") or str(uuid.uuid4())
        created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(
                """INSERT INTO variants 
                (id, campaign_id, channel, subject, body_template, status, sends_count, opens_count, replies_count, positive_replies_count, meetings_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (vid, data["campaign_id"], data.get("channel", "email"), data["subject"], data["body_template"],
                 data.get("status", "active"), data.get("sends_count", 0), data.get("opens_count", 0),
                 data.get("replies_count", 0), data.get("positive_replies_count", 0), data.get("meetings_count", 0), created_at)
            )
            await db.commit()
        data["id"] = vid
        return data

    async def increment_variant_metric(self, variant_id: str, metric: str, amount: int = 1):
        allowed_metrics = ["sends_count", "opens_count", "replies_count", "positive_replies_count", "meetings_count"]
        if metric not in allowed_metrics:
            return
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute(f"UPDATE variants SET {metric} = {metric} + ? WHERE id = ?", (amount, variant_id))
            await db.commit()

    async def kill_variant(self, variant_id: str):
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_FILE, timeout=30.0) as db:
            await db.execute("UPDATE variants SET status = 'killed', killed_at = ? WHERE id = ?", (now, variant_id))
            await db.commit()

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

db = Database()
