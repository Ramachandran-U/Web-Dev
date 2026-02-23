"""HTTP client wrapper around JIRA Cloud REST APIs."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests.auth import HTTPBasicAuth


logger = logging.getLogger(__name__)


class JiraClient:
    """Low-level JIRA REST client with retries and error handling."""

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        timeout: float = 20,
        retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.timeout = timeout
        self.retries = retries
        self._headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    auth=self.auth,
                    timeout=self.timeout,
                    headers=kwargs.pop("headers", self._headers),
                    **kwargs,
                )
                if response.status_code >= 500:
                    logger.warning("Transient JIRA error (%s): %s", response.status_code, response.text)
                    time.sleep(0.5 * attempt)
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("JIRA request attempt %s failed: %s", attempt, exc)
                time.sleep(0.5 * attempt)
        raise RuntimeError(f"JIRA request failed after retries: {last_error}")

    def create_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/rest/api/3/issue", json=payload).json()

    def update_issue(self, issue_key: str, payload: dict[str, Any]) -> None:
        self._request("PUT", f"/rest/api/3/issue/{issue_key}", json=payload)

    def assign_issue(self, issue_key: str, account_id: str) -> None:
        self._request("PUT", f"/rest/api/3/issue/{issue_key}/assignee", json={"accountId": account_id})

    def add_comment(self, issue_key: str, comment_body: str) -> dict[str, Any]:
        return self._request(
            "POST", f"/rest/api/3/issue/{issue_key}/comment", json={"body": comment_body}
        ).json()

    def search_issues(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/rest/api/3/search", json=payload).json()

    def get_comments(self, issue_key: str) -> dict[str, Any]:
        return self._request("GET", f"/rest/api/3/issue/{issue_key}/comment").json()

    def create_issue_link(self, payload: dict[str, Any]) -> None:
        self._request("POST", "/rest/api/3/issueLink", json=payload)

    def add_attachment(self, issue_key: str, file_path: str) -> dict[str, Any]:
        headers = {"Accept": "application/json", "X-Atlassian-Token": "no-check"}
        with open(file_path, "rb") as file_obj:
            files = {"file": file_obj}
            response = self._request(
                "POST",
                f"/rest/api/3/issue/{issue_key}/attachments",
                headers=headers,
                files=files,
            )
        return response.json()
