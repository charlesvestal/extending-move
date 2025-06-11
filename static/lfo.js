document.addEventListener('DOMContentLoaded', () => {
  const shapeEl = document.getElementById('shape');
  const rateEl = document.getElementById('rate');
  const attackEl = document.getElementById('attack');
  const offsetEl = document.getElementById('offset');
  const amountEl = document.getElementById('amount');
  const canvas = document.getElementById('lfo-canvas');
  const ctx = canvas.getContext('2d');

  function wave(shape, phase) {
    const p = phase % 1;
    switch(shape) {
      case 'sine':
        return Math.sin(2 * Math.PI * p);
      case 'square':
        return p < 0.5 ? 1 : -1;
      case 'triangle':
        return 1 - 4 * Math.abs(Math.round(p - 0.25) - (p - 0.25));
      case 'saw':
        return 2 * p - 1;
      default:
        return 0;
    }
  }

  function draw() {
    const rate = parseFloat(rateEl.value);
    const attack = parseFloat(attackEl.value);
    const offset = parseFloat(offsetEl.value);
    const amount = parseFloat(amountEl.value);
    const shape = shapeEl.value;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();

    const minHz = parseFloat(rateEl.min || '0.17');
    const maxHz = parseFloat(rateEl.max || '1700');
    const logMin = Math.log10(minHz);
    const logMax = Math.log10(maxHz);
    const logRate = rate > 0 ? Math.log10(rate) : logMin;
    const ratio = Math.min(Math.max((logRate - logMin) / (logMax - logMin), 0), 1);
    const cycles = 2 + (10 - 2) * ratio;
    const duration = cycles / Math.max(rate, 0.0001);

    for (let i = 0; i <= w; i++) {
      const t = (i / w) * duration;
      let amp = amount;
      if (attack > 0 && t < attack) {
        amp = amount * t / attack;
      }
      const ph = rate * t + offset;
      const val = wave(shape, ph) * amp * 0.5 + 0.5;
      const y = h - val * h;
      if (i === 0) ctx.moveTo(i, y); else ctx.lineTo(i, y);
    }
    ctx.strokeStyle = '#f00';
    ctx.stroke();
  }

  [shapeEl, rateEl, attackEl, offsetEl, amountEl].forEach(el => el.addEventListener('input', draw));
  draw();
});
