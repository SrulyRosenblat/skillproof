# Benchmark: Harden a localStorage preferences module

## Capability tested

This benchmark checks whether an agent applies three related
`vercel-react-best-practices` rules together, in a single realistic piece of
code (a "current user preferences" storage module):

- **`client-localstorage-schema`** (4.4) — storage keys must encode an
  explicit schema version, only the fields the UI actually needs should be
  persisted (never tokens/PII/internal flags), and every `localStorage` call
  must be wrapped so a thrown error (private browsing, quota exceeded,
  disabled storage) never propagates.
- **`js-cache-storage`** (7.5) — repeated reads of the same key should hit an
  in-memory cache instead of re-invoking the synchronous, expensive
  `localStorage` API on every call, with an explicit way to invalidate that
  cache.
- **`rendering-hydration-no-flicker`** (6.5) — client-only data (like a saved
  theme) that needs to be visible immediately, without an SSR crash and
  without a post-hydration flash of the wrong value, should be applied via a
  synchronous bootstrap script that runs before hydration rather than via
  `useEffect` + `setState`.

An agent unfamiliar with these rules will typically produce something close
to the shipped starter (`files/lib/prefs.js`): an unversioned key, the whole
user object serialized wholesale, no error handling, no caching, and no
flicker-free bootstrap mechanism — each of which is checked independently by
the grader.

## Task given to the model

The model is told to rewrite `/workspace/lib/prefs.js` (a CommonJS module) so
it exposes five specific functions (`saveUserPrefs`, `loadUserPrefs`,
`getStoredTheme`, `clearPrefsCache`, `getThemeBootstrapScript`) that satisfy a
precise behavioral contract — described entirely in terms of *what* the
functions must do (never throw, only persist two named fields, avoid
redundant reads, produce a safe standalone bootstrap script) without
mentioning the underlying technique names (versioning, memoization, inline
script injection) so the benchmark actually measures whether the agent
independently arrives at those techniques.

## Grading

`grader/grade.sh` runs `grader/check.js` under Node (no browser/DOM
dependency — everything is verified through plain execution):

1. **Test A — versioning + minimization.** Installs an in-memory
   `localStorage` mock, calls `saveUserPrefs()` with a realistic "full user"
   fixture (`files/fixtures/full-user-example.json`) that contains sensitive
   fields (`passwordHash`, `authToken`, `email`, …) alongside the two needed
   preference fields. Asserts every key written to storage matches a
   versioned pattern (`name:v<N>`), that none of the sensitive fixture values
   leaked into storage, that stored values contain only `theme`/`language`,
   and that `loadUserPrefs()` round-trips correctly without leaking extra
   fields.
2. **Test B — error resilience.** Swaps in a `localStorage` mock whose
   `getItem`/`setItem` always throw, and asserts `saveUserPrefs`,
   `loadUserPrefs`, `getStoredTheme`, and `clearPrefsCache` all degrade
   gracefully (return `false`/`null`, never throw).
3. **Test C — caching.** Calls `getStoredTheme()` several times in a row with
   an instrumented storage mock and asserts the underlying `getItem` call
   count does not increase on repeated calls, then asserts it increases again
   after `clearPrefsCache()` is called (proving the cache genuinely
   invalidates rather than never reading storage).
4. **Test D — hydration-safe bootstrap script.** Runs the string returned by
   `getThemeBootstrapScript()` inside a Node `vm` sandbox with a fake
   `document`/`localStorage`, and asserts it: applies the stored theme as the
   target element's `className`, falls back to `"light"` when nothing is
   stored, and never lets an exception escape even when storage throws or the
   target element is missing.

All four tests execute the produced code directly (via `require()` and
`vm.runInContext`) rather than pattern-matching its source, so any
implementation strategy that satisfies the behavioral contract passes.

The grader exits non-zero (and prints the first failing assertion) on the
first violation. It fails on the untouched starter file (unversioned key) and
passes on `reference_solution/lib/prefs.js`, which implements the module with
a versioned key, a `Map`-backed read cache, try/catch around every storage
call, and a template-generated inline bootstrap script.

## Reference solution

`reference_solution/lib/prefs.js` stores minimized preferences under
`userPrefs:v1`, wraps every `localStorage` call in try/catch, caches reads in
a module-level `Map` (cleared by `clearPrefsCache`), and generates a
self-contained bootstrap script string that reads the same versioned key,
falls back to `'light'`, and swallows any error.
