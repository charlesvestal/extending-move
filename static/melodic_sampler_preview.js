// Load and play the current melodic sampler sample

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('sample-waveform');
  const hidden = document.getElementById('sample-path-hidden');
  if (!container || !hidden || !hidden.value) return;

  const overlay = document.getElementById('adsr-overlay');
  const attack = document.querySelector(
    '.param-item[data-name="Voice_AmplitudeEnvelope_Attack"] input[type="range"]'
  );
  const decay = document.querySelector(
    '.param-item[data-name="Voice_AmplitudeEnvelope_Decay"] input[type="range"]'
  );
  const sustain = document.querySelector(
    '.param-item[data-name="Voice_AmplitudeEnvelope_Sustain"] input[type="range"]'
  );
  const release = document.querySelector(
    '.param-item[data-name="Voice_AmplitudeEnvelope_Release"] input[type="range"]'
  );

  function drawEnvelope() {
    if (!overlay) return;
    const ctx = overlay.getContext('2d');
    const a = parseFloat(attack?.value || '0');
    const d = parseFloat(decay?.value || '0');
    const s = parseFloat(sustain?.value || '0');
    const r = parseFloat(release?.value || '0');
    const i = 0;
    const p = 1;
    const f = 0;
    const hold = 0.25;
    const total = a + d + r + hold;
    const w = overlay.width;
    const h = overlay.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    ctx.moveTo(0, h);
    let x = (a / total) * w;
    ctx.lineTo(x, h - p * h);
    const decEnd = x + (d / total) * w;
    ctx.lineTo(decEnd, h - s * h);
    const relStart = w - (r / total) * w;
    ctx.lineTo(relStart, h - s * h);
    ctx.lineTo(w, h - f * h);
    ctx.strokeStyle = '#f00';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  function resizeOverlay() {
    if (!overlay) return;
    overlay.width = container.clientWidth;
    overlay.height = container.clientHeight;
    drawEnvelope();
  }

  function toFilesUrl(path) {
    // Convert a sample URI or absolute path to the /files route.
    if (path.startsWith('ableton:/user-library/')) {
      const rel = path.replace('ableton:/user-library/', 'user-library/');
      return '/files/' + encodeURI(rel);
    }
    const packMatch = path.match(/^ableton:\/packs\/[^/]+\/(.+)$/);
    if (packMatch) {
      return '/files/core-library/' + encodeURI(packMatch[1]);
    }
    if (path.startsWith('/data/UserData/UserLibrary/')) {
      const rel = path.replace('/data/UserData/UserLibrary/', 'user-library/');
      return '/files/' + encodeURI(rel);
    }
    if (path.startsWith('/data/CoreLibrary/')) {
      const rel = path.replace('/data/CoreLibrary/', 'core-library/');
      return '/files/' + encodeURI(rel);
    }
    return null;
  }

  const fileUrl = toFilesUrl(hidden.value.trim());
  if (!fileUrl) return;

  const ws = WaveSurfer.create({
    container: container,
    waveColor: '#888',
    progressColor: '#555',
    height: 64,
    responsive: true,
    normalize: true,
    cursorWidth: 0,
    hideScrollbar: true
  });

  ws.load(fileUrl);
  container.addEventListener('click', (e) => {
    e.stopPropagation();
    ws.stop();
    ws.seekTo(0);
    requestAnimationFrame(() => ws.play(0));
  });

  ws.on('ready', resizeOverlay);
  window.addEventListener('resize', resizeOverlay);
  [attack, decay, sustain, release].forEach(el => {
    if (el) el.addEventListener('input', drawEnvelope);
  });
  resizeOverlay();
});
