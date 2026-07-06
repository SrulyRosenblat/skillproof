// lib/global-listeners.js
//
// Shared helpers that widgets across the app use to react to global browser
// events (keyboard shortcuts, wheel scrolling) and to the current viewport
// size. This is a first draft: it works when only one widget uses each
// helper, but it has not been hardened for real-world usage yet.

function registerShortcut(key, callback) {
  const handler = function (e) {
    if (e.metaKey && e.key === key) {
      callback();
    }
  };
  window.addEventListener('keydown', handler);

  return function unregister() {
    window.removeEventListener('keydown', handler);
  };
}

function registerScrollTracker(onScroll) {
  const handler = function (e) {
    onScroll(e.deltaY);
  };
  window.addEventListener('wheel', handler);

  return function unregister() {
    window.removeEventListener('wheel', handler);
  };
}

function createMobileModeWatcher(initialWidth, { onEnable, onDisable } = {}) {
  return {
    update(width) {
      if (width < 768) {
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
