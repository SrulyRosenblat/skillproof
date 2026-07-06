"""Orchestrate evaluation: benchmark × model × arm × trial, with resume support.

Each trial: fresh sandbox → copy fixtures → (arm A) inject skill → run agent →
snapshot workspace → destroy agent container → grade snapshot in a fresh container.
"""

from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from ..agent.loop import run_agent
from ..agent.transcript import Transcript
from ..bench import store
from ..bench.spec import BenchmarkSpec
from ..config import Config
from ..models import Arm, RunResults, Skill, TrialResult
from ..sandbox.container import WORKSPACE, Sandbox
from ..sandbox.grader import grade_snapshot
from .uplift import aggregate

console = Console()


def new_run_id(cfg: Config) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    h = hashlib.sha256(json.dumps(cfg.model_dump(mode="json"), sort_keys=True).encode())
    return f"{stamp}-{h.hexdigest()[:6]}"


def _trial_paths(run_dir: Path, model: str, bench_id: str, arm: Arm, trial: int):
    model_slug = model.replace("/", "_")
    base = run_dir / "transcripts" / model_slug / bench_id / arm
    return base / f"trial_{trial}.jsonl", base / f"trial_{trial}.result.json"


def run_trial(
    skill: Skill,
    bench_dir: Path,
    spec: BenchmarkSpec,
    model: str,
    arm: Arm,
    trial: int,
    cfg: Config,
    run_dir: Path,
) -> TrialResult:
    transcript_path, result_path = _trial_paths(run_dir, model, spec.id, arm, trial)
    if result_path.exists():  # resume: keep graded verdicts, retry infra errors
        prior = TrialResult.model_validate_json(result_path.read_text())
        if prior.error is None:
            return prior

    started = time.monotonic()
    task_prompt = (bench_dir / "task_prompt.md").read_text(encoding="utf-8")

    wall_cap = min(cfg.eval.agent_wall_seconds, spec.timeouts.agent_wall_seconds)
    turn_cap = min(cfg.eval.max_turns, spec.limits.max_turns)
    trial_cfg = cfg.model_copy(deep=True)
    trial_cfg.eval.agent_wall_seconds = wall_cap
    trial_cfg.eval.max_turns = turn_cap

    with Transcript(transcript_path) as transcript:
        try:
            with Sandbox(cfg.sandbox) as sandbox:
                files_dir = bench_dir / "files"
                if files_dir.is_dir():
                    sandbox.put_dir(files_dir, WORKSPACE)
                outcome = run_agent(
                    task_prompt,
                    skill if arm == "with_skill" else None,
                    sandbox,
                    model,
                    trial_cfg,
                    transcript,
                )
                snapshot = sandbox.snapshot_workspace()
            grade = grade_snapshot(snapshot, bench_dir, spec, cfg.sandbox, cfg.judge)
            transcript.event("grade", passed=grade.passed, exit_code=grade.exit_code,
                             output=grade.output[:10_000], judge_qa=grade.judge_qa)
            result = TrialResult(
                model=model,
                benchmark_id=spec.id,
                arm=arm,
                trial=trial,
                passed=grade.passed and outcome.error is None,
                grader_exit_code=grade.exit_code,
                grader_output=grade.output[:10_000],
                judge_qa=grade.judge_qa,
                turns_used=outcome.turns_used,
                wall_seconds=round(time.monotonic() - started, 1),
                tokens_in=outcome.tokens_in,
                tokens_out=outcome.tokens_out,
                cost_usd=outcome.cost_usd,
                skill_files_read=outcome.skill_files_read,
                stop_reason=outcome.stop_reason,
                error=outcome.error,
                transcript_path=str(transcript_path),
            )
        except Exception as e:  # infra failure — record, don't kill the run
            transcript.event("infra_error", error=str(e))
            result = TrialResult(
                model=model, benchmark_id=spec.id, arm=arm, trial=trial,
                passed=False, stop_reason="infra_error", error=str(e),
                wall_seconds=round(time.monotonic() - started, 1),
                transcript_path=str(transcript_path),
            )

    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result


def run_eval(
    skill: Skill,
    cfg: Config,
    run_id: str | None = None,
    only_benchmarks: list[str] | None = None,
) -> tuple[RunResults, Path]:
    benchmarks = list(store.list_benchmarks(cfg.benchmarks_dir, skill.name))
    if only_benchmarks:
        benchmarks = [(d, s) for d, s in benchmarks if s.id in only_benchmarks]
    if not benchmarks:
        raise RuntimeError(
            f"No validated benchmarks found under {cfg.benchmarks_dir}/{skill.name}. "
            "Run `skillproof generate` first."
        )

    run_id = run_id or new_run_id(cfg)
    run_dir = cfg.results_dir / skill.name / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_config.json").write_text(
        json.dumps(cfg.model_dump(mode="json"), indent=2, default=str), encoding="utf-8"
    )

    jobs = [
        (bench_dir, spec, model, arm, trial)
        for bench_dir, spec in benchmarks
        for model in cfg.eval.models
        for arm in ("with_skill", "without_skill")
        for trial in range(1, cfg.eval.trials + 1)
    ]
    console.print(
        f"[bold]run {run_id}[/bold]: {len(benchmarks)} benchmarks × "
        f"{len(cfg.eval.models)} models × 2 arms × {cfg.eval.trials} trials "
        f"= {len(jobs)} trials"
    )

    trials: list[TrialResult] = []
    if cfg.eval.parallel > 1:
        with ThreadPoolExecutor(max_workers=cfg.eval.parallel) as pool:
            futures = {
                pool.submit(run_trial, skill, bd, sp, m, a, t, cfg, run_dir): (sp.id, m, a, t)
                for bd, sp, m, a, t in jobs
            }
            for fut in as_completed(futures):
                trial = fut.result()
                trials.append(trial)
                _log_trial(trial)
    else:
        for bd, sp, m, a, t in jobs:
            trial = run_trial(skill, bd, sp, m, a, t, cfg, run_dir)
            trials.append(trial)
            _log_trial(trial)

    results = RunResults(
        skill_name=skill.name,
        run_id=run_id,
        config_snapshot=cfg.model_dump(mode="json"),
        benchmark_hashes={spec.id: store.content_hash(bd) for bd, spec in benchmarks},
        sandbox_image=cfg.sandbox.image,
        results=aggregate(trials, cfg.eval.error_policy),
    )
    (run_dir / "results.json").write_text(results.model_dump_json(indent=2), encoding="utf-8")
    return results, run_dir


def _log_trial(t: TrialResult) -> None:
    status = "[green]PASS[/green]" if t.passed else (
        f"[red]ERROR[/red] {t.error}" if t.error else "[red]FAIL[/red]"
    )
    console.print(
        f"  {t.benchmark_id} | {t.model} | {t.arm} | trial {t.trial}: {status} "
        f"({t.turns_used} turns, {t.wall_seconds}s)"
    )
