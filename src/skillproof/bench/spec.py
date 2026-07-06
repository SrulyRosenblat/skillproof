"""benchmark.yaml schema — the contract benchmark authors (Codex) must satisfy."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

REQUIRED_FILES = ["benchmark.yaml", "README.md", "task_prompt.md"]


class Provenance(BaseModel):
    cluster_id: int
    cluster_label: str = ""
    chunk_ids: list[str] = Field(default_factory=list)


class Timeouts(BaseModel):
    agent_wall_seconds: int = 600
    grader_seconds: int = 120


class Limits(BaseModel):
    max_turns: int = 30


class GraderSpec(BaseModel):
    entrypoint: str = "grader/grade.sh"


class ValidationRecord(BaseModel):
    reference_passed: bool = False
    baseline_failed: bool = False
    determinism_checked: bool = False
    validated_at: datetime | None = None
    codex_attempts: int = 0


class BenchmarkSpec(BaseModel):
    schema_version: int = 1
    id: str
    skill_name: str
    title: str
    capability: str
    difficulty: str = "medium"  # easy | medium | hard
    provenance: Provenance
    timeouts: Timeouts = Field(default_factory=Timeouts)
    limits: Limits = Field(default_factory=Limits)
    grader: GraderSpec = Field(default_factory=GraderSpec)
    skill_assets_needed: bool = False
    validation: ValidationRecord = Field(default_factory=ValidationRecord)
    authoring: dict = Field(default_factory=dict)  # backend/model/tokens/cost, set by harness

    @field_validator("difficulty")
    @classmethod
    def _check_difficulty(cls, v: str) -> str:
        if v not in {"easy", "medium", "hard"}:
            raise ValueError(f"difficulty must be easy|medium|hard, got {v!r}")
        return v

    @property
    def is_validated(self) -> bool:
        return self.validation.reference_passed and self.validation.baseline_failed

    # ------------------------------------------------------------------ io

    @classmethod
    def load(cls, bench_dir: Path) -> "BenchmarkSpec":
        yaml_path = Path(bench_dir) / "benchmark.yaml"
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def save(self, bench_dir: Path) -> None:
        data = self.model_dump(mode="json")
        (Path(bench_dir) / "benchmark.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )


def structural_errors(bench_dir: Path) -> list[str]:
    """Check required files/dirs exist and the spec parses. Returns error strings."""
    bench_dir = Path(bench_dir)
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (bench_dir / name).is_file():
            errors.append(f"missing required file: {name}")
    if "benchmark.yaml" not in " ".join(errors):
        try:
            spec = BenchmarkSpec.load(bench_dir)
        except Exception as e:  # surface parse errors verbatim to the repair loop
            errors.append(f"benchmark.yaml failed to parse/validate: {e}")
            return errors
        grader_path = bench_dir / spec.grader.entrypoint
        if not grader_path.is_file():
            errors.append(f"grader entrypoint missing: {spec.grader.entrypoint}")
        ref_dir = bench_dir / "reference_solution"
        if not ref_dir.is_dir() or not any(ref_dir.rglob("*")):
            errors.append("reference_solution/ is missing or empty")
        task = (bench_dir / "task_prompt.md")
        if task.is_file() and len(task.read_text(encoding="utf-8").strip()) < 40:
            errors.append("task_prompt.md is suspiciously short (<40 chars)")
    return errors
