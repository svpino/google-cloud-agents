# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from uuid import uuid4

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events import Event, EventActions
from google.adk.models import Gemini
from google.adk.workflow import Workflow
from google.genai import types
from pydantic import BaseModel, Field


MODEL = "gemini-3.7-flash"
MIN_POST_LENGTH = 280
MAX_POST_LENGTH = 320


def _log_agent_content(
    *, event: str, request_id: str, field_name: str, value: str
) -> None:
    """Write one filterable JSON record for the idea or final response."""
    print(
        json.dumps(
            {
                "severity": "INFO",
                "message": event,
                "event": event,
                "request_id": request_id,
                field_name: value,
                "character_count": len(value),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


class EditorialReview(BaseModel):
    """The Editor's decision about the Writer's current draft."""

    approved: bool = Field(
        description="True only when the post is ready to publish without changes."
    )
    feedback: str = Field(
        description="Specific revision guidance, or an empty string when approved."
    )


class DraftOutput(BaseModel):
    """The Writer's current post draft."""

    post: str = Field(description="The standalone post text without labels.")


def _model() -> Gemini:
    """Create the scaffold-configured Gemini model for an LLM agent."""
    return Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    )


writer = LlmAgent(
    name="writer",
    description="Drafts and revises a concise post from the user's idea.",
    model=_model(),
    instruction="""
You are the Writer in a Writer/Editor collaboration.

Write a polished standalone post based only on the user's original idea. The
target is approximately 300 visible characters, ideally 280 - 320 characters
including spaces and punctuation.

Original idea:
{original_idea}

Current draft, if one exists:
{current_draft?}

Latest Editor review, if one exists:
{editor_review?}

On the first pass, create the draft. On later passes, revise the current draft
to address every actionable point in the latest review. Preserve the user's
meaning and do not invent facts, quotations, links, statistics, dates, or calls
to action. Favor natural, specific writing over padding.

Return only the post text. Do not add a label, explanation, character count,
quotation marks, or Markdown fence.
""".strip(),
    output_schema=DraftOutput,
    output_key="current_draft",
)


editor = LlmAgent(
    name="editor",
    description="Reviews the current post for accuracy and very simple language.",
    model=_model(),
    instruction="""
You are the Editor in a Writer/Editor collaboration. Review the current draft:

{current_draft}

The user's original idea is:

{original_idea}

Plain language is a hard requirement. The post must be very easy to understand
on the first read. It must use common, everyday words, short direct sentences,
active voice, and concrete wording. Reject jargon, buzzwords, technical terms,
uncommon or difficult words, abstract phrases, long sentences, and complex
sentence structures. If the idea needs a specialized term, replace it with a
plain explanation that a non-expert can understand.

Also check that the post faithfully expresses the user's original idea, is
polished, avoids unsupported details, and is approximately 300 visible
characters. Treat 280 - 320 characters as the preferred range.

Approve only when the language is already very simple and no meaningful
improvement is needed. Do not approve a draft merely because it is accurate or
within the target length. When changes are needed, set approved to false and
give concise, specific, actionable feedback. Name any hard words or phrases and
suggest simpler wording the Writer can use. When approved, set feedback to an
empty string.
""".strip(),
    output_schema=EditorialReview,
    output_key="editor_review",
)


def initialize_workflow(node_input: types.Content) -> Event:
    """Capture the new idea and reset per-run editing state."""
    idea = "".join(part.text or "" for part in node_input.parts or []).strip()
    request_id = uuid4().hex
    _log_agent_content(
        event="agent_idea",
        request_id=request_id,
        field_name="idea",
        value=idea,
    )
    return Event(
        output=idea,
        actions=EventActions(
            state_delta={
                "original_idea": idea,
                "current_draft": None,
                "editor_review": None,
                "review_rounds": 0,
                "character_count": 0,
                "request_id": request_id,
            }
        ),
    )


def review_gate(ctx: Context, node_input: EditorialReview) -> Event:
    """Route to another revision or finish after approval/three reviews."""
    draft = DraftOutput.model_validate(ctx.state.get("current_draft"))
    review = node_input
    review_rounds = int(ctx.state.get("review_rounds", 0)) + 1
    character_count = len(draft.post.strip())
    in_preferred_range = MIN_POST_LENGTH <= character_count <= MAX_POST_LENGTH

    if review.approved and not in_preferred_range:
        direction = "expand" if character_count < MIN_POST_LENGTH else "shorten"
        review = EditorialReview(
            approved=False,
            feedback=(
                f"{direction.capitalize()} the post naturally into the "
                f"{MIN_POST_LENGTH} - {MAX_POST_LENGTH} character range. "
                f"It is currently {character_count} characters."
            ),
        )

    should_finish = (review.approved and in_preferred_range) or review_rounds >= 3
    output = draft.post.strip() if should_finish else review.model_dump()

    return Event(
        output=output,
        actions=EventActions(
            route="finish" if should_finish else "revise",
            state_delta={
                "character_count": character_count,
                "editor_review": review.model_dump(),
                "review_rounds": review_rounds,
            },
        ),
    )


def final_post(ctx: Context, node_input: str) -> Event:
    """Emit the latest Writer draft as the workflow's final response."""
    _log_agent_content(
        event="agent_final_response",
        request_id=str(ctx.state.get("request_id", "")),
        field_name="final_response",
        value=node_input,
    )
    return Event(
        output=node_input,
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=node_input)],
        ),
    )


root_agent = Workflow(
    name="collaborative_post",
    description="Creates a polished post through a bounded Writer/Editor workflow.",
    edges=[
        ("START", initialize_workflow),
        (initialize_workflow, writer),
        (writer, editor),
        (editor, review_gate),
        (review_gate, {"revise": writer, "finish": final_post}),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
