// lib/global-listeners.js
//
// Shared helpers that widgets across the app use to react to global browser
// events (keyboard shortcuts, wheel scrolling) and to the current viewport
// size.

// ---- Keyboard shortcuts ---------------------------------------------------
// Many widgets may call registerShortcut() at the same time. They must all
// share a single underlying window listener, and that listener must go away
// once nothing is registered anymore (and come back if something registers
// again later).

const shortcutCallbacks = new Map(); // key -> Set<callback>
let keydownHandler = null;

function ensureKeydownListener() {
  if (keydownHandler) return;
  keydownHandler = function (e) {
    if (!e.metaKey) return;
    const set = shortcutCallbacks.get(e.key);
    if (!set) return;
    set.forEach((cb) => cb());
  };
  window.addEventListener('keydown', keydownHandler);
}

function teardownKeydownListenerIfUnused() {
  if (shortcutCallbacks.size === 0 && keydownHandler) {
    window.removeEventListener('keydown', keydownHandler);
    keydownHandler = null;
  }
}

function registerShortcut(key, callback) {
  if (!shortcutCallbacks.has(key)) {
    shortcutCallbacks.set(key, new Set());
  }
  shortcutCallbacks.get(key).add(callback);
  ensureKeydownListener();

  return function unregister() {
    const set = shortcutCallbacks.get(key);
    if (!set) return;
    set.delete(callback);
    if (set.size === 0) {
      shortcutCallbacks.delete(key);
    }
    teardownKeydownListenerIfUnused();
  };
}

// ---- Scroll tracking -------------------------------------------------------
// This listener only observes deltaY for analytics; it never calls
// preventDefault(), so it must not be allowed to block the browser's
// scrolling fast path.

function registerScrollTracker(onScroll) {
  const handler = function (e) {
    onScroll(e.deltaY);
  };
  window.addEventListener('wheel', handler, { passive: true });

  return function unregister() {
    window.removeEventListener('wheel', handler);
  };
}

// ---- Mobile mode watcher ----------------------------------------------------
// onEnable/onDisable represent expensive mode-switch work (e.g. swapping
// entire layouts). They must fire only at the moment the viewport crosses
// the 768px breakpoint, not on every width update within the same regime.

function createMobileModeWatcher(initialWidth, { onEnable, onDisable } = {}) {
  let isMobile = initialWidth < 768;

  return {
    update(width) {
      const nextIsMobile = width < 768;
      if (nextIsMobile === isMobile) return;
      isMobile = nextIsMobile;
      if (isMobile) {
        onEnable && onEnable();
      } else {
        onDisable && onDisable();
      }
    },
  };
}

module.exports = {
  registerShortcut,
  registerScrollTracker,
  createMobileModeWatcher,
};
