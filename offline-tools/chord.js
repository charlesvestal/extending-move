//v180220250205
/* Chord tool specific functions and event handlers */

// --- New Code: Generate a complete CHORDS object for every key (assume C as pitch 0)
// Define base chord types relative to C. Each array includes:
//   a lower-octave note (–12), the root (0), and then chord tones.
const baseChordTypes = {
  "":    [-12, 0, 4, 7, 12],       // Major
  "m":   [-12, 0, 3, 7, 12],       // Minor
  "dim": [-12, 0, 3, 6, 12],       // Diminished
  "aug": [-12, 0, 4, 8, 12],       // Augmented
  "7":   [-12, 0, 4, 7, 10],       // Dominant 7
  "maj7":[-12, 0, 4, 7, 11],       // Major 7
  "m7":  [-12, 0, 3, 7, 10],       // Minor 7
  "sus2":[-12, 0, 2, 7, 12],       // Sus2
  "sus4":[-12, 0, 5, 7, 12],       // Sus4
  "7sus":[-12, 0, 5, 7, 10],       // Dominant 7 with sus4
  "m9":  [-12, 0, 3, 7, 10, 15],   // Minor 9
  "maj9":[-12, 0, 4, 7, 11, 14],   // Major 9
  "m7b5":[-12, 0, 3, 6, 10],       // Half-diminished (m7b5)
  "6":   [-12, 0, 4, 7, 9],        // 6 chord
  "m6":  [-12, 0, 3, 7, 9],        // Minor 6
  "add9":[-12, 0, 4, 7, 14],        // add9 chord
  "7#9":  [-12, 0, 4, 7, 10, 15],   // Dominant 7 with sharp 9
  "7#5":  [-12, 0, 4, 8, 10],        // Dominant 7 with sharp 5
  "11sus": [-12, 0, 5, 7, 10, 17],   // 11 suspended chord
  "madd9": [-12, 0, 3, 7, 14]        // Minor add9 chord
};

// List of keys using flats for accidentals (as preferred in the default chords)
const keys = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];
const keyOffsets = { "C": 0, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "Gb": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11 };

// Build the CHORDS object by transposing each base chord type for every key.
const CHORDS = {};
for (let i = 0; i < keys.length; i++) {
  const key = keys[i];
  const offset = keyOffsets[key];
  for (let variation in baseChordTypes) {
    // For an empty variation, the chord name is just the key.
    const chordName = key + (variation === "" ? "" : variation);
    const baseIntervals = baseChordTypes[variation];
    // Transpose by adding the key's offset to each interval.
    const transposed = baseIntervals.map(interval => interval + offset);
    CHORDS[chordName] = transposed;
  }
}
// --- End of new CHORDS generation code

if (!window.selectedChords) {
    const defaultChords = [
        "Cm9",
        "Fm",
        "Abmaj7",
        "Bb11sus",
        "Ebmaj9",
        "Fm7",
        "G7#9",
        "C7#5",
        "Fm9",
        "Dbmaj7",
        "Bbm7",
        "C7sus",
        "C",
        "Fmadd9",
        "C",
        "C"
    ];
    window.selectedChords = [];
    for (let i = 0; i < 16; i++) {
        window.selectedChords[i] = defaultChords[i] || "";
    }
}

function populateChordList() {
  const listElem = document.getElementById('chordList');
  listElem.innerHTML = '';

  // Get chord keys and ensure there are 16 items (fill with empty strings if needed)
  let chordKeys = Object.keys(CHORDS);
  while (chordKeys.length < 16) {
    chordKeys.push("");
  }

  // Partition the array into 4 rows (each row: pads 1-4, 5-8, etc.)
  let rows = [];
  for (let i = 0; i < 4; i++) {
    rows.push(chordKeys.slice(i * 4, i * 4 + 4));
  }

  // Reverse rows so that the first row becomes the bottom row (pads 1-4)
  rows.reverse();

  // Create a grid container using CSS Grid
  const gridContainer = document.createElement('div');
  gridContainer.style.display = 'grid';
  gridContainer.style.gridTemplateColumns = 'repeat(4, 1fr)';
  gridContainer.style.gridGap = '5px';

  // Populate the grid with cells showing pad number and chord name
  for (let rowIndex = 0; rowIndex < rows.length; rowIndex++) {
    const row = rows[rowIndex];
    for (let colIndex = 0; colIndex < row.length; colIndex++) {
      // Calculate pad number: bottom row (rows[3]) are pads 1-4, then 5-8, etc.
      const padNumber = (rows.length - rowIndex - 1) * 4 + (colIndex + 1);
      const cell = document.createElement('div');
      cell.style.border = '1px solid #ccc';
      cell.style.padding = '10px';
      cell.style.textAlign = 'center';

      // Build a dropdown <select> with all available chords
      let availableChords = Object.keys(CHORDS);
      let selectHTML = '<select id="chord-select-' + padNumber + '">';
      availableChords.forEach(chord => {
          selectHTML += '<option value="' + chord + '">' + chord + '</option>';
      });
      selectHTML += '</select>';

      cell.innerHTML = `<div class="chord-label">${padNumber}: ${selectHTML}</div>
                        <div class="chord-preview" id="chord-preview-${padNumber}" style="height: 50px; cursor: pointer;"></div>`;
      gridContainer.appendChild(cell);

      // Set the select's value to the current selection and attach a change listener
      const selectElem = cell.querySelector(`#chord-select-${padNumber}`);
      selectElem.value = window.selectedChords[padNumber - 1];
      selectElem.addEventListener('change', function() {
          window.selectedChords[padNumber - 1] = this.value;
          regenerateChordPreview(padNumber);
      });
    }
  }
  listElem.appendChild(gridContainer);

  // After building the grid, update the waveform preview for each pad using the default selection.
  for (let padNumber = 1; padNumber <= 16; padNumber++) {
      if (window.selectedChords[padNumber - 1]) {
          regenerateChordPreview(padNumber);
      }
  }
}

document.addEventListener('DOMContentLoaded', function() {
    populateChordList();
});

async function regenerateChordPreview(padNumber) {
    if (!window.decodedBuffer) return;
    const selectedChord = window.selectedChords[padNumber - 1];
    const intervals = CHORDS[selectedChord];
    const blob = await processChordSample(window.decodedBuffer, intervals);
    const url = URL.createObjectURL(blob);
    const previewContainer = document.getElementById(`chord-preview-${padNumber}`);
    if (previewContainer) {
        // Destroy any existing waveform for this cell
        if (window.chordWaveforms && window.chordWaveforms[padNumber - 1]) {
            window.chordWaveforms[padNumber - 1].destroy();
            window.chordWaveforms[padNumber - 1] = null;
        }
        const ws = WaveSurfer.create({
            container: previewContainer,
            waveColor: '#888',
            progressColor: '#555',
            height: 50,
            responsive: true,
            interact: true,
            normalize: true,
            cursorWidth: 0
        });
        ws.load(url);
        previewContainer.addEventListener('click', function(e) {
            e.stopPropagation();
            // Stop all other chord waveform instances
            if (window.chordWaveforms && window.chordWaveforms.length) {
                window.chordWaveforms.forEach(instance => {
                    if (instance && instance !== ws) {
                        instance.stop();
                    }
                });
            }
            ws.stop();
            ws.seekTo(0);
            requestAnimationFrame(() => ws.play(0));
        });
        if (!window.chordWaveforms) window.chordWaveforms = [];
        window.chordWaveforms[padNumber - 1] = ws;
    }
}

/**
 * Generates a Chord preset using the shared base preset and drum cell chains.
 * @param {string} presetName - The preset name.
 * @param {Array} sampleFilenames - Array of sample filenames for each chord.
 * @returns {Object} - The generated preset object.
 */
function generateChordPreset(presetName, sampleFilenames) {
  const preset = generateBasePreset(presetName);
  for (let i = 0; i < window.selectedChords.length; i++) {
    const chordName = window.selectedChords[i];
    const chain = createDrumCellChain(
      36 + i,
      chordName,
      {"Voice_Envelope_Hold": 60.0},
      "Samples/" + encodeURIComponent(sampleFilenames[i])
    );
    preset.chains[0].devices[0].chains.push(chain);
  }
  return preset;
}

function toWav(buffer, opt) {
  opt = opt || {};
  var numChannels = buffer.numberOfChannels;
  var sampleRate = buffer.sampleRate;
  var format = opt.float32 ? 3 : 1;
  var bitDepth = format === 3 ? 32 : 16;
  var result;
  if (numChannels === 2) {
    result = interleave(buffer.getChannelData(0), buffer.getChannelData(1));
  } else {
    result = buffer.getChannelData(0);
  }
  return encodeWAV(result, numChannels, sampleRate, format, bitDepth);
}

function interleave(inputL, inputR) {
  var length = inputL.length + inputR.length;
  var result = new Float32Array(length);
  var index = 0, inputIndex = 0;
  while (index < length) {
    result[index++] = inputL[inputIndex];
    result[index++] = inputR[inputIndex];
    inputIndex++;
  }
  return result;
}

function encodeWAV(samples, numChannels, sampleRate, format, bitDepth) {
  var bytesPerSample = bitDepth / 8;
  var blockAlign = numChannels * bytesPerSample;
  var buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
  var view = new DataView(buffer);
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + samples.length * bytesPerSample, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, format, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitDepth, true);
  writeString(view, 36, 'data');
  view.setUint32(40, samples.length * bytesPerSample, true);
  if (format === 1) {
    floatTo16BitPCM(view, 44, samples);
  } else {
    writeFloat32(view, 44, samples);
  }
  return buffer;
}

function floatTo16BitPCM(output, offset, input) {
  for (var i = 0; i < input.length; i++, offset += 2) {
    var s = Math.max(-1, Math.min(1, input[i]));
    output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
}

function writeFloat32(output, offset, input) {
  for (var i = 0; i < input.length; i++, offset += 4) {
    output.setFloat32(offset, input[i], true);
  }
}

function writeString(view, offset, string) {
  for (var i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}

async function pitchShiftOffline(buffer, semitoneShift) {
  const factor = Math.pow(2, semitoneShift / 12);
  const newLength = Math.floor(buffer.length / factor);
  const offlineCtx = new OfflineAudioContext(
    buffer.numberOfChannels,
    newLength,
    buffer.sampleRate
  );
  const source = offlineCtx.createBufferSource();
  source.buffer = buffer;
  source.playbackRate.value = factor;
  source.connect(offlineCtx.destination);
  source.start(0);
  return offlineCtx.startRendering();
}

function mixAudioBuffers(buffers) {
  if (buffers.length === 0) return null;
  const numChannels = buffers[0].numberOfChannels;
  const sampleRate = buffers[0].sampleRate;
  const maxLength = Math.max(...buffers.map(b => b.length));
  const tempCtx = new (window.AudioContext || window.webkitAudioContext)();
  const mixedBuffer = tempCtx.createBuffer(numChannels, maxLength, sampleRate);
  for (let channel = 0; channel < numChannels; channel++) {
    const mixedData = mixedBuffer.getChannelData(channel);
    for (let i = 0; i < maxLength; i++) {
      let sum = 0;
      buffers.forEach(buffer => {
        const data = buffer.getChannelData(channel);
        if (i < data.length) {
          sum += data[i];
        }
      });
      mixedData[i] = sum;
    }
  }
  return mixedBuffer;
}

function normalizeAudioBuffer(buffer, targetPeak = 0.9) {
  const numChannels = buffer.numberOfChannels;
  let maxVal = 0;
  for (let channel = 0; channel < numChannels; channel++) {
    const data = buffer.getChannelData(channel);
    for (let i = 0; i < data.length; i++) {
      maxVal = Math.max(maxVal, Math.abs(data[i]));
    }
  }
  const gain = maxVal > 0 ? targetPeak / maxVal : 1;
  for (let channel = 0; channel < numChannels; channel++) {
    const data = buffer.getChannelData(channel);
    for (let i = 0; i < data.length; i++) {
      data[i] *= gain;
    }
  }
  return buffer;
}

async function processChordSample(buffer, intervals) {
  const pitchedBuffers = [];
  for (let semitone of intervals) {
    const pitched = await pitchShiftOffline(buffer, semitone);
    pitchedBuffers.push(pitched);
  }
  const mixed = mixAudioBuffers(pitchedBuffers);
  const normalized = normalizeAudioBuffer(mixed, 0.9);
  const wavData = toWav(normalized);
  return new Blob([new DataView(wavData)], { type: 'audio/wav' });
}

document.getElementById('generatePreset').addEventListener('click', async () => {
  document.getElementById('loadingIndicator').style.display = 'block';
  document.getElementById('progressPercent').textContent = '0%';
  
  const fileInput = document.getElementById('wavFileInput');
  const presetNameInput = document.getElementById('presetName');
  if (!fileInput.files || fileInput.files.length === 0) {
    alert("Please select a WAV file.");
    return;
  }
  const file = fileInput.files[0];
  let baseName = file.name.replace(/\.[^/.]+$/, "");
  let presetName = presetNameInput.value.trim() || baseName;

  const arrayBuffer = await file.arrayBuffer();
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const decodedBuffer = await audioCtx.decodeAudioData(arrayBuffer);

  const chordNames = window.selectedChords;
  let sampleFilenames = [];
  let processedSamples = {};
  for (let chordName of chordNames) {
    const intervals = CHORDS[chordName];
    const blob = await processChordSample(decodedBuffer, intervals);
    let safeChordName = chordName.replace(/\s+/g, '');
    let filename = `${baseName}_chord_${safeChordName}.wav`;
    sampleFilenames.push(filename);
    processedSamples[chordName] = blob;
  }

  const preset = generateChordPreset(presetName, sampleFilenames);
  const presetJson = JSON.stringify(preset, null, 2);

  const zip = new JSZip();
  zip.file("Preset.ablpreset", presetJson);
  const samplesFolder = zip.folder("Samples");
  for (let chordName of chordNames) {
    let safeChordName = chordName.replace(/\s+/g, '');
    let filename = `${baseName}_chord_${safeChordName}.wav`;
    const blob = processedSamples[chordName];
    samplesFolder.file(filename, blob);
  }
  zip.generateAsync({ type: "blob" }, function(metadata) {
    document.getElementById('progressPercent').textContent = Math.round(metadata.percent) + "%";
  }).then(function(content) {
    document.getElementById('loadingIndicator').style.display = 'none';
    const a = document.createElement("a");
    a.href = URL.createObjectURL(content);
    a.download = presetName + ".ablpresetbundle";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });
});

// Process chord samples for preview when a file is uploaded
document.getElementById('wavFileInput').addEventListener('change', async function(e) {
    // Clear any previously generated waveform previews
    if (window.chordWaveforms && window.chordWaveforms.length) {
        window.chordWaveforms.forEach(ws => ws.destroy());
    }
    window.chordWaveforms = [];

    // Clear the inner HTML of all preview containers (assuming IDs "chord-preview-1" to "chord-preview-16")
    for (let i = 1; i <= 16; i++) {
        const container = document.getElementById(`chord-preview-${i}`);
        if (container) {
            container.innerHTML = "";
        }
    }
    const file = e.target.files[0];
    if (!file) return;
    
    console.log("File selected:", file);
    
    const arrayBuffer = await file.arrayBuffer();
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const decodedBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    window.decodedBuffer = decodedBuffer;
    const chordNames = window.selectedChords;
        
    // Clear any previous chord waveform instances
    window.chordWaveforms = [];
    
    // Process each chord sample and create its waveform preview sequentially
    for (let i = 0; i < chordNames.length; i++) {
        const chordName = chordNames[i];
        console.log("Processing chord:", chordName);
        const blob = await processChordSample(decodedBuffer, CHORDS[chordName]);
        const url = URL.createObjectURL(blob);
        const padNumber = i + 1;  // Adjust this if your grid order differs
        const previewContainer = document.getElementById(`chord-preview-${padNumber}`);
        if (previewContainer) {
            const ws = WaveSurfer.create({
                container: previewContainer,
                waveColor: '#888',
                progressColor: '#555',
                height: 50,
                responsive: true,
                interact: true,
                normalize: true,
                cursorWidth: 0
            });
            ws.load(url);
            // Toggle play/pause on click
            previewContainer.addEventListener('click', function(e) {
              e.stopPropagation();
              // Stop all other chord waveform instances
              if (window.chordWaveforms && window.chordWaveforms.length) {
                  window.chordWaveforms.forEach(instance => {
                      if (instance && instance !== ws) {
                          instance.stop();
                      }
                  });
              }
              if (ws && ws.backend) {
                  ws.stop();
                  ws.seekTo(0);
                  requestAnimationFrame(() => ws.play(0));
              }
            });
            window.chordWaveforms.push(ws);
        }
    }
});
