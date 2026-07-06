#!/usr/bin/env python3
"""Deterministic grader for the agent-browser TaskFlow Desktop task.

Verifies /workspace/result.json against a sync code computed by independently
driving the same agent-browser tool (in a scratch copy) through the correct
"attach the electron skill's window commands, check the correct task, sync"
sequence. This avoids duplicating the tool's internal transform logic here.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

WORKSPACE = os.getcwd()


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    result_path = os.path.join(WORKSPACE, "result.json")
    if not os.path.isfile(result_path):
        fail("result.json not found in /workspace")

    try:
        with open(result_path) as f:
            result = json.load(f)
    except Exception as e:
        fail(f"result.json is not valid JSON: {e}")

    if not isinstance(result, dict) or set(result.keys()) != {"task_id", "sync_code"}:
        fail(f"result.json must contain exactly the keys 'task_id' and 'sync_code', got: {result!r}")

    got_task_id = result["task_id"]
    got_sync_code = result["sync_code"]
    if not isinstance(got_task_id, str) or not got_task_id.strip():
        fail("task_id must be a non-empty string")
    if not isinstance(got_sync_code, str) or not got_sync_code.strip():
        fail("sync_code must be a non-empty string")

    for name in ("bin", "data"):
        src = os.path.join(WORKSPACE, name)
        if not os.path.isdir(src):
            fail(f"expected fixture directory missing: {name} (do not delete/rename input files)")

    with open(os.path.join(WORKSPACE, "data", "task_queue.json")) as f:
        tasks = json.load(f)

    pending = [t for t in tasks if t["status"] == "pending"]
    if not pending:
        fail("internal error: no pending tasks in fixture")
    expected_task = min(pending, key=lambda t: t["priority_rank"])
    expected_task_id = expected_task["id"]

    if got_task_id != expected_task_id:
        fail(f"task_id mismatch: expected the highest-priority pending task {expected_task_id!r}, got {got_task_id!r}")

    with tempfile.TemporaryDirectory() as tmp:
        for name in ("bin", "data"):
            shutil.copytree(os.path.join(WORKSPACE, name), os.path.join(tmp, name))

        def run(*args):
            return subprocess.run(
                ["python3", "bin/agent-browser", *args],
                cwd=tmp,
                capture_output=True,
                text=True,
            )

        run("skills", "get", "electron")
        r = run("window", "attach", "taskflow")
        if r.returncode != 0:
            fail(f"internal error driving reference tool (attach): {r.stderr}")

        tree = run("window", "tree")
        if tree.returncode != 0:
            fail(f"internal error driving reference tool (tree): {tree.stderr}")

        m = re.search(r'(@e\d+) checkbox "' + re.escape(expected_task["title"]) + r'"', tree.stdout)
        if not m:
            fail("internal error: could not locate expected task's checkbox ref in reference run")
        ref = m.group(1)

        r = run("window", "do", ref, "click")
        if r.returncode != 0:
            fail(f"internal error driving reference tool (check task): {r.stderr}")

        sync_m = re.search(r'(@e\d+) button "Sync"', tree.stdout)
        if not sync_m:
            fail("internal error: could not locate Sync button ref in reference run")
        sync_ref = sync_m.group(1)

        r = run("window", "do", sync_ref, "click")
        if r.returncode != 0:
            fail(f"internal error driving reference tool (sync): {r.stderr}")

        final_tree = run("window", "tree")
        if final_tree.returncode != 0:
            fail(f"internal error driving reference tool (final tree): {final_tree.stderr}")

    code_m = re.search(r'Sync code:\s*([^"\s]+)', final_tree.stdout)
    if not code_m:
        fail("internal error: reference run did not produce a sync code")
    expected_sync_code = code_m.group(1)

    if got_sync_code != expected_sync_code:
        fail(f"sync_code mismatch: expected {expected_sync_code!r}, got {got_sync_code!r}")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
