export function initMelodicLfoViz() {
  const canvas = document.getElementById('melodic-lfo-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const qRange = name =>
    document.querySelector(`.param-item[data-name="${name}"] input[type="range"]`);
  const rateEl = qRange('Voice_Lfo_Rate');

  function draw() {
    if (!rateEl) return;
    const rate = parseFloat(rateEl.value || '0');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    const cycles = 1 + ((rate - parseFloat(rateEl.min || '0')) / (parseFloat(rateEl.max || '9') - parseFloat(rateEl.min || '0'))) * 9;
    const duration = rate > 0 ? cycles / rate : 1;
    for (let i = 0; i <= w; i++) {
      const t = (i / w) * duration;
      const val = Math.sin(2 * Math.PI * rate * t) * 0.5 + 0.5;
      const y = h - val * h;
      if (i === 0) ctx.moveTo(i, y); else ctx.lineTo(i, y);
    }
    ctx.strokeStyle = '#f00';
    ctx.stroke();
  }

  if (rateEl) rateEl.addEventListener('input', draw);
  draw();
}

document.addEventListener('DOMContentLoaded', initMelodicLfoViz);
