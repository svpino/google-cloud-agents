from types import SimpleNamespace

import pytest
from google.adk.workflow import Workflow
from pydantic import ValidationError

from app.agent import EditorialReview, review_gate, root_agent


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
