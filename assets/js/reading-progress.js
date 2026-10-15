/* reading-progress.js — top progress bar + back-to-top control */
(function () {
  'use strict';

  function init() {
    var bar = document.getElementById('reading-progress-bar');
    var backTop = document.getElementById('back-to-top');
    var ticking = false;

    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        var doc = document.documentElement;
        var max = doc.scrollHeight - doc.clientHeight;
        var pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
        if (bar) bar.style.width = pct.toFixed(2) + '%';
        if (backTop) backTop.hidden = doc.scrollTop < 600;
        ticking = false;
      });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    onScroll();

    if (backTop) backTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: prefersReduced() ? 'auto' : 'smooth' });
    });
  }

  function prefersReduced() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
