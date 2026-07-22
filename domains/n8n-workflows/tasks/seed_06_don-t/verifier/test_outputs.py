"""Deterministic checks on /workspace/workflow.json after it's been fixed.

Resolution of each field's expression is done against the payload actually
present in /workspace/sample_input.json, never against a hardcoded literal,
so a fix that gets the right shape by luck but the wrong procedure still
gets caught.
"""
import json
import re

WORKFLOW_PATH = "/workspace/workflow.json"
SAMPLE_INPUT_PATH = "/workspace/sample_input.json"


def load_workflow():
    with open(WORKFLOW_PATH) as f:
        return json.load(f)


def load_sample_input():
    with open(SAMPLE_INPUT_PATH) as f:
        return json.load(f)


def get_node(workflow, name):
    for node in workflow["nodes"]:
        if node["name"] == name:
            return node
    raise AssertionError(f"node {name!r} not found in workflow.json")


def get_field(node, name):
    for field in node["parameters"]["fields"]:
        if field["name"] == name:
            return field
    raise AssertionError(f"field {name!r} not found on node {node['name']!r}")


def resolve_expression(value, json_data):
    """Mirrors n8n's own resolution of a dynamic field: the value must be
    prefixed with '=' and wrap exactly one {{ ... }} template referencing
    $json.<dotted.path>. Extra nested braces or an unresolvable path fail
    to resolve, exactly as they would inside n8n itself."""
    assert isinstance(value, str) and value.startswith("="), f"not an expression: {value!r}"
    body = value[1:].strip()
    m = re.fullmatch(r"\{\{\s*(.+?)\s*\}\}", body, re.DOTALL)
    assert m, f"expression is not a single {{{{ }}}}-wrapped template: {value!r}"
    inner = m.group(1)
    m2 = re.fullmatch(r"\$json((?:\.[A-Za-z0-9_]+)+)", inner)
    assert m2, f"unsupported or malformed expression body: {inner!r}"
    cur = json_data
    for part in m2.group(1).lstrip(".").split("."):
        assert isinstance(cur, dict) and part in cur, (
            f"field not found while resolving {value!r}: no {part!r} at this level"
        )
        cur = cur[part]
    return cur


def test_webhook_path_is_a_static_string():
    workflow = load_workflow()
    webhook = get_node(workflow, "Webhook")
    path = webhook["parameters"]["path"]
    assert isinstance(path, str) and path, "webhook path must be a non-empty string"
    assert not path.startswith("="), f"webhook path must not be an n8n expression: {path!r}"
    assert "{{" not in path and "}}" not in path, f"webhook path must be static, not a template: {path!r}"

    # Registering *some* static string would silence n8n, but that's not the same
    # as fixing the parameter: the replacement has to actually be tied to what was
    # there before (the node itself, or the literal text the broken expression was
    # already built around) rather than an unrelated label invented from scratch.
    node_slug = re.sub(r"[^a-z0-9]+", "-", webhook["name"].lower()).strip("-")
    original_literal_suffix = "webhook"  # the non-expression tail of "={{$json.user_id}}/webhook"
    allowed = {node_slug, original_literal_suffix, "user-webhook", "my-webhook"}
    normalized = path.strip("/").lower()
    assert normalized in allowed, (
        f"webhook path {path!r} is static but reads as an invented label rather than a fix "
        f"tied to the node or to the broken expression it replaced (expected one of {sorted(allowed)})"
    )


def test_order_id_resolves_against_the_actual_webhook_payload():
    workflow = load_workflow()
    sample = load_sample_input()
    field = get_field(get_node(workflow, "Format Order"), "order_id")
    resolved = resolve_expression(field["value"], sample)
    assert resolved == sample["body"]["order_id"]


def test_customer_name_is_wrapped_exactly_once_and_resolves_correctly():
    workflow = load_workflow()
    sample = load_sample_input()
    field = get_field(get_node(workflow, "Format Order"), "customer_name")
    value = field["value"]
    assert value.count("{{") == 1 and value.count("}}") == 1, (
        f"expression must wrap its template exactly once, got {value!r}"
    )
    resolved = resolve_expression(value, sample)
    assert resolved == sample["body"]["customer_name"]


def test_already_correct_fields_are_left_alone():
    workflow = load_workflow()
    sample = load_sample_input()
    node = get_node(workflow, "Format Order")
    status_value = get_field(node, "status")["value"]
    assert resolve_expression(status_value, sample) == sample["body"]["status"]
    source_field = get_field(node, "source")
    assert source_field["value"] == "webhook-order-flow", (
        "the static 'source' field was already correct and must not be turned into an expression"
    )


def test_workflow_structure_is_unchanged():
    workflow = load_workflow()
    names = {n["name"] for n in workflow["nodes"]}
    assert names == {"Webhook", "Format Order"}, f"node set must not change, got {names}"

    types = {n["name"]: n["type"] for n in workflow["nodes"]}
    assert types["Webhook"] == "n8n-nodes-base.webhook"
    assert types["Format Order"] == "n8n-nodes-base.set"

    assert workflow["connections"] == {
        "Webhook": {"main": [[{"node": "Format Order", "type": "main", "index": 0}]]}
    }, "connections between Webhook and Format Order must not be altered"
