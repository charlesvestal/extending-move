export async function parseLoopPoints(arrayBuffer) {
  try {
    const mm = await import('https://cdn.jsdelivr.net/npm/music-metadata-browser/dist/music-metadata-browser.esm.min.js');
    const meta = await mm.parseBuffer(new Uint8Array(arrayBuffer), 'audio/wav');
    const smpl = meta.native && meta.native.smpl ? meta.native.smpl[0] : null;
    if (smpl && smpl.loops && smpl.loops.length) {
      return { loopStart: smpl.loops[0].start, loopEnd: smpl.loops[0].end };
    }
    const cues = meta.cue && meta.cue.points ? meta.cue.points : [];
    if (cues.length >= 2) {
      return { loopStart: cues[0].position, loopEnd: cues[1].position };
    }
  } catch (err) {
    console.log('metadata parse failed', err);
  }
  const view = new DataView(arrayBuffer);
  const text = (o) => String.fromCharCode(
    view.getUint8(o),
    view.getUint8(o+1),
    view.getUint8(o+2),
    view.getUint8(o+3)
  );
  let offset = 12; // skip RIFF header
  while (offset + 8 <= view.byteLength) {
    const id = text(offset);
    const size = view.getUint32(offset + 4, true);
    if (id === 'smpl') {
      const numLoops = view.getUint32(offset + 28, true);
      if (numLoops > 0) {
        const loopOff = offset + 36;
        const start = view.getUint32(loopOff + 4, true);
        const end = view.getUint32(loopOff + 8, true);
        return { loopStart: start, loopEnd: end };
      }
    }
    offset += 8 + size + (size % 2);
  }
  // fallback to cue points
  let cueStart = null;
  let cueEnd = null;
  offset = 12;
  while (offset + 8 <= view.byteLength) {
    const id = text(offset);
    const size = view.getUint32(offset + 4, true);
    if (id === 'cue ') {
      const num = view.getUint32(offset + 8, true);
      const first = offset + 12;
      for (let i=0;i<num;i++) {
        const pos = view.getUint32(first + i*24 + 20, true);
        if (cueStart === null) cueStart = pos;
        else if (cueEnd === null) cueEnd = pos;
      }
    }
    offset += 8 + size + (size % 2);
  }
  if (cueStart !== null && cueEnd !== null) {
    return { loopStart: cueStart, loopEnd: cueEnd };
  }
  throw new Error('No loop points found');
}

export async function bakeLoopedBuffer(buffer, loopStart, loopEnd, targetSec = 60, fadeMs = 15) {
  const abu = await import('https://cdn.jsdelivr.net/npm/audio-buffer-utils/+esm');
  const rate = buffer.sampleRate;
  const intro = abu.slice(buffer, 0, loopStart);
  const loopSeg = abu.slice(buffer, loopStart, loopEnd);
  const loops = Math.max(1, Math.ceil((targetSec * rate - loopStart) / (loopEnd - loopStart)));
  const fade = Math.floor(rate * fadeMs / 1000);
  let out = intro;
  for (let i = 0; i < loops; i++) {
    let seg = loopSeg;
    if (fade > 1 && i > 0) seg = abu.crossfade(out, seg, fade);
    out = abu.concat(out, seg);
  }
  return out;
}

export function exportWav(buffer, name = 'looped.wav') {
  const wavefileUrl = 'https://cdn.jsdelivr.net/npm/wavefile/+esm';
  return import(wavefileUrl).then(({ default: WaveFile }) => {
    const wav = new WaveFile();
    const chans = [];
    for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
      chans.push(buffer.getChannelData(ch));
    }
    wav.fromScratch(buffer.numberOfChannels, buffer.sampleRate, '32f', chans);
    const blob = new Blob([wav.toBuffer()], { type: 'audio/wav' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    return blob;
  });
}
