export function initParamAdsr() {
  const sets = [
    {
      canvas: document.getElementById('amp-env-canvas'),
      attack: document.querySelector('.param-item[data-name="Envelope1_Attack"] input[type="range"]'),
      decay: document.querySelector('.param-item[data-name="Envelope1_Decay"] input[type="range"]'),
      sustain: document.querySelector('.param-item[data-name="Envelope1_Sustain"] input[type="range"]'),
      release: document.querySelector('.param-item[data-name="Envelope1_Release"] input[type="range"]'),
      initial: document.querySelector('.param-item[data-name="Envelope1_Initial"] input[type="range"]'),
      peak: document.querySelector('.param-item[data-name="Envelope1_Peak"] input[type="range"]'),
      finalVal: document.querySelector('.param-item[data-name="Envelope1_Final"] input[type="range"]'),
    },
    {
      canvas: document.getElementById('env2-canvas'),
      attack: document.querySelector('.param-item[data-name="Envelope2_Attack"] input[type="range"]'),
      decay: document.querySelector('.param-item[data-name="Envelope2_Decay"] input[type="range"]'),
      sustain: document.querySelector('.param-item[data-name="Envelope2_Sustain"] input[type="range"]'),
      release: document.querySelector('.param-item[data-name="Envelope2_Release"] input[type="range"]'),
      initial: document.querySelector('.param-item[data-name="Envelope2_Initial"] input[type="range"]'),
      peak: document.querySelector('.param-item[data-name="Envelope2_Peak"] input[type="range"]'),
      finalVal: document.querySelector('.param-item[data-name="Envelope2_Final"] input[type="range"]'),
      modeInput: document.querySelector('.param-item[data-name="Global_Envelope2Mode"] input[type="hidden"]')
    },
    {
      canvas: document.getElementById('env3-canvas'),
      attack: document.querySelector('.param-item[data-name="Envelope3_Attack"] input[type="range"]'),
      decay: document.querySelector('.param-item[data-name="Envelope3_Decay"] input[type="range"]'),
      sustain: document.querySelector('.param-item[data-name="Envelope3_Sustain"] input[type="range"]'),
      release: document.querySelector('.param-item[data-name="Envelope3_Release"] input[type="range"]'),
      initial: document.querySelector('.param-item[data-name="Envelope3_Initial"] input[type="range"]'),
      peak: document.querySelector('.param-item[data-name="Envelope3_Peak"] input[type="range"]'),
      finalVal: document.querySelector('.param-item[data-name="Envelope3_Final"] input[type="range"]')
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
      const i = set.initial ? parseFloat(set.initial.value) : 0;
      const p = set.peak ? parseFloat(set.peak.value) : 1;
      const f = set.finalVal ? parseFloat(set.finalVal.value) : 0;
      const hold = 0.25;
      const total = a + d + r + hold;
      const w = set.canvas.width;
      const h = set.canvas.height;
      ctx.clearRect(0, 0, w, h);
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
    }
    [set.attack, set.decay, set.sustain, set.release, set.initial, set.peak, set.finalVal]
      .filter(Boolean)
      .forEach(el => {
        el.addEventListener('input', draw);
      });
    if (set.modeInput) {
      function updateVisibility() {
        const show = set.modeInput.value !== 'Cyc';
        set.canvas.classList.toggle('hidden', !show);
      }
      set.modeInput.addEventListener('change', () => {
        updateVisibility();
        draw();
      });
      updateVisibility();
    }
    draw();
  });
}

document.addEventListener('DOMContentLoaded', initParamAdsr);
