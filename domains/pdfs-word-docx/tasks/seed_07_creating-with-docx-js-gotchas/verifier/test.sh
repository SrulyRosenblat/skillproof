#!/bin/bash
# Upstream verifier contract: run pytest on /verifier/test_outputs.py, write
# scalar reward 0|1 to /logs/verifier/reward.txt, ALWAYS exit 0 — the reward
# file is the verdict.
mkdir -p /logs/verifier

# Sandbox is OFFLINE — pytest and lxml are preinstalled in the image. Any
# install attempt must be non-fatal.
pip3 install --break-system-packages pytest==8.3.4 lxml==5.3.0 >/dev/null 2>&1 || true

pytest /verifier/test_outputs.py -rA -v
if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi

exit 0
