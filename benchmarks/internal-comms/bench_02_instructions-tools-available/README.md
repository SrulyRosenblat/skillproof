# bench_02_instructions-tools-available

## Capability tested

The `internal-comms` skill's `examples/3p-updates.md` guide tells the agent to pull
3P (Progress/Plans/Problems) content from available tools — Slack, Google Drive,
Email, Calendar — and to prioritize *high-signal* items (posts in big channels with
lots of reactions, docs from key people with lots of views, emails with lots of
replies, non-recurring important meetings) within the correct time window (Progress
and Problems = the past week; Plans = the coming week). It also specifies a strict,
terse output format (emoji + team + date range header, three single-line labeled
sections, 1-3 sentences each, data-driven).

This benchmark gives the agent four simulated raw data exports for a "Search
Platform" team and asks it to produce a 3P update. Each export mixes exactly one
genuinely important, on-topic, in-window item with several decoys:

- **Slack**: a high-reaction (24), in-window, on-topic ship announcement vs. a
  low-reaction off-topic message, a high-reaction but out-of-window message, and a
  high-reaction but off-team (`#random`) message.
- **Google Drive**: a high-view (450), in-window, relevant roadmap doc vs. a
  low-view scratch doc and a high-view but out-of-window retrospective.
- **Email**: a high-reply (18), in-window incident postmortem vs. a zero-reply
  newsletter and a low-reply, out-of-window email.
- **Calendar**: a non-recurring, in-window (next week) leadership product review vs.
  two recurring standups and an out-of-window one-off social event.

An agent that has internalized the skill's guidance knows to weight engagement
signals, filter by relevance and date window, and use the strict format. An agent
without that guidance is likely to either dump everything indiscriminately (diluting
the update and pulling in noise), miss the real signal, or use a looser/generic
report format (headers, bullets, missing labels) instead of the required single-line
`Progress:`/`Plans:`/`Problems:` format.

## Why this matters

This is exactly the "Tools Available" part of the skill: without it, there's no
principled way to know which of several plausible-looking snippets belongs in a
30-60-second executive update versus which is noise. The fixtures are deliberately
engineered so that a naive summary (e.g. "include whatever is at the top of each
file" or "include everything") fails the grader, while correctly triaging by
engagement/relevance/date window passes.

## Grading

`grader/grade.sh` runs `grader/check.py`, which deterministically parses
`/workspace/3p_update.md` and checks:

1. **File exists** with a header line containing the team name (`Search Platform`),
   the exact date range (`2026-06-08` and `2026-06-15`), and an emoji before the team
   name.
2. **Format**: exactly one line each starting with `Progress:`, `Plans:`, `Problems:`,
   in that order, each with 1-3 sentences.
3. **Substance (positive)**: each section contains at least one keyword tying it back
   to the correct high-signal source item (e.g. Progress must mention `35%`,
   `hybrid ranking`, or `p95`; Plans must mention `vector index`, `migration`, or
   `june 18`; Problems must mention `outage`, `shard failure`, `open reqs`, or
   `short`).
4. **Substance (negative)**: the whole document must not contain any decoy tokens
   (`coffee machine`, `launch celebration`, `revenue up 12`, `font choices`,
   `sunset party`, `weekly standup`, `snacks`, `vendor contract renewal`,
   `year-end retrospective`, `all-hands recap`) — proving low-signal, off-topic,
   recurring, or out-of-window items were correctly excluded.

All checks are deterministic (no LLM judge needed): they parse the produced markdown
file and check content/structure directly, run against the actual fixture facts. The
grader fails on an untouched workspace (no `3p_update.md`) and passes on
`reference_solution/3p_update.md`.

## Reference solution

`reference_solution/3p_update.md` extracts exactly the four true-signal items (the
shipped ranking model with concrete metrics, the vector index migration + product
review, and the outage/staffing problem), ignores every decoy, and follows the exact
required format.
