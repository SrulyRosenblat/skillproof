from PIL import Image, ImageDraw


def make_badge(size: int = 128) -> Image.Image:
    image = Image.new("RGBA", (size, size), (20, 30, 44, 255))
    draw = ImageDraw.Draw(image)
    inset = size // 8
    draw.rounded_rectangle(
        [inset, inset, size - inset, size - inset],
        radius=size // 6,
        fill=(255, 210, 90, 255),
        outline=(255, 255, 255, 255),
        width=max(2, size // 24),
    )
    return image
