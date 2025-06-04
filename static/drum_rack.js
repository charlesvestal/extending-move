let drumRackWaveforms = [];

function initializeDrumRackWaveforms() {
    drumRackWaveforms.forEach(ws => {
        try { ws.destroy(); } catch (e) { console.error('destroy error', e); }
    });
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

        const audioContext = ws.backend.getAudioContext();
        fetch(audioPath)
            .then(res => res.arrayBuffer())
            .then(data => audioContext.decodeAudioData(data))
            .then(buffer => {
                const duration = buffer.duration;
                const sampleRate = buffer.sampleRate;
                const startSample = Math.floor(startPct * duration * sampleRate);
                const frameCount = Math.floor(lengthPct * duration * sampleRate);
                const slicedBuffer = audioContext.createBuffer(buffer.numberOfChannels, frameCount, sampleRate);
                for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
                    slicedBuffer.copyToChannel(
                        buffer.getChannelData(ch).subarray(startSample, startSample + frameCount),
                        ch,
                        0
                    );
                }
                ws.loadDecodedBuffer(slicedBuffer);
            });
        ws.on('finish', () => { ws.stop(); });
        container.addEventListener('click', function(e) {
            e.stopPropagation();
            drumRackWaveforms.forEach(other => { if (other.isPlaying()) other.stop(); });
            ws.stop();
            ws.seekTo(0);
            requestAnimationFrame(() => ws.play(0));
        });
    });
}

function initializeTimeStretchModal() {
    const modal = document.getElementById('timeStretchModal');
    if (!modal) return;
    const closeBtn = modal.querySelector('.modal-close');
    document.querySelectorAll('.time-stretch-button').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('ts_sample_path').value = btn.getAttribute('data-sample-path');
            document.getElementById('ts_preset_path').value = btn.getAttribute('data-preset-path');
            document.getElementById('ts_pad_number').value = btn.getAttribute('data-pad-number');
            modal.classList.remove('hidden');
        });
    });
    closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    window.addEventListener('click', e => { if (e.target === modal) modal.classList.add('hidden'); });
    const preserveCheckbox = document.getElementById('ts_preserve_pitch');
    const algoSelect = document.getElementById('ts_algorithm');
    function updateAlgoState() { algoSelect.disabled = !preserveCheckbox.checked; }
    preserveCheckbox.addEventListener('change', updateAlgoState);
    updateAlgoState();
}

function initDrumRackTab() {
    initializeDrumRackWaveforms();
    initializeTimeStretchModal();
}

export { initDrumRackTab };
