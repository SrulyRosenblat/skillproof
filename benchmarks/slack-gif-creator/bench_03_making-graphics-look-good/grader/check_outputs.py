from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence


WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
SCRIPT = WORKSPACE / "make_badge_gif.py"
GIF = WORKSPACE / "polished_badge.gif"
REPORT = WORKSPACE / "validation_report.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def load_source() -> str:
    if not SCRIPT.exists():
        fail("Missing /workspace/make_badge_gif.py")
    return SCRIPT.read_text(encoding="utf-8")


def parse_source(source: str) -> ast.AST:
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        fail(f"make_badge_gif.py is not valid Python: {exc}")


def count_calls(tree: ast.AST, names: set[str]) -> int:
    total = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in names:
            total += 1
        elif isinstance(func, ast.Attribute) and func.attr in names:
            total += 1
    return total


def check_widths(tree: ast.AST) -> None:
    supported = {"draw_star", "draw_circle", "ellipse", "polygon", "line"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        func_name = None
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr
        if func_name not in supported:
            continue
        width_keywords = [kw for kw in node.keywords if kw.arg == "width"]
        for width_kw in width_keywords:
            if not isinstance(width_kw.value, ast.Constant) or not isinstance(width_kw.value.value, int):
                fail("All outline widths must be explicit integer literals")
            if width_kw.value.value < 2:
                fail("Found an outline/line width smaller than 2")


def check_source_requirements(tree: ast.AST, source: str) -> None:
    if "create_gradient_background" not in source:
        fail("Source does not use create_gradient_background(...)")
    if count_calls(tree, {"draw_star"}) < 2:
        fail("Source must use draw_star(...) at least twice")
    if count_calls(tree, {"draw_circle", "ellipse"}) < 1:
        fail("Source must add a circular ring or highlight detail")
    check_widths(tree)


def load_report() -> dict:
    if not REPORT.exists():
        fail("Missing /workspace/validation_report.json")
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("validation_report.json must contain a JSON object")
    if "passes" not in data or "info" not in data:
        fail("validation_report.json must contain passes and info keys")
    if data["passes"] is not True:
        fail("validation_report.json reports a failing GIF")
    return data


def to_rgb_array(image: Image.Image) -> np.ndarray:
    return np.array(image.convert("RGB"), dtype=np.int16)


def color_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a - b).mean())


def has_warm_and_dark_colors(frame: np.ndarray) -> None:
    warm = np.any((frame[:, :, 0] >= 220) & (frame[:, :, 1] >= 110) & (frame[:, :, 2] <= 170))
    dark = np.any((frame[:, :, 0] <= 90) & (frame[:, :, 1] <= 90) & (frame[:, :, 2] <= 110))
    if not warm:
        fail("The rendered badge is missing a bright warm accent color")
    if not dark:
        fail("The rendered badge is missing a dark contrasting outline or shadow color")


def check_gif_properties() -> None:
    if not GIF.exists():
        fail("Missing /workspace/polished_badge.gif")

    image = Image.open(GIF)
    frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
    if image.size != (128, 128):
        fail("polished_badge.gif must be 128x128")
    if len(frames) != 12:
        fail("polished_badge.gif must contain exactly 12 frames")

    rgb_frames = [to_rgb_array(frame) for frame in frames]
    first = rgb_frames[0]

    top_sample = first[4:20, 4:28].mean(axis=(0, 1))
    bottom_sample = first[108:124, 4:28].mean(axis=(0, 1))
    if color_distance(top_sample, bottom_sample) < 18:
        fail("Background does not appear to be a visible vertical gradient")

    center_crop = first[32:96, 32:96]
    unique_center_colors = np.unique(center_crop.reshape(-1, 3), axis=0)
    if unique_center_colors.shape[0] < 12:
        fail("Center badge lacks enough layered color/detail complexity")

    has_warm_and_dark_colors(first)

    sparkle_region = first[8:120, 8:120]
    bright_pixels = np.argwhere(
        (sparkle_region[:, :, 0] >= 235)
        & (sparkle_region[:, :, 1] >= 235)
        & (sparkle_region[:, :, 2] >= 200)
    )
    if bright_pixels.shape[0] < 20:
        fail("Rendered frame is missing visible sparkle or highlight accents")

    motion_scores = []
    for index in range(1, len(rgb_frames)):
        motion_scores.append(color_distance(rgb_frames[index - 1], rgb_frames[index]))
    if sum(score > 1.5 for score in motion_scores) < 4:
        fail("Animation does not show enough visible frame-to-frame motion")


def main() -> None:
    source = load_source()
    tree = parse_source(source)
    check_source_requirements(tree, source)
    load_report()
    check_gif_properties()


if __name__ == "__main__":
    main()
