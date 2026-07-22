"""Difficulty-potential scoring for corpus chunks.

The pipeline's cheap *prior*: which parts of a domain corpus are most likely to
yield a task that a base model fails but domain knowledge solves. Not all corpus
prose is equal — a paragraph packed with exact values, "must/never" rules,
documented pitfalls, and non-default procedures gates on knowledge the base model
can't guess; generic overview prose does not.

This is a heuristic ranking, empirically confirmed by the headroom probe. Its job
is to raise the probe's hit-rate so scarce agent runs aren't spent authoring from
chunks that could only ever produce easy tasks.
"""

from __future__ import annotations

import re

# Signal patterns. Case-insensitive. Each is a *why-this-is-hard* marker.
_PATTERNS: dict[str, re.Pattern] = {
    # Normative constraints the base model won't honor spontaneously.
    "normative": re.compile(
        r"\b(must not|must|never|always|required|shall|do not|don't|cannot|"
        r"exactly|precisely|only if|at least|no more than|mandatory|forbidden)\b",
        re.I,
    ),
    # Documented failure modes — the single best hard-task seeds: they name the
    # naive approach the base model takes and the correct one it doesn't.
    "pitfall": re.compile(
        r"\b(pitfall|gotcha|common mistake|common error|caution|warning|"
        r"be careful|avoid|incorrect|wrong|will fail|breaks?|does not work|"
        r"instead of|rather than|not\s+(?:the|a)\s+\w+\s+approach)\b",
        re.I,
    ),
    # Specific, unguessable procedures / ordered steps.
    "procedure": re.compile(
        r"(^\s*\d+\.\s|\bstep\s+\d|\bfirst\b.*\bthen\b|\bbefore\b.*\bafter\b|"
        r"\bin order\b|\bsequence\b)",
        re.I | re.M,
    ),
}

# Specificity: exact tokens that must be reproduced correctly and can't be
# eyeballed. Counted together as one signal.
_SPECIFIC = [
    re.compile(r"#[0-9a-fA-F]{3,8}\b"),                 # hex colors / ids
    re.compile(r"`[^`]{1,60}`"),                        # inline code / literals
    re.compile(r"\b\d+(?:\.\d+)?\s?(px|em|rem|pt|%|ms|s|kb|mb|dpi|hz|deg)\b", re.I),  # measures
    re.compile(r"\b[a-z]+_[a-z0-9_]+\b"),               # snake_case identifiers
    re.compile(r"\b[a-z]+[A-Z][A-Za-z0-9]+\b"),         # camelCase identifiers
    re.compile(r"\"[^\"]{2,40}\"|'[^']{2,40}'"),        # quoted exact strings
]

# Composite weights. Pitfalls weighted highest — they most directly imply a task
# where the naive attempt fails a deterministic check.
_WEIGHTS = {"normative": 1.0, "pitfall": 1.6, "procedure": 0.8, "specificity": 1.2}
_DENSITY_CAP = 12.0  # cap per-signal density so one spammy marker can't dominate


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def score_text(text: str, weights: dict[str, float] | None = None) -> tuple[dict[str, int], dict[str, float], float]:
    """Return (raw hit counts, per-100-token densities, composite score)."""
    weights = weights or _WEIGHTS
    per_100 = 100.0 / _estimate_tokens(text)

    hits: dict[str, int] = {}
    for name, pat in _PATTERNS.items():
        hits[name] = len(pat.findall(text))
    hits["specificity"] = sum(len(p.findall(text)) for p in _SPECIFIC)

    densities = {k: v * per_100 for k, v in hits.items()}
    score = sum(min(densities[k], _DENSITY_CAP) * weights.get(k, 0.0) for k in hits)
    return hits, densities, score


def score_chunk(chunk_id: str, text: str, weights: dict[str, float] | None = None):
    """Score one chunk. Returns a DifficultySignal (imported lazily to keep this
    module dependency-light)."""
    from .models import DifficultySignal

    hits, densities, score = score_text(text, weights)
    return DifficultySignal(chunk_id=chunk_id, hits=hits, densities=densities, score=round(score, 4))


def rank(signals, top_frac: float = 1.0, min_score: float = 0.0):
    """Sort difficulty signals descending; optionally keep the top fraction and
    drop anything at/below min_score. Returns the kept signals in ranked order."""
    ordered = sorted(signals, key=lambda s: s.score, reverse=True)
    ordered = [s for s in ordered if s.score > min_score]
    if top_frac < 1.0:
        keep = max(1, int(len(ordered) * top_frac))
        ordered = ordered[:keep]
    return ordered
