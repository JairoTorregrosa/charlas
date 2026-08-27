// Vanilla-JS navigator for the charla deck.
// Contract documented in reference/html-deck-architecture.md.

(() => {
  const slides = Array.from(document.querySelectorAll('main#deck > section.slide'));
  if (slides.length === 0) return;

  const params = new URLSearchParams(location.search);
  const isPresenter = params.get('presenter') === '1';

  // ?motion=0 (deck-capture) apaga transiciones para que la captura sea estable.
  if (params.get('motion') === '0') document.documentElement.classList.add('no-motion');

  // ?steps=all arranca cada slide con TODOS los pasos visibles: es lo que usan
  // el PDF que se entrega y quien prefiera presentar sin animaciones.
  // (motion=0 solo apaga transiciones; no revela nada.)
  const allSteps = params.get('steps') === 'all';
  // Marca el modo en el <html>: con todo revelado a la vez, el velo «¿Y si…?»
  // deja de ser un velo y pasa a colocarse DEBAJO del cuerpo (deck.css
  // §html.steps-all), para que el PDF que se entrega muestre el par
  // Antes/Después y no solo la pregunta.
  if (allSteps) document.documentElement.classList.add('steps-all');

  // Compute steps per slide
  const stepsPerSlide = slides.map((s) =>
    Array.from(s.querySelectorAll('[data-step]')).reduce((max, el) => {
      const n = parseInt(el.dataset.step || '0', 10);
      return n > max ? n : max;
    }, 0)
  );

  let current = 0;
  let step = 0;

  // Resolve initial slide from hash
  if (location.hash) {
    const idx = slides.findIndex((s) => '#' + s.id === location.hash);
    if (idx >= 0) current = idx;
  }

  if (allSteps) step = stepsPerSlide[current];

  const actLabel = document.querySelector('[data-act-label]');
  const counterCurrent = document.querySelector('[data-current]');
  const counterTotal = document.querySelector('[data-total]');
  if (counterTotal) counterTotal.textContent = String(slides.length);

  function render() {
    slides.forEach((s, i) => s.classList.toggle('is-active', i === current));
    const active = slides[current];
    active.querySelectorAll('[data-step]').forEach((el) => {
      const n = parseInt(el.dataset.step || '0', 10);
      el.classList.toggle('is-visible', n <= step);
    });
    if (counterCurrent) counterCurrent.textContent = String(current + 1);
    if (actLabel) actLabel.textContent = active.dataset.act || '';
    document.body.classList.toggle('is-dark-slide', active.dataset.tone === 'dark');
    history.replaceState(null, '', '#' + active.id);

    if (isPresenter) renderPresenter();
  }

  function next() {
    if (step < stepsPerSlide[current]) { step++; return render(); }
    if (current < slides.length - 1) { current++; step = allSteps ? stepsPerSlide[current] : 0; return render(); }
  }

  function prev() {
    // con ?steps=all no hay pasos que deshacer: la flecha izquierda cambia de slide
    if (!allSteps && step > 0) { step--; return render(); }
    if (current > 0) { current--; step = stepsPerSlide[current]; return render(); }
  }

  function jumpTo(n) {
    if (n < 0 || n >= slides.length) return;
    current = n; step = allSteps ? stepsPerSlide[n] : 0; render();
  }

  // --- presenter view ---

  let nextPreviewEl;
  let notesEl;
  let timerEl;
  const startTime = Date.now();

  function setupPresenter() {
    document.body.classList.add('is-presenter');
    document.documentElement.classList.add('is-presenter');

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
      heading.style.fontSize = '14px';
      heading.textContent = `next · slide ${current + 2}`;
      const body = document.createElement('div');
      body.style.color = 'var(--fg)';
      body.style.fontSize = '26px';
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
