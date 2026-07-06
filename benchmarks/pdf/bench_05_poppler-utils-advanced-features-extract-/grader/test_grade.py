import json
import subprocess
from pathlib import Path

from PIL import Image

WORKSPACE = Path.cwd()


def expected_images():
    """Ground truth derived by asking poppler-utils directly about the
    fixture PDF, independent of anything the agent produced."""
    proc = subprocess.run(
        ["pdfimages", "-list", str(WORKSPACE / "input.pdf")],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = proc.stdout.splitlines()
    # Drop header line and the "----" separator line.
    data_lines = [l for l in lines[2:] if l.strip()]
    expected = []
    for line in data_lines:
        fields = line.split()
        page = int(fields[0])
        width = int(fields[3])
        height = int(fields[4])
        expected.append({"page": page, "width": width, "height": height})
    assert expected, "sanity check: fixture must contain embedded images"
    return expected


def test_extracted_images_dir_exists():
    d = WORKSPACE / "extracted_images"
    assert d.is_dir(), "extracted_images/ directory is missing"
    files = [f for f in d.iterdir() if f.is_file()]
    assert len(files) > 0, "extracted_images/ contains no files"


def test_manifest_matches_ground_truth():
    expected = expected_images()

    manifest_path = WORKSPACE / "image_manifest.json"
    assert manifest_path.is_file(), "image_manifest.json is missing"

    with open(manifest_path) as f:
        manifest = json.load(f)

    assert isinstance(manifest, list), "image_manifest.json must be a JSON array"
    assert len(manifest) == len(expected), (
        f"expected {len(expected)} images in manifest, got {len(manifest)}"
    )

    # Manifest must be sorted ascending by page.
    pages = [entry["page"] for entry in manifest]
    assert pages == sorted(pages), "manifest entries must be sorted by ascending page"
    assert pages == [e["page"] for e in expected], (
        f"manifest page numbers {pages} do not match the PDF's image pages "
        f"{[e['page'] for e in expected]}"
    )

    extracted_dir = WORKSPACE / "extracted_images"
    seen_files = set()

    for entry, exp in zip(manifest, expected):
        for key in ("page", "width", "height", "filename"):
            assert key in entry, f"manifest entry missing key '{key}': {entry}"

        assert entry["width"] == exp["width"], (
            f"page {entry['page']}: manifest width {entry['width']} != "
            f"native width {exp['width']}"
        )
        assert entry["height"] == exp["height"], (
            f"page {entry['page']}: manifest height {entry['height']} != "
            f"native height {exp['height']}"
        )

        filename = entry["filename"]
        assert "/" not in filename and "\\" not in filename, (
            f"filename must be a bare filename, not a path: {filename}"
        )
        img_path = extracted_dir / filename
        assert img_path.is_file(), f"referenced file does not exist: {img_path}"
        seen_files.add(img_path.resolve())

        with Image.open(img_path) as im:
            actual_w, actual_h = im.size
        assert (actual_w, actual_h) == (exp["width"], exp["height"]), (
            f"{filename}: actual pixel size {(actual_w, actual_h)} != "
            f"expected {(exp['width'], exp['height'])}"
        )

    # No unrelated extra files in the directory.
    all_files = {p.resolve() for p in extracted_dir.iterdir() if p.is_file()}
    extras = all_files - seen_files
    assert not extras, f"extracted_images/ has files not referenced by the manifest: {extras}"
