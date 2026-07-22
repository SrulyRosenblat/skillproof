"""Deterministic checks on /workspace/workflow.json.

Tests the produced artifact only: does each node carry the parameters its
own specific resource/operation/method actually needs (not the parameters a
*different* operation would need), sourced from the reference values in
context.json, and is the HTTP node's JSON-body dependency chain fully
enabled rather than partially configured.
"""
import json

WORKFLOW_PATH = "/workspace/workflow.json"
CONTEXT_PATH = "/workspace/context.json"


def load_workflow():
    with open(WORKFLOW_PATH) as f:
        return json.load(f)


def load_context():
    with open(CONTEXT_PATH) as f:
        return json.load(f)


def get_node(workflow, name):
    for node in workflow["nodes"]:
        if node["name"] == name:
            return node
    raise AssertionError(f"node {name!r} not found in workflow.json")


def test_structure_and_operations_preserved():
    workflow = load_workflow()
    names = {n["name"] for n in workflow["nodes"]}
    assert names == {
        "Post Task Notification",
        "Update Task Status",
        "Send Contact Webhook",
    }, f"node set changed unexpectedly: {names}"

    post = get_node(workflow, "Post Task Notification")
    update = get_node(workflow, "Update Task Status")
    http = get_node(workflow, "Send Contact Webhook")
    assert post["parameters"].get("operation") == "post"
    assert update["parameters"].get("operation") == "update"
    assert http["parameters"].get("method") == "POST"


def test_post_operation_has_its_required_fields():
    workflow = load_workflow()
    context = load_context()
    params = get_node(workflow, "Post Task Notification")["parameters"]

    assert params.get("channel") == context["targetChannel"], (
        "posting a new Slack message needs a destination channel"
    )
    assert isinstance(params.get("text"), str) and params["text"].strip()


def test_update_operation_has_its_own_required_fields_not_posts():
    workflow = load_workflow()
    context = load_context()
    params = get_node(workflow, "Update Task Status")["parameters"]

    assert params.get("messageId") == context["originalMessageTs"], (
        "updating an existing Slack message needs to identify which message "
        "via messageId - the channel a 'post' would need isn't enough here"
    )
    assert isinstance(params.get("text"), str) and params["text"].strip()


def test_http_request_body_chain_fully_enabled():
    workflow = load_workflow()
    params = get_node(workflow, "Send Contact Webhook")["parameters"]

    assert params.get("sendBody") is True, (
        "sending a body on a POST request requires sendBody to be explicitly enabled"
    )
    body = params.get("body")
    assert isinstance(body, dict), "sendBody=true requires a body object"
    assert body.get("contentType") == "json", "a JSON body requires contentType='json'"
    content = body.get("content")
    assert isinstance(content, dict), (
        "contentType='json' requires an actual content object, not a raw string"
    )


def test_http_request_content_matches_contact_record():
    workflow = load_workflow()
    context = load_context()
    content = get_node(workflow, "Send Contact Webhook")["parameters"]["body"]["content"]

    assert content.get("name") == context["contact"]["name"]
    assert content.get("email") == context["contact"]["email"]
