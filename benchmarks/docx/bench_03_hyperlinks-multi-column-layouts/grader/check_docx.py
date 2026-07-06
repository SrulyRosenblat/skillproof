from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

WORKSPACE = Path("/workspace") if Path("/workspace").exists() else Path.cwd()
OUTPUT = WORKSPACE / "riverside_brief.docx"
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
W = "{%s}" % NS["w"]
R = "{%s}" % NS["r"]

EXPECTED_PARAGRAPHS = [
    "Riverside Expansion Brief",
    "Prepared for the September operations launch",
    "The Riverside pilot opens on September 14. Field teams need a one-page brief that links readers to the program portal and lets them jump directly to the Risks section.",
    "Program portal | Jump to Risks",
    "Overview",
    "The site will support the first wave of evening fulfillment volume for the east corridor.",
    "Managers should review the launch window, staffing checkpoints, and known constraints before September 14.",
    "Milestones",
    "Vendor onboarding closes August 12.",
    "Site readiness review is August 26.",
    "Final staffing confirmations are due September 2.",
    "Risks",
    "Badge printing can slip if headcount changes after August 20.",
    "The loading dock remains shared with the warehouse until September 7.",
    "Appendix Resources",
    "Escalation desk: ops@example.com",
    "Program portal: https://example.com/program-portal",
]


def fail(message: str) -> None:
    raise SystemExit(message)


def parse_xml(docx_path: Path, member: str):
    with ZipFile(docx_path) as zf:
        return ET.fromstring(zf.read(member))


def read_zip_text(docx_path: Path, member: str) -> str:
    with ZipFile(docx_path) as zf:
        return zf.read(member).decode("utf-8")


def get_paragraphs(root):
    body = root.find("w:body", NS)
    if body is None:
        fail("Document body is missing.")
    return body.findall("w:p", NS)


def paragraph_text(paragraph) -> str:
    parts = []
    for node in paragraph.iter():
        if node.tag in {W + "t", W + "instrText", W + "delText"}:
            parts.append(node.text or "")
    return "".join(parts)


def nonempty_paragraphs(paragraphs):
    return [p for p in paragraphs if paragraph_text(p).strip()]


def paragraph_style_id(paragraph):
    node = paragraph.find("w:pPr/w:pStyle", NS)
    return node.get(W + "val") if node is not None else None


def load_relationship_targets(docx_path: Path):
    root = parse_xml(docx_path, "word/_rels/document.xml.rels")
    targets = {}
    for rel in root.findall("rel:Relationship", NS):
        targets[rel.get("Id")] = {
            "type": rel.get("Type"),
            "target": rel.get("Target"),
            "target_mode": rel.get("TargetMode"),
        }
    return targets


def get_section_props(paragraph):
    return paragraph.find("w:pPr/w:sectPr", NS)


def get_page_settings(sect_pr):
    pg_sz = sect_pr.find("w:pgSz", NS) if sect_pr is not None else None
    pg_mar = sect_pr.find("w:pgMar", NS) if sect_pr is not None else None
    if pg_sz is None or pg_mar is None:
        return None
    return {
        "width": pg_sz.get(W + "w"),
        "height": pg_sz.get(W + "h"),
        "top": pg_mar.get(W + "top"),
        "right": pg_mar.get(W + "right"),
        "bottom": pg_mar.get(W + "bottom"),
        "left": pg_mar.get(W + "left"),
    }


def assert_letter_margins(sect_pr, label: str):
    settings = get_page_settings(sect_pr)
    if settings is None:
        fail(f"{label} is missing page size or margin settings.")
    expected = {
        "width": "12240",
        "height": "15840",
        "top": "1440",
        "right": "1440",
        "bottom": "1440",
        "left": "1440",
    }
    if settings != expected:
        fail(f"{label} must use US Letter with 1-inch margins, found {settings}.")


def assert_two_column_section(sect_pr, label: str):
    cols = sect_pr.find("w:cols", NS) if sect_pr is not None else None
    if cols is None:
        fail(f"{label} is missing column settings.")
    if cols.get(W + "num") != "2":
        fail(f"{label} must have exactly two columns.")
    if cols.get(W + "space") != "720":
        fail(f"{label} must use a 0.5 inch column gap.")
    if cols.get(W + "sep") != "1":
        fail(f"{label} must enable the vertical separator line between columns.")


def main():
    if not OUTPUT.exists():
        fail("Missing /workspace/riverside_brief.docx.")

    document = parse_xml(OUTPUT, "word/document.xml")
    paragraphs = get_paragraphs(document)
    visible_paragraphs = nonempty_paragraphs(paragraphs)
    visible_text = [paragraph_text(p).strip() for p in visible_paragraphs]
    if visible_text != EXPECTED_PARAGRAPHS:
        fail(f"Visible paragraph sequence does not match the required outline.\nExpected: {EXPECTED_PARAGRAPHS}\nFound: {visible_text}")

    style_expectations = {
        "Riverside Expansion Brief": "Heading1",
        "Overview": "Heading2",
        "Milestones": "Heading2",
        "Risks": "Heading2",
        "Appendix Resources": "Heading2",
    }
    for paragraph in visible_paragraphs:
        text = paragraph_text(paragraph).strip()
        if text in style_expectations:
            actual = paragraph_style_id(paragraph)
            if actual != style_expectations[text]:
                fail(f'Paragraph "{text}" must use built-in style {style_expectations[text]}, found {actual}.')

    summary_index = visible_text.index(EXPECTED_PARAGRAPHS[2])
    summary_paragraph = visible_paragraphs[summary_index]
    intro_sect_pr = get_section_props(summary_paragraph)
    if intro_sect_pr is None:
        fail("The opening summary paragraph must terminate the first section.")
    assert_letter_margins(intro_sect_pr, "First section")
    intro_cols = intro_sect_pr.find("w:cols", NS)
    if intro_cols is not None and intro_cols.get(W + "num") == "2":
        fail("The first section must remain single-column.")

    body_sect_pr = document.find("w:body/w:sectPr", NS)
    if body_sect_pr is None:
        fail("The document is missing final section properties.")
    assert_letter_margins(body_sect_pr, "Final section")
    assert_two_column_section(body_sect_pr, "Final section")

    rel_targets = load_relationship_targets(OUTPUT)
    nav_paragraph = visible_paragraphs[3]
    hyperlinks = nav_paragraph.findall("w:hyperlink", NS)
    if len(hyperlinks) != 2:
        fail("The navigation paragraph must contain exactly two real Word hyperlinks.")

    external = None
    internal = None
    for hyperlink in hyperlinks:
        text = "".join(t.text or "" for t in hyperlink.findall(".//w:t", NS))
        if text == "Program portal":
            external = hyperlink
        elif text == "Jump to Risks":
            internal = hyperlink
    if external is None or internal is None:
        fail("The navigation paragraph must contain hyperlink runs for both required link labels.")

    rel_id = external.get(R + "id")
    if not rel_id:
        fail("The external hyperlink must use a relationship-backed Word hyperlink.")
    rel = rel_targets.get(rel_id)
    if rel is None:
        fail("The external hyperlink relationship is missing.")
    if rel["target"] != "https://example.com/program-portal" or rel["target_mode"] != "External":
        fail("The external hyperlink target is incorrect.")

    if internal.get(W + "anchor") != "risks":
        fail('The internal hyperlink must target the bookmark named "risks".')

    risks_paragraph = visible_paragraphs[11]
    bookmark_names = [
        node.get(W + "name")
        for node in risks_paragraph.findall("w:bookmarkStart", NS)
        if node.get(W + "name")
    ]
    if "risks" not in bookmark_names:
        fail('The "Risks" heading paragraph must contain the bookmark named "risks".')

    appendix_heading = visible_paragraphs[14]
    appendix_index = paragraphs.index(appendix_heading)
    if appendix_index == 0:
        fail("Appendix heading cannot be the first paragraph.")
    previous_paragraph = paragraphs[appendix_index - 1]
    next_col_sect_pr = get_section_props(previous_paragraph)
    if next_col_sect_pr is None:
        fail("A section break must appear immediately before the Appendix Resources heading.")
    start_type = next_col_sect_pr.find("w:type", NS)
    if start_type is None or start_type.get(W + "val") != "nextColumn":
        fail('The section break before "Appendix Resources" must use start type "nextColumn".')
    assert_letter_margins(next_col_sect_pr, 'The "nextColumn" section break')
    assert_two_column_section(next_col_sect_pr, 'The "nextColumn" section break')


if __name__ == "__main__":
    main()
