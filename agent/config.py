"""Configuration management for the underwriting JIRA orchestrator."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    openai_api_key: str
    openai_model: str = "gpt-4.1"
    openai_temperature: float = 0.2
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""
    log_level: str = "INFO"
    request_timeout_seconds: float = 20.0
    retry_attempts: int = 3

    @staticmethod
    def from_env() -> "Settings":
        """Create settings from environment values."""
        return Settings(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            openai_temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
            jira_base_url=os.getenv("JIRA_BASE_URL", ""),
            jira_email=os.getenv("JIRA_EMAIL", ""),
            jira_api_token=os.getenv("JIRA_API_TOKEN", ""),
            jira_project_key=os.getenv("JIRA_PROJECT_KEY", ""),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
        )

    def validate_for_runtime(self) -> None:
        """Validate critical runtime settings."""
        required = {
            "OPENAI_API_KEY": self.openai_api_key,
            "JIRA_BASE_URL": self.jira_base_url,
            "JIRA_EMAIL": self.jira_email,
            "JIRA_API_TOKEN": self.jira_api_token,
            "JIRA_PROJECT_KEY": self.jira_project_key,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
