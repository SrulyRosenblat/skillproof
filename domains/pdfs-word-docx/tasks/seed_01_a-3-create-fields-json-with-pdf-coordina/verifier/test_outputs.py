"""Deterministic checks for /workspace/fields.json.

Expected numbers are derived from the fixed /workspace/form_structure.json
baked into the environment image, applying the standard non-fillable-form
field-map convention: entry x0 = label x1 + 5, entry x1 = next label's x0
(or the row's right boundary), entry top = label top, entry bottom = the
row's boundary line (or label bottom + default row height when the row has
no boundary line), and a checkbox's entry box is its own rectangle.
"""

import json
from pathlib import Path

import pytest

FIELDS_JSON = Path("/workspace/fields.json")

EXPECTED_TEXT_FIELDS = {
    "First Name": {
        "label_bounding_box": [46, 196, 96, 208],
        "entry_bounding_box": [101, 196, 216, 214],
    },
    "Last Name": {
        "label_bounding_box": [216, 196, 266, 208],
        "entry_bounding_box": [271, 196, 566, 214],
    },
    "Email Address": {
        "label_bounding_box": [46, 226, 122, 238],
        "entry_bounding_box": [127, 226, 566, 256],
    },
}

EXPECTED_CHECKBOXES = {
    "US Citizen - Yes": {
        "label_bounding_box": [300, 258, 330, 268],
        "entry_bounding_box": [336, 257, 346, 267],
    },
    "US Citizen - No": {
        "label_bounding_box": [360, 258, 384, 268],
        "entry_bounding_box": [390, 257, 400, 267],
    },
}

TOL = 0.5


@pytest.fixture(scope="module")
def fields_data():
    assert FIELDS_JSON.exists(), f"{FIELDS_JSON} was not created"
    with open(FIELDS_JSON) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fields_by_label(fields_data):
    assert "form_fields" in fields_data, "fields.json is missing 'form_fields'"
    by_label = {}
    for field in fields_data["form_fields"]:
        by_label[field["field_label"]] = field
    return by_label


def _boxes_close(actual, expected):
    assert len(actual) == 4
    for a, e in zip(actual, expected):
        assert abs(a - e) <= TOL, f"{actual} != {expected}"


def test_page_metadata_signals_pdf_point_coordinates(fields_data):
    pages = fields_data["pages"]
    assert len(pages) == 1
    page = pages[0]
    assert page["page_number"] == 1
    # Coordinates were extracted directly from the form's vector layout, not
    # from a rasterized image, so the page must be described in PDF-point
    # dimensions (not image-pixel dimensions).
    assert "pdf_width" in page, "page metadata must use the PDF-point coordinate convention"
    assert "pdf_height" in page, "page metadata must use the PDF-point coordinate convention"
    assert abs(page["pdf_width"] - 612) <= TOL
    assert abs(page["pdf_height"] - 792) <= TOL


def test_all_expected_fields_present_once(fields_by_label):
    expected_labels = set(EXPECTED_TEXT_FIELDS) | set(EXPECTED_CHECKBOXES)
    assert expected_labels.issubset(fields_by_label.keys())
    field_list_labels = list(fields_by_label.keys())
    assert len(field_list_labels) == len(set(field_list_labels)), "duplicate field_label entries"


@pytest.mark.parametrize("label", list(EXPECTED_TEXT_FIELDS))
def test_text_field_label_box_preserved(fields_by_label, label):
    field = fields_by_label[label]
    assert field["page_number"] == 1
    assert isinstance(field.get("description"), str) and field["description"].strip()
    _boxes_close(field["label_bounding_box"], EXPECTED_TEXT_FIELDS[label]["label_bounding_box"])


@pytest.mark.parametrize("label", list(EXPECTED_TEXT_FIELDS))
def test_text_field_entry_box_matches_convention(fields_by_label, label):
    field = fields_by_label[label]
    _boxes_close(field["entry_bounding_box"], EXPECTED_TEXT_FIELDS[label]["entry_bounding_box"])


def test_row_boundary_used_when_present_and_default_height_as_fallback(fields_by_label):
    # Row 1 ("First Name", "Last Name") has an explicit row boundary line at
    # y=214; row 2 ("Email Address") has none and must fall back to
    # label_bottom + default_row_height (238 + 18 = 256).
    assert abs(fields_by_label["First Name"]["entry_bounding_box"][3] - 214) <= TOL
    assert abs(fields_by_label["Last Name"]["entry_bounding_box"][3] - 214) <= TOL
    assert abs(fields_by_label["Email Address"]["entry_bounding_box"][3] - 256) <= TOL


def test_entry_x1_bounded_by_next_label_or_row_margin(fields_by_label):
    # "First Name" is followed by "Last Name" on the same row, so its entry
    # box must stop at "Last Name"'s label x0 (216), not run to the row
    # margin. "Last Name" is last on its row, so it runs to the row's right
    # boundary (566).
    assert abs(fields_by_label["First Name"]["entry_bounding_box"][2] - 216) <= TOL
    assert abs(fields_by_label["Last Name"]["entry_bounding_box"][2] - 566) <= TOL


@pytest.mark.parametrize("label", list(EXPECTED_CHECKBOXES))
def test_checkbox_entry_box_is_the_checkbox_rectangle(fields_by_label, label):
    field = fields_by_label[label]
    assert field["page_number"] == 1
    assert isinstance(field.get("description"), str) and field["description"].strip()
    _boxes_close(field["label_bounding_box"], EXPECTED_CHECKBOXES[label]["label_bounding_box"])
    _boxes_close(field["entry_bounding_box"], EXPECTED_CHECKBOXES[label]["entry_bounding_box"])
