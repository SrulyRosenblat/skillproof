# Task: Generate a Formatted Quarterly Sales Report PDF

A JSON file with quarterly sales figures is available at:

```
/workspace/sales_data.json
```

It has this structure:

```json
{
  "report_title": "Quarterly Sales Report",
  "quarters": ["Q1", "Q2", "Q3", "Q4"],
  "products": [
    {"name": "Widgets", "sales": [120, 135, 142, 158]},
    ...
  ]
}
```

## Your job

Write the data to a single PDF report at **`/workspace/quarterly_report.pdf`** that a
sales manager could hand to executives. The report must satisfy all of the
following requirements:

1. **Title**: The report title text (from `report_title` in the JSON) must appear
   near the top of the page.

2. **Data table**: A table containing one row per product, with columns for the
   product name followed by its value for each quarter (in the order given in
   `quarters`), followed by a "Total" column holding that product's sum across
   all quarters.

3. **Totals row**: An additional row (e.g. labeled "Total") at the bottom of the
   table showing the column-wise sum for each quarter across all products, plus
   the grand total (sum of every sales figure in the file) in the final column.

4. **All numbers must be numerically correct** — computed from the values in
   `sales_data.json`, not hard-coded or approximated.

5. **Table styling**: The table must be visually presented as an actual table,
   not just space-aligned text:
   - The header row (product/quarter/total labels) must have a background fill
     color that is visibly different from the background of the data rows, so
     it stands out as a header at a glance.
   - Every cell in the table must have a visible border/grid line separating it
     from its neighbors, so the row/column structure is visually obvious.

6. **Text must be real, extractable text** (not an image/scan of a table) so
   that the numbers and labels can be programmatically extracted from the PDF.

The output PDF must contain exactly this one report (a single page is
sufficient). Do not leave any other files required for review — only the
final `/workspace/quarterly_report.pdf` needs to be produced.
