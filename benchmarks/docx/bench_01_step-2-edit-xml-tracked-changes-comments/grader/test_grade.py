from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
W = f"{{{W_NS}}}"
PR = f"{{{PR_NS}}}"
CT = f"{{{CT_NS}}}"
DATE = "2025-01-01T00:00:00Z"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def parse_xml(path: Path) -> ET.Element:
    try:
        return ET.fromstring(path.read_bytes())
    except Exception as exc:  # pragma: no cover
        fail(f"Failed to parse {path}: {exc}")


def canonical_xml_bytes(path: Path) -> bytes:
    return ET.tostring(parse_xml(path), encoding="utf-8")


def child_texts(elem: ET.Element, tag: str) -> list[str]:
    return [node.text or "" for node in elem.iter(tag)]


def check_required_files(workspace: Path) -> None:
    required = [
        workspace / "unpacked/word/document.xml",
        workspace / "unpacked/word/comments.xml",
        workspace / "unpacked/word/_rels/document.xml.rels",
        workspace / "unpacked/[Content_Types].xml",
        workspace / "final.docx",
    ]
    missing = [str(p.relative_to(workspace)) for p in required if not p.exists()]
    if missing:
        fail(f"Missing required output files: {', '.join(missing)}")


def get_paragraphs(doc_root: ET.Element) -> list[ET.Element]:
    body = doc_root.find(f"{W}body")
    if body is None:
        fail("document.xml is missing w:body")
    return [child for child in body if child.tag == f"{W}p"]


def check_first_paragraph(doc_root: ET.Element, raw_document: str) -> None:
    paragraphs = get_paragraphs(doc_root)
    if len(paragraphs) < 1:
        fail("document.xml does not contain the expected first paragraph")
    first_p = paragraphs[0]

    if "30 days&#x2019; written notice" not in raw_document:
        fail("Inserted wording must use the XML entity &#x2019; in document.xml")
    if "<w:delText>15 days notice</w:delText>" not in raw_document:
        fail("Expected tracked deletion of '15 days notice'")

    del_nodes = [child for child in first_p if child.tag == f"{W}del"]
    ins_nodes = [child for child in first_p if child.tag == f"{W}ins"]
    if len(del_nodes) != 1 or len(ins_nodes) != 1:
        fail("First paragraph must contain exactly one top-level <w:del> and one top-level <w:ins>")

    deletion = del_nodes[0]
    insertion = ins_nodes[0]
    for node in (deletion, insertion):
        if node.attrib.get(f"{W}author") != "Claude":
            fail("Tracked changes must use author Claude")
        if node.attrib.get(f"{W}date") != DATE:
            fail("Tracked changes must use the required timestamp")

    if list(deletion.iter(f"{W}t")):
        fail("Tracked deletions must use <w:delText>, not <w:t>")

    del_rpr = deletion.find(f"./{W}r/{W}rPr")
    ins_rpr = insertion.find(f"./{W}r/{W}rPr")
    if del_rpr is None or ins_rpr is None:
        fail("Both tracked-change runs must preserve the original run properties")
    for rpr in (del_rpr, ins_rpr):
        has_bold = rpr.find(f"{W}b") is not None
        color = rpr.find(f"{W}color")
        if not has_bold or color is None or color.attrib.get(f"{W}val") != "AA0000":
            fail("Tracked-change run properties must preserve bold red formatting")

    visible_text = "".join(child_texts(first_p, f"{W}t"))
    if visible_text != "Termination clause: 30 days’ written notice.":
        fail("First paragraph does not contain the required accepted text")


def check_comment_anchors(doc_root: ET.Element) -> None:
    first_p = get_paragraphs(doc_root)[0]
    tags = [child.tag for child in list(first_p)]
    expected_sequence = [
        f"{W}r",
        f"{W}del",
        f"{W}commentRangeStart",
        f"{W}commentRangeStart",
        f"{W}ins",
        f"{W}commentRangeEnd",
        f"{W}commentRangeEnd",
        f"{W}r",
        f"{W}r",
        f"{W}r",
    ]
    if tags != expected_sequence:
        fail("First paragraph must use nested comment ranges as siblings around the inserted phrase")

    children = list(first_p)
    ids = [
        children[2].attrib.get(f"{W}id"),
        children[3].attrib.get(f"{W}id"),
        children[5].attrib.get(f"{W}id"),
        children[6].attrib.get(f"{W}id"),
    ]
    if ids != ["0", "1", "1", "0"]:
        fail("Comment range ids must be nested as 0 -> 1 -> 1 -> 0")

    for run in first_p.iter(f"{W}r"):
        if run.find(f"{W}commentRangeStart") is not None or run.find(f"{W}commentRangeEnd") is not None:
            fail("commentRangeStart/commentRangeEnd must not appear inside a run")

    refs = []
    for run in [child for child in first_p if child.tag == f"{W}r"]:
        ref = run.find(f"{W}commentReference")
        if ref is not None:
            refs.append(ref.attrib.get(f"{W}id"))
    if refs != ["0", "1"]:
        fail("First paragraph must end with comment references for ids 0 and 1")


def check_deleted_paragraph(doc_root: ET.Element) -> None:
    paragraphs = get_paragraphs(doc_root)
    if len(paragraphs) < 2:
        fail("document.xml does not contain the expected second paragraph")
    second_p = paragraphs[1]

    ppr = second_p.find(f"{W}pPr")
    if ppr is None:
        fail("Whole-paragraph deletion must add w:pPr")
    rpr = ppr.find(f"{W}rPr")
    if rpr is None:
        fail("Whole-paragraph deletion must add w:pPr/w:rPr")
    ppr_del = rpr.find(f"{W}del")
    if ppr_del is None:
        fail("Whole-paragraph deletion must mark the paragraph mark inside w:pPr/w:rPr/w:del")
    if ppr_del.attrib.get(f"{W}author") != "Claude" or ppr_del.attrib.get(f"{W}date") != DATE:
        fail("Paragraph-mark deletion must use the required author/date")

    del_nodes = [child for child in second_p if child.tag == f"{W}del"]
    if len(del_nodes) != 1:
        fail("Second paragraph must contain a single tracked deletion wrapper")
    deleted = del_nodes[0]
    if deleted.attrib.get(f"{W}author") != "Claude" or deleted.attrib.get(f"{W}date") != DATE:
        fail("Deleted paragraph text must use the required author/date")
    if list(deleted.iter(f"{W}t")):
        fail("Deleted paragraph text must use w:delText, not w:t")
    deleted_text = "".join(child_texts(deleted, f"{W}delText"))
    if deleted_text != "Submit weekly status reports.":
        fail("Deleted paragraph text is incorrect")

    if [child for child in second_p if child.tag == f"{W}r"]:
        fail("The deleted paragraph should not leave behind normal runs")


def check_unchanged_third_paragraph(doc_root: ET.Element) -> None:
    paragraphs = get_paragraphs(doc_root)
    if len(paragraphs) < 3:
        fail("document.xml does not contain the expected third paragraph")
    third_text = "".join(child_texts(paragraphs[2], f"{W}t"))
    if third_text != "Payment is due within ten days of invoice receipt.":
        fail("The third paragraph text must remain unchanged")


def check_comments_xml(comments_root: ET.Element, comments_path: Path) -> None:
    comments = [child for child in comments_root if child.tag == f"{W}comment"]
    if [c.attrib.get(f"{W}id") for c in comments] != ["0", "1"]:
        fail("comments.xml must contain exactly comments 0 and 1")
    expected_texts = {
        "0": 'Confirm that “30 days’ written notice” matches the negotiated draft.',
        "1": "Confirmed. Counsel’s June 12 redline uses the same wording.",
    }
    for comment in comments:
        cid = comment.attrib.get(f"{W}id")
        if comment.attrib.get(f"{W}author") != "Claude":
            fail("All comments must use author Claude")
        if comment.attrib.get(f"{W}date") != DATE:
            fail("All comments must use the required timestamp")
        if "".join(child_texts(comment, f"{W}t")) != expected_texts[cid]:
            fail(f"Unexpected text for comment {cid}")

    raw = comments_path.read_text(encoding="utf-8")
    for entity in ("&#x201C;", "&#x201D;", "&#x2019;"):
        if entity not in raw:
            fail("comments.xml must encode smart punctuation with XML entities")


def check_comments_rel_and_content_types(workspace: Path) -> None:
    rels_root = parse_xml(workspace / "unpacked/word/_rels/document.xml.rels")
    rel_targets = [
        rel.attrib.get("Target")
        for rel in rels_root
        if rel.tag == f"{PR}Relationship"
        and rel.attrib.get("Type") == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
    ]
    if rel_targets != ["comments.xml"]:
        fail("document.xml.rels must contain the comments relationship")

    types_root = parse_xml(workspace / "unpacked/[Content_Types].xml")
    comment_override = [
        override.attrib.get("ContentType")
        for override in types_root
        if override.tag == f"{CT}Override" and override.attrib.get("PartName") == "/word/comments.xml"
    ]
    if comment_override != ["application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"]:
        fail("unpacked/[Content_Types].xml must keep the comments override")


def check_packed_docx(workspace: Path) -> None:
    final_docx = workspace / "final.docx"
    try:
        with zipfile.ZipFile(final_docx) as zf:
            names = set(zf.namelist())
            required = {
                "[Content_Types].xml",
                "_rels/.rels",
                "word/document.xml",
                "word/comments.xml",
                "word/_rels/document.xml.rels",
            }
            if not required.issubset(names):
                fail("final.docx is missing required package members")
            for rel_path in ("word/document.xml", "word/comments.xml", "word/_rels/document.xml.rels", "[Content_Types].xml"):
                packed = ET.tostring(ET.fromstring(zf.read(rel_path)), encoding="utf-8")
                unpacked_path = workspace / "unpacked" / rel_path
                unpacked = canonical_xml_bytes(unpacked_path)
                if packed != unpacked:
                    fail(f"Packed file {rel_path} does not match the edited workspace copy")
    except zipfile.BadZipFile:
        fail("final.docx is not a valid zip archive")


def main() -> None:
    workspace = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
    check_required_files(workspace)
    document_path = workspace / "unpacked/word/document.xml"
    doc_root = parse_xml(document_path)
    raw_document = document_path.read_text(encoding="utf-8")
    comments_path = workspace / "unpacked/word/comments.xml"
    comments_root = parse_xml(comments_path)

    check_first_paragraph(doc_root, raw_document)
    check_comment_anchors(doc_root)
    check_deleted_paragraph(doc_root)
    check_unchanged_third_paragraph(doc_root)
    check_comments_xml(comments_root, comments_path)
    check_comments_rel_and_content_types(workspace)
    check_packed_docx(workspace)


if __name__ == "__main__":
    main()
