from __future__ import annotations

from pathlib import Path

from PIL import Image


class GIFBuilder:
    def __init__(self, width: int, height: int, fps: int = 10) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.frames: list[Image.Image] = []

    def add_frame(self, frame: Image.Image) -> None:
        if frame.size != (self.width, self.height):
            raise ValueError(f"Expected {(self.width, self.height)}, got {frame.size}")
        self.frames.append(frame.convert("RGBA"))

    def add_frames(self, frames: list[Image.Image]) -> None:
        for frame in frames:
            self.add_frame(frame)

    def save(
        self,
        path: str | Path,
        num_colors: int = 64,
        optimize_for_emoji: bool = True,
        remove_duplicates: bool = True,
    ) -> None:
        if not self.frames:
            raise ValueError("No frames added")

        prepared: list[Image.Image] = []
        last_bytes: bytes | None = None
        for frame in self.frames:
            paletted = frame.convert("P", palette=Image.ADAPTIVE, colors=num_colors)
            current = paletted.tobytes()
            if remove_duplicates and current == last_bytes:
                continue
            prepared.append(paletted)
            last_bytes = current

        if not prepared:
            prepared = [self.frames[0].convert("P", palette=Image.ADAPTIVE, colors=num_colors)]

        duration_ms = int(1000 / self.fps)
        disposal = 2 if optimize_for_emoji else 0
        prepared[0].save(
            path,
            save_all=True,
            append_images=prepared[1:],
            loop=0,
            duration=duration_ms,
            optimize=False,
            disposal=disposal,
        )
