# bench_01_frontend-design

## Capability under test

The `frontend-design` skill says that when a design brief doesn't pin down
what the product or subject actually is, the designer must pin it down
themselves before designing: name one concrete subject, its audience, and the
page's single job, and then build every part of the page from that subject's
real content and vernacular — not generic language that could apply to any
similar product.

This benchmark gives the model a client brief that is deliberately
underspecified: a founder asking for "a subscription landing page" with no
name, no product detail, no audience, and no brand. A model that has
internalized this part of the skill will recognize that it has to invent a
concrete, specific product and audience and then write every section of the
page around that specific invention. A model that has not internalized it
tends to produce a page that stays at the level of the brief: "a premium
subscription," "great value," "sign up today" — content that would be equally
true of any subscription business, plus placeholder-shaped copy.

## Files

- `files/brief.txt` — the input fixture: the intentionally bare-bones client
  brief, copied into `/workspace` before the agent runs.
- `task_prompt.md` — the task given to the model under test.
- `reference_solution/design-notes.md` and `reference_solution/index.html` —
  a solution that invents a specific product (a single-farm, single-origin
  Japanese green tea subscription), a specific audience, and a single stated
  job, then writes a full landing page whose every section is grounded in
  that invented specific.
- `grader/grade.py` (invoked by `grader/grade.sh`) — the grading logic.

## How grading works

`grader/grade.sh` runs `grader/grade.py` against `/workspace`. It is a
two-pass grader (deterministic checks, then an LLM-judge pass):

**Pass 1 — deterministic checks (exit non-zero on any failure):**
1. `design-notes.md` and `index.html` both exist.
2. The first three non-empty lines of `design-notes.md` match the required
   `Subject: ...` / `Audience: ...` / `Primary job: ...` format, each with at
   least 6 words.
3. The `Subject` field isn't just one of a list of generic placeholder stubs
   (e.g. literally "a subscription box").
4. `index.html` parses as HTML with a non-empty `<title>`, a viewport meta
   tag, and exactly one `<h1>`.
5. The visible body text is at least 300 words (rules out skeleton pages).
6. No banned placeholder text appears anywhere in `index.html` ("Lorem
   ipsum," "Company Name," "Product Name," "Insert text here," bracketed
   placeholders like `[your product]`, etc).
7. **Grounding check**: the `Subject` field's specific/concrete words (after
   stripping generic subscription vocabulary and stopwords) must actually
   show up in `index.html`'s visible body text — at least 3 distinct matches.
   This is a property-based proxy for "the page is actually about the stated
   subject," and is verified separately in the section below.

**Pass 2 — LLM judge (only reached if pass 1 succeeds):** three strict
yes/no questions, evaluated on the actual field text / body text extracted
from the produced files (never on source code or process transcripts):
- Does the `Subject` field name a genuinely specific product, not a generic
  category?
- Does the `Audience` field name a genuinely specific group, not a generic
  one?
- Does the page's body copy stay grounded in that specific subject
  throughout (not just in the headline)?

All three deterministic and judge checks must pass for the grader to exit 0.

## Why the reference solution passes

`reference_solution/design-notes.md` names a specific invented product (Kioku
Tea Society: one named farm in Uji, Kyoto, shipped monthly, with a
farmer-written brewing card), a specific audience (coffee-habituated adults
drifting toward slower rituals), and a single stated job (make the sourcing
feel real rather than generic). `reference_solution/index.html` is a full
page whose sections (what arrives, why this audience, why one farm, pricing,
CTA) all reuse that same concrete material — the farm name, the farmer's
name, the tea varietal, the specific price — so the grounding check finds
plenty of overlap and the judge questions read as genuinely specific rather
than generic.

## Local verification

Both directions were verified locally (see commit history / grading run
logs): the grader fails when `/workspace` contains only `files/` (missing
required outputs), and passes when `/workspace` also contains
`reference_solution/`'s files followed by simulated "yes" judge answers. It
was also spot-checked against generic/templated/placeholder-laden
alternative solutions to confirm those fail the deterministic checks before
ever reaching the judge.
