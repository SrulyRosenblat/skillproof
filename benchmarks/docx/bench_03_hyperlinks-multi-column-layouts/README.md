# Hyperlinks and Multi-Column Layouts

This benchmark tests whether an agent can create a new `.docx` that uses real Word hyperlink structures together with multi-section column layout controls. That matters for the `docx` skill because this cluster is about features that are easy to fake visually but require the correct OOXML or document-construction primitives to behave properly in Word.

The task gives the agent `/workspace/files/briefing_outline.md` and asks it to produce `/workspace/riverside_brief.docx`. A correct solution must preserve the outline text exactly, map the required lines to built-in heading styles, add a real external hyperlink and a real internal bookmark-based hyperlink, place the document body in a two-column section with the required spacing and separator line, and force the appendix heading to begin at the top of the next column with a `nextColumn` section break.

## Grading

`grader/grade.sh` runs a deterministic Python checker over `/workspace/riverside_brief.docx`.

It verifies:

- the output file exists
- the visible non-empty paragraph sequence exactly matches the required outline plus the required navigation paragraph
- `Riverside Expansion Brief` uses built-in `Heading1`
- `Overview`, `Milestones`, `Risks`, and `Appendix Resources` use built-in `Heading2`
- the first section ends after the opening summary and remains single-column
- the document uses US Letter portrait geometry with 1-inch margins
- the final section uses exactly two equal-width columns with a 0.5 inch gap and a vertical separator line
- the navigation paragraph contains exactly two real Word hyperlinks
- `Program portal` is an external hyperlink targeting `https://example.com/program-portal`
- `Jump to Risks` is an internal hyperlink targeting a bookmark named `risks`
- the `Risks` heading paragraph contains the `risks` bookmark
- the paragraph immediately before `Appendix Resources` carries a section break whose start type is `nextColumn`, while keeping the required two-column settings

Because the grader checks hyperlink relationships, bookmark anchors, and section XML, a solution that only makes text look blue or manually spaces content into two visual columns will fail.

## Reference Solution

The reference solution is [reference_solution/riverside_brief.docx](/Users/srulyrosenblat/Developer/skill_auto_benchmark/benchmarks/docx/bench_03_hyperlinks-multi-column-layouts/reference_solution/riverside_brief.docx). It preserves the exact outline text, uses built-in heading styles for the required headings, inserts a relationship-backed external hyperlink and a bookmark-backed internal hyperlink in the navigation line, attaches the `risks` bookmark to the `Risks` heading, and defines the single-column intro section, two-column body section, and `nextColumn` appendix transition in the document OOXML.
