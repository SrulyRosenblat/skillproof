# Self-contained task environment: report.docx + figure.png baked in, plus the
# pinned packages needed to edit/inspect a .docx package. No skills/ here.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
        pytest==8.3.4 \
        python-docx==1.1.2 \
        pillow==11.1.0 \
        lxml==5.3.0 \
        beautifulsoup4==4.12.3

WORKDIR /workspace
COPY report.docx /workspace/report.docx
COPY figure.png /workspace/figure.png
