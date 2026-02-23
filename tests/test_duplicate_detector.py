from agent.core.duplicate_detector import DuplicateDetector
from agent.schemas.models import DuplicateStatus, JiraIssueReference


class StubDetector(DuplicateDetector):
    def __init__(self) -> None:
        pass

    def _embed(self, text: str) -> list[float]:
        if "CAT referral" in text:
            return [1.0, 0.0, 0.0]
        if "CAT" in text:
            return [0.9, 0.1, 0.0]
        return [0.0, 1.0, 0.0]


def test_duplicate_detector_identifies_partial_overlap() -> None:
    detector = StubDetector()
    existing = [
        JiraIssueReference(key="UW-1", summary="CAT referral threshold", description="Model trigger tuning"),
        JiraIssueReference(key="UW-2", summary="Claims FNOL workflow", description="FNOL only"),
    ]

    analysis = detector.analyze("CAT referral rules update", existing)

    assert analysis.status in {
        DuplicateStatus.exact_duplicate,
        DuplicateStatus.partial_overlap,
        DuplicateStatus.related_dependency,
    }
    assert "UW-1" in analysis.related_issues
