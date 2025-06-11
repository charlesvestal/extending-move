document.addEventListener('DOMContentLoaded', () => {
  const shapeEl = document.getElementById('shape');
  const rateEl = document.getElementById('rate');
  const offsetEl = document.getElementById('offset');
  const amountEl = document.getElementById('amount');
  const attackEl = document.getElementById('attack');
  const canvas = document.getElementById('lfo-canvas');
  const ctx = canvas.getContext('2d');

  function waveform(p, shape) {
    if (shape === 'saw') return (2 * (p % 1)) - 1;
    if (shape === 'square') return (p % 1) < 0.5 ? 1 : -1;
    if (shape === 'triangle') return 1 - 4 * Math.abs(Math.round(p - 0.25) - (p - 0.25));
    return Math.sin(2 * Math.PI * p);
  }

  function draw() {
    const shape = shapeEl.value;
    const rate = parseFloat(rateEl.value);
    const offset = parseFloat(offsetEl.value);
    const amount = parseFloat(amountEl.value);
    const attack = parseFloat(attackEl.value);
    const steps = 200;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const phase = rate * t;
      const env = attack > 0 ? Math.min(1, t / attack) : 1;
      const val = offset + amount * env * waveform(phase, shape);
      const x = t * canvas.width;
      const y = canvas.height - ((val + 1) / 2) * canvas.height;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = '#f00';
    ctx.stroke();
  }

  [shapeEl, rateEl, offsetEl, amountEl, attackEl].forEach(el => el.addEventListener('input', draw));
  draw();
});
