"""Seam A — author a Harbor task from a seed, then gate it.

Loop per seed (mirrors skillproof's author→validate→repair, plus gate 5):
  claude -p (Harbor contract, NO skill) → write provenance.yaml → gates 1-4
    → headroom probe (gate 5, skill-blind)
       ├─ base fails (≤ cap) → ACCEPT (record headroom) → done
       └─ base passes        → harden_prompt(transcript) → re-author → re-probe
  capped attempts → FAILED.md (excluded from the pool)

Reuses skillproof.codex.harness._run_codex verbatim to drive the CLI (host-side,
uses the local `claude` subscription auth — no API key needed for authoring).
Validation + probe need Docker + an eval model; authoring itself does not.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from . import authoring, harbor, validate
from .eval_runner import probe_headroom
from .models import TaskSeed


def _packages_note() -> str:
    p = Path("docker/packages.txt")
    if p.is_file():
        return f"## Sandbox environment inventory (the ONLY available dependencies)\n<packages>\n{p.read_text()}\n</packages>"
    return ""


def _write_provenance(task_dir: Path, seed: TaskSeed, headroom: dict | None = None) -> None:
    prov = {
        "domain": seed.domain,
        "origin": "authored",
        "imported_from": None,
        "corpus_refs": list(seed.chunk_ids),
        "difficulty_seed_score": seed.difficulty_score,
        "headroom": headroom or {"probe_agent": None, "trials": 0, "base_passes": 0},
    }
    (task_dir / "provenance.yaml").write_text(
        yaml.safe_dump(prov, sort_keys=False, allow_unicode=True), encoding="utf-8")


def generate_task(
    seed: TaskSeed,
    domain_title: str,
    tasks_dir: Path,
    cfg,
    sandbox_factory,
    probe_model: str,
    probe_trials: int = 3,
    max_base_pass_rate: float = 0.34,
    max_attempts: int = 3,
) -> tuple[Path, bool]:
    """Author + gate one task. Returns (task_dir, accepted)."""
    task_dir = Path(tasks_dir) / seed.seed_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "FAILED.md").unlink(missing_ok=True)

    from skillproof.codex.harness import _run_codex  # reuse the CLI driver

    prompt = authoring.authoring_prompt(seed, domain_title, _packages_note())
    last = "no attempt ran"

    for attempt in range(1, max_attempts + 1):
        try:
            _run_codex(prompt, task_dir, cfg, attempt)
        except Exception as e:
            last = f"CODEX_RUN: {e}"
            prompt = authoring.repair_prompt(last)
            continue

        _write_provenance(task_dir, seed)

        vr = validate.validate_task(task_dir, sandbox_factory)
        if not vr.ok:
            last = vr.report()
            prompt = authoring.repair_prompt(last)
            continue

        hr = probe_headroom(task_dir, cfg, sandbox_factory, probe_model,
                            probe_trials, max_base_pass_rate)
        if hr.accepted:
            _write_provenance(task_dir, seed, headroom={
                "probe_agent": probe_model, "trials": hr.trials,
                "base_passes": hr.base_passes, "base_pass_rate": round(hr.base_pass_rate, 3),
            })
            return task_dir, True

        last = (f"HEADROOM: base agent passed {hr.base_passes}/{hr.trials} unaided "
                f"(> {max_base_pass_rate:.0%} cap) — task is too easy.")
        prompt = authoring.harden_prompt(hr.worst_transcript or last)

    (task_dir / "FAILED.md").write_text(
        f"# Task generation failed\n\nAfter {max_attempts} attempts:\n\n{last}\n", encoding="utf-8")
    return task_dir, False


def generate_domain(seeds, domain_title, tasks_dir, cfg, sandbox_factory,
                    probe_model, **kw) -> list[tuple[Path, bool]]:
    return [generate_task(s, domain_title, tasks_dir, cfg, sandbox_factory, probe_model, **kw)
            for s in seeds]
