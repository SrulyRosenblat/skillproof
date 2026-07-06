# Task: Build an order/user reporting script

You are given three JSON fixtures describing a small e-commerce dataset:

- `/workspace/data/users.json` — an array of user objects: `{ id, name, isAdmin, isTester, isActive }`
- `/workspace/data/orders.json` — an array of order objects: `{ id, userId, amount }`
- `/workspace/data/tag_pairs.json` — an array of `{ id, current, original }` objects, where `current` and `original` are each arrays of tag strings (order does not matter; duplicates matter — `["a","a","b"]` and `["a","b","b"]` are different multisets)

Write a **plain CommonJS Node.js script** at `/workspace/solve.js` that can be run with `node solve.js` (cwd `/workspace`, Node 20, no npm packages available — use only the `fs`/`path` built-ins) and produces exactly these three output files under `/workspace/output/`:

### 1. `output/enriched_orders.json`

An array with one entry per order in `orders.json`, in the same order, where each entry contains all of the original order's fields plus a `user` field:

- If `order.userId` matches a `user.id` in `users.json`, `user` must be that full user object.
- If there is no match, `user` must be `null`.

### 2. `output/user_categories.json`

A single JSON object with three keys, each an array of user `id`s **in the same relative order they appear in `users.json`**:

- `admins`: ids of users where `isAdmin` is true
- `testers`: ids of users where `isTester` is true
- `inactive`: ids of users where `isActive` is false

(Note: a user can belong to more than one category, e.g. an inactive tester.)

### 3. `output/tag_changes.json`

An array with one entry per pair in `tag_pairs.json`, in the same order, of the form `{ "id": <pair id>, "changed": <boolean> }`. `changed` is `true` if `current` and `original` represent different multisets of tags (different length, or same length but different tag counts), and `false` if they represent the exact same multiset (regardless of ordering).

## Requirements

- `/workspace/solve.js` must run standalone via `node solve.js` and create the `output/` directory itself if it doesn't exist.
- The output must be exact — every id, join, category membership, and changed flag must be correct.
- These fixtures are a sample of a much larger production dataset (hundreds of thousands of users/orders/tag pairs in reality). Your script needs to scale to that size, so avoid any approach whose total work grows quadratically (or worse) with the input size — for example, repeatedly scanning one whole list for every item of another, doing several independent full passes over the same list when one pass would do, or performing an expensive comparison before a cheap one that could rule it out first.
- Do not use any external npm packages — only Node.js built-ins.

When you're done, `/workspace/solve.js` should be the only new file needed; running it will produce the `output/` directory with the three files described above.
