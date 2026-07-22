# Self-contained task environment: the raw status notes, the formatting
# guides, and the theme files are all baked in, plus the pinned packages
# needed to build and read .docx files. No skills/ here.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
        pytest==8.3.4 \
        pyyaml==6.0.2 \
        python-docx==1.1.2

WORKDIR /workspace
COPY notes.txt /workspace/notes.txt
COPY guidelines/ /workspace/guidelines/
COPY themes/ /workspace/themes/
RUN mkdir -p /workspace/output
