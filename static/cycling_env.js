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
    const h = parseFloat(hold.value);
    const mode = getTimeMode();

    let cycleLen = 1 / r; // default Hz -> seconds per cycle
    if (mode === 'ms') {
      cycleLen = parseFloat(rate.value) / 1000;
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
    for (let i = 0; i < cycleCount; i++) {
      const startX = (i / cycleCount) * w;
      const endX = ((i + 1) / cycleCount) * w;
      const peak = startX + peakX;
      points.push([startX, hgt]);
      points.push([peak, 0]);
      if (hold.value > 0) {
        const holdEnd = peak + (endX - startX) * hold.value;
        points.push([holdEnd, 0]);
      }
      points.push([endX, hgt]);
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
