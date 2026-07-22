"""Seam B — run Harbor tasks on skillproof's sandbox + agent loop.

Provides:
  - probe_headroom : gate 5, skill-blind. Run a base agent N trials; accept the
    task iff base pass-rate <= max_base_pass_rate (cap, don't zero). Failing tasks
    (base solved it) return the transcript so the author can harden.
  - evaluate       : the real measurement. Per task: one SHARED baseline arm-set +
    one with-skill arm per claiming skill (from the MatchPlan). Uplift = with-base.

Each trial mirrors skillproof isolation: agent runs in sandbox A; the workspace is
snapshotted; the verifier runs in a FRESH sandbox B so the agent can't tamper with
grading. `sandbox_factory` returns a context-manager Sandbox (prod:
`lambda: Sandbox(cfg.sandbox)`), injected so the control flow is unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import harbor


@dataclass
class HeadroomResult:
    task_id: str
    trials: int
    base_passes: int
    accepted: bool
    worst_transcript: str = ""   # a run where base PASSED (for hardening), if any

    @property
    def base_pass_rate(self) -> float:
        return self.base_passes / self.trials if self.trials else 0.0


@dataclass
class ArmResult:
    task_id: str
    skill: str | None            # None = baseline arm
    rewards: list[int] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return sum(self.rewards) / len(self.rewards) if self.rewards else 0.0


@dataclass
class TaskEval:
    task_id: str
    baseline: ArmResult
    with_skill: dict[str, ArmResult] = field(default_factory=dict)

    def uplift(self, skill: str) -> float:
        return self.with_skill[skill].pass_rate - self.baseline.pass_rate


def _agent_trial(task, skill, cfg, sandbox_factory, model: str, transcript_path: Path):
    """One arm trial → (reward, transcript_summary). skill=None → baseline arm."""
    from skillproof.agent.loop import run_agent
    from skillproof.agent.transcript import Transcript

    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    with Transcript(transcript_path) as tr:
        with sandbox_factory() as sb:
            harbor.stage_inputs(sb, task.dir)
            run_agent(task.prompt, skill, sb, model, cfg, tr)
            snapshot = sb.snapshot_workspace()
        with sandbox_factory() as sb2:
            sb2.restore_workspace(snapshot)
            reward, out = harbor.run_verifier(sb2, task.dir, task.verifier_timeout)
    return reward, out[:2000]


def probe_headroom(task_dir, cfg, sandbox_factory, probe_model: str, trials: int = 3,
                   max_base_pass_rate: float = 0.34, run_dir: Path | None = None) -> HeadroomResult:
    task = harbor.load_task(task_dir)
    run_dir = Path(run_dir or Path(task_dir) / ".probe")
    passes, worst = 0, ""
    for t in range(1, trials + 1):
        reward, summary = _agent_trial(
            task, None, cfg, sandbox_factory, probe_model, run_dir / f"probe_{t}.jsonl")
        if reward == 1:
            passes += 1
            worst = summary  # keep a passing run to feed the harden loop
    accepted = (passes / trials) <= max_base_pass_rate if trials else False
    return HeadroomResult(task_id=task.task_id, trials=trials, base_passes=passes,
                          accepted=accepted, worst_transcript=worst)


def evaluate(match_plan, tasks_dir, skills_dir, cfg, sandbox_factory,
             trials: int = 3, run_dir: Path | None = None) -> list[TaskEval]:
    """Run the MatchPlan: shared baseline + per-skill arms, per task."""
    from skillproof.skill_loader import load_skill

    tasks_dir, skills_dir = Path(tasks_dir), Path(skills_dir)
    run_dir = Path(run_dir or tasks_dir.parent / "runs" / "latest")
    model = cfg.eval.models[0]
    out: list[TaskEval] = []

    for arm in match_plan.arms:
        task = harbor.load_task(tasks_dir / arm.task_id)
        base = ArmResult(task_id=arm.task_id, skill=None)
        for t in range(1, trials + 1):
            r, _ = _agent_trial(task, None, cfg, sandbox_factory, model,
                                run_dir / arm.task_id / "baseline" / f"t{t}.jsonl")
            base.rewards.append(r)
        te = TaskEval(task_id=arm.task_id, baseline=base)
        for skill_name in arm.with_skill:
            skill = load_skill(skills_dir / skill_name)
            ar = ArmResult(task_id=arm.task_id, skill=skill_name)
            for t in range(1, trials + 1):
                r, _ = _agent_trial(task, skill, cfg, sandbox_factory, model,
                                    run_dir / arm.task_id / skill_name / f"t{t}.jsonl")
                ar.rewards.append(r)
            te.with_skill[skill_name] = ar
        out.append(te)
    return out
