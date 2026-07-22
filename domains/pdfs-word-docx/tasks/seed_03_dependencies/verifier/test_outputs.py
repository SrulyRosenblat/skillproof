"""Deterministic checks that each page of report.docx was faithfully
rendered to its own full-page PNG (not extracted artwork, not a mockup,
not the wrong page repeated three times)."""
import numpy as np
import pytest
from PIL import Image

WORKSPACE = "/workspace"

# The colour each page's embedded picture uses. A faithful full-page render
# of page N must show a sizeable patch of colour N and none of the others.
EXPECTED_COLORS = {
    1: (0, 0, 255),
    2: (220, 0, 0),
    3: (0, 150, 0),
}

COLOR_DIST_TOL = 60.0
OWN_COLOR_FRAC_MIN = 0.008
OWN_COLOR_FRAC_MAX = 0.35
OTHER_COLOR_FRAC_MAX = 0.01
WHITE_FRAC_MIN = 0.5

# US Letter portrait, the page size python-docx defaults to.
EXPECTED_ASPECT = 8.5 / 11.0
ASPECT_TOL = 0.08
MIN_LONG_SIDE = 600


def _load(page):
    path = f"{WORKSPACE}/page{page}_thumbnail.png"
    img = Image.open(path)
    assert img.mode in ("RGB", "RGBA", "L", "P"), f"unexpected image mode {img.mode}"
    return np.array(img.convert("RGB")).astype(int)


def _color_fraction(arr, color):
    dist = np.sqrt(((arr - np.array(color)) ** 2).sum(axis=2))
    return float((dist < COLOR_DIST_TOL).mean())


@pytest.mark.parametrize("page", [1, 2, 3])
def test_thumbnail_exists_and_sized_like_a_full_page(page):
    arr = _load(page)
    h, w = arr.shape[:2]
    assert max(w, h) >= MIN_LONG_SIDE, (
        f"page{page}_thumbnail.png is only {w}x{h}, too small to be a real "
        "full-page render"
    )
    aspect = w / h
    assert abs(aspect - EXPECTED_ASPECT) < ASPECT_TOL, (
        f"page{page}_thumbnail.png has aspect ratio {aspect:.3f}, expected "
        f"~{EXPECTED_ASPECT:.3f} (a US Letter page), got {w}x{h}"
    )


@pytest.mark.parametrize("page", [1, 2, 3])
def test_thumbnail_shows_only_its_own_page_content(page):
    arr = _load(page)

    own_frac = _color_fraction(arr, EXPECTED_COLORS[page])
    assert own_frac >= OWN_COLOR_FRAC_MIN, (
        f"page{page}_thumbnail.png does not contain page {page}'s picture "
        f"(matched only {own_frac:.4f} of pixels) -- this isn't a faithful "
        "render of that page"
    )
    assert own_frac <= OWN_COLOR_FRAC_MAX, (
        f"page{page}_thumbnail.png is {own_frac:.4f} the target colour -- "
        "looks like the raw embedded picture was saved instead of a "
        "rendered page"
    )

    for other_page, other_color in EXPECTED_COLORS.items():
        if other_page == page:
            continue
        other_frac = _color_fraction(arr, other_color)
        assert other_frac <= OTHER_COLOR_FRAC_MAX, (
            f"page{page}_thumbnail.png contains page {other_page}'s picture "
            f"(matched {other_frac:.4f} of pixels) -- wrong page was "
            "rendered"
        )

    white_frac = float((arr > 235).all(axis=2).mean())
    assert white_frac >= WHITE_FRAC_MIN, (
        f"page{page}_thumbnail.png is only {white_frac:.4f} near-white -- "
        "expected a mostly blank page background around the text/picture, "
        "not a cropped swatch or mockup"
    )
