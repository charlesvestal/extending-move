export function initDriftCombinedViz() {
  const filterPanel = document.querySelector('.param-panel.filter');
  const env2Canvas = document.getElementById('env2-canvas');
  const envPanelItems = env2Canvas ? env2Canvas.parentElement : null;
  if (!filterPanel || !envPanelItems) return;

  const env2ModeRow = envPanelItems.querySelector('.env2-mode');

  const canvas = document.createElement('canvas');
  canvas.id = 'driftVizCanvas';
  canvas.width = 300;
  canvas.height = 88;
  canvas.style.border = '1px solid #ccc';
  if (env2ModeRow) {
    envPanelItems.insertBefore(canvas, env2ModeRow);
  } else {
    envPanelItems.insertBefore(canvas, env2Canvas);
  }

  ['driftFilterChart', 'amp-env-canvas', 'env2-canvas'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });

  const ctx = canvas.getContext('2d');

  const qsel = name => document.querySelector(`.param-item[data-name="${name}"] input[type="hidden"]`);

  const filterInputs = {
    freq: qsel('Filter_Frequency'),
    type: qsel('Filter_Type'),
    res: qsel('Filter_Resonance'),
    hp: qsel('Filter_HiPassFrequency')
  };

  const qenv = name => document.querySelector(`.param-item[data-name="${name}"] input[type="range"]`);

  const env1 = {
    attack: qenv('Envelope1_Attack'),
    decay: qenv('Envelope1_Decay'),
    sustain: qenv('Envelope1_Sustain'),
    release: qenv('Envelope1_Release')
  };

  const env2 = {
    attack: qenv('Envelope2_Attack'),
    decay: qenv('Envelope2_Decay'),
    sustain: qenv('Envelope2_Sustain'),
    release: qenv('Envelope2_Release'),
    mode: qsel('Global_Envelope2Mode')
  };

  function biquadCoeffs(type, freq, q, sr) {
    const w0 = 2 * Math.PI * freq / sr;
    const alpha = Math.sin(w0) / (2 * q);
    const cosw0 = Math.cos(w0);
    let b0, b1, b2, a0, a1, a2;
    switch (type) {
      case 'highpass':
        b0 = (1 + cosw0) / 2; b1 = -(1 + cosw0); b2 = (1 + cosw0) / 2;
        a0 = 1 + alpha; a1 = -2 * cosw0; a2 = 1 - alpha; break;
      case 'lowpass':
      default:
        b0 = (1 - cosw0) / 2; b1 = 1 - cosw0; b2 = (1 - cosw0) / 2;
        a0 = 1 + alpha; a1 = -2 * cosw0; a2 = 1 - alpha; break;
    }
    return { b: [b0 / a0, b1 / a0, b2 / a0], a: [1, a1 / a0, a2 / a0] };
  }

  function biquadMag(b, a, w) {
    const cos = Math.cos(w);
    const sin = Math.sin(w);
    const cos2 = Math.cos(2 * w);
    const sin2 = Math.sin(2 * w);
    const numReal = b[0] + b[1] * cos + b[2] * cos2;
    const numImag = -(b[1] * sin + b[2] * sin2);
    const denReal = a[0] + a[1] * cos + a[2] * cos2;
    const denImag = -(a[1] * sin + a[2] * sin2);
    const numMag = Math.hypot(numReal, numImag);
    const denMag = Math.hypot(denReal, denImag);
    return numMag / denMag;
  }

  function computeResponse(type, freq, res, slope, sr = 44100, n = 256) {
    const q = 0.5 + 9.5 * res;
    const freqs = Array.from({ length: n }, (_, i) =>
      10 ** (Math.log10(10) + (Math.log10(20000) - Math.log10(10)) * i / (n - 1))
    );
    const { b, a } = biquadCoeffs(type, freq, q, sr);
    const mag = [];
    for (let i = 0; i < freqs.length; i++) {
      const w = 2 * Math.PI * freqs[i] / sr;
      let m = biquadMag(b, a, w);
      if (String(slope) === '24') m *= biquadMag(b, a, w);
      mag.push(20 * Math.log10(m + 1e-9));
    }
    return { freq: freqs, mag };
  }

  function drawLabel(text) {
    ctx.save();
    ctx.font = '10px sans-serif';
    ctx.fillStyle = '#000';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'top';
    ctx.fillText(text, canvas.width - 4, 2);
    ctx.restore();
  }

  function drawFilter() {
    const { freq, type, res, hp } = filterInputs;
    if (!freq || !type || !res || !hp) return;
    const slope = type.value === 'II' ? '24' : '12';
    const lp = computeResponse('lowpass', parseFloat(freq.value), parseFloat(res.value), slope);
    const hpResp = computeResponse('highpass', parseFloat(hp.value), 0, '12');
    const mag = lp.mag.map((m, i) => {
      const h1 = Math.pow(10, m / 20);
      const h2 = Math.pow(10, hpResp.mag[i] / 20);
      return 20 * Math.log10(h1 * h2 + 1e-9);
    });
    drawLine(lp.freq, mag, '#0074D9');
    drawLabel('Filter');
  }

  function drawEnv(inputs, label) {
    const a = parseFloat(inputs.attack.value);
    const d = parseFloat(inputs.decay.value);
    const s = parseFloat(inputs.sustain.value);
    const r = parseFloat(inputs.release.value);
    const i = inputs.initial ? parseFloat(inputs.initial.value) : 0;
    const p = inputs.peak ? parseFloat(inputs.peak.value) : 1;
    const f = inputs.finalVal ? parseFloat(inputs.finalVal.value) : 0;
    const hold = 0.25;
    const total = a + d + r + hold;
    const w = canvas.width;
    const h = canvas.height;
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
    drawLabel(label);
  }

  function drawLine(freq, mag, color) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    const minDb = -60;
    const maxDb = 60;
    const logMin = Math.log10(10);
    const logMax = Math.log10(20000);
    for (let i = 0; i < freq.length; i++) {
      const x = ((Math.log10(freq[i]) - logMin) / (logMax - logMin)) * canvas.width;
      const db = Math.max(minDb, Math.min(maxDb, mag[i]));
      const y = canvas.height - ((db - minDb) / (maxDb - minDb)) * canvas.height;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = color;
    ctx.stroke();
  }

  let active = 'filter';

  window.driftVizSetMode = (mode) => {
    if (['filter', 'env1', 'env2'].includes(mode)) {
      active = mode;
      update();
    }
  };
  function update() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (active === 'env1') {
      drawEnv(env1, 'Amp');
    } else if (active === 'env2' && (!env2.mode || env2.mode.value !== 'Cyc')) {
      drawEnv(env2, 'Env2');
    } else {
      drawFilter();
    }
  }

  const setFilter = () => { active = 'filter'; update(); };
  const setEnv1 = () => { active = 'env1'; update(); };
  const setEnv2 = () => { active = 'env2'; update(); };

  Object.values(filterInputs).forEach(el => {
    if (!el) return;
    el.addEventListener('change', setFilter);
    el.addEventListener('input', setFilter);
  });
  [env1.attack, env1.decay, env1.sustain, env1.release].forEach(el => el && el.addEventListener('input', setEnv1));
  [env2.attack, env2.decay, env2.sustain, env2.release].forEach(el => el && el.addEventListener('input', setEnv2));
  if (env2.mode) env2.mode.addEventListener('change', () => { if (active === 'env2') update(); });

  update();
}

document.addEventListener('DOMContentLoaded', initDriftCombinedViz);
