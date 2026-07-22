# Self-contained task environment: an n8n workflow export, a queued batch of
# update operations, and an evaluation run result, all baked in. No skills/ here.
FROM python:3.12-slim

WORKDIR /workspace
COPY workflow.json /workspace/workflow.json
COPY operations.json /workspace/operations.json
COPY run_metrics.json /workspace/run_metrics.json
