#!/bin/bash
# Computes the updated /workspace/report.docx from the task inputs:
# embeds figure.png sized to an exact physical width with aspect-ratio-preserved
# height, adds a centered caption paragraph, and adds a genuine Word comment
# anchored to the "quarterly results" phrase (comments.xml part + relationship +
# content type + range markers that are siblings of w:r, not nested inside it).
set -euo pipefail

python3 - <<'PY'
import zipfile
import shutil
from lxml import etree
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

DOCX_PATH = "/workspace/report.docx"
IMAGE_PATH = "/workspace/figure.png"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
PKGREL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def qn(ns, tag):
    return f"{{{ns}}}{tag}"


# --- Step 1: use python-docx for the parts it handles correctly on its own:
# the image relationship/content-type/EMU extent, and the centered, spaced
# caption paragraph (python-docx emits schema-ordered <w:pPr> children). ---
doc = Document(DOCX_PATH)
doc.add_picture(IMAGE_PATH, width=Inches(3))
caption = doc.add_paragraph("Figure 1: Quarterly Revenue Chart")
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_before = Pt(12)
doc.save(DOCX_PATH)

# --- Step 2: python-docx has no comment support at all, so the comment part,
# its relationship, its content type, and the in-body range markers are all
# added by hand. ---
TARGET_PHRASE = "quarterly results"
COMMENT_ID = "0"
AUTHOR = "Finance Review"
COMMENT_TEXT = "Please confirm these figures against the Q3 ledger before publishing."

with zipfile.ZipFile(DOCX_PATH, "r") as zin:
    names = zin.namelist()
    parts = {n: zin.read(n) for n in names}

doc_root = etree.fromstring(parts["word/document.xml"])
body = doc_root.find(qn(W_NS, "body"))

target_p, target_r, t_el = None, None, None
for p in body.findall(qn(W_NS, "p")):
    for r in p.findall(qn(W_NS, "r")):
        t = r.find(qn(W_NS, "t"))
        if t is not None and t.text and TARGET_PHRASE in t.text:
            target_p, target_r, t_el = p, r, t
            break
    if target_p is not None:
        break

assert target_p is not None, f"could not find phrase {TARGET_PHRASE!r}"

full_text = t_el.text
idx = full_text.index(TARGET_PHRASE)
before_text = full_text[:idx]
phrase_text = full_text[idx : idx + len(TARGET_PHRASE)]
after_text = full_text[idx + len(TARGET_PHRASE) :]

rpr_source = target_r.find(qn(W_NS, "rPr"))


def make_run(text):
    r = etree.Element(qn(W_NS, "r"))
    if rpr_source is not None:
        r.append(etree.fromstring(etree.tostring(rpr_source)))
    t = etree.SubElement(r, qn(W_NS, "t"))
    t.text = text
    if text != text.strip():
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r


new_nodes = []
if before_text:
    new_nodes.append(make_run(before_text))

range_start = etree.Element(qn(W_NS, "commentRangeStart"))
range_start.set(qn(W_NS, "id"), COMMENT_ID)
new_nodes.append(range_start)

new_nodes.append(make_run(phrase_text))

range_end = etree.Element(qn(W_NS, "commentRangeEnd"))
range_end.set(qn(W_NS, "id"), COMMENT_ID)
new_nodes.append(range_end)

ref_run = etree.Element(qn(W_NS, "r"))
ref_rpr = etree.SubElement(ref_run, qn(W_NS, "rPr"))
ref_style = etree.SubElement(ref_rpr, qn(W_NS, "rStyle"))
ref_style.set(qn(W_NS, "val"), "CommentReference")
etree.SubElement(ref_run, qn(W_NS, "commentReference")).set(qn(W_NS, "id"), COMMENT_ID)
new_nodes.append(ref_run)

if after_text:
    new_nodes.append(make_run(after_text))

r_index = list(target_p).index(target_r)
target_p.remove(target_r)
for offset, node in enumerate(new_nodes):
    target_p.insert(r_index + offset, node)

parts["word/document.xml"] = etree.tostring(
    doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
)

# comments.xml part
comments_root = etree.Element(qn(W_NS, "comments"), nsmap={"w": W_NS})
comment_el = etree.SubElement(comments_root, qn(W_NS, "comment"))
comment_el.set(qn(W_NS, "id"), COMMENT_ID)
comment_el.set(qn(W_NS, "author"), AUTHOR)
comment_el.set(qn(W_NS, "date"), "2026-07-17T00:00:00Z")
comment_el.set(qn(W_NS, "initials"), "FR")
c_p = etree.SubElement(comment_el, qn(W_NS, "p"))
c_r = etree.SubElement(c_p, qn(W_NS, "r"))
c_t = etree.SubElement(c_r, qn(W_NS, "t"))
c_t.text = COMMENT_TEXT
parts["word/comments.xml"] = etree.tostring(
    comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
)

# [Content_Types].xml: register the comments part
ct_root = etree.fromstring(parts["[Content_Types].xml"])
override = etree.SubElement(ct_root, qn(CT_NS, "Override"))
override.set("PartName", "/word/comments.xml")
override.set(
    "ContentType",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
)
parts["[Content_Types].xml"] = etree.tostring(
    ct_root, xml_declaration=True, encoding="UTF-8", standalone=True
)

# word/_rels/document.xml.rels: register the comments relationship
rels_root = etree.fromstring(parts["word/_rels/document.xml.rels"])
existing_ids = [
    int(rel.get("Id")[3:])
    for rel in rels_root
    if rel.get("Id", "").startswith("rId") and rel.get("Id")[3:].isdigit()
]
new_rid = f"rId{max(existing_ids) + 1}"
new_rel = etree.SubElement(rels_root, qn(PKGREL_NS, "Relationship"))
new_rel.set("Id", new_rid)
new_rel.set(
    "Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
)
new_rel.set("Target", "comments.xml")
parts["word/_rels/document.xml.rels"] = etree.tostring(
    rels_root, xml_declaration=True, encoding="UTF-8", standalone=True
)

with zipfile.ZipFile(DOCX_PATH, "w", zipfile.ZIP_DEFLATED) as zout:
    for name, data in parts.items():
        zout.writestr(name, data)

print("wrote", DOCX_PATH)
PY
