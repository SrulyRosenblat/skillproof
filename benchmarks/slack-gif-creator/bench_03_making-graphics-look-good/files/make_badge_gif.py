from __future__ import annotations

import json

from PIL import ImageDraw

from core.frame_composer import create_blank_frame, draw_star
from core.gif_builder import GIFBuilder
from core.validators import validate_gif

WIDTH = 128
HEIGHT = 128
FRAME_COUNT = 12
FPS = 12


def build_frames():
    frames = []
    for _ in range(FRAME_COUNT):
        frame = create_blank_frame(WIDTH, HEIGHT, color=(245, 245, 245))
        draw = ImageDraw.Draw(frame)
        draw_star(
            draw,
            center=(WIDTH // 2, HEIGHT // 2),
            outer_radius=30,
            inner_radius=14,
            fill=(255, 215, 0),
            outline=(255, 215, 0),
            width=1,
        )
        frames.append(frame)
    return frames


def main():
    builder = GIFBuilder(width=WIDTH, height=HEIGHT, fps=FPS)
    builder.add_frames(build_frames())
    builder.save("polished_badge.gif", num_colors=64, optimize_for_emoji=True)

    passes, info = validate_gif("polished_badge.gif", is_emoji=True, verbose=True)
    with open("validation_report.json", "w", encoding="utf-8") as handle:
        json.dump({"passes": passes, "info": info}, handle, indent=2)


if __name__ == "__main__":
    main()
