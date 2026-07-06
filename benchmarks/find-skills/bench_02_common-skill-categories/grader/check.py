#!/usr/bin/env python3
"""Deterministic grader for bench_02_common-skill-categories.

Checks /workspace/search_plan.json against the fixed set of requests in
/workspace/requests.json. No network, no randomness, no ordering dependence.
"""
import json
import re
import sys
from pathlib import Path

WORKSPACE = Path.cwd()

KNOWN_SOURCES = {
    "vercel-labs/agent-skills",
    "composiohq/awesome-claude-skills",
}

# id -> (required anchor terms for primary_query, allowed synonym terms for alternative_query)
DOMAIN_SPEC = {
    "r1": (
        ["playwright"],
        ["e2e", "end-to-end", "end to end", "test", "playwright", "flaky"],
    ),
    "r2": (
        ["kubernetes", "k8s"],
        ["deploy", "deployment", "ci-cd", "cicd", "pipeline", "kubernetes", "k8s"],
    ),
    "r3": (
        ["review"],
        ["review", "lint", "refactor", "quality"],
    ),
    "r4": (
        ["changelog"],
        ["changelog", "release notes", "release-notes", "docs", "commit"],
    ),
}

NO_MATCH_ID = "r5"
ALL_IDS = {"r1", "r2", "r3", "r4", "r5"}

NO_FOUND_PATTERNS = [
    r"no\s+(existing|pre-?built|matching|available|good)\s+(package|skill|tool)",
    r"(couldn'?t|could not|did not|didn'?t)\s+find",
    r"doesn'?t\s+(exist|appear to exist)",
    r"no\s+(package|skill|tool)\s+(exists|found|available)",
    r"none\s+(found|exist|available)",
]

HELP_WORD = re.compile(r"\bhelp\b", re.I)
IMMEDIACY_WORDS = re.compile(
    r"\b(now|directly|right away|myself|happy to|go ahead|today|immediately)\b", re.I
)

CREATE_OWN_PATTERN = re.compile(r"skills\s+init", re.I)


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    plan_path = WORKSPACE / "search_plan.json"
    if not plan_path.exists():
        fail("search_plan.json does not exist")

    try:
        raw = plan_path.read_text()
        data = json.loads(raw)
    except Exception as e:
        fail(f"search_plan.json is not valid JSON: {e}")

    if not isinstance(data, dict) or "plans" not in data:
        fail("search_plan.json must be a JSON object with a top-level 'plans' key")

    plans = data["plans"]
    if not isinstance(plans, list):
        fail("'plans' must be a list")

    by_id = {}
    for entry in plans:
        if not isinstance(entry, dict) or "id" not in entry:
            fail(f"each plan entry must be an object with an 'id' field, got: {entry!r}")
        eid = entry["id"]
        if eid in by_id:
            fail(f"duplicate plan id: {eid}")
        by_id[eid] = entry

    missing = ALL_IDS - set(by_id.keys())
    if missing:
        fail(f"missing plan entries for ids: {sorted(missing)}")

    extra = set(by_id.keys()) - ALL_IDS
    if extra:
        fail(f"unexpected plan ids (not in requests.json): {sorted(extra)}")

    # --- Domain requests: r1-r4 ---
    for rid, (anchors, alt_terms) in DOMAIN_SPEC.items():
        entry = by_id[rid]

        primary = entry.get("primary_query")
        alternative = entry.get("alternative_query")
        sources = entry.get("check_sources")

        if not isinstance(primary, str) or not primary.strip():
            fail(f"{rid}: 'primary_query' must be a non-empty string")
        if not isinstance(alternative, str) or not alternative.strip():
            fail(f"{rid}: 'alternative_query' must be a non-empty string")
        if not isinstance(sources, list) or not (1 <= len(sources) <= 2):
            fail(f"{rid}: 'check_sources' must be a list of 1-2 strings")
        for s in sources:
            if not isinstance(s, str):
                fail(f"{rid}: 'check_sources' entries must be strings")

        primary_l = primary.strip().lower()
        alt_l = alternative.strip().lower()

        if len(primary.strip().split()) < 2:
            fail(
                f"{rid}: 'primary_query' ({primary!r}) must use a specific, "
                "multi-word query, not a single generic word"
            )

        if not any(a in primary_l for a in anchors):
            fail(
                f"{rid}: 'primary_query' ({primary!r}) does not mention the "
                f"specific subject of the request (expected one of {anchors})"
            )

        if primary_l == alt_l:
            fail(f"{rid}: 'alternative_query' must differ from 'primary_query'")

        if not any(t in alt_l for t in alt_terms):
            fail(
                f"{rid}: 'alternative_query' ({alternative!r}) is not clearly "
                f"related to the request (expected one of {alt_terms})"
            )

        sources_l = {s.strip().lower() for s in sources}
        if not (sources_l & KNOWN_SOURCES):
            fail(
                f"{rid}: 'check_sources' ({sources!r}) does not include a "
                "well-known, broad source repository for this registry"
            )

    # --- No-match request: r5 ---
    entry = by_id[NO_MATCH_ID]
    response = entry.get("no_match_response")
    if not isinstance(response, str) or not response.strip():
        fail(f"{NO_MATCH_ID}: 'no_match_response' must be a non-empty string")

    if any(re.search(p, response, re.I) for p in NO_FOUND_PATTERNS):
        pass
    else:
        fail(
            f"{NO_MATCH_ID}: 'no_match_response' does not clearly state that "
            "no existing package was found"
        )

    if not (HELP_WORD.search(response) and IMMEDIACY_WORDS.search(response)):
        fail(
            f"{NO_MATCH_ID}: 'no_match_response' does not clearly offer to "
            "help with the task directly, right now"
        )

    if not CREATE_OWN_PATTERN.search(response):
        fail(
            f"{NO_MATCH_ID}: 'no_match_response' does not give the specific "
            "command/workflow for packaging this up as a reusable capability"
        )

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
