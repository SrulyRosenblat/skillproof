# Self-contained task environment: report.docx (a 3-page Word document,
# each page carrying its own embedded picture) baked in, plus the tool
# chain needed to turn an office document's pages into raster images.
# No LibreOffice here (not available in the shared eval sandbox either):
# docx -> PDF is done by hand with python-docx + reportlab, then Poppler
# rasterizes each PDF page to PNG. No skills/ here.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        pytest==8.3.4 \
        python-docx==1.1.2 \
        reportlab==4.2.5 \
        pillow==11.1.0 \
        numpy==2.2.1

WORKDIR /workspace
COPY report.docx /workspace/report.docx
