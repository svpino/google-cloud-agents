"""Local LLM-as-judge for `custom_response_quality` (see eval_config.yaml)."""

import threading

from google import genai
from google.genai import types
from pydantic import BaseModel

_local = threading.local()


class _Verdict(BaseModel):
    score: int  # 1-5
    explanation: str


def _client() -> genai.Client:
    """One client per grading thread.

    The eval SDK grades cases on its own thread pool; this initialization runs once
    per thread. Avoids creating a new client for each eval case, which would re-do
    ADC and the TLS handshake every time. Each thread gets its own client, because
    google-auth freezes the SSL context after the first connection when a client
    certificate is present.
    """
    client = getattr(_local, "client", None)
    if client is None:
        # AI Studio (GEMINI_API_KEY) or Agent Platform (ADC).
        client = _local.client = genai.Client()
    return client


def evaluate(instance):
    rubric = (
        "Grade the final post on a 1-5 scale (1 poor, 5 excellent). A 5 faithfully "
        "expresses the user's idea and uses very simple, plain language that a "
        "non-expert can understand on the first read. It must favor common everyday "
        "words, short direct sentences, active voice, and concrete wording. Penalize "
        "jargon, buzzwords, technical terms, difficult or uncommon words, abstract "
        "phrases, and complex sentence structures. A 5 also stands alone as a post, "
        "contains no unsupported facts or details, and is naturally close to 300 "
        "characters. Penalize process notes, labels, feedback, or character counts."
    )
    prompt = (
        f"You are an expert editor evaluating a collaborative writing agent. {rubric}\n"
        f"User Prompt: {instance.get('prompt', '')}\n"
        f"Final Response: {instance.get('response', '')}\n"
        f"Full Writer/Editor Trace: {instance.get('agent_data', '')}\n"
    )

    response = _client().models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,  # deterministic grading
            response_mime_type="application/json",
            response_schema=_Verdict,  # guaranteed schema-valid JSON
        ),
    )
    verdict = response.parsed
    if verdict is None:  # model returned nothing usable
        return {"score": 0, "explanation": response.text or ""}
    return {"score": max(1, min(5, verdict.score)), "explanation": verdict.explanation}
