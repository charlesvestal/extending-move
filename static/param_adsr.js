export function initParamAdsr() {
  document.querySelectorAll('.adsr-canvas').forEach(canvas => {
    const container = canvas.closest('.env-container') || document;
    const q = name =>
      container.querySelector(`.param-item[data-name$="_${name}"] input[type="range"]`);
    const attack = q('Attack');
    const decay = q('Decay');
    const sustain = q('Sustain');
    const release = q('Release');
    const initial = q('Initial');
    const peak = q('Peak');
    const finalVal = q('Final');
    const modeInput =
      canvas.id === 'env2-canvas'
        ? container.querySelector('.param-item[data-name="Global_Envelope2Mode"] input[type="hidden"]')
        : null;

    if (!attack || !decay || !sustain || !release) return;

    const ctx = canvas.getContext('2d');

    function setupCanvas() {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    }
    setupCanvas();
    function draw() {
      const a = parseFloat(attack.value);
      const d = parseFloat(decay.value);
      const s = parseFloat(sustain.value);
      const r = parseFloat(release.value);
      const i = initial ? parseFloat(initial.value) : 0;
      const p = peak ? parseFloat(peak.value) : 1;
      const f = finalVal ? parseFloat(finalVal.value) : 0;
      const hold = 0.25;
      const total = a + d + r + hold;
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.beginPath();
      ctx.moveTo(0, h - i * h);
      let x = (a / total) * w;
      ctx.lineTo(x, h - p * h);
      const decEnd = x + (d / total) * w;
      ctx.lineTo(decEnd, h - s * h);
      const relStart = w - (r / total) * w;
      ctx.lineTo(relStart, h - s * h);
      ctx.lineTo(w, h - f * h);
      ctx.strokeStyle = '#f00';
      ctx.stroke();
    }

    [attack, decay, sustain, release, initial, peak, finalVal].forEach(el => {
      if (el) el.addEventListener('input', draw);
    });

    if (modeInput) {
      function updateVisibility() {
        const show = modeInput.value !== 'Cyc';
        canvas.classList.toggle('hidden', !show);
      }
      modeInput.addEventListener('change', () => {
        updateVisibility();
        draw();
      });
      updateVisibility();
    }

    draw();
  });
}

document.addEventListener('DOMContentLoaded', initParamAdsr);
