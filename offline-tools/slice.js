/* Slice tool specific functions */

// Converts an AudioBuffer to a WAV ArrayBuffer (44.1kHz, 16-bit PCM)
function toWav(audioBuffer) {
  const numChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const bufferLength = audioBuffer.length * numChannels * 2 + 44;
  const buffer = new ArrayBuffer(bufferLength);
  const view = new DataView(buffer);

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + audioBuffer.length * numChannels * 2, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * 2, true);
  view.setUint16(32, numChannels * 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, 'data');
  view.setUint32(40, audioBuffer.length * numChannels * 2, true);

  let offset = 44;
  for (let i = 0; i < audioBuffer.length; i++) {
    for (let channel = 0; channel < numChannels; channel++) {
      let sample = audioBuffer.getChannelData(channel)[i];
      sample = Math.max(-1, Math.min(1, sample));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
      offset += 2;
    }
  }
  return buffer;
}

// Converts an MP3 file to a 44.1kHz 16-bit WAV Blob.
function convertMp3ToWav(file) {
  return new Promise((resolve, reject) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const reader = new FileReader();
    reader.onload = function(evt) {
      const arrayBuffer = evt.target.result;
      audioContext.decodeAudioData(arrayBuffer, (audioBuffer) => {
        const targetSampleRate = 44100;
        if (audioBuffer.sampleRate !== targetSampleRate) {
          // Resample using an OfflineAudioContext
          const offlineCtx = new OfflineAudioContext(
            audioBuffer.numberOfChannels,
            Math.ceil(audioBuffer.duration * targetSampleRate),
            targetSampleRate
          );
          const source = offlineCtx.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(offlineCtx.destination);
          source.start(0);
          offlineCtx.startRendering().then((resampledBuffer) => {
            const wavBuffer = toWav(resampledBuffer);
            resolve(new Blob([wavBuffer], { type: 'audio/wav' }));
          }).catch(reject);
        } else {
          const wavBuffer = toWav(audioBuffer);
          resolve(new Blob([wavBuffer], { type: 'audio/wav' }));
        }
      }, reject);
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}

function initWaveSurfer() {
  if (window.wavesurfer) {
    window.wavesurfer.destroy();
  }
  window.wavesurfer = WaveSurfer.create({
    container: '#waveform',
    waveColor: 'violet',
    progressColor: 'purple',
    height: 128,
    plugins: [
      WaveSurfer.regions.create({})
    ]
  });
  
  window.wavesurfer.on('ready', () => {
    if (window.wavesurfer.getDuration() > 0) {
      window.audioReady = true;
      createContiguousRegions();
    }
  });
  
  window.wavesurfer.on('region-update-end', keepRegionsContiguous);
  
  window.wavesurfer.on('region-click', (region, e) => {
    e.stopPropagation();
    region.play();
  });
}

function createContiguousRegions() {
  const numSlicesInput = document.getElementById('num_slices');
  const numSlices = parseInt(numSlicesInput.value, 10) || 16;
  window.wavesurfer.clearRegions();
  const duration = window.wavesurfer.getDuration();
  const sliceDuration = duration / numSlices;
  for (let i = 0; i < numSlices; i++) {
    let regionOptions = {
      start: i * sliceDuration,
      end: (i + 1) * sliceDuration,
      color: 'rgba(0, 255, 0, 0.2)',
      drag: false,
      resize: true
    };
    if (i === 0) { 
      regionOptions.resize = 'right'; 
    } else if (i === numSlices - 1) {
      regionOptions.resize = 'left';
    }
    window.wavesurfer.addRegion(regionOptions);
  }
}

function keepRegionsContiguous(updatedRegion) {
  let regions = Object.values(window.wavesurfer.regions.list).sort((a, b) => a.start - b.start);
  const idx = regions.findIndex(r => r.id === updatedRegion.id);
  if (idx > 0) {
    regions[idx - 1].update({ end: updatedRegion.start });
  }
  if (idx < regions.length - 1) {
    regions[idx + 1].update({ start: updatedRegion.end });
  }
}

/**
 * Generates a Slice preset using the shared base preset and drum cell chains.
 * @param {string} presetName - The preset name.
 * @returns {Object} - The generated preset object.
 */
function generateSlicePreset(presetName) {
  const preset = generateBasePreset(presetName);
  // Create 16 drum cell chains for slices.
  for (let i = 0; i < 16; i++) {
    const chain = createDrumCellChain(
      36 + i,
      "", 
      {"Voice_Envelope_Hold": 60.0, "Voice_PlaybackStart": 0.0, "Voice_Envelope_Decay": 0.0},
      null
    );
    preset.chains[0].devices[0].chains.push(chain);
  }
  return preset;
}

/**
 * Updates drum cell parameters with slice information.
 * @param {Object} template - The preset object.
 * @param {Array} slices_info - Array of slice info objects.
 * @param {string} sampleFileName - The sample file name.
 */
function updateDrumCellParameters(template, slices_info, sampleFileName) {
  let drumChains = template.chains[0].devices[0].chains;
  const totalDuration = window.wavesurfer.getDuration();
  for (let i = 0; i < drumChains.length; i++) {
    let drumCell = drumChains[i].devices[0];
    if (i < slices_info.length) {
      drumCell.parameters["Voice_PlaybackStart"] = slices_info[i].offset;
      drumCell.parameters["Voice_Envelope_Hold"] = 60.0;
      drumCell.parameters["Voice_Envelope_Decay"] = 0.0;
      drumCell.parameters["Voice_PlaybackLength"] = slices_info[i].hold / totalDuration;
      drumCell.deviceData["sampleUri"] = "Samples/" + encodeURIComponent(sampleFileName);
    } else {
      drumCell.deviceData["sampleUri"] = null;
    }
  }
}

// Event listeners for Slice tool

document.getElementById('resetSlices').addEventListener('click', () => {
  if (window.audioReady) {
    window.wavesurfer.clearRegions();
    createContiguousRegions();
  }
});

document.getElementById('num_slices').addEventListener('change', function() {
  if (window.audioReady) {
    window.wavesurfer.clearRegions();
    createContiguousRegions();
  }
});

document.getElementById('wavFileInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    // Check if the uploaded file is an MP3.
    if (file.type === 'audio/mpeg' || file.name.toLowerCase().endsWith('.mp3')) {
      convertMp3ToWav(file).then((wavBlob) => {
        // Update the file name to have a .wav extension for preset references.
        wavBlob.name = file.name.replace(/\.mp3$/i, '.wav');
        window.fileBlob = wavBlob;
        initWaveSurfer();
        window.wavesurfer.loadBlob(wavBlob);
      }).catch((err) => {
        alert("Error converting MP3 to WAV: " + err);
      });
    } else {
      window.fileBlob = file;
      initWaveSurfer();
      window.wavesurfer.loadBlob(file);
    }
  }
});

document.getElementById('generatePreset').addEventListener('click', () => {
  if (!window.audioReady) {
    alert("Audio not loaded.");
    return;
  }
  const duration = window.wavesurfer.getDuration();
  let regions = Object.values(window.wavesurfer.regions.list).sort((a, b) => a.start - b.start);
  let slices_info = regions.map(region => ({
    offset: region.start / duration,
    hold: region.end - region.start
  }));
  let presetName = window.fileBlob ? window.fileBlob.name.replace(/\.[^/.]+$/, "") : "Preset";
  let preset = generateSlicePreset(presetName);
  updateDrumCellParameters(preset, slices_info, window.fileBlob ? window.fileBlob.name : "sample.wav");
  
  let zip = new JSZip();
  zip.file("Preset.ablpreset", JSON.stringify(preset, null, 2));
  if (window.fileBlob) {
    zip.file("Samples/" + window.fileBlob.name, window.fileBlob);
  }
  
  zip.generateAsync({type:"blob"}).then(function(content) {
    let a = document.createElement("a");
    a.href = URL.createObjectURL(content);
    a.download = presetName + ".ablpresetbundle";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });
});

// Resize handler using the shared debounce function
window.addEventListener('resize', debounce(() => {
  if (window.wavesurfer && window.wavesurfer.drawer && window.wavesurfer.drawer.wrapper) {
    const container = document.getElementById('waveform');
    const newWidth = container.clientWidth;
    const canvases = window.wavesurfer.drawer.wrapper.querySelectorAll('canvas');
    canvases.forEach(canvas => {
      canvas.width = newWidth;
    });
    window.wavesurfer.drawBuffer();
  }
}, 300));
