# Benchmark: Harden shared global-listener helpers

## Capability tested

This benchmark checks whether an agent applies three related
`vercel-react-best-practices` rules together in one realistic module of
helpers shared by many independent UI widgets:

- **`client-event-listeners`** (4.1) — when many component instances each
  want to react to the same global event (a keyboard shortcut), the
  underlying `window` listener should be shared/deduplicated rather than
  attaching one physical listener per instance, and the shared listener
  should be torn down once nothing needs it and re-attached if something
  needs it again later (a live ref-count, not a one-time flag).
- **`client-passive-event-listeners`** (4.2) — a `wheel` listener that only
  reads data for analytics and never calls `preventDefault()` must be
  attached in a way that doesn't force the browser to wait on it before
  scrolling (i.e. as a passive listener).
- **`rerender-dependencies`** (5.7) — expensive mode-switch work driven by a
  derived boolean (`width < 768`) must fire only on the boolean's
  transitions, not on every raw value change that happens to satisfy the
  condition.

An agent unfamiliar with these rules will typically produce something close
to the shipped starter (`files/lib/global-listeners.js`): one listener
attached per `registerShortcut()` call, a non-passive `wheel` listener, and a
mobile-mode watcher that re-fires `onEnable`/`onDisable` on every `update()`
call instead of only at the boundary crossing.

## Task given to the model

The model is told to rewrite `/workspace/lib/global-listeners.js` (a
CommonJS module) so it exports three functions
(`registerShortcut`, `registerScrollTracker`, `createMobileModeWatcher`)
satisfying a precise behavioral contract, phrased entirely in terms of
observable behavior (call counts, invocation timing, event shapes) rather
than the underlying technique names — it never mentions "passive", "Map",
"Set", "ref-count", or "derived boolean". This means the benchmark actually
measures whether the agent independently arrives at those techniques instead
of copying a keyword from the prompt.

## Grading

`grader/grade.sh` runs `grader/check.js` under Node (no browser/React/SWR
dependency — everything is verified by executing the produced module
directly against an instrumented `window` mock):

1. **Test A — keyboard shortcut deduplication.** Installs a `window` mock
   that records every `addEventListener`/`removeEventListener` call and
   lets the test dispatch synthetic events to whatever handlers were
   registered. Registers three shortcuts (two for `'p'`, one for `'k'`) and
   asserts exactly one `keydown` listener was attached. Dispatches synthetic
   `keydown` events and asserts the right callbacks fire (and that a
   non-metaKey event fires none). Unregisters one of the two `'p'`
   registrations and asserts the shared listener stays attached and the
   remaining callback still fires. Unregisters everything else and asserts
   the shared listener is actually removed. Registers a new shortcut
   afterward and asserts the listener is re-attached and works — proving a
   genuine live ref-count rather than a "the first N calls don't add a
   listener" special case or a permanent single-listener hack.
2. **Test B — passive scroll tracking.** Asserts `addEventListener('wheel',
   handler, options)` was called with `options.passive === true`, then
   dispatches synthetic `wheel` events and checks `onScroll` receives the
   right `deltaY` values, and that unregistering stops further calls.
3. **Test C — mobile-mode boundary crossings.** Constructs the watcher at an
   initial width and asserts construction alone triggers nothing. Feeds it a
   sequence of `update(width)` calls that stay within the desktop regime,
   then cross into mobile, then wobble around inside the mobile regime
   (750 → 700 → 320), then cross back to desktop, then wobble inside desktop,
   then cross into mobile a second time and back out a second time — and
   asserts `onEnable`/`onDisable` fire exactly once per actual crossing and
   never on the same-regime wobbles, in either direction, repeatedly over
   the object's lifetime.

All three tests execute the produced code directly rather than pattern-
matching its source, so any implementation strategy that satisfies the
behavioral contract passes. The grader exits non-zero (printing the first
failing assertion) on the first violation. It fails on the untouched starter
file (one listener per registration, non-passive wheel listener, callbacks
fire on every qualifying `update()`) and passes on
`reference_solution/lib/global-listeners.js`.

## Reference solution

`reference_solution/lib/global-listeners.js` keeps a module-level
`Map<key, Set<callback>>` plus a single shared `keydown` handler that is
attached lazily and removed once the map is empty; attaches the `wheel`
listener with `{ passive: true }`; and tracks the mobile-mode boolean in a
closure variable, invoking `onEnable`/`onDisable` only when that boolean
actually flips.
