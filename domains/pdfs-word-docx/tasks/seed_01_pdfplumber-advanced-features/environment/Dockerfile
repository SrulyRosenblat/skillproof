# Self-contained task environment: tags.pdf baked in, plus the pinned
# packages needed to read PDF text/coordinates. No skills/ here.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
        pytest==8.3.4 \
        pypdf==5.1.0 \
        pdfplumber==0.11.10

WORKDIR /workspace
COPY tags.pdf /workspace/tags.pdf
