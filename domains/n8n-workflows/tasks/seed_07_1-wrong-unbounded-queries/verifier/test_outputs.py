"""
Deterministic behavioral verifier for the "Nightly Error Buffer Flush" n8n
workflow task.

Rather than grepping the produced workflow.json for magic strings, this file
implements a small, generic n8n-workflow graph executor and actually RUNS the
candidate workflow against controlled in-memory "Data Table" state for several
scenarios (normal flush, empty buffer, concurrent-write-during-flush), plus a
mock SQL executor for the historical-archive query. Assertions are made purely
on the resulting data state / return values, never on node names or source
text.
"""
import json
import re
from collections import deque

import pytest

WORKFLOW_PATH = "/workspace/workflow.json"

VALID_ROW_OPS = {"insert", "get", "update", "upsert", "deleteRows", "rowExists", "rowNotExists"}

EXPR_RE = re.compile(r"^=\{\{\s*\$json\.(\w+)\s*\}\}$")


def load_workflow():
    with open(WORKFLOW_PATH) as f:
        return json.load(f)


class DataStore:
    def __init__(self):
        self.tables = {}
        self._id_counters = {}
        self.big_table_size = 2_500_000
        self.last_sql_returned = None

    def get_table(self, name):
        return self.tables.setdefault(name, [])

    def next_id(self, name):
        self._id_counters[name] = self._id_counters.get(name, 0) + 1
        return self._id_counters[name]

    def insert(self, table, values):
        row = dict(values)
        row["id"] = self.next_id(table)
        self.get_table(table).append(row)
        return row


def resolve_value(val, json_ctx):
    if isinstance(val, str):
        m = EXPR_RE.match(val)
        if m:
            return json_ctx.get(m.group(1))
    return val


def match_condition(row, cond):
    key = cond["keyName"]
    op = cond["condition"]
    val = cond.get("keyValue")
    v = row.get(key)
    if op == "eq":
        return v == val
    if op == "neq":
        return v != val
    if op == "like":
        return val is not None and str(val) in str(v)
    if op == "ilike":
        return val is not None and str(val).lower() in str(v).lower()
    if op == "gt":
        return v is not None and val is not None and v > val
    if op == "gte":
        return v is not None and val is not None and v >= val
    if op == "lt":
        return v is not None and val is not None and v < val
    if op == "lte":
        return v is not None and val is not None and v <= val
    if op == "isEmpty":
        return v is None or v == ""
    if op == "isNotEmpty":
        return v is not None and v != ""
    if op == "isTrue":
        return v is True
    if op == "isFalse":
        return v is False
    raise ValueError(f"unknown condition operator: {op!r}")


def match_filters(row, resolved_conditions, match_type):
    if not resolved_conditions:
        raise ValueError("At least one condition is required")
    results = [match_condition(row, c) for c in resolved_conditions]
    return all(results) if match_type == "allConditions" else any(results)


def run_data_table_node(node, input_items, store):
    params = node.get("parameters", {})
    op = params.get("operation")
    if op not in VALID_ROW_OPS:
        raise ValueError(f"unknown data table operation: {op!r}")
    table_name = params.get("dataTableId", {}).get("value")
    raw_output = []

    if op == "insert":
        for it in input_items:
            json_ctx = it.get("json", {})
            values = {
                k: resolve_value(v, json_ctx)
                for k, v in params.get("columns", {}).get("value", {}).items()
            }
            row = store.insert(table_name, values)
            raw_output.append({"json": row})
    else:
        filters = params.get("filters", {})
        match_type = filters.get("matchType", "anyCondition")
        base_conditions = filters.get("conditions", [])
        for it in input_items:
            json_ctx = it.get("json", {})
            resolved_conditions = [
                dict(c, keyValue=resolve_value(c.get("keyValue"), json_ctx))
                for c in base_conditions
            ]
            table = store.get_table(table_name)
            matched = [r for r in table if match_filters(r, resolved_conditions, match_type)]

            if op == "get":
                raw_output.extend({"json": dict(r)} for r in matched)
            elif op == "deleteRows":
                for r in matched:
                    table.remove(r)
                raw_output.extend({"json": dict(r)} for r in matched)
            elif op in ("update", "upsert"):
                col_values = params.get("columns", {}).get("value", {})
                if matched:
                    for r in matched:
                        for k, v in col_values.items():
                            r[k] = resolve_value(v, json_ctx)
                        raw_output.append({"json": dict(r)})
                elif op == "upsert":
                    values = {k: resolve_value(v, json_ctx) for k, v in col_values.items()}
                    row = store.insert(table_name, values)
                    raw_output.append({"json": row})
            elif op == "rowExists":
                if matched:
                    raw_output.append(it)
            elif op == "rowNotExists":
                if not matched:
                    raw_output.append(it)

    if not raw_output and node.get("alwaysOutputData"):
        raw_output = [{"json": {}}]
    return raw_output


def run_code_node(node, input_items):
    if not input_items:
        return [{"json": {}}] if node.get("alwaysOutputData") else []
    return [{"json": {}}]


def run_sql_node(node, store):
    query = node.get("parameters", {}).get("query", "")
    m = re.search(r"limit\s+(\d+)", query, re.IGNORECASE)
    if m:
        n_returned = min(int(m.group(1)), store.big_table_size)
    else:
        n_returned = store.big_table_size
    store.last_sql_returned = n_returned
    return [{"json": {}}]


def topo_order(nodes_by_name, connections):
    indegree = {name: 0 for name in nodes_by_name}
    edges = {name: [] for name in nodes_by_name}
    for src, conn in connections.items():
        for output_list in conn.get("main") or []:
            for edge in output_list or []:
                dst = edge["node"]
                edges.setdefault(src, []).append(dst)
                indegree[dst] = indegree.get(dst, 0) + 1
    queue = deque(n for n in nodes_by_name if indegree.get(n, 0) == 0)
    order = []
    seen = set()
    while queue:
        n = queue.popleft()
        if n in seen:
            continue
        seen.add(n)
        order.append(n)
        for dst in edges.get(n, []):
            indegree[dst] -= 1
            if indegree[dst] == 0:
                queue.append(dst)
    return order


def build_incoming(nodes_by_name, connections):
    incoming = {name: [] for name in nodes_by_name}
    for src, conn in connections.items():
        for output_list in conn.get("main") or []:
            for edge in output_list or []:
                incoming.setdefault(edge["node"], []).append(src)
    return incoming


def find_get_error_buffer_node(nodes_by_name):
    for name, n in nodes_by_name.items():
        if n["type"] == "n8n-nodes-base.dataTable":
            p = n.get("parameters", {})
            if p.get("operation") == "get" and p.get("dataTableId", {}).get("value") == "error_buffer":
                return name
    return None


def execute_run(workflow, store, mid_flush_injection=None):
    """Run the workflow once against `store`. If `mid_flush_injection` is
    given, it is called with `store` right after the first node that reads
    error_buffer (operation "get") has executed, simulating a concurrent
    writer adding a row while the flush is still in progress."""
    nodes_by_name = {n["name"]: n for n in workflow["nodes"]}
    connections = workflow.get("connections", {})
    order = topo_order(nodes_by_name, connections)
    incoming = build_incoming(nodes_by_name, connections)
    outputs = {}

    hook_target = find_get_error_buffer_node(nodes_by_name) if mid_flush_injection else None
    hook_fired = False

    trigger_names = {n["name"] for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.scheduleTrigger"}

    for name in order:
        node = nodes_by_name[name]
        ntype = node["type"]
        if name in trigger_names:
            result = [{"json": {}}]
        else:
            input_items = []
            for src in incoming.get(name, []):
                input_items.extend(outputs.get(src, []))
            if ntype == "n8n-nodes-base.dataTable":
                result = run_data_table_node(node, input_items, store)
            elif ntype == "n8n-nodes-base.code":
                result = run_code_node(node, input_items)
            elif ntype == "n8n-nodes-base.postgres":
                result = run_sql_node(node, store)
            else:
                raise ValueError(f"unsupported node type: {ntype!r}")
        outputs[name] = result

        if mid_flush_injection and not hook_fired and name == hook_target:
            mid_flush_injection(store)
            hook_fired = True

    return outputs


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def test_schedule_trigger_has_explicit_timezone_and_correct_time():
    wf = load_workflow()
    trigger = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.scheduleTrigger")
    rule = trigger["parameters"]["rule"]
    interval = rule["interval"][0]
    assert interval.get("field") == "hours" and interval.get("hoursInterval") == 24
    assert rule.get("hour") == 9
    assert rule.get("minute") == 0
    assert rule.get("timezone") == "America/New_York"


def test_normal_flush_clears_buffer_and_records_exactly_one_summary():
    wf = load_workflow()
    store = DataStore()
    store.tables["error_buffer"] = [
        {"id": 1, "message": "boom"},
        {"id": 2, "message": "kaboom"},
    ]
    store._id_counters["error_buffer"] = 2

    execute_run(wf, store)

    assert store.get_table("error_buffer") == []
    assert len(store.get_table("flush_runs")) == 1


def test_empty_buffer_run_still_records_exactly_one_summary():
    wf = load_workflow()
    store = DataStore()
    # error_buffer starts completely empty this run.

    execute_run(wf, store)

    assert store.get_table("error_buffer") == []
    assert len(store.get_table("flush_runs")) == 1


def test_row_added_during_flush_is_not_lost():
    wf = load_workflow()
    store = DataStore()
    store.tables["error_buffer"] = [
        {"id": 1, "message": "boom"},
        {"id": 2, "message": "kaboom"},
    ]
    store._id_counters["error_buffer"] = 2

    def inject_concurrent_row(s):
        s.insert("error_buffer", {"message": "landed mid-flush"})

    execute_run(wf, store, mid_flush_injection=inject_concurrent_row)

    remaining = store.get_table("error_buffer")
    assert len(remaining) == 1
    assert remaining[0]["message"] == "landed mid-flush"
    assert len(store.get_table("flush_runs")) == 1


def test_dashboard_query_never_pulls_more_than_5000_rows():
    wf = load_workflow()
    store = DataStore()
    store.big_table_size = 2_500_000

    execute_run(wf, store)

    assert store.last_sql_returned is not None
    assert store.last_sql_returned <= 5000
