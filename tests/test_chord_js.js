const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

async function runProcessChordSample(file, keepLength) {
  const code = fs.readFileSync(file, 'utf8');
  const match = code.match(/async function processChordSample[\s\S]*?\n}\n/);
  if (!match) throw new Error('function not found');
  const context = {
    pitchShiftOffline: async (buf, semitone) => ({ length: buf.length }),
    trimLeadingSilence: buf => ({ length: buf.length - 1 }),
    soundtouchStretch: async (buf, len) => ({ length: len }),
    mixAudioBuffers: buffers => {
      context.mixedLen = Math.max(...buffers.map(b => b.length));
      return { length: context.mixedLen };
    },
    normalizeAudioBuffer: buf => buf,
    toWav: buf => new ArrayBuffer(buf.length || 0),
    Blob: function(arr, opt) {},
  };
  vm.createContext(context);
  vm.runInContext(match[0], context);
  await context.processChordSample({ length: 10 }, [0], keepLength);
  return context.mixedLen;
}

(async () => {
  assert.strictEqual(await runProcessChordSample('offline-tools/chord.js', true), 10);
  assert.strictEqual(await runProcessChordSample('static/chord.js', true), 10);
  assert.strictEqual(await runProcessChordSample('offline-tools/chord.js', false), 8);
  assert.strictEqual(await runProcessChordSample('static/chord.js', false), 8);
  console.log('All chord.js tests passed');
})();
