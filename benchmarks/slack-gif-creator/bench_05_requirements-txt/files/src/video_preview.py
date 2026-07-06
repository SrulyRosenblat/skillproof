import imageio.v2 as imageio
import numpy as np


def preview_frame(width: int = 128, height: int = 128) -> np.ndarray:
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:, :, 1] = 180
    canvas[:, :, 2] = 255
    return canvas


def write_preview(path: str) -> None:
    imageio.imwrite(path, preview_frame())
