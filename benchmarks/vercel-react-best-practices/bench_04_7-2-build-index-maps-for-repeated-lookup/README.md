# Benchmark: Build Index Maps for Repeated Lookups

## Capability tested

This benchmark targets three related JavaScript-performance rules from the
`vercel-react-best-practices` skill (cluster 7):

- **7.2 Build Index Maps for Repeated Lookups** — replace repeated
  `array.find()` calls keyed by id with a `Map` built once, turning O(n) lookups
  into O(1).
- **7.6 Combine Multiple Array Iterations** — replace several independent
  `.filter()` passes over the same array with a single pass that buckets items
  as it goes.
- **7.8 Early Length Check for Array Comparisons** — check `.length` before
  running an expensive order-insensitive comparison (sorting), since arrays of
  different length can never be equal.

These are exactly the anti-patterns and fixes described in
`rules/js-index-maps.md`, `rules/js-combine-iterations.md`, and
`rules/js-length-check-first.md`. A model that has internalized these rules
will reach for a `Map`, a single categorization pass, and a length guard
without being told to; a model that hasn't will very likely reproduce the
"incorrect" examples from those rule files (`users.find(...)` inside
`orders.map(...)`, three separate `.filter()` calls, `sort().join()` on every
pair) because those are the natural/idiomatic way to write this logic without
the optimization in mind.

## Task given to the model

The model is given three JSON fixtures (`users.json`, `orders.json`,
`tag_pairs.json`, each with ~2000 records / 300 pairs) and must write a single
Node.js script, `/workspace/solve.js`, that:

1. Joins each order to its user by `userId` (`enriched_orders.json`).
2. Buckets users into `admins` / `testers` / `inactive` categories
   (`user_categories.json`).
3. Detects whether each tag-pair's `current` vs `original` arrays represent a
   changed multiset (`tag_changes.json`).

The prompt describes the required output precisely, and tells the model the
data represents a much larger production dataset so its script "needs to
scale" and should avoid quadratic-or-worse approaches — without naming Map,
`.find()`, or any specific technique. This keeps the gap between "solves the
stated problem" and "solves it the way the skill teaches" exactly where the
benchmark needs it.

## How grading works

Grading never inspects `solve.js`'s source code (no string/AST matching).
Instead `grader/grade.sh`:

1. Fails immediately if `/workspace/solve.js` doesn't exist.
2. Deletes any pre-existing `/workspace/output/` so results reflect only this
   run.
3. Executes the script with `node -r grader/instrument.js solve.js`.
   `instrument.js` monkey-patches `Array.prototype.find`, `.filter`, `.sort`,
   and `.toSorted` *before* `solve.js` loads, counting how many times each
   callback actually fires (i.e. how many elements were scanned), and dumps
   the tally to a JSON file on process exit.
4. Runs `grader/check.py`, which:
   - Recomputes the expected `enriched_orders` / `user_categories` /
     `tag_changes` content directly from the fixtures in Python (independent
     of any particular algorithm) and diffs it against what `solve.js` wrote —
     this is the functional-correctness gate.
   - Reads the instrumentation counts and asserts they're consistent with the
     efficient patterns rather than their naive equivalents:
     - `findCallbackInvocations < 20,000` — an index-map join never calls
       `.find()` on the users array at all (count 0); a per-order
       `users.find(...)` over ~2000 users produces roughly two million
       predicate invocations.
     - `filterCallbackInvocations < 3,000` — a single combined pass never
       calls `.filter()` (count 0); three separate `.filter()` passes over
       ~2000 users produce 6,000.
     - `sortInvocations < 400` — checking length first only needs to sort the
       ~100 pairs that are actually equal-length (≈200 sort/`toSorted` calls);
       unconditionally sorting all 300 pairs produces 600.

This means the grader genuinely executes the produced artifact and observes
its runtime behavior, rather than grepping for `new Map` or a particular
`if` statement — any implementation strategy that achieves the same
call-count profile passes, and any that doesn't (regardless of how it's
phrased in source) fails.

Both thresholds were calibrated against a reference-quality solution (all
counts comfortably under threshold) and a deliberately naive solution using
the exact "incorrect" patterns from the skill's rule files (all three counts
comfortably over threshold — see counts in the calibration below), with wide
margins in both directions so the check isn't sensitive to minor
implementation variation.

| metric | good (reference) | naive | threshold |
|---|---|---|---|
| `findCallbackInvocations` | 0 | ~2,005,305 | < 20,000 |
| `filterCallbackInvocations` | 0 | 6,000 | < 3,000 |
| `sortInvocations` | 200 | 600 | < 400 |

## Reference solution

`reference_solution/solve.js` builds a `Map<userId, user>` once and uses
`.get()` for every order, categorizes users in one `for...of` loop pushing
into three arrays, and checks `current.length !== original.length` before
sorting and comparing — i.e. it applies rules 7.2, 7.6, and 7.8 directly.
