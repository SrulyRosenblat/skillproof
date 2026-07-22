---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    Two non-default n8n binary-data conventions have to be diagnosed and
    fixed together, and neither is spelled out in the prompt. First, `json`
    and `binary` are separate namespaces on an item, so a transform node
    that rewrites `json` does not automatically carry `binary` along with
    it - the starter workflow's Edit Fields node feeds straight into Merge
    with only one branch wired, so the original attachment is simply gone
    by the time it would reach the email node. A model that doesn't know
    this split plausibly pokes at node parameters near the email step and
    never notices the attachment was dropped two nodes earlier, or "fixes"
    it by wiring the bypass onto the same Merge input the transformed
    branch already uses (index collision, still no distinct binary path)
    instead of a separate, distinct, in-range input index. The starter
    file also doesn't let a model get the index for free by pattern-matching
    a canonical "transform on input 0, bypass on input 1" example: Edit
    Fields already occupies input 1, so a model that assumes the bypass
    always lands on input 1 (rather than computing which slot is actually
    free) collides with it instead of landing on the one free slot, input
    0. The prompt also no longer describes Merge's combine-by-position
    behavior up front, so a model has to read the node's own parameters to
    learn it needs a second branch at all, instead of being told the
    architecture. Second, the key
    inside `binary` is an arbitrary producer-chosen name, not always the
    'data' default - the webhook here names its slot 'invoice', but the
    email node's `binaryPropertyName` is left at the generic default, so
    even once the bytes are wired through, the consumer looks for a slot
    that doesn't exist. A model that assumes 'data' is always right without
    checking what the producer actually named its slot leaves this half
    fixed. Both checks are deterministic and don't depend on guessing a
    specific string - they compare the workflow's own producer/consumer
    values and connection graph against each other. Two further gates catch
    plausible-looking fixes that get the headline wiring right but miss the
    supporting detail. A model unsure whether the bypass wiring alone is
    enough often hedges by also flipping a pass-through/options flag on Edit
    Fields (e.g. an `includeOtherFields`-style key) so that node tries to
    carry binary too - overlooking that MERGE_FOR_CONTEXT.md frames the
    Merge-bypass and the transform-node-pass-through as alternatives, not a
    belt-and-suspenders combination: once the bypass branch is wired, Edit
    Fields' own parameters need zero changes, and the fix is checked against
    the exact original parameter dict. Separately, a model that hand-writes
    the new connection as a fresh entry appended to the outer `main` list
    (rather than as a sibling inside the trigger's single existing output-port
    array) produces a connections block that looks graph-complete under a
    naive walk but is structurally a second output pin the single-output
    webhook node doesn't have, so n8n would never fire it - the fix has to
    land inside the one real output port, not merely reference the right
    node names somewhere under `main`.
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
    - binary-data
    - merge-node
    - webhook
    - workflow-automation
    - node-configuration
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

`/workspace/workflow.json` is an n8n workflow export with four nodes:
**Invoice Webhook** receives an uploaded invoice file from a customer,
**Edit Fields** updates a couple of status fields on the item, **Merge**
sits in between, and **Send Invoice Email** emails the result back out
with the invoice attached.

Customers keep reporting that the emails they get back have the right
subject line and the right status text, but the invoice attachment is
always missing or empty. The workflow hasn't been touched since it was
exported, and its `resource`/`operation`/`mode` settings are all exactly as
intended - nothing about *what* each node is configured to do needs to
change.

Fix `/workspace/workflow.json` in place so that **Send Invoice Email**
actually goes out with the same invoice file **Invoice Webhook** received,
byte-for-byte, alongside the status fields **Edit Fields** sets. Figure out
where the attachment is currently getting lost between the webhook and the
email node, and correct whatever combination of wiring and parameters is
needed so the email node ends up with a working reference to it.

Don't rename any node, don't change any node's `mode`/`resource`/`operation`
value, and don't remove the existing connections between
**Invoice Webhook → Edit Fields** and **Merge → Send Invoice Email**.
`workflow.json` must remain valid JSON with the same four nodes when you're
done.
