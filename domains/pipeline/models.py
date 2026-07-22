"""Data types for the task-generation + skill-matching pipeline.

Plain dataclasses, no skillproof dependency — this layer lifts out of the repo
unchanged. The chunking/clustering/embedding primitives are imported from
skillproof in corpus.py/match.py (the documented lift-out seam).
"""

from __future__ import annotations

from dataclasses import dataclass, field


# --- difficulty ---------------------------------------------------------------


@dataclass
class DifficultySignal:
    """Why a corpus chunk is (or isn't) a promising hard-task seed.

    Densities are hits per 100 estimated tokens, so long generic prose can't win
    on length alone. `score` is the composite prior; it is a *ranking* signal
    within one corpus, empirically confirmed later by the headroom probe.
    """

    chunk_id: str
    hits: dict[str, int] = field(default_factory=dict)        # signal -> raw count
    densities: dict[str, float] = field(default_factory=dict)  # signal -> per-100-tok
    score: float = 0.0

    @property
    def rationale(self) -> str:
        top = sorted(self.densities.items(), key=lambda kv: kv[1], reverse=True)
        parts = [f"{k}={self.hits.get(k, 0)}" for k, v in top if v > 0]
        return ", ".join(parts) or "no difficulty signals"


# --- corpus / seeds -----------------------------------------------------------


@dataclass
class TaskSeed:
    """One authoring unit: a cluster of difficulty-dense corpus chunks.

    Fed to the authoring agent (with NO skill in context) to produce one Harbor
    task package. `chunk_ids` become the task's provenance.corpus_refs.
    """

    seed_id: str
    domain: str
    cluster_label: str
    chunk_ids: list[str]
    excerpts: list[str]          # the chunk texts the author sees
    difficulty_score: float      # mean prior over the seed's chunks
    rationale: str               # aggregated signal breakdown, for audit


# --- skills / matching --------------------------------------------------------


@dataclass
class SkillClaim:
    """A skill's domain claim: its SKILL.md `description`, verbatim.

    The matcher only ever sees this — never SKILL.md bodies — so matching is
    structurally skill-content-blind (it routes against the production contract).
    """

    name: str
    domain: str          # the domain whose domain.yaml lists this claim
    claim: str


@dataclass
class Relevance:
    task_id: str
    skill_name: str
    score: float         # cosine(task prompt, skill claim), in [-1, 1]
    in_domain: bool      # does this skill claim the task's domain?


@dataclass
class ArmPlan:
    """The evaluation arms for one task: shared baseline + per-skill with-skill."""

    task_id: str
    domain: str
    with_skill: list[str]              # claiming skills, ranked by relevance
    relevance: dict[str, float]        # skill -> score, for routing-validity metric


@dataclass
class MatchPlan:
    """Everything the eval harness needs to run a domain pool.

    baseline is shared across all skills (skill-blind, one arm-set per pool).
    skill_tax pairs inject an off-domain skill as a negative control.
    """

    domain: str
    arms: list[ArmPlan]
    skill_tax: list[tuple[str, str]] = field(default_factory=list)  # (task_id, off_domain_skill)
