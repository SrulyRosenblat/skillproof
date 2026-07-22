#!/usr/bin/env python3
"""Convert report.docx to report.pdf without LibreOffice.

The sandbox has no soffice binary, so the usual docx->PDF hop isn't
available. Instead: walk the document's paragraphs in order, splitting into
pages on explicit page-break runs, and redraw each page's text and embedded
pictures (at their true docx-specified size and page position) onto a
same-sized PDF page with reportlab.
"""
import io

import docx
from docx.oxml.ns import qn
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

SRC = "/workspace/report.docx"
DST = "/workspace/report.pdf"


def load_pages(path):
    doc = docx.Document(path)
    pages = []
    current = {"lines": [], "images": []}
    for para in doc.paragraphs:
        p = para._p
        text = para.text.strip()
        if text:
            current["lines"].append(text)
        for drawing in p.iter(qn("w:drawing")):
            blips = drawing.findall(f".//{qn('a:blip')}")
            extents = drawing.findall(f".//{qn('wp:extent')}")
            if blips and extents:
                rid = blips[0].get(qn("r:embed"))
                cx = int(extents[0].get("cx"))
                cy = int(extents[0].get("cy"))
                blob = doc.part.related_parts[rid].blob
                current["images"].append((blob, cx / 914400, cy / 914400))
        if any(br.get(qn("w:type")) == "page" for br in p.iter(qn("w:br"))):
            pages.append(current)
            current = {"lines": [], "images": []}
    pages.append(current)
    return doc, pages


def main():
    doc, pages = load_pages(SRC)
    section = doc.sections[0]
    page_w = section.page_width / 914400 * inch
    page_h = section.page_height / 914400 * inch

    c = canvas.Canvas(DST, pagesize=(page_w, page_h))
    margin = 1 * inch
    for page in pages:
        y = page_h - margin
        for i, line in enumerate(page["lines"]):
            font, size = ("Helvetica-Bold", 16) if i == 0 else ("Helvetica", 11)
            c.setFont(font, size)
            c.drawString(margin, y, line)
            y -= size * 1.6
        y -= 0.3 * inch
        for blob, w_in, h_in in page["images"]:
            img = ImageReader(io.BytesIO(blob))
            c.drawImage(img, margin, y - h_in * inch, width=w_in * inch, height=h_in * inch)
            y -= h_in * inch + 0.3 * inch
        c.showPage()
    c.save()


if __name__ == "__main__":
    main()
