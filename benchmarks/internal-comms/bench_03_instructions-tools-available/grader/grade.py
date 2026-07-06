import json
import os
import re
import sys

WORKDIR = os.getcwd()
FAQ_PATH = os.path.join(WORKDIR, "faq_digest.md")
JUDGE_DIR = os.path.join(WORKDIR, ".judge")
QUESTIONS_PATH = os.path.join(JUDGE_DIR, "questions.json")
ANSWERS_PATH = os.path.join(JUDGE_DIR, "answers.json")

ENTRY_PATTERN = re.compile(
    r"\*Question\*:\s*(.+?)\s*\n\*Answer\*:\s*(.+?)(?=\n\s*\*Question\*:|\Z)",
    re.DOTALL,
)


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def find_topic(entries, keywords):
    for q, a in entries:
        ql = q.lower()
        if any(k in ql for k in keywords):
            return q, a
    return None


def main():
    if not os.path.isfile(FAQ_PATH):
        fail("faq_digest.md not found in /workspace")

    content = open(FAQ_PATH, encoding="utf-8").read()

    raw_entries = ENTRY_PATTERN.findall(content)
    entries = [(q.strip(), " ".join(a.split())) for q, a in raw_entries]

    if len(entries) < 4:
        fail(
            "expected at least 4 entries in the required '*Question*: ... / "
            f"*Answer*: ...' format, found {len(entries)}"
        )
    if len(entries) > 6:
        fail(
            f"found {len(entries)} entries; the digest should focus on genuinely "
            "broad, company-wide topics, not every question that was raised anywhere"
        )

    lower_content = content.lower()

    banned = [
        "anyconnect", "vpn", "pr #482", "css fix", "settings page",
        "pto", "bagel", "happy hour", "trivia", "snack budget",
        "expense report", "standup cadence",
    ]
    hit = [b for b in banned if b in lower_content]
    if hit:
        fail(
            "output includes narrow/one-off or unrelated topics that should have "
            f"been excluded: {hit}"
        )

    # Topic 1: hybrid / return-to-office schedule
    hybrid = find_topic(
        entries,
        ["hybrid", "return to office", "return-to-office", "rto", "office schedule", "in-office"],
    )
    if not hybrid:
        fail("missing an FAQ entry about the new hybrid/return-to-office schedule")
    _, a = hybrid
    al = a.lower()
    for req in ["september 1", "hybrid"]:
        if req not in al:
            fail(f"hybrid work policy answer is missing key fact '{req}'")
    if "email" not in al and "people team" not in al and "hr" not in al:
        fail("hybrid work policy answer should note which source (the People/HR email) backs it")

    # Topic 2: new CFO
    cfo = find_topic(entries, ["cfo", "jordan kim", "new chief financial"])
    if not cfo:
        fail("missing an FAQ entry about the new CFO")
    _, a = cfo
    al = a.lower()
    for req in ["jordan kim", "july 15"]:
        if req not in al:
            fail(f"new CFO answer is missing key fact '{req}'")
    if "no change" not in al:
        fail("new CFO answer should reflect that the budget approval process is not changing yet")
    if "email" not in al and "ceo" not in al:
        fail("new CFO answer should note which source (the CEO's email) backs it")

    # Topic 3: Atlas launch timeline
    atlas = find_topic(entries, ["atlas", "launch"])
    if not atlas:
        fail("missing an FAQ entry about the Atlas launch timeline")
    _, a = atlas
    al = a.lower()
    for req in ["october 2026", "lidar"]:
        if req not in al:
            fail(f"Atlas launch answer is missing key fact '{req}'")
    if "email" not in al and "pm team" not in al and "announcement" not in al:
        fail("Atlas launch answer should note which source (the PM team's email) backs it")

    # Topic 4: layoffs / hiring freeze uncertainty
    layoffs = find_topic(entries, ["layoff", "hiring freeze", "job security", "restructur"])
    if not layoffs:
        fail("missing an FAQ entry about whether the Atlas delay means layoffs or a hiring freeze")
    _, layoffs_answer = layoffs
    al = layoffs_answer.lower()
    hedge_phrases = [
        "no decision", "not been decided", "no decisions have been made", "hasn't been decided",
        "open question", "unclear", "uncertain", "no official", "not confirmed", "no confirmed",
        "tbd", "to be determined", "nothing has been decided", "hasn't announced", "has not announced",
        "nothing to announce", "not settled", "leadership has not",
    ]
    if not any(h in al for h in hedge_phrases):
        fail(
            "the layoffs/hiring-freeze answer should clearly flag this as an open "
            "question leadership hasn't resolved, rather than asserting a definite outcome"
        )

    if os.path.isfile(ANSWERS_PATH):
        answers = json.load(open(ANSWERS_PATH, encoding="utf-8"))["answers"]
        if not answers.get("q1"):
            fail(
                "judge determined the layoffs/hiring-freeze answer does not properly "
                "reflect the open, unresolved nature of the question"
            )
        print("PASS")
        sys.exit(0)

    os.makedirs(JUDGE_DIR, exist_ok=True)
    with open(QUESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "questions": [
                    {
                        "id": "q1",
                        "question": (
                            "The text below is meant to answer employees' question about "
                            "whether a recent product launch delay means a hiring freeze or "
                            "layoffs are coming. Does the text avoid confirming or denying "
                            "that layoffs/a hiring freeze will happen, and instead accurately "
                            "convey that leadership has called this an open, undecided "
                            "question rather than a settled fact?"
                        ),
                        "text": layoffs_answer,
                    }
                ]
            },
            f,
            indent=2,
        )
    sys.exit(3)


if __name__ == "__main__":
    main()
