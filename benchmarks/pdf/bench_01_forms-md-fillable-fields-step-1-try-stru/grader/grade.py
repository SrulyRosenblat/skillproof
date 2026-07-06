"""
Deterministic grader for the "fill a non-fillable PDF form" benchmark.

Strategy: render the produced filled_form.pdf through `pdftotext -bbox`
(poppler) to get exact word-level coordinates, then check -- purely from
that rendered geometry -- that each value from values.json was placed on
the correct row, to the right of its own label, without overlapping any
label or any other field's text. This is a property-based / executed check:
we never grep the agent's source code, only the PDF it produced.
"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

WORKDIR = Path(os.environ.get("GRADE_WORKDIR", "/workspace"))

EXPECTED_VALUES = {
    "full_name": "Jordan Alvarez",
    "employee_id": "EMP-48213",
    "department": "Finance",
    "start_date": "2026-03-16",
}

# Ground-truth words present in the original, unfilled application_form.pdf
# (text, xMin, yMin, xMax, yMax) as reported by `pdftotext -bbox` at the time
# the fixture was generated. Used to (a) know each label's exact geometry and
# (b) filter label words out of the filled PDF's word list so only the
# agent-added value words remain.
ORIGINAL_WORDS = [
    ("Employee", 72.000, 41.948, 138.136, 54.898),
    ("Onboarding", 142.028, 41.948, 221.366, 54.898),
    ("Form", 225.258, 41.948, 260.258, 54.898),
    ("Full", 72.000, 84.102, 89.721, 94.277),
    ("Name:", 92.779, 84.102, 125.174, 94.277),
    ("Employee", 72.000, 154.102, 120.906, 164.277),
    ("ID:", 123.964, 154.102, 138.022, 164.277),
    ("Manager", 72.000, 204.102, 115.406, 214.277),
    ("Name:", 118.464, 204.102, 150.859, 214.277),
    ("Start", 72.000, 264.102, 95.232, 274.277),
    ("Date:", 98.290, 264.102, 124.580, 274.277),
    ("Department:", 258.022, 154.102, 318.544, 164.277),
]

# Row bands (yMin, yMax) with padding, in the same top-down PDF-point
# coordinates that `pdftotext -bbox` reports (and that fields.json must use).
ROW_BANDS = {
    "full_name": (76.0, 102.0),
    "employee_id": (146.0, 172.0),
    "department": (146.0, 172.0),
    "start_date": (256.0, 282.0),
}
MANAGER_ROW_BAND = (196.0, 222.0)  # distractor row -- must stay empty

# Each field's own label right edge (xMax) -- value must start to the right of this.
LABEL_XMAX = {
    "full_name": 125.174,
    "employee_id": 138.022,
    "department": 318.544,
    "start_date": 124.580,
}

DEPARTMENT_LABEL_XMIN = 258.022
PAGE_RIGHT_BOUND = 560.0
PAGE_W, PAGE_H = 612.0, 792.0

FAIL = []


def fail(msg):
    FAIL.append(msg)


def bbox_close(a, b, tol=0.75):
    return all(abs(a[i] - b[i]) <= tol for i in range(4))


def run_pdftotext_bbox(pdf_path):
    result = subprocess.run(
        ["pdftotext", "-bbox", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        fail(f"pdftotext failed on {pdf_path}: {result.stderr.strip()}")
        return []
    xml_text = result.stdout
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        fail(f"could not parse pdftotext -bbox output for {pdf_path}: {e}")
        return []
    for el in root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    page_el = root.find(".//page")
    if page_el is None:
        fail(f"no page found in {pdf_path}")
        return []
    words = []
    for w in page_el.findall("word"):
        words.append({
            "text": w.text or "",
            "xMin": float(w.get("xMin")),
            "yMin": float(w.get("yMin")),
            "xMax": float(w.get("xMax")),
            "yMax": float(w.get("yMax")),
        })
    return words


def main():
    filled_pdf = WORKDIR / "filled_form.pdf"
    fields_json_path = WORKDIR / "fields.json"
    values_json_path = WORKDIR / "values.json"

    if not filled_pdf.exists():
        fail("filled_form.pdf does not exist in /workspace")
    if not fields_json_path.exists():
        fail("fields.json does not exist in /workspace")

    if FAIL:
        return report()

    # values.json must be untouched
    if values_json_path.exists():
        try:
            actual_values = json.loads(values_json_path.read_text())
            if actual_values != EXPECTED_VALUES:
                fail("values.json was modified from its original content")
        except Exception as e:
            fail(f"values.json is not valid JSON: {e}")
    else:
        fail("values.json is missing from /workspace (it should not have been deleted)")

    # --- validate fields.json schema ---
    try:
        fields_data = json.loads(fields_json_path.read_text())
    except Exception as e:
        fail(f"fields.json is not valid JSON: {e}")
        return report()

    if not isinstance(fields_data, list):
        fail("fields.json must be a JSON array")
        return report()

    by_key = {}
    for i, entry in enumerate(fields_data):
        if not isinstance(entry, dict):
            fail(f"fields.json[{i}] is not an object")
            continue
        for req in ("field_key", "page", "entry_bounding_box", "value"):
            if req not in entry:
                fail(f"fields.json[{i}] missing required key '{req}'")
        key = entry.get("field_key")
        if key in by_key:
            fail(f"duplicate field_key '{key}' in fields.json")
        by_key[key] = entry

    expected_keys = set(EXPECTED_VALUES.keys())
    if set(by_key.keys()) != expected_keys:
        fail(
            f"fields.json field_key set {sorted(by_key.keys())} does not match "
            f"expected {sorted(expected_keys)}"
        )

    for key, entry in by_key.items():
        if key not in expected_keys:
            continue
        box = entry.get("entry_bounding_box")
        if not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)):
            fail(f"fields.json entry for '{key}' has invalid entry_bounding_box: {box}")
            continue
        x0, y0, x1, y1 = box
        if not (0 <= x0 < x1 <= PAGE_W and 0 <= y0 < y1 <= PAGE_H):
            fail(f"fields.json entry for '{key}' has out-of-range/inverted entry_bounding_box: {box}")
        if entry.get("value") != EXPECTED_VALUES[key]:
            fail(
                f"fields.json entry for '{key}' has value {entry.get('value')!r}, "
                f"expected {EXPECTED_VALUES[key]!r}"
            )
        if entry.get("page") != 1:
            fail(f"fields.json entry for '{key}' has page {entry.get('page')!r}, expected 1")

    if FAIL:
        return report()

    # --- inspect the rendered filled_form.pdf ---
    all_words = run_pdftotext_bbox(filled_pdf)
    if FAIL:
        return report()

    # Filter out the original label/title words to isolate agent-added content.
    value_words = []
    for w in all_words:
        wt = (w["text"], w["xMin"], w["yMin"], w["xMax"], w["yMax"])
        if any(bbox_close(wt[1:], orig[1:]) and wt[0] == orig[0] for orig in ORIGINAL_WORDS):
            continue
        value_words.append(w)

    # Nothing should have been written on the distractor "Manager Name" row.
    lo, hi = MANAGER_ROW_BAND
    stray = [w for w in value_words if lo <= w["yMin"] and w["yMax"] <= hi]
    if stray:
        fail(f"unexpected text found on the 'Manager Name' row (should be left blank): {stray}")

    field_combined_bbox = {}

    for field_key, value in EXPECTED_VALUES.items():
        tokens = value.split()
        matches = [w for w in value_words if w["text"] in tokens]
        if len(matches) < len(tokens):
            fail(
                f"could not find rendered text for field '{field_key}' "
                f"(expected value {value!r}) in filled_form.pdf"
            )
            continue
        # pick the closest matching set: sort by xMin, take the run whose count == expected
        matches.sort(key=lambda w: w["xMin"])
        # simple heuristic: use all matches (values are short & token texts are unique
        # across fields in this fixture, so no ambiguity expected)
        used = matches[: len(tokens)] if len(matches) > len(tokens) else matches
        xs_min = min(w["xMin"] for w in used)
        ys_min = min(w["yMin"] for w in used)
        xs_max = max(w["xMax"] for w in used)
        ys_max = max(w["yMax"] for w in used)
        field_combined_bbox[field_key] = (xs_min, ys_min, xs_max, ys_max)

        row_lo, row_hi = ROW_BANDS[field_key]
        if not (row_lo <= ys_min and ys_max <= row_hi):
            fail(
                f"field '{field_key}' text is not within its label's row "
                f"(text y-range {ys_min:.1f}-{ys_max:.1f}, expected within {row_lo}-{row_hi})"
            )

        if xs_min <= LABEL_XMAX[field_key] + 1:
            fail(
                f"field '{field_key}' text (xMin={xs_min:.1f}) does not start clearly to the "
                f"right of its own label (label ends at x={LABEL_XMAX[field_key]:.1f})"
            )

        if xs_max > PAGE_RIGHT_BOUND:
            fail(f"field '{field_key}' text (xMax={xs_max:.1f}) runs past the page margin")

        if field_key == "employee_id" and xs_max >= DEPARTMENT_LABEL_XMIN - 1:
            fail(
                f"field 'employee_id' text (xMax={xs_max:.1f}) overlaps/collides with the "
                f"'Department:' label that shares its row (starts at x={DEPARTMENT_LABEL_XMIN:.1f})"
            )

        # must not intersect any label/title word's bounding box
        for orig in ORIGINAL_WORDS:
            _, oxm, oym, oxM, oyM = orig
            if xs_min < oxM and xs_max > oxm and ys_min < oyM and ys_max > oym:
                fail(f"field '{field_key}' text overlaps label word {orig[0]!r} at {orig[1:]}")

    if FAIL:
        return report()

    # --- cross-check fields.json bounding boxes against actually-rendered text ---
    PAD = 3.0
    for field_key, (xs_min, ys_min, xs_max, ys_max) in field_combined_bbox.items():
        entry = by_key[field_key]
        x0, y0, x1, y1 = entry["entry_bounding_box"]
        if not (x0 <= xs_min + PAD and y0 <= ys_min + PAD and x1 >= xs_max - PAD and y1 >= ys_max - PAD):
            fail(
                f"fields.json entry_bounding_box for '{field_key}' ({entry['entry_bounding_box']}) "
                f"does not contain the actual rendered text bbox "
                f"({xs_min:.1f}, {ys_min:.1f}, {xs_max:.1f}, {ys_max:.1f})"
            )

    return report()


def report():
    if FAIL:
        print("FAIL:")
        for msg in FAIL:
            print(f"  - {msg}")
        return 1
    print("PASS: all fields correctly placed and validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
