---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: medium
  difficulty_explanation: >-
    The output schema and per-field geometry rules (which coordinate-system
    naming convention to use for the page metadata, the label-to-entry gap,
    how the entry box's right edge is bounded by the next label vs. the row
    margin, when to fall back to a default row height, and treating a
    checkbox's entry box as its own rectangle) follow a specific, non-obvious
    convention used by this document-forms pipeline. A model unfamiliar with
    that convention will produce plausible-looking but numerically wrong
    boxes and fail the exact-value checks; a model that knows the convention
    reproduces the same numbers deterministically from the given input.
  category: office-white-collar
  subcategory: pdf-editing
  category_confidence: medium
  task_type:
    - transformation
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
    - forms
    - coordinates
    - json
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

`/workspace/form_structure.json` is the layout extracted from page 1 of a
scanned/flat PDF intake form. The PDF has no interactive (fillable) form
fields — it was already checked, and none exist — so a later step needs a
field map computed from this layout, not looked up from AcroForm fields.

The structure groups each row's field labels under `rows` (each label has a
`field_label` and a `bounding_box` given as `[x0, top, x1, bottom]` in PDF
point units, top-down), and separately lists each `checkboxes` entry with its
own `label_bounding_box` and `checkbox_bounding_box`. Rows also carry a
`row_bottom_boundary` (a ruled line under that row, or `null` if the row has
none), and the document gives a `row_right_boundary` (the row's right-hand
margin) and a `default_row_height` fallback. Read the file directly for the
exact values.

Produce `/workspace/fields.json` with this top-level shape:

```json
{
  "pages": [
    {"page_number": 1, "<page-width-key>": ..., "<page-height-key>": ...}
  ],
  "form_fields": [
    {
      "page_number": 1,
      "field_label": "...",
      "description": "...",
      "label_bounding_box": [x0, top, x1, bottom],
      "entry_bounding_box": [x0, top, x1, bottom]
    }
  ]
}
```

One `form_fields` entry per label in `rows` and per entry in `checkboxes`
(5 total for this form). For each:

- `label_bounding_box` carries over that field's own label box unchanged.
- `entry_bounding_box` is the box where the corresponding answer should be
  written: for a row label, the empty region belonging to that field (to the
  right of its label, within its row, not overlapping the label, the next
  field's label, or the row's own boundaries); for a checkbox, the box a mark
  would be placed in for that checkbox.
- `description` is a short, non-empty description of the field.

For the page entry, record its width and height using this pipeline's
established key-naming convention that signals these are raw PDF-point
coordinates taken directly from the form's vector layout — as opposed to the
different convention used when coordinates instead come from pixel
measurements on a rendered/rasterized page image. Use the values from
`form_structure.json`.
