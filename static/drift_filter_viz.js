export function initDriftFilterViz() {
  const canvas = document.getElementById('driftFilterChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const freqInput = document.querySelector('.param-item[data-name="Filter_Frequency"] input[type="hidden"]');
  const typeInput = document.querySelector('.param-item[data-name="Filter_Type"] input[type="hidden"]');
  const resInput = document.querySelector('.param-item[data-name="Filter_Resonance"] input[type="hidden"]');
  const hpInput = document.querySelector('.param-item[data-name="Filter_HiPassFrequency"] input[type="hidden"]');

  async function update() {
    if (!freqInput || !typeInput || !resInput || !hpInput) return;
    const slope = typeInput.value === 'II' ? '24' : '12';
    const formData = new FormData();
    formData.append('filter1_type', 'Lowpass');
    formData.append('filter1_freq', freqInput.value);
    formData.append('filter1_res', resInput.value);
    formData.append('filter1_slope', slope);
    formData.append('use_filter2', 'on');
    formData.append('filter2_type', 'Highpass');
    formData.append('filter2_freq', hpInput.value);
    formData.append('filter2_res', '0');
    formData.append('filter2_slope', '12');
    formData.append('routing', 'Serial');
    const resp = await fetch('/filter-viz', { method: 'POST', body: formData });
    if (!resp.ok) return;
    const data = await resp.json();
    draw(data.freq, data.mag);
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
