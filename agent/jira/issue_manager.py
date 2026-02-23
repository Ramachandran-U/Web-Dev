"""High-level JIRA issue management with explicit approval gating."""

from __future__ import annotations

import logging
from typing import Any

from agent.jira.jira_client import JiraClient
from agent.schemas.models import ApprovalDecision

logger = logging.getLogger(__name__)


class ApprovalRequiredError(RuntimeError):
    """Raised when mutation is attempted without explicit approval."""


class IssueManager:
    """Executes approved JIRA operations and logs proposed actions."""

    def __init__(self, jira_client: JiraClient, project_key: str) -> None:
        self.jira_client = jira_client
        self.project_key = project_key

    @staticmethod
    def _assert_approved(approval: ApprovalDecision | None) -> None:
        if not approval or not approval.approved:
            raise ApprovalRequiredError("Human approval required before JIRA mutation")

    def build_create_payload(self, summary: str, description: str, issue_type: str = "Story") -> dict[str, Any]:
        if not summary or not description:
            raise ValueError("Summary and description are required JIRA fields")
        return {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": issue_type},
            }
        }

    def create_issue(self, payload: dict[str, Any], approval: ApprovalDecision | None) -> dict[str, Any]:
        logger.info("Proposed create issue payload: %s", payload)
        self._assert_approved(approval)
        return self.jira_client.create_issue(payload)

    def update_issue(self, issue_key: str, payload: dict[str, Any], approval: ApprovalDecision | None) -> None:
        logger.info("Proposed update for %s: %s", issue_key, payload)
        self._assert_approved(approval)
        self.jira_client.update_issue(issue_key, payload)

    def set_priority(self, issue_key: str, priority_name: str, approval: ApprovalDecision | None) -> None:
        self.update_issue(issue_key, {"fields": {"priority": {"name": priority_name}}}, approval)

    def assign_issue(self, issue_key: str, account_id: str, approval: ApprovalDecision | None) -> None:
        logger.info("Proposed assignment for %s -> %s", issue_key, account_id)
        self._assert_approved(approval)
        self.jira_client.assign_issue(issue_key, account_id)

    def add_comment(self, issue_key: str, body: str, approval: ApprovalDecision | None) -> dict[str, Any]:
        logger.info("Proposed comment on %s: %s", issue_key, body)
        self._assert_approved(approval)
        return self.jira_client.add_comment(issue_key, body)

    def upload_attachment(self, issue_key: str, file_path: str, approval: ApprovalDecision | None) -> dict[str, Any]:
        logger.info("Proposed attachment upload on %s: %s", issue_key, file_path)
        self._assert_approved(approval)
        return self.jira_client.add_attachment(issue_key, file_path)

    def link_issues(
        self,
        inward_key: str,
        outward_key: str,
        link_type: str,
        approval: ApprovalDecision | None,
    ) -> None:
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key},
        }
        logger.info("Proposed issue link payload: %s", payload)
        self._assert_approved(approval)
        self.jira_client.create_issue_link(payload)
