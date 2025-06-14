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
  const loopStart = parseFloat(dataDiv.dataset.loopStart || '0');
  const loopEnd = parseFloat(dataDiv.dataset.loopEnd || String(region));
  const paramRanges = JSON.parse(dataDiv.dataset.paramRanges || '{}');
  const canvas = document.getElementById('clipCanvas');
  const ctx = canvas.getContext('2d');
  const piano = document.getElementById('clipEditor');
  const pitchNotes = JSON.parse(dataDiv.dataset.pitchbendNotes || '[]');
  const pitchPad = dataDiv.dataset.pitchPad ? parseInt(dataDiv.dataset.pitchPad) : null;
  const timebase = piano ? parseInt(piano.getAttribute('timebase') || '16', 10) : 16;
  const xruler = piano ? parseInt(piano.getAttribute('xruler') || '24', 10) : 24;
  const yruler = piano ? parseInt(piano.getAttribute('yruler') || '24', 10) : 24;
  const kbwidth = piano ? parseInt(piano.getAttribute('kbwidth') || '40', 10) : 40;
  const ticksPerBeat = timebase / 4;
  if (piano && canvas) {
    const w = parseInt(piano.getAttribute('width') || piano.clientWidth || 0, 10);
    const h = parseInt(piano.getAttribute('height') || piano.clientHeight || 0, 10);
    canvas.width = w - (yruler + kbwidth);
    canvas.height = h - xruler;
    canvas.style.left = `${yruler + kbwidth}px`;
    canvas.style.top = `${xruler}px`;
  }
  const envSelect = document.getElementById('envelope_select');
  const legendDiv = document.getElementById('paramLegend');
  const valueDiv = document.getElementById('envValue');
  const saveClipForm = document.getElementById('saveClipForm');
  const saveClipBtn = document.getElementById('saveClipBtn');
  const notesInput = document.getElementById('clip_notes_input');
  const envsInput = document.getElementById('clip_envelopes_input');
  const regionInput = document.getElementById('region_end_input');
  const loopStartInput = document.getElementById('loop_start_input');
  const loopEndInput = document.getElementById('loop_end_input');

  let editing = false;
  let drawing = false;
  let dirty = false;
  let currentEnv = [];
  let tailEnv = [];
  let envInfo = null;
  let lastPid = envSelect && envSelect.value ? parseInt(envSelect.value) : null;
  let clipModified = false;

  function updateSaveButton() {
    if (saveClipBtn) saveClipBtn.disabled = !clipModified;
  }

  if (saveClipBtn) saveClipBtn.disabled = true;

  function updatePitchIcons() {
    if (!piano) return;
    const kb = piano.querySelector('#wac-kb');
    const openForm = document.getElementById('openPitchForm');
    const noteInput = document.getElementById('pitch_note_input');
    if (!kb || !openForm || !noteInput) return;
    kb.querySelectorAll('.pitch-icon').forEach(el => el.remove());
    if (!pitchNotes.length) return;
    const h = parseInt(piano.getAttribute('height') || '300', 10);
    const steph = (h - piano.xruler) / piano.yrange;
    pitchNotes.forEach(n => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pitch-icon';
      btn.textContent = '\u266A';
      const y = h - (n - piano.yoffset + 0.5) * steph;
      btn.style.top = `${y - 6}px`;
      btn.style.left = '2px';
      btn.addEventListener('click', () => {
        noteInput.value = n;
        openForm.submit();
      });
      kb.appendChild(btn);
    });
  }

  if (piano) {
    if (!piano.sequence) piano.sequence = [];
    piano.sequence = notes.map(n => ({
      t: Math.round(n.startTime * ticksPerBeat),
      n: n.noteNumber,
      g: Math.max(1, Math.round(n.duration * ticksPerBeat))
    }));
    if (!piano.hasAttribute('xrange')) piano.xrange = region * ticksPerBeat;
    if (!piano.hasAttribute('markstart')) piano.markstart = loopStart * ticksPerBeat;
    if (!piano.hasAttribute('markend')) piano.markend = loopEnd * ticksPerBeat;
    piano.showcursor = false;
    const { min, max } = notes.length
      ? { min: Math.min(...notes.map(n => n.noteNumber)),
          max: Math.max(...notes.map(n => n.noteNumber)) }
      : { min: 60, max: 71 };
    piano.yoffset = Math.max(0, min - 2);
    piano.yrange = Math.max(12, max - min + 5);
    if (piano.redraw) piano.redraw();

    // Add pitch bend icons to keyboard
    const kb = piano.querySelector('#wac-kb');
    const openForm = document.getElementById('openPitchForm');
    const noteInput = document.getElementById('pitch_note_input');

    updatePitchIcons();

    piano.addEventListener('dblclick', ev => {
      const rect = piano.getBoundingClientRect();
      const x = ev.clientX - rect.left;
      const y = ev.clientY - rect.top;
      if (y < piano.xruler) {
        piano.xoffset = 0;
        piano.xrange = region * ticksPerBeat;
        if (piano.redraw) piano.redraw();
        return;
      }
      if (x < piano.yruler + piano.kbwidth) {
        const { min, max } = notes.length
          ? { min: Math.min(...notes.map(n => n.noteNumber)),
              max: Math.max(...notes.map(n => n.noteNumber)) }
          : { min: 60, max: 71 };
        piano.yoffset = Math.max(0, min - 2);
        piano.yrange = Math.max(12, max - min + 5);
        if (piano.redraw) piano.redraw();
      }
    });
  }

  function isNormalized(env) {
    if (!env || !env.breakpoints || !env.breakpoints.length) return false;
    const vals = env.breakpoints.map(b => b.value);
    const minV = Math.min(...vals);
    const maxV = Math.max(...vals);
    return minV >= 0 && maxV <= 1 && (env.rangeMin !== 0 || env.rangeMax !== 1);
  }

  const defaultEditMode = piano ? (piano.editmode || piano.getAttribute('editmode') || 'dragpoly') : 'dragpoly';

  function updateControls() {
    if (canvas) {
      canvas.style.pointerEvents = editing ? 'auto' : 'none';
    }
    if (piano) {
      piano.enable = true;
      piano.editmode = editing ? '' : defaultEditMode;
    }
  }
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
    let env;
    if (editing) {
      let bps = drawing ? currentEnv.concat(tailEnv) : currentEnv;
      if (!bps.length && envInfo) {
        bps = envInfo.breakpoints;
      }
      env = envInfo ? { ...envInfo, breakpoints: bps } : { breakpoints: bps };
    } else {
      env = envInfo;
    }
    if (!env || !env.breakpoints || !env.breakpoints.length) return;
    ctx.strokeStyle = '#FF4136';
    ctx.beginPath();
    const needsScale = isNormalized(env);
    env.breakpoints.forEach((bp, i) => {
      const x = piano
        ? ((bp.time * ticksPerBeat - piano.xoffset) / piano.xrange) * canvas.width
        : (bp.time / region) * canvas.width;
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
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawEnvelope();
  }

  if (piano && piano.redraw) {
    const origRedraw = piano.redraw.bind(piano);
    piano.redraw = function(...args) {
      origRedraw(...args);
      draw();
      if (typeof updatePitchIcons === 'function') updatePitchIcons();
    };
  }

  if (envSelect) envSelect.addEventListener('change', () => {
    if (lastPid !== null) {
      let bps = currentEnv;
      if (!bps.length && envInfo) bps = envInfo.breakpoints;
      const idx = envelopes.findIndex(e => e.parameterId === lastPid);
      const newEnv = { parameterId: lastPid, breakpoints: bps };
      if (idx >= 0) envelopes[idx] = { ...envelopes[idx], breakpoints: bps };
      else envelopes.push(newEnv);
      if (dirty || currentEnv.length) {
        clipModified = true;
        updateSaveButton();
      }
    }
    drawing = false;
    dirty = false;
    currentEnv = [];
    envInfo = null;
    editing = !!envSelect.value;
    lastPid = envSelect.value ? parseInt(envSelect.value) : null;
    if (editing) {
      const pid = lastPid;
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
    updateLegend();
    updateControls();
    draw();
  });

  if (piano) {
    piano.addEventListener('mouseup', () => { clipModified = true; updateSaveButton(); });
    piano.addEventListener('touchend', () => { clipModified = true; updateSaveButton(); });
  }

  function canvasPos(ev) {
    const rect = canvas.getBoundingClientRect();
    const x = (ev.touches ? ev.touches[0].clientX : ev.clientX) - rect.left;
    const y = (ev.touches ? ev.touches[0].clientY : ev.clientY) - rect.top;
    return { x, y };
  }

  function showValue(ev) {
    if (!envSelect || !envSelect.value || !valueDiv) return;
    const param = parseInt(envSelect.value);
    let env;
    if (editing) {
      let bps = currentEnv;
      if (!bps.length && envInfo) {
        bps = envInfo.breakpoints;
      }
      env = envInfo ? { ...envInfo, breakpoints: bps } : { breakpoints: bps };
    } else {
      env = envInfo;
    }
    if (!env || !env.breakpoints || !env.breakpoints.length) { valueDiv.textContent = ''; return; }
    const pos = canvasPos(ev);
    const t = piano ? (piano.xoffset + (pos.x / canvas.width) * piano.xrange) / ticksPerBeat
                    : (pos.x / canvas.width) * region;
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
    clipModified = true;
    updateSaveButton();
    const { x, y } = canvasPos(ev);
    const t = piano ? (piano.xoffset + (x / canvas.width) * piano.xrange) / ticksPerBeat
                    : (x / canvas.width) * region;
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
    const t = piano ? (piano.xoffset + (x / canvas.width) * piano.xrange) / ticksPerBeat
                    : (x / canvas.width) * region;
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


  if (saveClipForm) saveClipForm.addEventListener('submit', () => {
    if (piano && notesInput) {
      const seq = piano.sequence || [];
      notesInput.value = JSON.stringify(seq.map(ev => ({
        noteNumber: ev.n,
        startTime: ev.t / ticksPerBeat,
        duration: ev.g / ticksPerBeat,
        velocity: 100.0,
        offVelocity: 0.0
      })));
    }
    if (envsInput) {
      let envs = envelopes.map(e => ({ parameterId: e.parameterId, breakpoints: e.breakpoints }));
      if (editing && envSelect && envSelect.value) {
        const pid = parseInt(envSelect.value);
        let bps = currentEnv;
        if (!bps.length && envInfo) {
          bps = envInfo.breakpoints;
        }
        const newEnv = { parameterId: pid, breakpoints: bps };
        const idx = envs.findIndex(e => e.parameterId === pid);
        if (idx >= 0) envs[idx] = newEnv; else envs.push(newEnv);
      }
      envsInput.value = JSON.stringify(envs);
    }
    if (regionInput) regionInput.value = (piano.xrange / ticksPerBeat).toFixed(6);
    if (loopStartInput) loopStartInput.value = (piano.markstart / ticksPerBeat).toFixed(6);
    if (loopEndInput) loopEndInput.value = (piano.markend / ticksPerBeat).toFixed(6);
    clipModified = false;
    updateSaveButton();
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
