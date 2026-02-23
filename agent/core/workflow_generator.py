"""Underwriting workflow and Figma prompt generation."""

from __future__ import annotations

from agent.schemas.models import WorkflowOutput


class WorkflowGenerator:
    """Builds domain-aware workflow artifacts for property underwriting stories."""

    def generate(self, summary: str, context: str) -> WorkflowOutput:
        swimlanes = [
            "Coverholder / Broker Intake",
            "Managing Agent Underwriting",
            "Exposure & CAT Modelling",
            "Referral Committee",
            "Claims & FNOL Coordination",
        ]
        decision_nodes = [
            "MRC completeness check",
            "Delegated authority binding authority validation",
            "CAT accumulation threshold exceeded?",
            "Pricing/rating deviation within tolerance?",
            "Regulatory or conduct risk escalation required?",
        ]
        exception_paths = [
            "Missing slip details -> return to coverholder",
            "Out-of-authority risk -> referral to syndicate committee",
            "Sanctions/compliance concern -> regulatory escalation",
            "FNOL mismatch with wording -> claims/legal joint review",
        ]

        workflow_text = (
            f"Underwriting workflow for: {summary}\n"
            "1) Intake risk submission and validate MRC data quality.\n"
            "2) Confirm delegated authority scope and coverholder permissions.\n"
            "3) Run CAT modelling, evaluate zonal aggregation and peril concentrations.\n"
            "4) Evaluate rating adequacy and policy wording consistency.\n"
            "5) If risk exceeds referral thresholds, escalate to referral committee.\n"
            "6) Bind/update policy record and notify claims/FNOL controls where relevant.\n"
            f"Context note: {context}"
        )

        figma_prompt = (
            "Create a Lloyd's property underwriting workflow diagram with swimlanes for intake, underwriting, "
            "CAT modelling, referral governance, and claims. Include decision diamonds for referral thresholds, "
            "rating logic, and regulatory escalation. Mark exception paths with red connectors and approval gates."
        )

        return WorkflowOutput(
            workflow_text=workflow_text,
            figma_prompt=figma_prompt,
            swimlanes=swimlanes,
            decision_nodes=decision_nodes,
            exception_paths=exception_paths,
        )
