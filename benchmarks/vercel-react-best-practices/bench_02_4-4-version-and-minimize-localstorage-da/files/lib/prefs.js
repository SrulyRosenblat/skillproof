// lib/prefs.js
//
// Stores the current user's UI preferences (theme, language) in the browser
// so they persist across page loads, and provides a way to apply the saved
// theme to the DOM before the app finishes loading.
//
// NOTE: this is a first draft. It works on a happy path but has not been
// hardened yet.

function saveUserPrefs(user) {
  localStorage.setItem('userPrefs', JSON.stringify(user));
  return true;
}

function loadUserPrefs() {
  const data = localStorage.getItem('userPrefs');
  return data ? JSON.parse(data) : null;
}

function getStoredTheme() {
  const data = localStorage.getItem('userPrefs');
  if (!data) return null;
  return JSON.parse(data).theme;
}

function clearPrefsCache() {
  // nothing to clear yet
}

function getThemeBootstrapScript() {
  return '';
}

module.exports = {
  saveUserPrefs,
  loadUserPrefs,
  getStoredTheme,
  clearPrefsCache,
  getThemeBootstrapScript,
};
