import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.config import settings
from app.llm.prompts import (
    VARIANT_GENERATION_SYSTEM_PROMPT,
    SENTIMENT_CLASSIFIER_PROMPT,
    REPLY_DRAFT_PROMPT
)

logger = logging.getLogger("llm_client")

class LLMClient:
    """
    OpenAI-compatible LLM Client.
    Defaults to Groq's OpenAI-compatible endpoint for fast latency.
    Can be seamlessly swapped via LLM_BASE_URL, LLM_API_KEY, LLM_MODEL in .env.
    
    NOTE: If switching to Anthropic native Messages API, an adapter wrapper
    is required to map messages and system prompts to Anthropic's schema.
    """

    def __init__(self):
        self.base_url = settings.LLM_BASE_URL
        self.api_key = settings.LLM_API_KEY or "dummy_key_for_sandbox"
        self.model = settings.LLM_MODEL
        self.has_real_key = bool(settings.LLM_API_KEY and settings.LLM_API_KEY != "your_groq_api_key_here")

        if self.has_real_key:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        else:
            self.client = None

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Raw chat completion call through OpenAI-compatible interface."""
        if not self.has_real_key or self.client is None:
            return self._mock_generate(messages)

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"[LLMClient] API error ({e}), utilizing intelligent local fallback.")
            return self._mock_generate(messages)

    def generate_variants(self, icp_filters: Dict[str, Any], reference_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates 2 contrasting email variants (Angle A: Pain Point, Angle B: ROI/Metrics)."""
        ref_text = "\n\n".join([
            f"Reference Example #{i+1}:\nSubject: {r.get('subject')}\nBody:\n{r.get('body')}\nNotes: {r.get('style_notes', '')}"
            for i, r in enumerate(reference_emails[:3])
        ])

        user_content = f"""Target ICP Filters:
{json.dumps(icp_filters, indent=2)}

Reference Examples to model after:
{ref_text if ref_text else 'None provided, use best B2B cold email practices.'}

Generate Variant A and Variant B in JSON."""

        messages = [
            {"role": "system", "content": VARIANT_GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        raw = self.generate(messages, temperature=0.7)
        try:
            clean_json = raw.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            return json.loads(clean_json)
        except Exception as e:
            logger.warning(f"[LLMClient] JSON parse error in generate_variants ({e}), using default variants.")
            return self._default_variants(icp_filters)

    def classify_sentiment(self, email_text: str) -> Dict[str, Any]:
        """Classifies incoming prospect reply into positive, neutral, or negative."""
        messages = [
            {"role": "system", "content": SENTIMENT_CLASSIFIER_PROMPT},
            {"role": "user", "content": f"Analyze this prospect reply:\n\n\"{email_text}\""}
        ]
        raw = self.generate(messages, temperature=0.2)
        try:
            clean_json = raw.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            return json.loads(clean_json)
        except Exception:
            # Fallback heuristic
            lower = email_text.lower()
            if any(w in lower for w in ["unsubscribe", "remove", "stop", "not interested", "spam", "no thanks", "dont contact"]):
                return {"sentiment": "negative", "confidence": 0.98, "reasoning": "Prospect requested removal or declined.", "suggested_action": "opt_out"}
            elif any(w in lower for w in ["demo", "interested", "call", "thursday", "friday", "meet", "time", "pricing"]):
                return {"sentiment": "positive", "confidence": 0.95, "reasoning": "Prospect requested demo or meeting slot.", "suggested_action": "schedule_demo"}
            return {"sentiment": "neutral", "confidence": 0.75, "reasoning": "General inquiry or deferral.", "suggested_action": "route_to_colleague"}

    def draft_reply(self, original_pitch: str, prospect_reply: str, prospect_name: str, company: str) -> str:
        """Drafts a contextual response to an interested prospect."""
        prompt = REPLY_DRAFT_PROMPT.format(
            prospect_name=prospect_name,
            company=company,
            prospect_reply=prospect_reply
        )
        messages = [
            {"role": "user", "content": prompt}
        ]
        return self.generate(messages, temperature=0.5).strip()

    def generate_evolution_variant(
        self,
        winner_variant: Dict[str, Any],
        reference_emails: List[Dict[str, Any]],
        icp_filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates Variant C (Evolution mutation) based on the winning variant's 
        successful hooks and campaign's selected reference emails.
        """
        ref_text = "\n\n".join([
            f"Reference Example #{i+1}:\nSubject: {r.get('subject')}\nBody:\n{r.get('body')}\nNotes: {r.get('style_notes', '')}"
            for i, r in enumerate(reference_emails[:3])
        ])

        user_content = f"""The following email variant WON our initial outbound round with proven positive replies:
Winner Subject: {winner_variant.get('subject')}
Winner Body:
{winner_variant.get('body_template')}
Performance Score: {winner_variant.get('score', 0.0)} ({winner_variant.get('positive_replies_count', 0)} positive replies)

Target ICP Filters:
{json.dumps(icp_filters, indent=2)}

Style Reference Examples:
{ref_text if ref_text else 'None provided, follow winning pitch style.'}

Task: Formulate Variant C (Evolution). Retain the winning core hook and value proposition, but introduce a sharper urgency angle or social proof contrast to challenge the champion variant.
Return strictly valid JSON with keys "subject", "body_template", and "evolution_rationale"."""

        messages = [
            {"role": "system", "content": "You are an elite B2B sales copywriter specializing in self-healing outbound evolution. Output ONLY JSON."},
            {"role": "user", "content": user_content}
        ]

        raw = self.generate(messages, temperature=0.7)
        try:
            clean_json = raw.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            parsed = json.loads(clean_json)
            if "subject" in parsed and "body_template" in parsed:
                return parsed
        except Exception:
            pass

        return {
            "subject": f"Quick follow-up for {{company}} — {winner_variant.get('subject', 'outbound deliverability')}",
            "body_template": winner_variant.get("body_template", "Hi {name},\n\nFollowing up on my previous note regarding outbound deliverability at {company}.\n\nBest,\nAlex"),
            "evolution_rationale": "Iterated on winning variant angles with concise social proof and low friction CTA."
        }

    def _default_variants(self, icp_filters: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "variant_a": {
                "subject": "Quick question regarding outbound deliverability at {company}",
                "body_template": "Hi {name},\n\nSaw {company} is scaling revenue operations. Most sales leaders we speak with burn domains due to static sequence fatigue.\n\nWe built an autonomous self-healing agent that adjusts messaging based on real-time buyer signals.\n\nOpen to a 10-minute chat this Thursday at 2pm?\n\nBest,\nAlex",
                "angle": "pain_point_driven",
                "generation_reasoning": "Targeted acute SDR domain burning and sequence fatigue pain points."
            },
            "variant_b": {
                "subject": "3.2x booked meeting rate for {company}'s outbound",
                "body_template": "Hi {name},\n\nTeams targeting {title} roles typically see outbound reply rates hover below 2.8%.\n\nOur intent-driven self-healing engine reallocates traffic dynamically to winning variants, driving a 3.2x lift in qualified meetings booked.\n\nWorth a brief 5-minute glance this week?\n\nCheers,\nAlex",
                "angle": "roi_metric_driven",
                "generation_reasoning": "Emphasized quantitative 3.2x meeting booking rate lift and peer benchmark."
            }
        }

    def _mock_generate(self, messages: List[Dict[str, str]]) -> str:
        prompt_str = " ".join([m.get("content", "") for m in messages]).lower()
        user_content = messages[-1].get("content", "").lower() if messages else ""

        if "generate variant a and variant b" in prompt_str or "variant_generation_system_prompt" in prompt_str or "variant_a" in prompt_str:
            return json.dumps(self._default_variants({}))
        elif "analyze this prospect reply" in user_content or "sentiment" in prompt_str:
            if any(w in user_content for w in ["unsubscribe", "remove", "not interested", "stop", "spam", "no thanks"]):
                return json.dumps({
                    "sentiment": "negative",
                    "confidence": 0.98,
                    "reasoning": "Prospect requested removal or declined.",
                    "suggested_action": "opt_out"
                })
            return json.dumps({
                "sentiment": "positive",
                "confidence": 0.94,
                "reasoning": "Prospect confirmed interest in self-healing deliverability demo and provided a time slot.",
                "suggested_action": "schedule_demo"
            })
        elif "account executive crafting" in prompt_str or "reply" in prompt_str:
            return "Hi Sarah,\n\nThanks for following up! That's a familiar challenge—traditional sequences stay blind to domain reputation while burning prospects.\n\nThursday at 2:00 PM EST works smoothly on my end. I will send over a calendar invite with the demo link.\n\nLooking forward to speaking!\n\nBest,\nAlex"
        return "Acknowledged. Proceeding with campaign optimization."

llm_client = LLMClient()
