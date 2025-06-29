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
    ctx.lineWidth = 2;

    const minRate = parseFloat(rateEl.min || '0');
    const maxRate = parseFloat(rateEl.max || '1');
    const ratio = Math.min(Math.max((rate - minRate) / (maxRate - minRate), 0), 1);
    const cycles = 1 + ratio * 9;
    const duration = cycles / (rate || 1); // seconds shown
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
    ctx.strokeStyle = '#FFA500';
    ctx.stroke();
  }

  [shapeEl, rateEl, attackEl, offsetEl, amountEl].forEach(el => el.addEventListener('input', draw));
  draw();
});
