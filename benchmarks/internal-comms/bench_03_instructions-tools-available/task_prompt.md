# Task: This Week's Company FAQ Digest

You work at Acme Robotics. Every week, someone compiles a short digest of the
questions that a lot of employees are actually asking, so the company can
answer them once instead of a hundred different people getting a hundred
different answers.

## Input material (in `/workspace`)

- `slack/general.json`, `slack/product-team.json`, `slack/random.json` —
  exports of several Slack channels. Each top-level message includes the
  author, their team, the message text, reaction counts, and any thread
  replies.
- `email/*.txt` — recent all-company emails.
- `documents/allhands-notes-2026-06-30.md` — notes from the most recent
  all-hands meeting, shared with the whole company.

## What to produce

Create `/workspace/faq_digest.md` containing one entry for each question
that is a genuine, company-wide source of confusion this week — meaning a
broad cross-section of employees, spanning multiple different teams, is
asking about or reacting to the same topic. Do not include questions that
really only concern one person's individual situation, one team's internal
day-to-day work, or that nobody else engaged with.

For every topic you include, add an entry in exactly this format (repeat for
each entry, in any order):

```
*Question*: <one sentence framing the shared question>
*Answer*: <one to two sentence answer>
```

Requirements for each answer:

1. Get the specifics right (dates, names, numbers) and base them only on
   facts actually present in the material above — do not invent details.
2. Briefly say which piece of source material backs the answer (e.g. which
   email, document, or announcement it came from).
3. If employees are asking about something that the material above does not
   actually confirm one way or the other, say so plainly in the answer
   instead of guessing at a resolution, and make clear that it's still an
   open question for leadership rather than a settled fact.

Only `/workspace/faq_digest.md` needs to be created. It should read as a
clean, ready-to-share digest — no extra commentary about your process.
