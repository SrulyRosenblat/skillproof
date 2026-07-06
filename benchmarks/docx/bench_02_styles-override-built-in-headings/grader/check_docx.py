from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

WORKSPACE = Path("/workspace") if Path("/workspace").exists() else Path.cwd()
SOURCE = WORKSPACE / "files" / "source_handbook.docx"
OUTPUT = WORKSPACE / "restyled_handbook.docx"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{%s}" % NS["w"]


def fail(message: str) -> None:
    raise SystemExit(message)


def parse_xml(docx_path: Path, member: str):
    with ZipFile(docx_path) as zf:
        return ET.fromstring(zf.read(member))


def paragraph_summary(docx_path: Path):
    root = parse_xml(docx_path, "word/document.xml")
    body = root.find("w:body", NS)
    items = []
    for p in body.findall("w:p", NS):
        style = p.find("w:pPr/w:pStyle", NS)
        style_id = style.get(W + "val") if style is not None else None
        text = "".join(t.text or "" for t in p.findall(".//w:t", NS))
        ppr = p.find("w:pPr", NS)
        ppr_children = []
        if ppr is not None:
            ppr_children = [child.tag.split("}", 1)[1] for child in ppr]
        banned_run_props = []
        for rpr in p.findall("w:r/w:rPr", NS):
            for child in rpr:
                local = child.tag.split("}", 1)[1]
                if local in {"rFonts", "b", "color", "sz", "szCs", "i", "u"}:
                    banned_run_props.append(local)
        items.append(
            {
                "style_id": style_id,
                "text": text,
                "ppr_children": ppr_children,
                "banned_run_props": banned_run_props,
            }
        )
    return items


def get_style(docx_path: Path, style_id: str):
    root = parse_xml(docx_path, "word/styles.xml")
    for style in root.findall("w:style", NS):
        if style.get(W + "styleId") == style_id:
            return style
    fail(f"Missing style definition for {style_id}.")


def get_attr(element, xpath: str, attr: str, required: bool = True):
    node = element.find(xpath, NS)
    if node is None:
        if required:
            fail(f"Missing XML node {xpath}.")
        return None
    value = node.get(W + attr)
    if value is None and required:
        fail(f"Missing attribute {attr} on {xpath}.")
    return value


def assert_font_block(style, font: str, size: str, color: str):
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        actual = get_attr(style, "w:rPr/w:rFonts", attr)
        if actual != font:
            fail(f"Expected font {font} on style {style.get(W + 'styleId')} attr {attr}, found {actual}.")
    if style.find("w:rPr/w:b", NS) is None:
        fail("Expected bold to be enabled on heading style.")
    if get_attr(style, "w:rPr/w:color", "val") != color:
        fail(f"Expected color {color}.")
    if get_attr(style, "w:rPr/w:sz", "val") != size:
        fail(f"Expected size {size}.")
    if get_attr(style, "w:rPr/w:szCs", "val") != size:
        fail(f"Expected size {size} in szCs.")


def main():
    if not OUTPUT.exists():
        fail("Missing /workspace/restyled_handbook.docx.")

    source_paras = paragraph_summary(SOURCE)
    output_paras = paragraph_summary(OUTPUT)
    if len(source_paras) != len(output_paras):
        fail("Paragraph count changed.")

    for idx, (src, out) in enumerate(zip(source_paras, output_paras), start=1):
        if src["text"] != out["text"]:
            fail(f"Paragraph {idx} text changed.")
        if src["style_id"] != out["style_id"]:
            fail(f"Paragraph {idx} style assignment changed.")
        if out["style_id"] in {"Heading1", "Heading2"}:
            if out["ppr_children"] != ["pStyle"]:
                fail(f"Paragraph {idx} has direct paragraph formatting instead of relying only on pStyle.")
            if out["banned_run_props"]:
                fail(f"Paragraph {idx} has direct run formatting: {sorted(set(out['banned_run_props']))}.")

    styles_root = parse_xml(OUTPUT, "word/styles.xml")
    defaults_font = get_attr(styles_root, "w:docDefaults/w:rPrDefault/w:rPr/w:rFonts", "ascii")
    defaults_size = get_attr(styles_root, "w:docDefaults/w:rPrDefault/w:rPr/w:sz", "val")
    defaults_size_cs = get_attr(styles_root, "w:docDefaults/w:rPrDefault/w:rPr/w:szCs", "val")
    if defaults_font != "Arial":
        fail(f"Expected default document font Arial, found {defaults_font}.")
    if defaults_size != "24" or defaults_size_cs != "24":
        fail("Expected default document size to be 24 half-points (12pt).")

    heading1 = get_style(OUTPUT, "Heading1")
    if get_attr(heading1, "w:name", "val") != "Heading 1":
        fail("Heading1 style must keep the built-in Heading 1 name.")
    if get_attr(heading1, "w:basedOn", "val") != "Normal":
        fail("Heading1 must be based on Normal.")
    if get_attr(heading1, "w:next", "val") != "Normal":
        fail("Heading1 must flow to Normal.")
    if get_attr(heading1, "w:pPr/w:spacing", "before") != "240":
        fail("Heading1 spacing before must be 240 twips.")
    if get_attr(heading1, "w:pPr/w:spacing", "after") != "240":
        fail("Heading1 spacing after must be 240 twips.")
    if get_attr(heading1, "w:pPr/w:outlineLvl", "val") != "0":
        fail("Heading1 outline level must be 0.")
    assert_font_block(heading1, "Arial", "32", "000000")

    heading2 = get_style(OUTPUT, "Heading2")
    if get_attr(heading2, "w:name", "val") != "Heading 2":
        fail("Heading2 style must keep the built-in Heading 2 name.")
    if get_attr(heading2, "w:basedOn", "val") != "Normal":
        fail("Heading2 must be based on Normal.")
    if get_attr(heading2, "w:next", "val") != "Normal":
        fail("Heading2 must flow to Normal.")
    if get_attr(heading2, "w:pPr/w:spacing", "before") != "180":
        fail("Heading2 spacing before must be 180 twips.")
    if get_attr(heading2, "w:pPr/w:spacing", "after") != "180":
        fail("Heading2 spacing after must be 180 twips.")
    if get_attr(heading2, "w:pPr/w:outlineLvl", "val") != "1":
        fail("Heading2 outline level must be 1.")
    assert_font_block(heading2, "Arial", "28", "000000")


if __name__ == "__main__":
    main()
