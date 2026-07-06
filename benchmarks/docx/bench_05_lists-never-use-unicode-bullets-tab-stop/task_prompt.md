Repair `/workspace/files/source_brief.docx` and write the result to `/workspace/repaired_brief.docx`.

Requirements:

1. Keep the paragraph order exactly the same as in the source document.
2. Keep the same wording for every heading, label, and list item, but remove the fake marker text described below.
3. The two paragraphs whose source text contains ` || ` must be rewritten so the separator becomes a real tab character between the left and right text, and each paragraph must define a real right-aligned tab stop.
4. The two paragraphs whose source text begins with `• ` must become real Word bullet-list paragraphs. Remove the typed bullet character from the text runs. Each of those paragraphs must carry real Word list numbering metadata.
5. The three paragraphs under `Launch Checklist` that begin with `1. `, `2. `, and `3. ` must become one continuous real Word decimal-numbered list. Remove the typed numbers from the text runs. Each of those paragraphs must carry real Word list numbering metadata.
6. The two paragraphs under `Escalation Steps` that begin with `1. ` and `2. ` must become a separate real Word decimal-numbered list that restarts at `1`, not a continuation of the `Launch Checklist` list. Remove the typed numbers from the text runs. Each of those paragraphs must carry real Word list numbering metadata.
7. The two paragraphs whose source text contains ` >> ` must be rewritten so only the label text and page number text remain, separated by a real dot-leader positional tab.
8. Do not use tables anywhere in the output document.
9. The result must be a valid `.docx` file at `/workspace/repaired_brief.docx`.

Only `/workspace/repaired_brief.docx` is required as output.
