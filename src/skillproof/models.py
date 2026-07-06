"""Shared data models for the skillproof pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- skills


class Skill(BaseModel):
    """A parsed Claude-style skill folder."""

    name: str
    description: str = ""
    path: Path
    skill_md: str  # full SKILL.md body (without frontmatter)
    frontmatter: dict = Field(default_factory=dict)
    reference_files: dict[str, str] = Field(default_factory=dict)  # rel path -> text
    script_files: list[str] = Field(default_factory=list)  # rel paths, not chunked
    asset_files: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------- chunk/cluster


class Chunk(BaseModel):
    id: str  # e.g. "SKILL.md#usage-workflow"
    source_file: str  # path relative to skill root
    heading_path: list[str] = Field(default_factory=list)
    text: str
    token_estimate: int

    @property
    def embed_text(self) -> str:
        prefix = " > ".join(self.heading_path)
        return f"{prefix}\n\n{self.text}" if prefix else self.text


class Cluster(BaseModel):
    cluster_id: int
    label: str
    chunk_ids: list[str]
    centroid_distance_score: float = 0.0  # mean cosine distance to other selected centroids


class ClusterReport(BaseModel):
    skill_name: str
    skill_path: str
    embedding_provider: str
    embedding_model: str
    n_chunks: int
    k_selected: int
    all_clusters: list[Cluster]
    selected_cluster_ids: list[int]
    chunks: list[Chunk]
    created_at: datetime = Field(default_factory=utcnow)

    def selected_clusters(self) -> list[Cluster]:
        by_id = {c.cluster_id: c for c in self.all_clusters}
        return [by_id[i] for i in self.selected_cluster_ids]

    def chunks_for(self, cluster: Cluster) -> list[Chunk]:
        by_id = {c.id: c for c in self.chunks}
        return [by_id[cid] for cid in cluster.chunk_ids if cid in by_id]


# ----------------------------------------------------------------------- evaluation

Arm = Literal["with_skill", "without_skill"]


class TrialResult(BaseModel):
    model: str
    benchmark_id: str
    arm: Arm
    trial: int
    passed: bool
    grader_exit_code: int | None = None
    grader_output: str = ""
    judge_qa: list[dict] = Field(default_factory=list)  # LLM-judge Q&A audit trail
    turns_used: int = 0
    wall_seconds: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float | None = None  # reported by OpenRouter when available
    skill_files_read: list[str] | None = None  # /skill paths touched (with_skill arm)
    stop_reason: str = ""
    error: str | None = None  # infra error (API failure etc.), distinct from grader fail
    transcript_path: str | None = None


class ArmStats(BaseModel):
    """Efficiency aggregates over the non-errored trials of one arm."""

    trials: int = 0
    mean_turns: float = 0.0
    mean_tokens_in: float = 0.0
    mean_tokens_out: float = 0.0
    mean_wall_seconds: float = 0.0
    total_cost_usd: float | None = None  # None if the provider reported no costs


class BenchmarkModelResult(BaseModel):
    benchmark_id: str
    model: str
    with_skill_pass_rate: float
    without_skill_pass_rate: float
    uplift: float
    with_skill_stats: ArmStats = Field(default_factory=ArmStats)
    without_skill_stats: ArmStats = Field(default_factory=ArmStats)
    trials: list[TrialResult]


class RunResults(BaseModel):
    skill_name: str
    run_id: str
    config_snapshot: dict
    benchmark_hashes: dict[str, str] = Field(default_factory=dict)
    sandbox_image: str = ""
    results: list[BenchmarkModelResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
