import json
import math
import os

import pytest
from pypdf import PdfReader

WORKSPACE = os.getcwd()

EXPECTED = [
    {"source_file": "invoice_1.pdf", "invoice_number": "INV-1001", "total_due": 245.00, "author": "Acme Corp"},
    {"source_file": "invoice_2.pdf", "invoice_number": "INV-1002", "total_due": 89.50, "author": "Acme Corp"},
    {"source_file": "invoice_3.pdf", "invoice_number": "INV-1003", "total_due": 1204.75, "author": "Beta LLC"},
]


def _path(name):
    return os.path.join(WORKSPACE, name)


def test_combined_pdf_exists():
    assert os.path.isfile(_path("combined_invoices.pdf")), "combined_invoices.pdf was not created in /workspace"


def test_combined_pdf_has_three_pages_in_order_and_upright():
    reader = PdfReader(_path("combined_invoices.pdf"))
    assert len(reader.pages) == 3, f"expected 3 pages, found {len(reader.pages)}"

    for i, expected in enumerate(EXPECTED):
        page = reader.pages[i]
        text = page.extract_text() or ""
        assert expected["invoice_number"] in text, (
            f"page {i + 1} of combined_invoices.pdf does not contain "
            f"{expected['invoice_number']!r} (wrong content or wrong order)"
        )

    # invoice_3's page originally displayed upside down (rotation flag of 180);
    # the final combined document must display it right-side up.
    last_page = reader.pages[2]
    assert last_page.rotation % 360 == 0, (
        f"page 3 of combined_invoices.pdf is not right-side up (rotation={last_page.rotation})"
    )


def test_summary_json_exists_and_is_valid():
    path = _path("invoice_summary.json")
    assert os.path.isfile(path), "invoice_summary.json was not created in /workspace"
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, list), "invoice_summary.json must contain a JSON list"
    assert len(data) == 3, f"expected 3 entries in invoice_summary.json, found {len(data)}"


def test_summary_json_content_and_order():
    with open(_path("invoice_summary.json")) as f:
        data = json.load(f)

    for i, (entry, expected) in enumerate(zip(data, EXPECTED)):
        assert isinstance(entry, dict), f"entry {i} in invoice_summary.json is not an object"
        for key in ("source_file", "invoice_number", "total_due", "author"):
            assert key in entry, f"entry {i} in invoice_summary.json is missing key {key!r}"

        assert entry["source_file"] == expected["source_file"], (
            f"entry {i} source_file={entry['source_file']!r}, expected {expected['source_file']!r} "
            "(entries must be in the same order as the combined PDF)"
        )
        assert entry["invoice_number"] == expected["invoice_number"], (
            f"entry {i} invoice_number={entry['invoice_number']!r}, expected {expected['invoice_number']!r}"
        )
        assert isinstance(entry["total_due"], (int, float)), (
            f"entry {i} total_due must be a number, got {type(entry['total_due'])}"
        )
        assert math.isclose(entry["total_due"], expected["total_due"], abs_tol=0.001), (
            f"entry {i} total_due={entry['total_due']!r}, expected {expected['total_due']!r}"
        )
        assert entry["author"] == expected["author"], (
            f"entry {i} author={entry['author']!r}, expected {expected['author']!r}"
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
