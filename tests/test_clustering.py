import numpy as np

from skillproof.clustering import cluster_chunks, select_dissimilar


def _blob(center, n, seed):
    rng = np.random.default_rng(seed)
    v = center + rng.normal(0, 0.05, size=(n, len(center)))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_cluster_chunks_finds_separated_blobs():
    a = _blob(np.array([1.0, 0.0, 0.0]), 10, 1)
    b = _blob(np.array([0.0, 1.0, 0.0]), 10, 2)
    c = _blob(np.array([0.0, 0.0, 1.0]), 10, 3)
    X = np.vstack([a, b, c])
    labels, centroids = cluster_chunks(X, (2, 6), seed=42)
    assert len(set(labels[:10])) == 1
    assert len(set(labels[10:20])) == 1
    assert len(set(labels[20:])) == 1
    assert len(set(labels)) == 3


def test_cluster_chunks_deterministic():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(30, 8))
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    l1, c1 = cluster_chunks(X, (2, 8), seed=42)
    l2, c2 = cluster_chunks(X, (2, 8), seed=42)
    assert (l1 == l2).all()
    assert np.allclose(c1, c2)


def test_select_dissimilar_picks_far_apart():
    centroids = np.array(
        [
            [1.0, 0.0],
            [0.99, 0.01],  # near-duplicate of 0
            [0.0, 1.0],
            [-1.0, 0.0],
        ]
    )
    picked = select_dissimilar(centroids, 3)
    assert len(picked) == 3
    # the near-duplicate pair should never both be chosen
    assert not ({0, 1} <= set(picked))


def test_select_dissimilar_all_when_few():
    centroids = np.eye(3)
    assert select_dissimilar(centroids, 5) == [0, 1, 2]
