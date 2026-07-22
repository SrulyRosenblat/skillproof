"""Validate a Harbor task package before acceptance.

Gates 1-4 here (deterministic, skill-blind, no agent needed):
  1. structure   — required files, task.md parses, no environment/skills/
  2. oracle      — stage inputs → run oracle/solve.sh → verifier reward == 1
  3. baseline    — stage inputs → verifier (untouched) reward == 0
  4. determinism — the oracle verdict repeats

Gate 5 (skill-blind headroom probe) needs an agent and lives in eval_runner.probe;
the author→validate→repair loop calls it after gates 1-4 pass.

Sandbox is injected so this is unit-testable without Docker (see tests' FakeSandbox).
`sandbox_factory()` returns a context-manager Sandbox — in production,
`lambda: Sandbox(cfg.sandbox)`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import harbor


@dataclass
class ValidationResult:
    ok: bool
    failures: list[str] = field(default_factory=list)
    oracle_reward: int | None = None
    baseline_reward: int | None = None

    def report(self) -> str:
        return "\n".join(f"- {f}" for f in self.failures) if self.failures else "all gates passed"


def validate_task(task_dir: Path, sandbox_factory, check_determinism: bool = True) -> ValidationResult:
    task_dir = Path(task_dir)

    errs = harbor.structure_errors(task_dir)
    if errs:
        return ValidationResult(ok=False, failures=[f"STRUCTURE: {e}" for e in errs])

    task = harbor.load_task(task_dir)
    failures: list[str] = []

    # Gate 2: oracle must reach reward 1.
    with sandbox_factory() as sb:
        harbor.stage_inputs(sb, task_dir)
        harbor.run_oracle(sb, task_dir, task.agent_timeout)
        oracle_reward, oracle_out = harbor.run_verifier(sb, task_dir, task.verifier_timeout)
    if oracle_reward != 1:
        failures.append(
            "ORACLE_CHECK: oracle/solve.sh did not reach reward 1 "
            f"(got {oracle_reward}). The oracle or verifier is wrong. Output:\n{oracle_out[:4000]}"
        )

    # Gate 3: untouched baseline must reward 0.
    with sandbox_factory() as sb:
        harbor.stage_inputs(sb, task_dir)
        baseline_reward, base_out = harbor.run_verifier(sb, task_dir, task.verifier_timeout)
    if baseline_reward != 0:
        failures.append(
            "BASELINE_CHECK: the untouched environment already reaches reward "
            f"{baseline_reward} (an agent doing nothing would pass). The verifier must "
            f"require real work. Output:\n{base_out[:4000]}"
        )

    # Gate 4: determinism — rerun the oracle verdict.
    if check_determinism and oracle_reward == 1:
        with sandbox_factory() as sb:
            harbor.stage_inputs(sb, task_dir)
            harbor.run_oracle(sb, task_dir, task.agent_timeout)
            r2, _ = harbor.run_verifier(sb, task_dir, task.verifier_timeout)
        if r2 != oracle_reward:
            failures.append(
                f"DETERMINISM_CHECK: two identical oracle+verifier runs disagreed "
                f"({oracle_reward} vs {r2}). The verifier must be deterministic."
            )

    return ValidationResult(
        ok=not failures, failures=failures,
        oracle_reward=oracle_reward, baseline_reward=baseline_reward,
    )
