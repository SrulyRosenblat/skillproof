#!/usr/bin/env bash
set -u

mkdir -p /logs/verifier

pytest -q -p no:cacheprovider /verifier/test_outputs.py > /logs/verifier/pytest.log 2>&1
status=$?

if [ "$status" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

cat /logs/verifier/pytest.log

exit 0
