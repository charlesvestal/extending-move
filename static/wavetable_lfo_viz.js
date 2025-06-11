export function initWavetableLfoViz() {
  const canvas = document.getElementById('lfo1-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const qValue = name => {
    const item = document.querySelector(`.param-item[data-name="${name}"]`);
    if (!item) return null;
    return item.querySelector('input[name$="_value"]');
  };
  const qSelect = name => {
    const item = document.querySelector(`.param-item[data-name="${name}"]`);
    return item ? item.querySelector('select') : null;
  };

  const rateEl = qValue('Voice_Modulators_Lfo1_Time_Rate');
  const syncRateEl = qValue('Voice_Modulators_Lfo1_Time_SyncedRate');
  const syncSel = qSelect('Voice_Modulators_Lfo1_Time_Sync');
  const shapeSel = qSelect('Voice_Modulators_Lfo1_Shape_Type');
  const amountEl = qValue('Voice_Modulators_Lfo1_Shape_Amount');
  const attackEl = qValue('Voice_Modulators_Lfo1_Time_AttackTime');
  const offsetEl = qValue('Voice_Modulators_Lfo1_Shape_PhaseOffset');

  const rateItem = document.querySelector('.param-item[data-name="Voice_Modulators_Lfo1_Time_Rate"]');
  const syncRateItem = document.querySelector('.param-item[data-name="Voice_Modulators_Lfo1_Time_SyncedRate"]');

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
      case 'Rectangle':
        return p < 0.5 ? 1 : -1;
      case 'Triangle':
        return 1 - 4 * Math.abs(Math.round(p - 0.25) - (p - 0.25));
      case 'Sawtooth':
        return 2 * p - 1;
      case 'Noise':
        return Math.random() * 2 - 1;
      default:
        return 0;
    }
  }

  function getRateHz() {
    if (syncSel && syncSel.value === 'Tempo' && syncRateEl) {
      const idx = parseInt(syncRateEl.value || '0', 10);
      const bars = SYNC_RATES[idx] || 1;
      const beats = bars * 4;
      const sec = (60 / BPM) * beats;
      return sec > 0 ? 1 / sec : 0;
    }
    return parseFloat(rateEl?.value || '0');
  }

  function draw() {
    const rate = getRateHz();
    const shape = shapeSel ? shapeSel.value : 'Sine';
    const amount = parseFloat(amountEl?.value || '1');
    const attack = parseFloat(attackEl?.value || '0');
    const offset = parseFloat(offsetEl?.value || '0') / 360;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    let ratio = 0;
    if (rateEl) {
      const min = parseFloat(rateEl.getAttribute('min') || '0');
      const max = parseFloat(rateEl.getAttribute('max') || '1');
      const val = parseFloat(rateEl.value || '0');
      ratio = Math.min(Math.max((val - min) / (max - min), 0), 1);
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

  function updateRateDisplay() {
    if (!syncSel) return;
    const tempo = syncSel.value === 'Tempo';
    if (rateItem) rateItem.classList.toggle('hidden', tempo);
    if (syncRateItem) syncRateItem.classList.toggle('hidden', !tempo);
  }

  [rateEl, syncRateEl, syncSel, shapeSel, amountEl, attackEl, offsetEl].forEach(el => {
    if (!el) return;
    const evt = el.tagName === 'SELECT' ? 'change' : 'input';
    el.addEventListener(evt, () => { draw(); });
    if (evt === 'input') el.addEventListener('change', draw);
  });
  if (syncSel) syncSel.addEventListener('change', updateRateDisplay);
  updateRateDisplay();
  draw();
}

document.addEventListener('DOMContentLoaded', initWavetableLfoViz);
