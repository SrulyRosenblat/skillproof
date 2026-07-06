#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys

WORKSPACE = os.getcwd()
PDF_PATH = os.path.join(WORKSPACE, "quarterly_report.pdf")
DATA_PATH = os.path.join(WORKSPACE, "sales_data.json")
GRADING_DIR = os.path.join(WORKSPACE, ".grading")
JUDGE_DIR = os.path.join(WORKSPACE, ".judge")
QUESTIONS_PATH = os.path.join(JUDGE_DIR, "questions.json")
ANSWERS_PATH = os.path.join(JUDGE_DIR, "answers.json")


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if not os.path.isfile(PDF_PATH):
        fail(f"missing output file {PDF_PATH}")

    if not os.path.isfile(DATA_PATH):
        fail(f"missing input fixture {DATA_PATH}")

    with open(DATA_PATH) as f:
        data = json.load(f)

    quarters = data["quarters"]
    products = data["products"]
    title = data["report_title"]

    col_totals = [0] * len(quarters)
    row_totals = {}
    grand_total = 0
    for p in products:
        sales = p["sales"]
        rt = sum(sales)
        row_totals[p["name"]] = rt
        grand_total += rt
        for i, v in enumerate(sales):
            col_totals[i] += v

    try:
        from pypdf import PdfReader
        reader = PdfReader(PDF_PATH)
        if len(reader.pages) < 1:
            fail("PDF has no pages")
    except Exception as e:
        fail(f"could not open PDF with pypdf: {e}")

    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", PDF_PATH, "-"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception as e:
        fail(f"pdftotext failed to run: {e}")

    if proc.returncode != 0:
        fail(f"pdftotext exited with error: {proc.stderr}")

    text = proc.stdout

    if not text.strip():
        fail("no extractable text found in PDF (must be real text, not a scanned image)")

    if title not in text:
        fail(f"report title '{title}' not found in extracted PDF text")

    for p in products:
        if p["name"] not in text:
            fail(f"product name '{p['name']}' not found in extracted PDF text")

    def has_number(n):
        return re.search(rf"(?<!\d){n}(?!\d)", text) is not None

    for name, rt in row_totals.items():
        if not has_number(rt):
            fail(f"row total for '{name}' ({rt}) not found in extracted PDF text")

    for i, ct in enumerate(col_totals):
        if not has_number(ct):
            fail(f"column total for {quarters[i]} ({ct}) not found in extracted PDF text")

    if not has_number(grand_total):
        fail(f"grand total ({grand_total}) not found in extracted PDF text")

    os.makedirs(GRADING_DIR, exist_ok=True)
    os.makedirs(JUDGE_DIR, exist_ok=True)

    page_prefix = os.path.join(GRADING_DIR, "page1")
    try:
        subprocess.run(
            ["pdftoppm", "-png", "-r", "150", "-f", "1", "-l", "1", PDF_PATH, page_prefix],
            check=True, timeout=30,
        )
    except Exception as e:
        fail(f"pdftoppm rendering failed: {e}")

    rendered = None
    for candidate in (page_prefix + "-1.png", page_prefix + "-01.png", page_prefix + ".png"):
        if os.path.isfile(candidate):
            rendered = candidate
            break
    if rendered is None:
        fail("could not find rendered page image produced by pdftoppm")

    if os.path.isfile(ANSWERS_PATH):
        with open(ANSWERS_PATH) as f:
            answers = json.load(f).get("answers", {})
        for qid in ("header_shading", "grid_lines"):
            if answers.get(qid) is not True:
                fail(f"visual judge check '{qid}' did not pass")
        print("PASS")
        sys.exit(0)
    else:
        questions = {
            "questions": [
                {
                    "id": "header_shading",
                    "question": "In this image, does the table's header row (the row with column labels) have a background fill color that is clearly different from the background of the data rows below it?",
                    "image": rendered,
                },
                {
                    "id": "grid_lines",
                    "question": "In this image, are there visible border/grid lines separating every cell of the table from its neighboring cells, both between rows and between columns?",
                    "image": rendered,
                },
            ]
        }
        with open(QUESTIONS_PATH, "w") as f:
            json.dump(questions, f, indent=2)
        sys.exit(3)


if __name__ == "__main__":
    main()
