# Task: design and build the Aria launch page, with a documented design process

Read `/workspace/brief.md` — it's the design brief for a one-page product site.
No colors, fonts, or layout are pinned down in the brief; those choices are
yours to make.

You must produce a **documented two-pass design process** (an initial plan, a
self-critique of that plan, and a final plan) before the build, plus the build
itself. Create exactly these files in `/workspace`:

## 1. `design/initial-plan.md`

Your first-draft design plan, with exactly these four sections (use these
exact `##` headings):

- `## Color` — a bulleted list of **4 to 6** named colors, one per line, in
  the form `- <Name> — #<6-digit hex> — <what it's used for>`.
- `## Type` — a bulleted list of **2 or 3** type roles, one per line, in the
  form `- <Role>: <Font name> — <what it's used for>`, where `<Role>` is one
  of `Display`, `Body`, or `Utility`. You must include at least `Display` and
  `Body`.
- `## Layout` — one to three sentences of prose describing the page structure,
  followed by an ASCII wireframe in a fenced code block (at least 4 lines,
  using characters like `+ - | /` to sketch boxes).
- `## Signature` — a line `Slug: <kebab-case-slug>` naming the one element
  this page should be remembered by, followed by 1-3 sentences describing it.

## 2. `design/critique.md`

A self-critique of the initial plan. It must contain exactly one line for
each of the four axes, in this exact form:

```
- Color: KEEP — <one-sentence reason>
- Type: KEEP — <one-sentence reason>
- Layout: KEEP — <one-sentence reason>
- Signature: KEEP — <one-sentence reason>
```

(using `REVISE` instead of `KEEP` on any axis you decide to change). **At
least one axis must be marked `REVISE`.** Each reason must be specific to
this brief and to what that axis actually contains — not a generic remark
that could apply to any page. If an axis is `REVISE`, the reason must say
what you're changing it to and why the original didn't fit this brief well
enough.

## 3. `design/final-plan.md`

The plan you'll actually build from, in the same format as
`initial-plan.md`. Axes marked `KEEP` in the critique must carry the exact
same values here as in `initial-plan.md` (same hex codes, same font names,
same wireframe, same slug). Axes marked `REVISE` must differ from
`initial-plan.md` (different hex set, different font, different wireframe,
or different slug, as applicable to what you revised).

## 4. `index.html` and `styles.css`

The built page, implementing `design/final-plan.md` exactly:

- A real page: `<html>`, `<head>` with a `viewport` meta tag, `<body>`, at
  least one heading, and `styles.css` linked as a stylesheet.
- The element that embodies your signature idea must carry
  `data-signature="<slug>"`, using the exact slug from `final-plan.md`.
- `styles.css` must use the actual hex colors from `final-plan.md`'s palette
  (not a different palette) and set `font-family` using the actual font
  names from `final-plan.md`'s Type section.
- The page copy must incorporate specific facts from the brief (at minimum:
  the product name, the peak pressure figure, and the handle material) —
  write real copy, not placeholder or lorem-ipsum text.
- The page must be usable on a mobile-width screen (include at least one
  `@media` breakpoint) and must show a visible focus state for keyboard
  navigation (a `:focus` rule) on any interactive element (link/button/form
  field).
- A way to join the waiting list (a form or a `mailto:` link is enough; no
  backend is required).

Do not create any other files in `/workspace` besides the five listed above
(plus `brief.md`, which already exists).
