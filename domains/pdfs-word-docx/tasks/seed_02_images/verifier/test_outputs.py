"""Deterministic checks for /workspace/report.docx.

Checks that a chart image was embedded as a properly registered OOXML part
(media file + relationship + content type + correctly sized <wp:extent>), that
a captioned paragraph was added with schema-ordered <w:pPr> children, and that
a genuine Word comment was attached to the exact target phrase using the
comments part + relationship + content type, with the range markers as
siblings of <w:r> rather than nested inside it.
"""

import io
import zipfile
from pathlib import Path

import pytest
from lxml import etree
from PIL import Image

DOCX_PATH = Path("/workspace/report.docx")
SOURCE_IMAGE_PATH = Path("/workspace/figure.png")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
PKGREL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NS = {"w": W_NS, "wp": WP_NS, "a": A_NS, "r": R_NS, "ct": CT_NS, "pr": PKGREL_NS}

ORIGINAL_SENTENCE = (
    "The quarterly results were strong across all regions, "
    "with revenue up 12% year-over-year."
)
TARGET_PHRASE = "quarterly results"
CAPTION_TEXT = "Figure 1: Quarterly Revenue Chart"
COMMENT_AUTHOR = "Finance Review"
COMMENT_TEXT = "Please confirm these figures against the Q3 ledger before publishing."

EXPECTED_CX = 2743200  # 3 inches
EXPECTED_CY = 1828800  # 2 inches (900x600 source -> 3:2 aspect ratio)
EMU_TOL = 9144  # 0.01 inch


def qn(ns, tag):
    return f"{{{ns}}}{tag}"


def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn(W_NS, "t")))


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
def rels_root(parts):
    assert "word/_rels/document.xml.rels" in parts
    return etree.fromstring(parts["word/_rels/document.xml.rels"])


@pytest.fixture(scope="module")
def content_types_root(parts):
    assert "[Content_Types].xml" in parts
    return etree.fromstring(parts["[Content_Types].xml"])


@pytest.fixture(scope="module")
def rel_targets(rels_root):
    return {
        rel.get("Id"): (rel.get("Type"), rel.get("Target"))
        for rel in rels_root
    }


def test_docx_opens_and_original_paragraph_text_is_preserved(document_root):
    body = document_root.find(qn(W_NS, "body"))
    paragraph_texts = [text_of(p) for p in body.findall(qn(W_NS, "p"))]
    assert ORIGINAL_SENTENCE in paragraph_texts, (
        "the paragraph containing the target phrase must keep its original "
        "wording across all its runs"
    )


def test_image_relationship_and_content_type_registered(
    document_root, rel_targets, content_types_root, parts
):
    blips = document_root.findall(f".//{qn(A_NS, 'blip')}")
    assert len(blips) == 1, "expected exactly one embedded image"
    embed_id = blips[0].get(qn(R_NS, "embed"))
    assert embed_id in rel_targets, "blip r:embed does not match any relationship"

    rel_type, target = rel_targets[embed_id]
    assert rel_type == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

    media_path = "word/" + target.lstrip("/")
    assert media_path in parts, f"embedded media part {media_path} missing from package"

    ext = media_path.rsplit(".", 1)[-1]
    defaults = {
        d.get("Extension"): d.get("ContentType")
        for d in content_types_root.findall(qn(CT_NS, "Default"))
    }
    assert defaults.get(ext) == "image/png"

    embedded = Image.open(io.BytesIO(parts[media_path]))
    source = Image.open(SOURCE_IMAGE_PATH)
    assert embedded.size == source.size, "embedded image must be the full-resolution source figure"


def test_image_extent_matches_required_physical_size(document_root):
    extents = document_root.findall(f".//{qn(WP_NS, 'extent')}")
    assert len(extents) == 1
    cx = int(extents[0].get("cx"))
    cy = int(extents[0].get("cy"))
    assert abs(cx - EXPECTED_CX) <= EMU_TOL, f"width {cx} EMU != 3 inches"
    assert abs(cy - EXPECTED_CY) <= EMU_TOL, f"height {cy} EMU != aspect-ratio-preserved 2 inches"


def test_caption_paragraph_alignment_spacing_and_pPr_order(document_root):
    body = document_root.find(qn(W_NS, "body"))
    caption_p = None
    for p in body.findall(qn(W_NS, "p")):
        if text_of(p) == CAPTION_TEXT:
            caption_p = p
            break
    assert caption_p is not None, f"no paragraph with caption text {CAPTION_TEXT!r}"

    pPr = caption_p.find(qn(W_NS, "pPr"))
    assert pPr is not None, "caption paragraph must carry paragraph formatting"

    jc = pPr.find(qn(W_NS, "jc"))
    assert jc is not None and jc.get(qn(W_NS, "val")) == "center"

    spacing = pPr.find(qn(W_NS, "spacing"))
    assert spacing is not None and spacing.get(qn(W_NS, "before")) == "240"

    # Schema-mandated child order inside <w:pPr>: spacing precedes jc.
    children = list(pPr)
    assert children.index(spacing) < children.index(jc), (
        "<w:pPr> children must follow schema order (spacing before jc); "
        "Word will flag/repair the document otherwise"
    )


def test_comment_part_and_relationship_registered(rel_targets, content_types_root, parts):
    assert "word/comments.xml" in parts

    comment_rel_types = [t for (t, _target) in rel_targets.values()]
    assert (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
        in comment_rel_types
    )

    overrides = {
        o.get("PartName"): o.get("ContentType")
        for o in content_types_root.findall(qn(CT_NS, "Override"))
    }
    assert (
        overrides.get("/word/comments.xml")
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
    )


def test_comment_metadata_matches(parts):
    comments_root = etree.fromstring(parts["word/comments.xml"])
    comments = comments_root.findall(qn(W_NS, "comment"))
    assert len(comments) == 1
    comment = comments[0]
    assert comment.get(qn(W_NS, "author")) == COMMENT_AUTHOR
    assert text_of(comment) == COMMENT_TEXT


def test_comment_range_markers_are_siblings_of_paragraph_not_nested_in_run(document_root):
    starts = document_root.findall(f".//{qn(W_NS, 'commentRangeStart')}")
    ends = document_root.findall(f".//{qn(W_NS, 'commentRangeEnd')}")
    refs = document_root.findall(f".//{qn(W_NS, 'commentReference')}")
    assert len(starts) == 1 and len(ends) == 1 and len(refs) == 1

    start, end, ref = starts[0], ends[0], refs[0]
    comment_id = start.get(qn(W_NS, "id"))
    assert comment_id == end.get(qn(W_NS, "id")) == ref.get(qn(W_NS, "id"))

    # CRITICAL rule: commentRangeStart/End must be direct children of w:p,
    # siblings of w:r -- never nested inside a w:r.
    assert start.getparent().tag == qn(W_NS, "p"), "commentRangeStart must be a sibling of w:r, not nested inside one"
    assert end.getparent().tag == qn(W_NS, "p"), "commentRangeEnd must be a sibling of w:r, not nested inside one"
    assert start.getparent() is end.getparent(), "range start/end must anchor the same paragraph"

    parent = start.getparent()
    siblings = list(parent)
    start_idx = siblings.index(start)
    end_idx = siblings.index(end)
    assert start_idx < end_idx

    between = siblings[start_idx + 1 : end_idx]
    wrapped_text = "".join(text_of(el) for el in between)
    assert wrapped_text == TARGET_PHRASE, (
        f"comment must be anchored to exactly {TARGET_PHRASE!r}, got {wrapped_text!r}"
    )

    ref_run = ref.getparent()
    assert ref_run.tag == qn(W_NS, "r")
    assert siblings.index(ref_run) > end_idx, "commentReference run must come after commentRangeEnd"
