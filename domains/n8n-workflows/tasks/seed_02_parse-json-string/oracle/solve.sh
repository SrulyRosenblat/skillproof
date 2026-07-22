#!/bin/bash
# Writes a generic n8n Code (Python) node body to /workspace/code.py: it
# parses whatever batch it is handed at run time (counts are computed from
# the actual items, not hardcoded), so it works against any batch shaped
# like the one described in the task prompt.
set -euo pipefail

cat > /workspace/code.py <<'PY'
import json

results = []
valid_count = 0
invalid_count = 0

for item in _input.all():
    payload = item["json"]["payload"]
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as e:
        invalid_count += 1
        results.append({"json": {"parsed": None, "error": str(e)}})
    else:
        valid_count += 1
        results.append({"json": {"parsed": value, "error": None}})

manifest_json = json.dumps({
    "valid_count": valid_count,
    "invalid_count": invalid_count,
})
results.append({"json": {"manifest_json": manifest_json}})

return results
PY

echo "wrote /workspace/code.py"
