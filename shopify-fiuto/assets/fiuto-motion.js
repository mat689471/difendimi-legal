/* ==========================================================================
   FIUTO — Motion engine
   Native APIs only: IntersectionObserver, requestAnimationFrame, matchMedia.
   No external libraries. Every effect degrades to "no motion" cleanly and is
   fully disabled under prefers-reduced-motion.
   ========================================================================== */
(function () {
  'use strict';

  var reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  var fineQuery = window.matchMedia('(hover: hover) and (pointer: fine)');
  var reduce = reduceQuery.matches;
  var fine = fineQuery.matches;

  reduceQuery.addEventListener('change', function (e) { reduce = e.matches; });
  fineQuery.addEventListener('change', function (e) { fine = e.matches; });

  var raf = window.requestAnimationFrame.bind(window);
  var scrollTasks = [];
  var rafTasks = [];
  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    raf(function () {
      var y = window.scrollY || window.pageYOffset;
      for (var i = 0; i < scrollTasks.length; i++) scrollTasks[i](y);
      ticking = false;
    });
  }

  function loop() {
    for (var i = 0; i < rafTasks.length; i++) rafTasks[i]();
    raf(loop);
  }

  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function lerp(a, b, t) { return a + (b - a) * t; }

  /* ---------------------------------------------------------------- reveal */
  function initReveal(root) {
    var nodes = (root || document).querySelectorAll('[data-f-reveal]:not([data-f-bound])');
    if (!nodes.length) return;

    if (reduce || !('IntersectionObserver' in window)) {
      nodes.forEach(function (n) { n.setAttribute('data-f-bound', ''); n.classList.add('is-in'); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });

    nodes.forEach(function (n) {
      n.setAttribute('data-f-bound', '');
      io.observe(n);
    });
  }

  /* Stagger children of [data-f-stagger] */
  function initStagger(root) {
    (root || document).querySelectorAll('[data-f-stagger]:not([data-f-stagger-bound])').forEach(function (group) {
      group.setAttribute('data-f-stagger-bound', '');
      var step = parseInt(group.getAttribute('data-f-stagger'), 10) || 80;
      var kids = group.querySelectorAll('[data-f-reveal]');
      kids.forEach(function (kid, i) {
        kid.style.setProperty('--f-delay', (i * step) + 'ms');
      });
    });
  }

  /* --------------------------------------------------------- split headings */
  function splitWords(el) {
    if (el.getAttribute('data-f-split-done')) return;
    el.setAttribute('data-f-split-done', '');
    var step = parseInt(el.getAttribute('data-f-split'), 10) || 55;

    var walk = function (node, out) {
      node.childNodes.forEach(function (child) {
        if (child.nodeType === 3) {
          var parts = child.textContent.split(/(\s+)/);
          var frag = document.createDocumentFragment();
          parts.forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(part)); return; }
            var w = document.createElement('span');
            w.className = 'f-word';
            var inner = document.createElement('span');
            inner.textContent = part;
            w.appendChild(inner);
            frag.appendChild(w);
            out.push(inner);
          });
          child.replaceWith(frag);
        } else if (child.nodeType === 1 && !child.classList.contains('f-word')) {
          walk(child, out);
        }
      });
    };

    var words = [];
    walk(el, words);
    words.forEach(function (w, i) { w.style.setProperty('--f-delay', (i * step) + 'ms'); });
  }

  function initSplit(root) {
    var nodes = (root || document).querySelectorAll('.f-reveal-text:not([data-f-split-done])');
    if (!nodes.length) return;

    nodes.forEach(splitWords);

    if (reduce || !('IntersectionObserver' in window)) {
      nodes.forEach(function (n) { n.classList.add('is-in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('is-in');
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.15 });
    nodes.forEach(function (n) { io.observe(n); });
  }

  /* ---------------------------------------------------------------- header */
  function initHeader() {
    var body = document.body;
    var last = 0;
    var overHero = document.querySelector('[data-f-overhero]');
    body.setAttribute('data-f-overhero', overHero ? 'true' : 'false');

    scrollTasks.push(function (y) {
      var doc = document.documentElement;
      var max = doc.scrollHeight - window.innerHeight;
      body.style.setProperty('--f-page-progress', max > 0 ? (y / max).toFixed(4) : '0');

      var state = 'top';
      if (y > 24) state = 'scrolled';
      if (y > 420 && y > last + 4 && !document.body.classList.contains('f-lock')) state = 'hidden';
      if (y < last - 4) state = y > 24 ? 'scrolled' : 'top';
      last = y;
      if (body.getAttribute('data-f-header') !== state) body.setAttribute('data-f-header', state);
    });
  }

  /* ------------------------------------------------------- mouse parallax */
  function initPointerParallax() {
    var layers = Array.prototype.slice.call(document.querySelectorAll('[data-f-parallax]'));
    if (!layers.length) return;

    var target = { x: 0, y: 0 };
    var current = { x: 0, y: 0 };
    var active = false;

    function enable() {
      if (active || reduce || !fine) return;
      active = true;
      rafTasks.push(tick);
    }

    function tick() {
      current.x = lerp(current.x, target.x, 0.065);
      current.y = lerp(current.y, target.y, 0.065);
      for (var i = 0; i < layers.length; i++) {
        var depth = parseFloat(layers[i].getAttribute('data-f-parallax')) || 10;
        layers[i].style.setProperty('--f-px', (current.x * depth).toFixed(2) + 'px');
        layers[i].style.setProperty('--f-py', (current.y * depth).toFixed(2) + 'px');
      }
    }

    window.addEventListener('pointermove', function (e) {
      if (reduce || !fine) return;
      target.x = (e.clientX / window.innerWidth - 0.5) * 2;
      target.y = (e.clientY / window.innerHeight - 0.5) * 2;
      enable();
    }, { passive: true });
  }

  /* ------------------------------------------------------- scroll parallax */
  function initScrollParallax() {
    var nodes = Array.prototype.slice.call(document.querySelectorAll('[data-f-scroll-parallax]'));
    if (!nodes.length || reduce) return;

    scrollTasks.push(function () {
      var vh = window.innerHeight;
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        var rect = el.getBoundingClientRect();
        if (rect.bottom < -200 || rect.top > vh + 200) continue;
        var amount = parseFloat(el.getAttribute('data-f-scroll-parallax')) || 40;
        var progress = (rect.top + rect.height / 2 - vh / 2) / vh; /* -1..1 */
        el.style.setProperty('--f-sy', (progress * amount * -1).toFixed(2) + 'px');
      }
    });
  }

  /* ------------------------------------------------------------- magnetic */
  function initMagnet() {
    if (reduce || !fine) return;
    document.querySelectorAll('[data-f-magnet]').forEach(function (el) {
      var strength = parseFloat(el.getAttribute('data-f-magnet')) || 0.22;
      var rect = null;
      var tx = 0, ty = 0, cx = 0, cy = 0, running = false;

      function animate() {
        cx = lerp(cx, tx, 0.18);
        cy = lerp(cy, ty, 0.18);
        el.style.transform = 'translate3d(' + cx.toFixed(2) + 'px,' + cy.toFixed(2) + 'px,0)';
        if (Math.abs(cx - tx) > 0.1 || Math.abs(cy - ty) > 0.1) raf(animate);
        else { el.style.transform = 'translate3d(' + tx + 'px,' + ty + 'px,0)'; running = false; }
      }
      function kick() { if (!running) { running = true; raf(animate); } }

      el.addEventListener('pointerenter', function () { rect = el.getBoundingClientRect(); });
      el.addEventListener('pointermove', function (e) {
        if (!rect) rect = el.getBoundingClientRect();
        tx = (e.clientX - (rect.left + rect.width / 2)) * strength;
        ty = (e.clientY - (rect.top + rect.height / 2)) * strength;
        kick();
      });
      el.addEventListener('pointerleave', function () { tx = 0; ty = 0; kick(); });
    });
  }

  /* --------------------------------------------------------- scroll story */
  function initStory() {
    document.querySelectorAll('[data-f-story]').forEach(function (story) {
      var chapters = Array.prototype.slice.call(story.querySelectorAll('[data-f-chapter]'));
      var scenes = Array.prototype.slice.call(story.querySelectorAll('[data-f-scene]'));
      if (!chapters.length) return;

      function update() {
        var rect = story.getBoundingClientRect();
        var vh = window.innerHeight;
        var total = rect.height - vh;
        if (total <= 0) return;
        var p = clamp((-rect.top) / total, 0, 1);
        story.style.setProperty('--f-progress', (p * 100).toFixed(2) + '%');
        story.style.setProperty('--f-p', p.toFixed(4));

        var idx = clamp(Math.floor(p * chapters.length - 0.0001), 0, chapters.length - 1);
        if (p <= 0) idx = 0;
        if (story.getAttribute('data-f-active') !== String(idx)) {
          story.setAttribute('data-f-active', String(idx));
          chapters.forEach(function (c, i) { c.classList.toggle('is-active', i === idx); });
          scenes.forEach(function (s, i) { s.classList.toggle('is-active', i === idx); });
        }
      }

      /* Chapters are readable without JS: activate the first by default. */
      chapters[0].classList.add('is-active');
      if (scenes[0]) scenes[0].classList.add('is-active');
      if (reduce) {
        chapters.forEach(function (c) { c.classList.add('is-active'); });
        return;
      }
      scrollTasks.push(update);
      update();
    });
  }

  /* -------------------------------------------------------------- marquee */
  function initMarquee() {
    var tracks = Array.prototype.slice.call(document.querySelectorAll('[data-f-marquee]'));
    if (!tracks.length) return;

    tracks.forEach(function (track) {
      /* Duplicate content until it comfortably exceeds the viewport width. */
      var inner = track.firstElementChild;
      if (!inner) return;
      var guard = 0;
      while (track.scrollWidth < window.innerWidth * 2 && guard < 8) {
        track.appendChild(inner.cloneNode(true));
        guard++;
      }
    });

    if (reduce) return;
    var lastY = window.scrollY;
    scrollTasks.push(function (y) {
      var v = clamp((y - lastY) / 18, -3.2, 3.2);
      lastY = y;
      tracks.forEach(function (t) { t.style.setProperty('--f-skew', v.toFixed(2) + 'deg'); });
    });
  }

  /* ---------------------------------------------------------- cart bubble */
  function initCartFeedback() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-f-atc], .add-to-cart-button, button[name="add"]');
      if (!btn) return;
      btn.classList.add('is-f-loading');
      setTimeout(function () { btn.classList.remove('is-f-loading'); }, 1200);
    }, true);

    var bubble = document.querySelector('.cart-bubble');
    if (!bubble || !('MutationObserver' in window)) return;
    new MutationObserver(function () {
      bubble.classList.remove('is-f-pop');
      void bubble.offsetWidth;
      bubble.classList.add('is-f-pop');
    }).observe(bubble, { childList: true, subtree: true, characterData: true });
  }

  /* ------------------------------------------------------------ scrollbar */
  function initScrollbar() {
    if (document.querySelector('.f-scrollbar')) return;
    var bar = document.createElement('div');
    bar.className = 'f-scrollbar';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
  }

  /* ------------------------------------------------------------- bootstrap */
  function boot(root) {
    initStagger(root);
    initReveal(root);
    initSplit(root);
  }

  function init() {
    boot(document);
    initHeader();
    initPointerParallax();
    initScrollParallax();
    initMagnet();
    initStory();
    initMarquee();
    initCartFeedback();
    initScrollbar();

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    raf(loop);
    onScroll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }

  /* Re-bind after Shopify section rendering (theme editor + section updates) */
  document.addEventListener('shopify:section:load', function (e) { boot(e.target); });
  document.addEventListener('shopify:section:select', function (e) { boot(e.target); });
  window.addEventListener('pageshow', function () { boot(document); });

  window.Fiuto = { refresh: function (r) { boot(r || document); } };
})();
