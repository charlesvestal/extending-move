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

  // Show selected clip name when choosing a clip
  const clipGrid = document.querySelector('#clipSelectForm .pad-grid');
  const clipNameSpan = document.getElementById('selected-clip-name');
  if (clipGrid && clipNameSpan) {
    clipGrid.querySelectorAll('input[name="clip_select"]').forEach(radio => {
      radio.addEventListener('change', () => {
        const label = clipGrid.querySelector(`label[for="${radio.id}"]`);
        clipNameSpan.textContent = label?.dataset.name || '';
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

  function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#ddd';
    for (let b = 0; b <= region; b++) {
      const x = (b / region) * canvas.width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let n = 0; n <= 127; n += 12) {
      const y = canvas.height - (n / 127) * canvas.height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
  }

  function drawNotes() {
    const h = canvas.height / 128;
    ctx.fillStyle = '#0074D9';
    notes.forEach(n => {
      const x = (n.startTime / region) * canvas.width;
      const w = (n.duration / region) * canvas.width;
      const y = canvas.height - (n.noteNumber + 1) * h;
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
    drawEnvelope();
  }

  if (envSelect) envSelect.addEventListener('change', draw);
  draw();
}

document.addEventListener('DOMContentLoaded', initSetInspector);
