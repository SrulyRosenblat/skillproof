---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    The page's plain extracted text never carries per-item coordinates, so
    determining which of the 24 scattered four-digit tags fall inside a given
    rectangular region cannot be done by dumping, concatenating, or
    regex-scanning the page text -- every naive text-extraction path throws
    away exactly the information the task needs. It is also not enough to
    pull each tag's nearest text-positioning operand out of the raw content
    stream: the tags are rendered under an active graphics-state transform
    (a non-identity current transformation matrix), so a positioning
    operand must be composed with that transform to get the tag's actual
    on-page origin -- reading the operand in isolation silently yields a
    different, wrong set of coordinates (and a wrong but plausible-looking
    sum). Solving it requires resolving each tag's fully-transformed
    placement position on the page (e.g. via a coordinate-aware extraction
    library that resolves the complete text-rendering matrix, or by
    correctly composing the transform by hand) and testing that position
    against the region bounds. A model that knows to resolve and use each
    item's fully-resolved page coordinates reproduces the exact sum and set
    deterministically; a model that extracts text ordinarily, or reads a
    positioning operator's raw operand without composing the active
    transform, has no principled way to pick the right five of 24
    candidates (plus a decoy) and fails the exact-match checks.
  category: office-white-collar
  subcategory: pdf-editing
  category_confidence: medium
  task_type:
    - extraction
    - calculation
  modality:
    - document
  interface:
    - terminal
  skill_type:
    - domain-procedure
    - file-format-knowledge
  tags:
    - pdf
    - coordinates
    - text-extraction
    - bounding-box
verifier:
  type: test-script
  timeout_sec: 300.0
agent:
  timeout_sec: 900.0
environment:
  network_mode: no-network
  build_timeout_sec: 300.0
  os: linux
  cpus: 2
  memory_mb: 2048
  storage_mb: 2048
  gpus: 0
---

`/workspace/tags.pdf` is a single-page PDF ("Inventory Tag Scan -- Zone
Map") produced by an automated scanner. Scattered across the page are a
number of four-digit numeric tag codes, each printed as its own standalone
piece of text at a specific position. The page also contains a line of
ordinary sentence text that happens to mention a four-digit reference number
("Report Reference: 4413...") -- that number is part of a sentence, not a
scanned tag, and must not be treated as one.

The page uses the PDF's standard coordinate system: the origin `(0, 0)` is
the bottom-left corner of the page, `x` increases to the right, `y`
increases upward, and both are measured in points (1/72 inch) -- the same
system the page's own `MediaBox` is defined in. The page is US Letter size,
612 x 792 points. For any given tag, its "position" means where that tag's
text is actually placed on the page in this coordinate system once
everything affecting its placement is accounted for -- the fully resolved
origin of its first character, not the raw operand of whichever single
positioning instruction happens to sit nearest that character in the page's
internal content stream. Some of the tags on this page are emitted under an
active coordinate transformation (affecting scale as well as offset), so a
positioning instruction's operand by itself is not the on-page position
unless that transformation has also been applied.

A rectangular region of the page is defined by:

- `x` from 200 to 420 (inclusive)
- `y` from 420 to 620 (inclusive)

Your job:

1. Determine which scanned tag codes have a position that falls inside that
   region.
2. Write each matching code, one per line (any order), to
   `/workspace/matched_codes.txt`.
3. Write the sum of exactly those matching codes, as a single bare integer
   with no other text, to `/workspace/answer.txt`.

Do not include the "Report Reference" number, and do not include any tag
whose position falls outside the region.
