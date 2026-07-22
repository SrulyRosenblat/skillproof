---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: medium
  difficulty_explanation: >-
    Processing exactly one item per run makes the intuitive move to just
    hand back the computed record directly — a bare dict, or at best a
    dict wrapped once under a `json` key — since there's only one thing to
    report on. But n8n's Code node contract requires every return value,
    regardless of how many items are involved, to be a list of items, each
    carrying its data under a top-level `json` key; for a single-item run
    that means the correct return value is a list containing exactly one
    such wrapped dict, not the wrapped dict on its own. Getting this wrong
    makes the node's output invisible to n8n even though the computed
    values are all correct. Second, because this node receives its item
    straight from a Webhook trigger, the data of interest sits nested one
    level deeper than the item's own json — under a `body` field alongside
    the request's headers, params, and query — so code that reaches into
    the item's json directly for `customer` or `orders` will find nothing
    there. A model without this specific knowledge plausibly returns a bare
    or singly-wrapped record instead of a one-item list, or reads fields
    from the wrong level of nesting — both of which the checks catch
    deterministically, and against hidden invocations the sample's values
    can't be hardcoded against.
  category: software-engineering
  subcategory: workflow-automation
  category_confidence: low
  task_type:
    - transformation
    - code-generation
  modality:
    - structured-data
  interface:
    - terminal
  skill_type:
    - domain-procedure
    - tool-workflow
  tags:
    - n8n
    - code-node
    - python
    - webhook
    - return-format
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

`/workspace/code.py` is the body of an n8n Code node (Python) configured to
run once for each incoming item. `/workspace/input.json` holds a sample
invocation in n8n's item format — a one-item batch, the same shape this
node receives each time it runs. This node sits directly after a Webhook
trigger node in the workflow, so the item's `json` carries the raw incoming
HTTP request (headers, params, query, and the request body) rather than
just the data your workflow cares about.

`/workspace/node_runtime.py` reproduces how n8n loads and executes a Code
node's body in this mode, so you can try your node out locally:

```
python3 /workspace/node_runtime.py /workspace/code.py /workspace/input.json /workspace/output.json
```

The invocation this node is graded against will *not* be the one sitting in
`/workspace/input.json` — it only illustrates the shape of the data. Write
`/workspace/code.py` so it works generically on any single-item invocation
shaped like it, not just the sample.

Finish `/workspace/code.py` (plain top-level statements ending in a
`return`, the same way the body of a real Code node is written — not a
script guarded by `if __name__ == "__main__":`, and not a function you
define and call yourself) so that, run against such an invocation, this
node's output data carries:

- `customer`: the customer name from the request body.
- `order_count`: how many line items are in the request body's `orders`
  list (zero if there are none).
- `total_amount`: the sum of `amount * quantity` across every line item in
  `orders` (zero if there are none), accurate to at least two decimal
  places.

Whatever this node hands back has to come back in exactly the shape n8n's
runtime expects a Code node's return value to be in for a single-item run,
or the platform won't recognize it as a row of data at all — even though
this run only ever has one item to report on.
