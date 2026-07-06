"""Parse a Claude-style skill folder (SKILL.md + reference docs + scripts/assets)."""

from __future__ import annotations

from pathlib import Path

import frontmatter

from .models import Skill

# Markdown/text files that are documentation but not skill instructions.
_SKIP_NAMES = {"license", "license.txt", "license.md", "third_party_notices.md", "changelog.md"}
_SCRIPT_DIRS = {"scripts", "bin"}
_ASSET_DIRS = {"assets", "templates", "fonts"}
_TEXT_SUFFIXES = {".md", ".txt"}


def load_skill(path: Path | str) -> Skill:
    root = Path(path).resolve()
    skill_md_path = root / "SKILL.md"
    if not skill_md_path.is_file():
        raise FileNotFoundError(f"Not a skill folder (no SKILL.md): {root}")

    post = frontmatter.loads(skill_md_path.read_text(encoding="utf-8"))
    meta = dict(post.metadata)
    name = str(meta.get("name") or root.name)

    reference_files: dict[str, str] = {}
    script_files: list[str] = []
    asset_files: list[str] = []

    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        rel_str = str(rel)
        if rel_str == "SKILL.md" or p.name.lower() in _SKIP_NAMES:
            continue
        top = rel.parts[0].lower() if len(rel.parts) > 1 else ""
        if top in _SCRIPT_DIRS or p.suffix == ".py":
            script_files.append(rel_str)
        elif top in _ASSET_DIRS:
            asset_files.append(rel_str)
        elif p.suffix.lower() in _TEXT_SUFFIXES:
            try:
                reference_files[rel_str] = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
        else:
            asset_files.append(rel_str)

    return Skill(
        name=name,
        description=str(meta.get("description", "")),
        path=root,
        skill_md=post.content,
        frontmatter=meta,
        reference_files=reference_files,
        script_files=script_files,
        asset_files=asset_files,
    )
