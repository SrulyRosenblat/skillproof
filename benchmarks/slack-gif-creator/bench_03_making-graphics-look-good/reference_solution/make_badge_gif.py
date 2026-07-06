from __future__ import annotations

import json
import math

from PIL import ImageDraw

from core.frame_composer import create_gradient_background, draw_circle, draw_star
from core.gif_builder import GIFBuilder
from core.validators import validate_gif

WIDTH = 128
HEIGHT = 128
FRAME_COUNT = 12
FPS = 12

TOP_COLOR = (40, 72, 122)
BOTTOM_COLOR = (12, 20, 48)
OUTLINE = (24, 16, 44)
GLOW = (255, 190, 70, 90)
GOLD = (255, 196, 58)
PEACH = (255, 133, 92)
CREAM = (255, 247, 214)
WHITE = (255, 252, 236)


def add_sparkle(draw: ImageDraw.ImageDraw, x: int, y: int, scale: int) -> None:
    draw.line([(x - scale, y), (x + scale, y)], fill=WHITE, width=2)
    draw.line([(x, y - scale), (x, y + scale)], fill=WHITE, width=2)
    draw_circle(draw, (x, y), 1, fill=(255, 232, 150), outline=None, width=2)


def build_frames():
    pulse_steps = [0, 1, 2, 3, 2, 1, 0, -1, -2, -3, -2, -1]
    shimmer_steps = [-2, -1, 0, 1, 2, 1, 0, -1, -2, -1, 0, 1]
    frames = []
    for index in range(FRAME_COUNT):
        t = index / FRAME_COUNT
        pulse = pulse_steps[index]
        shimmer = shimmer_steps[index]

        frame = create_gradient_background(WIDTH, HEIGHT, TOP_COLOR, BOTTOM_COLOR)
        draw = ImageDraw.Draw(frame)

        center_x = WIDTH // 2 + shimmer
        center_y = HEIGHT // 2 + int(math.sin(t * math.tau * 2) * 2)

        draw_circle(draw, (center_x, center_y + 1), 38 + pulse, fill=(255, 208, 96), outline=OUTLINE, width=3)
        draw_circle(draw, (center_x, center_y), 32 + pulse, fill=(255, 227, 150), outline=(140, 74, 26), width=3)
        draw_circle(draw, (center_x, center_y), 28 + max(pulse // 2, -1), fill=None, outline=CREAM, width=2)

        draw_star(
            draw,
            center=(center_x, center_y),
            outer_radius=31 + pulse,
            inner_radius=15 + max(pulse // 2, -1),
            fill=PEACH,
            outline=OUTLINE,
            width=3,
        )
        draw_star(
            draw,
            center=(center_x, center_y - 1),
            outer_radius=22 + pulse,
            inner_radius=10 + max(pulse // 2, -1),
            fill=GOLD,
            outline=(156, 78, 16),
            width=3,
        )
        draw_star(
            draw,
            center=(center_x, center_y - 2),
            outer_radius=12,
            inner_radius=5,
            fill=WHITE,
            outline=(214, 155, 48),
            width=2,
        )

        draw.arc([center_x - 18, center_y - 14, center_x + 18, center_y + 12], start=205, end=320, fill=CREAM, width=3)

        sparkle_offsets = [
            (-28, -24, 4),
            (30, -18, 3),
            (-22, 25, 3),
        ]
        for base_x, base_y, scale in sparkle_offsets:
            sparkle_x = center_x + base_x + shimmer
            sparkle_y = center_y + base_y + pulse
            add_sparkle(draw, sparkle_x, sparkle_y, scale)

        frames.append(frame)

    return frames


def main():
    builder = GIFBuilder(width=WIDTH, height=HEIGHT, fps=FPS)
    builder.add_frames(build_frames())
    builder.save("polished_badge.gif", num_colors=64, optimize_for_emoji=True, remove_duplicates=False)

    passes, info = validate_gif("polished_badge.gif", is_emoji=True, verbose=True)
    with open("validation_report.json", "w", encoding="utf-8") as handle:
        json.dump({"passes": passes, "info": info}, handle, indent=2)


if __name__ == "__main__":
    main()
