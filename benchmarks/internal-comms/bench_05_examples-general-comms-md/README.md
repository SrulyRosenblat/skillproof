# bench_05_examples-general-comms-md

## Capability tested

The `internal-comms` skill's `examples/general-comms.md` guide covers internal
communications that don't fit the standard formats (3P updates, newsletters,
FAQs). Once the audience, purpose, tone, and format are established, it lays
out general principles for the actual draft:

- put the most important information first, before background/context
- match the company's existing communication style
- include the relevant links/references
- be clear and concise, in active voice

This benchmark gives the agent a brief (audience/purpose/tone already
settled, since the harness has no interactive input) plus two source files:
a raw, unordered dump of facts about a mandatory system change
(`files/facts.md`), and two real past company announcements demonstrating a
consistent structural convention (`files/style_examples.md`): a bolded
"**Bottom line:**" lead sentence stating the action and deadline, short
paragraphs, a "Questions?" line, and an em-dash sign-off naming the
responsible team.

`facts.md` is deliberately unordered and includes one low-priority,
unrelated detail (a cosmetic dark-mode UI note) mixed in with the real
compliance deadline and its consequences. An agent that has internalized the
skill's "most important information first" and "match the company's style"
principles will:

1. Open with a "bottom line"-style sentence containing the actual required
   action and its deadline — not the tool's background history or the
   unrelated cosmetic note.
2. Reproduce the structural conventions shown in the examples (lead
   sentence, brevity, a "Questions?" line, an em-dash sign-off naming the
   correct team) without literally copying the examples' own content.
3. Include both reference links from the facts so the reader can act.
4. Leave out the irrelevant dark-mode detail entirely.

An agent without that guidance is likely to produce a flatter, chronological
or background-first account (e.g. opening with "As you may know, DevPortal
has run its own login system since 2019...", email-style with a "Subject:"
line and generic greeting/sign-off, no clear lead sentence), and/or pad the
draft with the irrelevant dark-mode note just because it was in the source
notes.

## Why this matters

Most internal announcements that don't fit a standard template still need to
follow good judgment about what a reader needs to see first, and they need
to sound like they came from the same company as everything else that
reader has seen. Getting this wrong — burying the actual ask under
background context, or writing in a voice/format that doesn't match
anything else the company sends — means readers skim past the one thing
they were required to do.

## Grading

`grader/grade.sh` runs `grader/check.py`, which deterministically parses
`/workspace/announcement.md` and checks:

1. **Length**: roughly 40-220 words (a announcement, not a one-liner or an essay).
2. **Substance**: mentions Okta, SSO, the exact deadline ("August 14, 2026"),
   the Q3 audit reason, the required re-link action, and the lockout
   consequence — all facts that only exist in `facts.md`.
3. **Links**: both exact reference URLs from `facts.md` appear verbatim.
4. **Negative (irrelevant content)**: the unrelated dark-mode note from
   `facts.md` does not appear anywhere in the draft.
5. **Negative (no copying)**: none of the content unique to the two examples
   in `style_examples.md` (e.g. "Duo", "VPN access", "eng-announcements")
   appears in the draft — proving the agent used the examples as a style
   template, not a content source.
6. **No placeholder text**: no "TODO"/"TBD"/"[link]"/lorem-ipsum-style
   filler.
7. **Structure — lead paragraph**: the first paragraph/block must contain a
   "bottom line"-style opening and the exact deadline string, and must NOT
   contain the tool's founding year ("2019") or the dark-mode note — i.e.
   the required action and deadline must come before background/context,
   not after it.
8. **Structure — sign-off**: the last line must start with an em dash (or
   `--`) and name "Platform Engineering", the rollout owner given in
   `facts.md`, matching the sign-off convention shown in both examples.
9. **Structure — contactability**: the draft must include a line inviting
   questions.

All checks are deterministic string/regex checks against the produced
markdown; no LLM judge is used. The grader was verified to:
- fail on an untouched workspace (no `announcement.md`)
- pass on `reference_solution/announcement.md`
- fail on a naive, background-first / email-style draft that pads in the
  dark-mode note (fails the "irrelevant content" and "lead paragraph" checks
  independently of each other)
- fail on a draft that copies example-specific content ("Duo", "VPN access")
  instead of drawing solely on the facts

## Reference solution

`reference_solution/announcement.md` opens with a "**Bottom line:**"
sentence stating the re-link requirement and the exact deadline, gives the
Okta/Q3-audit context and the lockout consequence in short paragraphs,
includes both reference links, invites questions, and signs off "—
Platform Engineering."
