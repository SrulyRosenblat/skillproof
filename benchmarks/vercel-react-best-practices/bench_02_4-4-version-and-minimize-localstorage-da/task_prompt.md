# Harden the user-preferences storage module

Your app persists a signed-in user's UI preferences (theme and language) in the
browser so they survive page reloads. The current implementation, at
`/workspace/lib/prefs.js`, is a rough first draft. Your job is to rewrite it so
it is safe to ship.

`/workspace/lib/prefs.js` is a plain **CommonJS** Node module (`module.exports`,
no bundler, no TypeScript, no JSX). It runs in a browser-like environment where a
global `localStorage` object exists, but it must be defensive: `localStorage`
access can throw at any time (private browsing, quota exceeded, storage
disabled, etc.), so nothing in this module may ever throw.

A sample of the object your code receives is at
`/workspace/fixtures/full-user-example.json`. Only two fields from it matter to
the UI: `preferences.theme` and `preferences.language`. Every other field —
including `id`, `email`, `passwordHash`, `authToken`, `internalFlags`,
`createdAt`, `billingPlan`, and even the sibling preference fields
`notifications` and `marketingOptIn` — must never be written to storage.

Rewrite `/workspace/lib/prefs.js` so it exports exactly these five functions
(same names, same shape of `module.exports`):

1. **`saveUserPrefs(user)`** — Persists only `user.preferences.theme` and
   `user.preferences.language`. Returns `true` if the write succeeded. If the
   underlying storage write fails, it must catch the failure and return
   `false` instead of throwing.

2. **`loadUserPrefs()`** — Returns `{ theme, language }` read back from
   storage, or `null` if nothing is stored, the read fails, or the stored data
   can't be parsed. Must never throw. The returned object must not contain any
   fields beyond `theme` and `language`.

3. **`getStoredTheme()`** — Returns just the saved theme (or `null` if none).
   This can be called many times back-to-back (e.g. once per render). Only
   the *first* call in such a run should actually hit the underlying storage
   API — repeated calls with no intervening save must not re-read storage.
   On a storage failure it returns `null` rather than throwing.

4. **`clearPrefsCache()`** — Drops any in-memory cache built up by the
   functions above, so the next read goes back to storage. Must be callable
   at any time (e.g. after another tab changes the value) without throwing.

5. **`getThemeBootstrapScript()`** — Returns a **string** of plain,
   framework-free JavaScript (no imports/exports, no JSX, no React, no
   hooks — just something that could be pasted directly into a bare
   `<script>` tag and run standalone, before any hydration or framework code
   executes). When that string is executed, it must:
   - read the persisted theme from storage,
   - fall back to the literal string `"light"` if nothing is stored or the
     read fails,
   - set that value as the `className` of the DOM element whose `id` is
     `theme-root` (only if such an element exists),
   - and never let an exception escape, no matter what storage or the DOM
     does.

**One more requirement that ties it all together:** whichever storage key(s)
you use must encode an explicit version as part of the key name — a pattern
like `somename:v1` (letters/digits/underscore/hyphen, then a literal `:v`,
then a number). `saveUserPrefs`, `loadUserPrefs`, `getStoredTheme`, and
`getThemeBootstrapScript` must all agree on the same key.

## Deliverable

Only modify `/workspace/lib/prefs.js`. Keep it a CommonJS module exporting
exactly the five functions above with those exact names. Do not change
`/workspace/fixtures/full-user-example.json`.
