#!/usr/bin/env node
'use strict';

const path = require('path');
const vm = require('vm');

const MOD_PATH = path.resolve(process.cwd(), 'lib/prefs.js');
const FIXTURE_PATH = path.resolve(process.cwd(), 'fixtures/full-user-example.json');

// Sensitive/unused values from the fixture that must never end up in storage.
const FORBIDDEN_STRINGS = [
  'usr_9f8c2d',
  'morgan@example.com',
  '$2b$12$KIXQ2f0z3n9mQeYh7ZzZ1O',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mocked.token',
  'beta_tester',
  'admin_override',
  'pro',
];

const ALLOWED_VALUE_KEYS = ['theme', 'language'];
const FORBIDDEN_LOAD_KEYS = [
  'id', 'email', 'passwordHash', 'authToken', 'internalFlags',
  'createdAt', 'billingPlan', 'notifications', 'marketingOptIn',
];

const VERSIONED_KEY_RE = /^[A-Za-z0-9_-]+:v\d+$/;

function fail(msg) {
  console.error('FAIL:', msg);
  process.exit(1);
}

function ok(msg) {
  console.log('PASS:', msg);
}

let fullUser;
try {
  fullUser = require(FIXTURE_PATH);
} catch (e) {
  fail('could not load fixture file: ' + e.message);
}

function makeStorage(opts = {}) {
  const store = opts.store || {};
  const calls = { getItem: 0, setItem: 0 };
  return {
    store,
    calls,
    getItem(key) {
      calls.getItem++;
      if (opts.throwOnGet) throw new Error('blocked getItem');
      return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null;
    },
    setItem(key, value) {
      calls.setItem++;
      if (opts.throwOnSet) throw new Error('blocked setItem');
      store[key] = String(value);
    },
    removeItem(key) {
      delete store[key];
    },
  };
}

function freshModule(storageMock) {
  try {
    delete require.cache[require.resolve(MOD_PATH)];
  } catch {
    // not yet required, ignore
  }
  global.localStorage = storageMock;

  let mod;
  try {
    mod = require(MOD_PATH);
  } catch (e) {
    fail('module threw while loading: ' + e.message);
  }

  const required = ['saveUserPrefs', 'loadUserPrefs', 'getStoredTheme', 'clearPrefsCache', 'getThemeBootstrapScript'];
  for (const name of required) {
    if (typeof mod[name] !== 'function') {
      fail(`module.exports.${name} must be a function`);
    }
  }
  return mod;
}

// ---------------------------------------------------------------------------
// Test A: versioned key + minimized fields on save/load
// ---------------------------------------------------------------------------
{
  const storage = makeStorage();
  const mod = freshModule(storage);

  let saved;
  try {
    saved = mod.saveUserPrefs(fullUser);
  } catch (e) {
    fail('saveUserPrefs threw on a healthy storage backend: ' + e.message);
  }
  if (saved !== true) fail('saveUserPrefs must return true when the underlying write succeeds');

  const keys = Object.keys(storage.store);
  if (keys.length === 0) fail('saveUserPrefs did not write anything to storage');

  for (const k of keys) {
    if (!VERSIONED_KEY_RE.test(k)) {
      fail(`storage key "${k}" does not encode a version (expected a pattern like name:v1)`);
    }
  }

  const rawDump = JSON.stringify(storage.store);
  for (const s of FORBIDDEN_STRINGS) {
    if (rawDump.includes(s)) {
      fail(`sensitive/unused fixture value "${s}" ended up in storage`);
    }
  }

  for (const k of keys) {
    let parsedVal;
    try {
      parsedVal = JSON.parse(storage.store[k]);
    } catch {
      parsedVal = null;
    }
    if (parsedVal && typeof parsedVal === 'object' && !Array.isArray(parsedVal)) {
      const disallowed = Object.keys(parsedVal).filter((vk) => !ALLOWED_VALUE_KEYS.includes(vk));
      if (disallowed.length > 0) {
        fail(`stored value under key "${k}" contains fields beyond theme/language: ${disallowed.join(', ')}`);
      }
    }
  }

  let loaded;
  try {
    loaded = mod.loadUserPrefs();
  } catch (e) {
    fail('loadUserPrefs threw: ' + e.message);
  }
  if (!loaded || loaded.theme !== fullUser.preferences.theme || loaded.language !== fullUser.preferences.language) {
    fail('loadUserPrefs did not return the theme/language that was saved');
  }
  const extraLoadKeys = Object.keys(loaded).filter((k) => !ALLOWED_VALUE_KEYS.includes(k));
  if (extraLoadKeys.length > 0) {
    fail('loadUserPrefs returned extra fields beyond theme/language: ' + extraLoadKeys.join(', '));
  }
  for (const k of FORBIDDEN_LOAD_KEYS) {
    if (Object.prototype.hasOwnProperty.call(loaded, k)) {
      fail(`loadUserPrefs leaked forbidden field "${k}"`);
    }
  }
}
ok('versioned key + field minimization');

// ---------------------------------------------------------------------------
// Test B: error resilience when the underlying storage throws
// ---------------------------------------------------------------------------
{
  const storage = makeStorage({ throwOnGet: true, throwOnSet: true });
  const mod = freshModule(storage);

  let saveResult;
  try {
    saveResult = mod.saveUserPrefs(fullUser);
  } catch (e) {
    fail('saveUserPrefs threw when the underlying storage write failed: ' + e.message);
  }
  if (saveResult !== false) fail('saveUserPrefs must return false when the underlying write fails');

  let loaded;
  try {
    loaded = mod.loadUserPrefs();
  } catch (e) {
    fail('loadUserPrefs threw when the underlying storage read failed: ' + e.message);
  }
  if (loaded !== null) fail('loadUserPrefs must return null when the underlying read fails');

  let theme;
  try {
    theme = mod.getStoredTheme();
  } catch (e) {
    fail('getStoredTheme threw when the underlying storage read failed: ' + e.message);
  }
  if (theme !== null) fail('getStoredTheme must return null when the underlying read fails');

  try {
    mod.clearPrefsCache();
  } catch (e) {
    fail('clearPrefsCache threw: ' + e.message);
  }
}
ok('error resilience');

// ---------------------------------------------------------------------------
// Test C: in-memory caching of repeated reads
// ---------------------------------------------------------------------------
{
  const storage = makeStorage();
  const mod = freshModule(storage);
  mod.saveUserPrefs(fullUser);

  const afterFirst = (() => {
    mod.getStoredTheme();
    return storage.calls.getItem;
  })();

  mod.getStoredTheme();
  mod.getStoredTheme();
  const afterRepeats = storage.calls.getItem;

  if (afterRepeats !== afterFirst) {
    fail(
      `getStoredTheme() re-read storage on repeated calls with no intervening save ` +
      `(getItem calls went from ${afterFirst} to ${afterRepeats})`
    );
  }

  mod.clearPrefsCache();
  mod.getStoredTheme();
  const afterClear = storage.calls.getItem;
  if (!(afterClear > afterRepeats)) {
    fail('after clearPrefsCache(), getStoredTheme() should read storage again, but the read count did not increase');
  }

  const theme = mod.getStoredTheme();
  if (theme !== fullUser.preferences.theme) {
    fail('getStoredTheme() returned an incorrect value');
  }
}
ok('in-memory read caching');

// ---------------------------------------------------------------------------
// Test D: hydration-safe bootstrap script
// ---------------------------------------------------------------------------
{
  const storage = makeStorage();
  const mod = freshModule(storage);
  mod.saveUserPrefs(fullUser); // theme = fullUser.preferences.theme

  const script = mod.getThemeBootstrapScript();
  if (typeof script !== 'string' || script.trim().length === 0) {
    fail('getThemeBootstrapScript() must return a non-empty string');
  }

  function runScript({ hasStoredValue, throwOnGet = false, elementExists = true }) {
    const el = { id: 'theme-root', className: '' };
    const sandbox = {
      localStorage: {
        getItem(key) {
          if (throwOnGet) throw new Error('blocked');
          if (!hasStoredValue) return null;
          return Object.prototype.hasOwnProperty.call(storage.store, key) ? storage.store[key] : null;
        },
      },
      document: {
        getElementById(id) {
          return elementExists && id === 'theme-root' ? el : null;
        },
      },
      console,
    };
    sandbox.window = sandbox;
    vm.createContext(sandbox);
    let threw = false;
    let threwMessage = '';
    try {
      vm.runInContext(script, sandbox, { timeout: 2000 });
    } catch (e) {
      threw = true;
      threwMessage = e.message;
    }
    return { threw, threwMessage, el };
  }

  let res = runScript({ hasStoredValue: true });
  if (res.threw) fail('bootstrap script threw during normal execution: ' + res.threwMessage);
  if (res.el.className !== fullUser.preferences.theme) {
    fail(`bootstrap script should set className to the stored theme ("${fullUser.preferences.theme}"), got "${res.el.className}"`);
  }

  res = runScript({ hasStoredValue: false });
  if (res.threw) fail('bootstrap script threw when nothing was stored: ' + res.threwMessage);
  if (res.el.className !== 'light') {
    fail(`bootstrap script should fall back to "light" when nothing is stored, got "${res.el.className}"`);
  }

  res = runScript({ hasStoredValue: true, throwOnGet: true });
  if (res.threw) fail('bootstrap script let an exception escape when storage access failed: ' + res.threwMessage);

  res = runScript({ hasStoredValue: true, elementExists: false });
  if (res.threw) fail('bootstrap script let an exception escape when the target element was missing: ' + res.threwMessage);
}
ok('hydration-safe bootstrap script');

console.log('ALL CHECKS PASSED');
process.exit(0);
