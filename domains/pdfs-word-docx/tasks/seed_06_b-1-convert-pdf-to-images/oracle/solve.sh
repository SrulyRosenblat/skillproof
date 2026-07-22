#!/bin/bash
# Computes /workspace/page_images/ from /workspace/input.pdf: rasterizes each
# page of the PDF to its own full-page image (via poppler's pdftoppm, the
# rasterization engine actually available in this offline sandbox), rather
# than pulling any picture assets embedded in the PDF's internal structure
# (which this particular PDF has none of -- it's built entirely from vector
# fills/text, so an embedded-asset extractor would yield zero files).
#
# This PDF's MediaBox (the full underlying sheet) is larger than its CropBox
# (the actual page area, which is what every viewer/printer actually shows).
# pdftoppm renders the MediaBox by default, so the -cropbox flag is required
# to get a faithful render of the page as it actually looks -- without it,
# the output includes a large blank margin outside the real page content.
set -euo pipefail

OUT_DIR="/workspace/page_images"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

pdftoppm -cropbox -png -r 150 /workspace/input.pdf "$OUT_DIR/page"

echo "wrote $(ls "$OUT_DIR" | wc -l) page images to $OUT_DIR"
