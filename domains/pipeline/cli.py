"""Pipeline CLI: import → cluster → seed → generate → match → evaluate.

Run from the repo root:  python -m pipeline.cli <command>  (with domains/ on sys.path)
or:  cd domains && python -m pipeline.cli <command>

Reuses skillproof's Config/embeddings/Sandbox for the runtime seams. Commands that
touch the sandbox (generate/validate/probe/evaluate) need Docker running; commands
that embed (cluster/seed/match) need OPENROUTER_API_KEY (or a local embedder).
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml

from . import author_runner, corpus, eval_runner, match, skillmap, skills_import
from .models import SkillClaim

app = typer.Typer(help="Generate hard, skill-matched Harbor tasks at scale.")

DOMAINS = Path("domains")
CACHE = DOMAINS / ".skills_cache"
MAP = DOMAINS / "domain_map.yaml"


def _cfg():
    from skillproof.config import Config
    return Config.load("skillproof.yaml")


def _embedder():
    from skillproof.embeddings import get_provider
    return get_provider(_cfg())


def _sandbox_factory(cfg):
    from skillproof.sandbox.container import Sandbox
    return lambda: Sandbox(cfg.sandbox)


def _domain_by_key(dmap: dict, key: str) -> dict:
    for d in dmap["domains"]:
        if str(d["id"]) == key or d["label"] == key:
            return d
    raise typer.BadParameter(f"domain {key!r} not in {MAP}")


@app.command("import-skills")
def import_skills(manifest: Path = DOMAINS / "skills_manifest.yaml", cache: Path = CACHE):
    folders = skills_import.import_all(manifest, cache)
    typer.echo(f"imported {len(folders)} skill folders into {cache}")


@app.command()
def cluster(cache: Path = CACHE, out: Path = MAP, k_lo: int = 2, k_hi: int = 20):
    skills = skillmap.discover_skills([cache])
    dm = skillmap.cluster_into_domains(skills, _embedder(), (k_lo, k_hi))
    out.write_text(dm.as_yaml_stub(), encoding="utf-8")
    typer.echo(f"{len(dm.domains)} domains from {len(skills)} skills → {out}")
    for d in dm.domains:
        typer.echo(f"  [{d.domain_id}] {d.label}: {', '.join(d.skills)}")


def _domain_corpus(skill_names: list[str], cache: Path, holdout: str | None):
    """Chunk the markdown of a domain's skills (leave-one-out: skip `holdout`)."""
    from skillproof.chunking import chunk_markdown
    chunks = []
    for name in skill_names:
        if name == holdout:
            continue
        for md in sorted((cache).rglob("SKILL.md")):
            if md.parent.name == name or _skill_name_of(md) == name:
                for f in sorted(md.parent.rglob("*.md")):
                    rel = f.relative_to(md.parent)
                    chunks.extend(chunk_markdown(f.read_text(encoding="utf-8"), f"{name}/{rel}"))
    return chunks


def _skill_name_of(md: Path) -> str:
    from pipeline.skillmap import load_skill_md
    return load_skill_md(md).name


@app.command()
def seed(domain: str, cache: Path = CACHE, map_path: Path = MAP,
         target_size: int = 15, holdout: str = typer.Option(None, help="skill to leave out")):
    dmap = yaml.safe_load(map_path.read_text())
    d = _domain_by_key(dmap, domain)
    chunks = _domain_corpus(d["skills"], cache, holdout)
    seeds = corpus.select_seeds(chunks, _embedder(), target_size=target_size)
    for s in seeds:
        s.domain = d["label"]
    out = DOMAINS / d["label"] / "seeds.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([s.__dict__ for s in seeds], indent=2), encoding="utf-8")
    typer.echo(f"{len(seeds)} seeds for domain {d['label']} → {out}")


@app.command()
def generate(domain: str, map_path: Path = MAP, trials: int = 3):
    from .models import TaskSeed
    cfg = _cfg()
    dmap = yaml.safe_load(map_path.read_text())
    d = _domain_by_key(dmap, domain)
    seeds = [TaskSeed(**s) for s in json.loads((DOMAINS / d["label"] / "seeds.json").read_text())]
    tasks_dir = DOMAINS / d["label"] / "tasks"
    probe_model = cfg.eval.models[0]
    results = author_runner.generate_domain(
        seeds, d["label"], tasks_dir, cfg, _sandbox_factory(cfg), probe_model, probe_trials=trials)
    ok = sum(1 for _, a in results if a)
    typer.echo(f"generated {ok}/{len(results)} accepted tasks in {tasks_dir}")


@app.command("match")
def match_cmd(domain: str, map_path: Path = MAP):
    dmap = yaml.safe_load(map_path.read_text())
    d = _domain_by_key(dmap, domain)
    tasks_dir = DOMAINS / d["label"] / "tasks"
    task_ids = [p.name for p in sorted(tasks_dir.iterdir())
                if p.is_dir() and (p / "task.md").is_file() and not (p / "FAILED.md").exists()]
    from . import harbor
    tasks = [(tid, harbor.load_task(tasks_dir / tid).prompt) for tid in task_ids]
    claims = [SkillClaim(name=s, domain=dd["label"], claim=_claim_for(s, dmap))
              for dd in dmap["domains"] for s in dd["skills"]]
    task_domain = {tid: d["label"] for tid in task_ids}
    seeded_by = {tid: _seed_skills(tasks_dir / tid) for tid in task_ids}
    plan = match.build_plan(d["label"], tasks, claims, task_domain, _embedder(),
                            seeded_by=seeded_by)
    out = DOMAINS / d["label"] / "match_plan.json"
    out.write_text(json.dumps({"domain": plan.domain,
        "arms": [{"task_id": a.task_id, "with_skill": a.with_skill, "relevance": a.relevance} for a in plan.arms],
        "skill_tax": plan.skill_tax}, indent=2), encoding="utf-8")
    typer.echo(f"match plan for {len(plan.arms)} tasks → {out}")


def _seed_skills(task_dir: Path) -> set[str]:
    """Skills whose corpus chunks seeded this task (leave-one-out exclusion set).

    corpus_refs are '<skill>/<file>#<heading>' — the prefix is the seeding skill.
    """
    prov = task_dir / "provenance.yaml"
    if not prov.is_file():
        return set()
    refs = (yaml.safe_load(prov.read_text()) or {}).get("corpus_refs") or []
    return {r.split("/", 1)[0] for r in refs if isinstance(r, str) and "/" in r}


def _claim_for(skill: str, dmap: dict) -> str:
    # description isn't in the map stub; read it back from the cache if present.
    for md in CACHE.rglob("SKILL.md"):
        s = skillmap.load_skill_md(md)
        if s.name == skill:
            return s.description
    return skill


@app.command()
def evaluate(domain: str, map_path: Path = MAP, trials: int = 3):
    cfg = _cfg()
    dmap = yaml.safe_load(map_path.read_text())
    d = _domain_by_key(dmap, domain)
    plan_raw = json.loads((DOMAINS / d["label"] / "match_plan.json").read_text())
    from .models import ArmPlan, MatchPlan
    plan = MatchPlan(domain=d["label"],
        arms=[ArmPlan(task_id=a["task_id"], domain=d["label"], with_skill=a["with_skill"],
                      relevance=a["relevance"]) for a in plan_raw["arms"]])
    evals = eval_runner.evaluate(plan, DOMAINS / d["label"] / "tasks", CACHE, cfg,
                                 _sandbox_factory(cfg), trials=trials)
    for te in evals:
        typer.echo(f"\n{te.task_id}: baseline {te.baseline.pass_rate:.0%}")
        for sk, ar in te.with_skill.items():
            typer.echo(f"    {sk}: {ar.pass_rate:.0%}  (uplift {te.uplift(sk):+.0%})")


if __name__ == "__main__":
    app()
