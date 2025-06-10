/* Preset editor utilities */

function generateBasePreset(presetName) {
  return {
    "$schema": "http://tech.ableton.com/schema/song/1.4.4/devicePreset.json",
    "kind": "instrumentRack",
    "name": presetName,
    "lockId": 1001,
    "lockSeal": -973461132,
    "parameters": {
      "Enabled": true,
      "Macro0": 0.0,
      "Macro1": 0.0,
      "Macro2": 0.0,
      "Macro3": 0.0,
      "Macro4": 0.0,
      "Macro5": 0.0,
      "Macro6": 0.0,
      "Macro7": 0.0
    },
    "chains": [
      {
        "name": "",
        "color": 0,
        "devices": [
          {
            "presetUri": null,
            "kind": "drumRack",
            "name": "",
            "lockId": 1001,
            "lockSeal": 830049224,
            "parameters": {
              "Enabled": true,
              "Macro0": 0.0,
              "Macro1": 0.0,
              "Macro2": 0.0,
              "Macro3": 0.0,
              "Macro4": 0.0,
              "Macro5": 0.0,
              "Macro6": 0.0,
              "Macro7": 0.0
            },
            "chains": [],
            "returnChains": [
              {
                "name": "",
                "color": 0,
                "devices": [
                  {
                    "presetUri": null,
                    "kind": "reverb",
                    "name": "",
                    "parameters": {},
                    "deviceData": {}
                  }
                ],
                "mixer": {
                  "pan": 0.0,
                  "solo-cue": false,
                  "speakerOn": true,
                  "volume": 0.0,
                  "sends": [
                    {
                      "isEnabled": false,
                      "amount": -70.0
                    }
                  ]
                }
              }
            ]
          },
          {
            "presetUri": null,
            "kind": "saturator",
            "name": "Saturator",
            "parameters": {},
            "deviceData": {}
          }
        ],
        "mixer": {
          "pan": 0.0,
          "solo-cue": false,
          "speakerOn": true,
          "volume": 0.0,
          "sends": []
        }
      }
    ]
  };
}

function createDrumCellChain(receivingNote, name, params, sampleUri) {
  return {
    "name": name,
    "color": 0,
    "devices": [
      {
        "presetUri": null,
        "kind": "drumCell",
        "name": name,
        "parameters": params,
        "deviceData": {
          "sampleUri": sampleUri || null
        }
      }
    ],
    "mixer": {
      "pan": 0.0,
      "solo-cue": false,
      "speakerOn": true,
      "volume": 0.0,
      "sends": [
        {
          "isEnabled": true,
          "amount": -70.0
        }
      ]
    },
    "drumZoneSettings": {
      "receivingNote": receivingNote,
      "sendingNote": 60,
      "chokeGroup": 1
    }
  };
}

function toWav(buffer, opt) {
  opt = opt || {};
  const numChannels = buffer.numberOfChannels;
  const sampleRate = buffer.sampleRate;
  const format = opt.float32 ? 3 : 1;
  const bitDepth = format === 3 ? 32 : 16;
  let result;
  if (numChannels === 2) {
    result = interleave(buffer.getChannelData(0), buffer.getChannelData(1));
  } else {
    result = buffer.getChannelData(0);
  }
  return encodeWAV(result, numChannels, sampleRate, format, bitDepth);
}

function interleave(inputL, inputR) {
  const length = inputL.length + inputR.length;
  const result = new Float32Array(length);
  let index = 0,
    inputIndex = 0;
  while (index < length) {
    result[index++] = inputL[inputIndex];
    result[index++] = inputR[inputIndex];
    inputIndex++;
  }
  return result;
}

function encodeWAV(samples, numChannels, sampleRate, format, bitDepth) {
  const bytesPerSample = bitDepth / 8;
  const blockAlign = numChannels * bytesPerSample;
  const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
  const view = new DataView(buffer);
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
  for (let i = 0; i < input.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, input[i]));
    output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
}

function writeFloat32(output, offset, input) {
  for (let i = 0; i < input.length; i++, offset += 4) {
    output.setFloat32(offset, input[i], true);
  }
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}

function mixAudioBuffers(buffers) {
  if (buffers.length === 0) return null;
  const numChannels = buffers[0].numberOfChannels;
  const sampleRate = buffers[0].sampleRate;
  const maxLength = Math.max(...buffers.map((b) => b.length));
  const tempCtx = new (window.AudioContext || window.webkitAudioContext)();
  const mixedBuffer = tempCtx.createBuffer(numChannels, maxLength, sampleRate);
  for (let channel = 0; channel < numChannels; channel++) {
    const mixedData = mixedBuffer.getChannelData(channel);
    for (let i = 0; i < maxLength; i++) {
      let sum = 0;
      buffers.forEach((buffer) => {
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

if (typeof window !== 'undefined') {
  window.generateBasePreset = generateBasePreset;
  window.createDrumCellChain = createDrumCellChain;
  window.toWav = toWav;
  window.mixAudioBuffers = mixAudioBuffers;
  window.normalizeAudioBuffer = normalizeAudioBuffer;
}
