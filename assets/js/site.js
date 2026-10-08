/* Site interactions: theme toggle, mobile menu, publication panels,
   BibTeX copy and publication filters. No dependencies. */
(function () {
  'use strict';

  var root = document.documentElement;

  /* Theme toggle. The initial theme is set inline in <head> to avoid a flash. */
  var themeBtn = document.getElementById('theme-toggle');

  function isDark() {
    return root.getAttribute('data-theme') === 'dark';
  }

  if (themeBtn) {
    themeBtn.setAttribute('aria-pressed', String(isDark()));
    themeBtn.addEventListener('click', function () {
      var next = isDark() ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* private mode */ }
      themeBtn.setAttribute('aria-pressed', String(next === 'dark'));
    });
  }

  /* Mobile menu */
  var navBtn = document.getElementById('nav-toggle');
  var nav = document.getElementById('site-nav');

  function setMenu(open) {
    nav.classList.toggle('is-open', open);
    navBtn.setAttribute('aria-expanded', String(open));
  }

  if (navBtn && nav) {
    navBtn.addEventListener('click', function () {
      setMenu(!nav.classList.contains('is-open'));
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        setMenu(false);
        navBtn.focus();
      }
    });
    document.addEventListener('click', function (e) {
      if (nav.classList.contains('is-open') && !nav.contains(e.target) && !navBtn.contains(e.target)) {
        setMenu(false);
      }
    });
  }

  /* Abstract / BibTeX panels: one open panel per publication. */
  function togglePanel(btn) {
    var panel = document.getElementById(btn.getAttribute('aria-controls'));
    if (!panel) return;
    var opening = btn.getAttribute('aria-expanded') !== 'true';
    var scope = btn.closest('.pub__body') || document;
    scope.querySelectorAll('[data-panel-toggle][aria-expanded="true"]').forEach(function (other) {
      if (other === btn) return;
      other.setAttribute('aria-expanded', 'false');
      var otherPanel = document.getElementById(other.getAttribute('aria-controls'));
      if (otherPanel) otherPanel.hidden = true;
    });
    btn.setAttribute('aria-expanded', String(opening));
    panel.hidden = !opening;
  }

  /* Copy BibTeX to the clipboard; fall back to execCommand where the
     async Clipboard API is missing or refused. */
  function legacyCopy(text) {
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () {
        if (!legacyCopy(text)) throw new Error('copy failed');
      });
    }
    return legacyCopy(text) ? Promise.resolve() : Promise.reject(new Error('copy failed'));
  }

  function copyFrom(btn) {
    var source = document.getElementById(btn.getAttribute('data-copy'));
    if (!source) return;
    var label = btn.getAttribute('data-label') || btn.textContent;
    btn.setAttribute('data-label', label);
    copyText(source.textContent).then(function () {
      btn.textContent = 'Copied';
    }, function () {
      /* Leave the text selected so it can be copied by hand. */
      btn.textContent = 'Selected';
      var range = document.createRange();
      range.selectNodeContents(source);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    });
    clearTimeout(btn._resetTimer);
    btn._resetTimer = setTimeout(function () { btn.textContent = label; }, 1800);
  }

  document.addEventListener('click', function (e) {
    var toggle = e.target.closest('[data-panel-toggle]');
    if (toggle) {
      togglePanel(toggle);
      return;
    }
    var copy = e.target.closest('[data-copy]');
    if (copy) copyFrom(copy);
  });

  /* Publication filters (Publications page). */
  var filterBar = document.querySelector('[data-pub-filters]');
  if (filterBar) {
    var pills = filterBar.querySelectorAll('[data-filter]');
    var entries = document.querySelectorAll('.pub[data-type]');
    var groups = document.querySelectorAll('.year-group');

    var applyFilter = function (filter) {
      pills.forEach(function (pill) {
        pill.setAttribute('aria-pressed', String(pill.getAttribute('data-filter') === filter));
      });
      entries.forEach(function (entry) {
        entry.hidden = filter !== 'all' && entry.getAttribute('data-type') !== filter;
      });
      groups.forEach(function (group) {
        group.hidden = !group.querySelector('.pub:not([hidden])');
      });
    };

    pills.forEach(function (pill) {
      pill.addEventListener('click', function () {
        applyFilter(pill.getAttribute('data-filter'));
      });
    });
    filterBar.hidden = false;
  }
})();
