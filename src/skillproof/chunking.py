"""Heading-based markdown chunking with merge/split size normalization."""

from __future__ import annotations

import re

from .config import ClusteringConfig
from .models import Chunk, Skill

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
_FENCE_RE = re.compile(r"^(```|~~~)")


def _estimate_tokens(text: str) -> int:
    # Rough heuristic: ~4 chars per token.
    return max(1, len(text) // 4)


def _slugify(parts: list[str]) -> str:
    joined = "-".join(parts) if parts else "top"
    slug = re.sub(r"[^a-z0-9]+", "-", joined.lower()).strip("-")
    return slug or "top"


def chunk_markdown(text: str, source_file: str) -> list[Chunk]:
    """Split markdown into sections at #/##/### headings, tracking heading paths.

    Headings inside fenced code blocks are ignored.
    """
    sections: list[tuple[list[str], list[str]]] = [([], [])]  # (heading_path, lines)
    heading_stack: list[tuple[int, str]] = []
    in_fence = False

    for line in text.splitlines():
        if _FENCE_RE.match(line.strip()):
            in_fence = not in_fence
        m = None if in_fence else _HEADING_RE.match(line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            heading_stack = [(lv, t) for lv, t in heading_stack if lv < level]
            heading_stack.append((level, title))
            sections.append(([t for _, t in heading_stack], [line]))
        else:
            sections[-1][1].append(line)

    chunks: list[Chunk] = []
    seen_ids: dict[str, int] = {}
    for heading_path, lines in sections:
        body = "\n".join(lines).strip()
        if not body:
            continue
        base_id = f"{source_file}#{_slugify(heading_path)}"
        n = seen_ids.get(base_id, 0)
        seen_ids[base_id] = n + 1
        cid = base_id if n == 0 else f"{base_id}-{n}"
        chunks.append(
            Chunk(
                id=cid,
                source_file=source_file,
                heading_path=heading_path,
                text=body,
                token_estimate=_estimate_tokens(body),
            )
        )
    return chunks


def _normalize_sizes(chunks: list[Chunk], cfg: ClusteringConfig) -> list[Chunk]:
    """Merge undersized chunks into their predecessor; split oversized on paragraphs."""
    merged: list[Chunk] = []
    for chunk in chunks:
        if (
            merged
            and chunk.token_estimate < cfg.min_chunk_tokens
            and merged[-1].source_file == chunk.source_file
        ):
            prev = merged[-1]
            text = prev.text + "\n\n" + chunk.text
            merged[-1] = prev.model_copy(
                update={"text": text, "token_estimate": _estimate_tokens(text)}
            )
        else:
            merged.append(chunk)

    out: list[Chunk] = []
    for chunk in merged:
        if chunk.token_estimate <= cfg.max_chunk_tokens:
            out.append(chunk)
            continue
        paras = re.split(r"\n\n+", chunk.text)
        part_lines: list[str] = []
        parts: list[str] = []
        budget = cfg.max_chunk_tokens * 4  # chars
        for para in paras:
            if part_lines and sum(len(s) for s in part_lines) + len(para) > budget:
                parts.append("\n\n".join(part_lines))
                part_lines = []
            part_lines.append(para)
        if part_lines:
            parts.append("\n\n".join(part_lines))
        for i, part in enumerate(parts):
            out.append(
                chunk.model_copy(
                    update={
                        "id": chunk.id if i == 0 else f"{chunk.id}--part{i}",
                        "text": part,
                        "token_estimate": _estimate_tokens(part),
                    }
                )
            )
    return out


def chunk_skill(skill: Skill, cfg: ClusteringConfig | None = None) -> list[Chunk]:
    cfg = cfg or ClusteringConfig()
    chunks = chunk_markdown(skill.skill_md, "SKILL.md")
    for rel_path in sorted(skill.reference_files):
        chunks.extend(chunk_markdown(skill.reference_files[rel_path], rel_path))
    return _normalize_sizes(chunks, cfg)
