# Task: cut down the Warble Press homepage draft

`/workspace/draft.html` is the current draft of the homepage for Warble Press, an
independent vinyl record pressing plant. It's a real, self-contained HTML page (open
it to see it fully — inline CSS, no external requests).

The client's reaction to this draft:

> "Every part of this page is trying to grab us at once — the logo won't stop
> bouncing, the button is glowing, there's a scrolling ticker, confetti falling in
> the middle of the page, and the whole background is cycling through colors. It's
> exhausting to look at. We also tried it on a phone and had to scroll sideways to
> read anything, and when our accessibility consultant tabbed through it with a
> keyboard she couldn't tell what was focused. Someone on our team also gets
> motion-sick from looping animations like that ticker. We don't want a blander
> page — we still want ONE moment that makes people stop and look — but everything
> else needs to calm down, and it needs to actually work for everyone who visits."

Your job is to revise the draft into a page that satisfies this feedback, using the
real facts already present in the draft (company name, founding year and city,
daily press capacity, turnaround time, minimum order size). Do not invent
contradicting facts, and do not strip the real content out along with the
decoration.

## Deliverables

Create exactly these two files in `/workspace` (leave `draft.html` in place,
unmodified, for reference):

### 1. `/workspace/index.html`

The revised page. A single self-contained HTML document (inline `<style>`/
`<script>` only, no external requests or fonts). It must satisfy all of the
following:

- **Keep the facts.** The visible page text must still include: the company name
  "Warble Press", the founding year (2016), the daily press capacity (500), the
  turnaround time (6-week / 6 week), and the minimum order size (100).
- **Exactly one bold moment.** Mark exactly one element on the page — the single
  thing this page gets to be memorable for — with the attribute
  `data-signature="true"`. That element must also carry its own unique `id`
  attribute. No other element may carry `data-signature="true"`.
- **Actually remove the rest, don't just soften it.** The draft currently has five
  separate attention-grabbing effects: the bouncing logo, the glowing/pulsing
  button, the scrolling ticker, the falling confetti, and the animated rainbow
  background. At most one of these five may still be present in your revision (it
  may be the one you kept as the signature, reworked, or you may replace it with a
  new idea of your own) — the other four (at least) must be gone entirely, not
  merely toned down or slowed.
- **Works on a phone.** No horizontal scrolling or cut-off content at a 375px-wide
  viewport. Include the usual mobile viewport meta tag and at least one responsive
  breakpoint in your CSS.
- **Visible keyboard focus.** Every interactive element (links, buttons) must show
  a clearly visible focus indicator when reached by keyboard. Don't just suppress
  the browser's default outline — replace it with your own visible one.
- **Respects motion sensitivity.** If your revision keeps or adds any looping or
  auto-playing CSS animation, wrap the motion-sensitive behavior in a
  `prefers-reduced-motion: reduce` media query that turns it off or holds it still
  for people who've asked for reduced motion.

### 2. `/workspace/CHANGES.md`

A short changelog, written for the client (not the design team), explaining your
revision. It must cover, specifically enough that it clearly refers to this draft
(not generic boilerplate):

- Which of the five original effects you removed, and which one (if any) you kept
  or replaced as the page's one signature moment, and why that one is the right
  one to keep.
- What you did to fix the phone layout, the keyboard focus visibility, and the
  motion-sensitivity problem the client described.

Do not create any other files in `/workspace`.
