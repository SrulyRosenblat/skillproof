"""Docker-dependent tests: pytest -m docker (requires built sandbox image)."""

from pathlib import Path

import pytest

from skillproof.bench.spec import BenchmarkSpec, Provenance
from skillproof.config import SandboxConfig
from skillproof.sandbox.container import Sandbox
from skillproof.sandbox.grader import grade_dirs

pytestmark = pytest.mark.docker

CFG = SandboxConfig()


@pytest.fixture(scope="module")
def sandbox():
    with Sandbox(CFG) as sb:
        yield sb


def test_exec_and_exit_codes(sandbox):
    assert sandbox.exec("echo hi").stdout.strip() == "hi"
    assert sandbox.exec("exit 3").exit_code == 3


def test_file_roundtrip(sandbox):
    sandbox.put_file("/workspace/sub/x.txt", b"payload")
    assert sandbox.get_file("/workspace/sub/x.txt") == b"payload"


def test_network_is_off(sandbox):
    r = sandbox.exec("python3 -c \"import urllib.request as u; u.urlopen('http://example.com', timeout=3)\"", timeout=15)
    assert r.exit_code != 0


def test_timeout_kills(tmp_path):
    with Sandbox(CFG) as sb:
        r = sb.exec("sleep 30", timeout=2)
        assert r.timed_out
        assert r.exit_code == 124


def test_grade_dirs_reference_vs_baseline(tmp_path):
    bench = tmp_path / "bench_01_smoke"
    (bench / "files").mkdir(parents=True)
    (bench / "grader").mkdir()
    (bench / "reference_solution").mkdir()
    spec = BenchmarkSpec(
        id="bench_01_smoke", skill_name="s", title="t", capability="c",
        provenance=Provenance(cluster_id=0),
    )
    spec.save(bench)
    (bench / "README.md").write_text("#")
    (bench / "task_prompt.md").write_text("Write done into out.txt in /workspace." * 2)
    (bench / "files" / "input.txt").write_text("hello")
    (bench / "grader" / "grade.sh").write_text("#!/bin/bash\ngrep -q done out.txt\n")
    (bench / "reference_solution" / "out.txt").write_text("done\n")

    ref = grade_dirs(bench, spec, CFG, [bench / "files", bench / "reference_solution"])
    assert ref.passed, ref.output
    base = grade_dirs(bench, spec, CFG, [bench / "files"])
    assert not base.passed


def test_workspace_snapshot_roundtrip():
    with Sandbox(CFG) as sb:
        sb.put_file("/workspace/result.txt", b"42")
        snap = sb.snapshot_workspace()
    with Sandbox(CFG) as sb2:
        sb2.restore_workspace(snap)
        assert sb2.get_file("/workspace/result.txt") == b"42"
