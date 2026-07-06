import json

import pytest

from skillproof.agent.tools import _resolve_workspace_path, dispatch
from skillproof.sandbox.container import ExecResult


class FakeSandbox:
    def __init__(self):
        self.files: dict[str, bytes] = {}
        self.commands: list[str] = []

    def exec(self, command, timeout=60, workdir="/workspace"):
        self.commands.append(command)
        return ExecResult(exit_code=0, stdout="ok", stderr="")

    def put_file(self, path, content):
        self.files[path] = content

    def get_file(self, path, limit_bytes=None):
        if path not in self.files:
            raise KeyError(path)
        return self.files[path]


def test_path_jail_rejects_traversal():
    with pytest.raises(ValueError):
        _resolve_workspace_path("../etc/passwd")
    with pytest.raises(ValueError):
        _resolve_workspace_path("/etc/passwd")
    with pytest.raises(ValueError):
        _resolve_workspace_path("a/../../b")


def test_path_jail_accepts_workspace_paths():
    assert _resolve_workspace_path("out/x.txt") == "/workspace/out/x.txt"
    assert _resolve_workspace_path("/workspace/x.txt") == "/workspace/x.txt"
    assert _resolve_workspace_path("./a/b") == "/workspace/a/b"


def test_read_file_allows_skill_mount_but_write_does_not():
    from skillproof.agent.tools import _resolve_path

    assert _resolve_path("/skill/SKILL.md", ("/workspace", "/skill")) == "/skill/SKILL.md"
    with pytest.raises(ValueError):
        _resolve_path("/skill/../etc", ("/workspace", "/skill"))
    with pytest.raises(ValueError):
        _resolve_workspace_path("/skill/SKILL.md")  # write_file jail: workspace only


def test_skill_access_tracking():
    from skillproof.agent.tools import extract_skill_accesses

    assert extract_skill_accesses("read_file", {"path": "/skill/REFERENCE.md"}) == [
        "/skill/REFERENCE.md"
    ]
    assert extract_skill_accesses("read_file", {"path": "out.txt"}) == []
    assert extract_skill_accesses(
        "bash", {"command": "python3 /skill/scripts/fill.py && cat /skill/FORMS.md"}
    ) == ["/skill/scripts/fill.py", "/skill/FORMS.md"]
    assert extract_skill_accesses("bash", {"command": "ls /skill"}) == ["/skill"]

    sb = FakeSandbox()
    accesses: set = set()
    dispatch("bash", json.dumps({"command": "head /skill/SKILL.md"}), sb, accesses)
    assert accesses == {"/skill/SKILL.md"}


def test_dispatch_bash():
    sb = FakeSandbox()
    out = json.loads(dispatch("bash", json.dumps({"command": "ls"}), sb))
    assert out["exit_code"] == 0
    assert sb.commands == ["ls"]


def test_dispatch_write_read_roundtrip():
    sb = FakeSandbox()
    dispatch("write_file", json.dumps({"path": "a.txt", "content": "hello"}), sb)
    out = json.loads(dispatch("read_file", json.dumps({"path": "a.txt"}), sb))
    assert out["content"] == "hello"


def test_dispatch_bad_args_returns_error_not_raises():
    sb = FakeSandbox()
    assert "error" in json.loads(dispatch("bash", "not json", sb))
    assert "error" in json.loads(dispatch("bash", "{}", sb))
    assert "error" in json.loads(dispatch("nope", "{}", sb))
    assert "error" in json.loads(
        dispatch("write_file", json.dumps({"path": "../x", "content": ""}), sb)
    )


def test_uplift_aggregation():
    from skillproof.eval.uplift import aggregate
    from skillproof.models import TrialResult

    def trial(arm, n, passed, error=None):
        return TrialResult(
            model="m", benchmark_id="b1", arm=arm, trial=n, passed=passed, error=error
        )

    trials = [
        trial("with_skill", 1, True),
        trial("with_skill", 2, True),
        trial("without_skill", 1, False),
        trial("without_skill", 2, True),
    ]
    (r,) = aggregate(trials)
    assert r.with_skill_pass_rate == 1.0
    assert r.without_skill_pass_rate == 0.5
    assert r.uplift == 0.5

    # error_policy=exclude drops errored trials from the denominator
    trials.append(trial("with_skill", 3, False, error="api down"))
    (r2,) = aggregate(trials, error_policy="exclude")
    assert r2.with_skill_pass_rate == 1.0
    (r3,) = aggregate(trials, error_policy="fail")
    assert r3.with_skill_pass_rate == pytest.approx(2 / 3, abs=1e-3)
