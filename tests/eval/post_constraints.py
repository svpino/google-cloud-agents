"""Deterministic checks for the final post and bounded editing loop."""


def _text(content):
    if not isinstance(content, dict):
        return ""
    return "".join(
        part.get("text", "")
        for part in content.get("parts", [])
        if isinstance(part, dict)
    ).strip()


def evaluate(instance):
    response = _text(instance.get("response"))
    agent_data = instance.get("agent_data") or {}
    events = [
        event
        for turn in agent_data.get("turns", [])
        for event in turn.get("events", [])
    ]
    editor_rounds = sum(event.get("author") == "editor" for event in events)

    failures = []
    if not 280 <= len(response) <= 320:
        failures.append(f"final length is {len(response)}, expected 280-320")
    if not 1 <= editor_rounds <= 3:
        failures.append(f"Editor ran {editor_rounds} times, expected 1-3")
    if response.startswith(("Final post:", "Draft:", "Writer:", "Editor:")):
        failures.append("final response contains a process label")

    if failures:
        return {"score": 0, "explanation": "; ".join(failures)}
    return {
        "score": 1,
        "explanation": (
            f"Final post is {len(response)} characters and used "
            f"{editor_rounds} Editor review round(s)."
        ),
    }
