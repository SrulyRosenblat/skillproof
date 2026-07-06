# bench_02_drawing-from-scratch

## Capability under test

The `slack-gif-creator` skill teaches that graphics for a Slack GIF should be
drawn from scratch with PIL's `ImageDraw` primitives (`ellipse`, `polygon`,
`line`, `rectangle`) — computing exact vertex coordinates for shapes like
stars rather than assuming pre-packaged art or emoji fonts are available.

This benchmark tests exactly that: the model must draw a precise 10-vertex
five-pointed star polygon (five outer tip vertices and five inner notch
vertices, at exact radii and angles around a center point) using
`ImageDraw.polygon`, and animate it by recomputing the polygon's vertices at
12 discrete rotation angles to produce a smooth 360-degree spin. Without the
skill's guidance to build shapes from primitive vertex math, a model is prone
to reaching for shortcuts (a text/emoji glyph, a canned "star" helper, or an
approximate/asymmetric polygon) that will not match the exact geometry the
grader checks pixel-for-pixel.

## Task given to the model

`task_prompt.md` asks for a 128x128 Slack emoji GIF of a spinning five-pointed
star, fully specifying:
- exact canvas size, background color, frame count (12), fps (10), and loop behavior
- exact star geometry (outer/inner radius, center, fill/outline colors, outline width)
- the exact rotation schedule (30 degrees clockwise per frame, frame 0 pointing straight up)
- three required output files: a standalone regenerating script
  (`output/make_spinning_star.py`), the GIF itself (`output/spinning_star.gif`),
  and a `report.json` metadata file with an exact required schema

The prompt never mentions PIL, `ImageDraw`, or any API names — it only
describes the desired visual/geometric outcome, so the model must independently
know (or figure out) that hand-drawing a polygon with PIL is the way to
achieve pixel-exact star geometry.

## Grading

`grader/grade.sh` runs `pytest grader/test_benchmark.py` with `cwd=/workspace`. The tests:

1. **File existence** — the script, GIF, and report.json all exist under `output/`.
2. **`report.json` schema** — parsed and compared for exact equality against the required JSON.
3. **GIF spec compliance** (`assert_gif_matches_spec`) — executes real image analysis
   on the produced GIF (not string-matching source code):
   - opens the GIF and asserts size, frame count, per-frame duration (100ms), and infinite loop flag
   - independently reconstructs the exact expected 12 frames (background fill + star
     polygon at each rotation angle) using the same PIL primitives, and asserts the
     actual GIF's frame pixel data matches **exactly**, frame by frame
   - asserts the total distinct color count stays within Slack's optimization guidance (≤48)
4. **Regeneration determinism** — deletes the committed GIF, runs
   `make_spinning_star.py` standalone via `subprocess`, and re-validates the
   freshly generated GIF against the same exact-pixel spec, proving the script
   is the true source of the artwork and is deterministic/reproducible.

All checks are deterministic (no LLM judge needed): geometry, colors, and
timing are fully pinned by the task prompt, so pixel-exact comparison is
possible and appropriate here.

## Reference solution

`reference_solution/output/make_spinning_star.py` computes the 10 star
vertices with `angle = -90 + rotation_deg + 36*k` (alternating outer radius
46.0 / inner radius 18.4 from the center), draws each of the 12 rotated
frames with `ImageDraw.polygon(..., fill=(255,200,40), outline=(90,46,7),
width=4)` over a `(18,32,66)` background, and saves them as a looping GIF
with `duration=100` and `loop=0`. It also writes the matching `report.json`.
This script is copied verbatim (with its already-generated `spinning_star.gif`
and `report.json`) as `reference_solution/`, so overlaying it onto the task
fixtures and running the grader passes all four checks; the empty `files/`
fixture alone (no output files) fails every check.
