// Vanilla-JS navigator for the charla deck.
// Contract documented in reference/html-deck-architecture.md.
// Motion (scripts/motion.js, window.Motion) only adds entrances; CSS classes remain the source of truth.

(() => {
  const slides = Array.from(document.querySelectorAll('main#deck > section.slide'));
  if (slides.length === 0) return;

  const params = new URLSearchParams(location.search);
  const isPresenter = params.get('presenter') === '1';

  // --- motion guards ---
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const M = window.Motion;
  const motionOn = !!M && !reduce && !isPresenter && params.get('motion') !== '0';
  if (motionOn) document.documentElement.classList.add('has-motion');
  const EASE = [0.22, 1, 0.36, 1];
  const ANIM_PROPS = ['opacity', 'transform', 'backgroundSize'];
  const SVG_ATTRS = ['pathLength', 'stroke-dasharray', 'stroke-dashoffset']; // los escribe Motion al animar pathLength en <path>

  let running = []; // { ctrl, els }
  // Motion escribe el último valor en el style inline en su siguiente frame (también tras stop()),
  // así que limpiamos ahora y otra vez tras dos frames: la clase CSS vuelve a mandar.
  function clean(els) {
    const wipe = () => els.forEach((el) => {
      ANIM_PROPS.forEach((p) => { el.style[p] = ''; });
      if (el instanceof SVGElement) SVG_ATTRS.forEach((a) => el.removeAttribute(a));
      if (!el.getAttribute('style')) el.removeAttribute('style'); // sin restos: style="" tampoco
    });
    wipe();
    requestAnimationFrame(() => requestAnimationFrame(wipe));
    setTimeout(wipe, 120);
  }
  function stopAll() {
    const list = running;
    running = [];
    list.forEach(({ ctrl, els }) => {
      try { ctrl.stop(); } catch (_) { /* already finished */ }
      clean(els);
    });
  }
  function run(targets, keyframes, options) {
    const els = Array.isArray(targets) ? targets : [targets];
    if (!motionOn || els.length === 0) return;
    const ctrl = M.animate(els, keyframes, options);
    const entry = { ctrl, els };
    running.push(entry);
    const done = () => {
      const i = running.indexOf(entry);
      if (i >= 0) { running.splice(i, 1); clean(els); }
    };
    if (ctrl.finished && ctrl.finished.then) ctrl.finished.then(done, done);
    else if (ctrl.then) ctrl.then(done, done);
    // red de seguridad: si el navegador no avanza frames (captura headless con virtual time, pestaña
    // en segundo plano), a los 1.6 s se detiene y se limpia: la slide queda en su estado final.
    setTimeout(() => {
      if (running.indexOf(entry) >= 0) { try { ctrl.stop(); } catch (_) { /* noop */ } done(); }
    }, 1600);
  }

  function enterSlide(slide, forward) {
    if (!motionOn || !forward) return;
    const layout = slide.dataset.layout;
    if (layout === 'cover') return enterCover(slide);
    if (layout === 'anchor') return enterAnchor(slide);
    if (layout === 'close') return enterClose(slide);
    const title = slide.querySelector(':scope > .slide-title, :scope > h1, :scope > h2');
    // el contenido vive en .slide-body (exposición) o directamente en la sección (cue cards de demo)
    const scope = slide.querySelector(':scope > .slide-body') || slide;
    const rest = Array.from(scope.querySelectorAll(':scope > *:not(aside):not([data-step]):not(pre):not(table):not(figure):not(.version)'))
      .filter((e) => e !== title)
      .slice(0, 5);
    if (title) run(title, { opacity: [0, 1], y: [14, 0] }, { duration: 0.36, ease: EASE });
    if (rest.length) run(rest, { opacity: [0, 1], y: [10, 0] }, { duration: 0.32, delay: M.stagger(0.05, { startDelay: 0.08 }), ease: EASE });
    // diagramas con loop visibles desde el inicio (16): las flechas se dibujan; las que están en un paso esperan a revealStep
    drawArrows(Array.from(slide.querySelectorAll('svg .loop-arrow')).filter((p) => !p.closest('[data-step]')), 0.2);
  }

  // Dibuja las flechas del loop: Motion anima pathLength 0 -> 1 (escribe pathLength="1" + stroke-dasharray/-dashoffset
  // como atributos del <path>); al terminar, clean() quita los atributos y el SVG queda como en el archivo.
  // Sin motion no toca nada: las flechas se ven completas.
  function drawArrows(paths, startDelay) {
    if (!motionOn || !paths.length) return;
    paths.forEach((p, i) => {
      p.setAttribute('pathLength', '1');
      p.setAttribute('stroke-dasharray', '0 1'); // arranca invisible (sin flash antes del delay)
      run(p, { pathLength: [0, 1] }, { duration: 0.9, delay: (startDelay || 0) + i * 0.15, ease: EASE });
    });
  }

  function enterCover(slide) {
    const h1 = slide.querySelector('h1');
    const sub = slide.querySelector('.cover-sub');
    const bottom = slide.querySelector('.cover-bottom');
    if (h1) run(h1, { opacity: [0, 1], y: [18, 0] }, { duration: 0.52, ease: EASE });
    if (sub) run(sub, { opacity: [0, 1], y: [18, 0] }, { duration: 0.4, delay: 0.14, ease: EASE });
    if (bottom) run(bottom, { opacity: [0, 1], y: [18, 0] }, { duration: 0.4, delay: 0.26, ease: EASE });
  }

  function enterAnchor(slide) {
    const kicker = slide.querySelector('.anchor-kicker');
    const text = slide.querySelector('.anchor-text');
    const keys = Array.from(slide.querySelectorAll('.anchor-text u.key'));
    if (kicker) run(kicker, { opacity: [0, 1] }, { duration: 0.18, ease: EASE });
    if (text) run(text, { opacity: [0, 1], y: [16, 0] }, { duration: 0.48, delay: 0.12, ease: EASE });
    if (keys.length) run(keys, { backgroundSize: ['0% 2px', '100% 2px'] }, { duration: 0.42, delay: 0.6, ease: EASE });
  }

  function enterClose(slide) {
    const left = Array.from(slide.querySelectorAll('.grid2 > div:first-child > *'));
    const qrs = Array.from(slide.querySelectorAll('.qr'));
    if (left.length) run(left, { opacity: [0, 1], y: [10, 0] }, { duration: 0.36, delay: M.stagger(0.06), ease: EASE });
    if (qrs.length) run(qrs, { opacity: [0, 1], scale: [0.96, 1] }, { duration: 0.36, delay: M.stagger(0.06, { startDelay: 0.2 }), ease: EASE });
  }

  function revealStep(el) {
    if (!motionOn || !el) return;
    run(el, { opacity: [0, 1], y: [10, 0] }, { duration: 0.26, ease: 'easeOut' });
    drawArrows(Array.from(el.querySelectorAll('svg .loop-arrow')), 0.1);
  }

  // Compute steps per slide
  const stepsPerSlide = slides.map((s) =>
    Array.from(s.querySelectorAll('[data-step]')).reduce((max, el) => {
      const n = parseInt(el.dataset.step || '0', 10);
      return n > max ? n : max;
    }, 0)
  );

  let current = 0;
  let step = 0;
  let prevCurrent = -1;
  let prevStep = 0;

  // Resolve initial slide from hash
  if (location.hash) {
    const idx = slides.findIndex((s) => '#' + s.id === location.hash);
    if (idx >= 0) current = idx;
  }

  const counterCurrent = document.querySelector('[data-current]');
  const counterTotal = document.querySelector('[data-total]');
  const progressEl = document.querySelector('.deck-progress');
  if (counterTotal) counterTotal.textContent = String(slides.length);

  function render() {
    stopAll();
    slides.forEach((s, i) => s.classList.toggle('is-active', i === current));
    const active = slides[current];
    let revealed = null;
    active.querySelectorAll('[data-step]').forEach((el) => {
      const n = parseInt(el.dataset.step || '0', 10);
      const vis = n <= step;
      const was = el.classList.contains('is-visible');
      el.classList.toggle('is-visible', vis);
      if (vis && n === step && step > 0) revealed = el;
      // GIFs reinician al revelarse (también con ?motion=0): src con cache-buster, así arrancan desde el primer frame
      if (vis && !was && n > 0) {
        el.querySelectorAll('img[data-gif]').forEach((g) => { g.src = g.dataset.gif + '?t=' + Date.now(); });
      }
    });
    if (counterCurrent) counterCurrent.textContent = String(current + 1);
    if (progressEl) progressEl.style.width = ((current + 1) / slides.length * 100).toFixed(2) + '%';
    // keep the query string (?presenter=1, ?motion=0) BEFORE the hash so reload works
    history.replaceState(null, '', location.pathname + location.search + '#' + active.id);

    if (current !== prevCurrent) {
      enterSlide(active, current > prevCurrent);
    } else if (step > prevStep) {
      revealStep(revealed);
    }
    prevCurrent = current;
    prevStep = step;

    if (isPresenter) renderPresenter();
  }

  function next() {
    if (step < stepsPerSlide[current]) { step++; return render(); }
    if (current < slides.length - 1) { current++; step = 0; return render(); }
  }

  function prev() {
    if (step > 0) { step--; return render(); }
    if (current > 0) { current--; step = stepsPerSlide[current]; return render(); }
  }

  function jumpTo(n) {
    if (n < 0 || n >= slides.length) return;
    current = n; step = 0; render();
  }

  // --- presenter view ---

  let nextPreviewEl;
  let notesEl;
  let timerEl;
  const startTime = Date.now();

  function setupPresenter() {
    document.body.classList.add('is-presenter');

    nextPreviewEl = document.createElement('div');
    nextPreviewEl.className = 'slide-next-preview';

    notesEl = document.createElement('div');
    notesEl.className = 'presenter-notes';
    timerEl = document.createElement('div');
    timerEl.className = 'timer';
    notesEl.appendChild(timerEl);
    const notesBody = document.createElement('div');
    notesBody.className = 'notes-body';
    notesEl.appendChild(notesBody);

    document.querySelector('main#deck').append(nextPreviewEl, notesEl);

    setInterval(updateTimer, 1000);
    updateTimer();
  }

  function updateTimer() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const s = String(elapsed % 60).padStart(2, '0');
    if (timerEl) timerEl.textContent = `${m}:${s}`;
  }

  function renderPresenter() {
    if (!nextPreviewEl) return;
    const nxt = slides[current + 1];
    nextPreviewEl.innerHTML = '';
    if (nxt) {
      const title = nxt.querySelector('h1, h2, .slide-title');
      const heading = document.createElement('div');
      heading.style.color = 'var(--muted)';
      heading.style.fontSize = '1rem';
      heading.textContent = `next · slide ${current + 2}`;
      const body = document.createElement('div');
      body.style.color = 'var(--bg)'; // panel oscuro: --fg es el mismo slate que --bg-deep
      body.style.fontSize = '1.5rem';
      body.style.marginTop = '0.5rem';
      body.textContent = title ? title.textContent : nxt.id;
      nextPreviewEl.append(heading, body);
    } else {
      nextPreviewEl.textContent = 'end of deck';
    }

    const notes = slides[current].querySelector('aside.notes');
    const notesBody = notesEl.querySelector('.notes-body');
    notesBody.innerHTML = notes ? notes.innerHTML : '<em style="color:var(--muted)">no notes for this slide</em>';
  }

  // --- input ---

  let goBuffer = '';
  window.addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    switch (e.key) {
      case 'ArrowRight':
      case ' ':
      case 'PageDown':
        e.preventDefault(); return next();
      case 'ArrowLeft':
      case 'PageUp':
        e.preventDefault(); return prev();
      case 'Home':
        e.preventDefault(); return jumpTo(0);
      case 'End':
        e.preventDefault(); return jumpTo(slides.length - 1);
      case '?':
        return document.querySelector('.kbd-hint')?.classList.toggle('is-visible');
      case 'Escape':
        if (isPresenter) { window.close(); }
        return;
      case 'g':
        goBuffer = ''; return;
    }
    if (/^\d$/.test(e.key)) {
      goBuffer += e.key;
      clearTimeout(window.__goTimeout);
      window.__goTimeout = setTimeout(() => {
        const n = parseInt(goBuffer, 10);
        if (!isNaN(n)) jumpTo(n - 1);
        goBuffer = '';
      }, 600);
    }
  });

  // Click anywhere advances (except on links / form inputs)
  window.addEventListener('click', (e) => {
    if (e.target.closest('a, button, input, textarea, select')) return;
    next();
  });

  if (isPresenter) setupPresenter();
  render();
})();
