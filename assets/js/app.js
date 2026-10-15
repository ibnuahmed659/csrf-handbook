/* app.js — copy-to-clipboard, small enhancements and progressive-enhancement flags */
(function () {
  'use strict';

  function copyText(text, btn) {
    var done = function () {
      var label = btn.querySelector('.copy-btn__label');
      var old = label ? label.textContent : '';
      btn.classList.add('is-copied');
      if (label) label.textContent = 'La nuuriyay';
      setTimeout(function () {
        btn.classList.remove('is-copied');
        if (label) label.textContent = old || 'Copy';
      }, 1600);
    };

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done).catch(function () { fallback(text, done); });
    } else {
      fallback(text, done);
    }
  }

  function fallback(text, done) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'absolute';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); done(); } catch (e) {}
    document.body.removeChild(ta);
  }

  function init() {
    document.documentElement.classList.remove('no-js');

    Array.prototype.forEach.call(document.querySelectorAll('.copy-btn'), function (btn) {
      btn.addEventListener('click', function () {
        var panel = btn.closest('.code-panel');
        var code = panel ? panel.querySelector('.code-block code') : null;
        if (code) copyText(code.textContent, btn);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
