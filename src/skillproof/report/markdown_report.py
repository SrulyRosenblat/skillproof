"""Render a human-readable markdown report from RunResults."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..models import RunResults


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _signed(x: float) -> str:
    return f"{x * 100:+.0f}pp"


def render(results: RunResults) -> str:
    lines: list[str] = []
    cfg = results.config_snapshot
    eval_cfg = cfg.get("eval", {})

    lines += [
        f"# Skill benchmark report: `{results.skill_name}`",
        "",
        f"- **Run**: `{results.run_id}` ({results.created_at:%Y-%m-%d %H:%M} UTC)",
        f"- **Models**: {', '.join(eval_cfg.get('models', []))}",
        f"- **Trials per arm**: {eval_cfg.get('trials')}  |  **Seed**: {cfg.get('seed')}  |  "
        f"**Temp**: {eval_cfg.get('temperature')}",
        f"- **Sandbox image**: `{results.sandbox_image}`",
        "",
        "**Uplift** = pass rate with skill − pass rate without skill. "
        "Positive uplift means the skill measurably helps.",
        "",
        "## Results by benchmark × model",
        "",
        "| Benchmark | Model | With skill | Without skill | Uplift |",
        "|---|---|---:|---:|---:|",
    ]
    for r in results.results:
        lines.append(
            f"| {r.benchmark_id} | {r.model} | {_pct(r.with_skill_pass_rate)} "
            f"| {_pct(r.without_skill_pass_rate)} | **{_signed(r.uplift)}** |"
        )

    # efficiency: how much work each arm took (means over non-errored trials)
    lines += [
        "",
        "## Efficiency by benchmark × model × arm",
        "",
        "Turns = model invocations in the agent loop (one per assistant response; "
        "all tool calls in a response execute within that turn). Tokens are summed "
        "across every API call in the trial; cost is OpenRouter-reported.",
        "",
        "| Benchmark | Model | Arm | Turns | Tokens in | Tokens out | Wall (s) | Cost |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in results.results:
        for arm, stats in (
            ("with_skill", r.with_skill_stats),
            ("without_skill", r.without_skill_stats),
        ):
            cost = f"${stats.total_cost_usd:.4f}" if stats.total_cost_usd is not None else "—"
            lines.append(
                f"| {r.benchmark_id} | {r.model} | {arm} | {stats.mean_turns:g} "
                f"| {stats.mean_tokens_in:,.0f} | {stats.mean_tokens_out:,.0f} "
                f"| {stats.mean_wall_seconds:g} | {cost} |"
            )

    # model summary
    by_model: dict[str, list[float]] = defaultdict(list)
    by_bench: dict[str, list[float]] = defaultdict(list)
    for r in results.results:
        by_model[r.model].append(r.uplift)
        by_bench[r.benchmark_id].append(r.uplift)

    lines += ["", "## Mean uplift by model", "", "| Model | Mean uplift |", "|---|---:|"]
    for model, ups in sorted(by_model.items()):
        lines.append(f"| {model} | **{_signed(sum(ups) / len(ups))}** |")

    lines += ["", "## Mean uplift by benchmark", "", "| Benchmark | Mean uplift | Hash |", "|---|---:|---|"]
    for bench, ups in sorted(by_bench.items()):
        h = results.benchmark_hashes.get(bench, "")
        lines.append(f"| {bench} | **{_signed(sum(ups) / len(ups))}** | `{h}` |")

    # which skill files the agent actually consulted (with_skill arm)
    skill_reads: dict[tuple[str, str], dict[str, int]] = {}
    for r in results.results:
        counts: dict[str, int] = defaultdict(int)
        for t in r.trials:
            if t.arm == "with_skill":
                for f in t.skill_files_read or []:
                    counts[f] += 1
        if counts:
            skill_reads[(r.benchmark_id, r.model)] = dict(counts)
    if skill_reads:
        lines += [
            "",
            "## Skill files consulted (with_skill arm)",
            "",
            "SKILL.md itself is injected at invocation; entries here are on-demand "
            "reads of reference files/scripts under `/skill` (count = trials that "
            "touched the path).",
            "",
            "| Benchmark | Model | File | Trials |",
            "|---|---|---|---:|",
        ]
        for (bench, model), counts in sorted(skill_reads.items()):
            for f, n in sorted(counts.items()):
                lines.append(f"| {bench} | {model} | `{f}` | {n} |")

    # caveats: errored trials
    errored = [
        t for r in results.results for t in r.trials if t.error is not None
    ]
    if errored:
        lines += ["", "## Caveats — errored trials (infra/API, not graded failures)", ""]
        for t in errored:
            lines.append(
                f"- `{t.benchmark_id}` / {t.model} / {t.arm} / trial {t.trial}: {t.error}"
            )

    lines += [
        "",
        "## Audit trail",
        "",
        "- Full per-trial transcripts: `transcripts/<model>/<benchmark>/<arm>/trial_N.jsonl`",
        "- Frozen config: `run_config.json`",
        "- Raw results: `results.json`",
        "",
    ]
    return "\n".join(lines)


def write(results: RunResults, run_dir: Path) -> Path:
    path = Path(run_dir) / "report.md"
    path.write_text(render(results), encoding="utf-8")
    return path
