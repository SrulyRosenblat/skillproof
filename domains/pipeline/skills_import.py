"""Import skills from a manifest into a local cache, ready for clustering.

Manifest (YAML) entries are either git repos (shallow-cloned, optional subpath) or
local paths (copied). After import, `skillmap.discover_skills([cache])` finds every
SKILL.md. Ranking to "top 100" is the manifest's job — curate it from the community
directories (VoltAgent/awesome-agent-skills, sickn33/agentic-awesome-skills,
awesomeclaude.ai) or a GitHub-API star/usage sort.

Kept deliberately thin: git is shelled out (no new deps); the local path is unit-
tested. Network clones are the caller's to run.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml


def load_manifest(path: Path) -> list[dict]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return data.get("skills_sources", [])


def _selected(folders: list[Path], entry: dict) -> list[Path]:
    include = entry.get("include")
    exclude = set(entry.get("exclude") or [])
    if include is not None:
        folders = [f for f in folders if f.name in set(include)]
    return [f for f in folders if f.name not in exclude]


def import_source(entry: dict, cache_dir: Path) -> list[Path]:
    """Import one manifest entry; return the skill folders (dirs with SKILL.md) added.

    Optional keys: `subpath` (dir inside a repo), `include` / `exclude` (skill folder
    names). When any of the three is set, the cache entry is pruned to exactly the
    selected skill folders — `discover_skills` rglobs the whole cache, so anything
    left behind (repo docs, unselected skills) would leak into the pool.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    name = entry.get("name") or entry.get("repo", "src").rstrip("/").split("/")[-1]
    dest = cache_dir / name
    prune = bool(entry.get("subpath") or entry.get("include") or entry.get("exclude"))

    if entry.get("path"):  # local source — copy (tested path)
        src = Path(entry["path"])
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        root = dest / entry["subpath"] if entry.get("subpath") else dest
    elif entry.get("repo"):  # git source — shallow clone (network; caller runs)
        if not dest.exists():
            subprocess.run(
                ["git", "clone", "--depth", "1", entry["repo"], str(dest)],
                check=True, capture_output=True, text=True,
            )
        root = dest / entry["subpath"] if entry.get("subpath") else dest
    else:
        raise ValueError(f"manifest entry needs 'repo' or 'path': {entry}")

    folders = _selected(sorted({p.parent for p in root.rglob("SKILL.md")}), entry)

    if prune:  # rebuild the cache entry as a flat dir of just the selected skills
        tmp = dest.with_name(dest.name + ".pruning")
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        for f in folders:
            shutil.copytree(f, tmp / f.name)
        shutil.rmtree(dest)
        tmp.rename(dest)
        folders = [dest / f.name for f in folders]

    return folders


def import_all(manifest_path: Path, cache_dir: Path) -> list[Path]:
    folders: list[Path] = []
    for entry in load_manifest(manifest_path):
        folders.extend(import_source(entry, cache_dir))
    return folders
