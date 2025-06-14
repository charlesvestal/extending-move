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

  function knobRatio(el, maxOverride = null) {
    if (!el) return 0;
    const min = parseFloat(el.min || '0');
    const max = maxOverride !== null ? maxOverride : parseFloat(el.max || '1');
    const val = parseFloat(el.value || '0');
    return Math.min(Math.max((val - min) / (max - min), 0), 1);
  }

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
      case 'Exponential Env':
        return 1 - Math.exp(-5 * Math.min(p, 1));
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

  let stepCache = { shape: '', count: 0, values: [] };

  function randomValues(count) {
    const arr = [];
    for (let i = 0; i < count; i++) arr.push(Math.random() * 2 - 1);
    return arr;
  }

  function draw() {
    const rate = getRateHz();
    const mode = modeSel ? modeSel.value : 'Freq';
    const shape = shapeSel ? shapeSel.value : 'Sine';
    const amount = amountEl ? parseFloat(amountEl.value) : 1;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    let duration = 1;
    if (mode === 'Time' && timeEl) {
      const t = parseFloat(timeEl.value || '0');
      if (t > 0) {
        const ratio = knobRatio(timeEl);
        const cycles = 1 + ratio * 9;
        duration = t * cycles;
      }
    } else {
      let ratio = 0;
      if (mode === 'Freq') ratio = knobRatio(rateEl);
      else if (mode === 'Ratio') ratio = knobRatio(ratioEl);
      else if (mode === 'Sync') ratio = knobRatio(syncEl, SYNC_RATES.length - 1);
      const cycles = 1 + ratio * 9;
      duration = rate > 0 ? cycles / rate : 1;
    }
    let steps = Math.max(2, Math.round(rate * 6));
    if (shape === 'Sample & Hold' || shape === 'Wander') {
      let ratio = 0;
      if (mode === 'Freq') ratio = knobRatio(rateEl);
      else if (mode === 'Ratio') ratio = knobRatio(ratioEl);
      else if (mode === 'Time') ratio = knobRatio(timeEl);
      else if (mode === 'Sync') ratio = knobRatio(syncEl, SYNC_RATES.length - 1);
      steps = Math.round(2 + ratio * 10);
      if (stepCache.shape !== shape || stepCache.count !== steps) {
        stepCache = {
          shape: shape,
          count: steps,
          values: randomValues(shape === 'Wander' ? steps + 1 : steps)
        };
      }
    }

    for (let i = 0; i <= w; i++) {
      const t = (i / w) * duration;
      const ph = rate * t;
      let val;
      if (shape === 'Sample & Hold') {
        const pos = (t / duration) * steps;
        const idx = Math.floor(pos);
        val = stepCache.values[idx] || 0;
      } else if (shape === 'Wander') {
        const pos = (t / duration) * steps;
        const idx = Math.floor(pos);
        const frac = pos - idx;
        const v1 = stepCache.values[idx] || 0;
        const v2 = stepCache.values[idx + 1] || v1;
        val = v1 + (v2 - v1) * frac;
      } else {
        val = wave(shape, ph);
      }
      val = val * amount * 0.5 + 0.5;
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

  window.driftLfoVizUpdate = draw;

  draw();
}

document.addEventListener('DOMContentLoaded', initDriftLfoViz);
