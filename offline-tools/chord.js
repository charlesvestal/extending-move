/* Chord tool specific functions and event handlers */

const CHORDS = {
  'Cm9': [-12, 0, 3, 7, 10, 15],
  'Fm': [-7, 5, 8, 17],
  'AbMaj7': [-4, 8, 15, 19],
  'Bb11 sus': [-2, 10, 15, 17, 20, 22],
  'EbMaj9': [-9, 3, 7, 10, 15, 19],
  'Fm7': [-7, 5, 8, 12, 15],
  'G7#9': [-5, 7, 11, 14, 17, 22],
  'C7#5': [-12, 0, 4, 8, 22],
  'Fm9': [-7, 5, 8, 12, 15, 19],
  'DbMaj7': [-11, 1, 5, 8, 13],
  'Bbm7': [-2, 10, 13, 17, 20],
  'C7sus': [-12, 0, 5, 7, 22],
  'C': [-12, 0, 4, 7, 12],
  'Fm add9': [-7, 5, 8, 12, 19]
};

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
      cell.textContent = padNumber + (row[colIndex] ? ": " + row[colIndex] : "");
      gridContainer.appendChild(cell);
    }
  }
  listElem.appendChild(gridContainer);
}

populateChordList();

/**
 * Generates a Chord preset using the shared base preset and drum cell chains.
 * @param {string} presetName - The preset name.
 * @param {Array} sampleFilenames - Array of sample filenames for each chord.
 * @returns {Object} - The generated preset object.
 */
function generateChordPreset(presetName, sampleFilenames) {
  const preset = generateBasePreset(presetName);
  const chordKeys = Object.keys(CHORDS);
  for (let i = 0; i < chordKeys.length; i++) {
    const chordName = chordKeys[i];
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

  const chordNames = Object.keys(CHORDS);
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
  zip.generateAsync({ type: "blob" }).then(function(content) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(content);
    a.download = presetName + ".ablpresetbundle";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });
});
