from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

WORKSPACE = Path("/workspace") if Path("/workspace").exists() else Path.cwd()
OUTPUT = WORKSPACE / "repaired_brief.docx"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
W = "{%s}" % NS["w"]


def fail(message: str) -> None:
    raise SystemExit(message)


def parse_xml(docx_path: Path, member: str):
    with ZipFile(docx_path) as zf:
        try:
            return ET.fromstring(zf.read(member))
        except KeyError:
            fail(f"Missing {member} in output DOCX.")


def zip_members(docx_path: Path):
    with ZipFile(docx_path) as zf:
        return set(zf.namelist())


def get_paragraphs(document_root):
    body = document_root.find("w:body", NS)
    if body is None:
        fail("Document body is missing.")
    return body.findall("w:p", NS)


def paragraph_text(paragraph) -> str:
    return "".join(node.text or "" for node in paragraph.iter() if node.tag == W + "t")


def text_chunks(paragraph):
    return [node.text or "" for node in paragraph.iter() if node.tag == W + "t"]


def has_tab_run(paragraph) -> bool:
    return paragraph.find(".//w:tab", NS) is not None


def right_tab_stops(paragraph):
    return paragraph.findall("w:pPr/w:tabs/w:tab", NS)


def numbering_props(paragraph):
    num_pr = paragraph.find("w:pPr/w:numPr", NS)
    if num_pr is None:
        return None
    ilvl = num_pr.find("w:ilvl", NS)
    num_id = num_pr.find("w:numId", NS)
    if ilvl is None or num_id is None:
        return None
    return {
        "level": ilvl.get(W + "val"),
        "num_id": num_id.get(W + "val"),
    }


def numbering_maps(numbering_root):
    num_to_abstract = {}
    abstract_formats = {}
    for abstract in numbering_root.findall("w:abstractNum", NS):
        abstract_id = abstract.get(W + "abstractNumId")
        lvl = abstract.find("w:lvl", NS)
        fmt = None
        if lvl is not None:
            num_fmt = lvl.find("w:numFmt", NS)
            fmt = num_fmt.get(W + "val") if num_fmt is not None else None
        abstract_formats[abstract_id] = fmt
    for num in numbering_root.findall("w:num", NS):
        num_id = num.get(W + "numId")
        abstract_ref = num.find("w:abstractNumId", NS)
        if abstract_ref is not None:
            num_to_abstract[num_id] = abstract_ref.get(W + "val")
    return num_to_abstract, abstract_formats


def format_for_num_id(num_id: str, num_to_abstract: dict, abstract_formats: dict) -> str | None:
    abstract_id = num_to_abstract.get(num_id)
    if abstract_id is None:
        return None
    return abstract_formats.get(abstract_id)


def check_schedule_paragraph(paragraph, left: str, right: str) -> None:
    if text_chunks(paragraph) != [left, right]:
        fail(f'Schedule paragraph must contain only "{left}" and "{right}" text chunks.')
    if not has_tab_run(paragraph):
        fail(f'Schedule paragraph "{left}" must contain a real tab character.')
    tabs = right_tab_stops(paragraph)
    if len(tabs) != 1:
        fail(f'Schedule paragraph "{left}" must define exactly one tab stop.')
    tab = tabs[0]
    if tab.get(W + "val") != "right":
        fail(f'Schedule paragraph "{left}" must use a right-aligned tab stop.')


def check_bullet_paragraph(paragraph, expected_text: str, num_to_abstract: dict, abstract_formats: dict) -> str:
    if paragraph_text(paragraph) != expected_text:
        fail(f'Bullet paragraph text must be "{expected_text}".')
    props = numbering_props(paragraph)
    if props is None:
        fail(f'Bullet paragraph "{expected_text}" is missing Word numbering metadata.')
    if props["level"] != "0":
        fail(f'Bullet paragraph "{expected_text}" must be at numbering level 0.')
    if format_for_num_id(props["num_id"], num_to_abstract, abstract_formats) != "bullet":
        fail(f'Bullet paragraph "{expected_text}" must use bullet numbering.')
    return props["num_id"]


def check_decimal_paragraph(paragraph, expected_text: str, num_to_abstract: dict, abstract_formats: dict) -> str:
    if paragraph_text(paragraph) != expected_text:
        fail(f'Numbered paragraph text must be "{expected_text}".')
    props = numbering_props(paragraph)
    if props is None:
        fail(f'Numbered paragraph "{expected_text}" is missing Word numbering metadata.')
    if props["level"] != "0":
        fail(f'Numbered paragraph "{expected_text}" must be at numbering level 0.')
    if format_for_num_id(props["num_id"], num_to_abstract, abstract_formats) != "decimal":
        fail(f'Numbered paragraph "{expected_text}" must use decimal numbering.')
    return props["num_id"]


def check_dot_leader_paragraph(paragraph, left: str, right: str) -> None:
    if text_chunks(paragraph) != [left, right]:
        fail(f'Dot-leader paragraph must contain only "{left}" and "{right}" text chunks.')
    ptab = paragraph.find(".//w:ptab", NS)
    if ptab is None:
        fail(f'Dot-leader paragraph "{left}" must contain a positional tab.')
    if ptab.get(W + "leader") != "dot":
        fail(f'Dot-leader paragraph "{left}" must use dot leader formatting.')
    if ptab.get(W + "alignment") != "right":
        fail(f'Dot-leader paragraph "{left}" must right-align the page number.')
    if ptab.get(W + "relativeTo") != "margin":
        fail(f'Dot-leader paragraph "{left}" must be relative to the margin.')


def main():
    if not OUTPUT.exists():
        fail("Missing /workspace/repaired_brief.docx.")

    members = zip_members(OUTPUT)
    for required in ["word/document.xml", "word/styles.xml", "word/numbering.xml"]:
        if required not in members:
            fail(f"Output DOCX is missing {required}.")

    document = parse_xml(OUTPUT, "word/document.xml")
    numbering = parse_xml(OUTPUT, "word/numbering.xml")
    num_to_abstract, abstract_formats = numbering_maps(numbering)

    if document.find(".//w:tbl", NS) is not None:
        fail("Tables are not allowed anywhere in the output document.")

    paragraphs = get_paragraphs(document)
    if len(paragraphs) != 16:
        fail(f"Expected 16 paragraphs, found {len(paragraphs)}.")

    expected_plain = {
        0: "Field Launch Brief",
        3: "Supplies",
        6: "Launch Checklist",
        10: "Escalation Steps",
        13: "Reference Pages",
    }
    for index, expected in expected_plain.items():
        actual = paragraph_text(paragraphs[index])
        if actual != expected:
            fail(f'Paragraph {index + 1} must be "{expected}", found "{actual}".')

    check_schedule_paragraph(paragraphs[1], "Operations", "October 2026")
    check_schedule_paragraph(paragraphs[2], "Safety review", "November 2026")

    bullet_num_ids = {
        check_bullet_paragraph(paragraphs[4], "Printed maps", num_to_abstract, abstract_formats),
        check_bullet_paragraph(paragraphs[5], "Spare badges", num_to_abstract, abstract_formats),
    }
    if len(bullet_num_ids) != 1:
        fail("The two bullet paragraphs must belong to the same bullet list.")

    checklist_ids = [
        check_decimal_paragraph(paragraphs[7], "Confirm badges", num_to_abstract, abstract_formats),
        check_decimal_paragraph(paragraphs[8], "Print route cards", num_to_abstract, abstract_formats),
        check_decimal_paragraph(paragraphs[9], "Load radios", num_to_abstract, abstract_formats),
    ]
    if len(set(checklist_ids)) != 1:
        fail("The Launch Checklist items must belong to one continuous numbered list.")

    escalation_ids = [
        check_decimal_paragraph(paragraphs[11], "Call site lead", num_to_abstract, abstract_formats),
        check_decimal_paragraph(paragraphs[12], "Email duty manager", num_to_abstract, abstract_formats),
    ]
    if len(set(escalation_ids)) != 1:
        fail("The Escalation Steps items must belong to one continuous numbered list.")
    if escalation_ids[0] == checklist_ids[0]:
        fail("Escalation Steps must use a separate numbering instance so the list restarts at 1.")

    check_dot_leader_paragraph(paragraphs[14], "Packing list", "2")
    check_dot_leader_paragraph(paragraphs[15], "Incident form", "5")

    document_xml_text = ZipFile(OUTPUT).read("word/document.xml").decode("utf-8")
    for forbidden in ["||", ">>", "•", "1. Confirm badges", "2. Print route cards", "3. Load radios", "1. Call site lead", "2. Email duty manager"]:
        if forbidden in document_xml_text:
            fail(f'Forbidden fake marker text "{forbidden}" is still present in word/document.xml.')


if __name__ == "__main__":
    main()
