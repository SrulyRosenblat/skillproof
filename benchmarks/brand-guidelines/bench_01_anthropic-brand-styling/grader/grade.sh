#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

cd "$WORKSPACE_DIR"
pytest -q "$SCRIPT_DIR/test_grader.py"
