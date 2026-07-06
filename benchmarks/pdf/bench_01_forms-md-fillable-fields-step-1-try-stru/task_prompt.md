# Task: Fill in a non-fillable PDF form

`/workspace/application_form.pdf` is a one-page PDF form (page size 612x792 points).
It was produced by flattening a document to PDF, so it has **no interactive/fillable
form fields** (opening it in a form-filling tool will show nothing to click on) — it's
just printed labels and blank underlines. Some labels share the same line (there are
two fields side by side on one row), and the vertical spacing between rows is not
uniform, so you cannot assume a fixed grid.

`/workspace/values.json` maps each field's key to the exact text that must be entered
for that field:

```json
{
  "full_name": "...",
  "employee_id": "...",
  "department": "...",
  "start_date": "..."
}
```

Note: the form contains one extra printed label ("Manager Name") that has **no**
corresponding entry in `values.json`. Leave that line blank — do not write anything
on it.

## What you must produce in `/workspace`

1. **`filled_form.pdf`** — a copy of the form with each value from `values.json`
   written onto the correct blank line next to its matching label, so that a person
   reading the page can clearly see which value belongs to which label. Text must:
   - sit clearly to the right of its own label (not overlapping the label text),
   - stay within its own row (not drift into a different label's row),
   - not overlap or collide with any other field's text or label (this matters
     especially for the two fields that share one row).

2. **`fields.json`** — a JSON array with one object per field key from
   `values.json`, in this exact shape:

   ```json
   [
     {
       "field_key": "full_name",
       "page": 1,
       "entry_bounding_box": [x0, y0, x1, y1],
       "value": "Jordan Alvarez"
     }
   ]
   ```

   where `entry_bounding_box` is the bounding box, in PDF point coordinates, of
   where you placed that field's text on the page, using the convention that
   `(0, 0)` is the **top-left** corner of the page and y increases **downward**
   (so `x0,y0` is the top-left of the box and `x1,y1` is its bottom-right, with
   `0 <= y0 < y1 <= 792` and `0 <= x0 < x1 <= 612`). The box you report must
   actually contain the text you drew for that field in `filled_form.pdf`.

Do not modify `application_form.pdf` or `values.json`.
