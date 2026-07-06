# bench_02_specialized-skills: Load the right agent-browser specialized skill for a non-web-page target

## Capability under test

`agent-browser`'s `SKILL.md` states that its default (`core`) workflow only
covers ordinary browser web pages, and that other kinds of targets require a
different, specifically-named specialized skill:

> Load a specialized skill when the task falls outside browser web pages:
>
> ```
> agent-browser skills get electron          # Electron desktop apps (VS Code, Slack, Discord, Figma, ...)
> agent-browser skills get slack             # Slack workspace automation
> agent-browser skills get dogfood           # Exploratory testing / QA / bug hunts
> agent-browser skills get vercel-sandbox    # agent-browser inside Vercel Sandbox microVMs
> agent-browser skills get agentcore         # AWS Bedrock AgentCore cloud browsers
> ```
>
> Run `agent-browser skills list` to see everything available on the
> installed version.

An agent that has internalized this treats "core" (`open`/`snapshot`/`act`)
as scoped to web pages only, recognizes when a target falls outside that
scope, and knows to look for (and load) a differently-named specialized
skill before attempting the automation — rather than assuming `core`
commands generalize to any target, or giving up when they don't work.

This benchmark operationalizes that distinction with a small mock
`agent-browser` CLI (`files/bin/agent-browser`) that mirrors the real tool's
structure:

- Running the CLI with no arguments (or an unknown command) prints a stub
  message pointing at `skills get core` for web pages and `skills list` for
  everything else — exactly mirroring the real tool's own discovery-stub
  behavior.
- `skills get core` loads a workflow with `open`/`snapshot`/`act`, but these
  commands only understand local HTML files/URLs. The task's target —
  **TaskFlow Desktop**, a native desktop app already running under the name
  `taskflow` — is not addressable that way (`open taskflow` simply errors:
  "no such file").
- `skills list` reveals five named specialized skills (electron, slack,
  dogfood, vercel-sandbox, agentcore), matching the real tool's catalog.
  Only `electron` unlocks the `window attach` / `window tree` / `window do`
  commands needed to drive a desktop app window; the other four print
  unrelated stub docs and don't unlock anything useful for this task.
- Attempting any `window ...` subcommand before `skills get electron` has
  been run fails with an explicit error pointing at the missing skill.

Because the correct skill name is never stated in `task_prompt.md`, the only
way to reach the actual desktop-window command syntax is to explore the tool
(`skills list`, then `skills get electron`) and recognize which of the five
listed skills fits an Electron-style desktop app target — mirroring exactly
the recognition the real skill's "Specialized skills" section is meant to
produce.

## Task summary

The agent is given:
- `bin/agent-browser` — the mock CLI described above.
- `data/task_queue.json` — a queue of ops tasks, each with an `id`, `title`,
  `priority_rank` (lower = higher priority), and `status`.

It must determine the single pending task with the highest priority, mark it
complete inside TaskFlow Desktop through `agent-browser`, trigger a sync, and
report the task's `id` plus the sync code the app displays, in
`/workspace/result.json` as `{"task_id": "...", "sync_code": "..."}`.

The sync code is generated at runtime by the tool from the completed task's
data (not stored anywhere in the static fixtures), so it cannot be obtained
by reading files directly — the only way to get the right answer is to
correctly identify and drive the right specialized skill end to end.

## Why this matters for the skill

`agent-browser`'s core workflow deliberately does *not* attempt to handle
Electron apps, Slack workspaces, exploratory QA, Vercel Sandbox microVMs, or
AgentCore cloud browsers — those are separate, differently-named skills
loaded on demand. An agent that doesn't know this will either misapply web
page commands to a target that isn't a web page (and get stuck on the
resulting errors), or fail to discover that a specialized skill exists at
all. This benchmark fails such an agent by construction: `core`'s commands
never succeed against `taskflow`, and the five specialized skill names are
only revealed via `skills list`, so guessing without exploring doesn't work
either.

## Grading

Grading is fully deterministic and network-free (`grader/grade.sh` →
`grader/check.py`):

1. Confirms `/workspace/result.json` exists, is valid JSON, and contains
   exactly the keys `task_id` and `sync_code` with non-empty string values.
2. Confirms the input fixture directories (`bin/`, `data/`) are still
   present (i.e. the agent didn't delete/rename its inputs).
3. Independently computes the expected `task_id` by reading
   `data/task_queue.json` and picking the pending task with the lowest
   `priority_rank`.
4. Independently computes the expected `sync_code` by copying the fixtures
   into a scratch temp directory and *executing* the same `agent-browser`
   tool through the correct sequence (`skills get electron` → `window attach
   taskflow` → `window tree` → `window do <ref-of-expected-task> click` →
   `window do <ref-of-Sync-button> click` → `window tree`), then parsing the
   sync code out of that final tree's output.
5. Passes only if the agent's `result.json` matches both independently
   computed values exactly.

This follows "execute, don't grep": grading never inspects the agent's
transcript or command history, and never string-matches source code — it
only asserts on the produced artifact by re-deriving ground truth through the
same executable tool.

## Reference solution

`reference_solution/result.json` contains the correct result for this
fixture's task queue: the highest-priority pending task is `t2` ("Prepare
quarterly report", `priority_rank` 1), and the sync code produced by
actually running `bin/agent-browser` through the full correct sequence is
`T2-124` (the task id, its priority rank, and its title's character count —
the exact transform used internally by the mock tool). This is the only
file a correct solution needs to add to the workspace.
