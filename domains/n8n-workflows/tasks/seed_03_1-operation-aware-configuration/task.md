---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    Two non-default n8n conventions have to be applied together, and neither
    is spelled out in the prompt. First, which parameters a Slack "message"
    node needs depends on its specific operation, not on its resource alone:
    "post" needs a destination channel, while "update" needs a messageId
    identifying the message to edit instead - the same channel value a
    "post" would use is not a substitute. The starter file makes this
    concrete: the "update" node still carries a leftover channel value (as
    if cloned from a "post" node) and is missing messageId entirely, so a
    model that assumes both operations need the same fields, or that just
    leaves the pre-existing channel value alone, never adds the field that
    actually matters. Second, enabling a JSON body on the HTTP Request node
    requires a specific dependency chain rather than one flat setting:
    sendBody must be turned on before body is meaningful, and body must carry
    both contentType='json' and a nested content object before n8n will
    treat it as a valid JSON payload - setting contentType alone, or a flat
    body without the nested content object, leaves the node invalid. A model
    without this specific knowledge plausibly reuses the "post" node's
    channel for "update", invents a generic field name (e.g. ts or
    timestamp) instead of messageId, or half-configures the HTTP body (e.g.
    turning on sendBody without the nested contentType/content structure) -
    all of which the checks catch deterministically.
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
    - slack
    - http-request
    - workflow-automation
    - node-configuration
    - json
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

`/workspace/workflow.json` is an n8n workflow export with three nodes: two
Slack message nodes and one HTTP Request node. It already went through the
export pipeline's standard parameter sanitizer/normalizer, so formatting and
casing are clean - but n8n will still refuse to import it, because some of
the parameters a node needs for the specific resource/operation/method it is
configured with are simply missing. Sanitization doesn't add missing
required fields; that part is on you.

`/workspace/context.json` holds the concrete reference values this workflow
is supposed to use: the Slack channel to post into, the timestamp
identifying the earlier message that needs updating, and a contact record to
forward to a webhook.

Fix `/workspace/workflow.json` in place so it is valid to import:

- **"Post Task Notification"** posts a brand-new Slack message. Give it
  whatever parameter(s) that specific operation needs in order to actually
  post, sourced from `context.json`.
- **"Update Task Status"** updates an existing Slack message rather than
  posting a new one. Give it whatever parameter(s) *that* operation
  specifically needs to identify which message to update, sourced from
  `context.json` - don't assume it needs the same parameters as the post
  operation just because both nodes share the same resource.
- **"Send Contact Webhook"** is meant to POST a JSON body containing the
  contact record from `context.json`, but right now nothing past the HTTP
  method is turned on. Enable and populate every setting in the chain that
  has to be turned on, in order, before n8n will actually send a JSON body.

Don't rename any node, and don't change any `resource`, `operation`, or
`method` value that's already set - only fill in the parameters needed to
make each node's existing configuration valid. `workflow.json` must remain
valid JSON with the same three nodes when you're done.
