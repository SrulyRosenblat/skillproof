# Task: Trim the server-to-client payload for a dashboard page

`/workspace` contains a small Node.js simulation of a server-rendered dashboard
page:

- `/workspace/data-source.js` — the data layer. Exports `fetchUsers()` and
  `fetchProduct()`, each returning a full record with many internal fields
  (contact info, HR metadata, warehouse/supplier info, etc.).
- `/workspace/server-page.js` — the server-side page logic. Exports
  `renderPage()`, which loads data and returns the exact payload that gets
  sent over the network to the client-rendered `Dashboard` component:

  ```js
  {
    component: 'Dashboard',
    props: { /* ... sent to the client ... */ },
  }
  ```

The `Dashboard` client component only ever reads the following out of `props`:

1. **User directory** — for every user, their `name` and `email` (plus enough
   identifying info to use as a list key).
2. **Active users panel** — the `name` of each user who is currently active,
   listed alphabetically.
3. **Product info panel** — the product's `name` and `price`.

`Dashboard` is fully capable of figuring out things like "which users are
active" and "alphabetical order" on its own from the user list it's given —
it does not need those views handed to it pre-built.

## Your task

Edit `/workspace/server-page.js` so that the `props` object returned by
`renderPage()`:

- Still contains everything `Dashboard` needs to render all three parts
  described above, with correct data.
- Contains no field, on any record, that `Dashboard` never reads.
- Represents each underlying piece of information (each user's data, the
  product's data) exactly once — don't include the same value under more
  than one prop, and don't include both a full record and a separately
  extracted piece of that same record.

You should not need to change `data-source.js` — it represents an existing
data layer outside the scope of this task.

## Output contract

- Modify only `/workspace/server-page.js`.
- Keep `module.exports = { renderPage }`.
- `renderPage()` must keep returning `{ component: 'Dashboard', props: {...} }`
  (a synchronous plain object — no Promises, no JSX).
- Inside `props`, keep the list of users under a key named `users`, where each
  entry is a plain object keyed by `id`, `name`, `email`, and `active`.
- Represent the product either as a single object under a key named `product`
  containing only `name` and `price`, OR as two top-level scalar props named
  `productName` and `productPrice`. Pick exactly one of these two
  representations — don't mix them.
