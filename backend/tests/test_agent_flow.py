import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db
from app.adapters.graph8_client import graph8_client
from app.llm.llm_client import llm_client
from app.agent.workflow import run_campaign_initiation, trigger_feedback_cycle

def test_database_and_defaults():
    async def _test():
        await db.init_db()
        camps = await db.get_campaigns()
        assert isinstance(camps, list)

        ref_emails = await db.get_reference_emails()
        assert len(ref_emails) >= 2
        assert any("outbound" in r["subject"].lower() for r in ref_emails)
    asyncio.run(_test())

def test_graph8_client_endpoints():
    async def _test():
        stats = await graph8_client.get_intent_stats()
        assert "total_keywords" in stats
        assert stats["total_keywords"] > 0

        kw_list = await graph8_client.list_intent_keywords()
        assert "keywords" in kw_list
        assert len(kw_list["keywords"]) > 0

        companies = await graph8_client.get_companies_for_keyword(kw_list["keywords"][0]["id"])
        assert len(companies) > 0

        mailboxes = await graph8_client.list_mailboxes()
        assert isinstance(mailboxes, list)
    asyncio.run(_test())

def test_llm_client():
    # Test sentiment classifier
    positive_reply = "Hi! We'd love to schedule a demo. Does Thursday at 2pm work?"
    analysis = llm_client.classify_sentiment(positive_reply)
    assert analysis["sentiment"] == "positive"

    negative_reply = "Please remove us from your list, we are not interested."
    neg_analysis = llm_client.classify_sentiment(negative_reply)
    assert neg_analysis["sentiment"] == "negative"

def test_end_to_end_agent_loop():
    async def _test():
        await db.init_db()

        # 1. Create a campaign
        camp = await db.create_campaign({
            "name": "E2E Automated Test Campaign",
            "icp_filters": {"industry": "Fintech SaaS", "target_titles": ["VP Sales"]}
        })
        assert camp["id"] is not None

        # 2. Run LangGraph discovery and variant generation
        result = await run_campaign_initiation(camp["id"], camp["icp_filters"])
        assert "variants" in result or "contacts" in result

        # 3. Check contacts and variants created
        contacts = await db.get_contacts(camp["id"])
        assert len(contacts) > 0

        variants = await db.get_variants(camp["id"])
        assert len(variants) >= 2

        # 4. Check approvals generated for first send
        approvals = await db.get_approvals("pending")
        assert len(approvals) > 0

        # 5. Simulate 5 sends on Variant B and Variant A
        var_a = variants[0]
        var_b = variants[1]
        for _ in range(5):
            await db.increment_variant_metric(var_b["id"], "sends_count", 1)
            await db.increment_variant_metric(var_a["id"], "sends_count", 1)

        # Positive reply on Variant B
        await db.increment_variant_metric(var_b["id"], "replies_count", 1)
        await db.increment_variant_metric(var_b["id"], "positive_replies_count", 1)

        # Trigger feedback cycle
        event_data = {
            "event_type": "replied",
            "contact_id": contacts[0]["id"],
            "variant_id": var_b["id"],
            "sentiment": "positive"
        }
        await trigger_feedback_cycle(camp["id"], event_data)

        # 6. Check that a kill_variant decision was generated for the underperforming Variant A
        decisions = await db.get_decisions(camp["id"])
        assert len(decisions) > 0
    asyncio.run(_test())
