# Benchmark: Styled Sales Report Table with ReportLab

## Capability under test

This benchmark targets the **reportlab Advanced Features** portion of the
"qpdf Advanced Features / pdfplumber Advanced Features / reportlab Advanced
Features" cluster — specifically the "Create Professional Reports with Tables"
pattern: building a `reportlab.platypus.Table` and styling it with
`TableStyle` (`BACKGROUND`, `GRID`, `ROWBACKGROUNDS`, `FONTNAME`, etc.) to
produce a report that reads as an actual formatted table rather than
manually space-aligned text drawn with `canvas.drawString`.

Note on scope: the sandbox available to the agent under test only provides
`reportlab` for PDF *creation* (no `qpdf` binary and no `pdfplumber` package
are installed — see the sandbox inventory). The qpdf and pdfplumber portions
of this cluster are therefore not exercisable in this environment, so the
benchmark narrows to the one sub-capability of the cluster that the sandbox
can actually exercise: reportlab's `Table`/`TableStyle` API for professional
report generation.

This matters for the skill because an agent that has internalized the
reportlab reference material knows to reach for `Table` + `TableStyle` (grid
lines, header shading, banded rows) when building a data report. An agent
that has not will typically fall back to manually positioned `drawString`
calls, which can *look* tabular if eyeballed quickly but lack real cell
borders/shading and are brittle to reproduce with correct alignment and
styling.

## Task given to the model

The model is given `/workspace/sales_data.json` (quarterly sales figures for
four products) and asked to produce `/workspace/quarterly_report.pdf`
containing:

- The report title,
- A data table (product rows × quarter columns) with a "Total" column per
  row,
- A totals row with per-quarter column sums and a grand total,
- A header row that is visually distinct (different background fill) from
  the data rows,
- Visible grid lines around every cell,
- Real, extractable text (not a rasterized/scanned table).

The prompt never mentions reportlab, `Table`, `TableStyle`, or any specific
API — it only specifies the required content and visual properties of the
output PDF.

## How grading works

`grader/grade.sh` invokes `grader/check.py`, which runs against
`/workspace` after the agent finishes:

1. **Deterministic content checks** (fail fast, exit 1 on any failure):
   - `/workspace/quarterly_report.pdf` exists and opens as a valid PDF via
     `pypdf` with at least one page.
   - `pdftotext -layout` extracts non-empty text from the PDF (rules out an
     image-only/scanned table).
   - The report title, every product name, every row total, every per-quarter
     column total, and the grand total (all computed independently from
     `sales_data.json` by the grader, not hard-coded) appear in the extracted
     text.

2. **Visual checks via LLM judge** (only reached if all deterministic checks
   pass): the grader renders page 1 to a PNG with `pdftoppm` and asks two
   strict yes/no questions — whether the header row has a background fill
   clearly distinguishable from the data rows, and whether every table cell
   has a visible grid/border line. Both answers must be affirmative or the
   run fails.

   This two-question judge round trip follows the harness protocol: first
   invocation writes `.judge/questions.json` and exits 3; after the harness
   supplies `.judge/answers.json`, a second invocation reads the answers and
   emits the final exit code.

Local testing confirmed:
- An untouched workspace (fixture only, no output PDF) fails at step 1.
- The reference solution passes all deterministic checks and (with
  simulated affirmative judge answers) passes overall.
- A naive `canvas.drawString`-based report with all the same numeric content
  but no header shading or grid lines passes the deterministic content
  checks but is rejected at the visual judge stage — demonstrating the
  benchmark actually discriminates on the target capability, not just
  content presence.

## How the reference solution satisfies it

`reference_solution/quarterly_report.pdf` was built with
`reportlab.platypus.SimpleDocTemplate`, `Table`, and `TableStyle`, using:
- `BACKGROUND` on the header row (dark fill) and totals row (light fill),
- `TEXTCOLOR`/`FONTNAME` to bold and recolor the header text,
- `ROWBACKGROUNDS` to band the data rows,
- `GRID` to draw borders around every cell,

directly mirroring the "Create Professional Reports with Tables" pattern
from the reportlab advanced reference.
