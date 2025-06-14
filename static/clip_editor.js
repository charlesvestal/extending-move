function snap(val, res) {
  return Math.round(val / res) * res;
}

function isInNote(x, y, note) {
  return (
    x >= note.start &&
    x <= note.start + note.duration &&
    y >= note.pitch - 0.5 &&
    y <= note.pitch + 0.5
  );
}

export function initClipEditor() {
  const dataDiv = document.getElementById('clipData');
  const notes = JSON.parse(dataDiv.dataset.notes || '[]');
  const region = parseFloat(dataDiv.dataset.region || '4');

  const gridCanvas = document.getElementById('grid');
  const rulerCanvas = document.getElementById('ruler');
  const pianoCanvas = document.getElementById('piano');
  const velCanvas = document.getElementById('velocity');

  const gCtx = gridCanvas.getContext('2d');
  const rCtx = rulerCanvas.getContext('2d');
  const pCtx = pianoCanvas.getContext('2d');
  const vCtx = velCanvas.getContext('2d');

  const state = {
    notes,
    selection: new Set(),
    playhead: 0,
    grid: { resolution: 0.25, snap: true },
    zoom: { x: 1, y: 1 },
    scroll: { x: 0, y: 0 },
  };

  const noteHeight = gridCanvas.height / 12;

  function drawBackground() {
    gCtx.clearRect(0, 0, gridCanvas.width, gridCanvas.height);
    for (let b = 0; b <= region; b += state.grid.resolution) {
      const x = (b / region) * gridCanvas.width;
      gCtx.strokeStyle = b % 1 === 0 ? '#999' : '#ddd';
      gCtx.beginPath();
      gCtx.moveTo(x, 0);
      gCtx.lineTo(x, gridCanvas.height);
      gCtx.stroke();
    }
    for (let p = 0; p < 128; p++) {
      const y = gridCanvas.height - (p + 1) * noteHeight;
      gCtx.strokeStyle = p % 12 === 0 ? '#ccc' : '#eee';
      gCtx.beginPath();
      gCtx.moveTo(0, y);
      gCtx.lineTo(gridCanvas.width, y);
      gCtx.stroke();
    }
  }

  function drawNotes() {
    gCtx.fillStyle = '#0074D9';
    state.notes.forEach(n => {
      const x = (n.start / region) * gridCanvas.width;
      const w = (n.duration / region) * gridCanvas.width;
      const y = gridCanvas.height - (n.pitch + 1) * noteHeight;
      gCtx.fillRect(x, y, w, noteHeight);
      if (state.selection.has(n.id)) {
        gCtx.strokeStyle = '#FF4136';
        gCtx.strokeRect(x, y, w, noteHeight);
      }
    });
  }

  function drawVelocity() {
    vCtx.clearRect(0, 0, velCanvas.width, velCanvas.height);
    state.notes.forEach(n => {
      const x = (n.start / region) * velCanvas.width;
      const w = (n.duration / region) * velCanvas.width;
      const h = (n.velocity / 127) * velCanvas.height;
      vCtx.fillStyle = state.selection.has(n.id) ? '#FF4136' : '#888';
      vCtx.fillRect(x, velCanvas.height - h, w, h);
    });
  }

  function drawRuler() {
    rCtx.clearRect(0, 0, rulerCanvas.width, rulerCanvas.height);
    rCtx.fillStyle = '#000';
    for (let b = 0; b <= region; b++) {
      const x = (b / region) * rulerCanvas.width;
      rCtx.fillText(b.toString(), x + 2, 10);
    }
    rCtx.strokeStyle = '#FF4136';
    const x = (state.playhead / region) * rulerCanvas.width;
    rCtx.beginPath();
    rCtx.moveTo(x, 0);
    rCtx.lineTo(x, rulerCanvas.height);
    rCtx.stroke();
  }

  function drawPiano() {
    pCtx.clearRect(0, 0, pianoCanvas.width, pianoCanvas.height);
    for (let p = 0; p < 128; p++) {
      const y = pianoCanvas.height - (p + 1) * noteHeight;
      pCtx.fillStyle = p % 12 === 0 ? '#bbb' : '#eee';
      pCtx.fillRect(0, y, pianoCanvas.width, noteHeight);
      if (p % 12 === 0) {
        const octave = Math.floor(p / 12) - 1;
        pCtx.fillStyle = '#000';
        pCtx.fillText('C' + octave, 2, y + noteHeight - 2);
      }
    }
  }

  function draw() {
    drawBackground();
    drawNotes();
    drawVelocity();
    drawRuler();
    drawPiano();
  }

  let currentNote = null;
  function canvasPos(ev) {
    const rect = gridCanvas.getBoundingClientRect();
    return {
      x: ev.clientX - rect.left,
      y: ev.clientY - rect.top,
    };
  }

  gridCanvas.addEventListener('mousedown', ev => {
    const pos = canvasPos(ev);
    const time = (pos.x / gridCanvas.width) * region;
    const pitch = 127 - Math.floor(pos.y / noteHeight);
    currentNote = {
      id: Date.now(),
      pitch,
      start: snap(time, state.grid.resolution),
      duration: state.grid.resolution,
      velocity: 100,
    };
    state.notes.push(currentNote);
    state.selection = new Set([currentNote.id]);
    draw();
  });

  gridCanvas.addEventListener('mousemove', ev => {
    if (!currentNote) return;
    const pos = canvasPos(ev);
    const time = (pos.x / gridCanvas.width) * region;
    const dur = snap(time, state.grid.resolution) - currentNote.start;
    currentNote.duration = Math.max(state.grid.resolution, dur);
    draw();
  });

  document.addEventListener('mouseup', () => {
    currentNote = null;
  });

  rulerCanvas.addEventListener('mousedown', ev => {
    const rect = rulerCanvas.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    state.playhead = (x / rulerCanvas.width) * region;
    drawRuler();
  });

  draw();
}

document.addEventListener('DOMContentLoaded', initClipEditor);
