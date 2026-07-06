from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageSequence


def validate_gif(path: str | Path, is_emoji: bool = True, verbose: bool = False):
    image = Image.open(path)
    frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
    width, height = image.size
    durations = [frame.info.get("duration", image.info.get("duration", 0)) for frame in frames]
    total_ms = sum(durations)
    info = {
        "width": width,
        "height": height,
        "frame_count": len(frames),
        "duration_ms": total_ms,
    }

    passes = True
    if is_emoji:
        passes &= (width, height) == (128, 128)
        passes &= total_ms <= 3000
        passes &= len(frames) >= 8

    if verbose:
        return passes, info
    return passes, info


def is_slack_ready(path: str | Path) -> bool:
    passes, _ = validate_gif(path, is_emoji=True, verbose=True)
    return passes
