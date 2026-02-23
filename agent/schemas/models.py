"""Pydantic models for reasoning, governance, and JIRA payload contracts."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class ConfidenceLevel(str, Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class DuplicateStatus(str, Enum):
    exact_duplicate = "Exact duplicate"
    partial_overlap = "Partial overlap"
    related_dependency = "Related dependency"
    no_match = "No match"


class DuplicateAnalysis(BaseModel):
    status: DuplicateStatus
    related_issues: list[str] = Field(default_factory=list)


class ProposedAction(BaseModel):
    jira_operation: str
    fields_to_update: dict[str, Any] = Field(default_factory=dict)
    status_recommendation: str = ""
    links_to_create: list[dict[str, str]] = Field(default_factory=list)


class ReasoningOutput(BaseModel):
    intent: str
    clarifying_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    duplicate_analysis: DuplicateAnalysis
    risk_level: RiskLevel
    confidence_level: ConfidenceLevel
    reasoning_summary: str
    proposed_action: ProposedAction
    human_approval_required: bool = True


class UnderwritingRequest(BaseModel):
    summary: str
    description: str
    requester: str
    business_context: str
    policy_type: str = "Property"
    metadata: dict[str, Any] = Field(default_factory=dict)
    attachments: list[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    approved: bool
    approver: str
    reason: str = ""


class JiraIssueReference(BaseModel):
    key: str
    summary: str
    description: str = ""
    status: str = ""


class CommentClassification(str, Enum):
    approval = "Approval"
    rejection = "Rejection"
    clarification = "Clarification"
    blocker = "Blocker"
    regulatory_escalation = "Regulatory escalation"
    informational = "Informational"


class CommentInterpretation(BaseModel):
    comment_id: str
    classification: CommentClassification
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    inferred_status_transition: str


class WorkflowOutput(BaseModel):
    workflow_text: str
    figma_prompt: str
    swimlanes: list[str]
    decision_nodes: list[str]
    exception_paths: list[str]


class JiraCreateIssuePayload(BaseModel):
    fields: dict[str, Any]


class JiraUpdateIssuePayload(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)
    update: dict[str, Any] = Field(default_factory=dict)


class JiraAddCommentPayload(BaseModel):
    body: str


class JiraSearchPayload(BaseModel):
    jql: str
    maxResults: int = 10
    fields: list[str] = Field(default_factory=lambda: ["summary", "description", "status"])
