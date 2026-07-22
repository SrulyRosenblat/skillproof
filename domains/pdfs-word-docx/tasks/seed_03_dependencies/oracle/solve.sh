#!/bin/bash
# Renders every page of /workspace/report.docx to its own full-page PNG.
# No LibreOffice in this sandbox, so docx->PDF is done by hand (render_pdf.py:
# walk paragraphs/pictures via python-docx, redraw each page with reportlab)
# before rasterizing each PDF page with poppler's pdftoppm.
set -euo pipefail

cd /workspace

python3 "$(dirname "$0")/render_pdf.py"

PAGES=$(pdfinfo /workspace/report.pdf | awk '/^Pages:/{print $2}')

for ((n = 1; n <= PAGES; n++)); do
    pdftoppm -png -f "$n" -l "$n" -r 150 -singlefile \
        /workspace/report.pdf "/workspace/page${n}_thumbnail"
done
