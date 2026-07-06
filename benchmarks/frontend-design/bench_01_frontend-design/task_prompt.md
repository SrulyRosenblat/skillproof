# Task: Build a subscription landing page from a bare-bones client brief

Read `/workspace/brief.txt`. It's the entire client intake for this job — a
founder asking for a landing page for a subscription product, without having
locked in what the product actually is, who it's for, or a brand name.

Your job is to take that brief and turn it into a real, shippable landing
page. Nothing about the specific subscription is decided yet, so before you
design anything, you need to decide it yourself: invent a specific, concrete
subscription product (what physical or digital thing arrives, how often, what
makes it distinct), a specific audience for it, and the one job this page has
to do for a visitor. Then build the page so every section is actually about
that product — not a generic "subscription service" that could be swapped for
any other subscription with a find-and-replace.

## Deliverables

Create exactly two files directly in `/workspace`:

### 1. `/workspace/design-notes.md`

A short rationale note, written so a non-designer on the client's team could
read it. The first three lines of the file must be exactly in this form (one
sentence each, replacing the bracketed part):

```
Subject: [the specific subscription product you invented, in one sentence]
Audience: [the specific group of people this page is written for, in one sentence]
Primary job: [the single thing this page needs to accomplish for a visitor, in one sentence]
```

Additional explanation below those three lines is optional.

### 2. `/workspace/index.html`

A single, self-contained, complete HTML document (valid `<html>`, `<head>`
with a `<title>` and a viewport meta tag, and `<body>`) that is the actual
landing page for the product you defined in `design-notes.md`. Requirements:

- Styling can be inline `<style>` in the `<head>` or inline `style` attributes
  — no external files or network requests.
- The page needs a clear headline (a single `<h1>`) and enough real body copy
  (at least a few hundred words total across the page) to read like a
  finished product page, not a wireframe or skeleton.
- Every section's copy should be written specifically for the product named
  in your `design-notes.md` — its actual name, what arrives, who it's for,
  and why someone would want it — rather than generic language that could
  describe any subscription box.
- Do not use placeholder content anywhere (no "Lorem ipsum", no "Company
  Name", no "Product Name", no "Insert text here", no bracketed placeholders
  like "[your product]").

Do not create any other files. Do not ask clarifying questions — the brief is
intentionally incomplete and filling the gap yourself is the task.
