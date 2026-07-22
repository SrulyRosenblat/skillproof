"""Deterministic checks on /workspace/workflow.json's `hitl_review` node.

Tests the produced artifact only (never the process/tooling that made it):
does the human-review step actually implement a two-outcome, recordable
decision whose button labels embed the real values being decided on, and is
the tool itself named specifically rather than left as a placeholder.
"""
import json
import re

WORKFLOW_PATH = "/workspace/workflow.json"

# Broad but bounded whitelist of common action verbs — the naming check only
# needs to catch generic placeholders ("Tool"), not enforce one exact word.
VERB_WHITELIST = {
    "approve", "confirm", "review", "choose", "pick", "decide", "select",
    "authorize", "verify", "ask", "request", "resolve", "determine", "settle",
    "validate", "sign", "grant", "deny", "escalate", "route", "process",
    "issue", "send", "notify", "flag", "check", "inspect", "get", "fetch",
    "lookup", "search", "create", "update", "delete", "cancel", "schedule",
    "refund", "dispatch", "assign", "forward", "reject", "accept", "obtain",
    "secure", "collect", "gather", "evaluate", "assess", "judge", "weigh",
    "clear", "sanction", "ratify", "recommend", "handle", "finalize",
}

EXPECTED_TOOL_PARAMS = {"customerName": "Morgan Chen", "refundAmount": 85}


def load_workflow():
    with open(WORKFLOW_PATH) as f:
        return json.load(f)


def get_node(workflow, node_id):
    for node in workflow["nodes"]:
        if node["id"] == node_id:
            return node
    raise AssertionError(f"node {node_id!r} not found in workflow.json")


def get_labels(workflow):
    hitl = get_node(workflow, "hitl_review")
    values = hitl["parameters"].get("approvalOptions", {}).get("values", {})
    return values.get("approveLabel"), values.get("disapproveLabel")


def test_source_tool_untouched():
    workflow = load_workflow()
    tool_node = get_node(workflow, "tool_refund")
    for key, value in EXPECTED_TOOL_PARAMS.items():
        assert tool_node["parameters"].get(key) == value, (
            f"tool_refund parameter {key!r} changed; it must stay the fixed "
            "input the review step reads from"
        )


def test_structure_preserved():
    workflow = load_workflow()
    ids = {node["id"] for node in workflow["nodes"]}
    assert ids == {"agent1", "tool_refund", "hitl_review"}, (
        f"node set changed unexpectedly: {ids}"
    )


def test_response_type_is_double_approval():
    workflow = load_workflow()
    hitl = get_node(workflow, "hitl_review")
    params = hitl["parameters"]

    assert params.get("responseType") == "approval", (
        "a two-outcome decision needs the button-based approval response "
        f"type, got responseType={params.get('responseType')!r}"
    )
    approval_type = params.get("approvalOptions", {}).get("values", {}).get("approvalType")
    assert approval_type == "double", (
        "both outcomes must be explicit, recordable buttons (approvalType "
        f"'double'), got {approval_type!r}"
    )


def test_labels_are_expressions_showing_the_real_values():
    workflow = load_workflow()
    tool_node = get_node(workflow, "tool_refund")
    relevant_keys = [k for k in tool_node["parameters"] if k != "url"]
    approve_label, disapprove_label = get_labels(workflow)

    for label_name, label in (
        ("approveLabel", approve_label),
        ("disapproveLabel", disapprove_label),
    ):
        assert isinstance(label, str) and label.strip(), (
            f"{label_name} must be a non-empty string"
        )
        assert label.startswith("="), (
            f"{label_name} ({label!r}) must start with '=' so n8n evaluates "
            "the embedded expression instead of showing the literal "
            "'{{ ... }}' text"
        )
        for key in relevant_keys:
            pattern = (
                r"\$tool\.parameters(?:\.%s\b|\[['\"]%s['\"]\])"
                % (re.escape(key), re.escape(key))
            )
            assert re.search(pattern, label), (
                f"{label_name} ({label!r}) must embed the actual "
                f"$tool.parameters.{key} value, not generic wording"
            )


def test_labels_are_distinct():
    approve_label, disapprove_label = get_labels(load_workflow())
    assert approve_label != disapprove_label, (
        "approveLabel and disapproveLabel must describe the two different "
        "outcomes, not be interchangeable"
    )


def test_tool_renamed_to_specific_verb_first_label():
    workflow = load_workflow()
    hitl = get_node(workflow, "hitl_review")
    name = hitl.get("name", "")

    assert name != "Tool", "the generic placeholder name must be replaced"
    words = name.strip().split()
    assert len(words) >= 3, f"name {name!r} is not specific enough"

    first_word = re.sub(r"[^a-zA-Z]", "", words[0]).lower()
    assert first_word in VERB_WHITELIST, (
        f"name {name!r} should be verb-first (start with an action verb "
        f"naming what the reviewer does), got {words[0]!r}"
    )
