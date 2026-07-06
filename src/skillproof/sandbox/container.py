"""Docker sandbox: fresh, network-less container per trial / grading run.

All untrusted code (agent commands, graders) executes here. API calls to
OpenRouter/Codex happen on the host, never inside the container.
"""

from __future__ import annotations

import io
import subprocess
import tarfile
import threading
from dataclasses import dataclass
from pathlib import Path

import docker
from docker.errors import ImageNotFound

from ..config import SandboxConfig

# Serializes automatic image rebuilds across parallel trials.
_build_lock = threading.Lock()

_FIXED_ENV = {
    "TZ": "UTC",
    "LC_ALL": "C.UTF-8",
    "LANG": "C.UTF-8",
    "PYTHONHASHSEED": "0",
    "SOURCE_DATE_EPOCH": "0",
}

WORKSPACE = "/workspace"
SKILL_MOUNT = "/skill"
GRADER_MOUNT = "/grader"


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str
    truncated: bool = False
    timed_out: bool = False


def _truncate(data: bytes | None, limit: int) -> tuple[str, bool]:
    if not data:
        return "", False
    truncated = len(data) > limit
    text = data[:limit].decode("utf-8", errors="replace")
    if truncated:
        text += f"\n... [output truncated at {limit} bytes]"
    return text, truncated


# uid/gid of the non-root `agent` user baked into the sandbox image; forced onto
# every tar member so the agent can modify fixture files in place.
_AGENT_UID = 1001


def _as_agent(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = info.gid = _AGENT_UID
    info.uname = info.gname = "agent"
    return info


def _tar_of_dir(host_dir: Path, arcname_prefix: str = "") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for p in sorted(Path(host_dir).rglob("*")):
            if p.is_file():
                arcname = str(Path(arcname_prefix) / p.relative_to(host_dir))
                tar.add(p, arcname=arcname, filter=_as_agent)
    return buf.getvalue()


def _tar_of_bytes(path: str, content: bytes) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=path)
        info.size = len(content)
        info.mode = 0o644
        tar.addfile(_as_agent(info), io.BytesIO(content))
    return buf.getvalue()


class Sandbox:
    """Context manager around a single disposable container."""

    def __init__(self, cfg: SandboxConfig):
        self.cfg = cfg
        self._client = docker.from_env()
        self._container = None

    def _ensure_image(self) -> None:
        """Make sure the sandbox image is usable; rebuild it if not.

        Handles both a missing image and the "zombie tag" state seen with the
        containerd image store, where `image ls` shows the tag with 0B content but
        inspect returns 404.
        """
        try:
            self._client.images.get(self.cfg.image)
            return
        except ImageNotFound:
            pass
        with _build_lock:
            try:  # another thread may have rebuilt while we waited
                self._client.images.get(self.cfg.image)
                return
            except ImageNotFound:
                pass
            dockerfile_dir = Path(self.cfg.dockerfile_dir)
            if not (dockerfile_dir / "Dockerfile").is_file():
                raise RuntimeError(
                    f"Sandbox image {self.cfg.image!r} not found and no Dockerfile at "
                    f"{dockerfile_dir}/. Run `skillproof build-image`."
                )
            subprocess.run(["docker", "rmi", "-f", self.cfg.image],
                           capture_output=True, text=True)
            build = subprocess.run(
                ["docker", "build", "--provenance=false", "--sbom=false",
                 "-t", self.cfg.image, str(dockerfile_dir)],
                capture_output=True, text=True, timeout=900,
            )
            if build.returncode != 0:
                raise RuntimeError(
                    f"Sandbox image {self.cfg.image!r} was missing and the automatic "
                    f"rebuild failed:\n{build.stderr[-2000:]}"
                )
            self._client.images.get(self.cfg.image)

    def __enter__(self) -> "Sandbox":
        self._ensure_image()
        self._container = self._client.containers.run(
            self.cfg.image,
            command=["sleep", "infinity"],
            detach=True,
            network_mode="none",
            mem_limit=self.cfg.mem_limit,
            nano_cpus=int(self.cfg.cpus * 1e9),
            pids_limit=self.cfg.pids_limit,
            security_opt=["no-new-privileges"],
            environment=_FIXED_ENV,
            working_dir=WORKSPACE,
        )
        return self

    def __exit__(self, *exc) -> None:
        self.destroy()

    def destroy(self) -> None:
        if self._container is not None:
            try:
                self._container.remove(force=True)
            finally:
                self._container = None

    @property
    def image_digest(self) -> str:
        image = self._client.images.get(self.cfg.image)
        return (image.attrs.get("RepoDigests") or [image.short_id])[0]

    # ------------------------------------------------------------------ exec

    def exec(self, command: str, timeout: int = 60, workdir: str = WORKSPACE) -> ExecResult:
        """Run a shell command; on timeout the whole container is killed."""
        assert self._container is not None
        result: dict = {}

        def _run():
            try:
                code, output = self._container.exec_run(
                    ["bash", "-lc", command], demux=True, workdir=workdir
                )
                result["code"], result["output"] = code, output
            except Exception as e:  # container killed from under us, etc.
                result["error"] = str(e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self._container.kill()
            return ExecResult(
                exit_code=124,
                stdout="",
                stderr=f"command killed after {timeout}s timeout",
                timed_out=True,
            )
        if "error" in result:
            return ExecResult(exit_code=125, stdout="", stderr=result["error"])
        stdout_b, stderr_b = result["output"] or (b"", b"")
        limit = self.cfg.output_limit_bytes
        stdout, t1 = _truncate(stdout_b, limit)
        stderr, t2 = _truncate(stderr_b, limit)
        return ExecResult(exit_code=result["code"], stdout=stdout, stderr=stderr,
                          truncated=t1 or t2)

    # ------------------------------------------------------------- file transfer

    def put_dir(self, host_dir: Path, container_path: str) -> None:
        assert self._container is not None
        self.exec(f"mkdir -p {container_path}", timeout=10)
        if any(Path(host_dir).rglob("*")):
            self._container.put_archive(container_path, _tar_of_dir(host_dir))

    def put_file(self, container_path: str, content: bytes) -> None:
        assert self._container is not None
        p = Path(container_path)
        self.exec(f"mkdir -p {p.parent}", timeout=10)
        self._container.put_archive(str(p.parent), _tar_of_bytes(p.name, content))

    def get_file(self, container_path: str, limit_bytes: int | None = None) -> bytes:
        assert self._container is not None
        stream, _stat = self._container.get_archive(container_path)
        buf = io.BytesIO(b"".join(stream))
        with tarfile.open(fileobj=buf) as tar:
            member = tar.getmembers()[0]
            f = tar.extractfile(member)
            data = f.read() if f else b""
        return data[:limit_bytes] if limit_bytes else data

    def snapshot_workspace(self) -> bytes:
        """Tar of /workspace contents, used to grade in a fresh container."""
        assert self._container is not None
        stream, _stat = self._container.get_archive(WORKSPACE)
        return b"".join(stream)

    def restore_workspace(self, snapshot_tar: bytes) -> None:
        """Restore a snapshot taken by snapshot_workspace() into /workspace."""
        assert self._container is not None
        # Archive contains a top-level "workspace/" folder; extract at parent.
        self._container.put_archive("/", snapshot_tar)
