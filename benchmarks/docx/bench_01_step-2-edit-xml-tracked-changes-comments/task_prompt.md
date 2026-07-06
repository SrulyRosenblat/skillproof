# Task

You are given an unpacked DOCX package in `/workspace/unpacked/` plus a helper packer at `/workspace/scripts/pack_docx.py`.

Edit the OOXML in place and then create `/workspace/final.docx` as a zip archive of the updated `/workspace/unpacked/` directory.

## Files you must edit

- `/workspace/unpacked/word/document.xml`
- `/workspace/unpacked/word/comments.xml`

Do not remove the existing comments relationship in `/workspace/unpacked/word/_rels/document.xml.rels` or the comments content-type override in `/workspace/unpacked/[Content_Types].xml`.

## Required document changes

1. In the first paragraph of `document.xml`, change the bold red text `15 days notice` into a tracked replacement so the accepted text reads `30 days’ written notice`.
   - Use a top-level `<w:del>` for `15 days notice` and a top-level `<w:ins>` for `30 days’ written notice`.
   - The `<w:del>` and `<w:ins>` elements must be siblings of `<w:r>` elements in the paragraph, not nested inside a run.
   - Copy the original `<w:rPr>` formatting into both tracked-change runs so the replacement stays bold and red.
   - Use `w:author="Claude"` and `w:date="2025-01-01T00:00:00Z"` on both tracked-change elements.
   - In the XML source, encode the apostrophe in `days’` as `&#x2019;`.

2. Add two comments anchored to the inserted phrase `30 days’ written notice`.
   - Comment `0` text: `Confirm that “30 days’ written notice” matches the negotiated draft.`
   - Comment `1` text: `Confirmed. Counsel’s June 12 redline uses the same wording.`
   - Use comment ids `0` and `1`.
   - Treat comment `1` as a reply anchored on the same inserted phrase by nesting the comment ranges in this order around the insertion: start `0`, start `1`, end `1`, end `0`.
   - Place `<w:commentRangeStart>` and `<w:commentRangeEnd>` as direct children of the paragraph, never inside a run.
   - Add matching `<w:commentReference>` runs for ids `0` and `1` after the sentence punctuation.
   - In `comments.xml`, use `w:author="Claude"` and `w:date="2025-01-01T00:00:00Z"` on both comments.
   - In the XML source, encode the smart punctuation with entities: `&#x201C;`, `&#x201D;`, and `&#x2019;`.

3. Convert the entire second paragraph, `Submit weekly status reports.`, into a tracked deletion that would disappear completely when changes are accepted.
   - Put the paragraph-mark deletion inside `w:pPr/w:rPr/w:del` with `w:author="Claude"` and `w:date="2025-01-01T00:00:00Z"`.
   - Wrap the deleted paragraph text in a paragraph-level `<w:del>` using `<w:delText>`, not `<w:t>`.
   - Do not leave any normal `<w:r>` text in that paragraph.

4. Leave the third paragraph text unchanged: `Payment is due within ten days of invoice receipt.`

## Required output

- `/workspace/final.docx`

`final.docx` must be a valid zip archive of the updated `/workspace/unpacked/` package and must contain at least:

- `[Content_Types].xml`
- `_rels/.rels`
- `word/document.xml`
- `word/comments.xml`
- `word/_rels/document.xml.rels`

You may use the provided helper:

```bash
python3 /workspace/scripts/pack_docx.py /workspace/unpacked /workspace/final.docx
```
