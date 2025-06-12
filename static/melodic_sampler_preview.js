// Load and play the current melodic sampler sample

document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('sample-waveform');
  const hidden = document.getElementById('sample-path-hidden');
  if (!container || !hidden || !hidden.value) return;

  const utils = await import('/static/loop_utils.js');

  const overlay = document.getElementById('adsr-overlay');
  const filterOverlay = document.getElementById('filter-adsr-overlay');
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
  const pbStart = document.querySelector(
    '.param-item[data-name="Voice_PlaybackStart"] input[type="range"]'
  );
  const pbLength = document.querySelector(
    '.param-item[data-name="Voice_PlaybackLength"] input[type="range"]'
  );
  const fOn = document.querySelector(
    '.param-item[data-name="Voice_FilterEnvelope_On"] input[type="checkbox"]'
  );
  const fAttack = document.querySelector(
    '.param-item[data-name="Voice_FilterEnvelope_Attack"] input[type="range"]'
  );
  const fDecay = document.querySelector(
    '.param-item[data-name="Voice_FilterEnvelope_Decay"] input[type="range"]'
  );
  const fSustain = document.querySelector(
    '.param-item[data-name="Voice_FilterEnvelope_Sustain"] input[type="range"]'
  );
  const fRelease = document.querySelector(
    '.param-item[data-name="Voice_FilterEnvelope_Release"] input[type="range"]'
  );

  let duration = 0;
  let region = null;

  function drawEnvelope() {
    if (!overlay || !duration) return;
    const ctx = overlay.getContext('2d');
    const a = parseFloat(attack?.value || '0');
    const d = parseFloat(decay?.value || '0');
    const s = parseFloat(sustain?.value || '0');
    const r = parseFloat(release?.value || '0');

    const startPct = parseFloat(pbStart?.value || '0');
    const lengthPct = parseFloat(pbLength?.value || '1');
    const start = Math.max(0, Math.min(1, startPct)) * duration;
    const end = Math.min(duration, start + Math.max(0, Math.min(1, lengthPct)) * duration);
    const playDur = Math.max(0, end - start);

    const aT = Math.min(a, playDur);
    const dT = Math.min(d, Math.max(0, playDur - aT));
    const rT = Math.min(r, Math.max(0, playDur - aT - dT));
    const total = playDur || 1;

    const w = overlay.width;
    const h = overlay.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    const startX = (start / duration) * w;
    const regionWidth = (playDur / duration) * w;
    ctx.moveTo(startX, h);
    const attackEnd = startX + (aT / total) * regionWidth;
    ctx.lineTo(attackEnd, 0);
    const decayEnd = attackEnd + (dT / total) * regionWidth;
    ctx.lineTo(decayEnd, h - s * h);
    const releaseStart = startX + regionWidth - (rT / total) * regionWidth;
    ctx.lineTo(releaseStart, h - s * h);
    ctx.lineTo(startX + regionWidth, h);
    ctx.strokeStyle = '#f00';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  function drawFilterEnvelope() {
    if (!filterOverlay || !duration) return;
    if (fOn && !fOn.checked) {
      filterOverlay.getContext('2d').clearRect(0, 0, filterOverlay.width, filterOverlay.height);
      filterOverlay.style.display = 'none';
      return;
    }
    filterOverlay.style.display = '';
    const ctx = filterOverlay.getContext('2d');
    const a = parseFloat(fAttack?.value || '0');
    const d = parseFloat(fDecay?.value || '0');
    let s = parseFloat(fSustain?.value || '0');
    const sMax = parseFloat(fSustain?.max || '1');
    if (sMax > 1) s /= sMax; // convert percent to 0..1 range based on max
    const r = parseFloat(fRelease?.value || '0');

    const startPct = parseFloat(pbStart?.value || '0');
    const lengthPct = parseFloat(pbLength?.value || '1');
    const start = Math.max(0, Math.min(1, startPct)) * duration;
    const end = Math.min(duration, start + Math.max(0, Math.min(1, lengthPct)) * duration);
    const playDur = Math.max(0, end - start);

    const aT = Math.min(a, playDur);
    const dT = Math.min(d, Math.max(0, playDur - aT));
    const rT = Math.min(r, Math.max(0, playDur - aT - dT));
    const total = playDur || 1;

    const w = filterOverlay.width;
    const h = filterOverlay.height;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    const startX = (start / duration) * w;
    const regionWidth = (playDur / duration) * w;
    ctx.moveTo(startX, h);
    const attackEnd = startX + (aT / total) * regionWidth;
    ctx.lineTo(attackEnd, 0);
    const decayEnd = attackEnd + (dT / total) * regionWidth;
    ctx.lineTo(decayEnd, h - s * h);
    const releaseStart = startX + regionWidth - (rT / total) * regionWidth;
    ctx.lineTo(releaseStart, h - s * h);
    ctx.lineTo(startX + regionWidth, h);
    ctx.strokeStyle = 'rgba(0, 136, 255, 0.5)';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  function updateRegion() {
    if (!ws || !duration) return;
    const startPct = parseFloat(pbStart?.value || '0');
    const lengthPct = parseFloat(pbLength?.value || '1');
    const start = Math.max(0, Math.min(1, startPct)) * duration;
    const end = Math.min(duration, start + Math.max(0, Math.min(1, lengthPct)) * duration);
    if (region) {
      region.update({ start, end });
    } else if (ws.regions) {
      region = ws.addRegion({ start, end, color: 'rgba(0,255,0,0.2)', drag: false, resize: false });
    }
    drawEnvelope();
    drawFilterEnvelope();
  }

  function resizeOverlay() {
    if (!overlay) return;
    const cs = getComputedStyle(container);
    const padL = parseFloat(cs.paddingLeft) || 0;
    const padR = parseFloat(cs.paddingRight) || 0;
    const padT = parseFloat(cs.paddingTop) || 0;
    const padB = parseFloat(cs.paddingBottom) || 0;
    const innerW = container.clientWidth - padL - padR;
    const innerH = container.clientHeight - padT - padB;
    overlay.width = innerW;
    overlay.height = innerH;
    overlay.style.left = padL + 'px';
    overlay.style.top = padT + 'px';
    overlay.style.width = innerW + 'px';
    overlay.style.height = innerH + 'px';
    if (filterOverlay) {
      filterOverlay.width = innerW;
      filterOverlay.height = innerH;
      filterOverlay.style.left = padL + 'px';
      filterOverlay.style.top = padT + 'px';
      filterOverlay.style.width = innerW + 'px';
      filterOverlay.style.height = innerH + 'px';
    }
    drawEnvelope();
    drawFilterEnvelope();
    updateRegion();
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

  let ws = WaveSurfer.create({
    container: container,
    waveColor: '#888',
    progressColor: '#555',
    height: 64,
    responsive: true,
    normalize: true,
    cursorWidth: 0,
    hideScrollbar: true,
    plugins: [WaveSurfer.regions.create({})]
  });

  const audioCtx = ws.backend.getAudioContext();
  const arr = await fetch(fileUrl).then(r => r.arrayBuffer());
  const decoded = await audioCtx.decodeAudioData(arr.slice(0));
  ws.loadDecodedBuffer(decoded);
  try {
    const { loopStart, loopEnd } = await utils.parseLoopPoints(arr.slice(0));
    const startSec = loopStart / decoded.sampleRate;
    const endSec = loopEnd / decoded.sampleRate;
    ws.clearRegions();
    region = ws.addRegion({ start: startSec, end: endSec, color: 'rgba(0,255,0,0.2)', drag: false, resize: false });
    if (duration === 0) duration = decoded.duration;
    if (pbStart) pbStart.value = (startSec / duration).toFixed(4);
    if (pbLength) pbLength.value = ((endSec - startSec) / duration).toFixed(4);
    updateRegion();
  } catch (e) {
    console.log('loop parse', e);
  }
  container.addEventListener('click', (e) => {
    e.stopPropagation();
    ws.stop();
    const start = region ? region.start : 0;
    const end = region ? region.end : undefined;
    ws.seekTo(start / duration);
    requestAnimationFrame(() => ws.play(start, end));
  });

  ws.on('ready', () => {
    duration = ws.getDuration();
    resizeOverlay();
    updateRegion();
  });
  window.addEventListener('resize', resizeOverlay);
  [attack, decay, sustain, release].forEach(el => {
    if (el) el.addEventListener('input', () => {
      drawEnvelope();
      drawFilterEnvelope();
    });
  });
  [fAttack, fDecay, fSustain, fRelease, fOn].forEach(el => {
    if (el) el.addEventListener('input', drawFilterEnvelope);
    if (el && el.type === 'checkbox') el.addEventListener('change', drawFilterEnvelope);
  });
  [pbStart, pbLength].forEach(el => {
    if (el) el.addEventListener('input', updateRegion);
  });
  resizeOverlay();
});
