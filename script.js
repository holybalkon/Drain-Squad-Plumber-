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
