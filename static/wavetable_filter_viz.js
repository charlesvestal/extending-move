export function initWavetableFilterViz() {
  const filterPanel = document.querySelector('.param-panel.filter');
  if (!filterPanel) return;
  const canvas = document.createElement('canvas');
  canvas.id = 'wavetableFilterChart';
  canvas.width = 175;
  canvas.height = 88;
  canvas.style.border = '1px solid #ccc';
  const paramItems = filterPanel.querySelector('.param-items');
  if (paramItems) {
    filterPanel.insertBefore(canvas, paramItems);
  } else {
    filterPanel.appendChild(canvas);
  }
  const ctx = canvas.getContext('2d');

  const qsel = (name, sel = 'input[type="hidden"]') =>
    filterPanel.querySelector(`.param-item[data-name="${name}"] ${sel}`);

  const inputs = {
    type1: qsel('Voice_Filter1_Type', 'select'),
    freq1: qsel('Voice_Filter1_Frequency'),
    res1: qsel('Voice_Filter1_Resonance'),
    slope1: qsel('Voice_Filter1_Slope', 'select'),
    morph1: qsel('Voice_Filter1_Morph'),
    on1: qsel('Voice_Filter1_On'),
    type2: qsel('Voice_Filter2_Type', 'select'),
    freq2: qsel('Voice_Filter2_Frequency'),
    res2: qsel('Voice_Filter2_Resonance'),
    slope2: qsel('Voice_Filter2_Slope', 'select'),
    morph2: qsel('Voice_Filter2_Morph'),
    on2: qsel('Voice_Filter2_On'),
    routing: qsel('Voice_Global_FilterRouting')
  };

  function biquadCoeffs(type, freq, q, sr) {
    const w0 = 2 * Math.PI * freq / sr;
    const alpha = Math.sin(w0) / (2 * q);
    const cosw0 = Math.cos(w0);
    let b0, b1, b2, a0, a1, a2;
    switch (type.toLowerCase()) {
      case 'highpass':
        b0 = (1 + cosw0) / 2; b1 = -(1 + cosw0); b2 = (1 + cosw0) / 2;
        a0 = 1 + alpha; a1 = -2 * cosw0; a2 = 1 - alpha; break;
      case 'bandpass':
        b0 = alpha; b1 = 0; b2 = -alpha;
        a0 = 1 + alpha; a1 = -2 * cosw0; a2 = 1 - alpha; break;
      case 'notch':
        b0 = 1; b1 = -2 * cosw0; b2 = 1;
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

  function singleResponse(type, freq, q, slope, sr, freqs) {
    const { b, a } = biquadCoeffs(type, freq, q, sr);
    const mag = [];
    for (let i = 0; i < freqs.length; i++) {
      const w = 2 * Math.PI * freqs[i] / sr;
      let m = biquadMag(b, a, w);
      if (String(slope) === '24') m *= biquadMag(b, a, w);
      mag.push(20 * Math.log10(m + 1e-9));
    }
    return mag;
  }

  function computeResponse(type, freq, res, slope, morph = 0, sr = 44100, n = 256) {
    const q = 0.5 + 9.5 * res;
    const freqs = Array.from({ length: n }, (_, i) =>
      10 ** (Math.log10(10) + (Math.log10(20000) - Math.log10(10)) * i / (n - 1)));

    if (type.toLowerCase() === 'morph') {
      const stages = ['lowpass', 'bandpass', 'highpass', 'notch', 'lowpass'];
      const pos = morph * 4;
      const idx = Math.floor(pos);
      const frac = pos - idx;
      const mag1 = singleResponse(stages[idx], freq, q, slope, sr, freqs);
      const mag2 = singleResponse(stages[idx + 1], freq, q, slope, sr, freqs);
      const mag = mag1.map((m, i) => m * (1 - frac) + mag2[i] * frac);
      return { freq: freqs, mag };
    }

    const mag = singleResponse(type, freq, q, slope, sr, freqs);
    return { freq: freqs, mag };
  }

  function computeChain(f1, f2, routing) {
    const r = (routing || 'Serial').toLowerCase();
    const has1 = !!f1;
    const has2 = !!f2;

    if (!has1 && !has2) {
      const resp = computeResponse('lowpass', 22050, 0, '12');
      return { freq: resp.freq, mag1: resp.mag };
    }

    if (has1 && !has2) {
      const resp1 = computeResponse(f1.type, f1.freq, f1.res, f1.slope, f1.morph);
      return { freq: resp1.freq, mag1: resp1.mag };
    }

    if (!has1 && has2) {
      const resp2 = computeResponse(f2.type, f2.freq, f2.res, f2.slope, f2.morph);
      return { freq: resp2.freq, mag1: resp2.mag };
    }

    const resp1 = computeResponse(f1.type, f1.freq, f1.res, f1.slope, f1.morph);
    const resp2 = computeResponse(f2.type, f2.freq, f2.res, f2.slope, f2.morph);
    if (r === 'serial') {
      const mag = resp1.mag.map((m, i) => {
        const h1 = Math.pow(10, m / 20);
        const h2 = Math.pow(10, resp2.mag[i] / 20);
        return 20 * Math.log10(h1 * h2 + 1e-9);
      });
      return { freq: resp1.freq, mag1: mag };
    }
    return { freq: resp1.freq, mag1: resp1.mag, mag2: resp2.mag };
  }

  function drawLine(freq, mag, color) {
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

  function draw(freq, mag1, mag2 = null) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawLine(freq, mag1, '#0074D9');
    if (mag2) drawLine(freq, mag2, '#FF4136');
  }

  function normMorph(inp) {
    if (!inp) return 0;
    const val = parseFloat(inp.value || '0');
    const max = parseFloat(inp.max || '1');
    if (!max || isNaN(max)) return val;
    return val / max;
  }

  function getFilterValues() {
    let f1 = null;
    if (!inputs.on1 || parseFloat(inputs.on1.value) !== 0) {
      f1 = {
        type: inputs.type1 ? inputs.type1.value : 'Lowpass',
        freq: parseFloat(inputs.freq1?.value || '1000'),
        res: parseFloat(inputs.res1?.value || '0'),
        slope: inputs.slope1 ? inputs.slope1.value : '12',
        morph: normMorph(inputs.morph1)
      };
    }
    let f2 = null;
    if (!inputs.on2 || parseFloat(inputs.on2.value) !== 0) {
      f2 = {
        type: inputs.type2 ? inputs.type2.value : 'Lowpass',
        freq: parseFloat(inputs.freq2?.value || '1000'),
        res: parseFloat(inputs.res2?.value || '0'),
        slope: inputs.slope2 ? inputs.slope2.value : '12',
        morph: normMorph(inputs.morph2)
      };
    }
    const routing = inputs.routing ? inputs.routing.value : 'Serial';
    return { f1, f2, routing };
  }

  function update() {
    const { f1, f2, routing } = getFilterValues();
    const resp = computeChain(f1, f2, routing);
    draw(resp.freq, resp.mag1, resp.mag2);
  }

  Object.values(inputs).forEach(inp => {
    if (!inp) return;
    inp.addEventListener('change', update);
    inp.addEventListener('input', update);
  });
  update();
}

document.addEventListener('DOMContentLoaded', initWavetableFilterViz);
