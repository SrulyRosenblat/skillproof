#!/usr/bin/env python3
"""Grader for bench_01_frontend-design.

Checks that the agent (1) pinned a concrete subject/audience/primary-job for
an intentionally underspecified subscription brief, and (2) built a landing
page whose actual copy is grounded in that stated subject rather than being
generic, templated, or placeholder text.
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

NOTES_PATH = WORKSPACE / "design-notes.md"
HTML_PATH = WORKSPACE / "index.html"

FIELD_PATTERNS = [
    ("subject", r"^Subject:\s*(.+)$"),
    ("audience", r"^Audience:\s*(.+)$"),
    ("primary_job", r"^Primary job:\s*(.+)$"),
]

BANNED_GENERIC_SUBJECT = {
    "a subscription service",
    "a subscription offering",
    "our product",
    "our service",
    "this product",
    "your product",
    "an app",
    "a platform",
    "a service",
    "something recurring",
    "a box of stuff",
    "a subscription",
    "a subscription box",
}

BANNED_PLACEHOLDER_TEXT = [
    "lorem ipsum",
    "company name",
    "product name",
    "insert text here",
    "your company",
    "placeholder text",
    "coming soon",
]

STOPWORDS = set(
    """
    a an the of for and or that this with from your our their there its its
    to in on is are be one each every someone people who what than more
    rather instead who's whos season each month monthly recurring day days
    subscription subscriptions service services product products box boxes
    like into over under about into onto brand new real thing things kind
    directly along
    """.split()
)


def fail(msg: str):
    print(f"FAIL: {msg}")
    sys.exit(1)


def load_required_files():
    if not NOTES_PATH.exists():
        fail("design-notes.md is missing from /workspace")
    if not HTML_PATH.exists():
        fail("index.html is missing from /workspace")
    notes_text = NOTES_PATH.read_text(encoding="utf-8")
    html_text = HTML_PATH.read_text(encoding="utf-8")
    return notes_text, html_text


def parse_fields(notes_text: str):
    non_empty_lines = [l.rstrip() for l in notes_text.splitlines() if l.strip()]
    if len(non_empty_lines) < 3:
        fail("design-notes.md must have at least 3 non-empty lines (Subject/Audience/Primary job)")

    fields = {}
    for (key, pattern), line in zip(FIELD_PATTERNS, non_empty_lines[:3]):
        m = re.match(pattern, line)
        if not m:
            fail(
                f"design-notes.md line {line!r} does not match the required "
                f"'{key}' format (expected the first 3 lines to be exactly "
                "'Subject: ...', 'Audience: ...', 'Primary job: ...' in order)"
            )
        value = m.group(1).strip()
        if not value:
            fail(f"'{key}' field in design-notes.md is empty")
        fields[key] = value
    return fields


def check_field_lengths(fields):
    for key, value in fields.items():
        word_count = len(value.split())
        if word_count < 6:
            fail(f"'{key}' field is too short ({word_count} words): {value!r}")


def check_subject_not_generic_stub(subject: str):
    normalized = subject.strip().strip(".").lower()
    if normalized in BANNED_GENERIC_SUBJECT:
        fail(f"Subject field is just a generic placeholder phrase: {subject!r}")


def significant_words(text: str):
    words = re.findall(r"[a-z']+", text.lower())
    return [w for w in words if len(w) > 3 and w not in STOPWORDS]


def parse_html(html_text: str):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_text, "lxml")
    if soup.find("html") is None:
        fail("index.html has no <html> element")
    if soup.find("head") is None:
        fail("index.html has no <head> element")
    body = soup.find("body")
    if body is None:
        fail("index.html has no <body> element")
    title = soup.find("title")
    if title is None or not title.get_text(strip=True):
        fail("index.html is missing a non-empty <title>")
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport is None:
        fail("index.html is missing a <meta name='viewport'> tag")
    h1s = soup.find_all("h1")
    if len(h1s) != 1:
        fail(f"index.html must have exactly one <h1>, found {len(h1s)}")

    body_text = body.get_text(separator=" ")
    return soup, body_text


def check_body_length(body_text: str):
    words = re.findall(r"[A-Za-z']+", body_text)
    if len(words) < 300:
        fail(f"index.html body text is too short ({len(words)} words, need >= 300)")


def check_no_placeholder_text(html_text: str):
    lower_html = html_text.lower()
    for phrase in BANNED_PLACEHOLDER_TEXT:
        if phrase in lower_html:
            fail(f"index.html contains banned placeholder text: {phrase!r}")
    if re.search(r"\[[a-zA-Z][a-zA-Z '-]{1,40}\]", html_text):
        fail("index.html contains bracketed placeholder text like '[your product]'")


def check_subject_grounding(subject: str, body_text: str):
    subj_words = significant_words(subject)
    if len(subj_words) < 4:
        fail(
            "Subject field does not contain enough concrete, specific detail "
            f"after removing generic subscription language (only found {subj_words!r})"
        )
    body_lower = body_text.lower()
    hits = sorted({w for w in subj_words if w in body_lower})
    if len(hits) < 3:
        fail(
            "index.html body text does not reflect the Subject stated in "
            f"design-notes.md (only matched {hits} of the specific words in "
            f"the Subject field: {sorted(set(subj_words))})"
        )
    return hits


def run_deterministic_checks():
    notes_text, html_text = load_required_files()
    fields = parse_fields(notes_text)
    check_field_lengths(fields)
    check_subject_not_generic_stub(fields["subject"])
    soup, body_text = parse_html(html_text)
    check_body_length(body_text)
    check_no_placeholder_text(html_text)
    check_subject_grounding(fields["subject"], body_text)
    print("Deterministic checks passed.")
    return fields, body_text


def ask_judge(fields, body_text):
    JUDGE_DIR.mkdir(exist_ok=True)
    truncated_body = body_text.strip()
    if len(truncated_body) > 6000:
        truncated_body = truncated_body[:6000]

    questions = [
        {
            "id": "subject_specific",
            "question": (
                "The following text is the 'Subject' field from a landing "
                "page's design notes, meant to describe one specific, "
                "concrete subscription product. Does it name a genuinely "
                "specific product (with concrete distinguishing detail, "
                "such as a particular source, method, or form the item "
                "takes) rather than a generic category like 'a subscription "
                "box', 'an app', or 'a monthly service'? Answer yes only if "
                "it is genuinely specific."
            ),
            "text": fields["subject"],
        },
        {
            "id": "audience_specific",
            "question": (
                "The following text is the 'Audience' field from a landing "
                "page's design notes. Does it describe a specific, "
                "identifiable group of people (defined by a real behavior, "
                "habit, or situation) rather than a generic audience like "
                "'everyone', 'busy professionals', or 'people who like this "
                "kind of thing'? Answer yes only if it is genuinely specific."
            ),
            "text": fields["audience"],
        },
        {
            "id": "copy_grounded_in_subject",
            "question": (
                "The following text is the visible body copy of a landing "
                "page. The page is supposed to be for this specific "
                f"product: \"{fields['subject']}\". Does the page's copy "
                "consistently write about that particular product using "
                "specific, concrete details (rather than generic marketing "
                "language that could describe almost any subscription "
                "product) across most of its sections, not just the "
                "headline? Answer yes only if the specificity holds "
                "throughout most of the page."
            ),
            "text": truncated_body,
        },
    ]
    QUESTIONS_PATH.write_text(json.dumps({"questions": questions}, indent=2), encoding="utf-8")
    print("Wrote judge questions; awaiting answers.")
    sys.exit(3)


def evaluate_judge_answers():
    answers = json.loads(ANSWERS_PATH.read_text(encoding="utf-8")).get("answers", {})
    required_ids = ["subject_specific", "audience_specific", "copy_grounded_in_subject"]
    for qid in required_ids:
        if qid not in answers:
            fail(f"missing judge answer for {qid!r}")
        if answers[qid] is not True:
            fail(f"judge answered 'no' (or non-true) for {qid!r}")
    print("Judge checks passed.")
    sys.exit(0)


def main():
    fields, body_text = run_deterministic_checks()
    if ANSWERS_PATH.exists():
        evaluate_judge_answers()
    else:
        ask_judge(fields, body_text)


if __name__ == "__main__":
    main()
