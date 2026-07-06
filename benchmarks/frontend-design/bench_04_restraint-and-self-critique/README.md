# bench_04_restraint-and-self-critique

## Capability under test

The `frontend-design` skill's "Restraint and self-critique" guidance says that a
designer should spend boldness in exactly one place, cut any decoration that
doesn't serve the brief, and hit a quality floor (mobile-responsive, visible
keyboard focus, reduced-motion respected) without announcing it — the same
instinct behind "look in the mirror and remove one accessory" before shipping.

Rather than testing this in the abstract, this benchmark hands the model a
concrete, deliberately over-decorated draft page and asks it to cut it down.
This directly exercises the judgment call the skill describes: given several
candidate "bold" ideas that are all currently present, identify which one (if
any) earns the one moment of boldness, remove the rest entirely rather than
softening them, and fix the accessibility/responsiveness bugs the draft's
decoration was hiding — while writing up the decision.

## Files

- `files/draft.html` — the input fixture: a self-contained homepage draft for
  "Warble Press," a fictional independent vinyl-record pressing plant. It
  deliberately packs in five competing decorative effects (a bouncing logo, a
  glowing/pulsing CTA button, a scrolling ticker, falling confetti, and an
  animated rainbow background), plus three concrete bugs: no viewport meta tag
  and a hardcoded `width: 1200px` layout (breaks on mobile), a blanket
  `*:focus { outline: none; }` (invisible keyboard focus), and four infinite
  CSS animations with no `prefers-reduced-motion` handling anywhere. Real
  facts about the business (name, founding year, capacity, turnaround,
  minimum order) are embedded in the copy alongside the decoration.
- `task_prompt.md` — the task given to the model under test, framed as client
  feedback asking for the draft to be calmed down to one signature moment
  while still working for everyone (phone, keyboard, motion-sensitive users).
- `reference_solution/index.html` and `reference_solution/CHANGES.md` — a
  solution that removes four of the five original effects, replaces the
  glowing CTA with a new single signature moment (a small hand-cut lacquer
  groove animation tied to the business's own craft), and fixes all three
  planted bugs.
- `grader/grade.py` (invoked by `grader/grade.sh`) — the grading logic.

## How grading works

`grader/grade.sh` runs `grader/grade.py` against `/workspace`. It's a two-pass
grader (deterministic checks, then an LLM-judge pass):

**Pass 1 — deterministic checks (exit non-zero on any failure):**
1. `index.html` and `CHANGES.md` both exist, and `draft.html` is still present.
2. `index.html`'s visible text still states the real facts from the draft:
   "Warble Press", the founding year (2016), daily capacity (500), turnaround
   (6-week/6 week), and minimum order size (100).
3. Exactly one element carries `data-signature="true"`, and it has its own
   `id` attribute.
4. Of the draft's five original decorative classes (`bounce-logo`,
   `glow-pulse-cta`, `ticker-marquee`, `confetti-burst`, `rainbow-bg`), at
   most one is still present anywhere in `index.html`.
5. The draft's specific `width: 1200px` fixed-layout bug is gone, and at
   least one `@media` rule with a `max-width` of 768px or less exists.
6. The draft's blanket `*:focus { outline: none; }` rule is gone, and some
   `:focus`/`:focus-visible` rule sets a real (non-`none`/`0`) outline,
   box-shadow, or border as a visible replacement.
7. If any looping CSS animation remains, a
   `@media (prefers-reduced-motion: reduce)` block exists that actually
   references `animation`/`transition` to neutralize it.
8. `CHANGES.md` is substantive (60+ words, no filler/placeholder text),
   names the signature element's `id`, names at least 3 of the 5 original
   effects it removed or kept, and describes at least 2 of the
   mobile/keyboard-focus/motion fixes.

**Pass 2 — LLM judge (only reached if pass 1 succeeds):** two strict yes/no
questions evaluated on the produced files (never on source code style or a
transcript):
- Reading the full HTML/CSS source, does the page read as having exactly one
  bold/attention-grabbing moment with everything else genuinely calm and
  restrained (not still cluttered, and not so plain there's no standout
  moment at all)?
- Does `CHANGES.md` give specific reasoning tied to this particular draft and
  business, rather than generic boilerplate ("we simplified the design and
  improved accessibility")?

Both passes must succeed for the grader to exit 0.

## Why the reference solution passes

`reference_solution/index.html` removes the bouncing logo, ticker, confetti,
and rainbow background outright, and replaces the glowing CTA button with a
new signature element (`#lathe-groove`, marked `data-signature="true"`) — a
small animated graphic of the concentric grooves the shop actually cuts by
hand, which is both the page's one saturated color accent and its one moving
element. It adds the viewport meta tag and a `max-width: 600px` breakpoint,
replaces the blanket outline removal with a `:focus-visible` ring, and wraps
the remaining animation in a `prefers-reduced-motion: reduce` query.
`reference_solution/CHANGES.md` explains, in business-specific terms, what was
cut, what was kept and why, and how each of the three planted bugs was fixed —
satisfying both the substance checks and the judge questions.

## Local verification

Verified locally with a Python virtualenv containing `beautifulsoup4` and
`lxml` (the same versions available in the grading sandbox):
- The grader fails on `files/` alone (`index.html`/`CHANGES.md` missing).
- The grader fails on a solution that copies `draft.html` to `index.html`
  unmodified (missing viewport tag, among other things).
- The grader fails on a solution that fixes the three accessibility bugs but
  keeps all five original decorative effects (the decoration-removal check).
- The grader passes on `files/` + `reference_solution/` through both passes
  once judge answers are simulated as `true`.
