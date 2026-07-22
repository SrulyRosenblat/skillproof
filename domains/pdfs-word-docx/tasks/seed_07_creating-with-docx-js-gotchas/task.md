---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: medium
  difficulty_explanation: >-
    Every requirement in the prompt lines up with a place where the docx
    library's own default silently produces a plausible-looking but wrong
    result: page size defaults to A4 instead of the requested US Letter
    dimensions; a table cell width alone does not set the table's own column
    grid, which is what a viewer actually renders from; shading needs the
    "clear" pattern type or a fill color renders as solid black; a "bulleted
    list" built by typing a bullet character into each paragraph is not real
    Word list numbering; and an embedded image saved without declaring its
    type gets no recognized file extension. None of these are visible from
    the task inputs or discoverable by trial and error without opening the
    produced .docx's internal XML, so a model that knows the library's
    footguns reproduces a conformant document while one that doesn't
    produces something that looks right at a glance but fails on inspection.
  category: office-white-collar
  subcategory: docx-creation
  category_confidence: high
  task_type:
    - generation
  modality:
    - document
  interface:
    - terminal
  skill_type:
    - domain-procedure
    - file-format-knowledge
  tags:
    - docx
    - docx-js
    - ooxml
    - word
    - node
verifier:
  type: test-script
  timeout_sec: 300.0
agent:
  timeout_sec: 1200.0
environment:
  network_mode: no-network
  build_timeout_sec: 300.0
  os: linux
  cpus: 2
  memory_mb: 2048
  storage_mb: 2048
  gpus: 0
---

`/workspace/data.json` holds the content for a quarterly business report, and
`/workspace/logo.png` is the company logo. Using the `docx` Node.js library
(already installed — `require('docx')` works from `/workspace`), generate
`/workspace/output.docx` as a single-section report with the following exact
requirements:

1. **Page size:** US Letter, 8.5in x 11in (not the library's default).
2. **Default document font:** Arial, applied as the actual document-wide
   default so it covers any text that doesn't explicitly request another
   font.
3. **Title:** a heading containing `report_title` from the data, built as a
   genuine top-level Word heading (so a table-of-contents or the Word
   navigation pane would recognize it as level 1), rendered in black text.
4. **Metrics table:** three columns, "Metric", "Value", "Notes", in that
   order, at exact widths of 2in, 1.5in, and 3in. One row per entry in
   `metrics`, in order, with each entry's `metric`, `value`, and `notes`
   fields in the matching column. The header row's background must be
   light gray (`#D9D9D9`) — and must actually render as light gray, not
   solid black.
5. **Takeaways:** each string in `takeaways` as one item of a genuine Word
   bulleted list (the kind Word itself would let you re-order or convert to
   numbers) — not paragraphs with a bullet character typed at the start.
   Item text must be exactly the takeaway string, with no added prefix.
6. **Logo:** embed `logo.png`, exactly 1.5in wide with height scaled to
   preserve its aspect ratio, with alt text set to title `Acme Corp Logo`,
   description `Acme Corp company logo`, and name `AcmeLogo`.

The resulting file must be a valid `.docx` package that standard docx
tooling can open and parse cleanly.
