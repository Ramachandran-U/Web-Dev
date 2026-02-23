"""Entry point for Lloyd's property underwriting JIRA orchestrator."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent.config import Settings
from agent.core.comment_engine import CommentEngine
from agent.core.duplicate_detector import DuplicateDetector
from agent.core.llm_client import LLMClient
from agent.core.risk_engine import RiskEngine
from agent.core.workflow_generator import WorkflowGenerator
from agent.jira.issue_manager import ApprovalRequiredError, IssueManager
from agent.jira.jira_client import JiraClient
from agent.schemas.models import ApprovalDecision, JiraIssueReference, JiraSearchPayload, UnderwritingRequest


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def build_example_payloads(project_key: str) -> dict[str, Any]:
    """Example JIRA REST payloads for operational documentation."""
    return {
        "create_issue": {
            "fields": {
                "project": {"key": project_key},
                "summary": "Add CAT referral controls for delegated authority property risks",
                "issuetype": {"name": "Story"},
            }
        },
        "update_issue": {"fields": {"priority": {"name": "High"}}},
        "add_comment": {"body": "Approved by underwriting committee; proceed to implementation."},
        "search_issues": JiraSearchPayload(
            jql=f'project = "{project_key}" AND text ~ "CAT referral"',
            maxResults=10,
        ).model_dump(),
    }


def mock_human_approval(reasoning_summary: str, approved: bool = False) -> ApprovalDecision:
    """Simulate explicit human approval event in non-interactive execution."""
    decision = ApprovalDecision(
        approved=approved,
        approver="underwriting.governance@example.com",
        reason=f"Auto-simulation for demo. Summary reviewed: {reasoning_summary[:120]}",
    )
    logging.getLogger(__name__).info("Approval simulation outcome: %s", decision.model_dump())
    return decision


def orchestrate(request: UnderwritingRequest, approve_mutations: bool = False) -> dict[str, Any]:
    settings = Settings.from_env()
    settings.validate_for_runtime()
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    llm = LLMClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
    )
    risk_engine = RiskEngine()
    workflow_generator = WorkflowGenerator()
    comment_engine = CommentEngine()

    jira_client = JiraClient(
        base_url=settings.jira_base_url,
        email=settings.jira_email,
        api_token=settings.jira_api_token,
        timeout=settings.request_timeout_seconds,
        retries=settings.retry_attempts,
    )
    issue_manager = IssueManager(jira_client=jira_client, project_key=settings.jira_project_key)
    duplicate_detector = DuplicateDetector(api_key=settings.openai_api_key)

    search_payload = JiraSearchPayload(
        jql=f'project = "{settings.jira_project_key}" AND text ~ "{request.summary}"',
        maxResults=25,
    ).model_dump()
    search_response = jira_client.search_issues(search_payload)
    existing_issues = [
        JiraIssueReference(
            key=item["key"],
            summary=item["fields"].get("summary", ""),
            description=(item["fields"].get("description") or ""),
            status=(item["fields"].get("status", {}) or {}).get("name", ""),
        )
        for item in search_response.get("issues", [])
    ]
    duplicate_analysis = duplicate_detector.analyze(
        candidate_text=f"{request.summary}\n{request.description}",
        existing_issues=existing_issues,
    )

    workflow = workflow_generator.generate(request.summary, request.business_context)

    reasoning_context = {
        "request": request.model_dump(),
        "duplicate_analysis": duplicate_analysis.model_dump(),
        "risk_engine_assessment": risk_engine.evaluate(request.description).value,
        "workflow_preview": workflow.model_dump(),
    }
    reasoning = llm.reason(
        user_prompt="Generate JIRA action plan for the underwriting request.",
        context=reasoning_context,
    )
    logger.info("Reasoning summary: %s", reasoning.reasoning_summary)

    approval = mock_human_approval(reasoning.reasoning_summary, approved=approve_mutations)

    mutation_result: dict[str, Any] = {"executed": False}
    try:
        if reasoning.proposed_action.jira_operation.lower() == "create_issue":
            create_payload = issue_manager.build_create_payload(
                summary=request.summary,
                description=(
                    f"{request.description}\n\nWorkflow:\n{workflow.workflow_text}\n\n"
                    f"Figma Prompt:\n{workflow.figma_prompt}"
                ),
            )
            issue = issue_manager.create_issue(create_payload, approval=approval)
            issue_key = issue.get("key", "")

            for attachment in request.attachments:
                issue_manager.upload_attachment(issue_key, attachment, approval=approval)

            mutation_result = {"executed": True, "operation": "create_issue", "issue": issue}
        elif reasoning.proposed_action.jira_operation.lower() == "update_issue":
            issue_key = reasoning.proposed_action.fields_to_update.get("issue_key", "")
            issue_manager.update_issue(issue_key, reasoning.proposed_action.fields_to_update, approval=approval)
            mutation_result = {"executed": True, "operation": "update_issue", "issue_key": issue_key}
        else:
            mutation_result = {
                "executed": False,
                "operation": reasoning.proposed_action.jira_operation,
                "message": "No supported mutation requested.",
            }
    except ApprovalRequiredError as exc:
        logger.warning("Execution paused pending approval: %s", exc)
        mutation_result = {"executed": False, "paused": True, "reason": str(exc)}

    comment_example = comment_engine.classify(
        comment_id="example-comment",
        text="Approved by delegated authority committee; move status to In Review after CAT validation.",
    )

    return {
        "reasoning": reasoning.model_dump(),
        "duplicate_analysis": duplicate_analysis.model_dump(),
        "workflow": workflow.model_dump(),
        "comment_interpretation_example": comment_example.model_dump(),
        "mutation_result": mutation_result,
        "api_payload_examples": build_example_payloads(settings.jira_project_key),
        "openai_prompt_example": llm.example_prompt(),
    }


if __name__ == "__main__":
    demo_request = UnderwritingRequest(
        summary="Implement CAT-driven referral threshold update for delegated authority property risks",
        description=(
            "Need to update underwriting workflow to enforce CAT model trigger points and referral "
            "rules for high-value binder submissions."
        ),
        requester="uw.ops@lloyds-market.example",
        business_context="Syndicate requests tighter accumulation controls for windstorm-exposed properties.",
        attachments=[],
    )
    result = orchestrate(demo_request, approve_mutations=False)
    print(json.dumps(result, indent=2))
