/* navigation.js — off-canvas drawers, TOC accordions and scroll spy */
(function () {
  'use strict';

  function init() {
    var sidebar = document.getElementById('sidebar');
    var scrim = document.getElementById('sidebar-scrim');
    var menuToggle = document.getElementById('menu-toggle');
    var tocAside = document.getElementById('onthispage');
    var tocToggle = document.getElementById('toc-toggle');

    function openSidebar(open) {
      if (!sidebar) return;
      sidebar.classList.toggle('is-open', open);
      if (menuToggle) menuToggle.setAttribute('aria-expanded', String(open));
      if (scrim) scrim.hidden = !open;
      document.body.style.overflow = open ? 'hidden' : '';
    }

    if (menuToggle) menuToggle.addEventListener('click', function () {
      openSidebar(!sidebar.classList.contains('is-open'));
    });
    if (scrim) scrim.addEventListener('click', function () { openSidebar(false); });

    function openToc(open) {
      if (!tocAside) return;
      tocAside.classList.toggle('is-open', open);
      if (tocToggle) tocToggle.setAttribute('aria-expanded', String(open));
    }
    if (tocToggle) tocToggle.addEventListener('click', function () {
      openToc(!tocAside.classList.contains('is-open'));
    });

    // Escape closes drawers
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { openSidebar(false); openToc(false); }
    });

    // current part opens + first section accordions expanded when active
    var activePart = sidebar && sidebar.querySelector('.toc__part.is-active');
    if (activePart) {
      activePart.classList.add('is-open');
      var t = activePart.querySelector('.toc__toggle');
      if (t) t.setAttribute('aria-expanded', 'true');
    }

    // accordion toggles
    var toggles = document.querySelectorAll('.toc__toggle');
    Array.prototype.forEach.call(toggles, function (btn) {
      btn.addEventListener('click', function () {
        var li = btn.closest('.toc__part');
        var open = li.classList.toggle('is-open');
        btn.setAttribute('aria-expanded', String(open));
      });
    });

    // clicking a link inside a drawer closes it (mobile)
    if (sidebar) sidebar.addEventListener('click', function (e) {
      var a = e.target.closest('a');
      if (a && window.matchMedia('(max-width: 992px)').matches) openSidebar(false);
    });

    initScrollSpy();
  }

  /* Scroll spy: highlight the active section in the right-hand rail and TOC */
  function initScrollSpy() {
    var targets = document.querySelectorAll('.section-title, .subsection-title');
    if (!targets.length || !('IntersectionObserver' in window)) return;

    var tocLinks = {};
    document.querySelectorAll('.onthispage__list a, .toc__sections a').forEach(function (a) {
      var id = (a.getAttribute('href') || '').split('#')[1];
      if (id) tocLinks[id] = a;
    });

    var visible = new Set();

    function update() {
      var activeId = null;
      var best = Infinity;
      visible.forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        var top = Math.abs(el.getBoundingClientRect().top);
        if (top < best) { best = top; activeId = id; }
      });
      Object.keys(tocLinks).forEach(function (id) {
        tocLinks[id].classList.toggle('is-active', id === activeId);
      });
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) visible.add(entry.target.id);
        else visible.delete(entry.target.id);
      });
      update();
    }, { rootMargin: '-72px 0px -70% 0px', threshold: 0 });

    targets.forEach(function (t) { if (t.id) observer.observe(t); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
