export function initFilterViz() {
  const form = document.getElementById('filter-form');
  const canvas = document.getElementById('filterChart');
  if (!form || !canvas) return;
  const ctx = canvas.getContext('2d');

  async function update() {
    const formData = new FormData(form);
    const resp = await fetch(form.action, {
      method: 'POST',
      body: formData
    });
    if (!resp.ok) return;
    const data = await resp.json();
    draw(data.freq, data.mag);
  }

  function draw(freq, mag) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    const minDb = -60;
    const maxDb = 12;
    for (let i = 0; i < freq.length; i++) {
      const x = (i / (freq.length - 1)) * canvas.width;
      const db = Math.max(minDb, Math.min(maxDb, mag[i]));
      const y = canvas.height - ((db - minDb) / (maxDb - minDb)) * canvas.height;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = '#0074D9';
    ctx.stroke();
  }

  form.addEventListener('input', update);
  update();
}

document.addEventListener('DOMContentLoaded', initFilterViz);
