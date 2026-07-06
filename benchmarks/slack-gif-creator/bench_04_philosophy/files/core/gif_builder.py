from __future__ import annotations

from pathlib import Path

from PIL import Image


class GIFBuilder:
    def __init__(self, width: int, height: int, fps: int = 10) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.frames = []

    def add_frame(self, frame) -> None:
        if frame.size != (self.width, self.height):
            raise ValueError(
                f"frame size {frame.size} does not match {(self.width, self.height)}"
            )
        self.frames.append(frame.copy())

    def add_frames(self, frames) -> None:
        for frame in frames:
            self.add_frame(frame)

    def save(
        self,
        path: str | Path,
        num_colors: int = 64,
        optimize_for_emoji: bool = True,
        remove_duplicates: bool = False,
    ) -> None:
        if not self.frames:
            raise ValueError("no frames added")

        duration = int(round(1000 / self.fps))
        path = Path(path)
        converted = []
        previous_bytes = None

        for frame in self.frames:
            palette_frame = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=num_colors)
            frame_bytes = palette_frame.tobytes()
            if remove_duplicates and previous_bytes == frame_bytes:
                continue
            converted.append(palette_frame)
            previous_bytes = frame_bytes

        if not converted:
            raise ValueError("all frames were removed as duplicates")

        converted[0].save(
            path,
            save_all=True,
            append_images=converted[1:],
            loop=0,
            duration=duration,
            optimize=optimize_for_emoji,
            disposal=2,
        )
