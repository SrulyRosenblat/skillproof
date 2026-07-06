"""Skill-uplift computation: pass-rate delta between with-skill and without-skill arms."""

from __future__ import annotations

from ..models import ArmStats, BenchmarkModelResult, TrialResult


def _pass_rate(trials: list[TrialResult], error_policy: str) -> float:
    if error_policy == "exclude":
        trials = [t for t in trials if t.error is None]
    if not trials:
        return 0.0
    return sum(1 for t in trials if t.passed) / len(trials)


def _arm_stats(trials: list[TrialResult]) -> ArmStats:
    """Efficiency aggregates; errored trials excluded (their numbers are noise)."""
    ok = [t for t in trials if t.error is None]
    if not ok:
        return ArmStats(trials=0)
    n = len(ok)
    costs = [t.cost_usd for t in ok if t.cost_usd is not None]
    return ArmStats(
        trials=n,
        mean_turns=round(sum(t.turns_used for t in ok) / n, 1),
        mean_tokens_in=round(sum(t.tokens_in for t in ok) / n, 1),
        mean_tokens_out=round(sum(t.tokens_out for t in ok) / n, 1),
        mean_wall_seconds=round(sum(t.wall_seconds for t in ok) / n, 1),
        total_cost_usd=round(sum(costs), 6) if costs else None,
    )


def aggregate(
    trials: list[TrialResult], error_policy: str = "fail"
) -> list[BenchmarkModelResult]:
    """Group trials by (benchmark, model) and compute uplift."""
    groups: dict[tuple[str, str], list[TrialResult]] = {}
    for t in trials:
        groups.setdefault((t.benchmark_id, t.model), []).append(t)

    results = []
    for (bench_id, model), group in sorted(groups.items()):
        with_arm = [t for t in group if t.arm == "with_skill"]
        without_arm = [t for t in group if t.arm == "without_skill"]
        wr = _pass_rate(with_arm, error_policy)
        wor = _pass_rate(without_arm, error_policy)
        results.append(
            BenchmarkModelResult(
                benchmark_id=bench_id,
                model=model,
                with_skill_pass_rate=round(wr, 4),
                without_skill_pass_rate=round(wor, 4),
                uplift=round(wr - wor, 4),
                with_skill_stats=_arm_stats(with_arm),
                without_skill_stats=_arm_stats(without_arm),
                trials=group,
            )
        )
    return results
