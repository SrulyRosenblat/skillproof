#!/usr/bin/env python3
"""Grader for bench_04_restraint-and-self-critique.

The fixture (draft.html) is a deliberately over-decorated homepage: five
competing attention-grabbing effects, a fixed-width desktop-only layout, a
blanket `outline: none`, and infinite CSS animations with no
prefers-reduced-motion handling. The task asks the agent to cut it down to one
signature moment, fix the quality-floor bugs, and document the changes.

This grader checks (deterministically):
  1. index.html and CHANGES.md exist.
  2. The real facts from the draft survive into index.html's visible text.
  3. Exactly one element carries data-signature="true", and it has an id.
  4. At most one of the draft's five decorative features is still present.
  5. The specific fixed-width bug is gone and a mobile breakpoint exists.
  6. The blanket outline-removal bug is gone and a real focus-visible
     indicator exists.
  7. Any remaining looping animation is neutralized under
     prefers-reduced-motion: reduce.
  8. CHANGES.md substantively names what was removed/kept and what
     accessibility fixes were made.
Then it asks an LLM judge two qualitative questions about restraint and about
the specificity of CHANGES.md.
"""
import json
import os
import re
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("BENCH_WORKSPACE", "/workspace"))
JUDGE_DIR = WORKSPACE / ".judge"
QUESTIONS_PATH = JUDGE_DIR / "questions.json"
ANSWERS_PATH = JUDGE_DIR / "answers.json"

DRAFT_PATH = WORKSPACE / "draft.html"
HTML_PATH = WORKSPACE / "index.html"
CHANGES_PATH = WORKSPACE / "CHANGES.md"

DECOR_CLASSES = [
    "bounce-logo",
    "glow-pulse-cta",
    "ticker-marquee",
    "confetti-burst",
    "rainbow-bg",
]

BANNED_FILLER = [
    "lorem ipsum",
    "tbd",
    "n/a",
    "placeholder text",
    "your text here",
    "insert text here",
]

REMOVED_EFFECT_KEYWORDS = {
    "bounce": ["bounce", "bouncing"],
    "glow": ["glow", "pulse", "pulsing", "pulsed"],
    "ticker": ["ticker", "marquee", "scroll"],
    "confetti": ["confetti"],
    "rainbow": ["rainbow"],
}

QUALITY_FLOOR_KEYWORDS = {
    "mobile": ["mobile", "phone", "responsive", "viewport"],
    "focus": ["focus", "keyboard"],
    "motion": ["motion", "reduced motion", "reduce motion", "animation"],
}


def fail(msg: str):
    print(f"FAIL: {msg}")
    sys.exit(1)


def load_files():
    if not DRAFT_PATH.exists():
        fail("draft.html is missing from /workspace (the input fixture was removed)")
    if not HTML_PATH.exists():
        fail("index.html is missing from /workspace")
    if not CHANGES_PATH.exists():
        fail("CHANGES.md is missing from /workspace")
    html_text = HTML_PATH.read_text(encoding="utf-8")
    changes_text = CHANGES_PATH.read_text(encoding="utf-8")
    return html_text, changes_text


def parse_html(html_text: str):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_text, "lxml")
    if soup.find("html") is None:
        fail("index.html has no <html> element")
    if soup.find("head") is None:
        fail("index.html has no <head> element")
    if soup.find("body") is None:
        fail("index.html has no <body> element")
    return soup


def get_css_text(soup) -> str:
    style_tags = soup.find_all("style")
    css_text = "\n".join(tag.get_text() for tag in style_tags)
    if not css_text.strip():
        fail("index.html has no inline <style> content to read CSS from")
    return css_text


def check_facts_preserved(soup):
    body_text = soup.get_text(" ", strip=True)
    lower = body_text.lower()
    if "warble press" not in lower:
        fail("index.html no longer mentions the company name 'Warble Press'")
    if "2016" not in body_text:
        fail("index.html no longer states the founding year (2016)")
    if not re.search(r"\b500\b", body_text):
        fail("index.html no longer states the daily press capacity (500)")
    if not re.search(r"6[\s-]*week", lower):
        fail("index.html no longer states the turnaround time (6-week / 6 week)")
    if not re.search(r"\b100\b", body_text):
        fail("index.html no longer states the minimum order size (100)")


def check_viewport(soup):
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport is None or "width=device-width" not in (viewport.get("content") or ""):
        fail("index.html is missing a <meta name='viewport' content='width=device-width...'> tag")


def check_signature(soup):
    matches = soup.find_all(attrs={"data-signature": "true"})
    if len(matches) == 0:
        fail("no element in index.html has data-signature=\"true\"")
    if len(matches) > 1:
        fail(f"more than one element has data-signature=\"true\" ({len(matches)} found); exactly one is required")
    sig = matches[0]
    sig_id = sig.get("id")
    if not sig_id or not sig_id.strip():
        fail("the data-signature=\"true\" element must also have a non-empty id attribute")
    return sig, sig_id.strip()


def check_decor_removed(soup):
    remaining = []
    for cls in DECOR_CLASSES:
        if soup.find(class_=cls) is not None:
            remaining.append(cls)
    if len(remaining) > 1:
        fail(
            "too many of the draft's original decorative effects are still present "
            f"({remaining}); at most one of the five may remain"
        )
    return remaining


def check_no_fixed_width_bug(css_text: str):
    if re.search(r"width\s*:\s*1200px", css_text, re.IGNORECASE):
        fail("index.html's CSS still hardcodes the draft's fixed width:1200px layout bug")
    breakpoints = re.findall(r"@media[^{]*max-width\s*:\s*(\d+)px", css_text, re.IGNORECASE)
    if not any(int(bp) <= 768 for bp in breakpoints):
        fail("index.html's CSS has no @media rule with a mobile breakpoint (max-width <= 600px)")


def check_focus(css_text: str):
    if re.search(r"\*\s*:\s*focus\s*\{[^}]*outline\s*:\s*(none|0)\b", css_text, re.IGNORECASE):
        fail("index.html's CSS still contains the draft's blanket '*:focus { outline: none }' rule")

    rule_re = re.compile(r"([^{}]+)\{([^{}]*)\}")
    has_visible_focus = False
    for selector_group, body in rule_re.findall(css_text):
        if ":focus" not in selector_group.lower():
            continue
        outline_m = re.search(r"outline(?:-\w+)?\s*:\s*([^;]+)", body, re.IGNORECASE)
        shadow_m = re.search(r"box-shadow\s*:\s*([^;]+)", body, re.IGNORECASE)
        border_m = re.search(r"border(?:-\w+)?\s*:\s*([^;]+)", body, re.IGNORECASE)
        for m in (outline_m, shadow_m, border_m):
            if m is None:
                continue
            value = m.group(1).strip().lower()
            if value not in ("none", "0", "0px") :
                has_visible_focus = True
    if not has_visible_focus:
        fail(
            "index.html's CSS has no ':focus' / ':focus-visible' rule that sets a visible "
            "outline, box-shadow, or border (a real replacement for the removed default outline)"
        )


def extract_media_block(css_text: str, marker: str):
    """Return the body of the first @media block whose prelude contains `marker`, or None."""
    idx = css_text.lower().find("@media")
    while idx != -1:
        brace_idx = css_text.find("{", idx)
        if brace_idx == -1:
            break
        prelude = css_text[idx:brace_idx]
        if marker.lower() in prelude.lower():
            depth = 1
            pos = brace_idx + 1
            start = pos
            while pos < len(css_text) and depth > 0:
                if css_text[pos] == "{":
                    depth += 1
                elif css_text[pos] == "}":
                    depth -= 1
                pos += 1
            return css_text[start:pos - 1]
        idx = css_text.lower().find("@media", brace_idx)
    return None


def check_reduced_motion(css_text: str):
    keyframes = re.findall(r"@keyframes\s+([\w-]+)", css_text, re.IGNORECASE)
    animated = bool(re.search(r"animation(?:-name)?\s*:\s*(?!none\b)[\w-]", css_text, re.IGNORECASE))
    if not keyframes and not animated:
        return  # nothing looping left; reduced-motion handling isn't required

    block = extract_media_block(css_text, "prefers-reduced-motion")
    if block is None:
        fail(
            "index.html keeps a looping CSS animation but has no "
            "@media (prefers-reduced-motion: reduce) block to neutralize it"
        )
    if not re.search(r"(animation|transition)", block, re.IGNORECASE):
        fail(
            "the prefers-reduced-motion media query in index.html doesn't actually "
            "reference animation/transition to turn the motion off"
        )


def check_changes_md(changes_text: str, sig_id: str):
    lower = changes_text.lower()
    for phrase in BANNED_FILLER:
        if phrase in lower:
            fail(f"CHANGES.md contains banned filler text: {phrase!r}")

    word_count = len(changes_text.split())
    if word_count < 60:
        fail(f"CHANGES.md is too short ({word_count} words) to substantively explain the revision")

    if sig_id.lower() not in lower:
        fail(f"CHANGES.md never mentions the signature element's id ({sig_id!r})")

    matched_effects = [name for name, kws in REMOVED_EFFECT_KEYWORDS.items() if any(kw in lower for kw in kws)]
    if len(matched_effects) < 3:
        fail(
            "CHANGES.md doesn't name at least 3 of the draft's original effects "
            f"(bounce/glow/ticker/confetti/rainbow) it removed or kept; found: {matched_effects}"
        )

    matched_floor = [name for name, kws in QUALITY_FLOOR_KEYWORDS.items() if any(kw in lower for kw in kws)]
    if len(matched_floor) < 2:
        fail(
            "CHANGES.md doesn't describe at least 2 of the mobile/focus/motion fixes it made; "
            f"found: {matched_floor}"
        )


def run_deterministic_checks():
    html_text, changes_text = load_files()
    soup = parse_html(html_text)
    check_facts_preserved(soup)
    check_viewport(soup)
    sig, sig_id = check_signature(soup)
    check_decor_removed(soup)
    css_text = get_css_text(soup)
    check_no_fixed_width_bug(css_text)
    check_focus(css_text)
    check_reduced_motion(css_text)
    check_changes_md(changes_text, sig_id)
    print("Deterministic checks passed.")
    return html_text, changes_text, sig_id


def ask_judge(html_text: str, changes_text: str):
    JUDGE_DIR.mkdir(exist_ok=True)

    page_source = html_text
    if len(page_source) > 8000:
        page_source = page_source[:8000]

    changes_source = changes_text
    if len(changes_source) > 4000:
        changes_source = changes_source[:4000]

    questions = [
        {
            "id": "one_signature_rest_calm",
            "question": (
                "Below is the full HTML and inline CSS source of a homepage. "
                "Reading it as a whole page (imagine how it would render), does it "
                "read as having exactly ONE clear bold or attention-grabbing visual "
                "moment, with everything else on the page (colors, type, other "
                "elements) staying calm, quiet, and disciplined rather than "
                "competing for attention? Answer yes only if there is a single "
                "standout moment and the rest is genuinely restrained, not if "
                "there are still multiple flashy or heavily animated elements, "
                "and not if the page has been made so plain that there is no "
                "standout moment at all."
            ),
            "text": page_source,
        },
        {
            "id": "changes_specific",
            "question": (
                "Below is a changelog written by a designer explaining a revision "
                "to a homepage draft for Warble Press, an independent vinyl record "
                "pressing plant. Does the changelog give specific, concrete "
                "reasoning tied to this particular draft and this particular "
                "business (e.g. referring to actual effects that were removed, or "
                "explaining why the specific element that was kept fits this "
                "business), rather than generic boilerplate that could describe "
                "cutting down almost any website ('we simplified the design and "
                "improved accessibility')?"
            ),
            "text": changes_source,
        },
    ]
    QUESTIONS_PATH.write_text(json.dumps({"questions": questions}, indent=2), encoding="utf-8")
    print("Wrote judge questions; awaiting answers.")
    sys.exit(3)


def evaluate_judge_answers():
    answers = json.loads(ANSWERS_PATH.read_text(encoding="utf-8")).get("answers", {})
    required_ids = ["one_signature_rest_calm", "changes_specific"]
    for qid in required_ids:
        if qid not in answers:
            fail(f"missing judge answer for {qid!r}")
        if answers[qid] is not True:
            fail(f"judge answered 'no' (or non-true) for {qid!r}")
    print("Judge checks passed.")
    sys.exit(0)


def main():
    html_text, changes_text, _sig_id = run_deterministic_checks()
    if ANSWERS_PATH.exists():
        evaluate_judge_answers()
    else:
        ask_judge(html_text, changes_text)


if __name__ == "__main__":
    main()
