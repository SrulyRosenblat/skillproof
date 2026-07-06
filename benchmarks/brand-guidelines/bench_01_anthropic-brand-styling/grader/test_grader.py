import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path


WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
BRIEF_PATH = WORKSPACE / "brief.json"
SVG_PATH = WORKSPACE / "poster.svg"
SUMMARY_PATH = WORKSPACE / "style-summary.json"

NS = {"svg": "http://www.w3.org/2000/svg"}

EXPECTED_HEADING_FONT = "Poppins, Arial, sans-serif"
EXPECTED_BODY_FONT = "Lora, Georgia, serif"
EXPECTED_MAIN_COLORS = {
    "dark": "#141413",
    "light": "#faf9f5",
    "mid_gray": "#b0aea5",
    "light_gray": "#e8e6dc",
}
EXPECTED_ACCENT_CYCLE = ["#d97757", "#6a9bcc", "#788c5d"]


def normalize_color(value: str) -> str:
    return value.strip().lower()


def parse_svg():
    assert SVG_PATH.exists(), "poster.svg is missing"
    tree = ET.parse(SVG_PATH)
    root = tree.getroot()
    return root


def parse_summary():
    assert SUMMARY_PATH.exists(), "style-summary.json is missing"
    with SUMMARY_PATH.open() as f:
        return json.load(f)


def parse_brief():
    with BRIEF_PATH.open() as f:
        return json.load(f)


def text_elements(root):
    return root.findall(".//svg:text", NS)


def rects(root):
    return root.findall(".//svg:rect", NS)


def circles(root):
    return root.findall(".//svg:circle", NS)


def required_texts(brief):
    items = [brief["title"], brief["subtitle"]]
    for section in brief["sections"]:
        items.append(section["heading"])
        items.extend(section["bullets"])
    items.extend([brief["quote"], brief["attribution"]])
    return items


def test_outputs_exist_and_svg_size():
    root = parse_svg()
    assert root.tag.endswith("svg")
    assert root.attrib.get("width") == "1200"
    assert root.attrib.get("height") == "900"


def test_required_shapes_and_positions():
    root = parse_svg()
    all_rects = rects(root)
    assert len(all_rects) >= 6, "expected background, banner, three cards, and quote strip"

    def find_rect(x, y, width, height):
        for rect in all_rects:
            if (
                rect.attrib.get("x") == str(x)
                and rect.attrib.get("y") == str(y)
                and rect.attrib.get("width") == str(width)
                and rect.attrib.get("height") == str(height)
            ):
                return rect
        return None

    assert find_rect(0, 0, 1200, 220) is not None, "top banner rectangle missing"
    assert find_rect(80, 300, 320, 260) is not None, "card 1 rectangle missing"
    assert find_rect(440, 300, 320, 260) is not None, "card 2 rectangle missing"
    assert find_rect(800, 300, 320, 260) is not None, "card 3 rectangle missing"
    assert find_rect(80, 620, 1040, 170) is not None, "footer quote strip missing"

    all_circles = circles(root)
    assert len(all_circles) == 3, "expected exactly three decorative circles"
    expected_centers = [("240", "255"), ("600", "255"), ("960", "255")]
    actual_centers = [(c.attrib.get("cx"), c.attrib.get("cy")) for c in all_circles]
    assert actual_centers == expected_centers
    for circle in all_circles:
        assert circle.attrib.get("r") == "22"


def test_brand_palette_and_fonts():
    root = parse_svg()

    fills = [normalize_color(node.attrib["fill"]) for node in root.iter() if "fill" in node.attrib]
    for color in [
        EXPECTED_MAIN_COLORS["dark"],
        EXPECTED_MAIN_COLORS["light"],
        EXPECTED_MAIN_COLORS["light_gray"],
        *EXPECTED_ACCENT_CYCLE,
    ]:
        assert normalize_color(color) in fills, f"missing brand color {color}"

    all_text = text_elements(root)
    assert len(all_text) == 13
    for node in all_text:
        assert "font-family" in node.attrib
        assert "font-size" in node.attrib
        assert "fill" in node.attrib
        size = int(node.attrib["font-size"])
        family = node.attrib["font-family"]
        if size >= 24:
            assert family == EXPECTED_HEADING_FONT
        else:
            assert family == EXPECTED_BODY_FONT


def test_text_content_and_contrast_rules():
    root = parse_svg()
    brief = parse_brief()
    nodes = text_elements(root)
    actual_texts = ["".join(node.itertext()).strip() for node in nodes]
    assert actual_texts == required_texts(brief)

    expected_fill_by_text = {
        brief["title"]: EXPECTED_MAIN_COLORS["light"],
        brief["subtitle"]: EXPECTED_MAIN_COLORS["light"],
        brief["quote"]: EXPECTED_MAIN_COLORS["light"],
        brief["attribution"]: EXPECTED_MAIN_COLORS["light"],
    }
    for section in brief["sections"]:
        expected_fill_by_text[section["heading"]] = EXPECTED_MAIN_COLORS["dark"]
        for bullet in section["bullets"]:
            expected_fill_by_text[bullet] = EXPECTED_MAIN_COLORS["dark"]

    for node in nodes:
        text = "".join(node.itertext()).strip()
        assert normalize_color(node.attrib["fill"]) == expected_fill_by_text[text]


def test_summary_schema_and_consistency():
    root = parse_svg()
    summary = parse_summary()
    assert set(summary.keys()) == {
        "heading_font",
        "body_font",
        "main_colors",
        "accent_cycle",
        "text_elements",
    }
    assert summary["heading_font"] == EXPECTED_HEADING_FONT
    assert summary["body_font"] == EXPECTED_BODY_FONT
    assert summary["main_colors"] == EXPECTED_MAIN_COLORS
    assert summary["accent_cycle"] == EXPECTED_ACCENT_CYCLE

    assert isinstance(summary["text_elements"], list)
    svg_text = text_elements(root)
    assert len(summary["text_elements"]) == len(svg_text)

    for summary_item, text_node in zip(summary["text_elements"], svg_text):
        assert set(summary_item.keys()) == {"text", "font_size", "font_family", "fill"}
        assert summary_item["text"] == "".join(text_node.itertext()).strip()
        assert summary_item["font_size"] == int(text_node.attrib["font-size"])
        assert summary_item["font_family"] == text_node.attrib["font-family"]
        assert normalize_color(summary_item["fill"]) == normalize_color(text_node.attrib["fill"])


def test_accent_cycle_left_to_right():
    root = parse_svg()
    all_circles = circles(root)
    actual_fills = [normalize_color(circle.attrib["fill"]) for circle in all_circles]
    assert actual_fills == EXPECTED_ACCENT_CYCLE
