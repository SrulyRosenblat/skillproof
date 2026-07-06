import json
import os
import re
import sys
from pathlib import Path


WORKSPACE = Path(os.environ.get("WORKSPACE", ".")).resolve()


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_required(path: Path) -> str:
    require(path.exists(), f"Missing required file: {path.name}")
    require(path.is_file(), f"Expected file but found something else: {path.name}")
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str | None) -> str:
    start = text.find(heading)
    require(start != -1, f"Missing heading: {heading}")
    start += len(heading)
    end = len(text) if next_heading is None else text.find(next_heading, start)
    require(end != -1 or next_heading is None, f"Missing heading after {heading}: {next_heading}")
    return text[start:end if end != -1 else None].strip()


def main() -> None:
    selection_text = load_required(WORKSPACE / "selection.json")
    response_text = load_required(WORKSPACE / "response.md")

    try:
        selection = json.loads(selection_text)
    except json.JSONDecodeError as exc:
        fail(f"selection.json is not valid JSON: {exc}")

    require(isinstance(selection, dict), "selection.json must contain a JSON object")
    require(set(selection.keys()) == {"request_type", "selected_guideline", "why"}, "selection.json must contain exactly request_type, selected_guideline, and why")

    request_type = selection["request_type"]
    selected_guideline = selection["selected_guideline"]
    why = selection["why"]

    require(isinstance(request_type, str) and request_type.strip(), "request_type must be a non-empty string")
    require(isinstance(selected_guideline, str) and selected_guideline.strip(), "selected_guideline must be a non-empty string")
    require(isinstance(why, str) and why.strip(), "why must be a non-empty string")

    require(selected_guideline == "examples/general-comms.md", "The selected guideline must be examples/general-comms.md")
    require("leadership" in request_type.lower(), "request_type must identify the request as a leadership update")

    lowered = response_text.lower()
    banned = ["tbd", "todo", "lorem ipsum", "[insert", "[add", "placeholder"]
    for token in banned:
        require(token not in lowered, f"response.md contains banned placeholder text: {token}")

    wrong_guide_markers = [
        "## progress",
        "## plans",
        "## problems",
        "## wins this week",
        "## coming up",
        "## team spotlight",
        "\nq: ",
        "\na: ",
    ]
    for marker in wrong_guide_markers:
        require(marker not in lowered, f"response.md appears to follow the wrong guide: {marker.strip()}")

    lines = [line.rstrip() for line in response_text.splitlines()]
    non_empty = [line for line in lines if line.strip()]
    require(non_empty, "response.md must not be empty")
    require(non_empty[0].startswith("# "), "response.md must start with an H1 title")

    require("Audience: Executive Leadership Team" in response_text, "response.md must include the required audience line")
    require("Date: July 6, 2026" in response_text, "response.md must include the required date line")

    summary_heading = "## Summary"
    changes_heading = "## Key Changes"
    impact_heading = "## Impact and Risks"
    next_heading = "## Next Steps"

    order = [response_text.find(h) for h in [summary_heading, changes_heading, impact_heading, next_heading]]
    require(all(i != -1 for i in order), "response.md is missing one or more required sections")
    require(order == sorted(order), "response.md sections are not in the required order")

    summary = section(response_text, summary_heading, changes_heading)
    summary_sentences = [part.strip() for part in re.split(r"[.!?]+", summary) if part.strip()]
    require(2 <= len(summary_sentences) <= 3, "Summary must contain 2 or 3 sentences")

    key_changes = section(response_text, changes_heading, impact_heading).splitlines()
    key_bullets = [line for line in key_changes if line.startswith("- ")]
    require(len(key_bullets) == 3, "Key Changes must contain exactly 3 bullets")
    for bullet in key_bullets:
        require(bullet.startswith("- **"), "Each Key Changes bullet must begin with a bold label")

    impact = section(response_text, impact_heading, next_heading).splitlines()
    impact_bullets = [line for line in impact if line.startswith("- ")]
    require(len(impact_bullets) == 2, "Impact and Risks must contain exactly 2 bullets")

    next_steps = section(response_text, next_heading, None).splitlines()
    numbered = [line for line in next_steps if re.match(r"\d+\. ", line)]
    require(len(numbered) == 2, "Next Steps must contain exactly 2 numbered items")

    fact_checks = [
        ("38 customers", "38 customers"),
        ("no data loss", "no data loss"),
        ("no security incident", "no security incident"),
        ("July 8, 2026", "July 8, 2026"),
        ("July 15, 2026", "July 15, 2026"),
        ("freeze on non-critical CRM releases", "freeze on non-critical CRM releases"),
    ]
    for needle, label in fact_checks:
        require(needle.lower() in lowered, f"response.md is missing required fact: {label}")

    root_cause_terms = ["retry job", "idempotency tokens", "queue failover"]
    present_terms = [term for term in root_cause_terms if term in lowered]
    require(len(present_terms) >= 2, "response.md must describe the root cause with enough specificity")

    require("july 3, 2026" in lowered or "2:20 pm et" in lowered, "response.md must mention when the customer-facing issue was fixed")
    require("july 4, 2026" in lowered or "9:00 am et" in lowered, "response.md must mention when duplicate records were fully removed")


if __name__ == "__main__":
    main()
