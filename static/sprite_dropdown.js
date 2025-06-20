/* Initialize category + waveform dropdowns for wavetable sprites */
function initSpriteDropdown(catId, waveId, hiddenId, spriteMap, selected) {
  const catSel = document.getElementById(catId);
  const waveSel = document.getElementById(waveId);
  const hidden = document.getElementById(hiddenId);
  if (!catSel || !waveSel || !hidden) return null;

  catSel.classList.add('param-select');
  waveSel.classList.add('param-select');

  const categories = Object.keys(spriteMap);
  const allNames = [];
  categories.forEach(c => { allNames.push(...spriteMap[c]); });

  function fillCategories() {
    catSel.innerHTML = '';
    categories.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      catSel.appendChild(opt);
    });
  }

  function fillWaves(cat) {
    waveSel.innerHTML = '';
    (spriteMap[cat] || []).forEach(w => {
      const opt = document.createElement('option');
      opt.value = w;
      opt.textContent = w;
      waveSel.appendChild(opt);
    });
  }

  const changeListeners = [];

  function setValue(val) {
    let cat = categories.find(c => (spriteMap[c] || []).includes(val));
    if (!cat) cat = categories[0];
    if (catSel.value !== cat) {
      catSel.value = cat;
      fillWaves(cat);
    }
    waveSel.value = val;
    hidden.value = val;
    hidden.dispatchEvent(new Event('change'));
    changeListeners.forEach(fn => {
      try { fn(val); } catch (_) { /* ignore */ }
    });
  }

  fillCategories();
  const initial = selected || hidden.value || (spriteMap[categories[0]] || [])[0] || '';
  let initCat = categories.find(c => (spriteMap[c] || []).includes(initial));
  if (!initCat) initCat = categories[0];
  fillWaves(initCat);
  setValue(initial);

  catSel.addEventListener('change', () => {
    fillWaves(catSel.value);
    setValue(waveSel.value);
  });
  waveSel.addEventListener('change', () => setValue(waveSel.value));

  function onChange(fn) {
    if (typeof fn === 'function') changeListeners.push(fn);
  }

  return { setValue, onChange, options: allNames };
}
if (typeof window !== 'undefined') {
  window.initSpriteDropdown = initSpriteDropdown;
}
