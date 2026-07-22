# Self-contained task environment: input.pdf baked in, plus poppler-utils
# (the only PDF-rasterization engine available -- no LibreOffice, no
# pdf2image/PyMuPDF pip packages) and the pinned Python libs needed to
# inspect the PDF and the produced images. No skills/ here.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        pytest==8.3.4 \
        numpy==2.2.1 \
        pillow==11.1.0 \
        pypdf==5.1.0

WORKDIR /workspace
COPY input.pdf /workspace/input.pdf
