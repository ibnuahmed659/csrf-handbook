/* animations.js — premium motion layer
   Scroll reveal, animated statistics, hero entrance, gentle parallax and
   ambient illustration motion. Everything degrades gracefully and is
   disabled under prefers-reduced-motion. */
(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  /* ---------------- scroll reveal ---------------- */
  function initReveal() {
    var items = document.querySelectorAll('[data-reveal], .reveal-hero');
    if (!items.length) return;

    if (reduce || !('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(items, function (el) { el.classList.add('is-visible'); });
      return;
    }

    var io = new IntersectionObserver(function (entries, obs) {
      var batch = 0;
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        el.style.setProperty('--reveal-i', String(batch++));
        el.classList.add('is-visible');
        obs.unobserve(el);
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });

    Array.prototype.forEach.call(items, function (el) { io.observe(el); });
  }

  /* ---------------- hero entrance ---------------- */
  function initHero() {
    var hero = document.querySelector('.hero__inner');
    if (!hero) return;
    var els = hero.querySelectorAll('.hero__eyebrow, .hero__title, .hero__lead, .hero__actions, .hero__stats, .hero__scene');
    Array.prototype.forEach.call(els, function (el, i) {
      el.classList.add('reveal-hero');
      if (reduce) { el.classList.add('is-visible'); return; }
      setTimeout(function () { el.classList.add('is-visible'); }, 120 + i * 110);
    });
  }

  /* ---------------- animated counters ---------------- */
  function initCounters() {
    var nums = document.querySelectorAll('[data-count]');
    if (!nums.length) return;

    function run(el) {
      var target = parseFloat(el.getAttribute('data-count')) || 0;
      var suffix = el.getAttribute('data-suffix') || '';
      if (reduce) { el.textContent = target + suffix; return; }
      var start = null, dur = 1100;
      function tick(ts) {
        if (start === null) start = ts;
        var p = Math.min(1, (ts - start) / dur);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(target * eased) + suffix;
        if (p < 1) window.requestAnimationFrame(tick);
      }
      window.requestAnimationFrame(tick);
    }

    if (!('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(nums, run);
      return;
    }
    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { run(e.target); obs.unobserve(e.target); }
      });
    }, { threshold: 0.4 });
    Array.prototype.forEach.call(nums, function (el) { io.observe(el); });
  }

  /* ---------------- gentle parallax on hero scene ---------------- */
  function initParallax() {
    if (reduce) return;
    var scene = document.querySelector('.hero__scene');
    if (!scene) return;
    var layers = scene.querySelectorAll('[data-depth]');
    if (!layers.length) return;
    var raf = false;
    window.addEventListener('mousemove', function (e) {
      if (raf) return;
      raf = true;
      window.requestAnimationFrame(function () {
        var cx = (e.clientX / window.innerWidth - 0.5);
        var cy = (e.clientY / window.innerHeight - 0.5);
        Array.prototype.forEach.call(layers, function (l) {
          var d = parseFloat(l.getAttribute('data-depth')) || 6;
          l.style.transform = 'translate3d(' + (-cx * d) + 'px,' + (-cy * d) + 'px,0)';
        });
        raf = false;
      });
    }, { passive: true });
  }

  /* ---------------- ambient mascot blink ---------------- */
  function initBlink() {
    var eyes = document.querySelectorAll('[data-blink]');
    if (!eyes.length || reduce) return;
    setInterval(function () {
      Array.prototype.forEach.call(eyes, function (eye) {
        eye.classList.add('is-blinking');
        setTimeout(function () { eye.classList.remove('is-blinking'); }, 140);
      });
    }, 3800);
  }

  /* ---------------- subtle 3D tilt on cards ---------------- */
  function initTilt() {
    if (reduce) return;
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    var cards = document.querySelectorAll('.part-card, .feature-card');
    Array.prototype.forEach.call(cards, function (card) {
      card.addEventListener('mousemove', function (e) {
        var r = card.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5;
        var py = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = 'translateY(-6px) perspective(760px) rotateX(' +
          (-py * 4).toFixed(2) + 'deg) rotateY(' + (px * 5).toFixed(2) + 'deg)';
      });
      card.addEventListener('mouseleave', function () {
        card.style.transform = '';
      });
    });
  }

  ready(function () {
    window.__csrfAnim = true;
    initHero();
    initReveal();
    initCounters();
    initParallax();
    initBlink();
    initTilt();
  });
})();
