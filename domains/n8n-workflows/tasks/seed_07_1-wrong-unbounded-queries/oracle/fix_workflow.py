#!/usr/bin/env python3
"""
Computes a corrected version of /workspace/workflow.json in place.

This locates the relevant nodes by their semantic role (node type + operation
+ target table), not by fixed names or array position, and mutates only what
is required to satisfy the task's behavioral requirements:

  * the schedule trigger must carry an explicit timezone
  * the Data Table "get" step reading error_buffer must be able to return
    every currently buffered row, and must not silently drop the run when
    the buffer happens to be empty
  * the deletion step must use the real "deleteRows" operation and must
    remove rows by the specific ids that were just read (never a broad
    re-query), so a row written concurrently during the flush survives
  * exactly one summary row must reach flush_runs per run regardless of how
    many rows were flushed, which requires collapsing the per-row branch
    down to a single item before the summary insert
  * the historical-archive dashboard query must be bounded
"""
import json

WORKFLOW_PATH = "/workspace/workflow.json"


def find_node(nodes, predicate):
    for n in nodes:
        if predicate(n):
            return n
    return None


def main():
    with open(WORKFLOW_PATH) as f:
        wf = json.load(f)

    nodes = wf["nodes"]
    connections = wf.setdefault("connections", {})

    # --- 1. Explicit timezone on the schedule trigger -----------------
    trigger = find_node(nodes, lambda n: n["type"] == "n8n-nodes-base.scheduleTrigger")
    trigger["parameters"]["rule"]["timezone"] = "America/New_York"

    # --- 2. Get step: must be able to see ALL buffered rows, and must
    #        keep the chain alive even when it matches zero rows --------
    get_node = find_node(
        nodes,
        lambda n: n["type"] == "n8n-nodes-base.dataTable"
        and n.get("parameters", {}).get("operation") == "get"
        and n.get("parameters", {}).get("dataTableId", {}).get("value") == "error_buffer",
    )
    get_node["parameters"]["filters"] = {
        "conditions": [{"keyName": "id", "condition": "isNotEmpty"}]
    }
    get_node["parameters"]["matchType"] = "anyCondition"
    get_node["parameters"]["returnAll"] = True
    get_node["alwaysOutputData"] = True
    get_name = get_node["name"]

    # --- 3. Delete step: real operation name, delete by the exact ids
    #        just read (not a broad re-query), keep the chain alive -----
    delete_node = find_node(
        nodes,
        lambda n: n["type"] == "n8n-nodes-base.dataTable"
        and n.get("parameters", {}).get("dataTableId", {}).get("value") == "error_buffer"
        and n.get("parameters", {}).get("operation") in ("delete", "deleteRows"),
    )
    delete_node["parameters"]["operation"] = "deleteRows"
    delete_node["parameters"]["filters"] = {
        "conditions": [{"keyName": "id", "condition": "eq", "keyValue": "={{ $json.id }}"}]
    }
    delete_node["parameters"]["matchType"] = "allConditions"
    delete_node["alwaysOutputData"] = True
    delete_name = delete_node["name"]

    # --- 4. Summary insert: must fire exactly once per run regardless
    #        of how many rows were flushed -> insert a collapsing Code
    #        node between the delete step and the summary insert --------
    summary_node = find_node(
        nodes,
        lambda n: n["type"] == "n8n-nodes-base.dataTable"
        and n.get("parameters", {}).get("dataTableId", {}).get("value") == "flush_runs"
        and n.get("parameters", {}).get("operation") == "insert",
    )
    summary_name = summary_node["name"]

    collapse_name = "Collapse To Single Run"
    if not any(n["name"] == collapse_name for n in nodes):
        nodes.append(
            {
                "name": collapse_name,
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [910, 220],
                "parameters": {
                    "jsCode": "return [{ json: {} }];"
                },
            }
        )

    # Rewire: delete_node -> collapse -> summary_node (instead of
    # delete_node -> summary_node directly).
    connections[delete_name] = {
        "main": [[{"node": collapse_name, "type": "main", "index": 0}]]
    }
    connections[collapse_name] = {
        "main": [[{"node": summary_name, "type": "main", "index": 0}]]
    }

    # --- 5. Bound the historical-archive dashboard query ----------------
    sql_node = find_node(nodes, lambda n: n["type"] == "n8n-nodes-base.postgres")
    query = sql_node["parameters"]["query"]
    if "limit" not in query.lower():
        sql_node["parameters"]["query"] = query.rstrip().rstrip(";") + " LIMIT 500"

    with open(WORKFLOW_PATH, "w") as f:
        json.dump(wf, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
