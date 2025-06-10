document.addEventListener('DOMContentLoaded', () => {
  const rate = document.getElementById('rate');
  const tilt = document.getElementById('tilt');
  const hold = document.getElementById('hold');
  const modeInputs = document.querySelectorAll('input[name="time_mode"]');
  const canvas = document.getElementById('cycle-canvas');
  const ctx = canvas.getContext('2d');

  function getTimeMode() {
    const checked = document.querySelector('input[name="time_mode"]:checked');
    return checked ? checked.value : 'Hz';
  }

  function draw() {
    const r = parseFloat(rate.value);
    const t = parseFloat(tilt.value);
    const mode = getTimeMode();

    let cycleLen = 1 / r; // default Hz -> seconds per cycle
    if (mode === 'ms') {
      // map knob range 0.1-10 to roughly 10-1000 ms
      cycleLen = r / 10; // seconds per cycle
    } else if (mode === 'ratio') {
      cycleLen = 1 / r; // treat same as Hz for prototype
    } else if (mode === 'sync') {
      cycleLen = 0.5; // quarter note at 120bpm for prototype
    }
    const displayLen = mode === 'sync' ? cycleLen * 3 : 2.25;
    const cycleCount = displayLen / cycleLen;

    const w = canvas.width;
    const hgt = canvas.height;
    ctx.clearRect(0, 0, w, hgt);
    ctx.strokeStyle = '#0a0';
    ctx.beginPath();

    const vertPos = (t + 1) / 2; // 0 to 1
    const peakX = vertPos * (w / cycleCount);

    const points = [];
    const holdVal = parseFloat(hold.value);
    for (let i = 0; i < cycleCount; i++) {
      const startX = (i / cycleCount) * w;
      const endX = ((i + 1) / cycleCount) * w;
      const peak = startX + peakX;

      points.push([startX, hgt]);
      points.push([peak, 0]);

      const holdEnd = peak + (endX - startX) * holdVal;
      if (holdVal > 0) {
        points.push([holdEnd, 0]);
      }

      if (t >= 0.2) {
        // Tilt at or above 0.2 draws a straight slope back to baseline
        points.push([endX, hgt]);
      } else {
        // Below 0.2 curve down using a simple 1/x style curve
        const curveStart = holdVal > 0 ? holdEnd : peak;
        const segs = 10;
        for (let s = 1; s <= segs; s++) {
          const frac = s / segs;
          const x = curveStart + frac * (endX - curveStart);
          const yFrac = 1 / (1 + frac * segs);
          points.push([x, (1 - yFrac) * hgt]);
        }
        points.push([endX, hgt]);
      }
    }
    ctx.moveTo(points[0][0], points[0][1]);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i][0], points[i][1]);
    }
    ctx.stroke();
  }

  [rate, tilt, hold].forEach(el => el.addEventListener('input', draw));
  modeInputs.forEach(el => el.addEventListener('change', draw));
  draw();
});
