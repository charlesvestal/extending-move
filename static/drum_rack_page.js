let drumRackWaveforms = [];
function initializeDrumRackWaveforms() {
  drumRackWaveforms.forEach(ws => { try { ws.destroy(); } catch (e) {} });
  drumRackWaveforms = [];
  const containers = document.querySelectorAll('.waveform-container');
  containers.forEach(container => {
    const startPct = parseFloat(container.dataset.playbackStart) || 0;
    const lengthPct = parseFloat(container.dataset.playbackLength) || 1;
    const audioPath = container.dataset.audioPath;
    if (!audioPath) return;
    const ws = WaveSurfer.create({
      container: container,
      waveColor: 'violet',
      progressColor: 'purple',
      height: 64,
      responsive: true,
      normalize: true,
      minPxPerSec: 50,
      barWidth: 2,
      interact: false,
      hideScrollbar: true
    });
    container.wavesurfer = ws;
    drumRackWaveforms.push(ws);
    const ctx = ws.backend.getAudioContext();
    fetch(audioPath)
      .then(r => r.arrayBuffer())
      .then(d => ctx.decodeAudioData(d))
      .then(buffer => {
        const dur = buffer.duration;
        const sr = buffer.sampleRate;
        const start = Math.floor(startPct * dur * sr);
        const count = Math.floor(lengthPct * dur * sr);
        const sliced = ctx.createBuffer(buffer.numberOfChannels, count, sr);
        for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
          sliced.copyToChannel(buffer.getChannelData(ch).subarray(start, start + count), ch, 0);
        }
        ws.loadDecodedBuffer(sliced);
      });
    ws.on('finish', () => ws.stop());
    container.addEventListener('click', e => {
      e.stopPropagation();
      drumRackWaveforms.forEach(other => { if (other.isPlaying()) { other.stop(); } });
      ws.stop();
      ws.seekTo(0);
      requestAnimationFrame(() => ws.play(0));
    });
  });
}
document.addEventListener('DOMContentLoaded', initializeDrumRackWaveforms);
