FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash coreutils git jq ripgrep poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pytest==8.3.4 \
    pyyaml==6.0.2

WORKDIR /workspace

COPY workflow.json /workspace/workflow.json
