#!/usr/bin/env python3
"""Deterministic grader for the agent-browser employee-portal task.

Verifies /workspace/result.json against a confirmation code computed by
independently driving the same agent-browser tool (in a scratch copy) through
the correct login sequence. This avoids duplicating the tool's internal
transform logic in the grader.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

WORKSPACE = os.getcwd()
EMPLOYEE_NAME = "Jordan Blake"


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

    if not isinstance(result, dict) or set(result.keys()) != {"confirmation_code"}:
        fail(f"result.json must contain exactly the key 'confirmation_code', got: {result!r}")

    got = result["confirmation_code"]
    if not isinstance(got, str) or not got.strip():
        fail("confirmation_code must be a non-empty string")

    for name in ("bin", "site", "data"):
        src = os.path.join(WORKSPACE, name)
        if not os.path.isdir(src):
            fail(f"expected fixture directory missing: {name} (do not delete/rename input files)")

    with tempfile.TemporaryDirectory() as tmp:
        for name in ("bin", "site", "data"):
            shutil.copytree(os.path.join(WORKSPACE, name), os.path.join(tmp, name))

        def run(*args):
            return subprocess.run(
                ["python3", "bin/agent-browser", *args],
                cwd=tmp,
                capture_output=True,
                text=True,
            )

        run("skills", "get", "core")
        r = run("open", "site/portal.html")
        if r.returncode != 0:
            fail(f"internal error driving reference tool (open): {r.stderr}")

        with open(os.path.join(tmp, "data", "employee_directory.json")) as f:
            directory = json.load(f)
        access_code = directory[EMPLOYEE_NAME]["access_code"]

        run("act", "@e1", "fill", EMPLOYEE_NAME)
        run("act", "@e2", "fill", access_code)
        r = run("act", "@e3", "click")
        if r.returncode != 0:
            fail(f"internal error driving reference tool (click): {r.stderr}")

        snap = run("snapshot")
        if snap.returncode != 0:
            fail(f"internal error driving reference tool (snapshot): {snap.stderr}")

    m = re.search(r'Confirmation Code:\s*([^"\s]+)', snap.stdout)
    if not m:
        fail("internal error: reference run did not produce a confirmation code")
    expected = m.group(1)

    if got != expected:
        fail(f"confirmation_code mismatch: expected {expected!r}, got {got!r}")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
