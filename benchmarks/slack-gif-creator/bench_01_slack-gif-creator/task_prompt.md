Create a Slack emoji GIF from the uploaded PNG at `/workspace/files/uploaded_badge.png`.

Write exactly these output files:

1. `/workspace/output/make_badge_gif.py`
2. `/workspace/output/badge_bounce.gif`
3. `/workspace/output/report.json`

Requirements for `/workspace/output/make_badge_gif.py`:

- Use `from core.gif_builder import GIFBuilder`.
- Use PIL to open `/workspace/files/uploaded_badge.png` and use that uploaded image directly in every frame. Do not redraw or approximate the badge.
- Build a 128x128 GIF at 10 FPS.
- Create exactly 12 frames.
- Every frame must have a solid background color of RGB `(240, 248, 255)`.
- Paste the uploaded image at these exact top-left coordinates, one position per frame in order:
  `[(28, 8), (28, 4), (28, 8), (28, 16), (28, 28), (28, 40), (28, 48), (28, 40), (28, 28), (28, 16), (28, 8), (28, 12)]`
- Save the GIF to `/workspace/output/badge_bounce.gif` using `num_colors=48` and `optimize_for_emoji=True`.

Requirements for `/workspace/output/badge_bounce.gif`:

- It must match the 12-frame animation described above.
- It must be a valid Slack emoji-sized GIF: 128x128 pixels and 3 seconds or shorter.

Requirements for `/workspace/output/report.json`:

- It must be valid JSON with exactly this content:

```json
{
  "source_image": "/workspace/files/uploaded_badge.png",
  "output_gif": "/workspace/output/badge_bounce.gif",
  "canvas_size": [128, 128],
  "fps": 10,
  "frame_count": 12,
  "duration_seconds": 1.2
}
```
