---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: medium-high
  difficulty_explanation: >-
    The obvious instinct for "get images out of a PDF" in this offline
    sandbox is poppler's embedded-picture extractor, since that's the
    PDF-to-images tool most readily recalled from general knowledge -- and
    this particular input.pdf reinforces that instinct fatally: it is built
    entirely from vector fills and text, with zero embedded raster picture
    assets, so an extractor runs without error but silently produces zero
    output files. Producing one image per page instead requires rendering
    each page's actual visual appearance (its shapes, fills, and text as
    they would look on screen), which in this network-less environment
    (no pdf2image/PyMuPDF pip packages reachable) is only achievable via
    poppler's page-rasterization tools, a different tool from its
    asset-extraction one. A model that conflates "convert a PDF to images"
    with "extract the images embedded in a PDF" reaches for the wrong tool
    and produces zero (or the wrong) files.

    Clearing that first trap is not enough on its own: every page's
    MediaBox (the full underlying sheet) is deliberately larger than its
    CropBox (the actual visible page area the colored rectangle lives in),
    the way a page pulled from a bigger artboard or an imposed sheet with
    trim/bleed margin would be. Poppler's rasterization tools render the
    MediaBox by default and need an explicit flag to honor the CropBox
    instead, so a model that rasterizes each page without accounting for
    that distinction gets the wrong aspect ratio and a colored block
    diluted by a large blank margin -- passing the page-count check but
    failing the dimension and color checks. Only a model that knows a
    PDF page's nominal sheet size and its actual visible/printable area
    can differ, and renders the latter, deterministically passes every
    check.
  category: office-white-collar
  subcategory: pdf-conversion
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
    - pdf
    - images
    - rasterization
    - page-rendering
    - poppler-utils
    - cropbox-vs-mediabox
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

`/workspace/input.pdf` is a small multi-page PDF. Render it into a sequence
of standalone raster image files, one per page, and save them into
`/workspace/page_images/` (create the directory if it doesn't exist).

Requirements:

- Produce exactly one image file per page of the PDF, and no other files in
  that directory.
- Each image must be a faithful rendering of everything visible on that
  page (its shapes, fills, and text as the page would actually look on
  screen or in print) — not just whatever picture assets happen to be
  embedded inside the PDF's internal file structure.
- Save the images in a common raster format (e.g. PNG or JPEG) at a
  resolution high enough to clearly show the page content (at least a few
  hundred pixels on each side).
- Name the files so that sorting them alphabetically reproduces the pages'
  original order (page 1 first, then page 2, and so on).
