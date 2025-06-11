document.addEventListener('DOMContentLoaded', () => {
  const attack = document.getElementById('attack');
  const decay = document.getElementById('decay');
  const sustain = document.getElementById('sustain');
  const release = document.getElementById('release');
  const initial = document.getElementById('initial');
  const peak = document.getElementById('peak');
  const finalVal = document.getElementById('final');
  const canvas = document.getElementById('adsr-canvas');
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
    const i = parseFloat(initial.value);
    const p = parseFloat(peak.value);
    const f = parseFloat(finalVal.value);
    const hold = 0.25; // constant hold portion
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

  attack.addEventListener('input', draw);
  decay.addEventListener('input', draw);
  sustain.addEventListener('input', draw);
  release.addEventListener('input', draw);
  initial.addEventListener('input', draw);
  peak.addEventListener('input', draw);
  finalVal.addEventListener('input', draw);
  draw();
});
