# bench_04: pdf-lib selective merge + page creation

## Capability under test

This benchmark tests whether an agent can use **pdf-lib** (the JavaScript PDF
library documented in the skill's advanced reference, under "JavaScript
Libraries") to:

1. Load existing PDFs with `PDFDocument.load`.
2. Selectively copy a *specific, non-contiguous subset* of pages from a source
   document into a new document with `copyPages(sourceDoc, [indices...])`
   (as opposed to copying every page, which is the trivial case covered by
   basic `pypdf` merge operations that other benchmarks in this suite already
   exercise).
3. Create a brand-new page with `addPage`, embed a standard font with
   `embedFont(StandardFonts...)`, and draw text on it with `drawText`.
4. Serialize the result with `doc.save()`.

These are exactly the patterns shown in the skill's "Advanced Merge and Split
Operations" and "Create Complex PDFs from Scratch" examples for pdf-lib. An
agent that has internalized that reference material can adapt those snippets
directly. An agent without it must independently rediscover pdf-lib's
specific API shape (async `copyPages` returning copied page objects that must
then be explicitly `addPage`'d, `embedFont` needing to happen before
`drawText` can reference the font, etc.) — via introspecting the vendored
module or its own knowledge of a fairly deep library.

## Why pdf-lib specifically (and not pypdf)

The sandbox has no network access and no npm registry, so `pdf-lib` cannot be
`npm install`ed at grading time. To make the capability testable at all, a
single self-contained, offline UMD bundle of pdf-lib
(`node_modules/pdf-lib/dist/pdf-lib.min.js`, MIT licensed) is vendored into
`files/lib/pdf-lib.min.js`. It has no other runtime dependencies (all of
pdf-lib's own dependencies are inlined in that bundle) and loads via a plain
Node `require()`.

The task prompt explicitly forbids using Python/pypdf for constructing the
output, so the agent cannot sidestep pdf-lib by falling back to the (easier,
more familiar) library exercised elsewhere in this benchmark suite.

## Task given to the agent

See `task_prompt.md`. In short: given `report_a.pdf` (4 pages) and
`report_b.pdf` (4 pages), write `/workspace/build_digest.js` (Node.js, using
the vendored pdf-lib) that produces `/workspace/digest.pdf` containing:

1. All 4 pages of `report_a.pdf`, in order.
2. Only the 1st and 3rd pages of `report_b.pdf` (2nd and 4th excluded).
3. One new page containing the text `Digest Summary`.

## How grading works

`grader/grade.sh` (invoked with cwd `/workspace`):

1. Fails immediately if `build_digest.js` is missing.
2. Fails if `build_digest.js` does not reference the mandated vendored path
   `lib/pdf-lib.min.js` — this exact token is mandated by `task_prompt.md`, so
   checking for it is checking a stated requirement, not reverse-engineering
   the solution.
3. Deletes any pre-existing `digest.pdf` and re-runs `node build_digest.js`
   fresh, so the graded output is actually produced by the submitted script
   (not a pre-baked file left over from local experimentation), and fails if
   the script errors or does not produce `digest.pdf`.
4. Runs `grader/check_digest.py`, which parses `digest.pdf` with `pypdf` and
   asserts:
   - it has exactly 7 pages,
   - pages 1-4 extract to `Report A - Page 1..4` in order,
   - pages 5-6 extract to `Report B - Page 1` and `Report B - Page 3` (proving
     the 2nd/4th pages of `report_b.pdf` were correctly excluded, not just
     that *some* subset was picked),
   - page 7's text contains `Digest Summary`.

All checks are property-based (parsed content, not byte-for-byte comparison),
since `pdf-lib`'s `save()` embeds a fresh timestamp on every run and so the
exact output bytes are never identical across runs.

## Reference solution

`reference_solution/build_digest.js` implements the described logic with
pdf-lib's `copyPages`/`addPage`/`embedFont`/`drawText`/`save`, plus the
resulting `digest.pdf` it produces. Verified locally: grading the
`files/` + `reference_solution/` overlay passes, and grading `files/` alone
(no submission) fails.
