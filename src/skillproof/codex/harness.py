"""Drive the Codex CLI to author benchmarks, with a validate-and-repair loop."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from ..bench import store
from ..config import Config
from ..models import Cluster, ClusterReport, Skill
from .prompts import authoring_prompt, repair_prompt
from .validate import ValidationResult, validate_benchmark

console = Console()


class CodexNotFound(RuntimeError):
    pass


def check_codex(cfg_or_binary="codex") -> str:
    """Resolve the authoring CLI for the configured backend."""
    if isinstance(cfg_or_binary, str):  # legacy call with a binary name
        binary, backend = cfg_or_binary, "codex"
    else:
        backend = cfg_or_binary.codex.backend
        binary = (
            cfg_or_binary.codex.claude_binary if backend == "claude"
            else cfg_or_binary.codex.binary
        )
    path = shutil.which(binary)
    if not path:
        raise CodexNotFound(
            f"The {backend} CLI ({binary!r}) was not found on PATH. Install and "
            "authenticate it, or point codex.binary / codex.claude_binary in "
            "skillproof.yaml at the right executable."
        )
    return path


def _run_codex(prompt: str, bench_dir: Path, cfg: Config, attempt: int) -> None:
    """One non-interactive authoring invocation, cwd'd into the benchmark dir."""
    log_dir = bench_dir / ".codex_logs"
    log_dir.mkdir(exist_ok=True)
    binary = check_codex(cfg)
    if cfg.codex.backend == "claude":
        cmd = [
            binary, "-p", prompt,
            "--model", cfg.codex.model or "sonnet",
            "--output-format", "json",  # result JSON includes usage + total_cost_usd
            "--permission-mode", "acceptEdits",  # auto-approve file writes
            "--allowedTools", "Bash",  # fixtures/graders need shell; no network tools
        ]
    else:
        cmd = [
            binary, "exec",
            "--cd", str(bench_dir),
            "--sandbox", "workspace-write",
            "--skip-git-repo-check",
            "-o", str(log_dir / f"attempt_{attempt}_last_message.md"),
        ]
        if cfg.codex.model:
            cmd += ["-m", cfg.codex.model]
        cmd.append(prompt)

    # Scrub CLAUDE* session vars: a nested `claude -p` inheriting them tries to
    # attach to the parent session and dies with ConnectionRefused.
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}

    log_path = log_dir / f"attempt_{attempt}.log"
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=cfg.codex.timeout_seconds,
            text=True,
            cwd=bench_dir,
            env=env,
        )
    _record_usage(cfg, log_dir, log_path, attempt)
    if proc.returncode != 0:
        raise RuntimeError(
            f"{cfg.codex.backend} authoring run exited {proc.returncode} (see {log_path})"
        )


def _record_usage(cfg: Config, log_dir: Path, log_path: Path, attempt: int) -> None:
    """Extract usage/cost from a claude -p JSON result into .codex_logs/usage.jsonl."""
    if cfg.codex.backend != "claude":
        return
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        if isinstance(data, list):  # some CLI versions emit the message array
            results = [d for d in data if isinstance(d, dict) and d.get("type") == "result"]
            data = results[-1] if results else (data[-1] if data and isinstance(data[-1], dict) else {})
        usage = data.get("usage") or {}
        if not isinstance(usage, dict):
            usage = {}
        record = {
            "attempt": attempt,
            "model": cfg.codex.model or "sonnet",
            "tokens_in": usage.get("input_tokens"),
            "tokens_out": usage.get("output_tokens"),
            "cache_read_tokens": usage.get("cache_read_input_tokens"),
            "cost_usd": data.get("total_cost_usd"),
            "duration_ms": data.get("duration_ms"),
            "num_turns": data.get("num_turns"),
        }
        with (log_dir / "usage.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:
        pass  # usage tracking must never fail an authoring run


def authoring_usage(bench_dir: Path) -> dict:
    """Sum recorded authoring usage across attempts for one benchmark."""
    path = bench_dir / ".codex_logs" / "usage.jsonl"
    totals = {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "attempts": 0}
    if not path.is_file():
        return {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if not isinstance(rec, dict):
                continue
            totals["attempts"] += 1
            totals["tokens_in"] += rec.get("tokens_in") or 0
            totals["tokens_out"] += rec.get("tokens_out") or 0
            totals["cost_usd"] = round(totals["cost_usd"] + (rec.get("cost_usd") or 0.0), 6)
    except Exception:
        return {}
    return totals


def generate_benchmark(
    skill: Skill,
    report: ClusterReport,
    cluster: Cluster,
    index: int,
    cfg: Config,
) -> tuple[Path, bool]:
    """Author + validate one benchmark for one cluster.

    Returns (bench_dir, succeeded). On terminal failure writes FAILED.md and returns
    False — callers must not abort the rest of the skill's benchmarks.
    """
    bench_id = store.bench_dir_name(index, cluster.label)
    bench_dir = store.skill_bench_dir(cfg.benchmarks_dir, skill.name) / bench_id
    bench_dir.mkdir(parents=True, exist_ok=True)
    (bench_dir / "FAILED.md").unlink(missing_ok=True)

    chunks = report.chunks_for(cluster)
    prompt = authoring_prompt(skill, cluster, chunks, bench_id)
    last_result: ValidationResult | None = None

    for attempt in range(1, cfg.codex.max_attempts + 1):
        console.print(f"  [cyan]{bench_id}[/cyan] codex attempt {attempt}/{cfg.codex.max_attempts}")
        try:
            _run_codex(prompt, bench_dir, cfg, attempt)
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            last_result = ValidationResult(ok=False, failures=[f"CODEX_RUN: {e}"])
            prompt = repair_prompt(last_result.report())
            continue

        last_result = validate_benchmark(bench_dir, cfg.sandbox, judge_cfg=cfg.judge)
        if last_result.ok:
            # record attempts + authoring usage/cost
            from ..bench.spec import BenchmarkSpec

            spec = BenchmarkSpec.load(bench_dir)
            spec.validation.codex_attempts = attempt
            spec.authoring = {
                "backend": cfg.codex.backend,
                "model": cfg.codex.model or ("sonnet" if cfg.codex.backend == "claude" else "default"),
                **authoring_usage(bench_dir),
            }
            spec.save(bench_dir)
            console.print(f"  [green]{bench_id} validated[/green] (attempt {attempt})")
            return bench_dir, True

        console.print(f"  [yellow]{bench_id} failed validation:[/yellow]\n{last_result.report()}")
        prompt = repair_prompt(last_result.report())

    (bench_dir / "FAILED.md").write_text(
        f"# Benchmark generation failed\n\nAfter {cfg.codex.max_attempts} Codex attempts, "
        f"validation still failed. This benchmark is EXCLUDED from evaluation runs.\n\n"
        f"## Last validation report\n{last_result.report() if last_result else 'n/a'}\n",
        encoding="utf-8",
    )
    console.print(f"  [red]{bench_id} gave up — wrote FAILED.md[/red]")
    return bench_dir, False


def generate_all(skill: Skill, report: ClusterReport, cfg: Config) -> list[tuple[Path, bool]]:
    check_codex(cfg)
    results = []
    for i, cluster in enumerate(report.selected_clusters(), start=1):
        results.append(generate_benchmark(skill, report, cluster, i, cfg))
    return results
