#!/bin/bash
# Computes the missing operation-specific parameters for each node in
# /workspace/workflow.json by reading the reference values that already
# exist in /workspace/context.json (does not hardcode the final JSON).
set -euo pipefail

python3 - <<'PY'
import json

WORKFLOW_PATH = "/workspace/workflow.json"
CONTEXT_PATH = "/workspace/context.json"

with open(WORKFLOW_PATH) as f:
    workflow = json.load(f)
with open(CONTEXT_PATH) as f:
    context = json.load(f)

nodes = {n["name"]: n for n in workflow["nodes"]}

# "post" needs a destination channel to send the new message into.
post_node = nodes["Post Task Notification"]
post_node["parameters"]["channel"] = context["targetChannel"]

# "update" needs to identify which existing message to edit, via messageId,
# not the channel a "post" operation would need.
update_node = nodes["Update Task Status"]
update_node["parameters"]["messageId"] = context["originalMessageTs"]

# POSTing a JSON body requires enabling the full chain: sendBody -> body ->
# body.contentType -> body.content, each link visible/required only once the
# previous one is set.
http_node = nodes["Send Contact Webhook"]
http_node["parameters"]["sendBody"] = True
http_node["parameters"]["body"] = {
    "contentType": "json",
    "content": {
        "name": context["contact"]["name"],
        "email": context["contact"]["email"],
    },
}

with open(WORKFLOW_PATH, "w") as f:
    json.dump(workflow, f, indent=2)
    f.write("\n")

print("updated", WORKFLOW_PATH)
PY
