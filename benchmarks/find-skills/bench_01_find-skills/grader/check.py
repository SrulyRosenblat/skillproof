import re
import sys
from pathlib import Path

WORKSPACE = Path("/workspace") if Path("/workspace").exists() else Path.cwd()

WINNER = {
    "identifier": "opensource-guild/dev-workflows@changelog-writer",
    "installs": "156000",
    "stars": "12400",
    "verified": "true",
}

DECOY_IDENTIFIERS = [
    "changelogzenith/cl-gen@auto-changelog",
    "driftwood-oss/release-toolkit@changelog-builder",
    "shadyscripts99/insta-changelog@changelog-magic",
]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def extract_field(text, label):
    m = re.search(
        r"\*\*" + re.escape(label) + r":\*\*\s*(.+)",
        text,
    )
    if not m:
        return None
    return m.group(1).strip()


def main():
    rec_path = WORKSPACE / "recommendation.md"
    if not rec_path.exists():
        fail("recommendation.md does not exist in /workspace")

    text = rec_path.read_text(encoding="utf-8")

    skill = extract_field(text, "Skill")
    installs = extract_field(text, "Installs")
    stars = extract_field(text, "GitHub Stars")
    verified = extract_field(text, "Verified Publisher")
    install_cmd = extract_field(text, "Install command")
    learn_more = extract_field(text, "Learn more")

    if skill is None:
        fail("could not find a **Skill:** field in recommendation.md")
    if skill.strip("`") != WINNER["identifier"]:
        fail(
            f"expected recommended skill '{WINNER['identifier']}', got '{skill}'"
        )

    if installs is None or re.sub(r"[,\s]", "", installs) != WINNER["installs"]:
        fail(f"Installs field does not match fixture data (got '{installs}')")

    if stars is None or re.sub(r"[,\s]", "", stars) != WINNER["stars"]:
        fail(f"GitHub Stars field does not match fixture data (got '{stars}')")

    if verified is None or verified.strip().lower() != WINNER["verified"]:
        fail(f"Verified Publisher field does not match fixture data (got '{verified}')")

    if install_cmd is None:
        fail("could not find an Install command field")
    cmd_clean = install_cmd.strip("`").strip()
    if WINNER["identifier"] not in cmd_clean:
        fail(f"Install command does not reference the recommended skill (got '{cmd_clean}')")
    if "-g" not in cmd_clean.split() or "-y" not in cmd_clean.split():
        fail(f"Install command is missing the global/no-prompt flags (got '{cmd_clean}')")
    if not cmd_clean.startswith("npx skills add"):
        fail(f"Install command does not start with 'npx skills add' (got '{cmd_clean}')")

    if learn_more is None:
        fail("could not find a Learn more field")
    expected_url = "https://skills.sh/opensource-guild/dev-workflows/changelog-writer"
    if learn_more.strip() != expected_url:
        fail(f"Learn more URL is wrong (expected '{expected_url}', got '{learn_more}')")

    # Rejected alternatives: every decoy must be mentioned with a non-trivial reason.
    rejected_section_match = re.search(
        r"## Rejected alternatives\s*\n(.+)", text, re.DOTALL
    )
    if not rejected_section_match:
        fail("missing '## Rejected alternatives' section")
    rejected_text = rejected_section_match.group(1)

    reasons_by_identifier = {}
    for line in rejected_text.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        m = re.match(r"-\s*([^\s:]+)\s*:\s*(.*)$", line)
        if not m:
            continue
        reasons_by_identifier[m.group(1)] = m.group(2).strip()

    for decoy in DECOY_IDENTIFIERS:
        reason = reasons_by_identifier.get(decoy)
        if reason is None:
            fail(f"Rejected alternatives section does not list '{decoy}' with a reason")
        if len(reason) < 10:
            fail(f"Reason given for rejecting '{decoy}' is too thin: '{reason}'")

    # The winner must not also appear as a rejected alternative.
    if WINNER["identifier"] in reasons_by_identifier:
        fail("the recommended skill must not also appear in Rejected alternatives")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
