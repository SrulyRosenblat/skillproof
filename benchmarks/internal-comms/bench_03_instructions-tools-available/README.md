# bench_03_instructions-tools-available

## Capability under test

The `internal-comms` skill's `examples/faq-answers.md` guideline says an FAQ
digest should be built by pulling signal from **all** of a company's
communication surfaces (Slack threads with lots of replies/reactions, emails,
and shared documents), and that the job is specifically to surface questions
that are "big sources of confusion for lots of employees ... generally about
things that affect a large portion of the employee base" — not just whatever
one person or team happens to be asking. It also lays out concrete answer
guidelines: ground answers in official communications, cite the source,
flag uncertainty explicitly, and flag when something needs an
executive/official response rather than guessing.

This benchmark tests whether an agent, working from raw multi-source
fixtures, actually does that filtering and grounding correctly — as opposed
to either (a) transcribing every question it sees regardless of how narrow
or personal it is, or (b) answering vaguely / inventing resolutions to
questions that haven't actually been settled.

## Why it matters for this skill

The "Instructions" and "Tools Available" sections are the core of
`faq-answers.md`: they define what counts as an FAQ-worthy topic (broad,
cross-team, well-engaged-with) and where to look for the raw signal (Slack
reactions/replies, emails, linked documents). An agent that hasn't
internalized this will tend to either dump every question it can find into
the digest, miss questions that are only implied by a document rather than
literally asked as a Slack message, or fail to distinguish "officially
confirmed" facts from "still an open question" — exactly the failure modes
this benchmark's fixtures are built to expose.

## Fixtures (`files/`, copied to the root of `/workspace`)

Acme Robotics' internal communications for the week:

- `slack/general.json` — a thread where employees from Sales, Engineering,
  Marketing, Support, Finance, Ops, and Product all ask about the upcoming
  hybrid work schedule, another thread where employees across many teams ask
  about the new CFO, and a one-off VPN certificate question from a single IT
  employee (noise — narrow, single-person, unrelated to anyone else).
- `slack/product-team.json` — a heavily-engaged thread (Sales, Marketing,
  Support, Ops, Engineering, Finance, People, IT all chime in) asking whether
  the Atlas product launch is still on schedule, plus an unrelated one-off
  PR-review request (noise — single team, zero reactions).
- `slack/random.json` — a personal PTO-rollover question and an Ops-only
  "free bagels" message (noise — personal / trivial, low engagement).
- `email/hr-rto-policy-faq.txt` — HR's official hybrid work policy email
  (Tue–Thu in office, Mon/Fri remote, starting September 1, 2026).
- `email/ceo-new-cfo-announcement.txt` — the CEO's email introducing Jordan
  Kim as CFO (effective July 15, 2026, no immediate process changes).
- `email/product-launch-timeline-update.txt` — the PM team's email pushing
  the Atlas launch from August to October 2026 due to a LIDAR supplier delay.
- `email/team-happy-hour-invite.txt` — a purely social invite (noise — not a
  question, not informative).
- `documents/allhands-notes-2026-06-30.md` — notes from the company
  all-hands, including the CEO's non-committal answer to "does the launch
  delay mean layoffs/a hiring freeze?" (no decision has been made — an
  officially-acknowledged but still-unresolved question) plus a trivial,
  single-team snack-budget aside (noise).

Four topics are genuinely company-wide (hybrid policy, new CFO, Atlas launch
delay, and the layoffs/hiring-freeze uncertainty raised in its wake); several
other messages are deliberately narrow, personal, or purely social and must
be excluded.

## Task given to the model (`task_prompt.md`)

The model is asked to produce `/workspace/faq_digest.md`, with one
`*Question*:` / `*Answer*:` entry per genuinely broad, cross-team topic. Each
answer must get its facts right, name which source backs it, and — if a
question isn't actually settled by the source material — say so plainly
instead of guessing. The prompt never names the skill, never says "Slack
reactions indicate importance," and never enumerates the specific noise
messages to exclude; the model has to infer breadth vs. narrowness and
grounded-vs-open answers itself from the raw fixtures.

## How grading works (`grader/grade.sh` → `grader/grade.py`)

All checks are deterministic except one LLM-judge question, following the
standard two-phase protocol:

1. **File and format check**: `faq_digest.md` must exist and contain 4–6
   entries matching the `*Question*: ... / *Answer*: ...` pattern.
2. **Negative check**: the whole file must not mention any of the noise
   topics (VPN/AnyConnect, the PR review, PTO, bagels, happy hour/trivia,
   the snack budget aside, expense reports, standup cadence changes).
3. **Per-topic substance checks** — for each of the four required topics, the
   grader locates the matching entry by keyword and asserts the answer
   contains the specific facts that only appear in the official source
   (e.g. "September 1" + "hybrid" for the RTO policy; "Jordan Kim" + "July
   15" + an explicit "no changes yet" for the CFO news; "October 2026" +
   "LIDAR" for the launch delay), plus a mention of which source backs it.
4. **Hedging check** for the layoffs/hiring-freeze topic: the answer must
   contain a phrase indicating the question is still open (e.g. "no
   decision", "open question", "nothing to announce") rather than a
   confident yes/no.
5. **LLM judge**: because keyword-matching "an open question" can't catch a
   subtler failure (asserting a confident outcome while sprinkling in a hedge
   word elsewhere), the grader also asks a judge whether the layoffs/hiring-
   freeze answer genuinely conveys "still unresolved" rather than confirming
   or denying an outcome. The grader writes `.judge/questions.json` and exits
   3; on the re-run it reads `.judge/answers.json` and finalizes the verdict.

The grader fails on an untouched workspace (no `faq_digest.md`) and passes on
`reference_solution/`, both verified locally.

## Reference solution

`reference_solution/faq_digest.md` contains exactly the four required
entries, each citing its source and getting the specific facts right, with
the layoffs/hiring-freeze answer explicitly framed as an open question the
CEO addressed at the all-hands without resolving — satisfying every
deterministic check and the judge question.
