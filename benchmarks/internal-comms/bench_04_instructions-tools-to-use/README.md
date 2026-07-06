# bench_04_instructions-tools-to-use

## Capability tested

The `internal-comms` skill's `examples/company-newsletter.md` guide tells the agent
that a company-wide newsletter must be assembled by pulling from *multiple* source
types — Slack (channels with lots of people, lots of reactions or thread replies),
email (executive, company-wide announcements), calendar (large-attendance meetings
like All-Hands, especially ones with attached docs), documents (new docs that got a
lot of attention, especially from key people), and external press — and then
filtering hard for company-wide relevance rather than team-specific minutiae. It
also specifies the output shape: ~20-25 short bullets, grouped into labeled
sections, written in "we" voice, with lots of links back to source material.

This benchmark gives the agent simulated raw exports from five source types and
asks it to produce that newsletter. Each file mixes genuinely company-wide,
high-signal items with several decoys that look superficially similar:

- **Slack**: five in-window, on-topic posts in the 1,240-member `#announcements`
  channel with high reactions/replies (product launch, funding round, new hires,
  All-Hands recap, new AI product) vs. a low-engagement infra fix in a 42-person
  channel, a decent-engagement but team-specific sales win in an 85-person channel,
  and a viral-but-irrelevant joke in `#random` with the *highest* reaction count of
  any message in the fixture (a deliberate trap: raw engagement alone is not a
  sufficient signal — the content also has to be substantive company news).
- **Email**: three company-wide executive/people-team emails (Q3 strategy, a new
  exec hire, a new stock purchase plan) vs. a routine all-employee IT maintenance
  notice and an 11-person team's sprint notes.
- **Calendar**: two large-attendance meetings with attached docs (All-Hands,
  quarterly roadmap review) vs. a 9-person team sync and a 4-person confidential
  board-prep meeting.
- **Documents**: two widely-viewed, exec-authored docs (company vision, new office
  guide) vs. a niche 14-view internal runbook.
- **Press**: two genuine external recognition pieces (TechCrunch, Forbes) vs. a
  minor real-estate filing mention.

An agent that has internalized the skill's guidance knows to check all five source
types (not just the obvious ones), weight engagement/scope/authorship as signals of
company-wide relevance, and produce the specific sectioned, we-voiced, link-heavy
bullet format. An agent without that guidance is likely to miss whole source types
(e.g. never check calendar attachments or document view counts), dump
team-specific/low-relevance noise in alongside real news, skip links, or write a
flat undifferentiated list in a detached third-person voice.

## Why this matters

This is exactly the "Tools to use" part of the skill: for a 1,000+ person company,
there is no single source of truth for "what mattered this week" — it has to be
synthesized across Slack, email, calendar, documents, and press, using engagement
and scope as filters. Skipping a source type or failing to filter by company-wide
relevance produces a newsletter that either misses real news or buries it in noise.

## Grading

`grader/grade.sh` runs `grader/check.py`, which deterministically parses
`/workspace/newsletter.md` and checks:

1. **Structure**: at least 3 markdown `##`/`###` section headers, and roughly
   12-34 top-level bullets (nested sub-bullets don't count), matching the
   requested "~20-25 top-level bullets across labeled sections" format.
2. **Brevity**: no top-level bullet exceeds 55 words (a generous proxy for
   "1-2 sentences").
3. **Voice**: at least 60% of top-level bullets use first-person-plural language
   (we/we're/we've/our/us).
4. **Substance (positive)**: the newsletter must reference every one of the 12
   genuinely high-signal items from the fixtures (Project Helios, the 45 new
   hires, the All-Hands, Acme Copilot, the Series D round, the Q3 strategy email,
   the new CPO, the stock purchase plan, the H2 roadmap, the company vision doc,
   the Austin office, and both press mentions).
5. **Substance (negative)**: the newsletter must not mention any of the 10
   low-signal/team-specific/routine decoys (the Redis fix, the Meridian Health
   deal, the dog-in-standup joke, network maintenance, sprint notes, the backend
   team sync, the infra runbook, or the confidential board-prep meeting/deck).
6. **Links**: at least 6 of the 9 exact source URLs from the fixtures must appear
   verbatim as links in the newsletter.

All checks are deterministic — they parse the produced markdown and check
content/structure directly against the known fixture facts, with no LLM judge
required. The grader fails on an untouched workspace (no `newsletter.md`) and
passes on `reference_solution/newsletter.md`. It was also verified to reject
solutions that skip sectioning/we-voice, and solutions that dump every source item
indiscriminately (including the decoys) alongside the real news.

## Reference solution

`reference_solution/newsletter.md` organizes the 12 true-signal items into four
labeled sections (Company Announcements, Progress on Priorities, Leadership
Updates, Social Highlights), links directly to 9 of the source items, writes
consistently in "we" voice, and omits every decoy.
