export function initPitchViewer() {
  const dataDiv = document.getElementById('pitchData');
  const piano = document.getElementById('pitchRoll');
  if (!dataDiv || !piano) return;
  const segs = JSON.parse(dataDiv.dataset.segments || '[]');
  const tpq = parseInt(piano.getAttribute('timebase') || '16', 10) / 4;
  piano.sequence = segs.map(s => ({
    t: Math.round(s.startTime * tpq),
    n: s.noteNumber,
    g: Math.round(s.duration * tpq)
  }));
  const end = segs.reduce((m, s) => Math.max(m, s.startTime + s.duration), 4);
  piano.xrange = end * tpq;
  piano.yoffset = 24;
  piano.yrange = 48;
  if (piano.redraw) piano.redraw();
}

document.addEventListener('DOMContentLoaded', initPitchViewer);
