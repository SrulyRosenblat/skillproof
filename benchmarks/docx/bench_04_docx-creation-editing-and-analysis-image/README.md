# Benchmark: OOXML Image Embedding in an Existing DOCX

This benchmark tests whether an agent can modify an existing `.docx` package to embed an image correctly. The target capability is the image-editing path from the `docx` skill: add the media file, wire up `word/_rels/document.xml.rels`, declare the image content type in `[Content_Types].xml`, and replace a placeholder paragraph in `word/document.xml` with an inline drawing.

## Why this matters

For existing Word documents, image work is often not a full document rewrite. The agent needs to understand that a `.docx` is a ZIP archive of OOXML parts and must patch the package in the right places. An agent that only knows high-level document generation will often recreate the file, break unrelated package parts, omit the content-type declaration, or fail to connect the drawing to the embedded media relationship.

## Fixtures

- `files/source/onepager.docx`: the source document with a single placeholder paragraph `[[PHOTO_SLOT]]`
- `files/source/campus-photo.png`: the image that must be embedded

These files are copied to `/workspace/source/...` before the tested agent runs.

## What the task requires

The task asks the agent to create `/workspace/output/onepager_with_photo.docx` by editing the existing package directly. The placeholder paragraph must become a centered inline image, the embedded file path must be `word/media/campus-photo.png`, and the size must be exactly `2194560 x 1463040` EMUs. It also explicitly requires preservation of every original ZIP member except the three OOXML files that need patching plus the new media file.

## How grading works

`grader/grade.sh` runs a Python checker that inspects only the final file state in `/workspace`.

It verifies that:

- `/workspace/output/onepager_with_photo.docx` exists.
- The output keeps every original ZIP member from the source document except the explicitly allowed modified parts.
- The only new ZIP member is `word/media/campus-photo.png`, and its bytes exactly match the provided PNG.
- The output document text is unchanged except that the placeholder paragraph becomes an image-only paragraph.
- The image paragraph is centered.
- The drawing uses an embedded relationship whose target is `media/campus-photo.png`.
- The image size is exactly `2194560 x 1463040` EMUs.
- `[Content_Types].xml` declares `png` as `image/png`.

## Why the reference solution passes

The reference solution patches exactly the required OOXML parts:

- `word/document.xml` replaces the `[[PHOTO_SLOT]]` paragraph with a centered inline drawing.
- `word/_rels/document.xml.rels` adds an image relationship targeting `media/campus-photo.png`.
- `[Content_Types].xml` adds the `png` content type declaration.
- `word/media/campus-photo.png` is added with the provided image bytes.

All other original package members are preserved unchanged, which is the main thing that distinguishes a correct package edit from a document rewrite.
