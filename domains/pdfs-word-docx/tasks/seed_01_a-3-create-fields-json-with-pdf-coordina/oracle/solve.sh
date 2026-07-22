#!/bin/bash
# Computes fields.json from /workspace/form_structure.json.
set -euo pipefail

python3 - <<'PY'
import json

with open("/workspace/form_structure.json") as f:
    data = json.load(f)

page_number = data["page_number"]
pdf_width = data["pdf_width"]
pdf_height = data["pdf_height"]
row_right_boundary = data["row_right_boundary"]
default_row_height = data["default_row_height"]

LABEL_TO_ENTRY_GAP = 5

form_fields = []

for row in data["rows"]:
    labels = row["labels"]
    row_bottom_boundary = row.get("row_bottom_boundary")
    for i, label in enumerate(labels):
        x0, top, x1, bottom = label["bounding_box"]

        entry_x0 = x1 + LABEL_TO_ENTRY_GAP
        if i + 1 < len(labels):
            entry_x1 = labels[i + 1]["bounding_box"][0]
        else:
            entry_x1 = row_right_boundary

        entry_top = top
        if row_bottom_boundary is not None:
            entry_bottom = row_bottom_boundary
        else:
            entry_bottom = bottom + default_row_height

        form_fields.append({
            "page_number": page_number,
            "field_label": label["field_label"],
            "description": f"Entry field for {label['field_label']}",
            "label_bounding_box": [x0, top, x1, bottom],
            "entry_bounding_box": [entry_x0, entry_top, entry_x1, entry_bottom],
        })

for checkbox in data["checkboxes"]:
    form_fields.append({
        "page_number": page_number,
        "field_label": checkbox["field_label"],
        "description": f"Checkbox for {checkbox['field_label']}",
        "label_bounding_box": checkbox["label_bounding_box"],
        "entry_bounding_box": checkbox["checkbox_bounding_box"],
    })

output = {
    "pages": [
        {"page_number": page_number, "pdf_width": pdf_width, "pdf_height": pdf_height}
    ],
    "form_fields": form_fields,
}

with open("/workspace/fields.json", "w") as f:
    json.dump(output, f, indent=2)

print("wrote /workspace/fields.json")
PY
