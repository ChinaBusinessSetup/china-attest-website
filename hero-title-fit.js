/* Fit the complete headline sentences without changing their copy or order. */
(() => {
  const heading = document.querySelector('.home .hero-service h1');
  if (!heading) return;
  const container = heading.closest('.hero-inner');
  const lines = [...heading.children];
  if (!container || lines.length !== 2) return;
  let frame = 0;
  let previousWidth = -1;
  function fit() {
    frame = 0;
    const available = heading.clientWidth - 2;
    if (available <= 0) return;
    // Resolve the responsive maximum, then measure actual rendered glyphs.
    heading.style.setProperty('--hero-title-fit', '1000px');
    let size = parseFloat(getComputedStyle(heading).fontSize);
    for (let pass = 0; pass < 4; pass++) {
      let widest = 0;
      for (const line of lines) {
        const range = document.createRange();
        range.selectNodeContents(line);
        widest = Math.max(widest, range.getBoundingClientRect().width);
      }
      if (widest <= available) break;
      size = Math.max(1, Math.floor(size * available / widest * 100) / 100);
      heading.style.setProperty('--hero-title-fit', `${size}px`);
    }
  }
  function schedule() {
    if (!frame) frame = requestAnimationFrame(fit);
  }
  if ('ResizeObserver' in window) {
    new ResizeObserver(entries => {
      const width = entries[0].contentRect.width;
      if (Math.abs(width - previousWidth) > 0.25) {
        previousWidth = width;
        schedule();
      }
    }).observe(container);
  }
  window.addEventListener('resize', schedule, { passive: true });
  if (document.fonts) {
    document.fonts.ready.then(schedule);
    document.fonts.addEventListener('loadingdone', schedule);
  }
  fit();
})();
