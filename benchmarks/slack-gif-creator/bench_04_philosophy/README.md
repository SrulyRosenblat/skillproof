# Philosophy Benchmark

This benchmark tests whether an agent understands the `slack-gif-creator` skill's philosophy: the skill gives utilities and constraints, but it does not provide pre-made graphics, rigid templates, or reliable emoji-font rendering. The task forces the agent to treat an uploaded image as inspiration only and to build a Slack-ready GIF from scratch with PIL primitives.

## Capability Under Test

The benchmark checks whether the agent can:

- use the provided `core.gif_builder` helper instead of inventing a different workflow
- interpret the uploaded image at `/workspace/reference_orb.png` as inspiration only
- create the animation with PIL drawing primitives rather than reusing source pixels
- avoid text or emoji rendering and instead draw shapes directly

This matters because a correct user-facing workflow for this skill often depends on deciding whether an uploaded asset should be used directly or only as reference. The philosophy excerpt explicitly says the skill does not ship a library of packaged graphics or rigid animation templates, so a strong agent should synthesize its own artwork.

## Grading

The grader inspects only the final files in `/workspace`:

- `make_philosophy_gif.py` must exist and import `GIFBuilder` from `core.gif_builder`
- the script must include at least one `draw.ellipse(...)` call and at least one `draw.polygon(...)` call
- the script must not mention `reference_orb.png`, `draw.text(...)`, `ImageFont`, or `truetype(...)`
- `philosophy.gif` must be a `128x128` GIF with exactly `12` frames and infinite looping
- every frame must keep a pale near-white border
- the blue orb must stay centered and visibly pulse over time
- exactly two gold sparkles must orbit the orb while staying roughly opposite each other

The grader uses property-based image checks rather than byte-for-byte comparison, so multiple correct implementations can pass as long as they satisfy the task requirements.

## Reference Solution

The reference solution creates the required GIF with a centered blue orb whose radius pulses sinusoidally across 12 frames. Two diamond sparkles are drawn with `draw.polygon(...)` and advance around the orb in opposite positions on each frame. The code imports and uses `GIFBuilder`, draws the art from scratch with PIL primitives, and never loads or reuses the uploaded reference image.
