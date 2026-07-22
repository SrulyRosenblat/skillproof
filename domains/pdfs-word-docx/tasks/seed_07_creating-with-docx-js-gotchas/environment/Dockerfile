# Self-contained task environment: data.json + logo.png baked in, plus the
# pinned Node/Python packages needed to generate and inspect a .docx package.
# No skills/ here.
#
# node_modules/docx (and its transitive deps) is also vendored under
# environment/ verbatim, because skillproof's local runner ignores this
# Dockerfile and just copies environment/ files into an offline, network-less
# /workspace -- it never runs `npm install docx` itself.
FROM node:20-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
        pytest==8.3.4 \
        lxml==5.3.0

WORKDIR /workspace
RUN npm install docx@9.7.1

COPY data.json /workspace/data.json
COPY logo.png /workspace/logo.png
