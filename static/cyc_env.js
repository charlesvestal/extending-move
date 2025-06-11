document.addEventListener('DOMContentLoaded', () => {
  const timeEl = document.getElementById('time');
  const tiltEl = document.getElementById('tilt');
  const holdEl = document.getElementById('hold');
  const canvas = document.getElementById('cyc-env-canvas');
  const ctx = canvas.getContext('2d');

  function mix(a, b, t) {
    return a * (1 - t) + b * t;
  }

  function draw() {
    const time = parseFloat(timeEl.value);
    const tilt = parseFloat(tiltEl.value);
    const hold = parseFloat(holdEl.value);
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    const steps = 100;
    for (let i = 0; i <= steps; i++) {
      const phase = i / steps;
      const rise_frac = 0.5 * (1 - hold);
      const fall_start = rise_frac + hold;
      let y0;
      if (phase < rise_frac) {
        y0 = phase / rise_frac;
      } else if (phase < fall_start) {
        y0 = 1;
      } else {
        y0 = (1 - phase) / rise_frac;
      }
      let y1;
      if (tilt < 0.2) {
        const curve_amount = 1 - tilt / 0.2;
        const sp = Math.min(Math.max((phase - 0.25) * 2, 0), 1);
        const sinVal = Math.sin(Math.PI * sp);
        y1 = mix(y0, sinVal, curve_amount);
      } else {
        const skew = (tilt - 0.2) / 0.8;
        const attack = mix(0.5, 0.1, skew);
        const decay = 1 - attack;
        if (phase < attack) {
          y1 = phase / attack;
        } else {
          y1 = 1 - (phase - attack) / decay;
        }
      }
      const x = phase * w;
      const y = h - y1 * h;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.strokeStyle = '#f00';
    ctx.stroke();
  }

  [timeEl, tiltEl, holdEl].forEach(el => el.addEventListener('input', draw));
  draw();
});
