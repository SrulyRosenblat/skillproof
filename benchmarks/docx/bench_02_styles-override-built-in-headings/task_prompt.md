Update the Word document at `/workspace/files/source_handbook.docx` and write the result to `/workspace/restyled_handbook.docx`.

Requirements:

1. Keep the document text, paragraph order, and which paragraphs are headings exactly the same as in the source file.
2. Do not directly format individual heading paragraphs or heading runs. Make the change by editing the document's built-in heading style definitions so every paragraph using those styles updates document-wide.
3. Paragraphs that are already top-level headings must still use the built-in style ID `Heading1`.
4. Paragraphs that are already second-level headings must still use the built-in style ID `Heading2`.
5. Set the default document run font to Arial 12pt.
6. Override the built-in `Heading1` style so it has:
   - name `Heading 1`
   - `basedOn` = `Normal`
   - `next` = `Normal`
   - Arial, 16pt, bold, black
   - paragraph spacing 12pt before and 12pt after
   - outline level 0
7. Override the built-in `Heading2` style so it has:
   - name `Heading 2`
   - `basedOn` = `Normal`
   - `next` = `Normal`
   - Arial, 14pt, bold, black
   - paragraph spacing 9pt before and 9pt after
   - outline level 1

Only `/workspace/restyled_handbook.docx` is required as output.
