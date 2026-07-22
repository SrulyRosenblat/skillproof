---
schema_version: '1.3'
metadata:
  author_name: Sruly Rosenblat
  author_email: srulyrosenblat@gmail.com
  difficulty: hard
  difficulty_explanation: >-
    Several non-default conventions have to be applied together, and none of
    them is spelled out in the prompt. First, every item this Code node
    hands back has to be wrapped n8n-style — a dict carrying its data under
    a top-level `json` key — rather than the plain records a general-purpose
    JSON-cleaning script would return; get this wrong and the node's whole
    output is unrecognizable even though every value in it is correct.
    Second, a batch with one malformed payload must still yield an item for
    every input, in order, which rules out both leaving parsing
    unprotected (the node dies on the first bad payload) and wrapping the
    whole loop in a single try/except (which drops every item after the
    first failure) — errors have to be caught per item. Third, "valid JSON"
    has to mean actual JSON, not Python's own literal syntax: JSON's
    lowercase true/false/null are not valid Python literals, and Python's
    single-quoted, capitalized-bool dict literals are not valid JSON, so a
    solution that reaches for `ast.literal_eval` or `eval` instead of
    `json.loads` mis-classifies both directions. Finally, the batch summary
    has to be re-serialized into an actual JSON string, not left as a nested
    object. A model without this specific knowledge plausibly returns bare
    records instead of `json`-wrapped items, or picks a parsing shortcut
    that silently mis-classifies some payloads — both of which the checks
    catch deterministically, and against a hidden batch the sample values
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
    - json
    - error-handling
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

`/workspace/code.py` is the body of an n8n Code node (Python) that will run
against a batch of items arriving from an upstream node. `/workspace/input.json`
holds a sample of that batch in n8n's item format — inside the node you'd
reach it through `_input.all()`. Each item's `json.payload` field holds a
string that is *supposed* to be JSON-encoded, but not every one of them
actually is.

`/workspace/node_runtime.py` reproduces how n8n loads and executes a Code
node's body and captures whatever it returns, so you can try your node out
locally:

```
python3 /workspace/node_runtime.py /workspace/code.py /workspace/input.json /workspace/output.json
```

The batch this node is graded against will *not* be the one sitting in
`/workspace/input.json` — it only illustrates the shape of the data (and its
mix of well-formed and malformed payloads). Write `/workspace/code.py` so it
works generically on any batch shaped like it, not just the sample.

Finish `/workspace/code.py` (plain top-level statements ending in a `return`,
the same way the body of a real Code node is written — not a script guarded
by `if __name__ == "__main__":`, and not a function you define and call
yourself) so that, run against such a batch:

- Every incoming item produces exactly one corresponding outgoing item, in
  the same order it arrived. Nothing may be silently dropped, and one
  malformed payload must not stop the rest of the batch from being
  processed.
- For an item whose `payload` is genuinely JSON, the outgoing item's data
  must carry that value already converted to native Python data (numbers as
  numbers, booleans as booleans, nested objects/arrays intact — not left as
  a string) under a field named `parsed`, with its `error` field left empty.
- For an item whose `payload` is not valid JSON, `parsed` must be empty and
  `error` must hold a non-empty description of what went wrong.
- After all of those, append exactly one more outgoing item summarizing the
  whole batch. Its data must carry a field named `manifest_json` whose value
  is itself a JSON-encoded *string* (not a nested object) representing
  `{"valid_count": <n>, "invalid_count": <n>}`, reflecting how many of the
  batch's payloads parsed successfully versus not.

Every item this node hands back — including the summary one — has to come
back in exactly the shape n8n's runtime expects an item to be in, or the
platform won't recognize it as a row of data at all.
