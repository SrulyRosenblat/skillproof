"""Deterministic checks for /workspace/report.pdf, built from
/workspace/section_a.pdf and /workspace/section_b.pdf with pdf-lib.

Every check targets a spot where a plausible-looking default fails: PDF page
dimensions are in points, so ISO A4 is ~595x842pt, not 210x297mm and not the
source pages' own 612x792pt US Letter size; the coordinate origin is the
bottom-left corner with y increasing upward, so "near the top" needs a large
y, and a naive top-left/screen-coordinate assumption places things near the
bottom instead; a title only renders bold with a genuine embedded bold font,
not a regular font reused with a style flag; the subtitle must sit below the
header band's own lower edge, not just below the title text; the header band
must run edge-to-edge (a naive inset "card" rectangle with side margins falls
short of the page's left/right edges and fails the width check); the PDF's
own Title metadata (set via pdf-lib's setTitle, distinct from the on-page
heading drawn with drawText) must match the visible title; and merging "only
the 1st, 3rd, and 5th pages" of section_b.pdf requires selecting those
specific page indices, not concatenating the whole document.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest
from pypdf import PdfReader
from PIL import Image

REPORT_PATH = "/workspace/report.pdf"
SEC_A_PATH = "/workspace/section_a.pdf"
SEC_B_PATH = "/workspace/section_b.pdf"

TITLE_TEXT = "Q1 Regional Summary"
SUBTITLE_TEXT = "Prepared for the Executive Committee"
HEADER_RGB = (0xD6, 0xE4, 0xF0)

A4_WIDTH = 595.28
A4_HEIGHT = 841.89


def _require_report():
    if not Path(REPORT_PATH).exists():
        pytest.fail(f"{REPORT_PATH} does not exist")
    return PdfReader(REPORT_PATH)


def _lines_by_row(page):
    """Reconstruct visual text lines on a page from (text, x, y, font) runs,
    clustering runs whose baseline y is within 2pt of each other."""
    runs = []

    def visitor(text, cm, tm, font_dict, font_size):
        if text.strip():
            base_font = font_dict.get("/BaseFont") if font_dict else None
            runs.append((tm[5], tm[4], text, base_font))

    page.extract_text(visitor_text=visitor)
    runs.sort(key=lambda r: (-r[0], r[1]))

    rows = []
    for y, x, text, font in runs:
        if rows and abs(rows[-1]["y"] - y) <= 2:
            rows[-1]["text"] += text
            rows[-1]["fonts"].add(font)
        else:
            rows.append({"y": y, "text": text, "fonts": {font}})
    return rows


def _find_header_band(tmp_path, tol=8):
    """Render the cover page and locate the header band by scanning for
    pixels matching HEADER_RGB, returning its vertical extent in PDF points
    (y-up) and how much of the page width it spans."""
    prefix = str(tmp_path / "cover")
    subprocess.run(
        ["pdftoppm", "-png", "-r", "150", "-f", "1", "-l", "1", REPORT_PATH, prefix],
        check=True, capture_output=True,
    )
    pngs = sorted(tmp_path.glob("cover*.png"))
    assert pngs, "pdftoppm did not produce a rendered cover page"

    img = Image.open(pngs[0]).convert("RGB")
    w, h = img.size
    px = img.load()

    row_matches = {}
    for y in range(h):
        cnt = 0
        for x in range(0, w, 3):
            p = px[x, y]
            if all(abs(p[i] - HEADER_RGB[i]) <= tol for i in range(3)):
                cnt += 1
        if cnt:
            row_matches[y] = cnt

    if not row_matches:
        return None

    top_px = min(row_matches)
    bottom_px = max(row_matches)
    width_frac = max(row_matches.values()) / (w / 3)

    reader = PdfReader(REPORT_PATH)
    page_height = float(reader.pages[0].mediabox.height)
    scale = page_height / h

    return {
        "top_y": page_height - top_px * scale,
        "bottom_y": page_height - bottom_px * scale,
        "width_frac": width_frac,
    }


def test_report_is_valid_pdf_with_8_pages():
    reader = _require_report()
    subprocess.run(["pdfinfo", REPORT_PATH], check=True, capture_output=True)
    assert len(reader.pages) == 8, f"expected 8 pages, got {len(reader.pages)}"


def test_cover_page_is_iso_a4():
    reader = _require_report()
    box = reader.pages[0].mediabox
    assert abs(float(box.width) - A4_WIDTH) < 2, f"cover width {box.width} is not ISO A4"
    assert abs(float(box.height) - A4_HEIGHT) < 2, f"cover height {box.height} is not ISO A4"


def test_header_band_color_position_and_width(tmp_path):
    band = _find_header_band(tmp_path)
    assert band, "no header band matching #D6E4F0 was found on the cover page"

    reader = _require_report()
    page_height = float(reader.pages[0].mediabox.height)
    center = (band["top_y"] + band["bottom_y"]) / 2
    assert center > page_height / 2, (
        f"header band center y={center:.1f} on a {page_height:.0f}pt page is not in "
        "the upper half (PDF y increases upward from the bottom-left origin)"
    )
    assert band["width_frac"] > 0.95, (
        f"header band spans only {band['width_frac']:.2f} of the page width; it must "
        "run edge-to-edge (touching both the left and right page edges), not sit "
        "inset with side margins"
    )


def test_document_title_metadata_matches_visible_title():
    reader = _require_report()
    assert reader.metadata is not None and reader.metadata.title == TITLE_TEXT, (
        f"PDF document Title metadata must be set to exactly {TITLE_TEXT!r} "
        "(e.g. via pdf-lib's PDFDocument.setTitle), not left unset -- this is "
        "separate from the on-page heading drawn with drawText"
    )


def test_title_is_bold_and_near_top():
    reader = _require_report()
    cover = reader.pages[0]
    height = float(cover.mediabox.height)
    rows = _lines_by_row(cover)

    title_rows = [r for r in rows if TITLE_TEXT in r["text"]]
    assert title_rows, f"expected a line containing {TITLE_TEXT!r} on the cover page"
    title_row = title_rows[0]

    assert title_row["y"] > 0.7 * height, (
        f"title baseline y={title_row['y']:.1f} on a {height:.0f}pt page must sit "
        "near the top"
    )
    assert any(f and "bold" in f.lower() for f in title_row["fonts"]), (
        "title must be rendered in an embedded bold font"
    )


def test_subtitle_is_regular_and_below_header_band(tmp_path):
    reader = _require_report()
    cover = reader.pages[0]
    rows = _lines_by_row(cover)

    subtitle_rows = [r for r in rows if SUBTITLE_TEXT in r["text"]]
    assert subtitle_rows, f"expected a line containing {SUBTITLE_TEXT!r} on the cover page"
    subtitle_row = subtitle_rows[0]

    assert not any(f and "bold" in f.lower() for f in subtitle_row["fonts"]), (
        "subtitle must be rendered in a regular (non-bold) font"
    )

    band = _find_header_band(tmp_path)
    assert band, "no header band matching #D6E4F0 was found on the cover page"
    assert subtitle_row["y"] < band["bottom_y"], (
        f"subtitle baseline y={subtitle_row['y']:.1f} must sit below the header "
        f"band's lower edge y={band['bottom_y']:.1f}, not overlapping it"
    )


def test_section_a_pages_appended_unchanged_and_in_order():
    reader = _require_report()
    sec_a = PdfReader(SEC_A_PATH)
    assert len(sec_a.pages) == 4

    for i in range(4):
        assert reader.pages[1 + i].extract_text() == sec_a.pages[i].extract_text(), (
            f"section_a.pdf page {i + 1} must be appended unchanged at report page {i + 2}"
        )


def test_only_1st_3rd_5th_pages_of_section_b_are_included():
    reader = _require_report()
    sec_b = PdfReader(SEC_B_PATH)
    assert len(sec_b.pages) == 6

    expected_indices = [0, 2, 4]  # 1st, 3rd, 5th pages (0-indexed)
    for offset, src_index in enumerate(expected_indices):
        report_page = reader.pages[5 + offset]
        assert report_page.extract_text() == sec_b.pages[src_index].extract_text(), (
            f"report page {6 + offset} must match section_b.pdf page {src_index + 1}"
        )

    skipped_indices = [1, 3, 5]  # 2nd, 4th, 6th pages must NOT appear
    report_tail_text = "\n".join(p.extract_text() for p in reader.pages[5:8])
    for src_index in skipped_indices:
        skipped_text = sec_b.pages[src_index].extract_text().strip()
        assert skipped_text not in report_tail_text, (
            f"section_b.pdf page {src_index + 1} must be skipped, but its text appears in report.pdf"
        )
