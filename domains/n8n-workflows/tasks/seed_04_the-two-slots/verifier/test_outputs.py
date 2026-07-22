"""Deterministic checks on /workspace/workflow.json.

The email node is supposed to send out the same invoice file the webhook
received, byte-for-byte, alongside the edited status fields. These tests
check that the binary attachment actually has a wired path from the webhook
through to the email node, and that the email node looks for it under the
name the webhook actually gave it - not just that some connection or
parameter changed.
"""
import json

WORKFLOW_PATH = "/workspace/workflow.json"

TRIGGER_NAME = "Invoice Webhook"
EDIT_NAME = "Edit Fields"
MERGE_NAME = "Merge"
EMAIL_NAME = "Send Invoice Email"

# The starter export's own values for Edit Fields. The correct fix never
# touches this node - the bypass branch into Merge is what carries the
# binary, so the transform node is left completely alone.
EDIT_FIELDS_ORIGINAL_PARAMETERS = {
    "mode": "manual",
    "assignments": {
        "assignments": [
            {
                "id": "1",
                "name": "customerId",
                "type": "string",
                "value": "={{$json.body.customerId}}",
            },
            {
                "id": "2",
                "name": "status",
                "type": "string",
                "value": "processed",
            },
        ]
    },
}


def load_workflow():
    with open(WORKFLOW_PATH) as f:
        return json.load(f)


def get_node(workflow, name):
    for node in workflow["nodes"]:
        if node["name"] == name:
            return node
    raise AssertionError(f"node {name!r} not found in workflow.json")


def incoming_edges(workflow, target_name):
    """List of (source_name, target_index) feeding target_name."""
    edges = []
    for src, outputs in workflow.get("connections", {}).items():
        for targets in outputs.get("main", []):
            for t in targets:
                if t.get("node") == target_name:
                    edges.append((src, t.get("index", 0)))
    return edges


def test_node_set_and_core_config_preserved():
    workflow = load_workflow()
    names = {n["name"] for n in workflow["nodes"]}
    assert names == {TRIGGER_NAME, EDIT_NAME, MERGE_NAME, EMAIL_NAME}, (
        f"node set changed unexpectedly: {names}"
    )

    merge = get_node(workflow, MERGE_NAME)
    assert merge["parameters"].get("mode") == "combine"
    assert merge["parameters"].get("combineBy") == "combineByPosition"

    edit_fields = get_node(workflow, EDIT_NAME)
    assert edit_fields["parameters"] == EDIT_FIELDS_ORIGINAL_PARAMETERS, (
        f"{EDIT_NAME} doesn't need to change to fix the attachment - the bypass "
        f"branch into {MERGE_NAME} is what carries the binary through. Its "
        "parameters (including any new pass-through/options flag) must stay "
        "exactly as exported."
    )


def test_original_connections_preserved():
    workflow = load_workflow()

    assert (TRIGGER_NAME, 0) in incoming_edges(workflow, EDIT_NAME), (
        f"{TRIGGER_NAME} -> {EDIT_NAME} connection is missing or moved"
    )
    assert (MERGE_NAME, 0) in incoming_edges(workflow, EMAIL_NAME), (
        f"{MERGE_NAME} -> {EMAIL_NAME} connection is missing or moved"
    )
    assert (EDIT_NAME, 1) in incoming_edges(workflow, MERGE_NAME), (
        f"{EDIT_NAME} -> {MERGE_NAME} connection is missing or moved"
    )


def test_trigger_connections_share_single_output_port():
    """Invoice Webhook has exactly one physical output pin. Every node it
    feeds must be a sibling entry inside connections[...]['main'][0] - a
    target appended as a *new* item in the outer 'main' list models a second
    output pin the node doesn't have, so n8n never fires it: the wire looks
    present in the JSON but is functionally dead.
    """
    workflow = load_workflow()
    ports = workflow.get("connections", {}).get(TRIGGER_NAME, {}).get("main", [])
    assert len(ports) == 1, (
        f"{TRIGGER_NAME}['main'] has {len(ports)} output-port entries, but "
        f"{TRIGGER_NAME} only has one real output - every downstream connection "
        "belongs inside the single existing port list (index 0), not a new "
        "entry appended after it"
    )
    targets = {t.get("node") for t in ports[0]}
    assert {EDIT_NAME, MERGE_NAME}.issubset(targets), (
        f"{TRIGGER_NAME} must feed both {EDIT_NAME} and {MERGE_NAME} from its "
        "single output port"
    )


def test_binary_bypasses_edit_fields_into_merge():
    workflow = load_workflow()
    merge_inputs = incoming_edges(workflow, MERGE_NAME)
    sources = {src for src, _idx in merge_inputs}

    assert TRIGGER_NAME in sources, (
        f"{MERGE_NAME} never receives a direct connection from {TRIGGER_NAME}, "
        f"so the original binary attachment has no way back into the item "
        f"once {EDIT_NAME} drops it"
    )

    relevant_indexes = [idx for src, idx in merge_inputs if src in (TRIGGER_NAME, EDIT_NAME)]
    assert len(relevant_indexes) >= 2 and len(set(relevant_indexes)) == len(relevant_indexes), (
        f"{TRIGGER_NAME} and {EDIT_NAME} must land on two distinct {MERGE_NAME} "
        "inputs, not the same one"
    )

    merge = get_node(workflow, MERGE_NAME)
    num_inputs = merge["parameters"].get("numberOfInputs", 2)
    assert all(0 <= idx < num_inputs for idx in relevant_indexes), (
        f"{MERGE_NAME} input index out of range for numberOfInputs={num_inputs}"
    )


def test_email_reads_the_binary_slot_the_webhook_actually_used():
    workflow = load_workflow()
    producer_slot = get_node(workflow, TRIGGER_NAME)["parameters"].get("binaryPropertyName")
    consumer_slot = get_node(workflow, EMAIL_NAME)["parameters"].get("binaryPropertyName")

    assert producer_slot, f"{TRIGGER_NAME} lost its own binaryPropertyName parameter"
    assert consumer_slot == producer_slot, (
        f"{EMAIL_NAME} looks for the attachment under {consumer_slot!r} but "
        f"{TRIGGER_NAME} puts it under {producer_slot!r} - the names have to match"
    )
