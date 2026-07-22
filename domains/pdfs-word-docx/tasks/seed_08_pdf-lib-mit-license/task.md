---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: medium
  difficulty_explanation: >-
    Every requirement lines up with a place where pdf-lib's own conventions
    diverge from a plausible-looking default: PDF page dimensions are
    expressed in points (1/72 inch), not millimeters, so ISO A4 is
    ~595x842pt rather than 210x297 -- and the source pages are themselves
    US Letter (612x792pt), so copying their size or guessing metric units
    both produce a page that fails the exact-size check. The page
    coordinate origin is the bottom-left corner with y increasing upward,
    so a title or header band meant to sit "near the top" needs a y close
    to the page height, not a small y near zero the way a screen/image
    coordinate system would suggest -- a model that assumes top-left-origin
    coordinates places everything near the bottom instead. drawText()
    requires an actual embedded bold font object (via embedFont), not a
    plain font plus a "bold" style flag, to render as bold. And merging
    "only the 1st, 3rd, and 5th pages" of a second document requires
    copying specific page indices rather than the whole document -- the
    default, obvious instinct when merging two PDFs is to concatenate all
    of both, which silently produces the wrong page count and content.
    None of this is discoverable by trial and error without opening the
    produced PDF's actual page boxes, content stream, and text positions;
    a model that knows pdf-lib's specific conventions reproduces a
    conformant report, while one that doesn't produces a file that opens
    fine but fails the geometry and selection checks. The cover page also
    composes two "near the top" facts rather than one in isolation: the
    header band sits near the top and the subtitle sits below that band,
    in the plain (uncolored) page background. Getting the absolute
    position of each element right independently is not sufficient --
    a model has to carry the y-up coordinate convention through a
    band-then-subtitle layout and keep the subtitle's baseline below the
    band's lower edge, or the subtitle ends up printed on top of the
    colored band instead of below it. Two further requirements target
    defaults that look reasonable but are wrong: a plausible "card" layout
    insets the header band with side margins, but the task requires an
    edge-to-edge band flush with both page edges, so a model that reaches
    for a comfortable margin (a near-universal instinct when laying out a
    rectangle) fails the width check even though the band is still the
    right color, height, and vertical position; and drawing the title text
    on the page is not the same as setting the PDF's own Title metadata
    (pdf-lib's `setTitle`) -- a model that only calls `drawText` never
    touches document metadata at all, so the produced file opens and reads
    fine but reports no title (or a default empty one) to `pdfinfo` and PDF
    viewers' window chrome.
  category: office-white-collar
  subcategory: pdf-creation
  category_confidence: high
  task_type:
    - generation
    - transformation
  modality:
    - document
  interface:
    - terminal
  skill_type:
    - domain-procedure
    - file-format-knowledge
  tags:
    - pdf
    - pdf-lib
    - node
    - merge
    - coordinates
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

`/workspace/section_a.pdf` (4 pages) and `/workspace/section_b.pdf` (6 pages)
are on disk. Each page contains a plain text label identifying its section
and page number.

Using the `pdf-lib` Node.js library (already installed --
`require('pdf-lib')` works from `/workspace`), generate
`/workspace/report.pdf` with the following exact structure, in this order:

1. **Cover page (new, first page):** a page sized to standard ISO A4 paper
   dimensions.

   - A title reading exactly `Q1 Regional Summary`, rendered in a bold font,
     placed near the top of the page.
   - A filled rectangular header band, in the exact hex color `#D6E4F0`,
     that spans the full width of the page edge-to-edge (touching both the
     left and right page edges, with no side margins) and sits in the upper
     half of the page, behind or near the title.
   - Below the header band, in the page's plain (non-highlighted)
     background -- not overlapping the colored band -- a subtitle reading
     exactly `Prepared for the Executive Committee`, rendered in a regular
     (non-bold) font.
   - The PDF document's own Title metadata (the property standard PDF
     tooling such as `pdfinfo` reports, distinct from the on-page heading
     text) must also be set to exactly `Q1 Regional Summary`.

2. **All pages of `section_a.pdf`**, unchanged, in their original order.

3. **Only the 1st, 3rd, and 5th pages of `section_b.pdf`**, in that order --
   skip the 2nd, 4th, and 6th pages entirely.

The resulting `report.pdf` must therefore have 8 pages total, and must be a
valid PDF that standard PDF tooling can open and parse cleanly.
