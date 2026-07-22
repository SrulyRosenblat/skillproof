# Self-contained task environment: section_a.pdf + section_b.pdf baked in,
# plus the pinned Node/Python packages needed to generate and inspect a PDF
# report. No skills/ here.
#
# node_modules/pdf-lib (and its transitive deps) is also vendored under
# environment/ verbatim, because skillproof's local runner ignores this
# Dockerfile and just copies environment/ files into an offline, network-less
# /workspace -- it never runs `npm install pdf-lib` itself.
FROM node:20-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip poppler-utils && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
        pytest==8.3.4 \
        pypdf==5.1.0 \
        pillow==11.1.0

WORKDIR /workspace
RUN npm install pdf-lib@1.17.1

COPY package.json /workspace/package.json
COPY node_modules /workspace/node_modules
COPY section_a.pdf /workspace/section_a.pdf
COPY section_b.pdf /workspace/section_b.pdf
