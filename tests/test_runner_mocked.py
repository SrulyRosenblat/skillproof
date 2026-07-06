"""End-to-end trial test with a scripted fake OpenRouter client.

Everything is real (Docker sandbox, workspace snapshot, grading) except the
chat-completions API, which replays a fixed tool-call script.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from skillproof.bench.spec import BenchmarkSpec, Provenance
from skillproof.config import Config
from skillproof.eval.runner import run_trial
from skillproof.skill_loader import load_skill

pytestmark = pytest.mark.docker

FIXTURE = Path(__file__).parent / "fixtures" / "sample_skill"


def _resp(content=None, tool_calls=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content, tool_calls=tool_calls),
                finish_reason="tool_calls" if tool_calls else "stop",
            )
        ],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )


def _tool_call(cid, name, args):
    return SimpleNamespace(
        id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(args))
    )


class FakeClient:
    """Replays a script: writes the expected output file, then finishes."""

    def __init__(self, script):
        self._script = list(script)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return self._script.pop(0)


def _make_bench(root: Path) -> tuple[Path, BenchmarkSpec]:
    bench = root / "bench_01_upper"
    (bench / "files").mkdir(parents=True)
    (bench / "grader").mkdir()
    (bench / "reference_solution").mkdir()
    spec = BenchmarkSpec(
        id="bench_01_upper", skill_name="csv-wrangler", title="t", capability="c",
        provenance=Provenance(cluster_id=0),
    )
    spec.validation.reference_passed = True
    spec.validation.baseline_failed = True
    spec.save(bench)
    (bench / "README.md").write_text("#")
    (bench / "task_prompt.md").write_text(
        "Read /workspace/input.txt, uppercase it, write /workspace/out.txt."
    )
    (bench / "files" / "input.txt").write_text("hello world\n")
    (bench / "grader" / "grade.sh").write_text(
        "#!/bin/bash\nset -e\ngrep -q 'HELLO WORLD' out.txt\n"
    )
    (bench / "reference_solution" / "out.txt").write_text("HELLO WORLD\n")
    return bench, spec


def _run(monkeypatch, tmp_path, script, arm):
    bench, spec = _make_bench(tmp_path / arm)
    cfg = Config()
    cfg.results_dir = tmp_path / "results" / arm
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "skillproof.agent.loop._make_client", lambda _cfg: FakeClient(script)
    )
    skill = load_skill(FIXTURE)
    return run_trial(
        skill, bench, spec, "fake/model", arm, 1, cfg, tmp_path / "run" / arm
    )


def _success_script():
    return [
        _resp(tool_calls=[
            _tool_call("c1", "bash",
                       {"command": "tr '[:lower:]' '[:upper:]' < input.txt > out.txt"})
        ]),
        _resp(content="Done."),
    ]


def test_trial_passes_and_grades(monkeypatch, tmp_path):
    result = _run(monkeypatch, tmp_path, _success_script(), "with_skill")
    assert result.error is None
    assert result.passed, result.grader_output
    assert result.turns_used == 2
    assert result.stop_reason == "completed"
    transcript = Path(result.transcript_path).read_text()
    assert '"tool_result"' in transcript and '"grade"' in transcript


def test_trial_fails_when_agent_does_nothing(monkeypatch, tmp_path):
    result = _run(monkeypatch, tmp_path, [_resp(content="I give up.")], "without_skill")
    assert result.error is None
    assert not result.passed
    assert result.grader_exit_code != 0


def test_with_skill_arm_mounts_skill_and_tracks_reads(monkeypatch, tmp_path):
    script = [
        _resp(tool_calls=[_tool_call("c1", "bash", {"command": "ls /skill"})]),
        _resp(tool_calls=[
            _tool_call("c2", "read_file", {"path": "/skill/references/guide.md"})
        ]),
        _resp(tool_calls=[
            _tool_call("c3", "bash",
                       {"command": "tr '[:lower:]' '[:upper:]' < input.txt > out.txt"})
        ]),
        _resp(content="Done."),
    ]
    result = _run(monkeypatch, tmp_path, script, "with_skill")
    assert result.passed
    transcript = Path(result.transcript_path).read_text()
    assert "SKILL.md" in transcript  # ls /skill saw the mounted skill
    assert "Deduplication" in transcript  # read_file returned real reference content
    assert result.skill_files_read == ["/skill", "/skill/references/guide.md"]


def test_without_skill_arm_has_no_skill_mount(monkeypatch, tmp_path):
    script = [
        _resp(tool_calls=[_tool_call("c1", "bash", {"command": "ls /skill"})]),
        _resp(content="Done."),
    ]
    result = _run(monkeypatch, tmp_path, script, "without_skill")
    assert result.skill_files_read is None
    transcript = Path(result.transcript_path).read_text()
    # /skill exists in the image but must be empty in this arm
    assert "SKILL.md" not in transcript
