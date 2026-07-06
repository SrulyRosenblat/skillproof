# Task: Write a weekly 3P update for the Search Platform team

You work on internal communications. The **Search Platform** team needs a "3P" update
(Progress, Plans, Problems) posted for leadership. Assume **today is Monday, June 15,
2026**.

- **Progress** and **Problems** should reflect what happened in the past week: **June 8
  through June 15, 2026**.
- **Plans** should reflect what's expected in the coming week: **June 15 through June
  22, 2026**.

You've been given raw data exports for the team in `/workspace`:

- `slack_export.json` — recent Slack messages (channel, author, date, reaction count,
  text)
- `gdrive_docs.json` — recent Google Drive docs (title, author, date, view count,
  summary)
- `emails.json` — recent emails (sender, subject, date, reply count, body)
- `calendar.json` — calendar events (title, date, whether it's a recurring event,
  attendees, description)

Not everything in these files is relevant or worth including — use your judgment about
which items actually belong in a leadership-facing update for this specific team, and
which fall outside the time windows above. Some entries are noise (off-topic, low
engagement, from a different team, or outdated) and should be left out.

## Output

Create a file at `/workspace/3p_update.md` containing exactly one 3P update, formatted
as follows:

```
<emoji> Search Platform (2026-06-08 to 2026-06-15)
Progress: <1-3 sentences>
Plans: <1-3 sentences>
Problems: <1-3 sentences>
```

Requirements:

- Line 1 must start with a single emoji, followed by the team name `Search Platform`,
  followed by the date range `(2026-06-08 to 2026-06-15)` exactly as shown.
- The next three lines must each start with the literal label `Progress:`, `Plans:`, or
  `Problems:` (in that order), followed by 1-3 sentences of content.
- Each section should be concise and matter-of-fact (something a busy executive could
  read in well under a minute), and should cite concrete facts/metrics from the source
  data rather than vague generalities.
- Do not include any sections, headers, or commentary beyond the four lines described
  above.
