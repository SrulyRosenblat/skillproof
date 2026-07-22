"""Deterministic checks on the n8n Code node body in /workspace/code.py.

Executes the artifact (via node_runtime.py, the same harness described to
the agent) against hidden single-item webhook invocations that are NOT the
sample sitting in /workspace/input.json, so a solution that special-cases
the sample values cannot pass. Never inspects code.py's source text
directly.
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

# Deliberately different customers/orders than the sample shipped in
# environment/input.json, so hardcoding the sample's answer cannot pass
# these hidden invocations. Each represents one incoming webhook call this
# node is executed against.
HIDDEN_CASES = [
    {"customer": "Globex Inc", "orders": [
        {"item": "Sprocket", "amount": 5.25, "quantity": 10},
    ]},
    {"customer": "Initech", "orders": []},
    {"customer": "Umbrella Corp", "orders": [
        {"item": "Vial", "amount": 12.35, "quantity": 4},
        {"item": "Case", "amount": 3.5, "quantity": 2},
    ]},
    {"customer": "Soylent Corp", "orders": [
        {"item": "Bar", "amount": 2.99, "quantity": 1},
    ]},
]


def _expected_for(case):
    orders = case["orders"]
    total = sum(o["amount"] * o["quantity"] for o in orders)
    return case["customer"], len(orders), total


def _make_batch(case):
    return [{
        "json": {
            "headers": {
                "content-type": "application/json",
                "x-forwarded-for": "198.51.100.1",
            },
            "params": {},
            "query": {},
            "body": {"customer": case["customer"], "orders": case["orders"]},
        }
    }]


def _run_case(case):
    with open(INPUT_PATH, "w") as f:
        json.dump(_make_batch(case), f)

    proc = subprocess.run(
        [sys.executable, RUNTIME_PATH, CODE_PATH, INPUT_PATH, OUTPUT_PATH],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (
        f"node_runtime.py did not complete successfully for customer "
        f"{case['customer']!r}:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )

    with open(OUTPUT_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def results():
    return [(case, _run_case(case)) for case in HIDDEN_CASES]


def test_output_is_a_single_item_wrapped_in_a_list(results):
    for case, output in results:
        assert isinstance(output, list), (
            f"customer {case['customer']!r}: expected the node to return a "
            f"list, got {type(output).__name__}"
        )
        assert len(output) == 1, (
            f"customer {case['customer']!r}: a run processing one item must "
            f"hand back exactly one outgoing item, got {len(output)}"
        )


def test_item_is_shaped_as_n8n_expects(results):
    for case, output in results:
        item = output[0]
        assert isinstance(item, dict) and isinstance(item.get("json"), dict), (
            f"customer {case['customer']!r}: outgoing item {item!r} is not "
            "shaped the way n8n expects a returned item to be shaped"
        )


def test_customer_is_carried_through(results):
    for case, output in results:
        expected_customer, _, _ = _expected_for(case)
        data = output[0]["json"]
        assert data.get("customer") == expected_customer, (
            f"expected customer {expected_customer!r}, got {data.get('customer')!r}"
        )


def test_order_count_is_correct(results):
    for case, output in results:
        _, expected_count, _ = _expected_for(case)
        data = output[0]["json"]
        assert data.get("order_count") == expected_count, (
            f"customer {case['customer']!r}: expected order_count == "
            f"{expected_count}, got {data.get('order_count')!r}"
        )


def test_total_amount_is_correct(results):
    for case, output in results:
        _, _, expected_total = _expected_for(case)
        data = output[0]["json"]
        total = data.get("total_amount")
        assert isinstance(total, (int, float)), (
            f"customer {case['customer']!r}: expected total_amount to be "
            f"numeric, got {total!r}"
        )
        assert abs(total - expected_total) < 0.01, (
            f"customer {case['customer']!r}: expected total_amount ≈ "
            f"{expected_total}, got {total!r}"
        )


def test_customer_with_no_orders_is_not_skipped(results):
    no_order_cases = [(case, output) for case, output in results if not case["orders"]]
    assert no_order_cases, "test setup error: expected a no-orders hidden case"
    for case, output in no_order_cases:
        data = output[0]["json"]
        assert data.get("order_count") == 0
        assert abs(data.get("total_amount", -1) - 0) < 0.01
