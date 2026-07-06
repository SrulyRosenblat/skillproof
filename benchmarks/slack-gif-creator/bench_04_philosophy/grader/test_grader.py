from __future__ import annotations

import os
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence


WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
SCRIPT_PATH = WORKSPACE / "make_philosophy_gif.py"
GIF_PATH = WORKSPACE / "philosophy.gif"


def _fail(message: str) -> None:
    raise AssertionError(message)


def _load_frames() -> list[np.ndarray]:
    with Image.open(GIF_PATH) as image:
        frames = [np.array(frame.convert("RGB")) for frame in ImageSequence.Iterator(image)]
        loop = image.info.get("loop")
    if loop != 0:
        _fail("philosophy.gif must loop infinitely (GIF loop=0)")
    return frames


def _components(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    components: list[list[tuple[int, int]]] = []

    for y in range(height):
        for x in range(width):
            if not mask[y, x] or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            component: list[tuple[int, int]] = []
            while stack:
                cy, cx = stack.pop()
                component.append((cy, cx))
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            components.append(component)
    return components


def test_required_files_exist() -> None:
    assert SCRIPT_PATH.exists(), "make_philosophy_gif.py is missing"
    assert GIF_PATH.exists(), "philosophy.gif is missing"


def test_script_obeys_task_constraints() -> None:
    text = SCRIPT_PATH.read_text()
    required_snippets = [
        "from core.gif_builder import GIFBuilder",
        "draw.ellipse(",
        "draw.polygon(",
    ]
    for snippet in required_snippets:
        assert snippet in text, f"make_philosophy_gif.py must include `{snippet}`"

    forbidden_snippets = [
        "reference_orb.png",
        "draw.text(",
        "ImageFont",
        "truetype(",
    ]
    for snippet in forbidden_snippets:
        assert snippet not in text, f"make_philosophy_gif.py must not include `{snippet}`"


def test_gif_shape_and_background() -> None:
    with Image.open(GIF_PATH) as image:
        assert image.format == "GIF", "philosophy.gif must be a GIF"
        assert image.size == (128, 128), "philosophy.gif must be 128x128"
        assert getattr(image, "n_frames", 1) == 12, "philosophy.gif must have exactly 12 frames"

    frames = _load_frames()
    border_mask = np.zeros((128, 128), dtype=bool)
    border_mask[:12, :] = True
    border_mask[-12:, :] = True
    border_mask[:, :12] = True
    border_mask[:, -12:] = True

    for index, frame in enumerate(frames):
        border_pixels = frame[border_mask]
        pale_ratio = np.mean(np.all(border_pixels >= 230, axis=1))
        assert pale_ratio >= 0.9, f"frame {index} border must stay near-white"


def test_blue_orb_pulses() -> None:
    frames = _load_frames()
    areas: list[int] = []

    for index, frame in enumerate(frames):
        blue_mask = (
            (frame[:, :, 2] >= 150)
            & (frame[:, :, 2] >= frame[:, :, 1] + 20)
            & (frame[:, :, 1] >= frame[:, :, 0] + 5)
        )
        y_coords, x_coords = np.where(blue_mask)
        assert len(x_coords) >= 1200, f"frame {index} must contain a substantial blue orb"

        mean_x = float(np.mean(x_coords))
        mean_y = float(np.mean(y_coords))
        assert 54 <= mean_x <= 74, f"frame {index} blue orb must stay centered horizontally"
        assert 54 <= mean_y <= 74, f"frame {index} blue orb must stay centered vertically"
        areas.append(len(x_coords))

    assert max(areas) - min(areas) >= 900, "blue orb must visibly pulse across frames"


def test_two_gold_sparkles_orbit() -> None:
    frames = _load_frames()
    center = np.array([63.5, 63.5])
    observed_angles: list[float] = []

    for index, frame in enumerate(frames):
        gold_mask = (
            (frame[:, :, 0] >= 190)
            & (frame[:, :, 1] >= 150)
            & (frame[:, :, 2] <= 170)
        )

        yy, xx = np.indices((128, 128))
        radius = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2)
        orbit_mask = gold_mask & (radius >= 28) & (radius <= 64)
        components = [c for c in _components(orbit_mask) if len(c) >= 8]
        assert len(components) == 2, f"frame {index} must have exactly two gold sparkles"

        centroids = []
        for component in components:
            points = np.array([(x, y) for y, x in component], dtype=float)
            centroid = points.mean(axis=0)
            dist = np.linalg.norm(centroid - center)
            assert 32 <= dist <= 60, f"frame {index} sparkle must orbit around the orb"
            centroids.append(centroid)

        angles = [math.atan2(c[1] - center[1], c[0] - center[0]) for c in centroids]
        angle_gap = abs((angles[0] - angles[1] + math.pi) % (2 * math.pi) - math.pi)
        assert angle_gap >= 2.2, f"frame {index} sparkles must stay roughly opposite each other"
        observed_angles.append(sorted(angles)[0])

    unwrapped = np.unwrap(np.array(observed_angles))
    assert float(unwrapped.max() - unwrapped.min()) >= 1.2, "sparkles must move across frames"
