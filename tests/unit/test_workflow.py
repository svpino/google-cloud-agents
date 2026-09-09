import json
from types import SimpleNamespace

import pytest
from google.adk.workflow import Workflow
from google.genai import types
from pydantic import ValidationError

from app.agent import (
    EditorialReview,
    final_post,
    initialize_workflow,
    review_gate,
    root_agent,
)


def test_workflow_uses_conditional_revision_routes() -> None:
    assert isinstance(root_agent, Workflow)
    edges = {
        (edge.from_node.name, edge.to_node.name, edge.route)
        for edge in root_agent.graph.edges
    }
    assert ("review_gate", "writer", "revise") in edges
    assert ("review_gate", "final_post", "finish") in edges


def test_review_gate_forces_finish_after_third_review() -> None:
    ctx = SimpleNamespace(
        state={"current_draft": {"post": "x" * 300}, "review_rounds": 2}
    )
    event = review_gate(
        ctx, EditorialReview(approved=False, feedback="Improve the wording.")
    )

    assert event.actions.route == "finish"
    assert event.actions.state_delta["review_rounds"] == 3
    assert event.output == "x" * 300


def test_editorial_review_requires_a_complete_decision() -> None:
    review = EditorialReview(approved=False, feedback="Make the opening clearer.")
    assert not review.approved
    assert review.feedback == "Make the opening clearer."

    with pytest.raises(ValidationError):
        EditorialReview.model_validate({"approved": True})


def test_content_logs_pair_idea_and_final_response(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LOG_AGENT_CONTENT", "true")
    idea = "Make time for a short walk each day."
    post = "A short daily walk can make room to breathe and reset."

    start_event = initialize_workflow(
        types.Content(role="user", parts=[types.Part.from_text(text=idea)])
    )
    request_id = start_event.actions.state_delta["request_id"]
    final_post(SimpleNamespace(state={"request_id": request_id}), post)

    logs = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert logs == [
        {
            "severity": "INFO",
            "message": "agent_idea",
            "event": "agent_idea",
            "request_id": request_id,
            "idea": idea,
            "character_count": len(idea),
        },
        {
            "severity": "INFO",
            "message": "agent_final_response",
            "event": "agent_final_response",
            "request_id": request_id,
            "final_response": post,
            "character_count": len(post),
        },
    ]


def test_content_logging_is_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("LOG_AGENT_CONTENT", raising=False)
    initialize_workflow(
        types.Content(role="user", parts=[types.Part.from_text(text="An idea")])
    )

    assert capsys.readouterr().out == ""
