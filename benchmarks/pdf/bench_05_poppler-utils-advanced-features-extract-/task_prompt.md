# Task: Extract Embedded Figures from a Report PDF

A short report is at `/workspace/input.pdf`. Each page contains a heading, a line
of body text, and one embedded raster figure. A downstream cataloging pipeline
needs the figures pulled out as standalone image files plus a small index
describing them.

Produce the following in `/workspace`:

## 1. `/workspace/extracted_images/`

A directory containing one image file for every embedded raster image found in
`input.pdf`, extracted at its original (native) resolution — do not
rasterize/screenshot the pages, and do not resize, recompress, or otherwise
alter the pixel dimensions of the images as they exist inside the PDF.

## 2. `/workspace/image_manifest.json`

A JSON file containing a single JSON array. It must have exactly one object
per extracted image, sorted in ascending order by page number, each with
exactly these keys:

- `"page"`: integer — the 1-indexed page number of the PDF the image was
  embedded on.
- `"width"`: integer — the image's native pixel width.
- `"height"`: integer — the image's native pixel height.
- `"filename"`: string — the image's filename (not a path), relative to
  `/workspace/extracted_images/`, e.g. `"img-000.png"`.

## Requirements

- Every embedded image in the PDF must be accounted for in the manifest, and
  every file referenced by the manifest must exist in `extracted_images/` and
  be openable as an image with pixel dimensions exactly matching the `width`
  and `height` recorded for it.
- Do not include any extra, unrelated files in `extracted_images/`.
- The `width`/`height` values must reflect the image's actual native
  resolution as stored in the PDF, not the size it happens to be displayed at
  on the page.
