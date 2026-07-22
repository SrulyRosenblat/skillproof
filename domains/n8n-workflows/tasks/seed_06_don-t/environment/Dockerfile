# Self-contained task environment: a broken n8n workflow export plus the
# sample webhook payload it should be validated against. No skills/ here.
FROM python:3.12-slim

WORKDIR /workspace
COPY workflow.json /workspace/workflow.json
COPY sample_input.json /workspace/sample_input.json
