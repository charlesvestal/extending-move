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

  // Auto-load clip when a clip cell is clicked
  const clipGrid = document.querySelector('#clipSelectForm .pad-grid');
  const clipNameSpan = document.getElementById('selected-clip-name');
  if (clipGrid) {
    const form = document.getElementById('clipSelectForm');
    clipGrid.querySelectorAll('input[name="clip_select"]').forEach(radio => {
      radio.addEventListener('change', () => {
        const label = clipGrid.querySelector(`label[for="${radio.id}"]`);
        if (clipNameSpan) {
          clipNameSpan.textContent = label?.dataset.name || '';
        }
        form.submit();
      });
    });
  }

  const dataDiv = document.getElementById('clipData');
  if (!dataDiv) return;
  const notes = JSON.parse(dataDiv.dataset.notes || '[]');
  const envelopes = JSON.parse(dataDiv.dataset.envelopes || '[]');
  const region = parseFloat(dataDiv.dataset.region || '4');
  const paramRanges = JSON.parse(dataDiv.dataset.paramRanges || '{}');
  const canvas = document.getElementById('clipCanvas');
  const ctx = canvas.getContext('2d');
  const envSelect = document.getElementById('envelope_select');
  const legendDiv = document.getElementById('paramLegend');
  const editBtn = document.getElementById('editEnvBtn');
  const saveForm = document.getElementById('saveEnvForm');
  const saveBtn = document.getElementById('saveEnvBtn');
  const paramInput = document.getElementById('parameter_id_input');
  const envInput = document.getElementById('envelope_data_input');
  const valueDiv = document.getElementById('envValue');

  let editing = false;
  let drawing = false;
  let currentEnv = [];
  if (legendDiv) {
    legendDiv.style.display = 'flex';
    legendDiv.style.flexDirection = 'column';
    legendDiv.style.justifyContent = 'space-between';
    legendDiv.style.alignItems = 'flex-end';
    legendDiv.style.height = canvas.height + 'px';
  }

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
    const env = editing ? { breakpoints: currentEnv } : envelopes.find(e => e.parameterId === param);
    if (!env || !env.breakpoints.length) return;
    ctx.strokeStyle = '#FF4136';
    ctx.beginPath();
    env.breakpoints.forEach((bp, i) => {
      const x = (bp.time / region) * canvas.width;
      const y = canvas.height - bp.value * canvas.height;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  function envValueAt(bps, t) {
    if (!bps.length) return 0;
    if (t <= bps[0].time) return bps[0].value;
    for (let i = 1; i < bps.length; i++) {
      if (t < bps[i].time) {
        const a = bps[i - 1];
        const b = bps[i];
        const p = (t - a.time) / (b.time - a.time);
        return a.value + p * (b.value - a.value);
      }
    }
    return bps[bps.length - 1].value;
  }

  function updateLegend() {
    if (!legendDiv) return;
    if (!envSelect || !envSelect.value) {
      legendDiv.textContent = '';
      return;
    }
    const param = parseInt(envSelect.value);
    const range = paramRanges[param];
    if (!range || typeof range.min !== 'number' || typeof range.max !== 'number') {
      legendDiv.textContent = '';
      return;
    }
    const mid = (range.min + range.max) / 2;
    const unit = range.unit ? ' ' + range.unit : '';
    const fmt = v => Number(v).toFixed(2) + unit;
    legendDiv.innerHTML =
      `<div style="text-align:right;">${fmt(range.max)}</div>` +
      `<div style="text-align:right;">${fmt(mid)}</div>` +
      `<div style="text-align:right;">${fmt(range.min)}</div>`;
  }

  function draw() {
    drawGrid();
    drawNotes();
    drawLabels();
    drawEnvelope();
  }

  if (envSelect) envSelect.addEventListener('change', () => {
    updateLegend();
    if (editing) {
      const param = parseInt(envSelect.value);
      const src = envelopes.find(e => e.parameterId === param);
      currentEnv = src ? src.breakpoints.map(bp => ({ ...bp })) : [];
      paramInput.value = envSelect.value;
      saveBtn.style.display = 'none';
    }
    draw();
  });

  function canvasPos(ev) {
    const rect = canvas.getBoundingClientRect();
    const x = (ev.touches ? ev.touches[0].clientX : ev.clientX) - rect.left;
    const y = (ev.touches ? ev.touches[0].clientY : ev.clientY) - rect.top;
    return { x, y };
  }

  function showValue(ev) {
    if (!envSelect || !envSelect.value || !valueDiv) return;
    const param = parseInt(envSelect.value);
    const env = editing ? { breakpoints: currentEnv } : envelopes.find(e => e.parameterId === param);
    if (!env || !env.breakpoints.length) { valueDiv.textContent = ''; draw(); return; }
    const pos = canvasPos(ev);
    const t = (pos.x / canvas.width) * region;
    let v = envValueAt(env.breakpoints, t);
    const range = paramRanges[param];
    if (range && typeof range.min === 'number' && typeof range.max === 'number') {
      v = range.min + v * (range.max - range.min);
    }
    const txt = v.toFixed(3);
    valueDiv.textContent = txt;

    draw();
    ctx.save();
    ctx.fillStyle = '#000';
    ctx.font = '10px sans-serif';
    ctx.textBaseline = 'bottom';
    ctx.fillText(txt, pos.x + 5, pos.y - 5);
    ctx.restore();
  }

  function startDraw(ev) {
    if (!editing) return;
    drawing = true;
    currentEnv = [];
    const { x, y } = canvasPos(ev);
    currentEnv.push({ time: (x / canvas.width) * region, value: 1 - y / canvas.height });
    ev.preventDefault();
  }

  function continueDraw(ev) {
    if (!drawing) {
      showValue(ev);
      return;
    }
    const { x, y } = canvasPos(ev);
    currentEnv.push({ time: (x / canvas.width) * region, value: 1 - y / canvas.height });
    draw();
    ev.preventDefault();
  }

  function endDraw() {
    if (drawing) {
      drawing = false;
      if (saveBtn) saveBtn.style.display = '';
    }
  }

  canvas.addEventListener('mousedown', startDraw);
  canvas.addEventListener('touchstart', startDraw);
  canvas.addEventListener('mousemove', continueDraw);
  canvas.addEventListener('touchmove', continueDraw);
  canvas.addEventListener('mouseleave', () => {
    if (!drawing && valueDiv) valueDiv.textContent = '';
    if (!drawing) draw();
  });
  document.addEventListener('mouseup', endDraw);
  document.addEventListener('touchend', endDraw);

  if (editBtn) editBtn.addEventListener('click', () => {
    if (!envSelect.value) return;
    editing = true;
    const param = parseInt(envSelect.value);
    const src = envelopes.find(e => e.parameterId === param);
    currentEnv = src ? src.breakpoints.map(bp => ({ ...bp })) : [];
    paramInput.value = envSelect.value;
    editBtn.style.display = 'none';
    if (saveForm) saveForm.style.display = 'block';
    saveBtn.style.display = 'none';
    draw();
  });

  if (saveForm) saveForm.addEventListener('submit', () => {
    envInput.value = JSON.stringify(currentEnv);
  });
  updateLegend();
  draw();
}

document.addEventListener('DOMContentLoaded', initSetInspector);
