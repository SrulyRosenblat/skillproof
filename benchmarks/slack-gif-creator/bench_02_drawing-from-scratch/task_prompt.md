Create a Slack emoji GIF of a five-pointed star that spins in place. No input files are needed for this task.

Write exactly these output files:

1. `/workspace/output/make_spinning_star.py` — a self-contained Python script that, when run as `python3 /workspace/output/make_spinning_star.py`, (re)generates `/workspace/output/spinning_star.gif` from scratch.
2. `/workspace/output/spinning_star.gif`
3. `/workspace/output/report.json`

## Animation specification

The GIF must be exactly 128x128 pixels, made of exactly 12 frames played at 10 frames per second (100 ms per frame), looping forever, for a total playback time of 1.2 seconds.

Every frame has a solid background fill of RGB `(18, 32, 66)`, with a single five-pointed star drawn on top, centered at pixel `(64, 64)`.

The star is a 10-vertex shape alternating between five "outer" tip vertices, each exactly 46 pixels from the center, and five "inner" notch vertices, each exactly 18.4 pixels from the center, spaced evenly 36 degrees apart around the center. The star's interior must be filled with RGB `(255, 200, 40)`, and its border must be stroked 4 pixels wide in RGB `(90, 46, 7)`.

In frame 0, one outer tip must point straight up from the center (directly above `(64, 64)`, on the vertical line `x=64`). Each following frame rotates the whole star exactly 30 degrees further clockwise than the previous frame, so frame `i` (0-indexed, `i` from 0 to 11) shows the star rotated `i * 30` degrees clockwise from frame 0's orientation. Frame 11 is rotated 330 degrees clockwise from frame 0, and looping from frame 11 back to frame 0 completes one full, seamless 360-degree turn.

## report.json

Write valid JSON with exactly this content:

```json
{
  "canvas_size": [128, 128],
  "fps": 10,
  "frame_count": 12,
  "duration_seconds": 1.2,
  "rotation_degrees_per_frame": 30
}
```

## Requirements recap

- `make_spinning_star.py` must run standalone (no arguments, no network, no user input) and produce `spinning_star.gif` matching the specification above exactly — the script is the source of truth for the artwork, so running it again must reproduce the same animation frame-for-frame.
- `spinning_star.gif` must be a valid, Slack-ready 128x128 emoji GIF (3 seconds or shorter) whose 12 frames show the exact star geometry, colors, and rotation sequence described above.
- `report.json` must exactly match the JSON shown above.
