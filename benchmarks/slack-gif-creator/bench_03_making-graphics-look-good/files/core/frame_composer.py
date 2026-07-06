from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont


def create_blank_frame(width: int, height: int, color=(255, 255, 255)):
    return Image.new("RGBA", (width, height), color)


def create_gradient_background(width: int, height: int, top_color, bottom_color):
    frame = Image.new("RGBA", (width, height))
    top_r, top_g, top_b = top_color
    bottom_r, bottom_g, bottom_b = bottom_color
    pixels = frame.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        color = (
            int(top_r + (bottom_r - top_r) * t),
            int(top_g + (bottom_g - top_g) * t),
            int(top_b + (bottom_b - top_b) * t),
            255,
        )
        for x in range(width):
            pixels[x, y] = color
    return frame


def draw_circle(draw: ImageDraw.ImageDraw, center, radius, fill, outline=None, width=2):
    x, y = center
    box = [x - radius, y - radius, x + radius, y + radius]
    draw.ellipse(box, fill=fill, outline=outline, width=width)


def draw_star(draw: ImageDraw.ImageDraw, center, outer_radius, inner_radius, fill, outline=None, width=2):
    cx, cy = center
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = outer_radius if i % 2 == 0 else inner_radius
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    draw.polygon(points, fill=fill, outline=outline, width=width)


def draw_text(draw: ImageDraw.ImageDraw, position, text, fill=(0, 0, 0)):
    font = ImageFont.load_default()
    draw.text(position, text, fill=fill, font=font)
