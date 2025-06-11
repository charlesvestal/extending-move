export function initParamCycEnv() {
  const canvas = document.getElementById('env2-cyc-canvas');
  if (!canvas) return;
  const container = canvas.closest('.env-container') || document;
  const q = name => container.querySelector(`.param-item[data-name="${name}"] input[type="range"]`);
  const time = q('CyclingEnvelope_Time');
  const tilt = q('CyclingEnvelope_MidPoint');
  const hold = q('CyclingEnvelope_Hold');
  const modeInput = container.querySelector('.param-item[data-name="Global_Envelope2Mode"] input[type="hidden"]');
  if (!time || !tilt || !hold || !modeInput) return;
  const ctx = canvas.getContext('2d');
  const DISPLAY = 2.5;
  function draw() {
    const cycle = parseFloat(time.value);
    const tVal = parseFloat(tilt.value);
    const hVal = parseFloat(hold.value);
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const steps = 100;
    const cycles = Math.max(1, Math.ceil(DISPLAY / cycle));
    for (let c = 0; c < cycles; c++) {
      ctx.beginPath();
      const offset = (c * cycle / DISPLAY) * w;
      const riseEnd = Math.min(Math.max((tVal - 0.2) / 0.8, 0), 1) * (1 - hVal);
      const fallStart = riseEnd + hVal;
      for (let i = 0; i <= steps; i++) {
        const phase = i / steps;
        let y;
        if (phase < riseEnd) {
          y = riseEnd === 0 ? 1 : phase / riseEnd;
        } else if (phase < fallStart) {
          y = 1;
        } else {
          const denom = 1 - fallStart;
          const p = denom === 0 ? 0 : (phase - fallStart) / denom;
          let linear = denom === 0 ? 1 : 1 - p;
          if (tVal < 0.2 && denom !== 0) {
            const t = (0.2 - tVal) / 0.2;
            const k = 5;
            const curve = (1 / (1 + (k - 1) * p) - 1 / k) / (1 - 1 / k);
            linear = linear * (1 - t) + curve * t;
          }
          y = linear;
        }
        const x = offset + (phase * cycle / DISPLAY) * w;
        const yPix = h - y * h;
        if (i === 0) ctx.moveTo(x, yPix); else ctx.lineTo(x, yPix);
      }
      ctx.strokeStyle = '#f00';
      ctx.stroke();
    }
  }
  function updateVisibility() {
    canvas.classList.toggle('hidden', modeInput.value !== 'Cyc');
  }
  [time, tilt, hold].forEach(el => el.addEventListener('input', draw));
  modeInput.addEventListener('change', () => { updateVisibility(); draw(); });
  updateVisibility();
  draw();
}

document.addEventListener('DOMContentLoaded', initParamCycEnv);
