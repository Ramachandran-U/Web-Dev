# Lloyd's Property Underwriting Agentic JIRA Orchestrator

Production-oriented Python backend for hybrid AI + human-governed JIRA orchestration in a Lloyd's property underwriting context.

## Features

- Structured LLM reasoning contract (JSON schema validated via Pydantic)
- Mandatory human approval gate before **any** JIRA mutation
- Duplicate detection using semantic embeddings + JIRA search
- Comment interpretation with classification and dynamic status inference
- Attachment upload support to JIRA
- Underwriting workflow + structured Figma design prompt generation
- Retry-enabled JIRA client with error handling/logging

## Project structure

```text
/agent
  /core
    llm_client.py
    risk_engine.py
    duplicate_detector.py
    comment_engine.py
    workflow_generator.py
  /jira
    jira_client.py
    issue_manager.py
  /schemas
    models.py
  main.py
  config.py
```

## Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Set real credentials in `.env`, then run:

```bash
python -m agent.main
```

## Notes

- In the sample runtime flow, `mock_human_approval(..., approved=False)` intentionally pauses mutation execution.
- Set `approve_mutations=True` in `orchestrate()` only when explicit approval is available.
