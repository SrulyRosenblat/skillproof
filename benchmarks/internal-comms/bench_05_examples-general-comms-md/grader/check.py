import os
import re
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("BENCH_WORKSPACE", "/workspace"))
OUTPUT_FILE = WORKSPACE / "announcement.md"

DEADLINE = "august 14, 2026"

LINK_WIKI = "https://wiki.example-corp.internal/devportal-sso-migration"
LINK_SLACK = "https://example-corp.slack.com/channels/devportal-support"

# Facts that must be present somewhere, proving the real substance of the
# change was pulled from facts.md (case-insensitive).
MUST_INCLUDE_SUBSTRINGS = [
    "okta",
    "sso",
    DEADLINE,
    "q3",
]

# The required action must be described, in some phrasing, somewhere.
ACTION_PATTERNS = [r"re-?link"]

# The lockout consequence must be described somewhere.
CONSEQUENCE_PATTERNS = [r"lock(ed)?\s*-?\s*out", r"lose access"]

# Low-priority/irrelevant note from facts.md that should not be dragged in.
MUST_EXCLUDE_SUBSTRINGS = [
    "dark mode",
]

# Content unique to the style examples — copying these verbatim would mean
# the model parroted the examples instead of writing new, fact-based content.
MUST_NOT_COPY_SUBSTRINGS = [
    "eng-announcements",
    "duo",
    "vpn access",
    "infra team",
    "it security team",
]

BANNED_PLACEHOLDER_SUBSTRINGS = [
    "todo",
    "tbd",
    "insert link",
    "lorem ipsum",
    "[link]",
    "xxx",
]

MIN_WORDS = 40
MAX_WORDS = 220


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    if not OUTPUT_FILE.exists():
        fail(f"{OUTPUT_FILE} does not exist")

    raw = OUTPUT_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        fail(f"{OUTPUT_FILE} is empty")

    lower = raw.lower()

    # --- Length sanity (proxy for concise, but substantive) ---
    word_count = len(raw.split())
    if not (MIN_WORDS <= word_count <= MAX_WORDS):
        fail(
            f"expected roughly {MIN_WORDS}-{MAX_WORDS} words, found {word_count}"
        )

    # --- Substance: required facts present ---
    missing = [s for s in MUST_INCLUDE_SUBSTRINGS if s not in lower]
    if missing:
        fail(f"missing required fact(s): {missing}")

    if not any(re.search(p, lower) for p in ACTION_PATTERNS):
        fail("does not describe the required re-link action")

    if not any(re.search(p, lower) for p in CONSEQUENCE_PATTERNS):
        fail("does not describe the lockout consequence of missing the deadline")

    # --- Links ---
    if LINK_WIKI not in raw:
        fail(f"missing exact link: {LINK_WIKI}")
    if LINK_SLACK not in raw:
        fail(f"missing exact link: {LINK_SLACK}")

    # --- Negative: irrelevant note left out ---
    present = [s for s in MUST_EXCLUDE_SUBSTRINGS if s in lower]
    if present:
        fail(f"includes irrelevant note(s) that should have been left out: {present}")

    # --- Negative: didn't just copy the style examples ---
    copied = [s for s in MUST_NOT_COPY_SUBSTRINGS if s in lower]
    if copied:
        fail(f"appears to copy content from style_examples.md verbatim: {copied}")

    # --- Negative: no placeholder text ---
    placeholder_hits = [s for s in BANNED_PLACEHOLDER_SUBSTRINGS if s in lower]
    if placeholder_hits:
        fail(f"contains placeholder text: {placeholder_hits}")

    # --- Structure: matches the "lead with the bottom line" convention ---
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    if len(paragraphs) < 3:
        fail(f"expected at least 3 distinct paragraphs/blocks, found {len(paragraphs)}")

    first_para = paragraphs[0].lower()
    if "bottom line" not in first_para:
        fail(
            "first paragraph does not open with a 'bottom line'-style lead, "
            "as demonstrated in style_examples.md"
        )
    if DEADLINE not in first_para:
        fail(
            "the required action and its deadline must be stated in the opening "
            "paragraph, before background/context information"
        )
    if "2019" in first_para:
        fail(
            "opening paragraph leads with background history instead of the "
            "required action and deadline"
        )
    if "dark mode" in first_para:
        fail("opening paragraph is cluttered with irrelevant/low-priority information")

    # --- Structure: sign-off convention ---
    last_line = paragraphs[-1].strip().splitlines()[-1].strip()
    if not re.match(r"^[—-]{1,2}\s*.*platform engineering", last_line, re.IGNORECASE):
        fail(
            f"expected a sign-off line starting with an em dash naming "
            f"'Platform Engineering' (the rollout owner from facts.md), got: {last_line!r}"
        )

    # --- Structure: a way to ask questions ---
    if "question" not in lower:
        fail("no line inviting/pointing to where to ask questions")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
