"""Deterministic checks for /workspace/output.docx, a quarterly report the
agent must generate from /workspace/data.json and /workspace/logo.png using
the docx (docx-js) Node library.

Every check targets a spot where the library's own defaults silently produce
a document that looks plausible but is wrong: A4 instead of US Letter page
size, a table whose column grid falls back to a meaningless placeholder width
unless the table (not just its cells) is also given explicit widths, header
shading that renders as solid black unless the "clear" pattern is used, a
"bulleted list" that is really just plain paragraphs typed with a literal
bullet character, and an embedded image saved with no recognized file
extension unless its type is declared.
"""

import json
import zipfile
from pathlib import Path

import pytest
from lxml import etree

DOCX_PATH = Path("/workspace/output.docx")
DATA_PATH = Path("/workspace/data.json")
LOGO_PATH = Path("/workspace/logo.png")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

EXPECTED_PAGE_WIDTH_DXA = 12240  # US Letter, 8.5in
EXPECTED_PAGE_HEIGHT_DXA = 15840  # US Letter, 11in

EXPECTED_COL_WIDTHS_DXA = [2880, 2160, 4320]  # 2in, 1.5in, 3in
HEADER_FILL = "D9D9D9"

EXPECTED_IMAGE_WIDTH_EMU = 1371600  # 1.5in
EMU_TOL = 18288  # 0.02 inch
ALT_TITLE = "Acme Corp Logo"
ALT_DESC = "Acme Corp company logo"
ALT_NAME = "AcmeLogo"


def qn(ns, tag):
    return f"{{{ns}}}{tag}"


def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn(W_NS, "t")))


@pytest.fixture(scope="module")
def report_data():
    return json.loads(DATA_PATH.read_text())


@pytest.fixture(scope="module")
def parts():
    assert DOCX_PATH.exists(), f"{DOCX_PATH} was not created"
    with zipfile.ZipFile(DOCX_PATH) as z:
        return {n: z.read(n) for n in z.namelist()}


@pytest.fixture(scope="module")
def document_root(parts):
    assert "word/document.xml" in parts
    return etree.fromstring(parts["word/document.xml"])


@pytest.fixture(scope="module")
def styles_root(parts):
    assert "word/styles.xml" in parts
    return etree.fromstring(parts["word/styles.xml"])


@pytest.fixture(scope="module")
def numbering_root(parts):
    assert "word/numbering.xml" in parts, "no numbering part -- list is not real Word numbering"
    return etree.fromstring(parts["word/numbering.xml"])


@pytest.fixture(scope="module")
def content_types_root(parts):
    return etree.fromstring(parts["[Content_Types].xml"])


@pytest.fixture(scope="module")
def rels_root(parts):
    assert "word/_rels/document.xml.rels" in parts
    return etree.fromstring(parts["word/_rels/document.xml.rels"])


def test_page_size_is_us_letter_not_default_a4(document_root):
    pgSz = document_root.find(f".//{qn(W_NS, 'pgSz')}")
    assert pgSz is not None, "no page size found"
    width = int(pgSz.get(qn(W_NS, "w")))
    height = int(pgSz.get(qn(W_NS, "h")))
    assert width == EXPECTED_PAGE_WIDTH_DXA and height == EXPECTED_PAGE_HEIGHT_DXA, (
        f"page size is {width}x{height} DXA, expected US Letter "
        f"{EXPECTED_PAGE_WIDTH_DXA}x{EXPECTED_PAGE_HEIGHT_DXA} DXA "
        "(the library's default page size is A4, not US Letter)"
    )


def test_document_default_font_is_arial(styles_root):
    doc_defaults = styles_root.find(qn(W_NS, "docDefaults"))
    ascii_fonts = set()
    if doc_defaults is not None:
        rfonts = doc_defaults.find(f".//{qn(W_NS, 'rFonts')}")
        if rfonts is not None and rfonts.get(qn(W_NS, "ascii")):
            ascii_fonts.add(rfonts.get(qn(W_NS, "ascii")))
    normal_style = None
    for style in styles_root.findall(qn(W_NS, "style")):
        if style.get(qn(W_NS, "styleId")) == "Normal":
            normal_style = style
            break
    if normal_style is not None:
        rfonts = normal_style.find(f".//{qn(W_NS, 'rFonts')}")
        if rfonts is not None and rfonts.get(qn(W_NS, "ascii")):
            ascii_fonts.add(rfonts.get(qn(W_NS, "ascii")))
    assert "Arial" in ascii_fonts, (
        "document-wide default font is not Arial "
        f"(found defaults: {ascii_fonts or 'none'}); a font that isn't set as "
        "the actual default won't apply to body text that doesn't explicitly "
        "request it"
    )


def _title_paragraph(document_root):
    body = document_root.find(qn(W_NS, "body"))
    for p in body.findall(qn(W_NS, "p")):
        pPr = p.find(qn(W_NS, "pPr"))
        if pPr is None:
            continue
        pStyle = pPr.find(qn(W_NS, "pStyle"))
        if pStyle is not None and pStyle.get(qn(W_NS, "val")) == "Heading1":
            return p, pPr
    return None, None


def _last_heading1_style(styles_root):
    matches = [
        s for s in styles_root.findall(qn(W_NS, "style"))
        if s.get(qn(W_NS, "styleId")) == "Heading1"
    ]
    return matches[-1] if matches else None


def test_title_uses_heading1_with_outline_level_zero(document_root, styles_root):
    title_p, title_pPr = _title_paragraph(document_root)
    assert title_p is not None, "no paragraph uses the built-in Heading 1 style"

    outline = title_pPr.find(qn(W_NS, "outlineLvl"))
    if outline is None:
        style = _last_heading1_style(styles_root)
        outline = style.find(f".//{qn(W_NS, 'outlineLvl')}") if style is not None else None
    assert outline is not None and outline.get(qn(W_NS, "val")) == "0", (
        "the Heading 1 title has no outline level 0 set (neither directly on "
        "the paragraph nor via a Heading1 style override) -- a TOC tool would "
        "not recognize it as a top-level heading"
    )


def test_title_renders_black_not_default_theme_color(document_root, styles_root):
    title_p, _ = _title_paragraph(document_root)
    assert title_p is not None

    run_colors = [
        c.get(qn(W_NS, "val"))
        for c in title_p.findall(f".//{qn(W_NS, 'rPr')}/{qn(W_NS, 'color')}")
    ]
    if run_colors:
        effective_color = run_colors[0]
    else:
        style = _last_heading1_style(styles_root)
        color_el = style.find(f".//{qn(W_NS, 'color')}") if style is not None else None
        effective_color = color_el.get(qn(W_NS, "val")) if color_el is not None else None

    assert effective_color is not None and effective_color.lower() == "000000", (
        f"title's effective text color is {effective_color!r}, expected black "
        "(000000) -- the library's built-in Heading 1 style defaults to a "
        "colored theme accent, not black"
    )


def _find_table(document_root):
    tables = document_root.findall(f".//{qn(W_NS, 'tbl')}")
    assert len(tables) == 1, f"expected exactly one table, found {len(tables)}"
    return tables[0]


def test_table_grid_and_cell_widths_are_absolute_dxa(document_root):
    table = _find_table(document_root)
    grid = table.find(qn(W_NS, "tblGrid"))
    assert grid is not None
    grid_widths = [int(g.get(qn(W_NS, "w"))) for g in grid.findall(qn(W_NS, "gridCol"))]
    assert grid_widths == EXPECTED_COL_WIDTHS_DXA, (
        f"table column grid is {grid_widths}, expected {EXPECTED_COL_WIDTHS_DXA} "
        "-- setting width only on each cell without also setting the table's "
        "own column widths leaves the grid at a meaningless placeholder"
    )

    rows = table.findall(qn(W_NS, "tr"))
    assert len(rows) >= 2
    for row in rows:
        cells = row.findall(qn(W_NS, "tc"))
        assert len(cells) == 3
        cell_widths = []
        for cell in cells:
            tcW = cell.find(f".//{qn(W_NS, 'tcW')}")
            assert tcW is not None
            assert tcW.get(qn(W_NS, "type")) == "dxa", (
                "cell width type must be dxa (absolute), not pct -- "
                "percentage widths break in Google Docs"
            )
            cell_widths.append(int(tcW.get(qn(W_NS, "w"))))
        assert cell_widths == EXPECTED_COL_WIDTHS_DXA


def test_table_header_row_shading_is_clear_not_solid(document_root):
    table = _find_table(document_root)
    header_row = table.findall(qn(W_NS, "tr"))[0]
    header_cells = header_row.findall(qn(W_NS, "tc"))
    assert len(header_cells) == 3
    for cell in header_cells:
        shd = cell.find(f".//{qn(W_NS, 'shd')}")
        assert shd is not None, "header cell has no shading at all"
        assert shd.get(qn(W_NS, "val")) == "clear", (
            f"header cell shading val is {shd.get(qn(W_NS, 'val'))!r}, expected "
            "'clear' -- 'solid' shading renders as a black fill regardless of "
            "the fill color"
        )
        assert (shd.get(qn(W_NS, "fill")) or "").upper() == HEADER_FILL


def test_table_content_matches_report_data(document_root, report_data):
    table = _find_table(document_root)
    rows = table.findall(qn(W_NS, "tr"))
    row_texts = [
        [text_of(cell) for cell in row.findall(qn(W_NS, "tc"))]
        for row in rows
    ]
    assert row_texts[0] == ["Metric", "Value", "Notes"]
    expected_body = [
        [m["metric"], m["value"], m["notes"]] for m in report_data["metrics"]
    ]
    assert row_texts[1:] == expected_body


def test_takeaways_use_real_bullet_numbering_not_literal_characters(
    document_root, numbering_root, report_data, content_types_root, rels_root
):
    body = document_root.find(qn(W_NS, "body"))
    list_paragraphs = []
    for p in body.findall(qn(W_NS, "p")):
        numPr = p.find(f"{qn(W_NS, 'pPr')}/{qn(W_NS, 'numPr')}")
        if numPr is not None:
            list_paragraphs.append((p, numPr))

    assert len(list_paragraphs) == len(report_data["takeaways"]), (
        f"expected {len(report_data['takeaways'])} real list paragraphs, "
        f"found {len(list_paragraphs)}"
    )

    texts = [text_of(p) for p, _ in list_paragraphs]
    assert texts == report_data["takeaways"], (
        "list item text must be exactly the takeaway text, with no literal "
        f"bullet/dash prefix typed into it; got {texts!r}"
    )
    for t in texts:
        assert not t.lstrip()[:1] in {"•", "-", "*", "●", "○"}

    num_ids = {numPr.find(qn(W_NS, "numId")).get(qn(W_NS, "val")) for _, numPr in list_paragraphs}
    assert len(num_ids) == 1, "all takeaway items should share one list definition"
    num_id = next(iter(num_ids))

    num_el = None
    for n in numbering_root.findall(qn(W_NS, "num")):
        if n.get(qn(W_NS, "numId")) == num_id:
            num_el = n
            break
    assert num_el is not None, f"numId {num_id} has no <w:num> definition in numbering.xml"
    abstract_ref = num_el.find(qn(W_NS, "abstractNumId"))
    assert abstract_ref is not None
    abstract_id = abstract_ref.get(qn(W_NS, "val"))

    abstract_el = None
    for an in numbering_root.findall(qn(W_NS, "abstractNum")):
        if an.get(qn(W_NS, "abstractNumId")) == abstract_id:
            abstract_el = an
            break
    assert abstract_el is not None

    lvl0 = None
    for lvl in abstract_el.findall(qn(W_NS, "lvl")):
        if lvl.get(qn(W_NS, "ilvl")) == "0":
            lvl0 = lvl
            break
    assert lvl0 is not None
    num_fmt = lvl0.find(qn(W_NS, "numFmt"))
    assert num_fmt is not None and num_fmt.get(qn(W_NS, "val")) == "bullet", (
        f"level-0 numbering format is {num_fmt.get(qn(W_NS, 'val')) if num_fmt is not None else None!r}, "
        "expected 'bullet'"
    )

    overrides = {
        o.get("PartName"): o.get("ContentType")
        for o in content_types_root.findall(qn(CT_NS, "Override"))
    }
    assert overrides.get("/word/numbering.xml") == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"
    )
    rel_targets = {rel.get("Target") for rel in rels_root}
    assert "numbering.xml" in rel_targets


def test_image_embedded_with_registered_type_and_full_alt_text(
    document_root, parts, content_types_root, rels_root
):
    blips = document_root.findall(f".//{qn(A_NS, 'blip')}")
    assert len(blips) == 1, "expected exactly one embedded image"
    embed_id = blips[0].get(qn(R_NS, "embed"))

    rel_targets = {rel.get("Id"): rel.get("Target") for rel in rels_root}
    assert embed_id in rel_targets
    media_path = "word/" + rel_targets[embed_id].lstrip("/")
    assert media_path in parts, f"embedded media part {media_path} missing"

    ext = media_path.rsplit(".", 1)[-1]
    assert ext != "undefined" and ext == "png", (
        f"embedded image was saved with extension {ext!r} -- omitting the "
        "image type produces a media file with no real extension"
    )

    defaults = {
        d.get("Extension"): d.get("ContentType")
        for d in content_types_root.findall(qn(CT_NS, "Default"))
    }
    assert defaults.get(ext) == "image/png", (
        f"no registered content type for extension {ext!r} -- the image "
        "part is not a valid, openable OOXML package member"
    )
    assert parts[media_path] == LOGO_PATH.read_bytes(), (
        "embedded media bytes do not match the source logo.png"
    )

    docPr = document_root.find(f".//{qn(WP_NS, 'docPr')}")
    assert docPr is not None
    assert docPr.get("title") == ALT_TITLE
    assert docPr.get("descr") == ALT_DESC
    assert docPr.get("name") == ALT_NAME

    extent = document_root.find(f".//{qn(WP_NS, 'extent')}")
    assert extent is not None
    cx = int(extent.get("cx"))
    assert abs(cx - EXPECTED_IMAGE_WIDTH_EMU) <= EMU_TOL, (
        f"image width is {cx} EMU, expected ~{EXPECTED_IMAGE_WIDTH_EMU} EMU (1.5in)"
    )
