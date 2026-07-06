# Task: Combine invoice PDFs into a single billing packet

Acme's billing team has three single-page invoice PDFs sitting in `/workspace`:

- `invoice_1.pdf`
- `invoice_2.pdf`
- `invoice_3.pdf`

They need these combined into one packet for archiving, plus a small JSON summary
for their bookkeeping system.

## Requirements

1. **Combine the pages** from all three PDFs, in the order `invoice_1.pdf`,
   `invoice_2.pdf`, `invoice_3.pdf`, into a single new PDF file named
   `combined_invoices.pdf` in `/workspace`. It must contain exactly one page per
   source file (3 pages total), in that order.

2. **Fix the orientation of `invoice_3.pdf`.** That file was produced by a
   different scanner and currently displays upside down. In the final
   `combined_invoices.pdf`, the page that came from `invoice_3.pdf` must display
   right-side up, the same way the other two pages do. The other two pages are
   already correctly oriented and should be left as-is.

3. **Write a summary file** named `invoice_summary.json` in `/workspace`
   containing a JSON array with exactly one object per source invoice, **in the
   same order as the pages in `combined_invoices.pdf`**. Each object must have
   exactly these keys:
   - `"source_file"`: the original filename, e.g. `"invoice_1.pdf"`
   - `"invoice_number"`: the invoice number printed on that invoice, as a string
     (e.g. `"INV-1001"`)
   - `"total_due"`: the total amount due printed on that invoice, as a JSON
     number (e.g. `245.00`), with no currency symbol or thousands separators
   - `"author"`: the value of the PDF document's Author metadata field for that
     source file

## Notes

- Each invoice's visible text includes a line like `Invoice Number: INV-1001`
  and a line like `Total Due: $245.00`.
- Only `combined_invoices.pdf` and `invoice_summary.json` will be checked; you
  may leave any intermediate scripts in `/workspace` if you like.
