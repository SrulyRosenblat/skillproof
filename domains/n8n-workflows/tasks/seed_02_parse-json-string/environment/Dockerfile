# Self-contained task environment: an n8n Code-node stub plus the harness
# that reproduces how n8n executes it. No skills/ here.
FROM python:3.12-slim

WORKDIR /workspace
COPY input.json /workspace/input.json
COPY code.py /workspace/code.py
COPY node_runtime.py /workspace/node_runtime.py
