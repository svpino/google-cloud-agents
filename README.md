# Collaborative Post

A deployable ADK Workflow API agent in which a Writer and Editor collaborate on
a polished post of approximately 300 characters. The Editor can approve a
draft or return actionable feedback; the Writer then revises it. Conditional
graph routes stop on approval or after three review rounds.

Agent generated with `agents-cli` version `1.5.0`

## Project Structure

```
google-cloud-agents/
├── app/                       # Core agent code
│   ├── agent.py               # Writer/Editor workflow graph
│   ├── fast_api_app.py        # FastAPI Backend server
│   └── app_utils/             # App utilities and helpers
├── deployment/                # Cloud Run Terraform configuration
├── tests/                     # Unit, integration, and evaluation tests
├── AGENTS.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies
```

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

Or run one idea directly:

```bash
agents-cli run "Share the idea that consistency beats occasional bursts of motivation."
```

The command returns only the final post. Add `--verbose` to inspect the Writer,
Editor, and review-gate trace.

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval run` | Generate traces and evaluate post quality and loop constraints                         |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

## Deployment

The agent is deployed as an authenticated Cloud Run service in `us-east1`:

```text
https://collaborative-post-c7icovgtka-ue.a.run.app
```

Send an authenticated request through the A2A endpoint:

```bash
agents-cli run \
  --url https://collaborative-post-c7icovgtka-ue.a.run.app \
  --mode a2a \
  "Share an idea about making time for a short walk each day."
```

Redeploy the current source with:

```bash
agents-cli deploy --project svpino --region us-east1
```

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

Set `LOG_AGENT_CONTENT=true` to emit two structured Cloud Logging records for
each run: `agent_idea` and `agent_final_response`. Both records share a
`request_id`, making each idea easy to pair with its final post. The Cloud Run
deployment enables this setting. View the records with:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="collaborative-post" AND (jsonPayload.event="agent_idea" OR jsonPayload.event="agent_final_response")' \
  --project svpino \
  --format='table(timestamp,jsonPayload.request_id,jsonPayload.event,jsonPayload.idea,jsonPayload.final_response)'
```

These records contain user-provided text. Limit access to Cloud Logging and use
an appropriate retention period. Set `LOG_AGENT_CONTENT=false` to disable them.

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/). Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability.
See the [A2A Inspector docs](https://github.com/a2aproject/a2a-inspector) for details.
