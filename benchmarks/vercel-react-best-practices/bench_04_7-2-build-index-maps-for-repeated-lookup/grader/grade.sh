#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${WORKSPACE_DIR:-/workspace}" || exit 1

if [ ! -f solve.js ]; then
  echo "FAIL: solve.js not found in $(pwd)" >&2
  exit 1
fi

rm -rf output
export INSTRUMENT_OUTPUT="/tmp/instrument_counts.json"
rm -f "$INSTRUMENT_OUTPUT"

node -r "$SCRIPT_DIR/instrument.js" solve.js
NODE_STATUS=$?
if [ $NODE_STATUS -ne 0 ]; then
  echo "FAIL: solve.js exited with status $NODE_STATUS" >&2
  exit 1
fi

if [ ! -f "$INSTRUMENT_OUTPUT" ]; then
  echo "FAIL: instrumentation data was not produced (did solve.js call process.exit()?)" >&2
  exit 1
fi

python3 "$SCRIPT_DIR/check.py"
exit $?
