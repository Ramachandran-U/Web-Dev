"""Risk scoring logic for underwriting change requests."""

from __future__ import annotations

from agent.schemas.models import RiskLevel


class RiskEngine:
    """Evaluates risk level for proposed JIRA mutations."""

    HIGH_RISK_KEYWORDS = {
        "policy wording",
        "regulatory",
        "rating logic",
        "cross-team reassignment",
        "financial exposure",
    }
    MEDIUM_RISK_KEYWORDS = {
        "process change",
        "workflow",
        "assignment",
        "sla",
        "operational",
    }

    def evaluate(self, text: str) -> RiskLevel:
        normalized = text.lower()
        if any(keyword in normalized for keyword in self.HIGH_RISK_KEYWORDS):
            return RiskLevel.high
        if any(keyword in normalized for keyword in self.MEDIUM_RISK_KEYWORDS):
            return RiskLevel.medium
        return RiskLevel.low
