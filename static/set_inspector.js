export function initSetInspector() {
  // Show selected set name when choosing a pad
  const grid = document.querySelector('#setSelectForm .pad-grid');
  const nameSpan = document.getElementById('selected-set-name');
  if (grid && nameSpan) {
    grid.querySelectorAll('input[name="pad_index"]').forEach(radio => {
      radio.addEventListener('change', () => {
        const label = grid.querySelector(`label[for="${radio.id}"]`);
        nameSpan.textContent = label?.dataset.name || '';
      });
    });
  }

  const dataDiv = document.getElementById('clipData');
  if (!dataDiv) return;
  const notes = JSON.parse(dataDiv.dataset.notes || '[]');
  const envelopes = JSON.parse(dataDiv.dataset.envelopes || '[]');
  const region = parseFloat(dataDiv.dataset.region || '4');
  const canvas = document.getElementById('clipCanvas');
  const ctx = canvas.getContext('2d');
  const envSelect = document.getElementById('envelope_select');

  function getVisibleRange() {
    if (!notes.length) return { min: 60, max: 71 }; // default middle C octave
    let min = Math.min(...notes.map(n => n.noteNumber));
    let max = Math.max(...notes.map(n => n.noteNumber));
    if (max - min < 11) {
      const extra = 11 - (max - min);
      min = Math.max(0, min - Math.floor(extra / 2));
      max = Math.min(127, max + Math.ceil(extra / 2));
    }
    return { min, max };
  }

  function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const { min, max } = getVisibleRange();
    const noteRange = max - min + 1;

    ctx.strokeStyle = '#ddd';
    for (let b = 0; b <= region; b++) {
      const x = (b / region) * canvas.width;
      ctx.beginPath();
      ctx.lineWidth = b % 4 === 0 ? 2 : 1;
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    ctx.lineWidth = 1;

    const h = canvas.height / noteRange;
    for (let n = min; n <= max; n++) {
      const y = canvas.height - (n - min) * h;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
  }

  function drawLabels() {
    const { min, max } = getVisibleRange();
    const noteRange = max - min + 1;
    const h = canvas.height / noteRange;
    ctx.fillStyle = '#000';
    ctx.font = '10px sans-serif';
    for (let n = min; n <= max; n++) {
      if (n % 12 === 0) {
        const y = canvas.height - (n - min) * h;
        const octave = Math.floor(n / 12) - 1;
        ctx.fillText(`C${octave}`, 2, y - 2);
      }
    }
  }

  function drawNotes() {
    const { min, max } = getVisibleRange();
    const noteRange = max - min + 1;
    const h = canvas.height / noteRange;
    ctx.fillStyle = '#0074D9';
    notes.forEach(n => {
      const x = (n.startTime / region) * canvas.width;
      const w = (n.duration / region) * canvas.width;
      const y = canvas.height - (n.noteNumber - min + 1) * h;
      ctx.fillRect(x, y, w, h);
    });
  }

  function drawEnvelope() {
    if (!envSelect || !envSelect.value) return;
    const param = parseInt(envSelect.value);
    const env = envelopes.find(e => e.parameterId === param);
    if (!env) return;
    ctx.strokeStyle = '#FF4136';
    ctx.beginPath();
    env.breakpoints.forEach((bp, i) => {
      const x = (bp.time / region) * canvas.width;
      const y = canvas.height - bp.value * canvas.height;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  function draw() {
    drawGrid();
    drawNotes();
    drawLabels();
    drawEnvelope();
  }

  if (envSelect) envSelect.addEventListener('change', draw);
  draw();
}

document.addEventListener('DOMContentLoaded', initSetInspector);
