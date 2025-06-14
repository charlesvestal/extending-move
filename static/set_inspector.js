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
  let dirty = false;
  let currentEnv = [];
  let tailEnv = [];
  let envInfo = null;
  let viewStart = 0;
  let viewLength = region;
  let panning = false;
  let panStartX = 0;
  let panStartY = 0;
  let panStartView = 0;
  let panStartNote = 0;
  let pinchStart = 0;
  let pinchView = 0;
  let pinchViewStart = 0;
  let pinchCenter = 0;

  function isNormalized(env) {
    if (!env || !env.breakpoints || !env.breakpoints.length) return false;
    const vals = env.breakpoints.map(b => b.value);
    const minV = Math.min(...vals);
    const maxV = Math.max(...vals);
    return minV >= 0 && maxV <= 1 && (env.rangeMin !== 0 || env.rangeMax !== 1);
  }

  function updateControls() {
    const hasEnv = envSelect && envSelect.value;
    if (editBtn) {
      editBtn.style.display = hasEnv && !editing ? '' : 'none';
    }
    if (saveForm) {
      saveForm.style.display = hasEnv && editing ? 'inline' : 'none';
    }
    if (saveBtn) {
      if (editing) {
        saveBtn.disabled = !dirty;
      } else {
        saveBtn.disabled = true;
      }
    }
  }
  if (legendDiv) {
    legendDiv.style.display = 'flex';
    legendDiv.style.flexDirection = 'column';
    legendDiv.style.justifyContent = 'space-between';
    legendDiv.style.alignItems = 'flex-end';
    legendDiv.style.height = canvas.height + 'px';
  }

  function calcInitialRange() {
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

  const baseRange = calcInitialRange();
  let noteViewMin = baseRange.min;
  const noteViewRange = baseRange.max - baseRange.min + 1;

  function getVisibleRange() {
    let min = Math.round(noteViewMin);
    let max = min + noteViewRange - 1;
    if (min < 0) {
      min = 0;
      max = min + noteViewRange - 1;
    }
    if (max > 127) {
      max = 127;
      min = max - noteViewRange + 1;
    }
    return { min, max };
  }

  function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const { min, max } = getVisibleRange();
    const noteRange = max - min + 1;

    const visibleEnd = viewStart + viewLength;
    ctx.strokeStyle = '#ddd';
    const startBeat = Math.floor(viewStart);
    const endBeat = Math.ceil(visibleEnd);
    for (let b = startBeat; b <= endBeat; b++) {
      const x = ((b - viewStart) / viewLength) * canvas.width;
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
    const visibleEnd = viewStart + viewLength;
    notes.forEach(n => {
      const start = Math.max(n.startTime, viewStart);
      const end = Math.min(n.startTime + n.duration, visibleEnd);
      if (end <= viewStart || start >= visibleEnd) return;
      const x = ((start - viewStart) / viewLength) * canvas.width;
      const w = ((end - start) / viewLength) * canvas.width;
      const y = canvas.height - (n.noteNumber - min + 1) * h;
      ctx.fillRect(x, y, w, h);
    });
  }

  function drawEnvelope() {
    if (!envSelect || !envSelect.value) return;
    const param = parseInt(envSelect.value);
    let env;
    if (editing) {
      const bps = drawing ? currentEnv.concat(tailEnv) : currentEnv;
      env = envInfo ? { ...envInfo, breakpoints: bps } : { breakpoints: bps };
    } else {
      env = envInfo;
    }
    if (!env || !env.breakpoints || !env.breakpoints.length) return;
    ctx.strokeStyle = '#FF4136';
    ctx.beginPath();
    const needsScale = isNormalized(env);
    const visibleEnd = viewStart + viewLength;
    env.breakpoints.forEach((bp, i) => {
      if (bp.time < viewStart || bp.time > visibleEnd) return;
      const x = ((bp.time - viewStart) / viewLength) * canvas.width;
      let v = bp.value;
      if (needsScale) {
        v = env.rangeMin + v * (env.rangeMax - env.rangeMin);
      }
      const scale = env.domainMax - env.domainMin;
      const y = canvas.height - ((v - env.domainMin) / scale) * canvas.height;
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

  function clampView() {
    if (viewLength < region / 32) viewLength = region / 32;
    if (viewLength > region) viewLength = region;
    if (viewStart < 0) viewStart = 0;
    if (viewStart + viewLength > region) viewStart = region - viewLength;
    if (noteViewMin < 0) noteViewMin = 0;
    if (noteViewMin + noteViewRange - 1 > 127) noteViewMin = 127 - noteViewRange + 1;
  }

  function updateLegend() {
    if (!legendDiv) return;
    if (!envSelect || !envSelect.value) {
      legendDiv.textContent = '';
      return;
    }
    const param = parseInt(envSelect.value);
    let range = envelopes.find(e => e.parameterId === param);
    if (!range) range = paramRanges[param];
    if (!range || typeof range.rangeMin === 'undefined' && typeof range.min === 'undefined') {
      legendDiv.textContent = '';
      return;
    }
    const min = range.rangeMin !== undefined ? range.rangeMin : range.min;
    const max = range.rangeMax !== undefined ? range.rangeMax : range.max;
    const unit = range.unit ? ' ' + range.unit : '';
    const mid = (min + max) / 2;
    const fmt = v => Number(v).toFixed(2) + unit;
    legendDiv.innerHTML =
      `<div style="text-align:right;">${fmt(max)}</div>` +
      `<div style="text-align:right;">${fmt(mid)}</div>` +
      `<div style="text-align:right;">${fmt(min)}</div>`;
  }

  function draw() {
    drawGrid();
    drawNotes();
    drawLabels();
    drawEnvelope();
  }

  if (envSelect) envSelect.addEventListener('change', () => {
    editing = false;
    drawing = false;
    dirty = false;
    currentEnv = [];
    envInfo = null;
    if (envSelect.value) {
      const pid = parseInt(envSelect.value);
      paramInput.value = pid;
      envInfo = envelopes.find(e => e.parameterId === pid);
      if (!envInfo && paramRanges[pid]) {
        const r = paramRanges[pid];
        envInfo = {
          rangeMin: r.min,
          rangeMax: r.max,
          domainMin: r.min,
          domainMax: r.max,
          unit: r.unit,
          breakpoints: [],
        };
      }
    }
    if (saveBtn) saveBtn.disabled = true;
    updateLegend();
    updateControls();
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
    const env = editing ? (envInfo ? { ...envInfo, breakpoints: currentEnv } : { breakpoints: currentEnv }) : envInfo;
    if (!env || !env.breakpoints || !env.breakpoints.length) { valueDiv.textContent = ''; return; }
    const pos = canvasPos(ev);
    const t = viewStart + (pos.x / canvas.width) * viewLength;
    let v = envValueAt(env.breakpoints, t);
    if (isNormalized(env)) {
      v = env.rangeMin + v * (env.rangeMax - env.rangeMin);
    }
    const unit = env.unit ? ' ' + env.unit : '';
    valueDiv.textContent = v.toFixed(3) + unit;
  }

  function startDraw(ev) {
    if (!editing) return;
    drawing = true;
    dirty = true;
    const { x, y } = canvasPos(ev);
    const t = viewStart + (x / canvas.width) * viewLength;
    const env = currentEnv.length ? currentEnv : (envInfo ? envInfo.breakpoints : []);
    const before = env.filter(bp => bp.time < t);
    tailEnv = env.filter(bp => bp.time > t);
    const startV = envValueAt(env, t);
    let v0;
    if (isNormalized(envInfo)) {
      v0 = 1 - y / canvas.height;
    } else {
      v0 = envInfo.domainMax - (y / canvas.height) * (envInfo.domainMax - envInfo.domainMin);
    }
    currentEnv = [...before, { time: t, value: startV }, { time: t, value: v0 }];
    updateControls();
    draw();
    ev.preventDefault();
  }

  function continueDraw(ev) {
    if (!drawing) {
      showValue(ev);
      return;
    }
    const { x, y } = canvasPos(ev);
    const t = viewStart + (x / canvas.width) * viewLength;
    let v;
    if (isNormalized(envInfo)) {
      v = 1 - y / canvas.height;
    } else {
      v = envInfo.domainMax - (y / canvas.height) * (envInfo.domainMax - envInfo.domainMin);
    }
    while (tailEnv.length && tailEnv[0].time <= t) {
      tailEnv.shift();
    }
    while (currentEnv.length && t < currentEnv[currentEnv.length - 1].time) {
      currentEnv.pop();
    }
    currentEnv.push({ time: t, value: v });
    draw();
    ev.preventDefault();
  }

  function endDraw() {
    if (drawing) {
      drawing = false;
      currentEnv = currentEnv.concat(tailEnv);
      tailEnv = [];
      draw();
    }
  }

  canvas.addEventListener('wheel', ev => {
    const rect = canvas.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const center = viewStart + (x / canvas.width) * viewLength;
    const scale = Math.exp(ev.deltaY * 0.001);
    viewLength *= scale;
    viewStart = center - (x / canvas.width) * viewLength;
    clampView();
    draw();
    ev.preventDefault();
  });

  canvas.addEventListener('mousedown', ev => {
    if (editing) { startDraw(ev); return; }
    panning = true;
    panStartX = ev.clientX;
    panStartY = ev.clientY;
    panStartView = viewStart;
    panStartNote = noteViewMin;
    ev.preventDefault();
  });

  canvas.addEventListener('mousemove', ev => {
    if (editing) { continueDraw(ev); return; }
    if (panning) {
      const dx = (ev.clientX - panStartX) / canvas.width * viewLength;
      const dy = (ev.clientY - panStartY) / canvas.height * noteViewRange;
      viewStart = panStartView - dx;
      noteViewMin = panStartNote - dy;
      clampView();
      draw();
    }
  });

  document.addEventListener('mouseup', ev => {
    if (panning) { panning = false; }
    endDraw();
  });

  canvas.addEventListener('touchstart', ev => {
    if (ev.touches.length === 1 && !editing) {
      panning = true;
      panStartX = ev.touches[0].clientX;
      panStartY = ev.touches[0].clientY;
      panStartView = viewStart;
      panStartNote = noteViewMin;
    } else if (ev.touches.length === 2) {
      panning = false;
      drawing = false;
      pinchStart = Math.hypot(
        ev.touches[0].clientX - ev.touches[1].clientX,
        ev.touches[0].clientY - ev.touches[1].clientY
      );
      pinchView = viewLength;
      pinchViewStart = viewStart;
      const rect = canvas.getBoundingClientRect();
      const midX = ((ev.touches[0].clientX + ev.touches[1].clientX) / 2) - rect.left;
      pinchCenter = viewStart + (midX / canvas.width) * viewLength;
    } else {
      startDraw(ev);
    }
    ev.preventDefault();
  });

  canvas.addEventListener('touchmove', ev => {
    if (ev.touches.length === 2 && pinchStart) {
      const newDist = Math.hypot(
        ev.touches[0].clientX - ev.touches[1].clientX,
        ev.touches[0].clientY - ev.touches[1].clientY
      );
      const scale = pinchStart / newDist;
      viewLength = pinchView * scale;
      viewStart = pinchCenter - ((pinchCenter - pinchViewStart) * (viewLength / pinchView));
    } else if (panning && ev.touches.length === 1) {
      const dx = (ev.touches[0].clientX - panStartX) / canvas.width * viewLength;
      const dy = (ev.touches[0].clientY - panStartY) / canvas.height * noteViewRange;
      viewStart = panStartView - dx;
      noteViewMin = panStartNote - dy;
    } else if (editing) {
      continueDraw(ev);
      return;
    }
    clampView();
    draw();
    ev.preventDefault();
  });

  document.addEventListener('touchend', ev => {
    if (ev.touches.length === 0) {
      panning = false;
      pinchStart = 0;
      endDraw();
    }
  });

  canvas.addEventListener('mouseleave', () => {
    if (!drawing && valueDiv) valueDiv.textContent = '';
  });

  if (editBtn) editBtn.addEventListener('click', () => {
    if (!envSelect.value) return;
    editing = true;
    drawing = false;
    dirty = false;
    const pid = parseInt(envSelect.value);
    envInfo = envelopes.find(e => e.parameterId === pid);
    if (!envInfo && paramRanges[pid]) {
      const r = paramRanges[pid];
      envInfo = {
        rangeMin: r.min,
        rangeMax: r.max,
        domainMin: r.min,
        domainMax: r.max,
        unit: r.unit,
        breakpoints: [],
      };
    }
    currentEnv = envInfo ? envInfo.breakpoints.map(bp => ({ ...bp })) : [];
    paramInput.value = pid;
    if (saveBtn) saveBtn.disabled = true;
    updateControls();
    draw();
  });

  if (saveForm) saveForm.addEventListener('submit', () => {
    envInput.value = JSON.stringify(currentEnv);
  });
  if (envSelect && envSelect.value) {
    envSelect.dispatchEvent(new Event('change'));
  } else {
    updateLegend();
    updateControls();
    draw();
  }
}

document.addEventListener('DOMContentLoaded', initSetInspector);
