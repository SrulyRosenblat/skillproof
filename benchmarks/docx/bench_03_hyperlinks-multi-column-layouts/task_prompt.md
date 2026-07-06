Read `/workspace/files/briefing_outline.md` and create `/workspace/riverside_brief.docx`.

Requirements:

1. Create a valid `.docx` document at exactly `/workspace/riverside_brief.docx`.
2. Use US Letter portrait page size with 1-inch margins throughout the document.
3. Use the text from `/workspace/files/briefing_outline.md` exactly, preserving the same non-empty line order and wording.
4. Format `Riverside Expansion Brief` as a built-in `Heading1` paragraph.
5. Format the section titles `Overview`, `Milestones`, `Risks`, and `Appendix Resources` as built-in `Heading2` paragraphs.
6. Keep the subtitle and all remaining content as normal body paragraphs.
7. The title, subtitle, and opening summary paragraph must appear in a single-column first section.
8. After that summary paragraph, start a new section for the body that is configured as exactly two equal-width columns with a 0.5 inch gap and a vertical separator line between the columns.
9. At the top of the two-column body section, add one navigation paragraph whose visible text is exactly `Program portal | Jump to Risks`.
10. In that navigation paragraph, `Program portal` must be a real external Word hyperlink targeting `https://example.com/program-portal`, not plain styled text.
11. In that navigation paragraph, `Jump to Risks` must be a real internal Word hyperlink that targets a bookmark named `risks`, not plain styled text.
12. Attach the bookmark named `risks` to the `Risks` heading paragraph.
13. Force `Appendix Resources` to start at the top of the next column by inserting a section break whose start type is `nextColumn` immediately before that heading.

Only `/workspace/riverside_brief.docx` is required as output.
