"""Validate a Codex-authored benchmark before it's accepted.

Checks, in order:
1. structure  — required files exist, benchmark.yaml parses
2. reference  — fixtures + reference_solution must PASS the grader
3. baseline   — fixtures alone (agent did nothing) must FAIL the grader
4. determinism (optional) — reference check repeated gives the same result

Every failure yields a machine-readable reason that is fed back to Codex verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..bench.spec import BenchmarkSpec, structural_errors
from ..config import JudgeConfig, SandboxConfig
from ..models import utcnow
from ..sandbox.grader import grade_dirs


@dataclass
class ValidationResult:
    ok: bool
    failures: list[str] = field(default_factory=list)

    def report(self) -> str:
        return "\n".join(f"- {f}" for f in self.failures) if self.failures else "all checks passed"


def validate_benchmark(
    bench_dir: Path,
    sandbox_cfg: SandboxConfig,
    check_determinism: bool = True,
    judge_cfg: JudgeConfig | None = None,
) -> ValidationResult:
    bench_dir = Path(bench_dir)
    failures: list[str] = []

    # 1. structure
    errs = structural_errors(bench_dir)
    if errs:
        return ValidationResult(ok=False, failures=[f"STRUCTURE: {e}" for e in errs])
    spec = BenchmarkSpec.load(bench_dir)

    files_dir = bench_dir / "files"
    ref_dir = bench_dir / "reference_solution"

    # 2. reference must pass
    ref = grade_dirs(bench_dir, spec, sandbox_cfg, [files_dir, ref_dir], judge_cfg)
    if not ref.passed:
        failures.append(
            "REFERENCE_CHECK: the grader FAILED against reference_solution/ "
            f"(exit code {ref.exit_code}). Either the reference solution is wrong or the "
            f"grader is broken. Grader output:\n{ref.output[:4000]}"
        )

    # 3. naive baseline must fail
    base = grade_dirs(bench_dir, spec, sandbox_cfg, [files_dir], judge_cfg)
    if base.passed:
        failures.append(
            "BASELINE_CHECK: the grader PASSED against the untouched input fixtures "
            "(an agent that does nothing would score 100%). The grader must verify "
            "work was actually done. Grader output:\n" + base.output[:4000]
        )

    # 4. determinism smoke: rerun reference, same verdict required
    if check_determinism and ref.passed:
        ref2 = grade_dirs(bench_dir, spec, sandbox_cfg, [files_dir, ref_dir], judge_cfg)
        if ref2.passed != ref.passed:
            failures.append(
                "DETERMINISM_CHECK: two identical grader runs disagreed "
                f"(run1 exit {ref.exit_code}, run2 exit {ref2.exit_code}). "
                "The grader must be deterministic (no randomness, timestamps, or ordering "
                "dependence). If an LLM-judge question flipped between runs, the "
                "question is too ambiguous — make it crisper or replace it with a "
                "deterministic check."
            )

    ok = not failures
    if ok:
        spec.validation.reference_passed = True
        spec.validation.baseline_failed = True
        spec.validation.determinism_checked = check_determinism
        spec.validation.validated_at = utcnow()
        spec.save(bench_dir)
    return ValidationResult(ok=ok, failures=failures)
