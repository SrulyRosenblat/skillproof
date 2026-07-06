#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
GRADER_DIR="${GRADER_DIR:-/grader}"

cd "$WORKSPACE_DIR"
pytest -q -o "cache_dir=$WORKSPACE_DIR/.pytest_cache" "$GRADER_DIR/test_grader.py"
