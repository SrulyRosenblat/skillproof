#!/bin/bash
# Upstream verifier contract: run pytest on /verifier/test_outputs.py, write
# scalar reward 0|1 to /logs/verifier/reward.txt, ALWAYS exit 0.
mkdir -p /logs/verifier

# Sandbox is OFFLINE -- these are already preinstalled in the image; the
# install attempt is a non-fatal no-op safety net.
pip3 install --break-system-packages pytest==8.3.4 pyyaml==6.0.2 python-docx==1.1.2 >/dev/null 2>&1 || true

pytest /verifier/test_outputs.py -rA -v
if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi

exit 0
