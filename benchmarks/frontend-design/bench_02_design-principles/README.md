# bench_02_design-principles

## Capability under test

The `frontend-design` skill's "Design principles" guidance says three things
that this benchmark targets together:

1. The hero should open with the most characteristic thing in the subject's
   world, not the template answer (a big number + small label + gradient
   accent), unless that's truly the best option for the brief.
2. Typography should be paired deliberately for the specific brief, not the
   same generic families reached for on any project.
3. Structural devices like numbered markers are only appropriate when the
   content is actually a sequence. Many generic designs number things (01 /
   02 / 03) by reflex; a designer who has internalized this principle
   questions that choice and, when the content has no real order, labels
   items by something that is actually true of them instead.

This benchmark gives the model a brief for a small hot sauce brand (Ember &
Ash) with three sauces, and the fixture is explicit that the three sauces are
**not** a ranked set, tasting flight, or sequence - customers buy exactly one,
based on how much heat they want. This is the natural setup where an AI
default (numbering three cards 01/02/03, or "Step 1/2/3") is actively wrong
per the skill's own guidance, while a model that has internalized "structure
is information" will label each card by something true of it (its heat
level) instead. The brief also gives the model room to write a generic
"Bold Flavor, Small Batch" hero versus a hero actually built from the brand's
own material (the shipping-container origin story), and to reach for a
generic single-font-family page versus a deliberately paired display/body
typeface choice.

## Files

- `files/brand-brief.json` - the input fixture: brand story and three sauces
  (name, heat_label, scoville, base ingredients, tasting notes), plus a
  `sales_note` field stating explicitly that the sauces are sold
  individually and not as a ranked set. Copied into `/workspace` before the
  agent runs.
- `task_prompt.md` - the task given to the model under test.
- `reference_solution/index.html` and `reference_solution/design-notes.md` -
  a solution that opens the hero with the shipping-container story, pairs an
  industrial display face (Anton) with a warm humanist serif (Lora), and
  labels each product card by heat level (Mild / Medium / Fierce) rather
  than position.
- `grader/grade.py` (invoked by `grader/grade.sh`) - the grading logic.

## How grading works

`grader/grade.sh` runs `grader/grade.py` against `/workspace`. It is a
two-pass grader (deterministic checks, then an LLM-judge pass):

**Pass 1 - deterministic checks (exit non-zero on any failure):**
1. `design-notes.md` and `index.html` both exist, and the fixture
   `brand-brief.json` is still present.
2. `design-notes.md`'s first three non-empty lines match the required
   `Hero: ...` / `Typography: ...` / `Structure: ...` format, each with at
   least 6 words.
3. `index.html` parses as HTML with a non-empty `<title>`, no banned
   placeholder text, and an element with `id="hero"` containing exactly one
   `<h1>` whose text includes the brand's name.
4. Exactly three elements with `class="flavor-card"` exist, each naming
   exactly one sauce from the fixture (a 1:1 match across all three sauces),
   stating that sauce's `heat_label` and `scoville` rating in its visible
   text, and containing its tasting notes inside a `<p>`.
5. **No sequence/step markers**: none of the three flavor-cards contain a
   standalone piece of text (its own element, e.g. `<span>01</span>`) that
   is a bare ordinal/sequence marker - digits 1-3 or 01-03, roman numerals
   I-III, "first/second/third", "1st/2nd/3rd", "Step 1/one", "Part 1/one",
   "No. 1", "Number 1". This is checked because the fixture explicitly
   states the three sauces have no real order.
6. **Typography pairing**: the CSS must set a `font-family` for `h1` and a
   separate one for `p`, the two values must differ, and neither one's
   first listed font may be a bare generic CSS keyword (`serif`,
   `sans-serif`, `monospace`, `system-ui`, etc. used alone).

**Pass 2 - LLM judge (only reached if pass 1 succeeds):** three strict
yes/no questions, evaluated on the actual extracted text/HTML from the
produced files (never on source code or process transcripts):
- Is the hero section's text specific and evocative of this particular
  brand, rather than a generic tagline that could describe almost any food
  brand?
- Do the (non-numeric) labels on the three product cards communicate real,
  differentiating information about each sauce, rather than being
  decorative or interchangeable?
- Does the `Typography` rationale in `design-notes.md` explain a font
  pairing chosen for a reason specific to this brand, rather than reciting
  generic pairing best-practice?

All checks in both passes must pass for the grader to exit 0.

## Why the reference solution passes

`reference_solution/index.html`'s hero headline is built entirely from the
brand's own material ("Ember & Ash bottles its heat by hand, forty at a
time, in a shipping container behind a Portland warehouse") rather than a
generic tagline, satisfying the hero-specificity judge question. Its CSS
pairs Anton (an industrial, stencil-adjacent display face) for headings with
Lora (a warm humanist serif) for body copy - two distinct, deliberately
chosen fonts, neither a bare generic keyword. Each `flavor-card` is tagged
with its heat level (Mild / Medium / Fierce) instead of a position number,
which passes both the deterministic sequence-marker check and the judge's
question about whether the labels carry real information.
`reference_solution/design-notes.md` states the reasoning behind all three
choices in brand-specific terms, which is what the typography-rationale
judge question checks for.

## Local verification

Verified locally with a Python virtualenv containing `beautifulsoup4` and
`lxml` (the same versions available in the grading sandbox):
- The grader fails on `files/` alone (missing `design-notes.md` /
  `index.html`).
- The grader passes on `files/` + `reference_solution/` once judge answers
  are simulated as all `true`.
- A hand-written "generic AI default" solution (numbered `01`/`02`/`03`
  spans on each card, `Arial`/`sans-serif` for both headings and body, a
  "Bold Flavor, Small Batch" hero) was confirmed to fail the deterministic
  sequence-marker check and the font-distinctness check before ever
  reaching the judge, exercising the exact failure modes this benchmark
  targets.
