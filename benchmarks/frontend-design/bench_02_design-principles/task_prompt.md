# Task: Build a product page for Ember & Ash

Read `/workspace/brand-brief.json`. It contains everything currently known about
Ember & Ash, a small hot sauce maker, and its three current sauces.

Build a single product page for the brand using this content.

## Deliverables

Create exactly two files directly in `/workspace`. Do not create any other files,
and do not ask clarifying questions.

### 1. `/workspace/index.html`

A single, self-contained HTML document (inline `<style>`/`<script>` only, no
external requests or fonts) with a `<head>` containing a non-empty `<title>`.
Requirements:

- A hero area: a container element with `id="hero"` that contains exactly one
  `<h1>`. The `<h1>` text must include the brand's name.
- Exactly three product cards, one per sauce listed in `brand-brief.json`, each
  as an element with `class="flavor-card"`. Each card must:
  - name the sauce (its `name` field)
  - state its `heat_label` somewhere in the card's visible text
  - state its `scoville` rating somewhere in the card's visible text
  - include its `notes` copy (or a close paraphrase of it) inside a `<p>`
    element
- CSS (inline `<style>` in the `<head>`) that sets a `font-family` for `h1`
  elements and a separate `font-family` for `p` elements. The two values must
  differ from each other, and each one's first listed font must be an actual
  font name, not just a bare generic keyword like `serif`, `sans-serif`,
  `monospace`, or `system-ui` used on its own.
- No placeholder text anywhere (no "Lorem ipsum", no bracketed placeholders
  like "[your text here]", no "Product Name").

### 2. `/workspace/design-notes.md`

A short rationale, written so a non-designer on the client's team could read
it. The first three non-empty lines of the file must be exactly in this form
(one sentence each, replacing the bracketed part):

```
Hero: [what you chose as the hero content, and why it's the right opening for this brand]
Typography: [the two typefaces you chose, one for headings and one for body copy, and why they fit this brand]
Structure: [how you decided to label and organize the three sauces on the page, and why]
```

Additional explanation below those three lines is optional.
