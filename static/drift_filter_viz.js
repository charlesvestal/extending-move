export function initDriftFilterViz() {
  const filterPanel = document.querySelector('.param-panel.filter');
  if (!filterPanel) return;
  const canvas = document.createElement('canvas');
  canvas.id = 'driftFilterChart';
  canvas.width = 175;
  canvas.height = 88;
  canvas.style.marginTop = '1em';
  canvas.style.border = '1px solid #ccc';
  filterPanel.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  const freqInput = document.querySelector('.param-item[data-name="Filter_Frequency"] input[type="hidden"]');
  const typeInput = document.querySelector('.param-item[data-name="Filter_Type"] input[type="hidden"]');
  const resInput = document.querySelector('.param-item[data-name="Filter_Resonance"] input[type="hidden"]');
  const hpInput = document.querySelector('.param-item[data-name="Filter_HiPassFrequency"] input[type="hidden"]');

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
    return {
      b: [b0 / a0, b1 / a0, b2 / a0],
      a: [1, a1 / a0, a2 / a0]
    };
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
      if (String(slope) === '24') {
        m *= biquadMag(b, a, w);
      }
      freqArr.push(sr * i / (2 * (n - 1)));
      mag.push(20 * Math.log10(m + 1e-9));
    }
    return { freq: freqArr, mag };
  }

  function update() {
    if (!freqInput || !typeInput || !resInput || !hpInput) return;
    const lpSlope = typeInput.value === 'II' ? '24' : '12';
    const lp = computeResponse('lowpass', parseFloat(freqInput.value), parseFloat(resInput.value), lpSlope);
    const hp = computeResponse('highpass', parseFloat(hpInput.value), 0, '12');
    const mag = lp.mag.map((m, i) => {
      const h1 = Math.pow(10, m / 20);
      const h2 = Math.pow(10, hp.mag[i] / 20);
      return 20 * Math.log10(h1 * h2 + 1e-9);
    });
    draw(lp.freq, mag);
  }

  function drawLine(freq, mag, color) {
    ctx.beginPath();
    const minDb = -60;
    const maxDb = 12;
    for (let i = 0; i < freq.length; i++) {
      const x = (i / (freq.length - 1)) * canvas.width;
      const db = Math.max(minDb, Math.min(maxDb, mag[i]));
      const y = canvas.height - ((db - minDb) / (maxDb - minDb)) * canvas.height;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = color;
    ctx.stroke();
  }

  function draw(freq, mag) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawLine(freq, mag, '#0074D9');
  }

  const inputs = [freqInput, typeInput, resInput, hpInput];
  inputs.forEach(inp => inp && inp.addEventListener('change', update));
  update();
}

document.addEventListener('DOMContentLoaded', initDriftFilterViz);
