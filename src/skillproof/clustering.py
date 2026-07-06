"""K-means clustering with silhouette-based K selection and greedy max-min
selection of the most mutually dissimilar clusters."""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from .config import Config
from .embeddings import get_provider
from .models import Chunk, Cluster, ClusterReport, Skill


def cluster_chunks(
    embeddings: np.ndarray, k_range: tuple[int, int], seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Sweep k over k_range, pick the k with the best silhouette score.

    Returns (labels, centroids).
    """
    n = embeddings.shape[0]
    k_min = max(2, k_range[0])
    k_max = min(k_range[1], n - 1)
    if n < 3 or k_max < k_min:
        # Too few chunks to cluster meaningfully: one cluster per chunk.
        return np.arange(n), embeddings.copy()

    best: tuple[float, np.ndarray, np.ndarray] | None = None
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=seed)
        labels = km.fit_predict(embeddings)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(embeddings, labels, metric="cosine")
        if best is None or score > best[0]:
            best = (score, labels, km.cluster_centers_)
    assert best is not None
    return best[1], best[2]


def select_dissimilar(centroids: np.ndarray, k_benchmarks: int) -> list[int]:
    """Greedy farthest-point selection of the k most mutually dissimilar centroids.

    Deterministic: starts from the pair with maximum cosine distance, then greedily
    adds the centroid maximizing its minimum distance to the selected set. Ties are
    broken by lower index.
    """
    n = centroids.shape[0]
    if n <= k_benchmarks:
        return list(range(n))

    normed = centroids / np.linalg.norm(centroids, axis=1, keepdims=True).clip(min=1e-12)
    dist = 1.0 - normed @ normed.T  # cosine distance matrix

    i, j = np.unravel_index(np.argmax(dist), dist.shape)
    selected = sorted([int(i), int(j)])
    while len(selected) < k_benchmarks:
        remaining = [c for c in range(n) if c not in selected]
        min_dists = [dist[c, selected].min() for c in remaining]
        selected.append(remaining[int(np.argmax(min_dists))])
    # k=1: the pair-seeded greedy overshoots; keep the lower-index one.
    return selected[:k_benchmarks]


def _label_for(chunks: list[Chunk]) -> str:
    """Short human label: the most common deepest headings in the cluster."""
    titles: list[str] = []
    for c in chunks:
        title = c.heading_path[-1] if c.heading_path else c.source_file
        if title not in titles:
            titles.append(title)
    return " / ".join(titles[:3])


def run_clustering(skill: Skill, chunks: list[Chunk], cfg: Config) -> ClusterReport:
    provider = get_provider(cfg)
    embeddings = provider.embed([c.embed_text for c in chunks])
    # Never cluster coarser than the number of benchmarks requested, else the
    # "most dissimilar clusters" selection has nothing to choose from.
    k_range = (
        max(cfg.clustering.k_range[0], cfg.clustering.k_benchmarks),
        max(cfg.clustering.k_range[1], cfg.clustering.k_benchmarks),
    )
    labels, centroids = cluster_chunks(embeddings, k_range, cfg.seed)

    selected = select_dissimilar(centroids, cfg.clustering.k_benchmarks)

    normed = centroids / np.linalg.norm(centroids, axis=1, keepdims=True).clip(min=1e-12)
    dist = 1.0 - normed @ normed.T

    clusters: list[Cluster] = []
    for cid in sorted(set(int(x) for x in labels)):
        member_ids = [chunks[i].id for i in range(len(chunks)) if labels[i] == cid]
        member_chunks = [chunks[i] for i in range(len(chunks)) if labels[i] == cid]
        others = [s for s in selected if s != cid]
        score = float(np.mean(dist[cid, others])) if others else 0.0
        clusters.append(
            Cluster(
                cluster_id=cid,
                label=_label_for(member_chunks),
                chunk_ids=member_ids,
                centroid_distance_score=round(score, 4),
            )
        )

    return ClusterReport(
        skill_name=skill.name,
        skill_path=str(skill.path),
        embedding_provider=provider.name,
        embedding_model=provider.model,
        n_chunks=len(chunks),
        k_selected=len(selected),
        all_clusters=clusters,
        selected_cluster_ids=[int(s) for s in selected],
        chunks=chunks,
    )
