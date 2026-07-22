"""Import skills and cluster them ACROSS each other into domains.

This is the front end the pipeline runs on: N skills (target ~100) → K domain
clusters. Two things fall out of one clustering:
  - the domain taxonomy is DISCOVERED, not hand-authored; and
  - each domain's member skills ARE its "relevant skills" for matching/eval.

Skill-blindness is preserved at the *task* level by the generator's leave-one-out
rule (a task scored against skill X is not seeded from skill X — see corpus.py /
README). Here we only read each skill's `name` + `description` (its routing
contract), not its body, so the domain map itself never depends on skill internals.

Lift-out seam: `cluster_chunks` (KMeans + silhouette) is imported from skillproof;
everything else is dependency-light.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

_STOP = set(
    "the a an and or for to of in on with using use used this that when help "
    "guide skill skills create creating build building any all your you user users "
    "into from via based set resources toolkit suite it its as be by".split()
)


@dataclass
class ImportedSkill:
    name: str
    description: str
    source: str            # repo/path it came from
    path: str              # local folder


@dataclass
class Domain:
    domain_id: int
    label: str
    skills: list[str] = field(default_factory=list)


@dataclass
class DomainMap:
    domains: list[Domain]
    skill_domain: dict[str, int]           # skill name -> domain_id
    embedding_model: str = ""

    def as_yaml_stub(self) -> str:
        """Emit a domains-index the generator/matcher can consume."""
        out = {"domains": [
            {"id": d.domain_id, "label": d.label, "skills": d.skills} for d in self.domains
        ]}
        return yaml.safe_dump(out, sort_keys=False, allow_unicode=True)


def load_skill_md(skill_md_path: Path, source: str = "") -> ImportedSkill:
    """Parse a SKILL.md's YAML frontmatter for name + description (body ignored —
    the domain map is built from the routing contract only)."""
    text = skill_md_path.read_text(encoding="utf-8")
    name = skill_md_path.parent.name
    description = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(text[3:end]) or {}
                name = str(fm.get("name") or name)
                description = str(fm.get("description") or "")
            except yaml.YAMLError:
                pass
    return ImportedSkill(name=name, description=description.strip(),
                         source=source, path=str(skill_md_path.parent))


def discover_skills(roots: list[Path]) -> list[ImportedSkill]:
    """Find every SKILL.md under the given roots (e.g. an imported-skills cache)."""
    skills: list[ImportedSkill] = []
    seen: set[str] = set()
    for root in roots:
        for md in sorted(Path(root).rglob("SKILL.md")):
            sk = load_skill_md(md, source=str(root))
            if sk.name in seen:
                continue
            seen.add(sk.name)
            skills.append(sk)
    return skills


def _label(skills: list[ImportedSkill]) -> str:
    words = Counter()
    for s in skills:
        for tok in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", f"{s.name} {s.description}".lower()):
            if tok not in _STOP:
                words[tok] += 1
    top = [w for w, _ in words.most_common(3)]
    return "-".join(top) if top else "domain"


def cluster_into_domains(
    skills: list[ImportedSkill],
    embedder,
    k_range: tuple[int, int] = (2, 20),
    seed: int = 42,
) -> DomainMap:
    """Embed each skill's name+description and cluster into domains."""
    from skillproof.clustering import cluster_chunks

    if not skills:
        return DomainMap(domains=[], skill_domain={})
    reps = [f"{s.name}. {s.description}" for s in skills]
    vecs = embedder.embed(reps)
    hi = min(k_range[1], len(skills) - 1)
    labels, _ = cluster_chunks(vecs, (k_range[0], max(k_range[0], hi)), seed)

    groups: dict[int, list[ImportedSkill]] = {}
    for sk, lab in zip(skills, labels):
        groups.setdefault(int(lab), []).append(sk)

    domains = [
        Domain(domain_id=did, label=_label(members), skills=[s.name for s in members])
        for did, members in sorted(groups.items())
    ]
    skill_domain = {s: d.domain_id for d in domains for s in d.skills}
    return DomainMap(domains=domains, skill_domain=skill_domain,
                     embedding_model=getattr(embedder, "model", ""))
