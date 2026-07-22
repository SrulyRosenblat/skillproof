---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    Three non-default n8n human-review-tool conventions must all be applied
    together, and none of them is spelled out in the prompt. A choice between
    exactly two named outcomes has to be modeled as the button-based approval
    response type with approvalType 'double', not free text, not a form, and
    not the single-button default. Each button's label has to be an
    expression-mode string (leading '=' plus a `{{ $tool.parameters.X }}`
    reference into the wrapped tool's real parameters) so the reviewer sees
    the actual customer and amount — omit the leading '=' and n8n renders the
    literal template text instead of the resolved value, which looks
    plausible but is silently wrong. The review tool's own placeholder name
    also has to be replaced with a specific, verb-first label. A model
    without this specific knowledge plausibly reaches for free-text or a
    single generic Approve button, which the checks catch deterministically.
  category: software-engineering
  subcategory: workflow-automation
  category_confidence: low
  task_type:
    - transformation
    - configuration
  modality:
    - structured-data
  interface:
    - terminal
  skill_type:
    - domain-procedure
    - tool-workflow
  tags:
    - n8n
    - human-in-the-loop
    - agent-tools
    - workflow-automation
    - approval
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

`/workspace/workflow.json` is an exported n8n workflow for a customer-support
agent. The agent can call a `Process Customer Refund` tool (node id
`tool_refund`), which already has a specific customer and dollar amount set
on its parameters. Before that tool actually runs, a human has to sign off.

The reviewer facing this specific request needs to decide between exactly two
outcomes: refund the customer through their original payment method, or issue
the same amount as store credit instead. Whichever way they decide has to be
captured as one unambiguous, recordable choice — not an open-ended reply, and
not a form with fields to fill in. And because a reviewer will see many of
these requests in a day, whatever they're shown for this particular decision
has to make plain, on its face, exactly which customer and dollar amount is
on the table — not generic wording that leaves them cross-referencing
something else to know what they're actually deciding.

Fill in the `parameters` of the node with id `hitl_review` in
`/workspace/workflow.json` (currently an empty stub) so it implements that
review step, using the customer/amount values already set on `tool_refund`.
Also replace that node's placeholder `name` ("Tool") with a specific label
describing what a reviewer is actually doing when they open it, rather than
a generic name.

Leave every other node, its parameters, and all node ids exactly as they are.
The file must remain valid JSON.
