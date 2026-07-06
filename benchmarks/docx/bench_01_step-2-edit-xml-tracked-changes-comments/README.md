# Benchmark: Tracked OOXML Edits With Nested Comment Anchors

This benchmark tests whether an agent can make precise Step 2 DOCX OOXML edits for tracked changes and comments inside an unpacked Word package. The task requires three distinct capabilities that are easy to get subtly wrong without the skill knowledge: replacing a run with sibling `<w:del>` and `<w:ins>` elements while preserving `<w:rPr>`, deleting an entire paragraph including the paragraph mark, and anchoring a comment plus reply with paragraph-level comment range markers.

This matters for the `docx` skill because naïve XML edits often produce invalid or semantically wrong redlines: deletions with `<w:t>` instead of `<w:delText>`, inserted/deleted markup nested inside runs, comments anchored inside `<w:r>`, or full-paragraph deletions that leave empty lines when changes are accepted. The benchmark isolates those failure modes in a small, deterministic fixture.

## Grading

The grader checks only the final file state in `/workspace`.

- `unpacked/word/document.xml` must contain a tracked replacement from `15 days notice` to `30 days’ written notice`, with top-level sibling `<w:del>` and `<w:ins>` elements, `Claude` as the author, the fixed timestamp `2025-01-01T00:00:00Z`, and preserved bold red run properties on both tracked-change runs.
- The inserted wording and comment bodies must use smart punctuation, and the XML source must encode it with `&#x2019;`, `&#x201C;`, and `&#x201D;`.
- The first paragraph must contain nested comment ranges with ids `0` and `1` around the insertion, followed by comment reference runs for both ids. The comment range markers must be siblings of runs, not children of runs.
- `unpacked/word/comments.xml` must contain exactly two comments, ids `0` and `1`, with the required text, author, and timestamp.
- The second paragraph must be a whole-paragraph tracked deletion: a paragraph-mark deletion inside `w:pPr/w:rPr/w:del` plus the deleted text inside a paragraph-level `<w:del>` using `<w:delText>`, with no remaining normal runs.
- The third paragraph must remain unchanged.
- `final.docx` must be a valid zip archive of the edited `unpacked/` package and its packaged XML members must match the edited workspace copies.

An untouched workspace fails because it has no `final.docx`, no tracked changes, and no comments.

## Reference solution

The reference solution updates only `unpacked/word/document.xml` and `unpacked/word/comments.xml`, then packs the package into `final.docx`.

- The original bold red run `15 days notice` is replaced with sibling `<w:del>` and `<w:ins>` elements that both copy the original `<w:rPr>`.
- The inserted phrase is wrapped by nested comment ranges `0` and `1`, with comment references after the period.
- The second paragraph gets both the paragraph-mark deletion and the deleted paragraph body, so accepting changes removes it cleanly.
- The comments file contains the exact requested comment and reply text with entity-encoded smart punctuation.
