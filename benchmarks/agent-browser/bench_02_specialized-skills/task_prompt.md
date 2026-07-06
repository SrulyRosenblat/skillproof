# Sync the highest-priority task in TaskFlow Desktop

Your workspace (`/workspace`) contains:

- `bin/agent-browser` — a command-line automation tool. Invoke it from
  `/workspace` as:
  ```
  python3 bin/agent-browser <args...>
  ```
- `data/task_queue.json` — the ops team's task queue. Each task has an `id`,
  a `title`, a `priority_rank` (lower number = higher priority), and a
  `status` (`"pending"` or `"done"`).

**TaskFlow Desktop** is a native desktop application (not a website) that is
already running on this machine under the app name `taskflow`. It is not a
page you can load from a file path or URL.

## Goal

Using the `agent-browser` tool, find the single **pending** task in
`data/task_queue.json` with the highest priority (i.e. the numerically
lowest `priority_rank` among tasks whose `status` is `"pending"`), mark that
one task complete in TaskFlow Desktop, and sync the app. Syncing produces a
sync code — capture its exact text.

`agent-browser` is a real automation tool with its own command syntax, and
that syntax differs depending on what kind of target you're automating. It
does not accept arbitrary or guessed commands, so you'll need to explore the
tool itself to figure out how to correctly drive a native desktop app like
this one before you can complete the task.

## Required output

Write your result to `/workspace/result.json`. It must be valid JSON
containing exactly these two keys:

```json
{"task_id": "<id of the task you completed, from task_queue.json>", "sync_code": "<the exact sync code text produced by the app>"}
```

Both values must come from actually completing the task through the tool —
not guessed, fabricated, or manually derived.
