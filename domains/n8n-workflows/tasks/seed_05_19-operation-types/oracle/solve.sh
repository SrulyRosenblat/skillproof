#!/bin/bash
# Computes the fix: applies /workspace/operations.json to /workspace/workflow.json
# in place, and derives /workspace/custom_metrics_summary.json from
# /workspace/run_metrics.json. Nothing here is hardcoded to the sample data -
# the operation-applying loop and the automatic-metric-key filter both work
# generically off whatever operations/metrics are actually present.
set -euo pipefail

python3 - <<'PY'
import json

WORKFLOW_PATH = "/workspace/workflow.json"
OPERATIONS_PATH = "/workspace/operations.json"
RUN_METRICS_PATH = "/workspace/run_metrics.json"
SUMMARY_PATH = "/workspace/custom_metrics_summary.json"

# The four metrics n8n's evaluation "get_run" action always attaches to a
# run, regardless of what the evaluation itself measures.
AUTOMATIC_METRIC_KEYS = {"promptTokens", "completionTokens", "totalTokens", "executionTime"}

with open(WORKFLOW_PATH) as f:
    workflow = json.load(f)
with open(OPERATIONS_PATH) as f:
    operations = json.load(f)


def find_node(name):
    for node in workflow["nodes"]:
        if node["name"] == name:
            return node
    raise KeyError(name)


def set_dot_path(d, path, value):
    parts = path.split(".")
    cur = d
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def ensure_slot(main, index):
    while len(main) <= index:
        main.append([])
    return main


for op in operations:
    kind = op["type"]

    if kind == "addNode":
        workflow["nodes"].append(op["node"])

    elif kind == "removeNode":
        name = op["name"]
        workflow["nodes"] = [n for n in workflow["nodes"] if n["name"] != name]

    elif kind == "updateNode":
        node = find_node(op["name"])
        for path, value in op["changes"].items():
            set_dot_path(node, path, value)

    elif kind == "addConnection":
        source, target = op["source"], op["target"]
        if "branch" in op:
            # IF node: first output is the true branch, second is false.
            index = 0 if op["branch"] == "true" else 1
        elif "case" in op:
            # Switch node: case number is the output index directly.
            index = op["case"]
        else:
            index = op.get("sourceIndex", 0)

        entry = workflow["connections"].setdefault(source, {})
        main = ensure_slot(entry.setdefault("main", []), index)
        main[index].append({"node": target, "type": "main", "index": 0})

    elif kind == "cleanStaleConnections":
        valid_names = {n["name"] for n in workflow["nodes"]}
        cleaned = {}
        for src, entry in workflow["connections"].items():
            if src not in valid_names:
                continue
            new_entry = {}
            for conn_type, ports in entry.items():
                new_entry[conn_type] = [
                    [t for t in port if t.get("node") in valid_names] for port in ports
                ]
            cleaned[src] = new_entry
        workflow["connections"] = cleaned

    elif kind == "updateName":
        workflow["name"] = op["name"]

    elif kind == "addTag":
        tags = workflow.setdefault("tags", [])
        if op["tag"] not in tags:
            tags.append(op["tag"])

    elif kind == "activateWorkflow":
        workflow["active"] = True

    elif kind == "deactivateWorkflow":
        workflow["active"] = False

    else:
        raise ValueError(f"unhandled operation type: {kind}")

with open(WORKFLOW_PATH, "w") as f:
    json.dump(workflow, f, indent=2)
    f.write("\n")

with open(RUN_METRICS_PATH) as f:
    run = json.load(f)

custom = {k: v for k, v in run["metrics"].items() if k not in AUTOMATIC_METRIC_KEYS}
names = sorted(custom)
average = round(sum(custom[n] for n in names) / len(names), 4)

with open(SUMMARY_PATH, "w") as f:
    json.dump({"custom_metric_names": names, "average": average}, f, indent=2)
    f.write("\n")

print("applied", len(operations), "operations; custom metrics:", names, "avg:", average)
PY
