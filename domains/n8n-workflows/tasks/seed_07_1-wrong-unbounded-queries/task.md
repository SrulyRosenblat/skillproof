---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >
    Passing requires several pieces of non-default n8n Data Table node
    knowledge at once: that Get/Update/Upsert/DeleteRows require at least one
    filter condition (so "return everything" needs an always-true condition
    trick), that these row operations execute once per input item (so a
    downstream step meant to run exactly once needs an explicit collapse to a
    single item), that a zero-match result silently halts the downstream
    branch unless the node is set to always output data, and that safe
    delete-after-read requires deleting by the specific ids just read rather
    than re-applying a broad filter (else a concurrently-added row is wiped
    unread). It also requires knowing to set an explicit timezone on a
    Schedule Trigger and to bound a SQL query against a table that can grow
    unboundedly. A model without this specific domain knowledge will very
    plausibly patch the obvious operation-name typo and stop there, which
    still fails most of the behavioral checks.
  category: workflow-automation
  subcategory: data-table-operations
  category_confidence: 0.85
  task_type:
    - bug_fix
    - code_repair
  modality:
    - text
  interface:
    - cli
  skill_type:
    - domain_knowledge
  tags:
    - n8n
    - data-table
    - schedule-trigger
    - race-condition
    - unbounded-query
    - workflow-json
verifier:
  type: test-script
  timeout_sec: 60
agent:
  timeout_sec: 1800
environment:
  network_mode: no-network
  build_timeout_sec: 600
  os: linux
  cpus: 2
  memory_mb: 2048
  storage_mb: 2048
  gpus: 0
---

# Fix the "Nightly Error Buffer Flush" n8n workflow

Your team exported an n8n workflow to `/workspace/workflow.json`, called
"Nightly Error Buffer Flush". It's meant to run every night, move buffered
error rows out of a Data Table named `error_buffer`, log a summary of the
run, and also run a small reporting query against a much larger historical
table. Several bugs currently make it unreliable in production.

Fix `/workspace/workflow.json` in place — it must remain a valid n8n workflow
export (keep the existing `nodes` / `connections` structure; you may add
nodes and connections if needed) — so that the workflow satisfies every
requirement below:

1. **Schedule.** The trigger must fire daily at exactly 9:00 AM in the
   `America/New_York` timezone. Don't leave the timezone to be inferred from
   wherever the server happens to run.

2. **Complete flush.** Every run must remove every row currently sitting in
   the `error_buffer` Data Table — regardless of how many rows happen to be
   buffered that day, including zero.

3. **No data loss under concurrency.** If a new row lands in `error_buffer`
   after the flush has already read the buffer's contents but before it
   finishes clearing them out, that new row must survive. It must NOT be
   deleted, and must remain available to be picked up on a later run.

4. **Exactly one summary per run.** Every scheduled run — even a run where
   the buffer was completely empty — must add exactly one new row to the
   `flush_runs` Data Table. Never zero, never more than one, no matter how
   many error rows were flushed that particular run.

5. **Bounded reporting query.** The workflow also queries the historical
   `error_log_archive` table for a dashboard widget. That table can grow
   arbitrarily large over time, so this query must never pull back more than
   5,000 rows, no matter how large the table gets.

Keep everything else about the workflow (its purpose, its node types, its
overall shape) intact — only change what's necessary to satisfy the
requirements above.
