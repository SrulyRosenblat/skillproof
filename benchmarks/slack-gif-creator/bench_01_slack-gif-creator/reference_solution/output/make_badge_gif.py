from pathlib import Path
import json
from PIL import Image
from core.gif_builder import GIFBuilder

SOURCE = Path("/workspace/files/uploaded_badge.png")
OUTPUT_DIR = Path("/workspace/output")
POSITIONS = [(28, 8), (28, 4), (28, 8), (28, 16), (28, 28), (28, 40), (28, 48), (28, 40), (28, 28), (28, 16), (28, 8), (28, 12)]
BACKGROUND = (240, 248, 255, 255)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sticker = Image.open(SOURCE).convert("RGBA")
    builder = GIFBuilder(width=128, height=128, fps=10)

    for x, y in POSITIONS:
        frame = Image.new("RGBA", (128, 128), BACKGROUND)
        frame.alpha_composite(sticker, (x, y))
        builder.add_frame(frame.convert("RGB"))

    gif_path = OUTPUT_DIR / "badge_bounce.gif"
    builder.save(gif_path, num_colors=48, optimize_for_emoji=True)

    report = {
        "source_image": str(SOURCE),
        "output_gif": "/workspace/output/badge_bounce.gif",
        "canvas_size": [128, 128],
        "fps": 10,
        "frame_count": len(POSITIONS),
        "duration_seconds": len(POSITIONS) / 10,
    }
    (OUTPUT_DIR / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
