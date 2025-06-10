export function initParamAdsr() {
  const sets = [
    {
      canvas: document.getElementById('amp-env-canvas'),
      attack: document.querySelector('.param-item[data-name="Envelope1_Attack"] input[type="range"]'),
      decay: document.querySelector('.param-item[data-name="Envelope1_Decay"] input[type="range"]'),
      sustain: document.querySelector('.param-item[data-name="Envelope1_Sustain"] input[type="range"]'),
      release: document.querySelector('.param-item[data-name="Envelope1_Release"] input[type="range"]'),
    },
    {
      canvas: document.getElementById('env2-canvas'),
      attack: document.querySelector('.param-item[data-name="Envelope2_Attack"] input[type="range"]'),
      decay: document.querySelector('.param-item[data-name="Envelope2_Decay"] input[type="range"]'),
      sustain: document.querySelector('.param-item[data-name="Envelope2_Sustain"] input[type="range"]'),
      release: document.querySelector('.param-item[data-name="Envelope2_Release"] input[type="range"]'),
      modeInput: document.querySelector('.param-item[data-name="Global_Envelope2Mode"] input[type="hidden"]')
    }
  ];

  sets.forEach(set => {
    if (!set.canvas || !set.attack || !set.decay || !set.sustain || !set.release) {
      return;
    }
    const ctx = set.canvas.getContext('2d');
    function draw() {
      const a = parseFloat(set.attack.value);
      const d = parseFloat(set.decay.value);
      const s = parseFloat(set.sustain.value);
      const r = parseFloat(set.release.value);
      const hold = 0.25;
      const total = a + d + r + hold;
      const w = set.canvas.width;
      const h = set.canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.beginPath();
      ctx.moveTo(0, h);
      let x = (a / total) * w;
      ctx.lineTo(x, 0);
      const decEnd = x + (d / total) * w;
      ctx.lineTo(decEnd, h - s * h);
      const relStart = w - (r / total) * w;
      ctx.lineTo(relStart, h - s * h);
      ctx.lineTo(w, h);
      ctx.strokeStyle = '#f00';
      ctx.stroke();
    }
    [set.attack, set.decay, set.sustain, set.release].forEach(el => {
      el.addEventListener('input', draw);
    });
    if (set.modeInput) {
      function toggle() {
        const envSel = document.querySelector('input[name="env_select"]:checked');
        const env2View = envSel && envSel.value === 'env2';
        const show = env2View && set.modeInput.value !== 'Cyc';
        set.canvas.classList.toggle('hidden', !show);
      }
      set.modeInput.addEventListener('change', toggle);
      document.querySelectorAll('input[name="env_select"]').forEach(r =>
        r.addEventListener('change', toggle)
      );
      toggle();
    }
    draw();
  });
}

document.addEventListener('DOMContentLoaded', initParamAdsr);
