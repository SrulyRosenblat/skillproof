# Styles Override Built-in Headings

This benchmark tests whether an agent can repair a `.docx` by overriding the built-in `Heading1` and `Heading2` style definitions instead of faking the result with direct paragraph formatting. That matters for the `docx` skill because document-wide heading control, TOC compatibility, and outline behavior depend on the built-in style IDs and their style metadata, not just on visible text formatting.

The task gives the agent `/workspace/files/source_handbook.docx`, whose heading paragraphs already point at the built-in heading style IDs but whose style definitions are wrong. The agent must produce `/workspace/restyled_handbook.docx` with unchanged content and unchanged heading assignments while fixing the document default run font and the `Heading1` and `Heading2` style definitions.

## Grading

`grader/grade.sh` runs a deterministic Python check over `/workspace/restyled_handbook.docx`.

It verifies:

- the output file exists
- the paragraph text and paragraph style assignments exactly match the source document
- heading paragraphs still rely only on their `pStyle` assignments, with no direct paragraph or run formatting added
- the default document run font is Arial 12pt
- the built-in `Heading1` style definition has the required name, base style, next style, Arial 16pt bold black run properties, 12pt before/after spacing, and outline level 0
- the built-in `Heading2` style definition has the required name, base style, next style, Arial 14pt bold black run properties, 9pt before/after spacing, and outline level 1

Because the grader checks style definitions and not just appearance, a solution that directly formats the visible headings fails.

## Reference Solution

The reference solution is [reference_solution/restyled_handbook.docx](/Users/srulyrosenblat/Developer/skill_auto_benchmark/benchmarks/docx/bench_02_styles-override-built-in-headings/reference_solution/restyled_handbook.docx). It keeps the source document content unchanged, leaves all heading paragraphs attached to the built-in `Heading1` and `Heading2` style IDs, sets the default run font to Arial 12pt, and rewrites the two built-in heading style definitions to the required Arial-based black heading system with the correct spacing and outline levels.
