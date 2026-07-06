from __future__ import annotations

import math

from PIL import Image, ImageDraw

from core.gif_builder import GIFBuilder

WIDTH = 128
HEIGHT = 128
CENTER = (64, 64)
BG = (245, 248, 252)
ORB_FILL = (96, 164, 234)
ORB_OUTLINE = (43, 96, 166)
ORB_HIGHLIGHT = (176, 220, 255)
SPARKLE_FILL = (240, 198, 82)
SPARKLE_OUTLINE = (184, 138, 42)


def draw_diamond(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float) -> None:
    points = [
        (cx, cy - radius),
        (cx + radius, cy),
        (cx, cy + radius),
        (cx - radius, cy),
    ]
    draw.polygon(points, fill=SPARKLE_FILL, outline=SPARKLE_OUTLINE)


def main() -> None:
    builder = GIFBuilder(width=WIDTH, height=HEIGHT, fps=12)

    for frame_index in range(12):
        frame = Image.new('RGB', (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(frame)

        pulse = math.sin((frame_index / 12) * math.tau)
        radius = 28 + pulse * 5
        bbox = (
            CENTER[0] - radius,
            CENTER[1] - radius,
            CENTER[0] + radius,
            CENTER[1] + radius,
        )
        draw.ellipse(bbox, fill=ORB_FILL, outline=ORB_OUTLINE, width=4)

        highlight_dx = -8 + 3 * math.sin((frame_index / 12) * math.tau)
        highlight_dy = -10 + 2 * math.cos((frame_index / 12) * math.tau)
        draw.ellipse(
            (
                CENTER[0] - 16 + highlight_dx,
                CENTER[1] - 14 + highlight_dy,
                CENTER[0] + 2 + highlight_dx,
                CENTER[1] + 4 + highlight_dy,
            ),
            fill=ORB_HIGHLIGHT,
        )

        orbit_radius = 45
        base_angle = (frame_index / 12) * math.tau
        for offset, sparkle_radius in ((0.0, 7), (math.pi, 6)):
            angle = base_angle + offset
            sx = CENTER[0] + orbit_radius * math.cos(angle)
            sy = CENTER[1] + orbit_radius * math.sin(angle)
            draw_diamond(draw, sx, sy, sparkle_radius)

        builder.add_frame(frame)

    builder.save('philosophy.gif', num_colors=48, optimize_for_emoji=True)


if __name__ == '__main__':
    main()
