---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: medium
  difficulty_explanation: >-
    The workspace's guidelines/ folder holds four different guides for
    different kinds of internal write-ups, and nothing in the request names
    which one to use -- the agent has to actually open and compare them
    against the request to find the one that fits (matching on each guide's
    own description, not a filename hint), then reproduce that guide's exact
    section labels, their order, and its required closing sentence verbatim;
    guessing at generic-sounding headings ("Status Update", "This Week") or
    paraphrasing the closing line fails an exact-text check. Independently,
    the theme file defines a font/color/size/weight quadruple for headings
    and a different one for body text, and all four must be applied
    explicitly and identically to every heading and every body paragraph in
    the finished .docx. python-docx's default heading style already renders
    bold with its own color, font, and size, so a solution that calls
    add_heading/add_paragraph and only sets each run's font name, RGB color,
    and point size -- reasoning that the heading "already looks bold enough"
    -- produces a plausible-looking document that still fails the exact
    style checks, because an unset `run.font.bold` reads back as `None`,
    not `True`/`False`, on every run regardless of which way the theme's
    weight actually points. A solution that copies the font/color/size logic
    but never notices the theme also pins a `font_bold` per section (there's
    no weight mentioned in the task prompt itself, and the two theme files
    disagree on which section is bold, so guessing "headings are bold, body
    isn't" is wrong exactly half the time) will pass the color/font/size
    checks while silently failing on weight.
  category: office-white-collar
  subcategory: docx-formatting
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
    - docx
    - python-docx
    - word
    - styling
    - internal-comms
    - formatting-guide
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

This week's team status update needs to go out as a Word document.

The raw notes for the update are in `/workspace/notes.txt` -- they cover what
shipped, what's coming up next, and what's currently blocking the team.

The document should be styled to match the "harbor-blue" visual identity,
defined in `/workspace/themes/harbor-blue.yaml`. There's a second theme file
in that same folder for a different kind of document -- make sure the one you
apply is harbor-blue, and apply its styling to the entire document, not just
part of it.

`/workspace/guidelines/` holds a handful of formatting guides for different
kinds of internal write-ups. Exactly one of them is meant for this kind of
recurring team update -- read them, find the one whose own description
matches this situation, and follow its structure and instructions precisely.
The others are for different kinds of communications and don't apply here.

Save the finished document to `/workspace/output/update.docx`.
