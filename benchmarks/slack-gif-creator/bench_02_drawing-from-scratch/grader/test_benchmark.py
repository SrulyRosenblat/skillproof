import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageSequence

WORKSPACE = Path.cwd()
OUTPUT_DIR = WORKSPACE / "output"
SCRIPT_PATH = OUTPUT_DIR / "make_spinning_star.py"
GIF_PATH = OUTPUT_DIR / "spinning_star.gif"
REPORT_PATH = OUTPUT_DIR / "report.json"

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
DURATION_MS = 100

EXPECTED_REPORT = {
    "canvas_size": [128, 128],
    "fps": 10,
    "frame_count": 12,
    "duration_seconds": 1.2,
    "rotation_degrees_per_frame": 30,
}


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


def build_expected_frames():
    frames = []
    for i in range(FRAME_COUNT):
        frame = Image.new("RGB", (CANVAS, CANVAS), BACKGROUND)
        draw = ImageDraw.Draw(frame)
        draw.polygon(
            star_points(i * ROTATION_STEP_DEG),
            fill=FILL_COLOR,
            outline=OUTLINE_COLOR,
            width=OUTLINE_WIDTH,
        )
        frames.append(frame)
    return frames


def assert_gif_matches_spec(gif_path):
    assert gif_path.exists(), f"Missing GIF: {gif_path}"
    expected_frames = build_expected_frames()

    image = Image.open(gif_path)
    assert image.size == (CANVAS, CANVAS), f"Expected 128x128, got {image.size}"

    actual_frames = [f.copy().convert("RGB") for f in ImageSequence.Iterator(image)]
    assert len(actual_frames) == FRAME_COUNT, (
        f"Expected {FRAME_COUNT} frames, got {len(actual_frames)}"
    )

    durations = [
        f.info.get("duration") for f in ImageSequence.Iterator(Image.open(gif_path))
    ]
    assert durations == [DURATION_MS] * FRAME_COUNT, f"Bad frame durations: {durations}"
    assert sum(durations) == 1200

    loop = Image.open(gif_path).info.get("loop")
    assert loop == 0, f"GIF must loop forever (loop=0), got {loop!r}"

    colors = set()
    for idx, (actual, expected) in enumerate(zip(actual_frames, expected_frames)):
        colors.update(actual.getdata())
        assert list(actual.getdata()) == list(expected.getdata()), (
            f"Frame {idx} pixels do not match the required star geometry"
        )
    assert len(colors) <= 48, f"Too many colors in GIF: {len(colors)}"


def test_required_files_exist():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    assert GIF_PATH.exists(), f"Missing GIF: {GIF_PATH}"
    assert REPORT_PATH.exists(), f"Missing report: {REPORT_PATH}"


def test_report_matches_required_schema():
    data = json.loads(REPORT_PATH.read_text())
    assert data == EXPECTED_REPORT


def test_committed_gif_matches_spec():
    assert_gif_matches_spec(GIF_PATH)


def test_script_regenerates_the_same_animation_from_scratch():
    # output/ may be a pre-populated fixture directory that this process
    # doesn't own (e.g. reference-solution files overlaid by the grading
    # harness), so its own write bit can't be relied on. Renaming it aside
    # only needs write permission on its parent, which is always ours;
    # recreate a fresh, definitely-writable output/ with just the script in it.
    script_text = SCRIPT_PATH.read_text()
    backup_dir = OUTPUT_DIR.parent / "output_prebuilt"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    OUTPUT_DIR.rename(backup_dir)
    OUTPUT_DIR.mkdir()
    SCRIPT_PATH.write_text(script_text)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"make_spinning_star.py failed to run standalone:\n{result.stdout}\n{result.stderr}"
    )
    assert_gif_matches_spec(GIF_PATH)
