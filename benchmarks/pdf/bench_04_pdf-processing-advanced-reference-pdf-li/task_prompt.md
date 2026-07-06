# Build a Digest PDF with Node.js

Two PDF reports are provided in `/workspace`:

- `/workspace/report_a.pdf` — 4 pages
- `/workspace/report_b.pdf` — 4 pages

A self-contained, offline copy of the `pdf-lib` JavaScript library is provided at
`/workspace/lib/pdf-lib.min.js`. It can be loaded directly with Node's `require()`
(e.g. `require('./lib/pdf-lib.min.js')`) — no `npm install` and no network access
are needed or available.

## Your task

Write a Node.js script at `/workspace/build_digest.js` that, when run from
`/workspace` with exactly:

```
node build_digest.js
```

(no CLI arguments, no interactive input, no network access) produces a new file
`/workspace/digest.pdf` containing exactly 7 pages, in this exact order:

1. All 4 pages of `report_a.pdf`, unmodified and in their original order.
2. Only the **1st and 3rd** pages of `report_b.pdf`, in their original order —
   the 2nd and 4th pages of `report_b.pdf` must **not** appear anywhere in the
   output.
3. One new final page (any page size) with the text `Digest Summary` drawn
   somewhere on it.

## Requirements

- `build_digest.js` must be a Node.js script that builds `digest.pdf` using the
  `pdf-lib` library vendored at `/workspace/lib/pdf-lib.min.js`. Do not use
  Python, `pypdf`, or any other PDF library to construct `digest.pdf`.
- Running `node build_digest.js` must complete successfully with no arguments
  and no prompts.
- Leave both `build_digest.js` and the resulting `digest.pdf` in `/workspace`
  when you are done.
