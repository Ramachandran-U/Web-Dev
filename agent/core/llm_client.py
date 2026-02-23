"""OpenAI interaction layer with strict structured JSON validation."""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from agent.schemas.models import ReasoningOutput

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are an expert Lloyd's London Property underwriting AI assistant. "
    "You understand syndicates, managing agents, delegated authority, coverholders, "
    "MRC structures, CAT modelling, referrals, endorsements, FNOL, and subscription market mechanics."
)

DEVELOPER_PROMPT = """
Return ONLY JSON. Follow this exact schema:
{
  "intent": "",
  "clarifying_questions": [],
  "assumptions": [],
  "duplicate_analysis": {
    "status": "Exact duplicate | Partial overlap | Related dependency | No match",
    "related_issues": []
  },
  "risk_level": "High | Medium | Low",
  "confidence_level": "High | Medium | Low",
  "reasoning_summary": "",
  "proposed_action": {
    "jira_operation": "",
    "fields_to_update": {},
    "status_recommendation": "",
    "links_to_create": []
  },
  "human_approval_required": true
}
Rules:
- Never claim certainty when underwriting details are incomplete.
- Always include explicit assumptions.
- Ask clarifying questions for missing underwriting data.
- Human approval must always be true for JIRA mutations.
""".strip()


class LLMClient:
    """Client for orchestrating LLM reasoning calls."""

    def __init__(self, api_key: str, model: str = "gpt-4.1", temperature: float = 0.2) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("openai package is required to use LLMClient") from exc

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def reason(self, user_prompt: str, context: dict[str, Any] | None = None) -> ReasoningOutput:
        """Generate and validate structured reasoning output."""
        context_blob = json.dumps(context or {}, indent=2)
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "developer", "content": DEVELOPER_PROMPT},
                {
                    "role": "user",
                    "content": f"Context:\n{context_blob}\n\nRequest:\n{user_prompt}",
                },
            ],
        )
        raw_content = response.choices[0].message.content or "{}"
        logger.debug("Raw model output: %s", raw_content)
        try:
            payload = json.loads(raw_content)
            validated = ReasoningOutput.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.exception("Failed to validate model output")
            raise ValueError("Model output validation failed") from exc
        return validated

    @staticmethod
    def example_prompt() -> dict[str, str]:
        """Return sample prompt details for docs/testing."""
        return {
            "system": SYSTEM_PROMPT,
            "developer": DEVELOPER_PROMPT,
            "user": (
                "Create a property underwriting story for adding CAT peril-specific referral thresholds "
                "for delegated authority business written via coverholders."
            ),
        }
