---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    Several non-default conventions of n8n's batch workflow-update mechanism
    have to be applied together, and none of them is spelled out in the
    prompt. First, a connection operation aimed at an IF node's "true"
    branch or a Switch node's numbered case has to land on the matching
    numeric output slot (true -> 0, false -> 1, case N -> slot N directly),
    and the target's output-slot array has to be built out to the right
    length first - a model that doesn't know this plausibly appends both an
    IF node's branches to the same slot, or assigns Switch targets
    sequential slots in the order they're listed (0, 1) rather than the
    case numbers actually given (0, 2), leaving slot 1 wrongly filled or the
    array too short. Second, a node-update operation's changed field is
    given as a dot-notation path, so an update to "parameters.meta.updatedBy"
    has to create a nested object inside the node's parameters, not a
    literal key containing a dot - a model unfamiliar with that convention
    plausibly sets the dotted string itself as a flat key. Third, the
    "clean up broken connections" operation has to sweep every connection in
    the whole graph for references to nodes that no longer exist, not just
    the one node a preceding remove-node operation named - the workflow
    already has one connection pointing at a node that was never real to
    begin with, planted before this batch ever ran, so an implementation
    that only reacts to the node it just removed leaves that one behind.
    Finally, summarizing an evaluation run's aggregated metrics requires
    knowing which metric names are attached to every run automatically
    (prompt/completion/total token counts and execution time) versus which
    are specific to this evaluation - a model that doesn't know the
    automatic set plausibly averages every field in the metrics map,
    producing a wildly different number dominated by token counts in the
    thousands instead of the small custom scores. Every check compares the
    result against values computed from the input files themselves, not
    against a hardcoded literal, so guessing the right shape without the
    right procedure doesn't pass.
  category: software-engineering
  subcategory: workflow-automation
  category_confidence: low
  task_type:
    - configuration
    - transformation
  modality:
    - structured-data
  interface:
    - terminal
  skill_type:
    - domain-procedure
    - tool-workflow
  tags:
    - n8n
    - mcp-tools
    - workflow-update
    - connections
    - evaluations
    - workflow-automation
verifier:
  type: test-script
  timeout_sec: 300.0
agent:
  timeout_sec: 900.0
environment:
  network_mode: no-network
  build_timeout_sec: 300.0
  os: linux
  cpus: 1
  memory_mb: 1024
  storage_mb: 1024
  gpus: 0
---

This team never hand-edits an exported n8n workflow directly. Instead, every
change is first queued up as a batch of typed update operations - the same
operation vocabulary and parameter shape n8n's own built-in workflow-update
mechanism accepts - and then that batch is carried out against the export.

`/workspace/workflow.json` is the current export for an "Order Routing"
workflow: a `Webhook` trigger feeds an `IF` node (whose two branches aren't
wired to anything yet) and a `Switch` node (whose three cases aren't wired to
anything yet), plus a leftover `Legacy Logger` node and an already-stale
connection or two left over from earlier manual surgery on the file.

`/workspace/operations.json` is the batch already queued up for this
workflow by an upstream planning step - a JSON array of operation objects,
each with a `type` field naming the kind of change and whatever other fields
that change needs. Carry out every operation in that array, in order,
directly against `/workspace/workflow.json`, editing the file in place so it
ends up reflecting the fully-applied result. Some operations' effects reach
further than the single node or connection they name directly - work out
from each operation's own fields and the current state of the file exactly
what it should do, rather than assuming every operation only touches what it
explicitly mentions.

Separately, `/workspace/run_metrics.json` is the aggregated result of an
evaluation test run recorded against this same workflow - the kind of object
you get back when checking on a test run, with a flat `metrics` map mixing
this evaluation's own scoring criteria together with the handful of metrics
that get attached to the result of *every* run regardless of what's being
measured. Write `/workspace/custom_metrics_summary.json` as a JSON object
with two fields: `custom_metric_names` (a sorted list of just the metric
names specific to this evaluation) and `average` (their mean, rounded to 4
decimal places) - leaving out whichever metrics aren't specific to this
evaluation.

Don't rename, retype, or reposition any node that isn't explicitly targeted
by an operation, and don't invent connections or metadata changes beyond
what the operations batch specifies. Both `workflow.json` and
`custom_metrics_summary.json` must be valid JSON when you're done.
