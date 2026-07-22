#!/bin/bash
# Computes the human-review configuration for the `hitl_review` node in
# /workspace/workflow.json from the actual parameters already present on the
# `tool_refund` node it guards (does not hardcode the final JSON).
set -euo pipefail

python3 - <<'PY'
import json

PATH = "/workspace/workflow.json"

with open(PATH) as f:
    workflow = json.load(f)

nodes_by_id = {n["id"]: n for n in workflow["nodes"]}
tool_node = nodes_by_id["tool_refund"]
hitl_node = nodes_by_id["hitl_review"]

# Only the parameters relevant to the human's decision (not plumbing like `url`).
relevant_keys = [k for k in tool_node["parameters"] if k != "url"]


def expr(key):
    return "{{ $tool.parameters.%s }}" % key


value_bits = " ".join(expr(k) for k in relevant_keys)

hitl_node["name"] = "Review refund method choice"
hitl_node["parameters"] = {
    "toolDescription": "Ask a human whether to refund %s to the customer's original "
    "payment method or issue the same amount as store credit instead." % value_bits,
    "responseType": "approval",
    "approvalOptions": {
        "values": {
            "approvalType": "double",
            "approveLabel": "=Refund %s via original payment method" % value_bits,
            "disapproveLabel": "=Issue %s as store credit instead" % value_bits,
        }
    },
}

with open(PATH, "w") as f:
    json.dump(workflow, f, indent=2)
    f.write("\n")

print("updated", PATH)
PY
