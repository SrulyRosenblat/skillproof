#!/usr/bin/env python3
"""Deterministic + LLM-judge grader for the brainstorm/critique/build benchmark."""
import json
import os
import re
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("BENCH_WORKSPACE", "/workspace"))
JUDGE_DIR = WORKSPACE / ".judge"

AXES = ["Color", "Type", "Layout", "Signature"]
REQUIRED_FILES = [
    "design/initial-plan.md",
    "design/critique.md",
    "design/final-plan.md",
    "index.html",
    "styles.css",
]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def read(path):
    p = WORKSPACE / path
    if not p.exists():
        fail(f"missing required file: {path}")
    return p.read_text(encoding="utf-8", errors="replace")


def section(text, heading):
    """Return the body text of a '## Heading' section, up to the next '## '."""
    m = re.search(
        rf"^##\s*{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not m:
        return None
    return m.group(1).strip("\n")


def parse_colors(body, label):
    if body is None:
        fail(f"{label}: missing '## Color' section")
    lines = [l for l in body.splitlines() if l.strip().startswith("-")]
    colors = []
    for line in lines:
        m = re.search(r"#([0-9A-Fa-f]{6})", line)
        if not m:
            continue
        hexval = m.group(1).lower()
        name_part = line[: m.start()]
        name = re.sub(r"^-\s*", "", name_part)
        name = re.sub(r"[—\-:]\s*$", "", name).strip()
        colors.append((name, hexval))
    if not (4 <= len(colors) <= 6):
        fail(
            f"{label}: Color section must have 4-6 named hex colors, found {len(colors)}"
        )
    return colors


def parse_types(body, label):
    if body is None:
        fail(f"{label}: missing '## Type' section")
    lines = [l for l in body.splitlines() if l.strip().startswith("-")]
    roles = {}
    for line in lines:
        m = re.match(r"^-\s*(Display|Body|Utility)\s*:\s*(.+)$", line.strip())
        if not m:
            continue
        role, rest = m.group(1), m.group(2)
        font = re.split(r"—|(?:\s-\s)", rest, maxsplit=1)[0].strip()
        roles[role] = font
    if "Display" not in roles or "Body" not in roles:
        fail(f"{label}: Type section must include at least Display and Body roles")
    if not (2 <= len(roles) <= 3):
        fail(f"{label}: Type section must have 2-3 roles, found {len(roles)}")
    return roles


def parse_layout(body, label):
    if body is None:
        fail(f"{label}: missing '## Layout' section")
    fence = re.search(r"```(.*?)```", body, re.DOTALL)
    if not fence:
        fail(f"{label}: Layout section must contain a fenced ASCII wireframe")
    wireframe = fence.group(1).strip("\n")
    wf_lines = [l for l in wireframe.splitlines() if l.strip()]
    if len(wf_lines) < 4:
        fail(f"{label}: Layout wireframe must have at least 4 non-empty lines")
    chars_used = set(c for l in wf_lines for c in l if c in "+-|/\\_")
    if len(chars_used) < 2:
        fail(f"{label}: Layout wireframe doesn't look like a structural sketch")
    prose = body[: fence.start()].strip()
    if len(prose) < 15:
        fail(f"{label}: Layout section is missing prose description")
    normalized = "\n".join(l.strip() for l in wf_lines)
    return {"prose": prose, "wireframe": normalized}


def parse_signature(body, label):
    if body is None:
        fail(f"{label}: missing '## Signature' section")
    m = re.search(r"^Slug:\s*([a-z0-9-]+)\s*$", body, re.MULTILINE)
    if not m:
        fail(f"{label}: Signature section must have a 'Slug: <kebab-slug>' line")
    slug = m.group(1)
    desc = body[m.end():].strip()
    if len(desc) < 15:
        fail(f"{label}: Signature section is missing a description")
    return {"slug": slug, "desc": desc}


def parse_plan(text, label):
    return {
        "colors": parse_colors(section(text, "Color"), label),
        "types": parse_types(section(text, "Type"), label),
        "layout": parse_layout(section(text, "Layout"), label),
        "signature": parse_signature(section(text, "Signature"), label),
    }


def parse_critique(text):
    verdicts = {}
    for axis in AXES:
        m = re.search(
            rf"^-\s*{axis}\s*:\s*(KEEP|REVISE)\s*[—\-]\s*(.+)$", text, re.MULTILINE
        )
        if not m:
            fail(
                f"critique.md: missing a '- {axis}: KEEP|REVISE — <reason>' line"
            )
        verdict, reason = m.group(1), m.group(2).strip()
        if len(reason) < 20:
            fail(f"critique.md: {axis} reason is too short to be a real justification")
        verdicts[axis] = {"verdict": verdict, "reason": reason}
    if not any(v["verdict"] == "REVISE" for v in verdicts.values()):
        fail("critique.md: at least one axis must be marked REVISE")
    return verdicts


def color_set(colors):
    return set(hexval for _, hexval in colors)


def type_tuple(types):
    return tuple(sorted((role, font.lower()) for role, font in types.items()))


def check_axis_consistency(verdicts, initial, final):
    c = verdicts["Color"]["verdict"]
    same_colors = color_set(initial["colors"]) == color_set(final["colors"])
    if c == "KEEP" and not same_colors:
        fail("final-plan.md: Color marked KEEP but palette differs from initial-plan.md")
    if c == "REVISE" and same_colors:
        fail("final-plan.md: Color marked REVISE but palette is identical to initial-plan.md")

    t = verdicts["Type"]["verdict"]
    same_types = type_tuple(initial["types"]) == type_tuple(final["types"])
    if t == "KEEP" and not same_types:
        fail("final-plan.md: Type marked KEEP but fonts differ from initial-plan.md")
    if t == "REVISE" and same_types:
        fail("final-plan.md: Type marked REVISE but fonts are identical to initial-plan.md")

    lay = verdicts["Layout"]["verdict"]
    same_layout = initial["layout"]["wireframe"] == final["layout"]["wireframe"]
    if lay == "KEEP" and not same_layout:
        fail("final-plan.md: Layout marked KEEP but wireframe differs from initial-plan.md")
    if lay == "REVISE" and same_layout:
        fail("final-plan.md: Layout marked REVISE but wireframe is identical to initial-plan.md")

    sig = verdicts["Signature"]["verdict"]
    same_slug = initial["signature"]["slug"] == final["signature"]["slug"]
    if sig == "KEEP" and not same_slug:
        fail("final-plan.md: Signature marked KEEP but slug differs from initial-plan.md")
    if sig == "REVISE" and same_slug:
        fail("final-plan.md: Signature marked REVISE but slug is identical to initial-plan.md")


def check_build(final):
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        fail("bs4 not available in grading environment")

    html = read("index.html")
    css = read("styles.css")
    soup = BeautifulSoup(html, "lxml")

    if not soup.find("html") or not soup.find("head") or not soup.find("body"):
        fail("index.html: must be a full document with html/head/body")

    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        fail("index.html: missing a viewport meta tag")

    link = soup.find("link", attrs={"rel": "stylesheet"})
    if not link or "styles.css" not in (link.get("href") or ""):
        fail("index.html: must link styles.css as a stylesheet")

    if not soup.find(["h1", "h2"]):
        fail("index.html: missing a heading")

    slug = final["signature"]["slug"]
    sig_el = soup.find(attrs={"data-signature": slug})
    if not sig_el:
        fail(f"index.html: no element has data-signature=\"{slug}\" matching final-plan.md")

    visible_text = soup.get_text(" ", strip=True)
    lower_text = visible_text.lower()
    for fact in ["aria", "9 bar", "walnut"]:
        if fact not in lower_text:
            fail(f"index.html: page copy must mention '{fact}' from the brief")

    for banned in ["lorem ipsum", "placeholder text"]:
        if banned in lower_text:
            fail(f"index.html: contains placeholder text ('{banned}')")
    if re.search(r"\btodo\b", lower_text):
        fail("index.html: contains a TODO placeholder")

    has_mailto = bool(soup.find("a", href=re.compile(r"^mailto:")))
    has_form = bool(soup.find("form"))
    if not (has_mailto or has_form):
        fail("index.html: no waitlist form or mailto link found")

    final_hexes = color_set(final["colors"])
    css_hexes = set(h.lower() for h in re.findall(r"#([0-9A-Fa-f]{6})\b", css))
    overlap = final_hexes & css_hexes
    needed = -(-len(final_hexes) // 2)  # ceil(n/2)
    if len(overlap) < needed:
        fail(
            "styles.css: must use most of final-plan.md's palette hex codes "
            f"(found {len(overlap)}/{len(final_hexes)})"
        )

    css_lower = css.lower()
    for role in ("Display", "Body"):
        font = final["types"][role].lower()
        if font not in css_lower:
            fail(f"styles.css: does not reference the {role} font '{final['types'][role]}'")

    if "@media" not in css:
        fail("styles.css: missing a responsive @media breakpoint")

    if not re.search(r":focus(-visible)?", css):
        fail("styles.css: missing a visible :focus rule")

    return visible_text


def main():
    for f in REQUIRED_FILES:
        if not (WORKSPACE / f).exists():
            fail(f"missing required file: {f}")

    initial_text = read("design/initial-plan.md")
    critique_text = read("design/critique.md")
    final_text = read("design/final-plan.md")

    initial = parse_plan(initial_text, "initial-plan.md")
    verdicts = parse_critique(critique_text)
    final = parse_plan(final_text, "final-plan.md")

    check_axis_consistency(verdicts, initial, final)
    visible_text = check_build(final)

    answers_path = JUDGE_DIR / "answers.json"
    if answers_path.exists():
        answers = json.loads(answers_path.read_text()).get("answers", {})
        if not answers.get("q1") or not answers.get("q2"):
            fail("judge determined the critique reasoning or page copy is not substantive")
        print("PASS")
        sys.exit(0)

    revise_reasons = " | ".join(
        f"{axis}: {v['reason']}" for axis, v in verdicts.items() if v["verdict"] == "REVISE"
    )
    product_context = (
        "Product context: a fully manual, spring-lever espresso machine (no pump, "
        "no PID controller) with brushed brass fittings, a matte black steel body, "
        "a walnut lever handle, and 9 bar of pressure produced by hand."
    )

    questions = {
        "questions": [
            {
                "id": "q1",
                "question": (
                    f"{product_context} A designer revised part of their initial plan "
                    "and gave the following reasons. For EVERY reason listed, does it "
                    "identify a specific, non-generic replacement that is clearly "
                    "motivated by this particular product (its mechanism, materials, "
                    "or audience), rather than an arbitrary, cosmetic, or unrelated "
                    f"tweak? Reasons: {revise_reasons}"
                ),
            },
            {
                "id": "q2",
                "question": (
                    f"{product_context} Does the following webpage copy read as "
                    "specific to this particular product (using its concrete "
                    "mechanism, materials, price, or process) rather than generic, "
                    "interchangeable marketing filler that could describe almost any "
                    f"premium gadget? Copy: {visible_text}"
                ),
            },
        ]
    }
    JUDGE_DIR.mkdir(parents=True, exist_ok=True)
    (JUDGE_DIR / "questions.json").write_text(json.dumps(questions, indent=2))
    sys.exit(3)


if __name__ == "__main__":
    main()
