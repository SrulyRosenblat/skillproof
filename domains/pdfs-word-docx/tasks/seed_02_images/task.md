---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    The required end state needs three separate, non-obvious OOXML package
    conventions applied correctly and simultaneously: an embedded picture must
    have a registered media file, relationship, and content-type entry, and be
    sized in EMUs computed from the source image's real pixel dimensions; a
    formatted paragraph's `<w:pPr>` children must appear in a fixed schema
    order or Word will silently reorder/repair the file; and a Word comment
    requires its own package part, relationship, and content-type plus
    in-body range markers that must be direct siblings of the run they
    anchor, never nested inside it. None of this is discoverable from the
    task inputs themselves, no bundled tool performs it automatically (the
    available docx library has no comment-authoring support at all), and the
    most intuitive way to structure the comment markers (nesting them inside
    the run, mirroring how the visual selection looks) is the wrong one and
    is deterministically caught by the checks. A model that knows the actual
    package conventions reproduces them correctly; one that doesn't produces
    a plausible-looking but non-conformant file.
  category: office-white-collar
  subcategory: docx-editing
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
    - ooxml
    - images
    - comments
    - word
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

`/workspace/report.docx` is a short internal report. `/workspace/figure.png`
is a revenue chart the finance team wants included in it. Update
`/workspace/report.docx` in place so that:

1. `figure.png` is embedded in the report as a picture exactly 3 inches wide,
   with its height scaled to preserve the image's own aspect ratio (don't
   distort it, and don't just embed it at some default size).
2. Immediately after the image, add a new paragraph containing exactly this
   caption text: `Figure 1: Quarterly Revenue Chart`. The caption paragraph
   must be centered and have 12 points of spacing above it.
3. Add a real Word comment anchored precisely to the phrase "quarterly
   results" exactly as it appears in the report's existing body text (not the
   whole sentence or paragraph it sits in). The comment's author must be
   `Finance Review` and its text must read exactly: `Please confirm these
   figures against the Q3 ledger before publishing.`

The report's existing text must otherwise be unchanged, and the file must
remain a `.docx` that standard docx tooling (and Word) can open cleanly, with
the comment recognizable and anchored as a genuine review comment rather than
as ordinary inline text.
