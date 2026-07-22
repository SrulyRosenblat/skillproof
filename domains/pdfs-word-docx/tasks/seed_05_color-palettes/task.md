---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: medium
  difficulty_explanation: >-
    The mechanics of building a two-slide python-pptx deck are trivial; the
    entire difficulty is in recalling two specific, non-derivable color
    palettes exactly. Slide 1 requires Anthropic's own real official brand
    colors (a light background hex, a dark text hex, and three accent hexes
    in a specific primary/secondary/tertiary order) rather than a plausible
    guess at "Anthropic orange" or generic dark/light tones. Slide 2 requires
    the exact primary/secondary/accent hex triplet for a named presentation
    design palette called "Coral Energy," whose hex values are arbitrary and
    unrecoverable from the name alone. A model without access to either
    source of truth will produce a deck that looks reasonable but fails
    every color assertion; a model that knows both palettes reproduces the
    exact hex values.
  category: office-white-collar
  subcategory: pptx-formatting
  category_confidence: medium
  task_type:
    - generation
    - formatting
  modality:
    - document
  interface:
    - terminal
  skill_type:
    - domain-procedure
    - file-format-knowledge
  tags:
    - pptx
    - color-palettes
    - branding
    - python-pptx
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

Build a two-slide PowerPoint deck for a partnership pitch and save it as
`/workspace/deck.pptx` (there is no existing file — create it from scratch).

**Slide 1 — "About Anthropic"**

- The title text must read exactly `About Anthropic`.
- Fill the slide background with Anthropic's own official light background
  color, taken from Anthropic's real brand style guide, and set the title
  text's font color to Anthropic's own official dark text color from that
  same guide.
- Add exactly three additional rectangle shapes, arranged left to right, and
  give each one a shape name (the shape's `name` property, not its visible
  label): `AccentOne`, `AccentTwo`, `AccentThree`. Fill each rectangle with
  one of Anthropic's three official accent colors from the same brand guide:
  `AccentOne` gets the primary accent, `AccentTwo` gets the secondary accent,
  `AccentThree` gets the tertiary accent.

**Slide 2 — "Our Partnership Vision"**

- The title text must read exactly `Our Partnership Vision`.
- Style this slide using the "Coral Energy" color palette — one of a set of
  named color palettes used for choosing an on-brand, non-default color
  scheme for a presentation. Fill the slide background with that palette's
  primary color. Set the title text's font color to the palette's accent
  color. Add one more rectangle shape, named `SecondaryBlock`, filled with
  the palette's secondary color.

Both slides may include any other supporting text or shapes you think fit a
partnership pitch, but the exact titles, the exact shape names above, and
all specified colors are mandatory. Apply every required color as a literal
RGB fill or font color (not a theme reference or placeholder default) so
that a tool can read back the exact color values directly from the file.
