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
    on1: qsel('Voice_Filter1_On'),
    type2: qsel('Voice_Filter2_Type', 'select'),
    freq2: qsel('Voice_Filter2_Frequency'),
    res2: qsel('Voice_Filter2_Resonance'),
    slope2: qsel('Voice_Filter2_Slope', 'select'),
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

  function computeResponse(type, freq, res, slope, sr = 44100, n = 256) {
    const q = 0.5 + 9.5 * res;
    const { b, a } = biquadCoeffs(type, freq, q, sr);
    const freqArr = [];
    const mag = [];
    for (let i = 0; i < n; i++) {
      const w = Math.PI * i / (n - 1);
      let m = biquadMag(b, a, w);
      if (String(slope) === '24') m *= biquadMag(b, a, w);
      freqArr.push(sr * i / (2 * (n - 1)));
      mag.push(20 * Math.log10(m + 1e-9));
    }
    return { freq: freqArr, mag };
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
      const resp1 = computeResponse(f1.type, f1.freq, f1.res, f1.slope);
      return { freq: resp1.freq, mag1: resp1.mag };
    }

    if (!has1 && has2) {
      const resp2 = computeResponse(f2.type, f2.freq, f2.res, f2.slope);
      return { freq: resp2.freq, mag1: resp2.mag };
    }

    const resp1 = computeResponse(f1.type, f1.freq, f1.res, f1.slope);
    const resp2 = computeResponse(f2.type, f2.freq, f2.res, f2.slope);
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
    const maxDb = 12;
    const minFreq = 1;
    let fMin = Infinity;
    let fMax = 0;
    for (let i = 0; i < freq.length; i++) {
      const f = Math.max(minFreq, freq[i]);
      if (f < fMin) fMin = f;
      if (f > fMax) fMax = f;
    }
    const logMin = Math.log10(fMin);
    const logMax = Math.log10(fMax);
    for (let i = 0; i < freq.length; i++) {
      const f = Math.max(minFreq, freq[i]);
      const x = (Math.log10(f) - logMin) / (logMax - logMin) * canvas.width;
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

  function getFilterValues() {
    let f1 = null;
    if (!inputs.on1 || parseFloat(inputs.on1.value) !== 0) {
      f1 = {
        type: inputs.type1 ? inputs.type1.value : 'Lowpass',
        freq: parseFloat(inputs.freq1?.value || '1000'),
        res: parseFloat(inputs.res1?.value || '0'),
        slope: inputs.slope1 ? inputs.slope1.value : '12'
      };
    }
    let f2 = null;
    if (!inputs.on2 || parseFloat(inputs.on2.value) !== 0) {
      f2 = {
        type: inputs.type2 ? inputs.type2.value : 'Lowpass',
        freq: parseFloat(inputs.freq2?.value || '1000'),
        res: parseFloat(inputs.res2?.value || '0'),
        slope: inputs.slope2 ? inputs.slope2.value : '12'
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

  Object.values(inputs).forEach(inp => inp && inp.addEventListener('change', update));
  update();
}

document.addEventListener('DOMContentLoaded', initWavetableFilterViz);
