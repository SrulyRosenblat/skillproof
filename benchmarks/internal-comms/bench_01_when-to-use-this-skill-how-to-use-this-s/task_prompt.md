Write the requested internal communication using the guide in `/workspace/examples` that best fits the request in `/workspace/request.md`.

Create exactly these files in `/workspace`:

- `response.md`
- `selection.json`

Requirements:

- Read `/workspace/request.md` and the guide files in `/workspace/examples/`.
- `selection.json` must be valid JSON with exactly these keys:
  - `request_type`
  - `selected_guideline`
  - `why`
- In `selection.json`, `request_type` must identify the communication type of the request.
- In `selection.json`, `selected_guideline` must be the relative path to the guide you chose, using the path as it appears under `/workspace/examples`.
- `response.md` must follow the chosen guide's formatting rules exactly.
- Use only facts supported by `/workspace/request.md`.
- Do not leave placeholders such as `TBD`, `TODO`, `lorem ipsum`, or bracketed notes to fill later.

No other output files are required.
