#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "lib/prefs.js" ]; then
  echo "FAIL: /workspace/lib/prefs.js not found"
  exit 1
fi

node "$SCRIPT_DIR/check.js"
