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
  let baseNotes = JSON.parse(dataDiv.dataset.notes || '[]');
  const envelopes = JSON.parse(dataDiv.dataset.envelopes || '[]');
  const region = parseFloat(dataDiv.dataset.region || '4');
  const loopStart = parseFloat(dataDiv.dataset.loopStart || '0');
  const loopEnd = parseFloat(dataDiv.dataset.loopEnd || String(region));
  const paramRanges = JSON.parse(dataDiv.dataset.paramRanges || '{}');
  const pitchPads = JSON.parse(dataDiv.dataset.pitchpads || '[]');
  const canvas = document.getElementById('clipCanvas');
  const ctx = canvas.getContext('2d');
  const velCanvas = document.getElementById('velocityCanvas');
  const vctx = velCanvas ? velCanvas.getContext('2d') : null;
  const piano = document.getElementById('clipEditor');
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
    if (velCanvas && vctx) {
      velCanvas.width = canvas.width;
      velCanvas.style.left = `${yruler + kbwidth}px`;
      velCanvas.style.top = `${h}px`;
    }
  }
  const envSelect = document.getElementById('envelope_select');
  const pitchPadSelect = document.getElementById('pitch_pad_select');
  const legendDiv = document.getElementById('paramLegend');
  const valueDiv = document.getElementById('envValue');
  const saveClipForm = document.getElementById('saveClipForm');
  const notesInput = document.getElementById('clip_notes_input');
  const envsInput = document.getElementById('clip_envelopes_input');
  const regionInput = document.getElementById('region_end_input');
  const loopStartInput = document.getElementById('loop_start_input');
  const loopEndInput = document.getElementById('loop_end_input');
  if (pitchPadSelect && pitchPads.length === 0) {
    pitchPadSelect.disabled = true;
  }

  let editing = false;
  let drawing = false;
  let dirty = false;
  let currentEnv = [];
  let tailEnv = [];
  let envInfo = null;
  let pitchMode = false;
  let activePad = null;

  function loadNormalSequence() {
    piano.sequence = baseNotes.map(n => ({
      t: Math.round(n.startTime * ticksPerBeat),
      n: n.noteNumber,
      g: Math.round(n.duration * ticksPerBeat),
      v: Math.round(n.velocity || 100),
      pb: n.pitchBend || 0
    }));
  }

  function loadPitchSequence(pad) {
    const padNotes = baseNotes.filter(n => n.noteNumber === pad);
    piano.sequence = padNotes.map(n => ({
      t: Math.round(n.startTime * ticksPerBeat),
      n: Math.round(36 + (n.pitchBend || 0) / 170.6458282470703),
      g: Math.round(n.duration * ticksPerBeat),
      v: Math.round(n.velocity || 100),
      pb: n.pitchBend || 0
    }));
  }

  function updateRange() {
    const seq = piano.sequence || [];
    const { min, max } = seq.length
      ? { min: Math.min(...seq.map(ev => ev.n)),
          max: Math.max(...seq.map(ev => ev.n)) }
      : { min: 60, max: 71 };
    piano.yoffset = Math.max(0, min - 2);
    piano.yrange = Math.max(12, max - min + 5);
  }

  function refreshPiano() {
    if (pitchMode && activePad !== null) {
      loadPitchSequence(activePad);
      piano.colnote = '#0074D9';
      piano.colnotesel = '#00A1FF';
      piano.colnoteselinactive = '#0074D9';
    } else {
      loadNormalSequence();
      piano.colnote = '#f22';
      piano.colnotesel = '#0f0';
      piano.colnoteselinactive = '#0b0';
    }
    updateRange();
    if (piano.redraw) piano.redraw();
  }

  if (piano) {
    if (!piano.sequence) piano.sequence = [];
    refreshPiano();
    if (!piano.hasAttribute('xrange')) piano.xrange = region * ticksPerBeat;
    if (!piano.hasAttribute('markstart')) piano.markstart = loopStart * ticksPerBeat;
    if (!piano.hasAttribute('markend')) piano.markend = loopEnd * ticksPerBeat;
    piano.showcursor = false;

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
        const src = pitchMode && activePad !== null
          ? baseNotes.filter(n => n.noteNumber === activePad)
          : baseNotes;
        const { min, max } = src.length
          ? { min: Math.min(...src.map(n => n.noteNumber)),
              max: Math.max(...src.map(n => n.noteNumber)) }
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

  let defaultEditMode = piano ? (piano.editmode || piano.getAttribute('editmode') || 'dragpoly') : 'dragpoly';
  const drawToggle = document.getElementById('note_draw_toggle');
  if (drawToggle) {
    drawToggle.checked = defaultEditMode.startsWith('draw');
    drawToggle.addEventListener('change', () => {
      defaultEditMode = drawToggle.checked ? 'drawpoly' : 'dragpoly';
      updateControls();
    });
  }

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
    const seq = piano.sequence || [];
    if (!seq.length) return { min: 60, max: 71 };
    let min = Math.min(...seq.map(ev => ev.n));
    let max = Math.max(...seq.map(ev => ev.n));
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
    ctx.fillStyle = piano.colnote;
    (piano.sequence || []).forEach(ev => {
      const x = (ev.t / ticksPerBeat / region) * canvas.width;
      const w = (ev.g / ticksPerBeat / region) * canvas.width;
      const y = canvas.height - (ev.n - min + 1) * h;
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

  function drawVelocity() {
    if (!velCanvas || !vctx || !piano) return;
    vctx.clearRect(0, 0, velCanvas.width, velCanvas.height);
    const seq = piano.sequence || [];
    const barWidth = Math.max(2,
      (piano.grid || piano.snap) * (velCanvas.width / piano.xrange) * 0.8);

    const drawBar = ev => {
      const x = ((ev.t - piano.xoffset) / piano.xrange) * velCanvas.width;
      const h = ((ev.v || 100) / 127) * velCanvas.height;
      vctx.fillStyle = ev.f
        ? (piano.hasFocus ? piano.colnotesel : piano.colnoteselinactive)
        : piano.colnote;
      vctx.fillRect(x, velCanvas.height - h, barWidth, h);
    };

    seq.filter(ev => !ev.f).forEach(drawBar);
    seq.filter(ev => ev.f).forEach(drawBar);
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
    drawVelocity();
  }

  if (piano && piano.redraw) {
    const origRedraw = piano.redraw.bind(piano);
    piano.redraw = function(...args) {
      origRedraw(...args);
      draw();
    };
  }

  if (envSelect) envSelect.addEventListener('change', () => {
    drawing = false;
    dirty = false;
    currentEnv = [];
    envInfo = null;
    editing = !!envSelect.value;
    if (editing) {
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
    }
    updateLegend();
    updateControls();
    draw();
  });

  if (pitchPadSelect) pitchPadSelect.addEventListener('change', () => {
    syncBaseFromSequence();
    if (pitchPadSelect.value) {
      pitchMode = true;
      activePad = parseInt(pitchPadSelect.value);
    } else {
      pitchMode = false;
      activePad = null;
    }
    refreshPiano();
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

  let velDragging = false;
  function velPos(ev) {
    const rect = velCanvas.getBoundingClientRect();
    const x = (ev.touches ? ev.touches[0].clientX : ev.clientX) - rect.left;
    const y = (ev.touches ? ev.touches[0].clientY : ev.clientY) - rect.top;
    return { x, y };
  }
  function notesAtX(x) {
    const seq = piano.sequence || [];
    const barWidth = Math.max(2,
      (piano.grid || piano.snap) * (velCanvas.width / piano.xrange) * 0.8);
    const list = [];
    for (let i = 0; i < seq.length; i++) {
      const ex = ((seq[i].t - piano.xoffset) / piano.xrange) * velCanvas.width;
      if (x >= ex && x <= ex + barWidth) list.push(i);
    }
    return list;
  }
  function updateVel(ev) {
    if (!velDragging) return;
    const { x, y } = velPos(ev);
    const indices = notesAtX(x);
    if (!indices.length) return;
    const v = Math.max(1,
      Math.min(127, Math.round(127 - (y / velCanvas.height) * 127)));
    const anySel = piano.sequence.some(ev => ev.f);
    const selected = indices.filter(i => piano.sequence[i].f);
    const targets = anySel && selected.length ? selected : indices;
    targets.forEach(i => { piano.sequence[i].v = v; });
    drawVelocity();
    ev.preventDefault();
  }
  function startVel(ev) {
    velDragging = true;
    updateVel(ev);
  }
  function endVel() {
    velDragging = false;
  }

  canvas.addEventListener('mousedown', startDraw);
  canvas.addEventListener('touchstart', startDraw);
  canvas.addEventListener('mousemove', continueDraw);
  canvas.addEventListener('touchmove', continueDraw);
  canvas.addEventListener('mouseleave', () => { if (!drawing && valueDiv) valueDiv.textContent = ''; });
  document.addEventListener('mouseup', endDraw);
  document.addEventListener('touchend', endDraw);

  if (velCanvas) {
    velCanvas.addEventListener('mousedown', startVel);
    velCanvas.addEventListener('touchstart', startVel);
    velCanvas.addEventListener('mousemove', updateVel);
    velCanvas.addEventListener('touchmove', updateVel);
    document.addEventListener('mouseup', endVel);
    document.addEventListener('touchend', endVel);
  }

  function syncBaseFromSequence() {
    const seq = piano.sequence || [];
    if (pitchMode && activePad !== null) {
      const others = baseNotes.filter(n => n.noteNumber !== activePad);
      const newPad = seq.map(ev => ({
        noteNumber: activePad,
        startTime: ev.t / ticksPerBeat,
        duration: ev.g / ticksPerBeat,
        velocity: ev.v ?? 100.0,
        offVelocity: 0.0,
        pitchBend: (ev.n - 36) * 170.6458282470703
      }));
      baseNotes = others.concat(newPad);
    } else {
      baseNotes = seq.map(ev => ({
        noteNumber: ev.n,
        startTime: ev.t / ticksPerBeat,
        duration: ev.g / ticksPerBeat,
        velocity: ev.v ?? 100.0,
        offVelocity: 0.0,
        pitchBend: ev.pb || 0
      }));
    }
  }


  if (saveClipForm) saveClipForm.addEventListener('submit', () => {
    if (piano && notesInput) {
      syncBaseFromSequence();
      notesInput.value = JSON.stringify(baseNotes);
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
