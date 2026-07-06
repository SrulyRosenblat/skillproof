#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path
import sys

expected = [
    "pillow>=10.0.0",
    "imageio>=2.31.0",
    "imageio-ffmpeg>=0.4.9",
    "numpy>=1.24.0",
]

path = Path.cwd() / "requirements.txt"
if not path.exists():
    print("Missing requirements.txt in /workspace", file=sys.stderr)
    sys.exit(1)

raw = path.read_text(encoding="utf-8")
if raw != raw.strip() + "\n" and raw != raw.strip():
    print("requirements.txt must not contain leading/trailing blank lines or whitespace-only padding", file=sys.stderr)
    sys.exit(1)

lines = raw.splitlines()
if lines != expected:
    print("requirements.txt contents did not match the required packages, versions, or order", file=sys.stderr)
    print("Expected:", expected, file=sys.stderr)
    print("Actual:", lines, file=sys.stderr)
    sys.exit(1)

for line in lines:
    if line != line.strip():
        print("Each dependency line must be trimmed", file=sys.stderr)
        sys.exit(1)
    if line.lower() != line:
        print("Dependencies must be lowercase", file=sys.stderr)
        sys.exit(1)
    if " " in line or "\t" in line:
        print("Dependencies must not contain whitespace", file=sys.stderr)
        sys.exit(1)

print("PASS")
PY
