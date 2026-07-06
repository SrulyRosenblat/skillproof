#!/usr/bin/env node
'use strict';

const path = require('path');

const MOD_PATH = path.resolve(process.cwd(), 'lib/global-listeners.js');

function fail(msg) {
  console.error('FAIL:', msg);
  process.exit(1);
}

function ok(msg) {
  console.log('PASS:', msg);
}

function makeWindowMock() {
  const listeners = {}; // type -> array of { handler, options }
  const calls = { add: [], remove: [] };
  return {
    addEventListener(type, handler, options) {
      calls.add.push({ type, options });
      if (!listeners[type]) listeners[type] = [];
      listeners[type].push(handler);
    },
    removeEventListener(type, handler) {
      calls.remove.push({ type });
      if (listeners[type]) {
        listeners[type] = listeners[type].filter((h) => h !== handler);
      }
    },
    dispatch(type, eventObj) {
      (listeners[type] || []).forEach((h) => h(eventObj));
    },
    activeCount(type) {
      return (listeners[type] || []).length;
    },
    addCallCount(type) {
      return calls.add.filter((c) => c.type === type).length;
    },
    removeCallCount(type) {
      return calls.remove.filter((c) => c.type === type).length;
    },
    lastAddOptions(type) {
      const matches = calls.add.filter((c) => c.type === type);
      if (matches.length === 0) return undefined;
      return matches[matches.length - 1].options;
    },
  };
}

function freshModule(windowMock) {
  try {
    delete require.cache[require.resolve(MOD_PATH)];
  } catch {
    // not yet required, ignore
  }
  global.window = windowMock;

  let mod;
  try {
    mod = require(MOD_PATH);
  } catch (e) {
    fail('module threw while loading: ' + e.message);
  }

  const required = ['registerShortcut', 'registerScrollTracker', 'createMobileModeWatcher'];
  for (const name of required) {
    if (typeof mod[name] !== 'function') {
      fail(`module.exports.${name} must be a function`);
    }
  }
  return mod;
}

// ---------------------------------------------------------------------------
// Test A: keyboard shortcut listener deduplication
// ---------------------------------------------------------------------------
{
  const win = makeWindowMock();
  const mod = freshModule(win);

  let cb1Calls = 0;
  let cb2Calls = 0;
  let cb3Calls = 0;

  const unregister1 = mod.registerShortcut('p', () => cb1Calls++);
  const unregister2 = mod.registerShortcut('k', () => cb2Calls++);
  const unregister3 = mod.registerShortcut('p', () => cb3Calls++);

  if (win.addCallCount('keydown') !== 1) {
    fail(
      `registering 3 shortcuts should attach exactly 1 underlying keydown listener, ` +
      `but window.addEventListener('keydown', ...) was called ${win.addCallCount('keydown')} time(s)`
    );
  }

  win.dispatch('keydown', { metaKey: true, key: 'p' });
  if (cb1Calls !== 1 || cb3Calls !== 1 || cb2Calls !== 0) {
    fail(`dispatching a 'p' shortcut should fire both 'p' callbacks and not the 'k' callback (got cb1=${cb1Calls}, cb3=${cb3Calls}, cb2=${cb2Calls})`);
  }

  win.dispatch('keydown', { metaKey: true, key: 'k' });
  if (cb2Calls !== 1 || cb1Calls !== 1 || cb3Calls !== 1) {
    fail(`dispatching a 'k' shortcut should fire only the 'k' callback (got cb1=${cb1Calls}, cb2=${cb2Calls}, cb3=${cb3Calls})`);
  }

  win.dispatch('keydown', { metaKey: false, key: 'p' });
  if (cb1Calls !== 1 || cb3Calls !== 1) {
    fail('a keydown event without metaKey must not fire shortcut callbacks');
  }

  // Unregister one of the two 'p' registrations; the other must keep working
  // and the underlying listener must still be attached (still in use).
  unregister1();
  if (win.activeCount('keydown') !== 1) {
    fail('unregistering one of several active registrations must not remove the shared listener while others remain active');
  }
  win.dispatch('keydown', { metaKey: true, key: 'p' });
  if (cb3Calls !== 2) {
    fail('the remaining "p" registration must keep firing after a sibling registration is unregistered');
  }
  if (cb1Calls !== 1) {
    fail('an unregistered callback must not fire anymore');
  }

  // Unregister everything else -> underlying listener must be torn down.
  unregister2();
  unregister3();
  if (win.activeCount('keydown') !== 0) {
    fail('once every registration is unregistered, the underlying keydown listener must be removed from window');
  }
  if (win.removeCallCount('keydown') < 1) {
    fail('window.removeEventListener("keydown", ...) was never called even though all registrations were unregistered');
  }

  // Registering again afterward must re-attach a real listener (ref-counting,
  // not a one-shot "attach once ever" flag).
  let cb4Calls = 0;
  mod.registerShortcut('z', () => cb4Calls++);
  if (win.addCallCount('keydown') !== 2) {
    fail('after the shared listener was fully torn down, registering a new shortcut must attach it again');
  }
  win.dispatch('keydown', { metaKey: true, key: 'z' });
  if (cb4Calls !== 1) {
    fail('a shortcut registered after a full teardown/re-attach cycle must still fire');
  }
}
ok('keyboard shortcut listener deduplication');

// ---------------------------------------------------------------------------
// Test B: passive wheel listener for scroll tracking
// ---------------------------------------------------------------------------
{
  const win = makeWindowMock();
  const mod = freshModule(win);

  const seenDeltas = [];
  const unregister = mod.registerScrollTracker((deltaY) => seenDeltas.push(deltaY));

  const options = win.lastAddOptions('wheel');
  if (!options || typeof options !== 'object' || options.passive !== true) {
    fail(
      `registerScrollTracker must attach its 'wheel' listener in a way that lets the browser scroll ` +
      `immediately without waiting on the listener (window.addEventListener('wheel', handler, options) ` +
      `was called with options=${JSON.stringify(options)}, expected an object with passive: true)`
    );
  }

  win.dispatch('wheel', { deltaY: 42 });
  win.dispatch('wheel', { deltaY: -7 });
  if (seenDeltas.length !== 2 || seenDeltas[0] !== 42 || seenDeltas[1] !== -7) {
    fail(`onScroll should have been called with each event's deltaY, got ${JSON.stringify(seenDeltas)}`);
  }

  unregister();
  win.dispatch('wheel', { deltaY: 100 });
  if (seenDeltas.length !== 2) {
    fail('after unregister(), onScroll must not be called for subsequent wheel events');
  }
}
ok('passive wheel listener for scroll tracking');

// ---------------------------------------------------------------------------
// Test C: mobile-mode watcher only fires on boundary crossings
// ---------------------------------------------------------------------------
{
  const win = makeWindowMock();
  const mod = freshModule(win);

  let enableCalls = 0;
  let disableCalls = 0;
  const watcher = mod.createMobileModeWatcher(1024, {
    onEnable: () => enableCalls++,
    onDisable: () => disableCalls++,
  });

  if (enableCalls !== 0 || disableCalls !== 0) {
    fail('constructing the watcher must not itself trigger onEnable/onDisable');
  }

  watcher.update(1024); // no-op, still desktop
  watcher.update(900); // still desktop
  if (enableCalls !== 0 || disableCalls !== 0) {
    fail('updates that stay in desktop mode must not trigger any callback');
  }

  watcher.update(767); // crosses into mobile
  if (enableCalls !== 1 || disableCalls !== 0) {
    fail(`crossing below 768 must call onEnable exactly once (got enable=${enableCalls}, disable=${disableCalls})`);
  }

  // These must NOT re-trigger onEnable even though every value is different
  // and each one individually satisfies width < 768.
  watcher.update(766);
  watcher.update(700);
  watcher.update(750);
  watcher.update(320);
  if (enableCalls !== 1) {
    fail(`onEnable must only fire on the transition into mobile mode, not on every update while already mobile (got ${enableCalls} calls)`);
  }
  if (disableCalls !== 0) {
    fail('onDisable must not fire while still in mobile mode');
  }

  watcher.update(768); // crosses back to desktop
  if (disableCalls !== 1 || enableCalls !== 1) {
    fail(`crossing back to >= 768 must call onDisable exactly once (got enable=${enableCalls}, disable=${disableCalls})`);
  }

  watcher.update(800);
  watcher.update(1200);
  if (disableCalls !== 1) {
    fail(`onDisable must only fire on the transition out of mobile mode, not on every update while already desktop (got ${disableCalls} calls)`);
  }

  // A second crossing in each direction must still work (ongoing tracking,
  // not a one-shot latch).
  watcher.update(500);
  if (enableCalls !== 2) {
    fail('the watcher must detect and fire a second entry into mobile mode later in its lifetime');
  }
  watcher.update(1000);
  if (disableCalls !== 2) {
    fail('the watcher must detect and fire a second exit from mobile mode later in its lifetime');
  }
}
ok('mobile-mode watcher only fires on boundary crossings');

console.log('ALL CHECKS PASSED');
process.exit(0);
