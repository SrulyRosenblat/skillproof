#!/bin/bash
# Computes the fix for /workspace/workflow.json against /workspace/sample_input.json.
# Nothing here is hardcoded to specific field names or values - the webhook-path
# fix derives a slug from the node's own name, and the field-expression fix
# works generically by testing, for each $json.<path> expression, whether that
# path actually resolves against the sample payload at the root or has to be
# nested one level under "body" - it never assumes which fields exist.
set -euo pipefail

python3 - <<'PY'
import json
import re

WORKFLOW_PATH = "/workspace/workflow.json"
SAMPLE_INPUT_PATH = "/workspace/sample_input.json"

with open(WORKFLOW_PATH) as f:
    workflow = json.load(f)
with open(SAMPLE_INPUT_PATH) as f:
    sample = json.load(f)


def is_expression(value):
    return isinstance(value, str) and value.startswith("=")


def unwrap(text):
    """Collapse any number of nested {{ ... }} layers down to the bare
    inner template, e.g. "{{ {{$json.x}} }}" -> "$json.x"."""
    text = text.strip()
    while True:
        m = re.fullmatch(r"\{\{\s*(.+?)\s*\}\}", text, re.DOTALL)
        if not m:
            return text
        inner = m.group(1).strip()
        if inner == text:
            return text
        text = inner


def resolvable(data, parts):
    cur = data
    for part in parts:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False
    return True


def fix_field_value(value):
    if not is_expression(value):
        return value
    inner = unwrap(value[1:])
    m = re.fullmatch(r"\$json((?:\.[A-Za-z0-9_]+)+)", inner)
    if not m:
        return value
    parts = m.group(1).lstrip(".").split(".")
    if resolvable(sample, parts):
        fixed_parts = parts
    elif resolvable(sample, ["body"] + parts):
        fixed_parts = ["body"] + parts
    else:
        fixed_parts = parts
    return "={{ $json." + ".".join(fixed_parts) + " }}"


for node in workflow["nodes"]:
    if node["type"] == "n8n-nodes-base.webhook":
        path = node["parameters"].get("path", "")
        if is_expression(path) or "{{" in path:
            slug = re.sub(r"[^a-z0-9]+", "-", node["name"].lower()).strip("-")
            node["parameters"]["path"] = slug or "webhook"
    if node["type"] == "n8n-nodes-base.set":
        for field in node["parameters"].get("fields", []):
            field["value"] = fix_field_value(field["value"])

with open(WORKFLOW_PATH, "w") as f:
    json.dump(workflow, f, indent=2)
    f.write("\n")

print("fixed workflow.json")
PY
