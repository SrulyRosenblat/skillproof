# bench_01_forms-md-fillable-fields-step-1-try-stru

## Capability under test

The `pdf` skill's `FORMS.md` guide instructs that when a PDF form has **no
fillable/interactive fields**, the agent must first try **structure extraction**
(pulling exact text-label coordinates out of the PDF itself) to compute entry-field
positions, and only fall back to rougher visual/pixel estimation if the PDF has no
usable embedded text. The guide is explicit that naive approaches — assuming a
uniform grid of rows, or guessing coordinates without checking the actual label
positions — will misplace text, especially when rows are unevenly spaced or when
two fields share one row.

This benchmark tests exactly that capability: can the agent, without being told the
mechanism, realize it needs the PDF's real text-layout geometry (rather than
assuming a regular grid) to correctly place four values onto a flattened form?

## The task

`files/application_form.pdf` is a one-page, non-fillable (flattened) form generated
with `reportlab`, containing four real fields:

- `Full Name:` — alone on its row
- `Employee ID:` and `Department:` — sharing one row (two fields, side by side)
- `Start Date:` — alone on its row

...plus one **distractor** label, `Manager Name:`, that has no corresponding value
and must be left blank. Row-to-row vertical spacing is deliberately irregular
(70pt, 50pt, 60pt gaps) so an agent that assumes evenly-spaced rows will misplace
at least one field.

`files/values.json` gives the exact value string for each of the four real fields.

The agent must produce:
1. `filled_form.pdf` — the form with each value written next to its correct label.
2. `fields.json` — a self-reported list of the bounding box (in PDF point,
   top-left-origin coordinates) where each value was actually placed.

An agent that has internalized the skill's guidance will extract the PDF's text
geometry (e.g. via `pdftotext -bbox`, or by walking character positions with
`pypdf`) to find each label's precise coordinates, notice that `Employee ID:` and
`Department:` share a row, and compute a `Department:`-column start x that stays
clear of the `Employee ID:` entry — rather than assuming fixed offsets or an even
grid, which breaks on this fixture's irregular spacing and shared row.

## Why this matters for the `pdf` skill

Filling non-fillable/flattened forms is a named, explicit workflow in `FORMS.md`
("Non-fillable fields"), and picking structure extraction over blind visual
guessing (or a hardcoded grid) as the *first* attempt is precisely the discipline
the guide calls out ("Step 1: Try Structure Extraction First" / Approach A). Any
agent that skips this and guesses coordinates will visibly fail on real-world forms
whose layout isn't a perfect uniform grid — which is the norm, not the exception.

## Grading

`grader/grade.sh` runs `grader/grade.py`, which is fully deterministic and
executes/inspects only the artifacts the agent produced in `/workspace`:

1. Checks `filled_form.pdf` and `fields.json` exist, and that `values.json` was left
   untouched.
2. Validates `fields.json`'s schema (correct field keys, in-range/non-inverted
   bounding boxes, matching values, correct page number).
3. Runs `pdftotext -bbox` on the agent's `filled_form.pdf` to get exact rendered
   word coordinates (this is the same class of tool the skill's own structure
   extraction relies on) — this is an **executed, property-based check**, not a
   source-code grep.
4. Filters out the form's original label/title words (whose exact coordinates are
   known from how the fixture was generated) to isolate the value text the agent
   added.
5. For each of the four fields, confirms the rendered value text:
   - falls within that label's row band (catches row misassignment caused by
     assuming uniform spacing),
   - starts clearly to the right of its own label (catches guessed/fixed x-offsets
     that don't account for variable label width),
   - for `Employee ID:`, stays clear of the neighboring `Department:` label/column
     on the same row (catches the shared-row collision case),
   - does not overlap any label or title word's bounding box,
   - stays on the page.
6. Confirms nothing was written on the blank distractor `Manager Name:` row.
7. Cross-checks that each `fields.json` entry's declared bounding box actually
   contains the corresponding rendered text (catches self-reported boxes that don't
   match reality).

The grader was verified locally to **fail** on an untouched workspace (missing
outputs) and to **pass** on `reference_solution/`. It was also stress-tested
against several plausible incorrect solutions (a naive fixed-grid/fixed-x
placement, a content-swap between the two same-row fields, and a `fields.json`
whose declared box doesn't match the rendered text) — all were correctly rejected
— and against an alternate, differently-fonted but genuinely correct placement,
which was correctly accepted.

## Reference solution

`reference_solution/` contains a `filled_form.pdf` and `fields.json` produced by a
script that mirrors the skill's intended workflow: it runs `pdftotext -bbox` on the
input PDF, groups adjacent words into labels, detects same-row neighbors to bound
each entry column, computes entry bounding boxes and baselines from that real
geometry, overlays the values with `reportlab`, and merges the overlay onto the
original page with `pypdf`.
