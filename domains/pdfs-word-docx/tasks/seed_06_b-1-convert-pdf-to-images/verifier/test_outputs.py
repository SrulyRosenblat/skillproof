"""Deterministic checks for /workspace/page_images/, produced from /workspace/input.pdf.

/workspace/input.pdf is a 3-page PDF built entirely out of vector fills and
text -- it has no embedded raster picture assets at all. Each page carries
one large, distinctly-colored rectangle covering a known fraction of the
page: page 1 is red, page 2 is green, page 3 is blue, and no page contains
any other page's color. A tool that pulls embedded picture assets out of the
PDF's internal structure (rather than rendering each page's actual visual
appearance) finds nothing to extract from this file, so these checks can
only be satisfied by genuinely rasterizing each page.

Each page's MediaBox (the full underlying sheet, 792x1224 tabloid-size) is
deliberately larger than its CropBox (612x792 letter-size), which is the
actual visible page area where the colored rectangle lives. Rasterizers
(e.g. poppler's pdftoppm) render the MediaBox by default, so a render that
ignores the CropBox comes out at the wrong aspect ratio and with the
colored rectangle diluted by a large blank margin -- only a render that
honors the CropBox (e.g. `pdftoppm -cropbox`) matches the checks below.
"""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pypdf import PdfReader

INPUT_PDF = Path("/workspace/input.pdf")
OUTPUT_DIR = Path("/workspace/page_images")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".ppm", ".pgm"}

# (name, RGB) target color per page, in page order (page 1 first).
PAGE_COLORS = [
    ("red", (255, 0, 0)),
    ("green", (0, 255, 0)),
    ("blue", (0, 0, 255)),
]

COLOR_TOL = 40  # per-channel tolerance for a pixel to "match" a target color
MIN_TARGET_FRACTION = 0.05  # each page's own color must cover >=5% of its image
MAX_OTHER_FRACTION = 0.02  # neither of the other two colors may exceed 2%


def _color_fraction(arr, rgb):
    diff = np.abs(arr.astype(int) - np.array(rgb).reshape(1, 1, 3))
    mask = (diff <= COLOR_TOL).all(axis=2)
    return float(mask.mean())


@pytest.fixture(scope="module")
def expected_page_count():
    return len(PdfReader(INPUT_PDF).pages)


@pytest.fixture(scope="module")
def expected_aspect_ratio():
    # The CropBox, not the MediaBox, is the actual visible page area.
    box = PdfReader(INPUT_PDF).pages[0].cropbox
    return float(box.width) / float(box.height)


@pytest.fixture(scope="module")
def output_files():
    assert OUTPUT_DIR.is_dir(), f"{OUTPUT_DIR} was not created"
    return sorted(
        p
        for p in OUTPUT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def test_one_image_per_page_and_no_extra_files(output_files, expected_page_count):
    all_entries = list(OUTPUT_DIR.iterdir())
    assert len(all_entries) == len(output_files), (
        "page_images/ must contain only the per-page image files, found "
        f"extra non-image entries: {sorted(p.name for p in all_entries)}"
    )
    assert len(output_files) == expected_page_count, (
        f"expected exactly {expected_page_count} images (one per PDF page), "
        f"found {len(output_files)}"
    )


def test_images_are_full_page_renders_not_thumbnails(output_files, expected_aspect_ratio):
    assert output_files, "no output image files to check"
    for f in output_files:
        with Image.open(f) as im:
            width, height = im.size
        assert min(width, height) >= 400, (
            f"{f.name} is only {width}x{height}px -- too small to be a real "
            "full-page rendering"
        )
        actual_ratio = width / height
        assert actual_ratio == pytest.approx(expected_aspect_ratio, rel=0.1), (
            f"{f.name} has aspect ratio {actual_ratio:.3f}, expected "
            f"~{expected_aspect_ratio:.3f} (the PDF page's own aspect ratio) "
            "-- this doesn't look like a render of the full page"
        )


def test_each_page_shows_its_own_color_and_no_other_pages_color(output_files):
    assert len(output_files) == len(PAGE_COLORS), "expected a 3-page input PDF"

    for f, (color_name, rgb) in zip(output_files, PAGE_COLORS):
        with Image.open(f) as im:
            arr = np.array(im.convert("RGB"))

        own_fraction = _color_fraction(arr, rgb)
        assert own_fraction >= MIN_TARGET_FRACTION, (
            f"{f.name} (sorted into this page's position) shows only "
            f"{own_fraction:.1%} {color_name} pixels; expected this page's "
            "distinctive colored block to be clearly visible in a genuine "
            "page render"
        )

        for other_name, other_rgb in PAGE_COLORS:
            if other_name == color_name:
                continue
            other_fraction = _color_fraction(arr, other_rgb)
            assert other_fraction <= MAX_OTHER_FRACTION, (
                f"{f.name} contains {other_fraction:.1%} {other_name} pixels, "
                "but that color belongs to a different page -- images are "
                "not in the correct per-page order, or don't show that "
                "page's actual content"
            )
