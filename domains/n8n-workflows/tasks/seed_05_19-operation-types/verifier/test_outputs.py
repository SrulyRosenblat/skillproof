"""Deterministic checks on /workspace/workflow.json and
/workspace/custom_metrics_summary.json after the queued operations batch and
the evaluation-run summary have been carried out.
"""
import json

WORKFLOW_PATH = "/workspace/workflow.json"
SUMMARY_PATH = "/workspace/custom_metrics_summary.json"


def load_workflow():
    with open(WORKFLOW_PATH) as f:
        return json.load(f)


def get_node(workflow, name):
    for node in workflow["nodes"]:
        if node["name"] == name:
            return node
    raise AssertionError(f"node {name!r} not found in workflow.json")


def test_node_add_and_remove_applied():
    workflow = load_workflow()
    names = {n["name"] for n in workflow["nodes"]}

    assert "Notify Ops" in names, "addNode operation was not applied"
    notify = get_node(workflow, "Notify Ops")
    assert notify["type"] == "n8n-nodes-base.noOp"

    assert "Legacy Logger" not in names, "removeNode operation was not applied"
    # every other original node must still be present
    assert {"Webhook", "IF", "Switch", "On True", "On False", "Case A", "Case C", "Archive"} <= names


def test_updateNode_uses_dot_notation_as_a_nested_path():
    workflow = load_workflow()
    node = get_node(workflow, "On True")
    params = node["parameters"]

    assert params.get("value") == "true-branch-hit"
    assert params.get("meta", {}).get("updatedBy") == "diff-engine", (
        "dot-notation change 'parameters.meta.updatedBy' must create/update a "
        "nested 'meta' object inside parameters, not a literal key"
    )
    # a naive implementation might set the dotted string as a literal key
    # instead of traversing into nested objects
    assert "parameters.value" not in node
    assert "meta.updatedBy" not in params


def test_if_node_smart_branch_mapping():
    workflow = load_workflow()
    main = workflow["connections"]["IF"]["main"]
    assert len(main) >= 2, "IF node must have both a true (0) and false (1) output slot"
    assert main[0] == [{"node": "On True", "type": "main", "index": 0}], (
        "branch: 'true' must land on IF's output index 0"
    )
    assert main[1] == [{"node": "On False", "type": "main", "index": 0}], (
        "branch: 'false' must land on IF's output index 1"
    )


def test_switch_node_smart_case_mapping():
    workflow = load_workflow()
    main = workflow["connections"]["Switch"]["main"]
    assert len(main) >= 3, "Switch node must have a slot for every case up through 2"
    assert main[0] == [{"node": "Case A", "type": "main", "index": 0}], (
        "case: 0 must land on Switch's output index 0"
    )
    assert main[1] == [], "case 1 was never referenced and must stay empty"
    assert main[2] == [{"node": "Case C", "type": "main", "index": 0}], (
        "case: 2 must land on Switch's output index 2, not the next free slot"
    )


def test_clean_stale_connections_sweeps_whole_graph():
    workflow = load_workflow()
    connections = workflow["connections"]

    assert "Legacy Logger" not in connections, (
        "removed node's own outgoing connections entry must be dropped"
    )

    webhook_targets = {t["node"] for t in connections["Webhook"]["main"][0]}
    assert webhook_targets == {"IF", "Switch"}, (
        f"stale references must be removed from every remaining connection list, "
        f"including one ('Old Notify') that was already broken before this batch "
        f"ran, not just the node named in the removeNode operation; got {webhook_targets}"
    )


def test_metadata_and_activation_operations():
    workflow = load_workflow()
    assert workflow["name"] == "Order Routing v2"
    assert "reviewed" in workflow.get("tags", [])
    assert workflow["active"] is True


def test_custom_metrics_summary_excludes_automatic_keys():
    with open(SUMMARY_PATH) as f:
        summary = json.load(f)

    assert summary["custom_metric_names"] == ["accuracy", "helpfulness", "toxicity"], (
        "must list exactly the metrics specific to this evaluation, sorted - not "
        "the automatic ones n8n attaches to every run (promptTokens, "
        "completionTokens, totalTokens, executionTime)"
    )
    assert abs(summary["average"] - 0.605) < 1e-6, (
        f"average must be computed only over the custom metrics; got {summary['average']}"
    )
