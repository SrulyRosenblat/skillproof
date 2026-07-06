// lib/prefs.js
//
// Stores the current user's UI preferences (theme, language) in the browser
// so they persist across page loads, and provides a way to apply the saved
// theme to the DOM before the app finishes loading.

const PREFS_KEY = 'userPrefs:v1';

const cache = new Map();

function readRaw(key) {
  if (cache.has(key)) {
    return cache.get(key);
  }
  let value = null;
  try {
    value = localStorage.getItem(key);
  } catch {
    value = null;
  }
  cache.set(key, value);
  return value;
}

function writeRaw(key, value) {
  try {
    localStorage.setItem(key, value);
    cache.set(key, value);
    return true;
  } catch {
    return false;
  }
}

function saveUserPrefs(user) {
  const prefs = (user && user.preferences) || {};
  const minimal = {
    theme: prefs.theme,
    language: prefs.language,
  };
  return writeRaw(PREFS_KEY, JSON.stringify(minimal));
}

function loadUserPrefs() {
  const raw = readRaw(PREFS_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return { theme: parsed.theme, language: parsed.language };
  } catch {
    return null;
  }
}

function getStoredTheme() {
  const prefs = loadUserPrefs();
  return prefs ? prefs.theme : null;
}

function clearPrefsCache() {
  cache.clear();
}

function getThemeBootstrapScript() {
  return `
(function () {
  try {
    var raw = localStorage.getItem(${JSON.stringify(PREFS_KEY)});
    var parsed = raw ? JSON.parse(raw) : null;
    var theme = (parsed && parsed.theme) || 'light';
    var el = document.getElementById('theme-root');
    if (el) el.className = theme;
  } catch (e) {}
})();
`;
}

module.exports = {
  saveUserPrefs,
  loadUserPrefs,
  getStoredTheme,
  clearPrefsCache,
  getThemeBootstrapScript,
};
