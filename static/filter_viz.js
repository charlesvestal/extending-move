export function initFilterViz() {
  const form = document.getElementById('filter-form');
  const canvas = document.getElementById('filterChart');
  if (!form || !canvas) return;
  const ctx = canvas.getContext('2d');

  async function update() {
    const formData = new FormData(form);
    const resp = await fetch(form.action, {
      method: 'POST',
      body: formData,
    });
    if (!resp.ok) return;
    const data = await resp.json();
    if (data.mag1 && data.mag2) {
      draw(data.freq, data.mag1, data.mag2);
    } else {
      draw(data.freq, data.mag);
    }
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
    if (mag2) {
      drawLine(freq, mag2, '#FF4136');
    }
  }

  form.addEventListener('input', update);
  update();
}

document.addEventListener('DOMContentLoaded', initFilterViz);
