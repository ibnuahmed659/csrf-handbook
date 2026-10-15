/* search.js — full-text search across the whole handbook (headings, body,
   lists, tables and code) using the generated index. */
(function () {
  'use strict';

  var INDEX = Array.isArray(window.SEARCH_INDEX) ? window.SEARCH_INDEX : [];
  var MAX_RESULTS = 40;
  var els = {};
  var activeIndex = -1;
  var results = [];

  function chapterDir() {
    return document.body.getAttribute('data-chapterdir') || '';
  }

  function entryUrl(entry) {
    var base = chapterDir() + entry.partId + '.html';
    return entry.id ? base + '#' + entry.id : base;
  }

  function tokenize(q) {
    return q.toLowerCase().split(/\s+/).map(function (s) { return s.trim(); }).filter(Boolean);
  }

  function score(entry, terms) {
    var hay = entry.text.toLowerCase();
    var head = (entry.heading || '').toLowerCase();
    var s = 0;
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i];
      var idx = hay.indexOf(t);
      if (idx === -1) return 0; // every term must appear (AND)
      s += 1 + Math.min(4, (hay.split(t).length - 1)); // occurrences
      if (head.indexOf(t) !== -1) s += 6;
      if (entry.type === 'heading') s += 2;
      if (idx < 40) s += 1;
    }
    return s;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function excerpt(text, terms) {
    var lower = text.toLowerCase();
    var at = -1;
    for (var i = 0; i < terms.length; i++) {
      var idx = lower.indexOf(terms[i]);
      if (idx !== -1 && (at === -1 || idx < at)) at = idx;
    }
    var start = at > 60 ? at - 50 : 0;
    var chunk = text.slice(start, start + 180);
    return (start > 0 ? '\u2026' : '') + escapeHtml(chunk) + (start + 180 < text.length ? '\u2026' : '');
  }

  function highlightTerms(html, terms) {
    var out = html;
    terms.forEach(function (t) {
      if (!t) return;
      var re = new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      out = out.replace(re, '<mark>$1</mark>');
    });
    return out;
  }

  function render(query) {
    var terms = tokenize(query);
    els.results.innerHTML = '';
    activeIndex = -1;
    results = [];

    if (!terms.length) {
      els.hint.hidden = false;
      els.hint.textContent = 'Qor eray si aad uga raadiso buugga oo dhan.';
      return;
    }

    var scored = [];
    for (var i = 0; i < INDEX.length; i++) {
      var s = score(INDEX[i], terms);
      if (s > 0) scored.push({ e: INDEX[i], s: s });
    }
    scored.sort(function (a, b) { return b.s - a.s; });
    results = scored.slice(0, MAX_RESULTS).map(function (x) { return x.e; });

    if (!results.length) {
      els.hint.hidden = true;
      var empty = document.createElement('li');
      empty.className = 'search-results__empty';
      empty.textContent = 'Wax natiijo ah lama helin "' + query + '".';
      els.results.appendChild(empty);
      return;
    }

    els.hint.hidden = true;
    results.forEach(function (entry, idx) {
      var li = document.createElement('li');
      li.className = 'search-results__item';
      li.setAttribute('role', 'option');
      var a = document.createElement('a');
      a.href = entryUrl(entry);
      a.dataset.index = String(idx);
      var crumb = document.createElement('div');
      crumb.className = 'search-results__crumb';
      crumb.textContent = entry.part + ' \u2022 ' + (entry.type === 'heading' ? 'cinwaan' : entry.type);
      var title = document.createElement('div');
      title.className = 'search-results__title';
      title.innerHTML = highlightTerms(escapeHtml(entry.heading || entry.text.slice(0, 80)), terms);
      var ex = document.createElement('div');
      ex.className = 'search-results__excerpt';
      ex.innerHTML = highlightTerms(excerpt(entry.text, terms), terms);
      a.appendChild(crumb); a.appendChild(title); a.appendChild(ex);
      li.appendChild(a);
      els.results.appendChild(li);
    });
  }

  function move(delta) {
    if (!results.length) return;
    activeIndex = (activeIndex + delta + results.length) % results.length;
    var links = els.results.querySelectorAll('a');
    Array.prototype.forEach.call(links, function (a, i) {
      a.classList.toggle('is-active', i === activeIndex);
      if (i === activeIndex) {
        a.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  function open(initial) {
    els.modal.hidden = false;
    document.body.style.overflow = 'hidden';
    els.input.value = initial || '';
    render(els.input.value);
    setTimeout(function () { els.input.focus(); }, 20);
  }

  function close() {
    els.modal.hidden = true;
    document.body.style.overflow = '';
    els.input.value = '';
    els.results.innerHTML = '';
    els.hint.hidden = false;
  }

  function init() {
    els.modal = document.getElementById('search-modal');
    els.input = document.getElementById('search-input');
    els.results = document.getElementById('search-results');
    els.hint = document.getElementById('search-hint');
    if (!els.modal) return;

    var openBtn = document.getElementById('search-open');
    if (openBtn) openBtn.addEventListener('click', function () { open(''); });

    Array.prototype.forEach.call(document.querySelectorAll('[data-search-close]'), function (el) {
      el.addEventListener('click', close);
    });

    els.input.addEventListener('input', function () { render(els.input.value); });

    els.input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') {
        var active = els.results.querySelector('a.is-active') || els.results.querySelector('a');
        if (active) window.location.href = active.href;
      }
    });

    document.addEventListener('keydown', function (e) {
      var tag = (e.target.tagName || '').toLowerCase();
      var typing = tag === 'input' || tag === 'textarea' || e.target.isContentEditable;
      if (e.key === '/' && !typing && els.modal.hidden) {
        e.preventDefault(); open('');
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault(); open('');
      } else if (e.key === 'Escape' && !els.modal.hidden) {
        close();
      }
    });

    // deep-link support: /?q=term  or  #search=term
    var q = new URLSearchParams(window.location.search).get('q');
    if (q) open(q);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
