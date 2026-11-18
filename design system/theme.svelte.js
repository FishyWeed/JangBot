// Rainy night (dark, default) / Misty dawn (light): sets data-theme on <html>. A saved choice wins.
const KEY = 'jangbot-theme';

export const theme = $state({ current: /** @type {'light' | 'dark'} */ ('dark') });

function apply(/** @type {string} */ next, persist = true) {
  theme.current = next === 'light' ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme.current;
  if (persist) {
    try { localStorage.setItem(KEY, theme.current); } catch {}
  }
}

/** Call once on mount (e.g. in +layout.svelte). */
export function initTheme() {
  if (typeof window === 'undefined') return;
  let saved = null;
  try { saved = localStorage.getItem(KEY); } catch {}
  apply(saved ?? 'dark', false);
}

export function setTheme(/** @type {'light' | 'dark'} */ next) { apply(next); }
export function toggleTheme() { apply(theme.current === 'dark' ? 'light' : 'dark'); }
