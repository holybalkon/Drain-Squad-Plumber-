document.documentElement.classList.remove('no-js');

(function () {
  'use strict';

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
