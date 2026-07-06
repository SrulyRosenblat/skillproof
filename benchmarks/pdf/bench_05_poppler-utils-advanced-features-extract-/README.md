# bench_05_poppler-utils-advanced-features-extract-

## Capability tested

This benchmark tests whether an agent knows how to extract the **embedded
raster images** from a PDF at their **native resolution**, as opposed to
rasterizing whole pages (e.g. `pdftoppm`) or otherwise re-encoding/resizing
the figures. This is the "Extract Embedded Images" / "Extract Figures/Images
from PDF (Method 1)" capability documented in the skill's advanced
poppler-utils reference, which recommends `pdfimages -all` (and
`pdfimages -list` to enumerate images with their page/dimensions) rather than
generic page-rendering tools.

Why it matters: a very common mistake for an agent unfamiliar with
poppler-utils is to reach for `pdftoppm` (page rasterization) or a
PDF-to-image render loop when asked to "extract figures," producing full-page
screenshots instead of the actual embedded image assets at their original
resolution. The skill explicitly distinguishes these two operations, and only
`pdfimages` recovers the original embedded raster data untouched.

## Fixture

`files/input.pdf` is a 3-page PDF generated with reportlab. Each page has a
heading, a line of body text, and one embedded PNG raster image drawn onto
the page, at these native pixel resolutions:

- Page 1: 120x80
- Page 2: 200x150
- Page 3: 90x180

These dimensions are deliberately distinct from each other and from the
page's rendered/screenshot resolution (e.g. `pdftoppm -r 150` on a
letter-size page yields ~1275x1650), so any solution that rasterizes pages
instead of extracting the embedded images will fail the dimension checks.

## Task given to the agent

The agent is asked to (see `task_prompt.md`):
1. Extract every embedded raster image from `/workspace/input.pdf` into
   `/workspace/extracted_images/`, at native resolution (no resizing/
   recompression, no page screenshots).
2. Write `/workspace/image_manifest.json`: a JSON array, one object per
   extracted image, sorted by ascending page number, with keys `page`,
   `width`, `height`, `filename`.

## Grading

`grader/grade.sh` runs `pytest grader/test_grade.py` with cwd=`/workspace`.
The tests:

1. Establish ground truth **independently of the agent's work** by running
   `pdfimages -list` directly on the fixture `input.pdf` (present in
   `/workspace` regardless of what the agent did) to get the true
   page/width/height for every embedded image.
2. Assert `/workspace/extracted_images/` exists and is non-empty.
3. Assert `/workspace/image_manifest.json` exists, parses as a JSON array of
   the correct length, and its entries are sorted ascending by page and
   correspond 1:1 with the true image pages.
4. For every manifest entry: check required keys are present, that its
   declared `width`/`height` match the ground truth for that page, that
   `filename` is a bare filename (not a path) that exists inside
   `extracted_images/`, and that actually opening that file with Pillow
   yields pixel dimensions matching both the manifest and the ground truth.
5. Assert there are no extra/unreferenced files sitting in
   `extracted_images/`.

Because dimensions are checked by actually opening the produced image files
with Pillow (not by trusting the manifest, and not by string-matching source
code), a solution that fabricates a manifest without real matching files, or
that substitutes full-page screenshots for the embedded figures, is rejected.

## How the reference solution satisfies it

`reference_solution/` was built by running:

```bash
pdfimages -all files/input.pdf reference_solution/extracted_images/img
```

which produced `img-000.png`, `img-001.png`, `img-002.png` at exactly the
original 120x80, 200x150, and 90x180 resolutions (verified with
`pdfimages -list`). `reference_solution/image_manifest.json` was then
hand-written to describe those three files with their page numbers and
dimensions, sorted ascending by page.

## Local verification performed

- `bash grader/grade.sh` (via `pytest`) **passes** when `reference_solution/`
  is overlaid on `files/`.
- It **fails** on an untouched workspace (`files/` alone, no agent output).
- It also **fails** against a plausible wrong-approach baseline that runs
  `pdftoppm -png -r 150` to rasterize whole pages instead of extracting the
  embedded images (dimensions mismatch: 1275x1650 vs. the true 120x80 /
  200x150 / 90x180).
