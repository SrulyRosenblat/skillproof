#!/bin/bash
# Oracle: computes the solution from the task inputs (notes.txt, guidelines/,
# themes/) rather than hardcoding the output. Running this then the verifier
# must yield reward 1.0.
set -euo pipefail

python3 "$(dirname "$0")/build_report.py"
