"""Run a benchmark's grader against a workspace state, always in a fresh container.

Judge protocol: a grader that needs LLM yes/no judgments writes
/workspace/.judge/questions.json and exits with code 3; the harness answers the
questions host-side (see judge.py), writes .judge/answers.json, and re-runs the
grader once for the final verdict. The sandbox stays offline throughout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..bench.spec import BenchmarkSpec
from ..config import JudgeConfig, SandboxConfig
from ..judge import JUDGE_EXIT_CODE, JudgeError, answer_questions
from .container import GRADER_MOUNT, WORKSPACE, Sandbox


@dataclass
class GradeResult:
    passed: bool
    exit_code: int
    output: str  # combined stdout+stderr, truncated
    timed_out: bool = False
    judge_qa: list[dict] = field(default_factory=list)  # audit trail of judge Q&A


def _exec_grader(sandbox: Sandbox, spec: BenchmarkSpec):
    entry = spec.grader.entrypoint
    entry_name = str(Path(entry).relative_to("grader")) if entry.startswith("grader/") else entry
    return sandbox.exec(
        f"bash {GRADER_MOUNT}/{entry_name}",
        timeout=spec.timeouts.grader_seconds,
        workdir=WORKSPACE,
    )


def _run_grader_in(
    sandbox: Sandbox,
    bench_dir: Path,
    spec: BenchmarkSpec,
    judge_cfg: JudgeConfig | None,
) -> GradeResult:
    sandbox.put_dir(bench_dir / "grader", GRADER_MOUNT)
    result = _exec_grader(sandbox, spec)
    judge_qa: list[dict] = []

    if result.exit_code == JUDGE_EXIT_CODE and not result.timed_out:
        if judge_cfg is None:
            return GradeResult(
                passed=False, exit_code=result.exit_code,
                output="grader requested LLM judge (exit 3) but no judge is configured",
            )
        try:
            records = answer_questions(sandbox, judge_cfg)
        except (JudgeError, Exception) as e:  # judge infra failure = grading failure
            return GradeResult(
                passed=False, exit_code=JUDGE_EXIT_CODE,
                output=f"LLM judge failed: {e}",
            )
        judge_qa = [
            {"id": r.id, "question": r.question, "answer": r.answer, "votes": r.votes}
            for r in records
        ]
        result = _exec_grader(sandbox, spec)  # final verdict with answers present
        if result.exit_code == JUDGE_EXIT_CODE:
            return GradeResult(
                passed=False, exit_code=result.exit_code,
                output="grader exited 3 again after judge answers were provided",
                judge_qa=judge_qa,
            )

    output = "\n".join(x for x in [result.stdout, result.stderr] if x)
    return GradeResult(
        passed=result.exit_code == 0,
        exit_code=result.exit_code,
        output=output,
        timed_out=result.timed_out,
        judge_qa=judge_qa,
    )


def grade_snapshot(
    snapshot_tar: bytes,
    bench_dir: Path,
    spec: BenchmarkSpec,
    sandbox_cfg: SandboxConfig,
    judge_cfg: JudgeConfig | None = None,
) -> GradeResult:
    """Grade an agent-produced workspace snapshot in a fresh container."""
    with Sandbox(sandbox_cfg) as sandbox:
        sandbox.restore_workspace(snapshot_tar)
        return _run_grader_in(sandbox, bench_dir, spec, judge_cfg)


def grade_dirs(
    bench_dir: Path,
    spec: BenchmarkSpec,
    sandbox_cfg: SandboxConfig,
    overlay_dirs: list[Path],
    judge_cfg: JudgeConfig | None = None,
) -> GradeResult:
    """Grade a workspace built from host dirs (fixtures + optional overlays)."""
    with Sandbox(sandbox_cfg) as sandbox:
        for d in overlay_dirs:
            if d.is_dir():
                sandbox.put_dir(d, WORKSPACE)
        return _run_grader_in(sandbox, bench_dir, spec, judge_cfg)
