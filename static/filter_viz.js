export function initFilterViz() {
  const form = document.getElementById('filter-form');
  const canvas = document.getElementById('filterChart');
  if (!form || !canvas) return;
  const ctx = canvas.getContext('2d');
  const fMin = 20;
  const fMax = 20000;
  const minDb = -60;
  const maxDb = 0;

  function freqToX(f) {
    const xNorm = (Math.log10(f / fMin) / Math.log10(fMax / fMin));
    return xNorm * canvas.width;
  }

  function dbToY(db) {
    const clamped = Math.max(minDb, Math.min(maxDb, db));
    return canvas.height - ((clamped - minDb) / (maxDb - minDb)) * canvas.height;
  }

  async function update() {
    const formData = new FormData(form);
    const resp = await fetch(form.action, {
      method: 'POST',
      body: formData,
    });
    if (!resp.ok) return;
    const data = await resp.json();
    const slope1 = parseInt(form.querySelector('select[name="filter1_slope"]').value || '12');
    const slope2Sel = form.querySelector('select[name="filter2_slope"]');
    const slope2 = slope2Sel ? parseInt(slope2Sel.value || '12') : 12;
    if (data.mag1 && data.mag2) {
      draw(data.freq, data.mag1, slope1, data.mag2, slope2);
    } else {
      draw(data.freq, data.mag, slope1);
    }
  }

  function drawLine(freq, mag, color) {
    ctx.beginPath();
    for (let i = 0; i < freq.length; i++) {
      const x = freqToX(freq[i]);
      const y = dbToY(mag[i]);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = color;
    ctx.stroke();
  }

  function cutoffFrequency(freq, mag) {
    for (let i = 0; i < freq.length; i++) {
      if (mag[i] <= -3) {
        return freq[i];
      }
    }
    return null;
  }

  function drawCutoff(fc) {
    if (!fc) return;
    const x = freqToX(fc);
    const y = dbToY(-3);
    ctx.strokeStyle = '#666';
    ctx.beginPath();
    ctx.moveTo(x, canvas.height);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.fillStyle = '#666';
    ctx.fillText('f_c', x + 4, y - 4);
  }

  function drawSlope(fc, slopeDbOct) {
    if (!fc) return;
    const x1 = freqToX(fc);
    const y1 = dbToY(-3);
    const x2 = freqToX(Math.min(fc * 2, fMax));
    const y2 = dbToY(-3 - slopeDbOct);
    ctx.strokeStyle = '#666';
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.fillStyle = '#666';
    ctx.fillText(`${slopeDbOct} dB/oct`, x2 + 4, y2);
  }

  function draw(freq, mag1, slope1, mag2 = null, slope2 = null) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawLine(freq, mag1, '#0074D9');
    const fc1 = cutoffFrequency(freq, mag1);
    drawCutoff(fc1);
    drawSlope(fc1, slope1);
    if (mag2) {
      drawLine(freq, mag2, '#FF4136');
      const fc2 = cutoffFrequency(freq, mag2);
      drawCutoff(fc2);
      drawSlope(fc2, slope2);
    }
  }

  form.addEventListener('input', update);
  update();
}

document.addEventListener('DOMContentLoaded', initFilterViz);
