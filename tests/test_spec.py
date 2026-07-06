from pathlib import Path

import pytest

from skillproof.bench.spec import BenchmarkSpec, Provenance, structural_errors
from skillproof.bench.store import bench_dir_name, content_hash


def _make_valid_bench(root: Path) -> Path:
    bench = root / "bench_01_test"
    (bench / "files").mkdir(parents=True)
    (bench / "grader").mkdir()
    (bench / "reference_solution").mkdir()
    spec = BenchmarkSpec(
        id="bench_01_test",
        skill_name="sample",
        title="t",
        capability="c",
        provenance=Provenance(cluster_id=0),
    )
    spec.save(bench)
    (bench / "README.md").write_text("# doc")
    (bench / "task_prompt.md").write_text("Create /workspace/out.txt containing the word done.")
    (bench / "grader" / "grade.sh").write_text("#!/bin/bash\ngrep -q done out.txt\n")
    (bench / "reference_solution" / "out.txt").write_text("done\n")
    (bench / "files" / "input.txt").write_text("hello\n")
    return bench


def test_spec_roundtrip(tmp_path):
    bench = _make_valid_bench(tmp_path)
    spec = BenchmarkSpec.load(bench)
    assert spec.id == "bench_01_test"
    assert not spec.is_validated
    spec.validation.reference_passed = True
    spec.validation.baseline_failed = True
    spec.save(bench)
    assert BenchmarkSpec.load(bench).is_validated


def test_structural_errors_ok(tmp_path):
    bench = _make_valid_bench(tmp_path)
    assert structural_errors(bench) == []


def test_structural_errors_missing_files(tmp_path):
    bench = _make_valid_bench(tmp_path)
    (bench / "grader" / "grade.sh").unlink()
    (bench / "README.md").unlink()
    errors = " ".join(structural_errors(bench))
    assert "README.md" in errors
    assert "grader" in errors


def test_difficulty_validation(tmp_path):
    with pytest.raises(ValueError):
        BenchmarkSpec(
            id="x", skill_name="s", title="t", capability="c",
            difficulty="impossible", provenance=Provenance(cluster_id=0),
        )


def test_bench_dir_name():
    assert bench_dir_name(3, "PDF Form Filling!") == "bench_03_pdf-form-filling"


def test_content_hash_stable_and_sensitive(tmp_path):
    bench = _make_valid_bench(tmp_path)
    h1 = content_hash(bench)
    assert content_hash(bench) == h1
    (bench / "files" / "input.txt").write_text("changed\n")
    assert content_hash(bench) != h1
