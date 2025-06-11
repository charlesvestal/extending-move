export function initDriftLfoViz() {
  const canvas = document.getElementById('lfo-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const qRange = name => {
    const el = document.querySelector(`.param-item[data-name="${name}"] input[type="range"]`);
    return el;
  };
  const qSelect = name => {
    const el = document.querySelector(`.param-item[data-name="${name}"] select`);
    return el;
  };

  const rateEl = qRange('Lfo_Rate');
  const ratioEl = qRange('Lfo_Ratio');
  const timeEl = qRange('Lfo_Time');
  const syncEl = qRange('Lfo_SyncedRate');
  const modeSel = qSelect('Lfo_Mode');
  const shapeSel = qSelect('Lfo_Shape');
  const amountEl = qRange('Lfo_Amount');

  const SYNC_RATES = [
    8, 6, 4, 3, 2, 1.5, 1, 0.75, 0.5, 0.375, 1/3, 5/16,
    0.25, 3/16, 1/6, 1/8, 1/12, 1/16, 1/24, 1/32, 1/48,
    1/64
  ];
  const BPM = 120;

  function wave(shape, phase) {
    const p = phase % 1;
    switch (shape) {
      case 'Sine':
        return Math.sin(2 * Math.PI * p);
      case 'Square':
        return p < 0.5 ? 1 : -1;
      case 'Triangle':
        return 1 - 4 * Math.abs(Math.round(p - 0.25) - (p - 0.25));
      case 'Saw Up':
        return 2 * p - 1;
      case 'Saw Down':
        return 1 - 2 * p;
      case 'Sample & Hold':
        return (Math.floor(p * 8) % 2) * 2 - 1;
      case 'Exponential Env':
        return 1 - Math.exp(-5 * Math.min(p, 1));
      case 'Wander':
        return 0.5 * Math.sin(2 * Math.PI * p * 0.5) +
               0.5 * Math.sin(2 * Math.PI * p * 0.25);
      default:
        return 0;
    }
  }

  function getRateHz() {
    const mode = modeSel ? modeSel.value : 'Freq';
    if (mode === 'Freq' && rateEl) return parseFloat(rateEl.value || '0');
    if (mode === 'Ratio' && ratioEl) return parseFloat(ratioEl.value || '0');
    if (mode === 'Time' && timeEl) {
      const t = parseFloat(timeEl.value || '0');
      return t > 0 ? 1 / t : 0;
    }
    if (mode === 'Sync' && syncEl) {
      const idx = parseInt(syncEl.value || '0', 10);
      const bars = SYNC_RATES[idx] || 1;
      const beats = bars * 4;
      const sec = (60 / BPM) * beats;
      return sec > 0 ? 1 / sec : 0;
    }
    return 0;
  }

  function draw() {
    const rate = getRateHz();
    const shape = shapeSel ? shapeSel.value : 'Sine';
    const amount = amountEl ? parseFloat(amountEl.value) : 1;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    const minCycles = 2;
    const maxCycles = 10;
    const minRate = 0.17; // matches standalone LFO viz
    const maxRate = 1700;
    const rateNorm = Math.max(0, Math.min(1, (rate - minRate) / (maxRate - minRate)));
    const cycles = minCycles + (maxCycles - minCycles) * rateNorm;
    const duration = rate > 0 ? cycles / rate : 0;
    for (let i = 0; i <= w; i++) {
      const t = (i / w) * duration;
      const ph = rate * t;
      const val = wave(shape, ph) * amount * 0.5 + 0.5;
      const y = h - val * h;
      if (i === 0) ctx.moveTo(i, y); else ctx.lineTo(i, y);
    }
    ctx.strokeStyle = '#f00';
    ctx.stroke();
  }

  [rateEl, ratioEl, timeEl, syncEl, modeSel, shapeSel, amountEl].forEach(el => {
    if (!el) return;
    const evt = el.tagName === 'SELECT' ? 'change' : 'input';
    el.addEventListener(evt, draw);
  });

  draw();
}

document.addEventListener('DOMContentLoaded', initDriftLfoViz);
