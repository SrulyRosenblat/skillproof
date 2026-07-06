# Benchmark: Merge invoices, fix page rotation, and extract text/metadata with pypdf

## Capability tested

This benchmark targets the "pypdf - Basic Operations" portion of the PDF
skill: merging pages from multiple PDFs into one output file in a specific
order, rotating an individual page's orientation before it goes into the
merged output, extracting a page's text content, and reading a PDF's
document metadata (Author field). These are exactly the operations shown in
the skill's Quick Start and "pypdf - Basic Operations" sections (merge,
rotate, extract metadata, extract text), combined into one realistic
multi-step task.

`pdfplumber` is not installed in the sandbox, so this benchmark does not
require table extraction — it exercises the pypdf-based text/metadata
extraction and page manipulation instead, which is the part of the cluster
that overlaps with the available tooling.

Why it matters: real-world PDF workflows rarely require just one operation in
isolation. An agent that has internalized the skill knows that `PdfWriter`
pages are independent `PageObject`s that can be individually rotated with
`page.rotate(angle)` before being added with `writer.add_page(page)`, that
`page.extract_text()` is the way to pull text back out, and that
`reader.metadata.author` (etc.) exposes document metadata — and will combine
these idioms directly. An agent without this knowledge has to discover the
`PdfReader`/`PdfWriter` API and the fact that rotation is a per-page,
additive integer property (multiples of 90) largely from scratch.

## Input fixtures (`files/`)

Three single-page invoice PDFs generated with reportlab:

- `invoice_1.pdf` — Author "Acme Corp", `Invoice Number: INV-1001`, `Total Due: $245.00`, correctly oriented (rotation 0).
- `invoice_2.pdf` — Author "Acme Corp", `Invoice Number: INV-1002`, `Total Due: $89.50`, correctly oriented (rotation 0).
- `invoice_3.pdf` — Author "Beta LLC", `Invoice Number: INV-1003`, `Total Due: $1,204.75`, but its single page carries a `/Rotate 180` flag, i.e. it currently displays upside down.

## Task

The model is asked (see `task_prompt.md`) to:

1. Merge the three PDFs' pages, in numeric order, into `combined_invoices.pdf` (3 pages).
2. Correct `invoice_3.pdf`'s page so it displays right-side up in the merged output, leaving the other two pages untouched.
3. Write `invoice_summary.json`: a JSON array of 3 objects (same order as the merged PDF), each with `source_file`, `invoice_number`, `total_due` (a number), and `author`.

The task prompt never mentions pypdf, `PdfReader`/`PdfWriter`, `.rotate()`,
`.extract_text()`, or `.metadata` — it only states the desired end state, so
the benchmark measures whether the agent brings that API knowledge itself.

## Grading (`grader/grade.sh` → `grader/test_grade.py`)

Fully deterministic, no LLM judge needed (nothing here is visual/subjective —
rotation and text content are both directly inspectable with pypdf). The
grader runs with cwd = `/workspace` and executes `pytest grader/test_grade.py`,
which:

1. Asserts `combined_invoices.pdf` exists.
2. Opens it with `pypdf.PdfReader` and checks:
   - it has exactly 3 pages,
   - page `i`'s extracted text contains the expected invoice number for
     source file `i` (`INV-1001`, `INV-1002`, `INV-1003` in that order) —
     this catches wrong ordering or missing pages,
   - the third page's `.rotation` is a multiple of 360 (i.e., effectively
     upright) — this catches a naive merge that forgets to fix the
     upside-down page. (`pypdf`'s `rotate()` is additive rather than
     normalizing mod 360, so the reference solution's `-page.rotation`
     correction and any other angle that nets out to a multiple of 360 both
     pass.)
3. Asserts `invoice_summary.json` exists and parses as a JSON list of 3 objects.
4. Checks each entry's `source_file`, `invoice_number`, `total_due` (numeric,
   within 0.001 of the expected value — so `1204.75` parsed from
   `"$1,204.75"` is required), and `author` against the known-correct values,
   in order.

Running `bash grader/grade.sh` against just `files/` (untouched workspace)
fails (missing output files). Running it against `files/` +
`reference_solution/` passes.

## Reference solution (`reference_solution/`)

`solve.py` shows one correct approach: for each source PDF, open it with
`PdfReader`, and if `page.rotation % 360 != 0`, counter-rotate it with
`page.rotate(-page.rotation)` before adding it to a shared `PdfWriter`;
extract text with `page.extract_text()` and parse the invoice number/total
with a couple of regexes; read `reader.metadata.author` for the author field;
write `combined_invoices.pdf` and `invoice_summary.json`. The committed
`combined_invoices.pdf` and `invoice_summary.json` in this directory are the
actual output of running that script against `files/`.
