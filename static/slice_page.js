let wavesurfer;
let audioReady = false;

function createWaveSurfer() {
  wavesurfer = WaveSurfer.create({
    container: '#waveform',
    waveColor: 'violet',
    progressColor: 'purple',
    height: 128,
    responsive: true,
    plugins: [WaveSurfer.regions.create({})]
  });

  wavesurfer.on('ready', () => {
    audioReady = true;
    createEvenRegions();
  });

  wavesurfer.on('region-click', (region, e) => {
    e.stopPropagation();
    region.play();
  });

  wavesurfer.on('region-update-end', keepRegionsContiguous);
}

function createEvenRegions() {
  const numInput = document.getElementById('num_slices');
  if (!audioReady || !wavesurfer || !numInput) return;
  const count = parseInt(numInput.value, 10) || 0;
  if (count <= 0) return;
  wavesurfer.clearRegions();
  const duration = wavesurfer.getDuration();
  const sliceDur = duration / count;
  for (let i = 0; i < count; i++) {
    wavesurfer.addRegion({
      start: i * sliceDur,
      end: (i + 1) * sliceDur,
      color: 'rgba(0, 255, 0, 0.2)',
      drag: false
    });
  }
}

function keepRegionsContiguous(updated) {
  const regions = Object.values(wavesurfer.regions.list).sort((a, b) => a.start - b.start);
  const idx = regions.findIndex(r => r.id === updated.id);
  if (idx > 0) {
    const prev = regions[idx - 1];
    prev.update({ end: updated.start });
  }
  if (idx < regions.length - 1) {
    const next = regions[idx + 1];
    next.update({ start: updated.end });
  }
}

function detectTransients() {
  const fileInput = document.getElementById('file');
  const msg = document.getElementById('transient-detect-message');
  if (!fileInput.files[0]) {
    msg.textContent = 'Please select a file first.';
    msg.style.color = 'orange';
    return;
  }
  msg.textContent = 'Detecting transients...';
  msg.style.color = '#337ab7';
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  const sens = document.getElementById('sensitivity');
  formData.append('sensitivity', sens ? sens.value : 0.07);
  fetch('http://' + location.host + '/detect-transients', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.success && data.regions) {
        msg.textContent = data.message;
        msg.style.color = 'green';
        wavesurfer.clearRegions();
        data.regions.forEach(r => {
          wavesurfer.addRegion({ start: r.start, end: r.end, color: 'rgba(0, 255, 0, 0.2)', drag: false });
        });
      } else {
        msg.textContent = data.message || 'No transients detected.';
        msg.style.color = 'orange';
      }
    })
    .catch(e => {
      msg.textContent = 'Error detecting transients.';
      msg.style.color = 'red';
      console.error(e);
    });
}

document.addEventListener('DOMContentLoaded', () => {
  createWaveSurfer();

  document.getElementById('file').addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) {
      audioReady = false;
      wavesurfer.clearRegions();
      wavesurfer.loadBlob(file);
    }
  });

  document.getElementById('even-slices-btn').addEventListener('click', createEvenRegions);
  document.getElementById('detect-transients-btn').addEventListener('click', detectTransients);

  const sens = document.getElementById('sensitivity');
  if (sens) {
    sens.addEventListener('input', () => {
      document.getElementById('sensitivity-value').textContent = sens.value;
    });
  }

  const form = document.getElementById('slice-form');
  form.addEventListener('submit', () => {
    if (wavesurfer && audioReady) {
      const regions = Object.values(wavesurfer.regions.list).map(r => ({ start: r.start, end: r.end }));
      document.getElementById('regions-input').value = JSON.stringify(regions);
    }
  });
});
