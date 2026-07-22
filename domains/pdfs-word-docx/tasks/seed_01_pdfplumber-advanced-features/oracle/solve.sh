#!/bin/bash
# Computes answer.txt / matched_codes.txt from /workspace/tags.pdf by reading
# the fully-resolved per-character placement of each tag on the page -- i.e.
# the text-rendering matrix (text matrix Tm composed with the current
# transformation matrix, CTM, in effect at that point), not just the raw
# operand of the nearest text-positioning operator.
#
# pypdf (the only PDF library available in this sandbox) does not resolve
# this composed matrix for us, so we walk the page's raw content stream by
# hand: track the CTM across q/cm/Q, track Tm across BT/Tm/Td/TD/T*, and at
# each Tj compose position = mult(Tm, CTM) -- the standard PDF text-rendering
# matrix formula (PDF spec 9.4.4), restricted to the translation component
# since that's all a glyph's origin point needs.
set -euo pipefail

python3 - <<'PY'
import re
import pypdf

BOX_X0, BOX_Y0, BOX_X1, BOX_Y1 = 200, 420, 420, 620


def mult(m, n):
    """Row-vector matrix product m*n, PDF convention: apply m then n."""
    return [
        m[0] * n[0] + m[1] * n[2],
        m[0] * n[1] + m[1] * n[3],
        m[2] * n[0] + m[3] * n[2],
        m[2] * n[1] + m[3] * n[3],
        m[4] * n[0] + m[5] * n[2] + n[4],
        m[4] * n[1] + m[5] * n[3] + n[5],
    ]


def decode_pdf_string(raw):
    out = []
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            if nxt == "\n":
                i += 2
                continue
            escapes = {"(": "(", ")": ")", "\\": "\\", "n": "\n", "r": "\r",
                       "t": "\t", "b": "\b", "f": "\f"}
            out.append(escapes.get(nxt, nxt))
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


TOKEN_RE = re.compile(r"\((?:[^()\\]|\\.)*\)|[^\s()]+")


def iter_text_positions(content_bytes):
    """Yield (shown_text, x, y) for each Tj/'/'' show-text op, where (x, y)
    is the fully-resolved on-page origin (translation of Tm composed with
    the active CTM at the moment the text is shown)."""
    ctm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    ctm_stack = []
    tm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    tl = 0.0
    operands = []

    for tok in TOKEN_RE.findall(content_bytes.decode("latin1")):
        if tok.startswith("("):
            operands.append(decode_pdf_string(tok[1:-1]))
            continue
        try:
            operands.append(float(tok))
            continue
        except ValueError:
            pass

        op = tok
        if op == "q":
            ctm_stack.append(ctm)
        elif op == "Q":
            ctm = ctm_stack.pop()
        elif op == "cm":
            a, b, c, d, e, f = operands[-6:]
            ctm = mult([a, b, c, d, e, f], ctm)
        elif op == "BT":
            tm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        elif op == "Tm":
            a, b, c, d, e, f = operands[-6:]
            tm = [a, b, c, d, e, f]
        elif op in ("Td", "TD"):
            tx, ty = operands[-2:]
            if op == "TD":
                tl = -ty
            tm = mult([1.0, 0.0, 0.0, 1.0, tx, ty], tm)
        elif op == "TL":
            tl = operands[-1]
        elif op == "T*":
            tm = mult([1.0, 0.0, 0.0, 1.0, 0.0, -tl], tm)
        elif op in ("Tj", "'", '"'):
            text = operands[-1]
            trm = mult(tm, ctm)
            yield text, trm[4], trm[5]
            if op in ("'", '"'):
                tm = mult([1.0, 0.0, 0.0, 1.0, 0.0, -tl], tm)

        operands = []


reader = pypdf.PdfReader("/workspace/tags.pdf")
page = reader.pages[0]
content = page.get_contents().get_data()

candidates = [
    (text, x, y)
    for text, x, y in iter_text_positions(content)
    if text.isdigit() and len(text) == 4
]

matched = sorted(
    int(code)
    for code, x, y in candidates
    if BOX_X0 <= x <= BOX_X1 and BOX_Y0 <= y <= BOX_Y1
)

with open("/workspace/answer.txt", "w") as f:
    f.write(str(sum(matched)))

with open("/workspace/matched_codes.txt", "w") as f:
    for code in matched:
        f.write(f"{code}\n")

print("matched:", matched, "sum:", sum(matched))
PY
