"""JSONL transcript capture for audit: every model turn and tool execution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class Transcript:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", encoding="utf-8")

    def event(self, type_: str, **payload) -> None:
        record = {"ts": datetime.now(timezone.utc).isoformat(), "type": type_, **payload}
        self._fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "Transcript":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
