# Benchmark: Infer Slack GIF Runtime Dependencies

This benchmark tests whether an agent can author the correct `requirements.txt` for a small Slack GIF utility project by inspecting source files and a short implementation note. The key capability is identifying the right runtime packages and writing them with minimum-version lower bounds, including two details that are easy to miss without the skill knowledge: `PIL` must be installed via `pillow`, and ffmpeg-based `imageio` usage requires the separate `imageio-ffmpeg` package.

This matters for the `slack-gif-creator` skill because the skill’s setup depends on exactly these libraries: Pillow for frame drawing, NumPy for pixel/math operations, ImageIO for frame and media I/O, and ImageIO’s ffmpeg backend for video-backed workflows. An agent that only follows Python import names will usually omit `imageio-ffmpeg`, and an agent that does not know the PyPI mapping may incorrectly write `PIL` instead of `pillow`.

## Task Summary

The model under test receives a small project in `/workspace/src` plus `/workspace/NOTES.md`. It must create `/workspace/requirements.txt` by:

1. Scanning the source tree for non-stdlib runtime dependencies.
2. Incorporating the explicit extra runtime dependency described in the note.
3. Writing lowercase PyPI package names with `>=` minimum versions only.
4. Preserving the required package order.

## Grading

`grader/grade.sh` checks only the final workspace state. It fails unless:

1. `/workspace/requirements.txt` exists.
2. The file contains exactly four non-empty lines, in this order:
   - `pillow>=10.0.0`
   - `imageio>=2.31.0`
   - `imageio-ffmpeg>=0.4.9`
   - `numpy>=1.24.0`
3. There is no extra whitespace, comments, blank lines, or additional packages.

Every check is directly traceable to the task prompt, which explicitly requires one package per line, lowercase PyPI names, exact minimum versions, and that the package order follow the first relevant appearance while scanning `src/` and then `NOTES.md`.

## Reference Solution

The reference solution creates `requirements.txt` with these lines:

```text
pillow>=10.0.0
imageio>=2.31.0
imageio-ffmpeg>=0.4.9
numpy>=1.24.0
```

It satisfies the task by mapping imports and implementation notes to installable packages:

- `from PIL ...` maps to `pillow`
- `import imageio.v2 as imageio` maps to `imageio`
- the ffmpeg note adds `imageio-ffmpeg`
- `import numpy as np` maps to `numpy`
