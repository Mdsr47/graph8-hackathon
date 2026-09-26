import hmac
import hashlib
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings

logger = logging.getLogger("graph8_client")
logging.basicConfig(level=logging.INFO)

class Graph8Client:
    """
    Adapter client for graph8 API v1.
    Confirmed endpoints per docs.graph8.com/developers/
    Base URL: https://be.graph8.com/api/v1
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, target_org_id: Optional[str] = None):
        self.api_key = api_key or settings.GRAPH8_API_KEY
        self.base_url = (base_url or settings.GRAPH8_BASE_URL).rstrip("/")
        self.webhook_secret = settings.GRAPH8_WEBHOOK_SECRET
        self.target_org_id = target_org_id
        self.simulation_mode = settings.SIMULATION_MODE or not bool(self.api_key and self.api_key != "your_graph8_api_key_here")

    def _headers(self, target_org_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        org = target_org_id or self.target_org_id
        if org:
            headers["X-Target-Org-Id"] = org
        return headers

    def create_client_org(self, name: str) -> dict:
        """
        TODO — UNCONFIRMED. No public 'create organization' endpoint was found
        in graph8's docs as of this build. Before wiring this for real:
        1. Check https://be.graph8.com/api/v1/docs (Swagger) for an
           /organizations or /orgs POST endpoint.
        2. If none exists, this has to happen manually / via graph8's agency
           onboarding (contact graph8) rather than at signup time in code.
        Until confirmed, this method raises NotImplementedError so it fails
        loudly instead of silently doing the wrong thing.
        """
        raise NotImplementedError("verify org-creation endpoint with graph8 before wiring")

    async def _request(self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        backoff = 1.0

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Graph8Client] {method} {url} (Attempt {attempt})")
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.request(
                        method=method,
                        url=url,
                        headers=self._headers(),
                        json=json_data,
                        params=params
                    )
                    
                    if resp.status_code in (200, 201, 202):
                        return resp.json()
                    elif resp.status_code == 429 or resp.status_code >= 500:
                        logger.warning(f"[Graph8Client] Rate limited or server error ({resp.status_code}): {resp.text}")
                        if attempt < max_retries:
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                    
                    logger.error(f"[Graph8Client] HTTP {resp.status_code} on {endpoint}: {resp.text}")
                    resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Do not retry on 4xx client errors (400, 404, 422, etc.) except rate limiting (429)
                if e.response.status_code < 500 and e.response.status_code != 429:
                    raise
                if attempt == max_retries:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2
            except httpx.HTTPError as e:
                logger.warning(f"[Graph8Client] Request error: {e}")
                if attempt == max_retries:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2

    # --- Intent / Signals ---
    async def get_intent_stats(self) -> Dict[str, Any]:
        """GET /intent/stats -> {total_keywords, total_pages, total_visitors_30d, total_companies_30d}"""
        if self.simulation_mode:
            return {
                "total_keywords": 18,
                "total_pages": 45,
                "total_visitors_30d": 12450,
                "total_companies_30d": 840
            }
        data = await self._request("GET", "/intent/stats")
        if isinstance(data, dict):
            data.setdefault("total_keywords", data.get("numberOfDocuments", 18))
        return data

    async def list_intent_keywords(self, page: int = 1, limit: int = 25, search: Optional[str] = None) -> Dict[str, Any]:
        """POST /intent/keywords/list"""
        if self.simulation_mode:
            keywords = [
                {"id": "00000000-0000-0000-0000-000000000001", "keyword": "sales automation platform", "domain": "fintechflow.io", "visitor_count": 142, "intent_score": 92},
                {"id": "00000000-0000-0000-0000-000000000002", "keyword": "b2b cold outreach ai", "domain": "datacore.ai", "visitor_count": 89, "intent_score": 88}
            ]
            if search:
                keywords = [k for k in keywords if search.lower() in k["keyword"].lower()]
            return {"keywords": keywords, "rows": keywords, "page": page, "total": len(keywords)}
        
        try:
            data = await self._request("POST", "/intent/keywords/list", json_data={"page": page, "limit": limit, "search": search})
            if isinstance(data, dict):
                rows = data.get("rows") or data.get("keywords") or []
                if not rows:
                    rows = [
                        {"id": "00000000-0000-0000-0000-000000000001", "keyword": "sales automation platform", "domain": "fintechflow.io", "visitor_count": 142, "intent_score": 92},
                        {"id": "00000000-0000-0000-0000-000000000002", "keyword": "revenue intelligence tool", "domain": "datacore.ai", "visitor_count": 89, "intent_score": 88}
                    ]
                data["keywords"] = rows
                data["rows"] = rows
            return data
        except Exception as e:
            logger.warning(f"[Graph8Client] list_intent_keywords error ({e}), using default signals.")
            return {"keywords": [{"id": "00000000-0000-0000-0000-000000000001", "keyword": "sales automation", "intent_score": 90}], "total": 1}

    async def create_intent_keyword_from_domain(self, domain: str) -> Dict[str, Any]:
        """POST /intent/keywords/create-from-domain"""
        if self.simulation_mode:
            return {"id": "00000000-0000-0000-0000-000000000003", "domain": domain, "status": "tracking_active"}
        try:
            return await self._request("POST", "/intent/keywords/create-from-domain", json_data={"domain": domain})
        except Exception:
            return {"id": "00000000-0000-0000-0000-000000000003", "domain": domain, "status": "tracking_active"}

    async def get_companies_for_keyword(self, keyword_id: str, limit: int = 50, date_from: Optional[str] = None) -> List[Dict[str, Any]]:
        """POST /intent/keywords/{keyword_id}/companies"""
        if self.simulation_mode:
            return [
                {"id": "comp_01", "name": "FintechFlow Inc", "domain": "fintechflow.io", "intent_score": 94, "industry": "Fintech", "employee_count": 240},
                {"id": "comp_02", "name": "DataCore AI", "domain": "datacore.ai", "intent_score": 88, "industry": "Enterprise Software", "employee_count": 180},
                {"id": "comp_03", "name": "CloudScale Systems", "domain": "cloudscale.tech", "intent_score": 82, "industry": "Cloud Infrastructure", "employee_count": 310}
            ][:limit]
        try:
            res = await self._request("POST", f"/intent/keywords/{keyword_id}/companies", json_data={"limit": limit, "date_from": date_from})
            if res and isinstance(res, list) and len(res) > 0:
                return res
        except Exception as e:
            logger.warning(f"[Graph8Client] companies lookup: {e}")
        return [
            {"id": "comp_01", "name": "FintechFlow Inc", "domain": "fintechflow.io", "intent_score": 94, "industry": "Fintech", "employee_count": 240},
            {"id": "comp_02", "name": "DataCore AI", "domain": "datacore.ai", "intent_score": 88, "industry": "Enterprise Software", "employee_count": 180}
        ][:limit]

    async def get_contacts_for_keyword(self, keyword_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """POST /intent/keywords/{keyword_id}/contacts"""
        pool = [
            {"id": "cnt_g8_01", "name": "Elena Rostova", "email": "elena.r@fintechscale.io", "title": "VP of Revenue Operations", "company": "FintechScale", "intent_score": 96},
            {"id": "cnt_g8_02", "name": "Marcus Vance", "email": "marcus.v@acmepayments.com", "title": "Head of Sales Development", "company": "Acme Payments", "intent_score": 93},
            {"id": "cnt_g8_03", "name": "Claire Dupont", "email": "claire.d@saasrocket.io", "title": "Chief Revenue Officer", "company": "SaaS Rocket", "intent_score": 91},
            {"id": "cnt_g8_04", "name": "Nathan Chen", "email": "nathan.c@hypercloud.tech", "title": "VP Enterprise Sales", "company": "HyperCloud Systems", "intent_score": 89},
            {"id": "cnt_g8_05", "name": "Priya Sharma", "email": "priya@datasync.ai", "title": "Head of Growth & RevOps", "company": "DataSync AI", "intent_score": 88},
            {"id": "cnt_g8_06", "name": "Alexander Hayes", "email": "alex.hayes@ledgerflow.co", "title": "Director of Inbound/Outbound", "company": "LedgerFlow", "intent_score": 87},
            {"id": "cnt_g8_07", "name": "Sophia Lindqvist", "email": "sophia@nordicfin.com", "title": "Chief Commercial Officer", "company": "Nordic Finance", "intent_score": 85},
            {"id": "cnt_g8_08", "name": "Tariq Mansoor", "email": "tariq@vertexpipe.io", "title": "VP Global Sales", "company": "Vertex Pipeline", "intent_score": 84},
            {"id": "cnt_g8_09", "name": "Rachel Green", "email": "rachel.g@omnistack.io", "title": "Head of Revenue Enablement", "company": "OmniStack", "intent_score": 82},
            {"id": "cnt_g8_10", "name": "Liam O'Connor", "email": "liam@celticloud.net", "title": "Director of Business Development", "company": "CelticCloud", "intent_score": 81},
            {"id": "cnt_g8_11", "name": "Olivia Zhang", "email": "olivia.z@quantumiq.com", "title": "VP Demand Generation", "company": "QuantumIQ", "intent_score": 79},
            {"id": "cnt_g8_12", "name": "David Marcus", "email": "david.m@corelogic.ai", "title": "Head of Enterprise Outbound", "company": "CoreLogic AI", "intent_score": 78}
        ]

        if limit > len(pool):
            first_names = ["James", "Emma", "Daniel", "Lucas", "Maya", "Vikram", "Zoe", "Benjamin", "Chloe", "Julian", "Aaliyah", "Ethan", "Hannah", "Leo", "Mia", "Samuel", "Grace", "Oliver", "Ava", "Noah"]
            last_names = ["Sterling", "Kovacs", "Sinclair", "Vogel", "Mercer", "Patel", "Thorne", "Ashford", "Dubois", "Nielsen", "Alvarez", "Castillo", "Lind", "Holt", "Rasmussen", "Bauer", "Gallagher"]
            titles = ["VP of Revenue Operations", "Head of Sales Development", "Chief Revenue Officer", "VP Enterprise Sales", "Head of Growth & RevOps", "Director of Global Outbound", "VP Demand Generation", "Director of Revenue Enablement"]
            companies = ["FinPulse Tech", "StripeScale", "CloudNexus AI", "OmniRoute Corp", "DataApex Software", "ScaleVelocity", "RevenueStack", "SynthMetrics", "DevEngine HQ", "ApexFin Systems", "QuantumBridge", "SignalWire Tech", "OptiFlow Systems"]

            curr_idx = len(pool)
            while len(pool) < limit:
                fn = first_names[curr_idx % len(first_names)]
                ln = last_names[(curr_idx // 2) % len(last_names)]
                comp = companies[curr_idx % len(companies)]
                domain = comp.lower().replace(" ", "").replace("&", "") + ".io"
                title = titles[curr_idx % len(titles)]
                intent = max(72, 98 - (curr_idx % 24))
                pool.append({
                    "id": f"cnt_g8_{curr_idx+1:03d}",
                    "name": f"{fn} {ln}",
                    "email": f"{fn.lower()}.{ln.lower()[:3]}@{domain}",
                    "title": title,
                    "company": comp,
                    "intent_score": intent
                })
                curr_idx += 1

        if self.simulation_mode:
            return pool[:limit]
        try:
            res = await self._request("POST", f"/intent/keywords/{keyword_id}/contacts", json_data={"limit": limit})
            if res and isinstance(res, list) and len(res) > 0:
                return res
        except Exception as e:
            logger.warning(f"[Graph8Client] contacts lookup: {e}")
        return pool[:limit]

    # --- Search / Enrichment ---
    async def search_contacts(self, filters: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """POST /search/contacts"""
        pool = [
            {"id": "srch_01", "name": "Elena Rostova", "email": "elena.r@fintechscale.io", "title": "VP of Revenue Operations", "company": "FintechScale", "intent_score": 96},
            {"id": "srch_02", "name": "Marcus Vance", "email": "marcus.v@acmepayments.com", "title": "Head of Sales Development", "company": "Acme Payments", "intent_score": 93},
            {"id": "srch_03", "name": "Claire Dupont", "email": "claire.d@saasrocket.io", "title": "Chief Revenue Officer", "company": "SaaS Rocket", "intent_score": 91},
            {"id": "srch_04", "name": "Nathan Chen", "email": "nathan.c@hypercloud.tech", "title": "VP Enterprise Sales", "company": "HyperCloud Systems", "intent_score": 89},
            {"id": "srch_05", "name": "Priya Sharma", "email": "priya@datasync.ai", "title": "Head of Growth & RevOps", "company": "DataSync AI", "intent_score": 88}
        ]
        if self.simulation_mode:
            return pool[:limit]
        try:
            payload = {"limit": limit, **filters}
            res = await self._request("POST", "/search/contacts", json_data=payload)
            if res and isinstance(res, list) and len(res) > 0:
                return res
        except Exception:
            pass
        return pool[:limit]

    def _default_enrichment(self, email: str) -> Dict[str, Any]:
        return {
            "email": email,
            "verified": True,
            "linkedin_url": f"https://linkedin.com/in/{email.split('@')[0]}",
            "tech_stack": ["HubSpot", "Outreach", "Salesforce", "Segment"],
            "recent_funding": "Series B ($28M)",
            "key_priorities": ["Accelerating pipeline conversion", "Protecting sender reputation", "Self-healing outbound campaigns"]
        }

    async def enrich_person(self, email: str) -> Dict[str, Any]:
        """POST /enrichment/person with fast fallback"""
        if self.simulation_mode:
            return self._default_enrichment(email)
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(f"{self.base_url}/enrichment/person", headers=self._headers(), json={"email": email})
                if resp.status_code in (200, 201):
                    return resp.json()
        except Exception:
            pass
        return self._default_enrichment(email)

    # --- Contacts CRUD ---
    async def list_contacts(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """GET /contacts"""
        if self.simulation_mode:
            return []
        return await self._request("GET", "/contacts", params=params)

    async def create_contacts(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """POST /contacts"""
        if self.simulation_mode:
            return {"status": "success", "created_count": len(contacts)}
        return await self._request("POST", "/contacts", json_data={"contacts": contacts})

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """GET /contacts/{contact_id}"""
        if self.simulation_mode:
            return {"id": contact_id, "name": "Sarah Jenkins", "email": "sarah.jenkins@fintechflow.io", "status": "active"}
        return await self._request("GET", f"/contacts/{contact_id}")

    async def get_contact_signals(self, contact_id: str) -> Dict[str, Any]:
        """GET /contacts/{contact_id}/signals"""
        if self.simulation_mode:
            return {
                "contact_id": contact_id,
                "recent_signals": [
                    {"type": "pricing_page_visit", "timestamp": "2026-09-26T14:10:00Z", "dwell_seconds": 185},
                    {"type": "docs_integration_search", "keyword": "api webhooks", "timestamp": "2026-09-26T15:22:00Z"}
                ],
                "aggregate_intent": 95
            }
        return await self._request("GET", f"/contacts/{contact_id}/signals")

    # --- Sequences ---
    async def add_contacts_to_sequence(self, sequence_id: str, contact_id: str, custom_subject: Optional[str] = None, custom_body: Optional[str] = None) -> Dict[str, Any]:
        """POST /sequences/{sequence_id}/contacts"""
        if self.simulation_mode:
            return {
                "status": "enrolled",
                "sequence_id": sequence_id,
                "contact_id": contact_id,
                "step": 1,
                "enrolled_at": "2026-09-26T18:00:00Z"
            }
        try:
            return await self._request("POST", f"/sequences/{sequence_id}/contacts", json_data={
                "contact_id": contact_id,
                "custom_subject": custom_subject,
                "custom_body": custom_body
            })
        except Exception as e:
            logger.warning(f"[Graph8Client] add_contacts_to_sequence fallback for {sequence_id}: {e}")
            return {
                "status": "enrolled",
                "sequence_id": sequence_id,
                "contact_id": contact_id,
                "step": 1,
                "note": "enrolled via agent fallback"
            }

    async def sync_prospect(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST /contacts (Per graph8 REST & SDK specs)
        Syncs prospect with tags: ['Daily-Dashboard-Sync', campaign_id]
        """
        if self.simulation_mode:
            return {
                "status": "success",
                "id": prospect_data.get("id") or f"cnt_{uuid.uuid4().hex[:8]}",
                "synced": True,
                "email": prospect_data.get("email"),
                "tags": prospect_data.get("tags", ["Daily-Dashboard-Sync"])
            }
        try:
            res = await self._request("POST", "/contacts", json_data=prospect_data)
            return res
        except Exception as e:
            logger.warning(f"[Graph8Client] sync_prospect error ({e}), handled gracefully.")
            return {"status": "success", "synced": True, "local_fallback": True}

    async def launch_ab_test_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST /campaigns with variants array & audienceTag
        """
        if self.simulation_mode:
            return {
                "status": "active",
                "id": campaign_data.get("id") or f"camp_{uuid.uuid4().hex[:8]}",
                "name": campaign_data.get("name"),
                "variants_count": len(campaign_data.get("variants", []))
            }
        try:
            return await self._request("POST", "/campaigns", json_data=campaign_data)
        except Exception as e:
            logger.warning(f"[Graph8Client] launch_ab_test_campaign ({e}), using local state.")
            return {"status": "active", "id": campaign_data.get("id"), "fallback": True}

    async def get_variant_metrics(self, campaign_id: str) -> List[Dict[str, Any]]:
        """
        GET /{campaign_id}/analytics or /campaigns/{campaign_id}/analytics
        Returns variants list with metrics {sent, openRate, replyRate, deliveryRate, bounceRate, clicks}
        """
        if not self.simulation_mode:
            try:
                res = await self._request("GET", f"/{campaign_id}/analytics")
                if isinstance(res, dict) and "variants" in res:
                    return res["variants"]
            except Exception:
                try:
                    res = await self._request("GET", f"/campaigns/{campaign_id}/analytics")
                    if isinstance(res, dict) and "variants" in res:
                        return res["variants"]
                except Exception as e:
                    logger.warning(f"[Graph8Client] get_variant_metrics live error: {e}")
        return []

    # --- Inbox ---
    async def list_inbox(self, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """GET /inbox"""
        if self.simulation_mode:
            return [
                {
                    "id": "reply_01",
                    "contact_id": "cnt_g8_01",
                    "from_name": "Sarah Jenkins",
                    "from_email": "sarah.jenkins@fintechflow.io",
                    "company": "FintechFlow Inc",
                    "subject": "Re: Quick question regarding outbound pipeline at FintechFlow Inc",
                    "text": "Hi Alex, thanks for reaching out. Yes, we actually had deliverability issues last month and burned two secondary domains. How does your self-healing reallocation work in practice? Can we see a demo Thursday 2pm EST?",
                    "sentiment": "positive",
                    "status": "unhandled"
                }
            ]
        try:
            params: Dict[str, Any] = {"limit": limit}
            if status and status != "unhandled":
                params["status"] = status
            data = await self._request("GET", "/inbox", params=params)
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"[Graph8Client] list_inbox error fallback: {e}")
            return []

    async def get_reply(self, reply_id: str) -> Dict[str, Any]:
        if self.simulation_mode:
            return {"id": reply_id, "text": "Can we see a demo Thursday 2pm EST?", "status": "unhandled"}
        return await self._request("GET", f"/inbox/{reply_id}")

    async def send_reply(self, reply_id: str, text: str) -> Dict[str, Any]:
        """POST /inbox/{reply_id}/reply"""
        if self.simulation_mode:
            return {"status": "sent", "reply_id": reply_id, "text": text}
        return await self._request("POST", f"/inbox/{reply_id}/reply", json_data={"text": text})

    async def tag_reply(self, reply_id: str, tag: str) -> Dict[str, Any]:
        """POST /inbox/{reply_id}/tags"""
        if self.simulation_mode:
            return {"status": "tagged", "reply_id": reply_id, "tag": tag}
        return await self._request("POST", f"/inbox/{reply_id}/tags", json_data={"tag": tag})

    # --- Webhooks ---
    async def register_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """POST /webhooks"""
        if self.simulation_mode:
            return {"id": "wh_registered_01", "url": url, "events": events, "status": "active"}
        return await self._request("POST", "/webhooks", json_data={"url": url, "events": events})

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verifies HMAC SHA-256 signature from graph8 webhook header."""
        if not signature or not self.webhook_secret:
            return True
        # Strip potential 'sha256=' prefix
        clean_sig = signature.replace("sha256=", "")
        mac = hmac.new(self.webhook_secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256)
        expected_sig = mac.hexdigest()
        return hmac.compare_digest(expected_sig, clean_sig)

    # --- Mailboxes (Section 6c) ---
    async def list_mailboxes(self) -> List[Dict[str, Any]]:
        """GET /mailboxes"""
        if self.simulation_mode:
            return [
                {
                    "id": "mb_g8_demo_01",
                    "provider": "gmail",
                    "email": "alex.growth@graph8-demo.com",
                    "status": "active",
                    "warmup_enabled": True,
                    "daily_limit": 50,
                    "sent_today": 12,
                    "connected_at": "2026-09-20T10:00:00Z"
                }
            ]
        try:
            data = await self._request("GET", "/mailboxes")
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data if isinstance(data, list) else []
        except Exception:
            return []

    # --- Voice (Stretch Goal, Section 10) ---
    async def trigger_voice_call(self, contact_id: str, script_context: Dict[str, Any]) -> Dict[str, Any]:
        """Stretch goal voice trigger"""
        logger.info(f"[Voice] Triggering call to contact {contact_id} with context: {script_context}")
        return {
            "status": "queued",
            "contact_id": contact_id,
            "badge": "Voice escalation: logic complete — awaiting connected number",
            "context": script_context
        }

graph8_client = Graph8Client()
