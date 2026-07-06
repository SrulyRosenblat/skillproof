"""Tool definitions + dispatch for the model-under-test agent loop.

Tools execute inside the sandbox container; results are returned to the model as
JSON strings. Errors never raise — they come back as {"error": ...} so a bad tool
call costs the model a turn, not the trial.
"""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

from ..sandbox.container import SKILL_MOUNT, WORKSPACE, Sandbox

_SKILL_PATH_RE = re.compile(r"/skill(?:/[\w.@%+-]+)*")

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a bash command in the sandbox (cwd=/workspace, no network).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Max seconds (default 60, max 300)",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a text file under /workspace (parent dirs created).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to /workspace"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file under /workspace (or /skill when available).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to /workspace, or an absolute "
                        "/workspace/... or /skill/... path",
                    },
                    "offset_bytes": {"type": "integer"},
                    "limit_bytes": {"type": "integer", "description": "Default 20000"},
                },
                "required": ["path"],
            },
        },
    },
]


def _resolve_path(path: str, roots: tuple[str, ...]) -> str:
    """Jail a model-supplied path under one of the allowed roots.

    Relative paths resolve under the first root. Raises ValueError on escape.
    """
    p = PurePosixPath(path)
    root = roots[0]
    if p.is_absolute():
        for candidate in roots:
            if str(p) == candidate or str(p).startswith(candidate + "/"):
                root = candidate
                p = p.relative_to(candidate)
                break
        else:
            raise ValueError(f"absolute paths outside {'/'.join(roots)} are not allowed: {path}")
    parts = [x for x in p.parts if x != "."]
    if ".." in parts:
        raise ValueError(f"path traversal not allowed: {path}")
    return str(PurePosixPath(root, *parts))


def _resolve_workspace_path(path: str) -> str:
    return _resolve_path(path, (WORKSPACE,))


def extract_skill_accesses(name: str, args: dict) -> list[str]:
    """Paths under /skill that a tool call touches (for skill-usage tracking)."""
    if name == "read_file":
        target = str(args.get("path", ""))
        if target == SKILL_MOUNT or target.startswith(SKILL_MOUNT + "/"):
            return [target]
        return []
    if name == "bash":
        return _SKILL_PATH_RE.findall(str(args.get("command", "")))
    return []


def dispatch(
    name: str,
    arguments: str,
    sandbox: Sandbox,
    skill_accesses: set[str] | None = None,
) -> str:
    """Execute one tool call; always returns a JSON string for the tool message.

    When skill_accesses is given, any /skill path this call touches is added to it.
    """
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"invalid JSON arguments: {e}"})

    if skill_accesses is not None:
        skill_accesses.update(extract_skill_accesses(name, args))

    try:
        if name == "bash":
            timeout = min(int(args.get("timeout_seconds") or 60), 300)
            r = sandbox.exec(str(args["command"]), timeout=timeout)
            return json.dumps(
                {"exit_code": r.exit_code, "stdout": r.stdout, "stderr": r.stderr,
                 **({"timed_out": True} if r.timed_out else {})}
            )
        if name == "write_file":
            target = _resolve_workspace_path(str(args["path"]))
            sandbox.put_file(target, str(args["content"]).encode("utf-8"))
            return json.dumps({"ok": True, "path": target})
        if name == "read_file":
            target = _resolve_path(str(args["path"]), (WORKSPACE, SKILL_MOUNT))
            offset = int(args.get("offset_bytes") or 0)
            limit = int(args.get("limit_bytes") or 20_000)
            data = sandbox.get_file(target)
            chunk = data[offset : offset + limit]
            return json.dumps(
                {"content": chunk.decode("utf-8", errors="replace"),
                 "total_bytes": len(data), "returned_bytes": len(chunk)}
            )
        return json.dumps({"error": f"unknown tool: {name}"})
    except (KeyError, ValueError, TypeError) as e:
        return json.dumps({"error": str(e)})
    except Exception as e:  # sandbox/docker errors — report, don't crash the loop
        return json.dumps({"error": f"tool execution failed: {e}"})
