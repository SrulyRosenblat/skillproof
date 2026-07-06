# Repair Fake Lists and Tab-Aligned Lines

This benchmark tests whether an agent can repair a `.docx` that currently fakes bullets, numbered lists, right-aligned same-line text, and dot leaders with literal characters. The target capability is specific to the `docx` skill: real Word list numbering must replace typed bullets and manual numbers, and real tab-stop structures must replace separator text.

The agent receives [files/source_brief.docx](/Users/srulyrosenblat/Developer/skill_auto_benchmark/benchmarks/docx/bench_05_lists-never-use-unicode-bullets-tab-stop/files/source_brief.docx) and must write `/workspace/repaired_brief.docx`. The source document intentionally uses `•`, `1.`, `||`, and `>>` as plain text. A correct solution keeps the same wording and paragraph order while converting those paragraphs to proper Word constructs.

## Grading

`grader/grade.sh` runs a deterministic Python checker against `/workspace/repaired_brief.docx`.

It verifies:

- the output file exists and is a readable `.docx` zip package
- the document has exactly the required paragraph order and wording for all untouched headings and labels
- the two `||` schedule lines were rewritten to use a real tab character plus a real right-aligned paragraph tab stop
- the two `•` lines were converted to real bullet list paragraphs, with no bullet characters left in their text runs
- the three `Launch Checklist` lines were converted to one real decimal-numbered list
- the two `Escalation Steps` lines were converted to a separate real decimal-numbered list that uses a different numbering instance, so it restarts at `1`
- the two `>>` lines were converted to use a real dot-leader positional tab, with only the label text and page number text remaining
- no tables appear anywhere in the document
- the document XML no longer contains the fake separator strings or typed bullet characters

Because the grader checks Word numbering metadata, paragraph tab definitions, and positional-tab OOXML, a solution that only makes the page look similar with spaces, tables, or typed markers fails.

## Reference Solution

The reference solution is [reference_solution/repaired_brief.docx](/Users/srulyrosenblat/Developer/skill_auto_benchmark/benchmarks/docx/bench_05_lists-never-use-unicode-bullets-tab-stop/reference_solution/repaired_brief.docx). It preserves the original paragraph order and wording, replaces the fake bullets and numbers with real numbering definitions, uses one bullet numbering instance plus two independent decimal numbering instances, rewrites the schedule lines to real right-tab paragraphs, and rewrites the reference lines to real dot-leader positional-tab paragraphs.
