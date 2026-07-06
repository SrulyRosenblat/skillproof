"""Helpers for the benchmarks/<skill>/ output directory."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ..models import ClusterReport
from .spec import BenchmarkSpec


def skill_bench_dir(benchmarks_root: Path, skill_name: str) -> Path:
    return Path(benchmarks_root) / skill_name


def clusters_path(benchmarks_root: Path, skill_name: str) -> Path:
    return skill_bench_dir(benchmarks_root, skill_name) / "clusters.json"


def save_cluster_report(report: ClusterReport, benchmarks_root: Path) -> Path:
    path = clusters_path(benchmarks_root, report.skill_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_cluster_report(benchmarks_root: Path, skill_name: str) -> ClusterReport:
    path = clusters_path(benchmarks_root, skill_name)
    return ClusterReport.model_validate_json(path.read_text(encoding="utf-8"))


def bench_dir_name(index: int, label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:40] or "capability"
    return f"bench_{index:02d}_{slug}"


def list_benchmarks(benchmarks_root: Path, skill_name: str, validated_only: bool = True):
    """Yield (bench_dir, BenchmarkSpec) for each benchmark of a skill."""
    root = skill_bench_dir(benchmarks_root, skill_name)
    if not root.is_dir():
        return
    for bench_dir in sorted(root.iterdir()):
        if not bench_dir.is_dir() or not bench_dir.name.startswith("bench_"):
            continue
        if (bench_dir / "FAILED.md").exists():
            continue
        try:
            spec = BenchmarkSpec.load(bench_dir)
        except Exception:
            continue
        if validated_only and not spec.is_validated:
            continue
        yield bench_dir, spec


def content_hash(bench_dir: Path) -> str:
    """Stable hash of a benchmark dir's contents (for audit trails)."""
    h = hashlib.sha256()
    for p in sorted(Path(bench_dir).rglob("*")):
        if p.is_file() and ".codex_logs" not in p.parts:
            h.update(str(p.relative_to(bench_dir)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:16]
