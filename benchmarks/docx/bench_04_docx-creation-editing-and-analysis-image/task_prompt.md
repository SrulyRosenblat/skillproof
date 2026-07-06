# Task

Starting from `/workspace/source/onepager.docx` and `/workspace/source/campus-photo.png`, create `/workspace/output/onepager_with_photo.docx`.

Requirements:

1. Edit the existing DOCX package directly. Do not regenerate the document from scratch.
2. Replace the paragraph whose only text is `[[PHOTO_SLOT]]` with a centered inline image.
3. Embed `/workspace/source/campus-photo.png` into the DOCX as `word/media/campus-photo.png`. Do not use an external link.
4. The displayed image size must be exactly `2.4` inches by `1.6` inches, which is `2194560 x 1463040` EMUs in OOXML.
5. Preserve every existing ZIP member from `/workspace/source/onepager.docx` byte-for-byte except:
   - `word/document.xml`
   - `word/_rels/document.xml.rels`
   - `[Content_Types].xml`
   - the new embedded media file `word/media/campus-photo.png`
6. Keep all non-placeholder document text and paragraph order unchanged.
7. The result must be a valid `.docx` file at `/workspace/output/onepager_with_photo.docx`.
