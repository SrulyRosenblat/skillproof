#!/usr/bin/env python3
"""Grader for bench_02_design-principles.

Checks that the agent built the Ember & Ash product page in a way that
reflects three "design principles" behaviors:
  1. The hero is grounded in the brand (not generic filler).
  2. Headings and body copy use two distinct, specific font choices rather
     than one generic stack or a lazy default keyword.
  3. The three sauces - which the fixture explicitly says are NOT a ranked
     sequence, set, or flight - are not labeled with sequence/step/ordinal
     markers (01/02/03, Step 1, First/Second/Third, etc).
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

BRIEF_PATH = WORKSPACE / "brand-brief.json"
NOTES_PATH = WORKSPACE / "design-notes.md"
HTML_PATH = WORKSPACE / "index.html"

NOTE_FIELD_PATTERNS = [
    ("hero", r"^Hero:\s*(.+)$"),
    ("typography", r"^Typography:\s*(.+)$"),
    ("structure", r"^Structure:\s*(.+)$"),
]

BANNED_PLACEHOLDER_TEXT = [
    "lorem ipsum",
    "product name",
    "insert text here",
    "placeholder text",
    "your text here",
]

GENERIC_FONT_KEYWORDS = {
    "serif",
    "sans-serif",
    "monospace",
    "cursive",
    "fantasy",
    "system-ui",
    "ui-serif",
    "ui-sans-serif",
    "ui-monospace",
    "ui-rounded",
    "math",
    "emoji",
    "fangsong",
    "inherit",
    "initial",
    "unset",
}

SEQUENCE_MARKER_RE = re.compile(
    r"^("
    r"0?[1-3]"
    r"|i{1,3}"
    r"|1st|2nd|3rd"
    r"|first|second|third"
    r"|step\s*(1|2|3|one|two|three)"
    r"|part\s*(1|2|3|one|two|three)"
    r"|no\.?\s*(1|2|3)"
    r"|number\s*(1|2|3)"
    r")$",
    re.IGNORECASE,
)


def fail(msg: str):
    print(f"FAIL: {msg}")
    sys.exit(1)


def load_files():
    if not BRIEF_PATH.exists():
        fail("brand-brief.json is missing from /workspace (fixture was removed)")
    if not NOTES_PATH.exists():
        fail("design-notes.md is missing from /workspace")
    if not HTML_PATH.exists():
        fail("index.html is missing from /workspace")
    brief = json.loads(BRIEF_PATH.read_text(encoding="utf-8"))
    notes_text = NOTES_PATH.read_text(encoding="utf-8")
    html_text = HTML_PATH.read_text(encoding="utf-8")
    return brief, notes_text, html_text


def parse_notes_fields(notes_text: str):
    non_empty_lines = [l.rstrip() for l in notes_text.splitlines() if l.strip()]
    if len(non_empty_lines) < 3:
        fail("design-notes.md must have at least 3 non-empty lines (Hero/Typography/Structure)")

    fields = {}
    for (key, pattern), line in zip(NOTE_FIELD_PATTERNS, non_empty_lines[:3]):
        m = re.match(pattern, line)
        if not m:
            fail(
                f"design-notes.md line {line!r} does not match the required "
                f"'{key}' format (expected the first 3 lines to be exactly "
                "'Hero: ...', 'Typography: ...', 'Structure: ...' in order)"
            )
        value = m.group(1).strip()
        word_count = len(value.split())
        if word_count < 6:
            fail(f"'{key}' field in design-notes.md is too short ({word_count} words): {value!r}")
        fields[key] = value
    return fields


def parse_html(html_text: str):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_text, "lxml")
    if soup.find("html") is None:
        fail("index.html has no <html> element")
    head = soup.find("head")
    if head is None:
        fail("index.html has no <head> element")
    title = soup.find("title")
    if title is None or not title.get_text(strip=True):
        fail("index.html is missing a non-empty <title>")
    return soup


def check_no_placeholder_text(html_text: str):
    lower_html = html_text.lower()
    for phrase in BANNED_PLACEHOLDER_TEXT:
        if phrase in lower_html:
            fail(f"index.html contains banned placeholder text: {phrase!r}")
    if re.search(r"\[[a-zA-Z][a-zA-Z '-]{1,40}\]", html_text):
        fail("index.html contains bracketed placeholder text like '[your text here]'")


def check_hero(soup, brand: str):
    hero = soup.find(id="hero")
    if hero is None:
        fail("index.html has no element with id='hero'")
    h1s = hero.find_all("h1")
    if len(h1s) != 1:
        fail(f"the #hero element must contain exactly one <h1>, found {len(h1s)}")
    h1_text = h1s[0].get_text(" ", strip=True)
    brand_tokens = [t for t in re.split(r"[^A-Za-z0-9]+", brand) if len(t) > 1]
    missing = [t for t in brand_tokens if t.lower() not in h1_text.lower()]
    if missing:
        fail(
            f"the <h1> inside #hero ({h1_text!r}) does not include the brand "
            f"name {brand!r} (missing tokens: {missing})"
        )
    return hero, h1_text


def check_flavor_cards(soup, sauces):
    cards = soup.find_all(class_="flavor-card")
    if len(cards) != 3:
        fail(f"index.html must contain exactly 3 elements with class='flavor-card', found {len(cards)}")

    unmatched_sauces = list(sauces)
    card_info = []
    for card in cards:
        card_text = card.get_text(" ", strip=True)
        matches = [s for s in sauces if s["name"].lower() in card_text.lower()]
        if len(matches) == 0:
            fail(f"a flavor-card's text does not name any sauce from brand-brief.json: {card_text[:120]!r}")
        if len(matches) > 1:
            fail(
                "a flavor-card's text names more than one sauce, cards must be "
                f"one-per-sauce: {card_text[:120]!r}"
            )
        sauce = matches[0]

        if sauce["heat_label"].lower() not in card_text.lower():
            fail(f"the {sauce['name']} flavor-card does not state its heat_label ({sauce['heat_label']!r})")

        normalized_card = re.sub(r"[,\s]", "", card_text).lower()
        normalized_scoville_digits = re.sub(r"[^0-9]", "", sauce["scoville"])
        if normalized_scoville_digits not in normalized_card:
            fail(f"the {sauce['name']} flavor-card does not state its scoville rating ({sauce['scoville']!r})")
        if "shu" not in card_text.lower():
            fail(f"the {sauce['name']} flavor-card does not include the SHU unit for its scoville rating")

        p_tags = card.find_all("p")
        if not any(len(p.get_text(strip=True)) > 15 for p in p_tags):
            fail(f"the {sauce['name']} flavor-card has no <p> element with its notes copy")

        card_info.append((sauce, card, card_text))
        if sauce in unmatched_sauces:
            unmatched_sauces.remove(sauce)

    if unmatched_sauces:
        names = [s["name"] for s in unmatched_sauces]
        fail(f"these sauces from brand-brief.json are missing from the page's flavor-cards: {names}")

    return card_info


def check_no_sequence_markers(card_info):
    for sauce, card, _card_text in card_info:
        for piece in card.stripped_strings:
            if SEQUENCE_MARKER_RE.match(piece.strip()):
                fail(
                    f"the {sauce['name']} flavor-card contains a sequence/step marker "
                    f"({piece.strip()!r}), but brand-brief.json states the three sauces "
                    "are not sold as a ranked set or in any particular order"
                )


def base_tag_of_selector_token(token: str):
    token = token.strip()
    if not token:
        return None
    last = re.split(r"[\s>+~]+", token)[-1]
    m = re.match(r"^[a-zA-Z][a-zA-Z0-9-]*", last)
    return m.group(0).lower() if m else None


def extract_font_family(declarations: str):
    m = re.search(r"font-family\s*:\s*([^;}}]+)", declarations, re.IGNORECASE)
    if not m:
        return None
    value = m.group(1).strip().rstrip(";").strip()
    first = value.split(",")[0].strip().strip("'\"")
    return first, value


def check_typography(html_text: str):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_text, "lxml")
    style_tags = soup.find_all("style")
    css_text = "\n".join(tag.get_text() for tag in style_tags)
    if not css_text.strip():
        fail("index.html has no inline <style> content to read font-family declarations from")

    rule_re = re.compile(r"([^{}]+)\{([^{}]*)\}")
    h1_font = None
    p_font = None
    for selector_group, body in rule_re.findall(css_text):
        if "font-family" not in body.lower():
            continue
        extracted = extract_font_family(body)
        if extracted is None:
            continue
        first_font, _full_value = extracted
        for token in selector_group.split(","):
            base = base_tag_of_selector_token(token)
            if base == "h1":
                h1_font = (first_font, _full_value)
            elif base == "p":
                p_font = (first_font, _full_value)

    if h1_font is None:
        fail("no CSS rule sets font-family for h1 (directly or via a selector ending in h1)")
    if p_font is None:
        fail("no CSS rule sets font-family for p (directly or via a selector ending in p)")

    if h1_font[0].lower() in GENERIC_FONT_KEYWORDS:
        fail(f"the h1 font-family's first font is just a generic keyword: {h1_font[1]!r}")
    if p_font[0].lower() in GENERIC_FONT_KEYWORDS:
        fail(f"the p font-family's first font is just a generic keyword: {p_font[1]!r}")

    if h1_font[0].strip().lower() == p_font[0].strip().lower():
        fail(
            "the h1 and p font-family declarations use the same primary font "
            f"({h1_font[0]!r}); headings and body copy must use distinct fonts"
        )

    return h1_font, p_font


def run_deterministic_checks():
    brief, notes_text, html_text = load_files()
    notes_fields = parse_notes_fields(notes_text)
    check_no_placeholder_text(html_text)
    soup = parse_html(html_text)
    hero, h1_text = check_hero(soup, brief["brand"])
    card_info = check_flavor_cards(soup, brief["sauces"])
    check_no_sequence_markers(card_info)
    h1_font, p_font = check_typography(html_text)
    print("Deterministic checks passed.")
    return brief, notes_fields, hero, h1_text, card_info, h1_font, p_font


def ask_judge(brief, notes_fields, hero, h1_text, card_info):
    JUDGE_DIR.mkdir(exist_ok=True)
    hero_text = hero.get_text(" ", strip=True)

    card_snippets = []
    for sauce, card, _card_text in card_info:
        snippet = str(card)
        if len(snippet) > 1200:
            snippet = snippet[:1200]
        card_snippets.append(f"--- card for {sauce['name']} ---\n{snippet}")
    cards_blob = "\n\n".join(card_snippets)
    if len(cards_blob) > 6000:
        cards_blob = cards_blob[:6000]

    typography_and_structure_notes = (
        f"Typography: {notes_fields['typography']}\n\nStructure: {notes_fields['structure']}"
    )

    questions = [
        {
            "id": "hero_specific",
            "question": (
                "The following is the full visible text of a hot sauce brand's "
                "website hero section. The brand (Ember & Ash) is a small, "
                "two-person operation that hand-bottles hot sauce in a "
                "converted shipping container. Does this hero text read as "
                "specific and evocative of this particular brand, rather "
                "than a generic tagline/headline that could equally describe "
                "almost any food or condiment brand? Answer yes only if it is "
                "genuinely specific to this brand."
            ),
            "text": hero_text,
        },
        {
            "id": "cards_meaningful_labels",
            "question": (
                "Below are the HTML snippets for three hot sauce product "
                "cards from the same page. These three sauces are explicitly "
                "not sold as a ranked set, flight, or sequence - customers "
                "pick whichever one matches the heat level they want. Setting "
                "aside plain sequence/step numbering (which has already been "
                "confirmed absent), do any structural labels, tags, or "
                "eyebrows attached to each card communicate real, specific "
                "information about that particular sauce (such as its heat "
                "character or flavor profile), rather than being purely "
                "decorative or interchangeable between the three cards? "
                "Answer yes only if the cards are differentiated by "
                "meaningful content, not just by name."
            ),
            "text": cards_blob,
        },
        {
            "id": "typography_rationale_specific",
            "question": (
                "The following are the 'Typography' and 'Structure' fields "
                "from a designer's rationale notes for the Ember & Ash hot "
                "sauce website described above. Does the Typography field "
                "explain a font pairing chosen for a reason specific to this "
                "rustic, small-batch, handmade hot sauce brand (rather than "
                "reciting generic best-practice advice about pairing a "
                "display font with a body font that could apply to any "
                "brand)? Answer yes only if the reasoning given is "
                "genuinely tied to this brand's particular character."
            ),
            "text": typography_and_structure_notes,
        },
    ]
    QUESTIONS_PATH.write_text(json.dumps({"questions": questions}, indent=2), encoding="utf-8")
    print("Wrote judge questions; awaiting answers.")
    sys.exit(3)


def evaluate_judge_answers():
    answers = json.loads(ANSWERS_PATH.read_text(encoding="utf-8")).get("answers", {})
    required_ids = ["hero_specific", "cards_meaningful_labels", "typography_rationale_specific"]
    for qid in required_ids:
        if qid not in answers:
            fail(f"missing judge answer for {qid!r}")
        if answers[qid] is not True:
            fail(f"judge answered 'no' (or non-true) for {qid!r}")
    print("Judge checks passed.")
    sys.exit(0)


def main():
    brief, notes_fields, hero, h1_text, card_info, h1_font, p_font = run_deterministic_checks()
    if ANSWERS_PATH.exists():
        evaluate_judge_answers()
    else:
        ask_judge(brief, notes_fields, hero, h1_text, card_info)


if __name__ == "__main__":
    main()
