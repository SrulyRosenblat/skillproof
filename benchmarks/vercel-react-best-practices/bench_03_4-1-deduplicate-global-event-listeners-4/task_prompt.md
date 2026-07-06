# Harden the shared global-listener helpers

`/workspace/lib/global-listeners.js` is a plain **CommonJS** module (`module.exports`,
no bundler, no TypeScript, no JSX, no framework) used by many independent
widgets across a web app. It runs in a browser-like environment where a
global `window` object exists with standard `addEventListener` /
`removeEventListener` methods. The current file is a rough first draft that
only behaves correctly when a single widget uses each helper at a time.
Harden it for real-world usage, where many widgets use these helpers
simultaneously and mount/unmount independently over time.

Rewrite `/workspace/lib/global-listeners.js` so it exports exactly these
three functions (same names, same shape of `module.exports`), each satisfying
the contract below:

## 1. `registerShortcut(key, callback)`

Lets a widget react to a global keyboard shortcut. Returns an `unregister()`
function.

- `window` will dispatch `keydown` events with a boolean `metaKey` property
  and a `key` property (e.g. `'p'`, `'k'`). Your callback must fire whenever
  a `keydown` event arrives with `metaKey: true` and `key` equal to the
  requested key.
- Any number of widgets may call `registerShortcut` at the same time,
  including more than once for the *same* key (all matching callbacks must
  fire) and for *different* keys (each callback only fires for its own key).
- No matter how many active registrations exist, the module must never have
  more than one underlying `keydown` listener attached to `window` at once.
- When the last active registration for the whole module is unregistered,
  the underlying `window` listener must be removed. If something registers
  again afterward, the underlying listener must be re-attached (i.e. this
  must be a live, ongoing accounting of active registrations, not a one-time
  "attach once ever" flag).
- Calling the `unregister()` function returned for one registration must
  never affect other still-active registrations (their callbacks keep
  firing).

## 2. `registerScrollTracker(onScroll)`

Lets a widget observe wheel-scroll activity for analytics purposes only —
it never needs to block or alter the scroll. Returns an `unregister()`
function.

- `window` will dispatch `wheel` events with a numeric `deltaY` property.
  Call `onScroll(deltaY)` for each event while a registration is active.
- Because this listener only reads data and never calls
  `preventDefault()`, it must be attached in a way that lets the browser
  start scrolling immediately instead of waiting to see whether the
  listener will block the scroll.
- After `unregister()` is called, `onScroll` must not be invoked for
  subsequent events.

## 3. `createMobileModeWatcher(initialWidth, { onEnable, onDisable })`

Tracks whether the viewport is currently in "mobile mode" (width `< 768`)
and triggers expensive mode-switch callbacks — `onEnable()` when entering
mobile mode, `onDisable()` when leaving it. Returns an object with an
`update(width)` method.

- `initialWidth` sets the starting mode silently — it must **not** trigger
  `onEnable` or `onDisable` on its own.
- Calling `update(width)` afterward must invoke `onEnable()` or
  `onDisable()` **only at the exact moment the width crosses the 768px
  boundary** in that direction.
- Calling `update(width)` repeatedly with values that stay on the same side
  of the boundary (e.g. shrinking from 750 to 740 to 700) must **not**
  invoke either callback again — even though every individual call passes a
  different width.
- The watcher must correctly detect and fire on every subsequent crossing,
  in either direction, for the lifetime of the object (not just the first
  one).

## Deliverable

Only modify `/workspace/lib/global-listeners.js`. Keep it a CommonJS module
exporting exactly `registerShortcut`, `registerScrollTracker`, and
`createMobileModeWatcher` with those exact names and signatures.
