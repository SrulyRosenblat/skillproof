# Benchmark: Trim duplicate and unused fields from an RSC-to-client payload

## Capability tested

This benchmark targets the "3.2 Avoid Duplicate Serialization in RSC Props" and
"3.6 Minimize Serialization at RSC Boundaries" rules from the
`vercel-react-best-practices` skill:

- **3.2**: React Server Component → Client Component serialization dedupes by
  object *reference*, not by value. If a server component computes a derived
  view of some data (`.filter()`, `.sort()`, `.map()`, spreads, etc.) and sends
  both the original and the derived view as separate props, the underlying
  values get serialized twice, because the derived view is a new object/array
  reference. The fix is to send the raw data once and let the client derive
  the view itself.
- **3.6**: The RSC boundary serializes whatever fields are present, so a
  server component should only forward the fields the client component
  actually reads — not the entire record.

Both rules together describe a common anti-pattern: a server component that
"helpfully" precomputes a filtered/sorted subset *and* forwards full records
"just in case," roughly doubling (or worse) the payload sent to the client
for no functional benefit.

## Why it matters

Excess or duplicated serialization directly inflates the RSC payload embedded
in the initial HTML response and in subsequent RSC navigation requests. This
is pure waste: every extra byte here is a byte the client has to download and
parse before it can do anything, with zero benefit since the client either
already has the data (in the un-derived form) or never reads it at all. A
coding agent that has internalized this rule will recognize both symptoms at
once — "this field is never read by the client" and "this array is just a
`.filter().sort()` of something already being sent" — and fix both, rather
than only trimming record fields (a more generic, commonly-known optimization)
while leaving the duplicated derived array in place.

## Task setup

`files/` contains a small Node.js simulation of a Next.js RSC page, kept
dependency-free (no React/Next/TypeScript toolchain is available in the
sandbox) so it can be executed directly and its output asserted on:

- `data-source.js` — a data layer returning full user records (11 fields each,
  most of them HR/contact metadata irrelevant to the UI) and a full product
  record (8 fields, mostly warehouse/supplier metadata irrelevant to the UI).
- `server-page.js` — the buggy "server component." Its `renderPage()`
  function returns the exact props payload that would cross the RSC boundary.
  It has two problems at once:
  1. It forwards the full `users` array *and* a separately computed
     `activeUsersSorted` array (`.filter().sort().map()` — a new reference),
     duplicating every active user's name.
  2. It forwards the entire `product` record (unused fields like `sku`,
     `description`, `warehouseLocation`, ...) *and* separately extracted
     `productName` / `productPrice` scalars, duplicating those two values.

The task prompt describes exactly what the client component reads (full
directory of name/email, an alphabetically-sorted active-users name list, and
product name/price) without naming the underlying rule or its mechanics, and
asks the model to edit `server-page.js` so the payload contains each piece of
data exactly once and excludes anything the client never reads.

## Grading

`grader/grade.sh` runs `grader/check.js` with Node against `/workspace`. It:

1. Loads `/workspace/server-page.js` and calls the exported `renderPage()`.
2. Executes the real returned data structure (no source-text/grep matching)
   and asserts, structurally:
   - `props.users` has exactly the 4 expected users, each with the correct
     `id`/`name`/`email`/`active` values and *no other keys* (catches
     unrelated/unused fields leaking through).
   - The top-level keys of `props` are exactly `{users, product}` or
     `{users, productName, productPrice}` — no extra key is present. This
     directly catches a lingering duplicated/derived array (e.g.
     `activeUsersSorted`) or a full `product` object left alongside trimmed
     scalars, since either would introduce an extra top-level key.
   - Whichever product representation is used, `name`/`price` are correct and
     no other product fields are present.
3. Exits 0 only if every check passes; otherwise prints the specific failure
   and exits non-zero.

This is deterministic (no randomness, no clock, no network) and re-runnable:
same workspace contents in, same verdict out. The grader was verified to fail
on the untouched `files/` fixture (duplicated/unused fields present) and pass
on `reference_solution/`, as well as on hand-written variants that use the
other valid product representation, and to reject variants that still
duplicate data (kept a derived array, or mixed both product representations).

## Reference solution

`reference_solution/server-page.js` maps each fetched user down to
`{id, name, email, active}` (dropping the 7 unused fields) and sends the
`users` array once with no separately precomputed active/sorted view — the
client is expected to derive that itself from the same array. For the
product, it forwards only `productName` and `productPrice` as scalars instead
of the full record, and does not also include a `product` object. This
satisfies both rules simultaneously: no field is serialized that the client
doesn't read, and no value is serialized under more than one prop.
