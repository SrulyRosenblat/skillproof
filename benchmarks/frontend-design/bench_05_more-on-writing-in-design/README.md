# bench_05_more-on-writing-in-design

## Capability tested

This benchmark targets the "More on writing in design" cluster of the
`frontend-design` skill: the idea that UI copy is design material, not decoration,
and should be written from the end user's side of the screen, in active voice, with
a single consistent name for an action across a flow, and with errors/empty states
treated as specific, actionable moments rather than vague or apologetic filler.

Concretely, the skill excerpt asks for:
- Naming things by what people control/recognize, not by internal implementation
  (e.g. "notifications," not "webhook config").
- Active voice, with the same action name carried through the whole flow (a button
  that says "Publish" produces a toast that says "Published," not a generic
  "Success").
- Errors that state exactly what happened and how to fix it, without apologizing or
  being vague.
- Empty states written as an invitation to act, not a flat description of absence.
- A plain, conversational register with no filler.

## Why this matters for `frontend-design`

A design can have perfect spacing, color, and type and still read as generic or
AI-templated if its copy leaks implementation details, uses mismatched or generic
button/confirmation pairs, or hedges in errors and empty states. This cluster of the
skill is specifically about applying the same intentionality to words that the rest
of the skill applies to layout and type — so a benchmark for it has to isolate
copywriting decisions from visual/layout decisions, which is why the deliverable
here is a small structured copy file rather than a full page build.

## Task summary

The agent is given two fixtures under `files/` describing a small feature
("Fernbox," a shared-folder tool) purely from an engineering point of view:

- `system_notes.md`: ticket-style notes for four UI moments (archiving a folder,
  removing a member, an oversized upload, an empty folder), written in backend/API
  terms (`sync_group`, `POST /api/v2/sync-groups/{id}/deactivate`,
  `MAX_UPLOAD_BYTES`, `413 Payload Too Large`, etc.), and with the archive action
  even named inconsistently across the ticket ("archive," "deactivate,"
  "soft-delete").
- `limits.json`: the numeric limit referenced by the upload-size ticket
  (`MAX_UPLOAD_BYTES: 314572800`, i.e. 300 MB).

The agent must write `/workspace/ui_copy.json`, a fixed-schema JSON file with the
button label + confirmation text for the two actions, the error message for the
oversized upload, and the heading + body for the empty folder state. The task
prompt states the required file, schema, and what each field is for, but never
states the skill's actual writing principles (no mention of jargon, active voice,
apology-avoidance, or action-name consistency) — a model that hasn't internalized
those principles is expected to lean on the fixture's own vocabulary and produce
mismatched or generic confirmations, apologetic/vague errors, raw internal numbers,
and a flat empty state.

## How grading works

`grader/grade.sh` runs `grader/grade.py` with `cwd=/workspace`, in two stages:

1. **Deterministic checks** (exit 1 on any failure):
   - `ui_copy.json` exists, is valid JSON, and has all required keys/fields
     non-empty.
   - No internal/system jargon from the fixtures (`sync_group`, `api`, `endpoint`,
     `config`, `database`, `byte(s)`, the raw `314572800`, etc.) appears anywhere in
     the copy — checked with word-boundary/substring matching so legitimate words
     like "megabytes" are never falsely flagged.
   - No apologetic/vague filler ("sorry," "oops," "unfortunately," "an error
     occurred") appears anywhere.
   - Neither action button uses a generic label ("Submit," "OK," "Confirm," ...).
   - For each action, the confirmation message shares the verb root of the button
     label (a lightweight stemmer checks that, e.g., "Archive folder" is followed by
     a confirmation containing "archiv...", not an unrelated word) — this is the
     property-based stand-in for "the button that says Publish produces a toast
     that says Published."
   - The upload error states the actual limit in human-readable form ("300" plus
     "MB"/"megabyte") — a fact that must be correctly derived and converted from
     `limits.json` — and names a concrete fix (a word like "smaller," "compress,"
     "split," ...).
   - The empty-folder copy contains "upload," i.e. it names the action that would
     fill the empty state, rather than only describing the absence of files.
2. **LLM judge** (only reached once all deterministic checks pass): four strict
   yes/no questions confirming, in more holistic/semantic terms than string
   matching can, that the button/confirmation pairs match, the error is specific
   and actionable without apologizing, the empty state invites action, and the
   overall register is plain and free of engineering jargon. All four must be
   answered "yes" for the grader to pass.

The grader fails immediately (exit 1) on an untouched workspace, since
`ui_copy.json` won't exist yet.

## Reference solution

`reference_solution/ui_copy.json` renames the feature's internal concepts into
plain, customer-facing language ("Archive folder" / "Folder archived," "Remove
member" / "Member removed"), states the upload limit as "300 MB" with a concrete
fix ("Try a smaller file, or split it into parts..."), and writes the empty state as
an invitation ("Upload your first file to start sharing it with your team."). It
was verified locally to satisfy every deterministic check, and is written so that a
reasonable judge would answer "yes" to all four holistic questions.
