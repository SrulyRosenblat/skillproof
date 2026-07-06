# bench_03_process-brainstorm-explore-plan-critique

## Capability under test

The `frontend-design` skill prescribes a specific two-pass workflow before any
code is written: brainstorm a compact token plan (color, type, layout,
signature), then critically review that plan against the brief and revise
anything that reads as a generic, could-be-any-project default, *before*
building. This benchmark tests whether an agent actually performs that
process (produces a real first draft, genuinely revises at least one part of
it with a brief-specific reason, and then builds from the revised plan) as
opposed to skipping straight to a build, or going through the motions of a
"critique" step without any real reconsideration.

This matters because the skill's central failure mode it's guarding against
is exactly this: an agent that never pauses to ask "is this the generic
choice I'd make for any similar brief?" reliably lands on one of a small set
of AI-design defaults. The brainstorm → critique → revise → build loop is
the mechanism the skill relies on to catch that before the page is built.

## Task given to the model

The model reads `/workspace/brief.md`, a design brief for a one-page site for
"Aria," a manual lever espresso machine. The brief deliberately pins down the
product's content and material vocabulary (brass, walnut, steam, hand-pulled
pressure) but leaves color, type, and layout unspecified. The model must
produce:

- `design/initial-plan.md` — a first-draft token plan (4-6 named colors, 2-3
  type roles, a layout concept with an ASCII wireframe, and a named signature
  element).
- `design/critique.md` — a verdict (`KEEP`/`REVISE`) with a reason for each of
  the four axes, with **at least one `REVISE`**.
- `design/final-plan.md` — the plan actually built from, matching
  `initial-plan.md` on `KEEP` axes and differing on `REVISE` axes.
- `index.html` + `styles.css` — a build that implements `final-plan.md`
  exactly (same palette, same fonts, the signature element tagged with
  `data-signature`), incorporates specific facts from the brief, and meets a
  basic responsive/accessibility floor.

The task prompt states the required file formats and structure (so the
benchmark isn't just testing whether the model can guess an arbitrary
schema), but never tells the model what a "generic AI default" looks like or
why a two-pass process matters — that judgment is exactly what's scored.

## How grading works

`grader/grade.sh` runs `grader/check.py`, entirely against files in
`/workspace` (no transcript/process inspection):

1. **Structural parsing** — each of `initial-plan.md` / `final-plan.md` is
   parsed for its four sections (regex-based: hex codes, font-role lines, a
   fenced ASCII wireframe, a signature slug). `critique.md` is parsed for its
   four `KEEP`/`REVISE` verdict lines, each requiring a reason of non-trivial
   length. Missing/malformed sections fail immediately.
2. **Cross-file consistency** — for every axis, the grader diffs
   `initial-plan.md` against `final-plan.md`: axes marked `KEEP` must be
   byte-identical on that axis's content (color set, font names, wireframe
   text, or slug); axes marked `REVISE` must differ. This is checked with
   plain set/tuple/string comparison, not string-matching the model's prose.
3. **Build verification** — `index.html`/`styles.css` are parsed with
   BeautifulSoup/regex and *executed as data*, not grepped for API calls:
   the element carrying `data-signature` must match `final-plan.md`'s slug,
   the CSS's literal hex codes must cover most of `final-plan.md`'s palette,
   the CSS must reference the plan's actual font names, the visible text
   (via `get_text()`) must contain specific brief facts (product name, "9
   bar", "walnut") and must not contain lorem-ipsum/placeholder/TODO text,
   and the CSS must include a `@media` breakpoint and a `:focus` rule.
4. **LLM judge (2 questions, text-only, no rendering needed since there's no
   browser in the sandbox)** — once every deterministic check passes, the
   grader writes `.judge/questions.json` and exits 3:
   - Q1: do the stated `REVISE` reasons describe a change motivated by this
     specific product, rather than an arbitrary or unrelated tweak?
   - Q2: does the built page's visible copy read as specific to this
     product rather than generic, interchangeable marketing filler?
   On the re-run, `.judge/answers.json` is read and the grader exits 0 only
   if both are `true`.

Any deterministic failure exits non-zero immediately, before any judge
question is asked.

## How the reference solution satisfies it

`reference_solution/design/initial-plan.md` deliberately drafts the
"warm-neutral-plus-terracotta, high-contrast serif" combination as a
first-instinct palette and a decorative pressure-gauge illustration as a
first-instinct signature. `critique.md` marks `Color` and `Signature` as
`REVISE` (identifying the palette as generic and the gauge as merely
decorative rather than experiential), and marks `Type` and `Layout` as `KEEP`
with brief-specific reasons for why they already fit. `final-plan.md` carries
a materials-derived palette (bronze-black, brass, steam white, gauge red,
walnut) and a signature slug of `lever-pull` — an interactive lever the
visitor can hover/focus to pull, tying the one memorable element to the
product's actual mechanism. `index.html`/`styles.css` implement that revised
plan exactly, use the brief's concrete facts in the copy, and include a
`@media` breakpoint and `:focus-visible` outline.

## Validation

- Running the grader against `files/` alone (no agent output) fails on the
  first missing-file check.
- Running it against `files/` + `reference_solution/` passes all
  deterministic checks and would pass the judge stage given honest answers
  (verified locally by stubbing `.judge/answers.json`).
- Spot-checked failure modes: an all-`KEEP` critique (no revision) fails the
  "at least one REVISE" check; a `final-plan.md` that claims `REVISE` but is
  byte-identical to `initial-plan.md` fails the cross-file consistency check;
  missing a required brief fact, placeholder text, or a `:focus` rule each
  fail their respective build checks.
