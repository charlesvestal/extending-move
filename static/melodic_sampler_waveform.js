function initMelodicSamplerPreview() {
    const container = document.getElementById('melodicSampleWaveform');
    if (!container) return;
    const audioPath = container.dataset.audioPath;
    if (!audioPath) return;
    const ws = WaveSurfer.create({
        container: container,
        waveColor: 'violet',
        progressColor: 'purple',
        height: 64,
        responsive: true,
        normalize: true,
        hideScrollbar: true,
        interact: false
    });
    container.wavesurfer = ws;
    ws.load(audioPath);
    container.addEventListener('click', function(e) {
        e.stopPropagation();
        ws.stop();
        ws.seekTo(0);
        requestAnimationFrame(() => ws.play(0));
    });
}

export { initMelodicSamplerPreview };
