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
  const container = document.getElementById('pianoRollContainer');
  let ctx = null;
  if (canvas) {
    ctx = canvas.getContext('2d');
  }
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

  function toTransport(t) {
    const bar = Math.floor(t / 4);
    const q = Math.floor(t % 4);
    const s = Math.round((t - bar * 4 - q) * 4);
    return `${bar}:${q}:${s}`;
  }

  function toDuration(d) {
    if (!d) return 4;
    return Math.max(1, Math.round(4 / d));
  }

  let pianoRoll = null;
  if (container && window.pixiPianoRoll) {
    const noteData = notes.map(n => [toTransport(n.startTime), n.noteNumber, toDuration(n.duration)]);
    pianoRoll = pixiPianoRoll({
      width: canvas.width,
      height: canvas.height,
      noteFormat: 'MIDI',
      zoom: region,
      resolution: 4,
      renderer: 'Renderer',
      noteData,
    });
    pianoRoll.view.style.position = 'absolute';
    pianoRoll.view.style.left = '0';
    pianoRoll.view.style.top = '0';
    container.insertBefore(pianoRoll.view, canvas);
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
    env.breakpoints.forEach((bp, i) => {
      const x = (bp.time / region) * canvas.width;
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
    const t = (pos.x / canvas.width) * region;
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
    const t = (x / canvas.width) * region;
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
    const t = (x / canvas.width) * region;
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

  canvas.addEventListener('mousedown', startDraw);
  canvas.addEventListener('touchstart', startDraw);
  canvas.addEventListener('mousemove', continueDraw);
  canvas.addEventListener('touchmove', continueDraw);
  canvas.addEventListener('mouseleave', () => { if (!drawing && valueDiv) valueDiv.textContent = ''; });
  document.addEventListener('mouseup', endDraw);
  document.addEventListener('touchend', endDraw);

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
