import json
import re
from pathlib import Path

from PIL import Image, ImageSequence


WORKSPACE = Path.cwd()
OUTPUT_DIR = WORKSPACE / "output"
SOURCE_PATH = WORKSPACE / "files" / "uploaded_badge.png"
SCRIPT_PATH = OUTPUT_DIR / "make_badge_gif.py"
GIF_PATH = OUTPUT_DIR / "badge_bounce.gif"
REPORT_PATH = OUTPUT_DIR / "report.json"

POSITIONS = [
    (28, 8),
    (28, 4),
    (28, 8),
    (28, 16),
    (28, 28),
    (28, 40),
    (28, 48),
    (28, 40),
    (28, 28),
    (28, 16),
    (28, 8),
    (28, 12),
]
BACKGROUND = (240, 248, 255)


def build_expected_frames():
    sticker = Image.open(SOURCE_PATH).convert("RGBA")
    frames = []
    for x, y in POSITIONS:
        frame = Image.new("RGBA", (128, 128), BACKGROUND + (255,))
        frame.alpha_composite(sticker, (x, y))
        quantized = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=48)
        frames.append(quantized.convert("RGB"))
    return frames


def test_required_files_exist():
    assert SOURCE_PATH.exists(), f"Missing input fixture: {SOURCE_PATH}"
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    assert GIF_PATH.exists(), f"Missing GIF: {GIF_PATH}"
    assert REPORT_PATH.exists(), f"Missing report: {REPORT_PATH}"


def test_script_uses_required_workflow():
    text = SCRIPT_PATH.read_text()
    assert "from core.gif_builder import GIFBuilder" in text
    assert "Image.open" in text
    assert "/workspace/files/uploaded_badge.png" in text
    assert re.search(r"GIFBuilder\s*\(\s*width\s*=\s*128\s*,\s*height\s*=\s*128\s*,\s*fps\s*=\s*10\s*\)", text)
    assert "builder.add_frame" in text
    assert "builder.save" in text
    assert "num_colors=48" in text
    assert "optimize_for_emoji=True" in text


def test_report_matches_required_schema():
    data = json.loads(REPORT_PATH.read_text())
    assert data == {
        "source_image": "/workspace/files/uploaded_badge.png",
        "output_gif": "/workspace/output/badge_bounce.gif",
        "canvas_size": [128, 128],
        "fps": 10,
        "frame_count": 12,
        "duration_seconds": 1.2,
    }


def test_gif_meets_slack_emoji_requirements_and_expected_animation():
    expected_frames = build_expected_frames()
    image = Image.open(GIF_PATH)
    assert image.size == (128, 128)

    actual_frames = [frame.copy().convert("RGB") for frame in ImageSequence.Iterator(image)]
    assert len(actual_frames) == 12

    durations = [frame.info.get("duration") for frame in ImageSequence.Iterator(Image.open(GIF_PATH))]
    assert durations == [100] * 12
    assert sum(durations) == 1200

    colors = set()
    for actual, expected in zip(actual_frames, expected_frames):
        colors.update(actual.getdata())
        assert list(actual.getdata()) == list(expected.getdata())
    assert len(colors) <= 48
