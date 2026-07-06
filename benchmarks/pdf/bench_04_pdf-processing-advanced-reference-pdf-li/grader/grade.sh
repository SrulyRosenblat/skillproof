#!/usr/bin/env bash
set -euo pipefail

cd /workspace

if [ ! -f build_digest.js ]; then
    echo "FAIL: /workspace/build_digest.js does not exist"
    exit 1
fi

# task_prompt.md explicitly mandates that build_digest.js load the vendored
# pdf-lib library from this exact path, so checking for that literal token
# is checking a stated requirement, not reverse-engineering the solution.
if ! grep -q "lib/pdf-lib.min.js" build_digest.js; then
    echo "FAIL: build_digest.js must load the vendored library at lib/pdf-lib.min.js"
    exit 1
fi

# Force a fresh run so the graded digest.pdf is actually produced by the
# submitted script, not a pre-baked file left over from experimentation.
rm -f digest.pdf

if ! node build_digest.js; then
    echo "FAIL: node build_digest.js exited with an error"
    exit 1
fi

if [ ! -f digest.pdf ]; then
    echo "FAIL: build_digest.js did not produce /workspace/digest.pdf"
    exit 1
fi

python3 /grader/check_digest.py
