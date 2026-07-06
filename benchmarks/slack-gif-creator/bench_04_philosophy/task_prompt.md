# Task

Create two files in `/workspace`:

1. `/workspace/make_philosophy_gif.py`
2. `/workspace/philosophy.gif`

Use the provided helper module at `/workspace/core/gif_builder.py`.

The file `/workspace/reference_orb.png` is an uploaded reference image, but for this task it is **inspiration only**. Build the animation from scratch. Do **not** load `/workspace/reference_orb.png` in your script, and do **not** copy, paste, composite, resize, rotate, mask, or otherwise reuse any pixels from it.

`/workspace/make_philosophy_gif.py` must generate `/workspace/philosophy.gif` when run with:

```bash
python /workspace/make_philosophy_gif.py
```

Animation requirements for `/workspace/philosophy.gif`:

- GIF format, exactly `128x128` pixels
- Exactly `12` frames
- Infinite loop
- Every frame must be drawn from scratch with PIL `ImageDraw` primitives
- Your script must contain at least one `draw.ellipse(...)` call and at least one `draw.polygon(...)` call
- Do not render text or emoji glyphs

Visual requirements:

- Use a pale near-white background in every frame
- Draw a centered blue orb near the middle of the canvas
- The orb must visibly pulse over the 12-frame animation
- Add exactly two gold diamond-shaped sparkles orbiting the orb
- The two sparkles must stay roughly opposite each other while their positions change across frames

You may use only the packages already available in the environment.
