document.documentElement.classList.remove('no-js');
document.documentElement.classList.add('js');

(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Mobile menu
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');
  if (toggle && nav) {
    var setMenu = function (open) {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    };
    toggle.addEventListener('click', function () { setMenu(!nav.classList.contains('is-open')); });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) { setMenu(false); } });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { setMenu(false); toggle.focus(); } });
    document.addEventListener('click', function (e) { if (!e.target.closest('.site-header')) { setMenu(false); } });
  }

  // Header shadow once the page is scrolled
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Scroll reveal with a small stagger between siblings
  var revealSel = '.sec-head, .offers-head, .why-head, .team-head, .svc-card, .price-card, .price-note, .offer, ' +
    '.how-panel, .step, .review, .gsummary, .form-card, .faq-item, .locate-info, .paybar-text, .paybar-cta, .chips li';
  var targets = document.querySelectorAll(revealSel);
  if (!reduceMotion && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    targets.forEach(function (el) {
      var sibs = el.parentElement ? Array.prototype.filter.call(el.parentElement.children, function (c) { return c.matches(revealSel); }) : [];
      el.style.transitionDelay = (Math.min(sibs.indexOf(el), 5) * 90) + 'ms';
      el.classList.add('js-reveal');
      io.observe(el);
    });
  }

  // Highlight the nav link of the section in view (home page)
  var navLinks = document.querySelectorAll('.nav a[href*="#"]');
  if ('IntersectionObserver' in window && navLinks.length) {
    var map = {};
    navLinks.forEach(function (a) { map[a.getAttribute('href').split('#')[1]] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var a = map[e.target.id];
        if (a && e.isIntersecting) {
          navLinks.forEach(function (l) { l.classList.remove('is-active'); });
          a.classList.add('is-active');
        }
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    Object.keys(map).forEach(function (id) { var s = document.getElementById(id); if (s) { spy.observe(s); } });
  }

  // FAQ accordion: collapse after load; answers stay in the DOM
  document.querySelectorAll('.faq-item').forEach(function (item) {
    var btn = item.querySelector('.faq-trigger');
    if (!btn) { return; }
    btn.setAttribute('aria-expanded', 'false');
    btn.addEventListener('click', function () {
      var open = item.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  // Team carousel arrows (home page only)
  var track = document.getElementById('team-track');
  document.querySelectorAll('[data-team-scroll]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (!track) { return; }
      var dir = Number(b.getAttribute('data-team-scroll'));
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      track.scrollBy({ left: dir * track.clientWidth * 0.8, behavior: reduce ? 'auto' : 'smooth' });
    });
  });

  // Print a single offer card (home page only)
  function clearPrint() {
    document.querySelectorAll('.offer.printing').forEach(function (el) { el.classList.remove('printing'); });
  }
  window.addEventListener('afterprint', clearPrint);
  document.querySelectorAll('[data-print]').forEach(function (b) {
    b.addEventListener('click', function () {
      var card = b.closest('.offer');
      if (!card) { return; }
      card.classList.add('printing');
      window.print();
      clearPrint();
    });
  });

  // Styled dropdown: replaces the look of <select>, keeps it as the source of truth
  document.querySelectorAll('.field select').forEach(function (sel) {
    var wrap = document.createElement('div');
    wrap.className = 'select';
    sel.parentNode.insertBefore(wrap, sel);
    wrap.appendChild(sel);
    sel.classList.add('select-native');
    sel.tabIndex = -1;
    sel.setAttribute('aria-hidden', 'true');

    var label = document.querySelector('label[for="' + sel.id + '"]');
    if (label && !label.id) { label.id = sel.id + '-label'; }

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'select-btn';
    btn.setAttribute('aria-haspopup', 'listbox');
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-controls', sel.id + '-list');
    if (label) { btn.setAttribute('aria-labelledby', label.id + ' ' + sel.id + '-value'); }
    var value = document.createElement('span');
    value.className = 'select-value';
    value.id = sel.id + '-value';
    btn.appendChild(value);

    var list = document.createElement('ul');
    list.className = 'select-list';
    list.id = sel.id + '-list';
    list.setAttribute('role', 'listbox');
    if (label) { list.setAttribute('aria-labelledby', label.id); }

    var items = Array.prototype.map.call(sel.options, function (opt, i) {
      var li = document.createElement('li');
      li.setAttribute('role', 'option');
      li.id = sel.id + '-opt-' + i;
      li.textContent = opt.text;
      if (opt.value === '') { li.className = 'is-placeholder'; }
      li.addEventListener('mousedown', function (e) { e.preventDefault(); });
      li.addEventListener('click', function () { choose(i); });
      li.addEventListener('mousemove', function () { setActive(i); });
      list.appendChild(li);
      return li;
    });
    wrap.appendChild(btn);
    wrap.appendChild(list);

    var active = 0;
    function render() {
      var o = sel.options[sel.selectedIndex];
      value.textContent = o ? o.text : '';
      btn.classList.toggle('is-placeholder', !o || o.value === '');
      items.forEach(function (li, i) { li.setAttribute('aria-selected', String(i === sel.selectedIndex)); });
    }
    function setActive(i) {
      active = Math.max(0, Math.min(items.length - 1, i));
      items.forEach(function (li, j) { li.classList.toggle('is-active', j === active); });
      btn.setAttribute('aria-activedescendant', items[active].id);
      var el = items[active];
      if (el.offsetTop < list.scrollTop) { list.scrollTop = el.offsetTop - 6; }
      else if (el.offsetTop + el.offsetHeight > list.scrollTop + list.clientHeight) { list.scrollTop = el.offsetTop + el.offsetHeight - list.clientHeight + 6; }
    }
    function isOpen() { return wrap.classList.contains('is-open'); }
    function open() {
      wrap.classList.add('is-open');
      btn.setAttribute('aria-expanded', 'true');
      setActive(sel.selectedIndex < 0 ? 0 : sel.selectedIndex);
    }
    function close() {
      wrap.classList.remove('is-open');
      btn.setAttribute('aria-expanded', 'false');
      btn.removeAttribute('aria-activedescendant');
    }
    function choose(i) {
      sel.selectedIndex = i;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      render();
      close();
      btn.focus();
    }

    btn.addEventListener('click', function () { if (isOpen()) { close(); } else { open(); } });
    btn.addEventListener('keydown', function (e) {
      var k = e.key;
      if (k === 'ArrowDown' || k === 'ArrowUp') {
        e.preventDefault();
        if (!isOpen()) { open(); } else { setActive(active + (k === 'ArrowDown' ? 1 : -1)); }
      } else if (k === 'Home' && isOpen()) { e.preventDefault(); setActive(0); }
      else if (k === 'End' && isOpen()) { e.preventDefault(); setActive(items.length - 1); }
      else if (k === 'Enter' || k === ' ') {
        e.preventDefault();
        if (isOpen()) { choose(active); } else { open(); }
      } else if (k === 'Escape' && isOpen()) { e.preventDefault(); close(); }
      else if (k === 'Tab') { close(); }
      else if (k.length === 1 && /\S/.test(k)) {
        var start = isOpen() ? active + 1 : sel.selectedIndex + 1;
        for (var n = 0; n < items.length; n++) {
          var idx = (start + n) % items.length;
          if (items[idx].textContent.charAt(0).toLowerCase() === k.toLowerCase()) {
            if (isOpen()) { setActive(idx); } else { choose(idx); }
            break;
          }
        }
      }
    });
    document.addEventListener('click', function (e) { if (!wrap.contains(e.target)) { close(); } });
    if (label) { label.addEventListener('click', function (e) { e.preventDefault(); btn.focus(); }); }
    if (sel.form) { sel.form.addEventListener('reset', function () { setTimeout(render, 0); }); }
    render();
  });

  // Contact form
  var form = document.getElementById('lead-form');
  if (form) {
    var status = document.getElementById('form-status');
    var btn = form.querySelector('button[type="submit"]');

    // TODO: replace with the real form endpoint (CRM, email service or webhook).
    function sendRequest(data) {
      return new Promise(function (resolve) { setTimeout(resolve, 400); });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      btn.disabled = true;
      btn.textContent = 'Sending…';
      status.className = 'form-status';
      status.textContent = '';
      sendRequest(new FormData(form)).then(function () {
        form.reset();
        status.className = 'form-status ok';
        status.textContent = 'Got it! We’ve received your request and will be in touch shortly.';
      }).catch(function () {
        status.className = 'form-status err';
        status.textContent = 'Something went wrong. Please try again or call us.';
      }).then(function () {
        btn.disabled = false;
        btn.textContent = 'Send request';
      });
    });
  }
})();
