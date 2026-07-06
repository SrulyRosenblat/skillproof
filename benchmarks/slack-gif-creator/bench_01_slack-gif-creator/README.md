# Slack GIF Builder With Uploaded Image

This benchmark tests whether an agent can use the Slack GIF Creator skill to turn a user-provided PNG into a Slack-ready emoji GIF. The core capability is using the uploaded image directly with the skill’s GIF-building workflow while honoring Slack emoji constraints such as 128x128 dimensions, short duration, and palette optimization.

Why this matters:

- The skill explicitly supports working with uploaded images through PIL instead of redrawing them.
- The skill’s main workflow centers on `core.gif_builder.GIFBuilder` with Slack-oriented save options.
- Slack emoji GIFs have concrete size and duration requirements that are easy to miss without the skill knowledge.

How grading works:

- The grader checks that `/workspace/output/make_badge_gif.py` exists and contains the required workflow elements: `GIFBuilder`, loading the uploaded PNG from `/workspace/files/uploaded_badge.png`, building a 128x128 GIF at 10 FPS, and saving with `num_colors=48` plus `optimize_for_emoji=True`.
- The grader checks that `/workspace/output/report.json` exactly matches the required JSON object.
- The grader opens `/workspace/output/badge_bounce.gif` and verifies:
  - the GIF is 128x128,
  - it has exactly 12 frames,
  - each frame duration is 100 ms, so the total duration is 1.2 seconds,
  - the rendered animation matches the required frame-by-frame placement of the uploaded image on the specified background,
  - the rendered GIF uses no more than 48 colors.

How the reference solution satisfies the task:

- It loads the provided PNG with PIL and composites that exact image into each frame.
- It uses the required `GIFBuilder` import and Slack-oriented save call in `output/make_badge_gif.py`.
- It produces a 12-frame, 128x128 bounce animation and writes the exact JSON report requested by the task.
