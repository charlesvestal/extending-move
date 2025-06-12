// Load and play the current melodic sampler sample

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('sample-waveform');
  const hidden = document.getElementById('sample-path-hidden');
  if (!container || !hidden || !hidden.value) return;

  function toFilesUrl(path) {
    // Convert a sample URI or absolute path to the /files route.
    if (path.startsWith('ableton:/user-library/')) {
      const rel = path.replace('ableton:/user-library/', 'user-library/');
      return '/files/' + encodeURI(rel);
    }
    const packMatch = path.match(/^ableton:\/packs\/[^/]+\/(.+)$/);
    if (packMatch) {
      return '/files/core-library/' + encodeURI(packMatch[1]);
    }
    if (path.startsWith('/data/UserData/UserLibrary/')) {
      const rel = path.replace('/data/UserData/UserLibrary/', 'user-library/');
      return '/files/' + encodeURI(rel);
    }
    if (path.startsWith('/data/CoreLibrary/')) {
      const rel = path.replace('/data/CoreLibrary/', 'core-library/');
      return '/files/' + encodeURI(rel);
    }
    return null;
  }

  const fileUrl = toFilesUrl(hidden.value.trim());
  if (!fileUrl) return;

  const ws = WaveSurfer.create({
    container: container,
    waveColor: '#888',
    progressColor: '#555',
    height: 64,
    responsive: true,
    normalize: true,
    cursorWidth: 0,
    hideScrollbar: true
  });

  ws.load(fileUrl);
  container.addEventListener('click', (e) => {
    e.stopPropagation();
    ws.stop();
    ws.seekTo(0);
    requestAnimationFrame(() => ws.play(0));
  });
});
