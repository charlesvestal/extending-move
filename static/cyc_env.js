document.addEventListener('DOMContentLoaded', () => {
  const timeEl = document.getElementById('time');
  const tiltEl = document.getElementById('tilt');
  const holdEl = document.getElementById('hold');
  const canvas = document.getElementById('cyc-env-canvas');
  const ctx = canvas.getContext('2d');

  function draw() {
    const time = parseFloat(timeEl.value);
    const tilt = parseFloat(tiltEl.value);
    const hold = parseFloat(holdEl.value);
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    const steps = 100;
    const peakPos = Math.min(Math.max((tilt - 0.2) / 0.8, 0), 1);
    const riseEnd = peakPos * (1 - hold);
    const fallStart = riseEnd + hold;
    for (let i = 0; i <= steps; i++) {
      const phase = i / steps;
      let y = 0;
      if (hold >= 1) {
        y = 1;
      } else if (hold <= 0 && phase !== peakPos) {
        if (phase < peakPos) {
          y = peakPos === 0 ? 1 : phase / peakPos;
        } else {
          y = peakPos === 1 ? 1 : (1 - phase) / (1 - peakPos);
        }
      } else if (phase < riseEnd) {
        y = riseEnd === 0 ? 1 : phase / riseEnd;
      } else if (phase < fallStart) {
        y = 1;
      } else {
        const denom = 1 - fallStart;
        y = denom === 0 ? 1 : (1 - phase) / denom;
      }
      const maxTime = parseFloat(timeEl.max) || 1;
      const x = (phase * time / maxTime) * w;
      const yPix = h - y * h;
      if (i === 0) {
        ctx.moveTo(x, yPix);
      } else {
        ctx.lineTo(x, yPix);
      }
    }
    ctx.strokeStyle = '#f00';
    ctx.stroke();
  }

  [timeEl, tiltEl, holdEl].forEach(el => el.addEventListener('input', draw));
  draw();
});
