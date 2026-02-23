"""Duplicate and related issue detection using semantic embeddings."""

from __future__ import annotations

import logging
import math
from typing import Iterable

from agent.schemas.models import DuplicateAnalysis, DuplicateStatus, JiraIssueReference

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Computes semantic similarity for issue deduplication decisions."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("openai package is required to use DuplicateDetector") from exc

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    @staticmethod
    def _cosine_similarity(v1: Iterable[float], v2: Iterable[float]) -> float:
        a = list(v1)
        b = list(v2)
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def analyze(self, candidate_text: str, existing_issues: list[JiraIssueReference]) -> DuplicateAnalysis:
        if not existing_issues:
            return DuplicateAnalysis(status=DuplicateStatus.no_match, related_issues=[])

        target_embedding = self._embed(candidate_text)
        scored: list[tuple[JiraIssueReference, float]] = []

        for issue in existing_issues:
            combined = f"{issue.summary}\n{issue.description}".strip()
            issue_embedding = self._embed(combined)
            similarity = self._cosine_similarity(target_embedding, issue_embedding)
            scored.append((issue, similarity))

        scored.sort(key=lambda item: item[1], reverse=True)
        top_issue, top_score = scored[0]
        logger.info("Top duplicate candidate %s with score %.4f", top_issue.key, top_score)

        if top_score >= 0.92:
            status = DuplicateStatus.exact_duplicate
        elif top_score >= 0.78:
            status = DuplicateStatus.partial_overlap
        elif top_score >= 0.6:
            status = DuplicateStatus.related_dependency
        else:
            status = DuplicateStatus.no_match

        related = [issue.key for issue, score in scored if score >= 0.6][:5]
        return DuplicateAnalysis(status=status, related_issues=related)
