Upgrade the starter animation in `/workspace/make_badge_gif.py` so it produces a polished Slack emoji GIF instead of a flat placeholder.

Use the supplied helpers in `/workspace/core`.

Requirements:

1. Keep the script entrypoint in `/workspace/make_badge_gif.py`.
2. The script must generate `/workspace/polished_badge.gif` and `/workspace/validation_report.json`.
3. The GIF must be a 128x128 emoji GIF with exactly 12 frames.
4. Build every frame on a vertical gradient background created with `create_gradient_background(...)`. Do not use a flat background color.
5. The main badge must be centered and must use at least two layered star shapes drawn with the provided `draw_star(...)` helper.
6. Add at least one circular ring or highlight detail using `draw_circle(...)` or `draw.ellipse(...)`.
7. Add at least two small sparkle or accent details so the design is not just one flat shape.
8. Use a vibrant high-contrast palette: include at least one bright warm accent color in the badge and at least one dark contrasting outline or shadow color.
9. Every outline or line you draw must use an explicit integer `width` of 2 or greater. Do not leave any outline at width 1.
10. The animation must be deterministic and show visible motion across the 12 frames, such as a pulse, shimmer, wobble, or sparkle movement.
11. Save the GIF with the provided `GIFBuilder`.
12. After generating the GIF, validate it with `validate_gif(..., is_emoji=True, verbose=True)` and write `/workspace/validation_report.json` as JSON with this structure:

```json
{
  "passes": true,
  "info": {
    "width": 128,
    "height": 128,
    "frame_count": 12,
    "duration_ms": 1000
  }
}
```

The exact `duration_ms` value may differ, but the JSON object must contain `passes` and `info`.
