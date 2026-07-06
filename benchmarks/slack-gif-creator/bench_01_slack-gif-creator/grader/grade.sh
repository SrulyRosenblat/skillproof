#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d /workspace ]; then
  cd /workspace
fi
pytest -q "$SCRIPT_DIR/test_benchmark.py"
