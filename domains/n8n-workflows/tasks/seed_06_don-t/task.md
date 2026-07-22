---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    Three non-default n8n expression conventions have to be diagnosed and
    fixed together, and none of them is spelled out in the prompt. First,
    the Webhook node's path is set to an expression referencing $json - but
    a webhook's route has to be registered before any request (and thus any
    $json) exists, so n8n only ever accepts a plain static string there. A
    model that doesn't know expressions are disallowed in webhook paths
    specifically (as opposed to most other n8n parameters, where they're
    the norm) plausibly leaves it as-is, tries to "fix" the syntax while
    keeping it dynamic, or guesses at some other templated form instead of
    replacing it with a fixed string. Swapping in *any* static string is
    enough to make n8n register the route, but the check requires the
    replacement to actually be tied to what was already there - the
    webhook node's own name, or the literal ("/webhook") tail that was
    already sitting after the broken "{{$json.user_id}}" segment - rather
    than an unrelated label invented from scratch (e.g. a name lifted from
    the workflow's business purpose). A model that hasn't internalized the
    static-path convention from real n8n guidance tends to invent a
    descriptive, purpose-driven slug instead of landing on one of these;
    one that has seen the convention's own canonical examples for this
    exact broken snippet reproduces one of them. Second, the incoming webhook payload
    is delivered to downstream nodes as a wrapper object with the actual
    request payload nested one level down under a "body" key, not at the
    top level of $json - the order_id field references $json.order_id
    directly, which resolves against the wrapper and fails, when the value
    actually lives at $json.body.order_id. A model that assumes webhook
    data sits at the root of $json gets this field wrong or leaves it
    unresolvable. Third, one field is already wrapped correctly in
    $json.body but has been doubled up with an extra pair of {{ }}
    delimiters - valid n8n expressions use exactly one wrapping, and a
    double-wrapped value is not a template n8n (or this task's checks) can
    resolve at all, so it has to be collapsed back to a single wrap rather
    than patched some other way. A model unfamiliar with this specific
    failure mode may not think to look for it, since the underlying path
    reference is otherwise already correct. Every check resolves the
    workflow's expressions against the sample payload's actual structure
    rather than comparing to a hardcoded literal, and two fields are
    already correct and must survive untouched, so blanket rewrites (e.g.
    prefixing every field with "body.", or normalizing all brace nesting)
    fail as readily as leaving the bugs in place.
  category: software-engineering
  subcategory: workflow-automation
  category_confidence: low
  task_type:
    - debugging
    - configuration
  modality:
    - structured-data
  interface:
    - terminal
  skill_type:
    - domain-procedure
  tags:
    - n8n
    - expressions
    - webhook
    - workflow-automation
    - debugging
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

`/workspace/workflow.json` is an n8n export for an "Order Confirmation
Automation": a `Webhook` trigger feeds a `Format Order` node that assembles
a normalized order record from the incoming request. `/workspace/sample_input.json`
is a representative payload, structured exactly as n8n hands it to the
workflow the instant the webhook fires.

Two things are broken. First, the workflow can't be deployed at all - n8n
refuses to register the `Webhook` node's endpoint as it's currently
configured. Second, even setting that aside, the record `Format Order`
assembles doesn't match the order that actually came in: when checked
against the sample payload, some of the fields it produces are wrong or
can't be resolved at all.

Fix `/workspace/workflow.json` in place so that:

- The webhook's endpoint can actually be registered.
- For the payload in `/workspace/sample_input.json`, every field
  `Format Order` produces (`order_id`, `customer_name`, `status`, `source`)
  resolves to the value truly present in that payload.

Don't rename any node, change a node's type, alter the connections, or
touch a field that's already correct - only change the specific parameter
values that are actually broken. `sample_input.json` is read-only reference
data; leave it as is. `workflow.json` must remain valid JSON with the same
two nodes when you're done.
