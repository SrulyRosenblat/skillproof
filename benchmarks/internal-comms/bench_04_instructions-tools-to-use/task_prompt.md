# Task: Write this week's company-wide newsletter

You work on internal communications at Acme Inc., a company of about 1,290
employees. You need to write the company-wide weekly newsletter covering
**June 29 - July 6, 2026**. It will be posted to Slack and sent over email to
every employee, from the most senior executive to the newest hire.

You've been given raw exports from the company's internal systems in
`/workspace`:

- `slack_messages.json` — recent Slack messages, each with the channel name,
  channel member count, author, text, reaction count, and thread reply count
- `emails.json` — recent emails, each with sender, recipient description,
  recipient count, subject, body, and a link
- `calendar_events.json` — recent calendar events, each with title, attendee
  count, and any documents attached to the event
- `documents.json` — recently published internal documents, each with title,
  author, view count, link, and description
- `press_mentions.json` — recent external press coverage, each with
  publication, title, date, and URL
- `company_info.json` — basic company metadata for context

Not everything in these exports belongs in a company-wide newsletter. Each
file is a mix of things that matter to the whole company (major
announcements, leadership messages, company milestones, external
recognition) and things that don't (routine operational notices, small-team
or single-department chatter, discussions that are off-topic or not
newsworthy even if they got a lot of engagement). Use your judgment about
which items are actually significant enough for a 1,290-person company-wide
audience, and leave the rest out.

## Output

Create a file at `/workspace/newsletter.md` with the following requirements:

1. **Length and format**: roughly 20-25 top-level bullet points in total
   (bullets may have nested sub-bullets, which don't count toward this
   total), organized under at least 3 clearly labeled section headings
   (use markdown `##` headers). Each top-level bullet should be about 1-2
   sentences — short and easy to skim in Slack or email.
2. **Sections**: group related bullets together under headings that make
   sense for the content (for example, separating company announcements
   from progress on major initiatives from leadership messages from social
   highlights) so the different areas of the company are easy to scan
   rather than one long undifferentiated list.
3. **Voice**: write from the company's own point of view — most bullets
   should be phrased in the first-person plural ("we shipped...", "we
   welcomed...", "our team...") rather than a detached third-person report.
4. **Links**: wherever a source item has a URL, link to it directly in
   the corresponding bullet using markdown link syntax, so readers can jump
   to the original Slack thread, email, document, or article.
5. **Substance**: every bullet should be traceable to something that
   actually happened this week according to the provided data — don't
   invent facts, and don't include placeholder or filler bullets just to
   hit the target count.

Do not create any files other than `/workspace/newsletter.md`.
