import json
import re
from pypdf import PdfReader, PdfWriter

SOURCE_FILES = ["invoice_1.pdf", "invoice_2.pdf", "invoice_3.pdf"]

writer = PdfWriter()
summary = []

for name in SOURCE_FILES:
    reader = PdfReader(name)
    page = reader.pages[0]

    if page.rotation % 360 != 0:
        page.rotate(-page.rotation)

    writer.add_page(page)

    text = page.extract_text()
    invoice_number = re.search(r"Invoice Number:\s*(\S+)", text).group(1)
    total_str = re.search(r"Total Due:\s*\$([0-9,.]+)", text).group(1)
    total_due = float(total_str.replace(",", ""))
    author = reader.metadata.author

    summary.append(
        {
            "source_file": name,
            "invoice_number": invoice_number,
            "total_due": total_due,
            "author": author,
        }
    )

with open("combined_invoices.pdf", "wb") as f:
    writer.write(f)

with open("invoice_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
