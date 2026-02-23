"""Comment interpretation engine with dynamic status transition inference."""

from __future__ import annotations

import re
from collections import Counter

from agent.schemas.models import CommentClassification, CommentInterpretation


class CommentEngine:
    """Classifies comments and infers likely workflow movement."""

    _PATTERN_MAP: dict[CommentClassification, tuple[str, ...]] = {
        CommentClassification.approval: ("approved", "looks good", "proceed", "sign-off"),
        CommentClassification.rejection: ("rejected", "decline", "do not proceed", "not acceptable"),
        CommentClassification.clarification: ("clarify", "can you", "please confirm", "question"),
        CommentClassification.blocker: ("blocked", "dependency", "cannot continue", "waiting on"),
        CommentClassification.regulatory_escalation: (
            "regulator",
            "compliance",
            "conduct risk",
            "sanction",
            "regulatory",
        ),
        CommentClassification.informational: ("for information", "fyi", "note that", "heads up"),
    }

    _STATUS_HINT_PATTERN = re.compile(
        r"(?:move|set|change)\s+(?:the\s+)?status\s+(?:to\s+)?([A-Za-z][A-Za-z\s-]{2,40})",
        re.IGNORECASE,
    )

    def classify(self, comment_id: str, text: str) -> CommentInterpretation:
        lowered = text.lower()
        score_counter: Counter[CommentClassification] = Counter()

        for classification, patterns in self._PATTERN_MAP.items():
            for pattern in patterns:
                if pattern in lowered:
                    score_counter[classification] += 1

        if score_counter:
            classification = score_counter.most_common(1)[0][0]
            raw_score = score_counter[classification]
            confidence = min(0.55 + raw_score * 0.15, 0.95)
        else:
            classification = CommentClassification.informational
            confidence = 0.5

        inferred_transition = self.infer_status_transition(text)
        rationale = (
            f"Detected '{classification.value}' cues and inferred transition '{inferred_transition}'."
        )
        return CommentInterpretation(
            comment_id=comment_id,
            classification=classification,
            confidence=confidence,
            rationale=rationale,
            inferred_status_transition=inferred_transition,
        )

    def infer_status_transition(self, text: str) -> str:
        """Infer transition from status hints present in free-form text."""
        status_match = self._STATUS_HINT_PATTERN.search(text)
        if status_match:
            return status_match.group(1).strip().title()

        phrases = re.findall(r"\b(to|into)\s+([A-Za-z][A-Za-z\s-]{2,40})", text, re.IGNORECASE)
        if phrases:
            candidate = phrases[0][1].strip().title()
            if any(token in candidate.lower() for token in ("progress", "review", "approved", "blocked")):
                return candidate

        return "No explicit status transition found; human review required"
