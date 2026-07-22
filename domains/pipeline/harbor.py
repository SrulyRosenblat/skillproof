"""Harbor task adapter — load/parse a task package and run its verifier/oracle
against skillproof's Docker sandbox.

We intentionally run Harbor-format tasks on skillproof's shared, offline sandbox
image (reusing its proven Sandbox + agent loop) rather than depending on Harbor the
framework. The task still carries `environment/Dockerfile` for upstream interchange;
the LOCAL runner ignores it and stages `environment/` inputs into /workspace, so
authored tasks must use only the shared image's dependencies (the authoring contract
enforces this). Per-task Dockerfile builds are a follow-up for imported tasks.

Sandbox contract used here (skillproof.sandbox.container.Sandbox):
  put_dir(host_dir, container_path) · exec(cmd, timeout, workdir) · get_file(path)
  snapshot_workspace() · restore_workspace(tar)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

WORKSPACE = "/workspace"
VERIFIER_MOUNT = "/verifier"
ORACLE_MOUNT = "/oracle"
REWARD_PATH = "/logs/verifier/reward.txt"

REQUIRED = ["task.md", "verifier/test.sh", "verifier/test_outputs.py", "oracle/solve.sh"]


@dataclass
class HarborTask:
    task_id: str
    dir: Path
    prompt: str                       # task.md body (what the agent sees)
    metadata: dict = field(default_factory=dict)
    verifier_timeout: int = 600
    agent_timeout: int = 1800


def parse_reward(text: str | bytes | None) -> int:
    """The Harbor verdict: scalar 0|1 in /logs/verifier/reward.txt. Anything
    unparseable is a fail (0) — a missing/garbled reward is not a pass."""
    if text is None:
        return 0
    if isinstance(text, bytes):
        text = text.decode("utf-8", "replace")
    tok = text.strip().split()[0] if text.strip() else ""
    try:
        return 1 if int(float(tok)) == 1 else 0
    except (ValueError, IndexError):
        return 0


def load_task(task_dir: Path) -> HarborTask:
    task_dir = Path(task_dir)
    text = (task_dir / "task.md").read_text(encoding="utf-8")
    meta: dict = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            meta = yaml.safe_load(text[3:end]) or {}
            body = text[end + 4 :].lstrip("\n")
    vt = int(((meta.get("verifier") or {}).get("timeout_sec")) or 600)
    at = int(((meta.get("agent") or {}).get("timeout_sec")) or 1800)
    return HarborTask(task_id=task_dir.name, dir=task_dir, prompt=body,
                      metadata=meta, verifier_timeout=vt, agent_timeout=at)


def structure_errors(task_dir: Path) -> list[str]:
    """Gate 1: required files present, task.md parses, no baked-in skills."""
    task_dir = Path(task_dir)
    errs = [f"missing {r}" for r in REQUIRED if not (task_dir / r).is_file()]
    if (task_dir / "environment" / "skills").exists():
        errs.append("environment/skills/ must not exist (skills are injected per arm)")
    if (task_dir / "task.md").is_file():
        try:
            t = load_task(task_dir)
            if len(t.prompt.strip()) < 30:
                errs.append("task.md body is suspiciously short")
        except Exception as e:
            errs.append(f"task.md failed to parse: {e}")
    return errs


# --- sandbox operations -------------------------------------------------------


def stage_inputs(sandbox, task_dir: Path) -> None:
    """Copy environment/ inputs (minus Dockerfile and skills/) into /workspace."""
    env_dir = Path(task_dir) / "environment"
    if not env_dir.is_dir():
        return
    for p in sorted(env_dir.rglob("*")):
        if p.is_file() and p.name != "Dockerfile" and "skills" not in p.relative_to(env_dir).parts:
            rel = p.relative_to(env_dir)
            sandbox.put_file(f"{WORKSPACE}/{rel}", p.read_bytes())


def run_verifier(sandbox, task_dir: Path, timeout: int = 600) -> tuple[int, str]:
    """Run verifier/test.sh in the sandbox; return (reward, output)."""
    sandbox.put_dir(Path(task_dir) / "verifier", VERIFIER_MOUNT)
    res = sandbox.exec(
        f"mkdir -p /logs/verifier && bash {VERIFIER_MOUNT}/test.sh", timeout=timeout,
        workdir=WORKSPACE,
    )
    try:
        reward = parse_reward(sandbox.get_file(REWARD_PATH))
    except Exception:
        reward = 0  # no reward file written = fail
    out = "\n".join(x for x in [res.stdout, res.stderr] if x)
    return reward, out


def run_oracle(sandbox, task_dir: Path, timeout: int = 600) -> str:
    """Run oracle/solve.sh in /workspace (computes the solution in place)."""
    sandbox.put_dir(Path(task_dir) / "oracle", ORACLE_MOUNT)
    res = sandbox.exec(f"bash {ORACLE_MOUNT}/solve.sh", timeout=timeout, workdir=WORKSPACE)
    return "\n".join(x for x in [res.stdout, res.stderr] if x)
