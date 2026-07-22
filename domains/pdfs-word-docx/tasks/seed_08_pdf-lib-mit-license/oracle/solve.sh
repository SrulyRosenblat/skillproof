#!/bin/bash
# Computes /workspace/report.pdf from /workspace/section_a.pdf and
# /workspace/section_b.pdf using the pdf-lib library, working around its
# defaults: PDF page dimensions are points (1/72in), so ISO A4 is
# 595.28x841.89pt, not 210x297; the coordinate origin is bottom-left with y
# increasing upward, so "near the top" needs a large y, not a small one;
# drawText() only renders bold if given an actual embedded bold font object
# (via embedFont), not a regular font plus a style flag; copying "only
# the 1st, 3rd, and 5th pages" of a document requires copyPages with those
# specific indices, not the whole page range; the header band must run
# edge-to-edge (x=0, full page width) rather than inset with side margins;
# and the document's Title metadata (set via setTitle, separate from the
# on-page heading drawn with drawText) must also be populated.
set -euo pipefail

node <<'JS'
const fs = require("fs");
const { PDFDocument, StandardFonts, rgb } = require("pdf-lib");

const A4 = [595.28, 841.89];
const HEADER_HEX = "D6E4F0";

function hexToRgb01(hex) {
  const r = parseInt(hex.slice(0, 2), 16) / 255;
  const g = parseInt(hex.slice(2, 4), 16) / 255;
  const b = parseInt(hex.slice(4, 6), 16) / 255;
  return rgb(r, g, b);
}

async function main() {
  const secABytes = fs.readFileSync("/workspace/section_a.pdf");
  const secBBytes = fs.readFileSync("/workspace/section_b.pdf");
  const secA = await PDFDocument.load(secABytes);
  const secB = await PDFDocument.load(secBBytes);

  const out = await PDFDocument.create();
  const regularFont = await out.embedFont(StandardFonts.Helvetica);
  const boldFont = await out.embedFont(StandardFonts.HelveticaBold);

  out.setTitle("Q1 Regional Summary");

  const [pageWidth, pageHeight] = A4;
  const cover = out.addPage([pageWidth, pageHeight]);

  const bandHeight = 70;
  const bandX = 0;
  const bandWidth = pageWidth; // edge-to-edge, no side margins
  const bandY = pageHeight - 150; // bottom edge of the band, upper half of the page
  const textX = 40;

  cover.drawRectangle({
    x: bandX,
    y: bandY,
    width: bandWidth,
    height: bandHeight,
    color: hexToRgb01(HEADER_HEX),
  });

  const titleSize = 24;
  cover.drawText("Q1 Regional Summary", {
    x: textX,
    y: bandY + bandHeight / 2 - titleSize / 2 + 6,
    size: titleSize,
    font: boldFont,
    color: rgb(0.1, 0.1, 0.1),
  });

  const subtitleSize = 14;
  cover.drawText("Prepared for the Executive Committee", {
    x: textX,
    y: bandY - 40, // below the band's lower edge, in the plain background
    size: subtitleSize,
    font: regularFont,
    color: rgb(0.2, 0.2, 0.2),
  });

  const aPages = await out.copyPages(secA, secA.getPageIndices());
  aPages.forEach((page) => out.addPage(page));

  // Only the 1st, 3rd, and 5th pages of section_b.pdf (0-indexed: 0, 2, 4).
  const bPages = await out.copyPages(secB, [0, 2, 4]);
  bPages.forEach((page) => out.addPage(page));

  const reportBytes = await out.save();
  fs.writeFileSync("/workspace/report.pdf", reportBytes);
  console.log(`wrote /workspace/report.pdf with ${out.getPageCount()} pages`);
}

main();
JS
