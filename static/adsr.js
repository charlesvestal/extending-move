document.addEventListener('DOMContentLoaded', () => {
  const attack = document.getElementById('attack');
  const decay = document.getElementById('decay');
  const sustain = document.getElementById('sustain');
  const release = document.getElementById('release');
  const attackSlope = document.getElementById('attack-slope');
  const decaySlope = document.getElementById('decay-slope');
  const releaseSlope = document.getElementById('release-slope');
  const initial = document.getElementById('initial');
  const peak = document.getElementById('peak');
  const final = document.getElementById('final');
  const canvas = document.getElementById('adsr-canvas');
  const ctx = canvas.getContext('2d');

  function applySlope(t, slope) {
    const s = parseFloat(slope) / 100;
    // slope -100 => exp=3 (convex), 0 => exp=1 (linear), 100 => exp=-1 (concave)
    const exp = 1 - 2 * s;
    const clamped = Math.max(parseFloat(t), 0.001);
    return Math.pow(clamped, exp);
  }

  function draw() {
    const a = parseFloat(attack.value);
    const d = parseFloat(decay.value);
    const sLevel = parseFloat(sustain.value);
    const r = parseFloat(release.value);
    const aSlopeVal = parseFloat(attackSlope.value);
    const dSlopeVal = parseFloat(decaySlope.value);
    const rSlopeVal = parseFloat(releaseSlope.value);
    const initVal = parseFloat(initial.value);
    const peakVal = parseFloat(peak.value);
    const finalVal = parseFloat(final.value);

    const hold = 0.25; // constant hold portion
    const total = a + d + r + hold;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();

    const steps = 20;
    let x = 0;
    ctx.moveTo(0, h - initVal * h);

    const aWidth = (a / total) * w;
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      const curve = applySlope(t, aSlopeVal);
      const val = initVal + (peakVal - initVal) * curve;
      ctx.lineTo(x + aWidth * t, h - val * h);
    }
    x += aWidth;

    const dWidth = (d / total) * w;
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      const curve = applySlope(t, dSlopeVal);
      const val = peakVal + (sLevel - peakVal) * curve;
      ctx.lineTo(x + dWidth * t, h - val * h);
    }
    x += dWidth;

    const holdWidth = (hold / total) * w;
    ctx.lineTo(x + holdWidth, h - sLevel * h);
    x += holdWidth;

    const rWidth = (r / total) * w;
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      const curve = applySlope(t, rSlopeVal);
      const val = sLevel + (finalVal - sLevel) * curve;
      ctx.lineTo(x + rWidth * t, h - val * h);
    }

    ctx.strokeStyle = '#f00';
    ctx.stroke();
  }

  attack.addEventListener('input', draw);
  decay.addEventListener('input', draw);
  sustain.addEventListener('input', draw);
  release.addEventListener('input', draw);
  attackSlope.addEventListener('input', draw);
  decaySlope.addEventListener('input', draw);
  releaseSlope.addEventListener('input', draw);
  initial.addEventListener('input', draw);
  peak.addEventListener('input', draw);
  final.addEventListener('input', draw);
  draw();
});
