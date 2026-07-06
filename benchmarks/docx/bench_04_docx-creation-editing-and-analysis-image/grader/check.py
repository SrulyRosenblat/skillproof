#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


WORKSPACE = Path("/workspace")
SOURCE_DOCX = WORKSPACE / "source/onepager.docx"
SOURCE_IMAGE = WORKSPACE / "source/campus-photo.png"
OUTPUT_DOCX = WORKSPACE / "output/onepager_with_photo.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {
    "w": W_NS,
    "r": R_NS,
    "wp": WP_NS,
    "a": A_NS,
    "ct": CT_NS,
    "pr": PR_NS,
}

ALLOWED_CHANGED = {
    "[Content_Types].xml",
    "word/document.xml",
    "word/_rels/document.xml.rels",
}
ALLOWED_NEW = {"word/media/campus-photo.png"}
EXPECTED_TEXTS = [
    "Community Garden Open House",
    "Join neighbors for an afternoon of tours, planting demos, and family activities at the Riverside lots.",
    "Saturday, September 14, 2026 | 1:00 PM to 4:00 PM",
    "",
    "Volunteers will provide seed packets, composting tips, and sign-ups for fall cleanup crews.",
    "Questions: gardens@example.org",
]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def read_zip(path: Path) -> dict[str, bytes]:
    if not path.exists():
        fail(f"Missing required file: {path}")
    with ZipFile(path) as zf:
        return {
            name: zf.read(name)
            for name in zf.namelist()
            if not name.endswith("/")
        }


def paragraph_texts(document_xml: bytes) -> list[str]:
    root = ET.fromstring(document_xml)
    texts: list[str] = []
    for para in root.findall(".//w:body/w:p", NS):
        text = "".join(node.text or "" for node in para.findall(".//w:t", NS))
        texts.append(text)
    return texts


def main() -> None:
    source_entries = read_zip(SOURCE_DOCX)
    output_entries = read_zip(OUTPUT_DOCX)

    extra_entries = set(output_entries) - set(source_entries)
    if extra_entries != ALLOWED_NEW:
        fail(f"Unexpected new ZIP members: {sorted(extra_entries)}")

    missing_entries = set(source_entries) - set(output_entries)
    if missing_entries:
        fail(f"Output DOCX is missing original ZIP members: {sorted(missing_entries)}")

    for name, source_bytes in source_entries.items():
        if name in ALLOWED_CHANGED:
            continue
        if output_entries[name] != source_bytes:
            fail(f"Original ZIP member changed unexpectedly: {name}")

    embedded_image = output_entries.get("word/media/campus-photo.png")
    if embedded_image is None:
        fail("Embedded image word/media/campus-photo.png is missing")
    if embedded_image != SOURCE_IMAGE.read_bytes():
        fail("Embedded image bytes do not match source/campus-photo.png")

    output_texts = paragraph_texts(output_entries["word/document.xml"])
    if output_texts != EXPECTED_TEXTS:
        fail(f"Document text/paragraph order is wrong: {output_texts}")
    if "[[PHOTO_SLOT]]" in "".join(output_texts):
        fail("Placeholder text [[PHOTO_SLOT]] is still present")

    document_root = ET.fromstring(output_entries["word/document.xml"])
    body_paragraphs = document_root.findall(".//w:body/w:p", NS)
    if len(body_paragraphs) != len(EXPECTED_TEXTS):
        fail(f"Expected {len(EXPECTED_TEXTS)} body paragraphs, found {len(body_paragraphs)}")

    image_para = body_paragraphs[3]
    jc = image_para.find("w:pPr/w:jc", NS)
    if jc is None or jc.attrib.get(f"{{{W_NS}}}val") != "center":
        fail("Image paragraph is not centered with <w:jc w:val=\"center\">")

    drawings = image_para.findall(".//w:drawing", NS)
    if len(drawings) != 1:
        fail(f"Expected exactly one drawing in the image paragraph, found {len(drawings)}")

    extent = image_para.find(".//wp:inline/wp:extent", NS)
    if extent is None or extent.attrib != {"cx": "2194560", "cy": "1463040"}:
        fail("Image size is not exactly 2.4in x 1.6in (2194560 x 1463040 EMUs)")

    blip = image_para.find(".//a:blip", NS)
    if blip is None:
        fail("Drawing does not contain an a:blip image reference")
    embed_id = blip.attrib.get(f"{{{R_NS}}}embed")
    if not embed_id:
        fail("Drawing does not use an embedded relationship")

    rels_root = ET.fromstring(output_entries["word/_rels/document.xml.rels"])
    relationships = rels_root.findall("pr:Relationship", NS)
    matching = [
        rel
        for rel in relationships
        if rel.attrib.get("Id") == embed_id
    ]
    if len(matching) != 1:
        fail(f"Image relationship {embed_id} is missing from word/_rels/document.xml.rels")
    rel = matching[0]
    if rel.attrib.get("Type") != "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image":
        fail("Embedded relationship is not typed as an image relationship")
    if rel.attrib.get("Target") != "media/campus-photo.png":
        fail("Image relationship does not target media/campus-photo.png")

    content_types_root = ET.fromstring(output_entries["[Content_Types].xml"])
    png_defaults = [
        node
        for node in content_types_root.findall("ct:Default", NS)
        if node.attrib.get("Extension") == "png"
    ]
    if len(png_defaults) != 1:
        fail("Expected exactly one PNG content type declaration in [Content_Types].xml")
    if png_defaults[0].attrib.get("ContentType") != "image/png":
        fail("PNG content type declaration is not image/png")

    print("PASS")


if __name__ == "__main__":
    main()
