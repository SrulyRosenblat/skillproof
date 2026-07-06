#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "src/access-control.js" ]; then
  echo "Missing required file: $(pwd)/src/access-control.js"
  exit 1
fi

node "$SCRIPT_DIR/check.js"
