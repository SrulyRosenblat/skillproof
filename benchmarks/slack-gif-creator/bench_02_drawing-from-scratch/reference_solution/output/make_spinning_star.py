#!/usr/bin/env python3
"""Generate a spinning five-pointed star emoji GIF drawn entirely with PIL primitives."""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUTPUT_DIR = Path(__file__).resolve().parent
CANVAS = 128
CENTER = (64, 64)
OUTER_RADIUS = 46.0
INNER_RADIUS = 18.4
BACKGROUND = (18, 32, 66)
FILL_COLOR = (255, 200, 40)
OUTLINE_COLOR = (90, 46, 7)
OUTLINE_WIDTH = 4
FRAME_COUNT = 12
ROTATION_STEP_DEG = 30
FPS = 10
FRAME_DURATION_MS = 1000 // FPS


def star_points(rotation_deg):
    points = []
    for k in range(10):
        angle_deg = -90 + rotation_deg + 36 * k
        angle_rad = math.radians(angle_deg)
        radius = OUTER_RADIUS if k % 2 == 0 else INNER_RADIUS
        x = CENTER[0] + radius * math.cos(angle_rad)
        y = CENTER[1] + radius * math.sin(angle_rad)
        points.append((x, y))
    return points


def build_frame(rotation_deg):
    frame = Image.new("RGB", (CANVAS, CANVAS), BACKGROUND)
    draw = ImageDraw.Draw(frame)
    draw.polygon(
        star_points(rotation_deg),
        fill=FILL_COLOR,
        outline=OUTLINE_COLOR,
        width=OUTLINE_WIDTH,
    )
    return frame


def main():
    frames = [build_frame(i * ROTATION_STEP_DEG) for i in range(FRAME_COUNT)]

    gif_path = OUTPUT_DIR / "spinning_star.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=False,
    )

    report = {
        "canvas_size": [CANVAS, CANVAS],
        "fps": FPS,
        "frame_count": FRAME_COUNT,
        "duration_seconds": FRAME_COUNT * FRAME_DURATION_MS / 1000,
        "rotation_degrees_per_frame": ROTATION_STEP_DEG,
    }
    (OUTPUT_DIR / "report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
