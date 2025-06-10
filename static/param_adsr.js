export function initParamAdsr() {
  const sets = [
    {
      canvas: document.getElementById('amp-env-canvas'),
      attack: document.querySelector('.param-item[data-name="Voice_Modulators_AmpEnvelope_Times_Attack"] input[type="range"]'),
      decay: document.querySelector('.param-item[data-name="Voice_Modulators_AmpEnvelope_Times_Decay"] input[type="range"]'),
      sustain: document.querySelector('.param-item[data-name="Voice_Modulators_AmpEnvelope_Sustain"] input[type="range"]'),
      release: document.querySelector('.param-item[data-name="Voice_Modulators_AmpEnvelope_Times_Release"] input[type="range"]'),
    },
    {
      canvas: document.getElementById('env2-canvas'),
      attack: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope2_Times_Attack"] input[type="range"]'),
      decay: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope2_Times_Decay"] input[type="range"]'),
      sustain: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope2_Values_Sustain"] input[type="range"]'),
      release: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope2_Times_Release"] input[type="range"]'),
      initial: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope2_Values_Initial"] input[type="range"]'),
      peak: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope2_Values_Peak"] input[type="range"]'),
      final: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope2_Values_Final"] input[type="range"]'),
    },
    {
      canvas: document.getElementById('env3-canvas'),
      attack: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope3_Times_Attack"] input[type="range"]'),
      decay: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope3_Times_Decay"] input[type="range"]'),
      sustain: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope3_Values_Sustain"] input[type="range"]'),
      release: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope3_Times_Release"] input[type="range"]'),
      initial: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope3_Values_Initial"] input[type="range"]'),
      peak: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope3_Values_Peak"] input[type="range"]'),
      final: document.querySelector('.param-item[data-name="Voice_Modulators_Envelope3_Values_Final"] input[type="range"]'),
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
      const f = set.final ? parseFloat(set.final.value) : 0;

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
    [set.attack, set.decay, set.sustain, set.release, set.initial, set.peak, set.final].forEach(el => {
      if (el) el.addEventListener('input', draw);
    });
    draw();
  });
}

document.addEventListener('DOMContentLoaded', initParamAdsr);
