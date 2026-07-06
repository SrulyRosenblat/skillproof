Create `/workspace/requirements.txt` for the provided Slack GIF helper project.

Inspect the Python files under `/workspace/src` and the implementation note at `/workspace/NOTES.md`, then write a runtime dependency file that satisfies all of the following requirements:

1. The output file must be exactly `/workspace/requirements.txt`.
2. Include every non-stdlib runtime dependency required by the project source files and by the explicit runtime note in `/workspace/NOTES.md`.
3. Use the installable PyPI package name for each dependency, not the import name if they differ.
4. Write exactly one dependency per line, all lowercase, with a minimum-version lower bound only, in the form `package>=x.y.z`.
5. Use these exact minimum versions when applicable to the dependencies you identify:
   - `pillow` version `10.0.0`
   - `imageio` version `2.31.0`
   - `imageio-ffmpeg` version `0.4.9`
   - `numpy` version `1.24.0`
6. Order the lines by first relevant appearance while scanning `/workspace/src` in lexical file order, then append any additional dependency required only by `/workspace/NOTES.md`.
7. Do not add comments, blank lines, extras, dev dependencies, or transitive dependencies that are not explicitly required by the source files or the note.

No other files need to be modified.
