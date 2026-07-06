import os
import re
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("BENCH_WORKSPACE", "/workspace"))
OUTPUT_FILE = WORKSPACE / "3p_update.md"

SECTION_LABELS = ["Progress", "Plans", "Problems"]

# Keywords that must appear (case-insensitive) somewhere in the relevant section,
# proving the correct high-signal source was actually used.
REQUIRED_KEYWORDS = {
    "Progress": ["35%", "hybrid ranking", "p95"],
    "Plans": ["vector index", "migration", "june 18"],
    "Problems": ["outage", "shard failure", "open reqs", "short"],
}

# Tokens unique to noise/decoy/off-topic/out-of-window source items. None of these
# should appear anywhere in the final update if the low-signal or irrelevant or
# out-of-window items were correctly filtered out.
BANNED_TOKENS = [
    "coffee machine",
    "launch celebration",
    "revenue up 12",
    "font choices",
    "sunset party",
    "weekly standup",
    "snacks",
    "vendor contract renewal",
    "year-end retrospective",
    "all-hands recap",
]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def count_sentences(text):
    text = text.strip()
    if not text:
        return 0
    parts = re.split(r"(?<=[.!?])\s+", text)
    return len([p for p in parts if p.strip()])


def main():
    if not OUTPUT_FILE.exists():
        fail(f"{OUTPUT_FILE} does not exist")

    raw = OUTPUT_FILE.read_text(encoding="utf-8")
    lines = [line for line in raw.splitlines() if line.strip() != ""]

    if len(lines) < 4:
        fail(f"expected at least 4 non-empty lines (header + 3 sections), got {len(lines)}")

    header = lines[0].strip()

    if "Search Platform" not in header:
        fail("header line must contain the team name 'Search Platform'")

    if "2026-06-08" not in header or "2026-06-15" not in header:
        fail("header line must contain the date range 2026-06-08 to 2026-06-15")

    prefix = header.split("Search Platform")[0]
    if not any(ord(c) > 0x2000 for c in prefix):
        fail("header line must start with an emoji before the team name")

    # Locate the three labeled lines, in order, each exactly once.
    body = "\n".join(lines[1:])
    positions = {}
    for label in SECTION_LABELS:
        matches = [m.start() for m in re.finditer(rf"^{label}:", body, flags=re.MULTILINE)]
        if len(matches) != 1:
            fail(f"expected exactly one line starting with '{label}:', found {len(matches)}")
        positions[label] = matches[0]

    if not (positions["Progress"] < positions["Plans"] < positions["Problems"]):
        fail("sections must appear in the order Progress, Plans, Problems")

    # Extract each section's content (from its label to the next label or EOF).
    ordered = sorted(positions.items(), key=lambda kv: kv[1])
    bounds = [pos for _, pos in ordered] + [len(body)]
    section_text = {}
    for i, (label, pos) in enumerate(ordered):
        chunk = body[pos:bounds[i + 1]]
        content = re.sub(rf"^{label}:", "", chunk, count=1).strip()
        section_text[label] = content

    for label, content in section_text.items():
        if not content:
            fail(f"section '{label}' has no content")
        n = count_sentences(content)
        if not (1 <= n <= 3):
            fail(f"section '{label}' should have 1-3 sentences, found {n}: {content!r}")

    lower_full = raw.lower()

    for label, keywords in REQUIRED_KEYWORDS.items():
        content_lower = section_text[label].lower()
        if not any(kw.lower() in content_lower for kw in keywords):
            fail(
                f"section '{label}' does not appear to reference the correct source "
                f"material (expected one of {keywords})"
            )

    for token in BANNED_TOKENS:
        if token.lower() in lower_full:
            fail(f"output contains content from a low-signal/irrelevant/out-of-window source: '{token}'")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
