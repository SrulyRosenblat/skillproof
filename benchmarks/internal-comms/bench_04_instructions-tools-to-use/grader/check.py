import os
import re
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("BENCH_WORKSPACE", "/workspace"))
OUTPUT_FILE = WORKSPACE / "newsletter.md"

# Substrings that must appear (case-insensitive) somewhere in the newsletter,
# proving that each genuinely high-signal, company-wide item from the source
# data was actually surfaced. "all-hands" is checked separately via regex to
# tolerate the "all hands" / "all-hands" spelling variants.
MUST_INCLUDE_SUBSTRINGS = [
    "helios",
    "45 new",
    "acme copilot",
    "series d",
    "q3 strategy",
    "jordan alvarez",
    "stock purchase plan",
    "h2 2026 roadmap",
    "vision 2027",
    "austin",
    "techcrunch",
    "forbes",
]
ALL_HANDS_RE = re.compile(r"all[\s-]?hands", re.IGNORECASE)

# Substrings unique to low-signal / team-specific / routine-operational / off-topic
# source items. None of these should appear in a correctly-triaged newsletter.
MUST_EXCLUDE_SUBSTRINGS = [
    "redis",
    "meridian health",
    "joined their standup",
    "network maintenance",
    "sprint 42",
    "backend platform weekly sync",
    "infra runbook",
    "real estate permit",
    "board of directors prep",
    "confidential board deck",
]

# Exact URLs from the source fixtures. At least this many must appear verbatim
# as links in the newsletter.
FIXTURE_URLS = [
    "https://acmeinc.slack.com/archives/C01ANNOUNCE/p1000001001",
    "https://acmeinc.slack.com/archives/C01ANNOUNCE/p1000001005",
    "https://mail.acmeinc.com/thread/q3-strategy-2026",
    "https://mail.acmeinc.com/thread/welcome-jordan-alvarez",
    "https://drive.acmeinc.com/doc/company-vision-2027",
    "https://drive.acmeinc.com/doc/austin-office-guide",
    "https://drive.acmeinc.com/doc/roadmap-h2-2026",
    "https://techcrunch.com/2026/acme-helios-launch",
    "https://forbes.com/2026/acme-best-places-to-work",
]
MIN_URLS_REQUIRED = 6

MIN_TOP_LEVEL_BULLETS = 12
MAX_TOP_LEVEL_BULLETS = 34
MIN_SECTION_HEADERS = 3
MIN_WE_VOICE_FRACTION = 0.6
MAX_WORDS_PER_BULLET = 55

WE_VOICE_RE = re.compile(r"\b(we|we're|we've|our|us)\b", re.IGNORECASE)
TOP_LEVEL_BULLET_RE = re.compile(r"^[-*]\s+\S")
HEADER_RE = re.compile(r"^#{2,3}\s+\S")


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    if not OUTPUT_FILE.exists():
        fail(f"{OUTPUT_FILE} does not exist")

    raw = OUTPUT_FILE.read_text(encoding="utf-8")
    lower = raw.lower()
    lines = raw.splitlines()

    # --- Section headers ---
    headers = [line for line in lines if HEADER_RE.match(line)]
    if len(headers) < MIN_SECTION_HEADERS:
        fail(
            f"expected at least {MIN_SECTION_HEADERS} markdown section headers (##/###), "
            f"found {len(headers)}"
        )

    # --- Top-level bullets (no leading whitespace) ---
    top_bullets = [line for line in lines if TOP_LEVEL_BULLET_RE.match(line)]
    n_bullets = len(top_bullets)
    if not (MIN_TOP_LEVEL_BULLETS <= n_bullets <= MAX_TOP_LEVEL_BULLETS):
        fail(
            f"expected roughly {MIN_TOP_LEVEL_BULLETS}-{MAX_TOP_LEVEL_BULLETS} top-level "
            f"bullets, found {n_bullets}"
        )

    # --- Bullet brevity (proxy for "1-2 sentences") ---
    too_long = []
    for b in top_bullets:
        text = re.sub(r"^[-*]\s+", "", b)
        word_count = len(text.split())
        if word_count > MAX_WORDS_PER_BULLET:
            too_long.append((word_count, text))
    if too_long:
        worst = max(too_long, key=lambda t: t[0])
        fail(
            f"{len(too_long)} top-level bullet(s) exceed {MAX_WORDS_PER_BULLET} words "
            f"(worst: {worst[0]} words: {worst[1]!r})"
        )

    # --- "We" voice ---
    we_count = sum(1 for b in top_bullets if WE_VOICE_RE.search(b))
    fraction = we_count / n_bullets if n_bullets else 0
    if fraction < MIN_WE_VOICE_FRACTION:
        fail(
            f"only {we_count}/{n_bullets} ({fraction:.0%}) top-level bullets use "
            f"first-person-plural voice (we/our/us); expected at least "
            f"{MIN_WE_VOICE_FRACTION:.0%}"
        )

    # --- Must-include substance ---
    missing = [s for s in MUST_INCLUDE_SUBSTRINGS if s not in lower]
    if not ALL_HANDS_RE.search(raw):
        missing.append("all-hands")
    if missing:
        fail(f"newsletter is missing coverage of high-signal item(s): {missing}")

    # --- Must-exclude substance ---
    present = [s for s in MUST_EXCLUDE_SUBSTRINGS if s in lower]
    if present:
        fail(
            f"newsletter includes low-signal/team-specific/routine item(s) that "
            f"should have been left out: {present}"
        )

    # --- Links ---
    url_count = sum(1 for u in FIXTURE_URLS if u in raw)
    if url_count < MIN_URLS_REQUIRED:
        fail(
            f"expected at least {MIN_URLS_REQUIRED} direct links to source material, "
            f"found {url_count}"
        )

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
