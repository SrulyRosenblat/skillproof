#!/bin/bash
# Computes the fix for /workspace/workflow.json by reading the workflow's own
# graph and parameters (does not hardcode node names' values or a literal
# binary-slot string).
set -euo pipefail

python3 - <<'PY'
import json

WORKFLOW_PATH = "/workspace/workflow.json"

with open(WORKFLOW_PATH) as f:
    workflow = json.load(f)

nodes = {n["name"]: n for n in workflow["nodes"]}
connections = workflow.setdefault("connections", {})

def incoming_edges(target_name):
    edges = []
    for src, outputs in connections.items():
        for targets in outputs.get("main", []):
            for t in targets:
                if t.get("node") == target_name:
                    edges.append((src, t.get("index", 0)))
    return edges

# The trigger is whichever node never shows up as a connection target.
target_names = {name for name in nodes if incoming_edges(name)}
trigger_candidates = [n for n in nodes if n not in target_names]
assert len(trigger_candidates) == 1, trigger_candidates
trigger_name = trigger_candidates[0]
producer_slot = nodes[trigger_name]["parameters"].get("binaryPropertyName", "data")

# The merge node is identified by its node type, not by a hardcoded name.
merge_name = next(n for n, node in nodes.items() if "merge" in node["type"].lower())
merge_node = nodes[merge_name]
num_inputs = merge_node["parameters"].get("numberOfInputs", 2)

merge_inputs = incoming_edges(merge_name)
used_indexes = {idx for _src, idx in merge_inputs}
free_indexes = [i for i in range(num_inputs) if i not in used_indexes]
assert free_indexes, f"{merge_name} has no free input slot to bypass into"
bypass_index = free_indexes[0]

already_wired = any(src == trigger_name for src, _idx in merge_inputs)
if not already_wired:
    connections.setdefault(trigger_name, {}).setdefault("main", [[]])
    connections[trigger_name]["main"][0].append(
        {"node": merge_name, "type": "main", "index": bypass_index}
    )

# The sink is whichever node is never a connection source, and is the one
# consumer that names a binary slot of its own to read from.
source_names = set(connections.keys())
sink_candidates = [
    n for n, node in nodes.items()
    if n not in source_names and "binaryPropertyName" in node.get("parameters", {})
]
assert len(sink_candidates) == 1, sink_candidates
sink_name = sink_candidates[0]
nodes[sink_name]["parameters"]["binaryPropertyName"] = producer_slot

with open(WORKFLOW_PATH, "w") as f:
    json.dump(workflow, f, indent=2)
    f.write("\n")

print(
    f"wired {trigger_name} -> {merge_name} @ input {bypass_index}; "
    f"{sink_name}.binaryPropertyName = {producer_slot!r}"
)
PY
