# Task: Write the user-facing text for four product moments

You're helping ship a small feature for "Fernbox," a shared-folder tool that small
teams use to store and sync files. The engineering team has written up their
implementation notes for four moments in the product, but nobody has written the
actual text that will appear on screen yet.

Read:
- `/workspace/system_notes.md` — engineering notes for the four moments below
- `/workspace/limits.json` — the numeric limits referenced in those notes

Write the on-screen text for these four moments and save it as
`/workspace/ui_copy.json`, a single JSON file with exactly this structure (every
value is a string you write):

```json
{
  "archive_action": {
    "button_label": "...",
    "confirmation_message": "..."
  },
  "remove_member_action": {
    "button_label": "...",
    "confirmation_message": "..."
  },
  "upload_error": {
    "message": "..."
  },
  "empty_folder_state": {
    "heading": "...",
    "body": "..."
  }
}
```

What each field is for:
- `archive_action`: the label of the button a folder owner clicks to archive a shared
  folder (see ENG-482), and the message shown after the action succeeds.
- `remove_member_action`: the label of the button a folder owner clicks to remove
  someone else's access to a shared folder (see ENG-491), and the message shown after
  the action succeeds.
- `upload_error.message`: the text shown to whoever's upload gets rejected for being
  too large (see ENG-503). It should reflect the actual size limit defined in
  `limits.json`.
- `empty_folder_state`: the `heading` and `body` text shown when a shared folder has
  no files in it yet (see ENG-511).

This text will appear directly in the product, in front of ordinary small-business
customers and their teams — not the engineers who wrote the notes above. Write
finished, ready-to-ship copy: no placeholders, no brackets, no TODOs.

Output only `/workspace/ui_copy.json` — no other files are required.
