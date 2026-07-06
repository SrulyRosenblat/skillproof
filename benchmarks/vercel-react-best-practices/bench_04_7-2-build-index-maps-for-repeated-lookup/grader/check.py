#!/usr/bin/env python3
"""Functional + algorithmic-behavior checks for the index-map benchmark.

Run after `node -r instrument.js solve.js` has already executed in
/workspace (grade.sh handles that). This script:
  1. Recomputes the expected outputs directly from the fixtures (independent
     of whatever algorithm the agent used) and diffs them against what the
     agent's script wrote to /workspace/output/.
  2. Reads the instrumentation counts written by instrument.js and asserts
     they are consistent with the taught patterns (index map, single-pass
     categorization, early length check) rather than the naive equivalents.
"""
import json
import os
import sys

WORKSPACE = os.environ.get("WORKSPACE_DIR", "/workspace")
DATA_DIR = os.path.join(WORKSPACE, "data")
OUTPUT_DIR = os.path.join(WORKSPACE, "output")
INSTRUMENT_OUTPUT = os.environ.get("INSTRUMENT_OUTPUT", "/tmp/instrument_counts.json")

# Thresholds calibrated so that:
#   - an index-map join yields 0 find-callback invocations, vs. ~2,000,000
#     for a per-order Array.prototype.find over 2000 users.
#   - a single-pass categorization yields 0 filter-callback invocations, vs.
#     6000 (3 separate filter() calls x 2000 users) for the naive version.
#   - an early-length-check comparison yields ~200 sort invocations (only
#     for the 100 equal-length pairs), vs. 600 for unconditionally sorting
#     both arrays of all 300 pairs.
FIND_CALLBACK_THRESHOLD = 20_000
FILTER_CALLBACK_THRESHOLD = 3_000
SORT_INVOCATIONS_THRESHOLD = 400


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path):
    if not os.path.isfile(path):
        fail(f"expected file missing: {path}")
    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            fail(f"invalid JSON in {path}: {e}")


def main():
    users = load_json(os.path.join(DATA_DIR, "users.json"))
    orders = load_json(os.path.join(DATA_DIR, "orders.json"))
    tag_pairs = load_json(os.path.join(DATA_DIR, "tag_pairs.json"))

    user_by_id = {u["id"]: u for u in users}

    # ---- expected enriched_orders -----------------------------------------
    expected_enriched = []
    for order in orders:
        user = user_by_id.get(order["userId"])
        expected_enriched.append({**order, "user": user})

    # ---- expected user_categories ------------------------------------------
    expected_admins = [u["id"] for u in users if u["isAdmin"]]
    expected_testers = [u["id"] for u in users if u["isTester"]]
    expected_inactive = [u["id"] for u in users if not u["isActive"]]

    # ---- expected tag_changes ------------------------------------------------
    expected_tag_changes = []
    for pair in tag_pairs:
        cur = pair["current"]
        orig = pair["original"]
        if len(cur) != len(orig):
            changed = True
        else:
            changed = sorted(cur) != sorted(orig)
        expected_tag_changes.append({"id": pair["id"], "changed": changed})

    # ---- load produced output ------------------------------------------------
    actual_enriched = load_json(os.path.join(OUTPUT_DIR, "enriched_orders.json"))
    actual_categories = load_json(os.path.join(OUTPUT_DIR, "user_categories.json"))
    actual_tag_changes = load_json(os.path.join(OUTPUT_DIR, "tag_changes.json"))

    # ---- functional correctness ------------------------------------------------
    if not isinstance(actual_enriched, list) or len(actual_enriched) != len(expected_enriched):
        fail("enriched_orders.json: wrong length or not a list")
    for i, (exp, act) in enumerate(zip(expected_enriched, actual_enriched)):
        if act.get("id") != exp["id"] or act.get("userId") != exp["userId"]:
            fail(f"enriched_orders.json: order at index {i} has wrong id/userId")
        if act.get("user") != exp["user"]:
            fail(f"enriched_orders.json: order {exp['id']} joined to wrong user (expected {exp['user']!r}, got {act.get('user')!r})")

    if not isinstance(actual_categories, dict):
        fail("user_categories.json: must be a JSON object")
    for key, expected_list in (
        ("admins", expected_admins),
        ("testers", expected_testers),
        ("inactive", expected_inactive),
    ):
        if actual_categories.get(key) != expected_list:
            fail(f"user_categories.json: '{key}' does not match expected ids (in order)")

    if not isinstance(actual_tag_changes, list) or len(actual_tag_changes) != len(expected_tag_changes):
        fail("tag_changes.json: wrong length or not a list")
    by_id_actual = {}
    for i, entry in enumerate(actual_tag_changes):
        if "id" not in entry or "changed" not in entry:
            fail(f"tag_changes.json: entry at index {i} missing 'id' or 'changed'")
        by_id_actual[entry["id"]] = entry["changed"]
    for exp in expected_tag_changes:
        if exp["id"] not in by_id_actual:
            fail(f"tag_changes.json: missing entry for id {exp['id']}")
        if by_id_actual[exp["id"]] != exp["changed"]:
            fail(f"tag_changes.json: wrong 'changed' value for id {exp['id']} (expected {exp['changed']})")

    # ---- algorithmic-behavior checks (from execution instrumentation) --------
    counts = load_json(INSTRUMENT_OUTPUT)

    find_calls = counts.get("findCallbackInvocations", float("inf"))
    filter_calls = counts.get("filterCallbackInvocations", float("inf"))
    sort_calls = counts.get("sortInvocations", float("inf"))

    if find_calls >= FIND_CALLBACK_THRESHOLD:
        fail(
            f"enriched_orders join scanned {find_calls} elements via .find() "
            f"(limit {FIND_CALLBACK_THRESHOLD}) -- looks like a per-order linear "
            f"scan over the full users list instead of an indexed lookup"
        )

    if filter_calls >= FILTER_CALLBACK_THRESHOLD:
        fail(
            f"user_categories computation scanned {filter_calls} elements via "
            f".filter() (limit {FILTER_CALLBACK_THRESHOLD}) -- looks like multiple "
            f"separate full passes over the users list instead of one combined pass"
        )

    if sort_calls >= SORT_INVOCATIONS_THRESHOLD:
        fail(
            f"tag comparison invoked sort/toSorted {sort_calls} times (limit "
            f"{SORT_INVOCATIONS_THRESHOLD}) -- looks like every pair is sorted "
            f"unconditionally instead of checking lengths first"
        )

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
