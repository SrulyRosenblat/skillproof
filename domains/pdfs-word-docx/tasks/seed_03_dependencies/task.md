---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    The obvious way to "screenshot" a Word document's pages is a single
    direct conversion command, but there is no direct docx-page-to-raster
    export available at all in this environment (no LibreOffice/Word to
    drive) -- so a faithful per-page render only exists by reconstructing
    each page's true layout from the docx's own paragraph and picture data
    (python-docx gives page size, text, and each embedded picture's real
    on-page size at its point in the flow, split on explicit page breaks),
    redrawing it onto a same-sized PDF page, and then rasterizing each PDF
    page individually with a tool that is available, picking the right page
    index each time. A model that doesn't know this is possible tends to
    either give up on a real render and fabricate a mockup from the
    extracted text/picture (which won't show the true page layout,
    proportions, or whitespace), or extract and re-save the embedded picture
    directly (which is the artwork, not the page it sits on), or convert
    only a single page and reuse it for all three outputs. Each of these
    plausible-looking shortcuts is caught deterministically: every page
    carries its own distinct embedded picture, so a genuine per-page render
    of page N shows a sizeable patch of that page's picture colour, none of
    the other pages' colours, a mostly-blank page background, and the page's
    true aspect ratio -- properties none of the shortcuts reproduce together.
  category: office-white-collar
  subcategory: docx-rendering
  category_confidence: medium
  task_type:
    - transformation
  modality:
    - document
  interface:
    - terminal
  skill_type:
    - domain-procedure
    - file-format-knowledge
  tags:
    - docx
    - rendering
    - thumbnail
    - pdf
    - reportlab
    - poppler
    - dependencies
verifier:
  type: test-script
  timeout_sec: 300.0
agent:
  timeout_sec: 900.0
environment:
  network_mode: no-network
  build_timeout_sec: 600.0
  os: linux
  cpus: 2
  memory_mb: 2048
  storage_mb: 3072
  gpus: 0
---

`/workspace/report.docx` is a short 3-page internal report. Each page has its
own text and one embedded picture.

Produce three PNG files in `/workspace`: `page1_thumbnail.png`,
`page2_thumbnail.png`, and `page3_thumbnail.png`, one per page in document
order. Each PNG must be a faithful full-page rendering of that specific
page, exactly as it would look if the document were opened or printed --
the whole page (text, picture, and surrounding white space) in its real
layout and proportions. A crop of just the embedded picture, a hand-built
mockup, or the same page's content reused across the three files does not
satisfy this.

Each image should be high enough resolution for the page's content to be
clearly legible (at least ~600px on its longer side) and should preserve
the page's true aspect ratio. No other files in `/workspace` need to
change.
