"""Skill matching — associate tasks with the skills that should help them.

Skill-blind by construction: the matcher only ever sees a skill's `claim` (its
SKILL.md `description` frontmatter, quoted in domain.yaml), never the skill body.
That is exactly the text production skill-routing matches against, so:

  relevance(task, skill) = cosine( embed(task prompt), embed(skill claim) )

is the production-routing analog. It never inspects skill content, so it cannot
tune tasks toward a skill (rule 1: skills consulted at measurement time, never
selection time).

Outputs a MatchPlan: per-task with-skill arms (all claiming skills, ranked),
a shared baseline (implicit — one skill-blind arm-set per pool), and sampled
off-domain skill-tax pairs as negative controls.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from .models import ArmPlan, MatchPlan, Relevance, SkillClaim


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray: ...  # returns L2-normalized rows


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    # rows are already L2-normalized by every skillproof provider; guard anyway.
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def relevances(
    tasks: list[tuple[str, str]],       # (task_id, prompt_text)
    claims: list[SkillClaim],
    task_domain: dict[str, str],        # task_id -> domain
    embedder: Embedder,
) -> list[Relevance]:
    """Every (task, skill) cosine, tagged in_domain. One embed batch each side."""
    if not tasks or not claims:
        return []
    task_vecs = embedder.embed([t[1] for t in tasks])
    claim_vecs = embedder.embed([c.claim for c in claims])

    out: list[Relevance] = []
    for i, (tid, _) in enumerate(tasks):
        dom = task_domain.get(tid)
        for j, c in enumerate(claims):
            out.append(
                Relevance(
                    task_id=tid,
                    skill_name=c.name,
                    score=round(_cos(task_vecs[i], claim_vecs[j]), 4),
                    in_domain=(c.domain == dom),
                )
            )
    return out


def build_plan(
    domain: str,
    tasks: list[tuple[str, str]],
    claims: list[SkillClaim],
    task_domain: dict[str, str],
    embedder: Embedder,
    max_arms: int | None = None,
    tax_per_task: int = 1,
    tax_seed: int = 42,
    seeded_by: dict[str, set[str]] | None = None,
) -> MatchPlan:
    """Assemble the evaluation plan for one domain pool.

    with-skill arms = skills claiming this domain, ranked by relevance (capped at
    max_arms if set). skill-tax = up to tax_per_task off-domain skills per task,
    chosen as the LOWEST-relevance off-domain claims (hardest negative control:
    if even a clearly-irrelevant skill changes the score, that's pure tax).

    seeded_by = task_id -> skills whose corpus chunks seeded that task (from
    provenance.yaml). Those skills are excluded from the task's with-skill arms —
    the leave-one-out rule: a skill is never scored on a task authored from its
    own content. Their relevance is still recorded for audit.
    """
    rels = relevances(tasks, claims, task_domain, embedder)
    by_task: dict[str, list[Relevance]] = {}
    for r in rels:
        by_task.setdefault(r.task_id, []).append(r)

    rng = np.random.default_rng(tax_seed)
    arms: list[ArmPlan] = []
    tax: list[tuple[str, str]] = []
    for tid, _ in tasks:
        rs = by_task.get(tid, [])
        in_dom = sorted((r for r in rs if r.in_domain), key=lambda r: r.score, reverse=True)
        seeded = (seeded_by or {}).get(tid, set())
        eligible = [r for r in in_dom if r.skill_name not in seeded]
        chosen = eligible[:max_arms] if max_arms else eligible
        arms.append(
            ArmPlan(
                task_id=tid,
                domain=domain,
                with_skill=[r.skill_name for r in chosen],
                relevance={r.skill_name: r.score for r in in_dom},
            )
        )
        off = sorted((r for r in rs if not r.in_domain), key=lambda r: r.score)
        if off and tax_per_task:
            # sample from the least-relevant third to keep controls genuinely off-topic
            pool = off[: max(tax_per_task, len(off) // 3)]
            picks = rng.choice(len(pool), size=min(tax_per_task, len(pool)), replace=False)
            tax.extend((tid, pool[int(i)].skill_name) for i in picks)

    return MatchPlan(domain=domain, arms=arms, skill_tax=tax)


def classify_to_domain(
    task_text: str,
    domain_refs: dict[str, list[str]],   # domain -> reference texts (claims or corpus excerpts)
    embedder: Embedder,
) -> list[tuple[str, float]]:
    """Rank domains for one task by similarity to each domain's reference set.

    Used to route imported/unlabeled tasks (e.g. a SkillsBench task whose upstream
    category we want to remap to our domain taxonomy). Returns (domain, score)
    descending; caller applies a threshold / manual audit.
    """
    domains = list(domain_refs)
    flat = [t for d in domains for t in domain_refs[d]]
    if not flat:
        return []
    vecs = embedder.embed([task_text] + flat)
    tvec, ref_vecs = vecs[0], vecs[1:]

    scored: list[tuple[str, float]] = []
    idx = 0
    for d in domains:
        n = len(domain_refs[d])
        sims = [_cos(tvec, ref_vecs[idx + k]) for k in range(n)]
        idx += n
        scored.append((d, round(max(sims), 4) if sims else -1.0))  # max = best-matching claim
    return sorted(scored, key=lambda kv: kv[1], reverse=True)
