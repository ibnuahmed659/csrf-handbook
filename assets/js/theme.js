/* theme.js — dark/light theme switching with persistence */
(function () {
  'use strict';

  var STORAGE_KEY = 'csrf-theme';
  var root = document.documentElement;

  function current() {
    return root.getAttribute('data-theme') || 'dark';
  }

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) {}
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      var isLight = theme === 'light';
      btn.setAttribute('aria-pressed', String(isLight));
      btn.setAttribute('title', isLight ? 'Beddel mawduuca mugdiga' : 'Beddel mawduuca iftiinka');
    }
  }

  function init() {
    var saved = null;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    if (!saved) {
      saved = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }
    apply(saved);

    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.addEventListener('click', function () {
        apply(current() === 'dark' ? 'light' : 'dark');
      });
    }

    // react to OS changes only if the user has not chosen explicitly
    try {
      window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function (e) {
        if (!localStorage.getItem(STORAGE_KEY)) {
          apply(e.matches ? 'light' : 'dark');
        }
      });
    } catch (e) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
