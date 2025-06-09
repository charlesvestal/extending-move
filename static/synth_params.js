function initNewPresetModal() {
  const modal = document.getElementById('newPresetModal');
  const openBtn = document.getElementById('create-new-btn');
  if (!modal || !openBtn) return;
  const closeBtn = modal.querySelector('.modal-close');
  openBtn.addEventListener('click', (e) => {
    e.preventDefault();
    modal.classList.remove('hidden');
  });
  if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
  window.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });
}

function randomizeParams() {
  const refs = {};
  document.querySelectorAll('.param-item').forEach(item => {
    const param = item.dataset.name;
    const dial = item.querySelector('input.param-dial');
    const select = item.querySelector('select.param-select');
    const toggle = item.querySelector('input.param-toggle');
    const slider = item.querySelector('.rect-slider');

    if (param === 'Mixer_OscillatorOn1') refs.oscOn1 = toggle;
    if (param === 'Mixer_OscillatorOn2') refs.oscOn2 = toggle;
    if (param === 'Mixer_OscillatorGain1') refs.gain1 = dial || slider;
    if (param === 'Mixer_OscillatorGain2') refs.gain2 = dial || slider;
    if (param === 'Filter_Frequency') refs.cutoff = dial || slider;
    if (param === 'Global_Volume') refs.volume = dial || slider;

    if (dial) {
      const min = parseFloat(dial.min || '0');
      const max = parseFloat(dial.max || '1');
      const step = parseFloat(dial.step || '1');
      const unit = dial.dataset.unit || '';
      const shouldScale = unit === '%' && Math.abs(max) <= 1 && Math.abs(min) <= 1;
      let lo = min;
      if (param === 'Mixer_OscillatorGain1' || param === 'Mixer_OscillatorGain2') lo = Math.max(min, 0.3);
      if (param === 'Global_Volume') lo = Math.max(min, 0.4);
      if (param === 'Filter_Frequency') lo = Math.max(min, 100);
      let val = Math.random() * (max - lo) + lo;
      const st = getPercentStep(val, unit, step, shouldScale);
      const q = Math.round((val - min) / st) * st + min;
      dial.value = q;
      dial.dispatchEvent(new Event('input'));
    } else if (select) {
      const opts = Array.from(select.options).map(o => o.value);
      select.value = opts[Math.floor(Math.random() * opts.length)];
      select.dispatchEvent(new Event('change'));
    } else if (toggle) {
      toggle.checked = Math.random() < 0.5;
      toggle.dispatchEvent(new Event('change'));
    } else if (slider) {
      const min = parseFloat(slider.dataset.min || '0');
      const max = parseFloat(slider.dataset.max || '1');
      const step = parseFloat(slider.dataset.step || '1');
      const unit = slider.dataset.unit || '';
      const shouldScale = unit === '%' && Math.abs(max) <= 1 && Math.abs(min) <= 1;
      let lo = min;
      if (param === 'Mixer_OscillatorGain1' || param === 'Mixer_OscillatorGain2') lo = Math.max(min, 0.3);
      if (param === 'Global_Volume') lo = Math.max(min, 0.4);
      if (param === 'Filter_Frequency') lo = Math.max(min, 100);
      let val = Math.random() * (max - lo) + lo;
      const st = getPercentStep(val, unit, step, shouldScale);
      val = Math.round((val - min) / st) * st + min;
      slider.dataset.value = val;
      if (typeof slider._sliderUpdate === 'function') slider._sliderUpdate(val);
    }
  });

  if (refs.oscOn1 && refs.oscOn2 && !refs.oscOn1.checked && !refs.oscOn2.checked) {
    const pick = Math.random() < 0.5 ? refs.oscOn1 : refs.oscOn2;
    pick.checked = true;
    pick.dispatchEvent(new Event('change'));
  }

  const saveBtn = document.getElementById('save-params-btn');
  if (saveBtn) saveBtn.disabled = false;
}

function initRandomizeButton() {
  const btn = document.getElementById('randomize-btn');
  if (btn) btn.addEventListener('click', (e) => {
    e.preventDefault();
    randomizeParams();
  });
}

function initSynthParams() {
  initNewPresetModal();
  initRandomizeButton();
}

document.addEventListener('DOMContentLoaded', initSynthParams);
