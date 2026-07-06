# Benchmark: Polish a Slack Badge GIF

This benchmark tests whether an agent can take a deliberately bland Slack emoji animation and improve its visual quality using the specific "Making Graphics Look Good" guidance from the `slack-gif-creator` skill.

## Capability Under Test

The task targets polished graphic construction rather than basic GIF assembly. A passing solution must apply the skill's visual guidance in concrete ways:

- use a gradient background instead of a flat fill
- use thick outlines instead of `width=1`
- build the badge from layered shapes rather than a single flat icon
- add circular highlight or ring detail
- use vibrant warm colors with a dark contrasting outline or shadow
- include small accent details and visible motion so the result feels finished

This matters for the skill because a Slack GIF can be technically valid yet still look amateurish. The benchmark checks whether the agent can convert "looks good" advice into an actual polished render.

## Task Shape

The workspace starts with:

- `core/`: a small helper toolkit with `GIFBuilder`, `validate_gif`, `create_gradient_background`, `draw_circle`, and `draw_star`
- `make_badge_gif.py`: a starter script that currently renders a flat, low-detail badge

The agent must update `make_badge_gif.py` so it writes:

- `polished_badge.gif`
- `validation_report.json`

## How Grading Works

The grader is deterministic and inspects only workspace files.

It checks the source code for requirements explicitly stated in `task_prompt.md`:

- `create_gradient_background(...)` is used
- `draw_star(...)` is called at least twice
- a circular ring or highlight is added with `draw_circle(...)` or `draw.ellipse(...)`
- every explicit outline or line width is an integer literal `>= 2`

It then checks the rendered `polished_badge.gif`:

- file exists and is exactly `128x128`
- GIF contains exactly `12` frames
- the background shows a visible vertical gradient
- the center badge has enough color/detail complexity
- the frame includes both a bright warm accent color and a dark contrasting color
- visible bright accent pixels exist for sparkles or highlights
- multiple adjacent frames differ enough to show real motion

It also checks `validation_report.json`:

- file exists
- JSON contains `passes` and `info`
- `passes` is `true`

## Why the Reference Solution Passes

The reference solution:

- replaces the flat background with a blue vertical gradient
- uses multiple layered star shapes, circular rings, and a curved highlight
- uses dark outlines and warm gold/peach fills
- adds three sparkle accents
- animates pulse and shimmer motion across all 12 frames
- validates the generated GIF and writes the required JSON report

## Local Verification Performed

I verified two cases locally:

- `files/ + reference_solution/` passes `bash grader/grade.sh`
- `files/` alone fails `bash grader/grade.sh`
