import sys

from pypdf import PdfReader

EXPECTED = [
    "Report A - Page 1",
    "Report A - Page 2",
    "Report A - Page 3",
    "Report A - Page 4",
    "Report B - Page 1",
    "Report B - Page 3",
]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    try:
        reader = PdfReader("digest.pdf")
    except Exception as exc:
        fail(f"could not open digest.pdf: {exc}")

    pages = reader.pages
    if len(pages) != 7:
        fail(f"expected 7 pages in digest.pdf, found {len(pages)}")

    for i, expected_text in enumerate(EXPECTED):
        actual = (pages[i].extract_text() or "").strip()
        if actual != expected_text:
            fail(f"page {i + 1}: expected text {expected_text!r}, got {actual!r}")

    summary_text = (pages[6].extract_text() or "").strip()
    if "Digest Summary" not in summary_text:
        fail(f"page 7: expected to contain 'Digest Summary', got {summary_text!r}")

    print("OK: digest.pdf has correct page order and content")
    sys.exit(0)


if __name__ == "__main__":
    main()
