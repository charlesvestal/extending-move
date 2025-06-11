export function initWavetableLfoViz() {
  function init(prefix, canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const qRange = suffix =>
      document.querySelector(`.param-item[data-name="${prefix}${suffix}"] input[type="range"]`);
    const qSelect = suffix =>
      document.querySelector(`.param-item[data-name="${prefix}${suffix}"] select`);
    const shapeEl = qSelect('Shape_Type');
    const rateEl = qRange('Time_Rate');
    const syncSel = qSelect('Time_Sync');
    const syncRateEl = qRange('Time_SyncedRate');
    const attackEl = qRange('Time_AttackTime');
    const offsetEl = qRange('Shape_PhaseOffset');
    const amountEl = qRange('Shape_Amount');
    const timeScaleEl = document.querySelector(
      '.param-item[data-name="Voice_Modulators_TimeScale"] input[type="range"]'
    );

    const SYNC_RATES = [
      8, 6, 4, 3, 2, 1.5, 1, 0.75, 0.5, 0.375, 1 / 3, 5 / 16,
      0.25, 3 / 16, 1 / 6, 1 / 8, 1 / 12, 1 / 16, 1 / 24, 1 / 32, 1 / 48,
      1 / 64
    ];
    const BPM = 120;

    function knobRatio(el, maxOverride = null) {
      if (!el) return 0;
      const min = parseFloat(el.min || '0');
      const max = maxOverride !== null ? maxOverride : parseFloat(el.max || '1');
      const val = parseFloat(el.value || '0');
      return Math.min(Math.max((val - min) / (max - min), 0), 1);
    }

    function getRateHz() {
      const mode = syncSel ? syncSel.value : 'Free';
      if (mode === 'Tempo' && syncRateEl) {
        const idx = parseInt(syncRateEl.value || '0', 10);
        const bars = SYNC_RATES[idx] || 1;
        const beats = bars * 4;
        const sec = (60 / BPM) * beats;
        return sec > 0 ? 1 / sec : 0;
      }
      return parseFloat(rateEl ? rateEl.value || '0' : '0');
    }

    function getTimeScale() {
      if (!timeScaleEl) return 1;
      const val = parseFloat(timeScaleEl.value || '0');
      return Math.pow(2, val);
    }

    function wave(shape, phase) {
      const p = phase % 1;
      switch (shape) {
        case 'Sine':
          return Math.sin(2 * Math.PI * p);
        case 'Triangle':
          return 1 - 4 * Math.abs(Math.round(p - 0.25) - (p - 0.25));
        case 'Sawtooth':
          return 2 * p - 1;
        case 'Rectangle':
          return p < 0.5 ? 1 : -1;
        case 'Noise':
          return Math.random() * 2 - 1;
        default:
          return 0;
      }
    }

    function draw() {
      const rate = getRateHz() * getTimeScale();
      const attack = attackEl ? parseFloat(attackEl.value || '0') : 0;
      const offset = offsetEl ? parseFloat(offsetEl.value || '0') / 360 : 0;
      const amount = amountEl ? parseFloat(amountEl.value || '1') : 1;
      const shape = shapeEl ? shapeEl.value : 'Sine';
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.beginPath();
      let ratio = 0;
      if (syncSel && syncSel.value === 'Tempo') {
        ratio = knobRatio(syncRateEl, SYNC_RATES.length - 1);
      } else {
        ratio = knobRatio(rateEl);
      }
      const cycles = 1 + ratio * 9;
      const duration = rate > 0 ? cycles / rate : 1;
      for (let i = 0; i <= w; i++) {
        const t = (i / w) * duration;
        let amp = amount;
        if (attack > 0 && t < attack) amp = amount * t / attack;
        const ph = rate * t + offset;
        const val = wave(shape, ph) * amp * 0.5 + 0.5;
        const y = h - val * h;
        if (i === 0) ctx.moveTo(i, y); else ctx.lineTo(i, y);
      }
      ctx.strokeStyle = '#f00';
      ctx.stroke();
    }

    [shapeEl, rateEl, syncSel, syncRateEl, attackEl, offsetEl, amountEl, timeScaleEl].forEach(el => {
      if (!el) return;
      const evt = el.tagName === 'SELECT' ? 'change' : 'input';
      el.addEventListener(evt, draw);
    });

    draw();
  }

  init('Voice_Modulators_Lfo1_', 'lfo1-canvas');
  init('Voice_Modulators_Lfo2_', 'lfo2-canvas');
}

document.addEventListener('DOMContentLoaded', initWavetableLfoViz);
