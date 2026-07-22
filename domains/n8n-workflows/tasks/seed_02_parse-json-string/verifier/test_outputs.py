"""Deterministic checks on the n8n Code node body in /workspace/code.py.

Executes the artifact (via node_runtime.py, the same harness described to
the agent) against a hidden batch that is NOT the sample sitting in
/workspace/input.json, so a solution that special-cases the sample values
cannot pass. Never inspects code.py's source text directly.
"""
import json
import subprocess
import sys

import pytest

WORKSPACE = "/workspace"
CODE_PATH = f"{WORKSPACE}/code.py"
RUNTIME_PATH = f"{WORKSPACE}/node_runtime.py"
INPUT_PATH = f"{WORKSPACE}/input.json"
OUTPUT_PATH = f"{WORKSPACE}/output.json"

# Deliberately different literal values (and a different batch size) than
# the sample batch shipped in environment/input.json, so hardcoding the
# sample's answers cannot pass this hidden batch.
HIDDEN_BATCH = [
    {"json": {"id": 101, "payload": '{"city": "Paris", "population": 2148000, "capital": true}'}},
    {"json": {"id": 102, "payload": '{"matrix": [[1, 2], [3, 4]], "determinant": -2}'}},
    {"json": {"id": 103, "payload": '{"label": "naïve résumé"}'}},
    {"json": {"id": 104, "payload": "definitely not json"}},
    {"json": {"id": 105, "payload": "[true, false, null, 42]"}},
    {"json": {"id": 106, "payload": "{'broken': True}"}},
    {"json": {"id": 107, "payload": '{"empty": {}, "list": []}'}},
]

EXPECTED_VALID_COUNT = 5
EXPECTED_INVALID_COUNT = 2


def _expected_for(payload):
    try:
        return True, json.loads(payload)
    except json.JSONDecodeError:
        return False, None


@pytest.fixture(scope="module")
def output():
    with open(INPUT_PATH, "w") as f:
        json.dump(HIDDEN_BATCH, f)

    proc = subprocess.run(
        [sys.executable, RUNTIME_PATH, CODE_PATH, INPUT_PATH, OUTPUT_PATH],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (
        "node_runtime.py did not complete successfully — a single malformed "
        f"payload must not stop the rest of the batch from being processed:\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )

    with open(OUTPUT_PATH) as f:
        return json.load(f)


def test_one_output_item_per_input_item_plus_summary(output):
    assert isinstance(output, list), f"expected a list of output items, got {type(output).__name__}"
    expected_len = len(HIDDEN_BATCH) + 1
    assert len(output) == expected_len, (
        f"expected {expected_len} output items (one per input item, in "
        f"order, plus one trailing summary item), got {len(output)}"
    )


def test_items_are_shaped_as_n8n_expects(output):
    for i, item in enumerate(output):
        assert isinstance(item, dict) and isinstance(item.get("json"), dict), (
            f"output item {i} ({item!r}) is not shaped the way n8n expects "
            "a returned item to be shaped"
        )


def test_valid_payloads_are_parsed_to_native_data(output):
    for i, entry in enumerate(HIDDEN_BATCH):
        is_valid, expected_value = _expected_for(entry["json"]["payload"])
        if not is_valid:
            continue
        data = output[i]["json"]
        assert data.get("parsed") == expected_value, (
            f"item {i}: expected parsed == {expected_value!r}, got {data.get('parsed')!r} "
            "(payload must be decoded to native Python data, not left as a string)"
        )
        assert data.get("error") is None, (
            f"item {i}: a successfully parsed payload must leave error empty, "
            f"got {data.get('error')!r}"
        )


def test_invalid_payloads_are_reported_without_crashing(output):
    for i, entry in enumerate(HIDDEN_BATCH):
        is_valid, _ = _expected_for(entry["json"]["payload"])
        if is_valid:
            continue
        data = output[i]["json"]
        assert data.get("parsed") is None, (
            f"item {i}: a payload that fails to parse must have parsed == None, "
            f"got {data.get('parsed')!r}"
        )
        error = data.get("error")
        assert isinstance(error, str) and error.strip(), (
            f"item {i}: a payload that fails to parse must record a non-empty "
            f"error message, got {error!r}"
        )


def test_summary_item_is_a_json_encoded_manifest(output):
    data = output[-1]["json"]
    manifest_json = data.get("manifest_json")
    assert isinstance(manifest_json, str), (
        "the summary item's manifest_json must be a JSON-encoded string, got "
        f"{manifest_json!r} ({type(manifest_json).__name__})"
    )
    manifest = json.loads(manifest_json)
    assert manifest == {
        "valid_count": EXPECTED_VALID_COUNT,
        "invalid_count": EXPECTED_INVALID_COUNT,
    }, (
        f"expected manifest {{'valid_count': {EXPECTED_VALID_COUNT}, "
        f"'invalid_count': {EXPECTED_INVALID_COUNT}}}, got {manifest}"
    )
