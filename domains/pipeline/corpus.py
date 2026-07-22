"""Corpus ingestion and difficulty-targeted seed selection.

Turns a domain's committed corpus into a ranked set of TaskSeeds: diverse,
difficulty-dense authoring units. This is where the difficulty *prior* meets
topical diversity — we want tasks that are hard-with-headroom AND spread across
the domain, not 15 variations of the same pitfall.

Pipeline:
  corpus/*.md --chunk--> chunks --score--> keep top-difficulty --embed+cluster-->
  most-dissimilar clusters --> one seed per cluster from its hardest chunks.

Lift-out seam: the chunk/cluster/embedding primitives are imported from
skillproof. To lift this project out, vendor those three modules (chunking,
clustering, embeddings) — nothing else here touches skillproof.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from . import difficulty
from .models import TaskSeed


def _slug(text: str, n: int = 40) -> str:
    return (re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:n]) or "seed"


def load_corpus(corpus_dir: Path):
    """Chunk every markdown file under corpus/ (skipping SOURCES.json). Returns
    skillproof Chunk objects; chunk ids are `<relpath>#<heading-slug>`."""
    from skillproof.chunking import chunk_markdown

    corpus_dir = Path(corpus_dir)
    chunks = []
    for md in sorted(corpus_dir.rglob("*.md")):
        rel = str(md.relative_to(corpus_dir))
        chunks.extend(chunk_markdown(md.read_text(encoding="utf-8"), f"corpus/{rel}"))
    return chunks


def score_corpus(chunks):
    """DifficultySignal per chunk, in input order."""
    return [difficulty.score_chunk(c.id, c.text) for c in chunks]


def select_seeds(
    chunks,
    embedder,
    target_size: int = 15,
    top_frac: float = 0.6,
    chunks_per_seed: int = 3,
    seed: int = 42,
) -> list[TaskSeed]:
    """Select diverse, difficulty-dense authoring seeds.

    1. score every chunk; keep the top `top_frac` by difficulty (the prior).
    2. embed + cluster the survivors; pick the `target_size` most-dissimilar
       clusters (diversity).
    3. one seed per selected cluster, built from its highest-difficulty chunks.
    """
    from skillproof.clustering import cluster_chunks, select_dissimilar

    if not chunks:
        return []

    signals = {s.chunk_id: s for s in score_corpus(chunks)}
    kept = difficulty.rank(list(signals.values()), top_frac=top_frac, min_score=0.0)
    kept_ids = {s.chunk_id for s in kept}
    kept_chunks = [c for c in chunks if c.id in kept_ids]
    if len(kept_chunks) <= target_size:
        # too few survivors to cluster meaningfully: one seed per chunk, hardest first.
        ranked = sorted(kept_chunks, key=lambda c: signals[c.id].score, reverse=True)
        return [_seed_from(i, [c], signals) for i, c in enumerate(ranked, 1)]

    vecs = embedder.embed([c.embed_text for c in kept_chunks])
    # force at least target_size clusters so the diversity selection has choices.
    k_range = (min(target_size, len(kept_chunks) - 1), min(target_size * 2, len(kept_chunks) - 1))
    labels, centroids = cluster_chunks(vecs, k_range, seed)
    chosen = select_dissimilar(centroids, target_size)

    seeds: list[TaskSeed] = []
    for idx, cid in enumerate(chosen, 1):
        members = [kept_chunks[i] for i in range(len(kept_chunks)) if int(labels[i]) == cid]
        if not members:
            continue
        members.sort(key=lambda c: signals[c.id].score, reverse=True)
        seeds.append(_seed_from(idx, members[:chunks_per_seed], signals))
    return seeds


def _seed_from(idx: int, members, signals) -> TaskSeed:
    label = members[0].heading_path[-1] if members[0].heading_path else members[0].source_file
    scores = [signals[c.id].score for c in members]
    rationale = " | ".join(f"{c.id}: {signals[c.id].rationale}" for c in members)
    return TaskSeed(
        seed_id=f"seed_{idx:02d}_{_slug(label)}",
        domain="",  # set by caller
        cluster_label=label,
        chunk_ids=[c.id for c in members],
        excerpts=[c.text for c in members],
        difficulty_score=round(float(np.mean(scores)), 4),
        rationale=rationale,
    )
