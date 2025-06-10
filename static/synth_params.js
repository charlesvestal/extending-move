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
  const adsrParams = [
    'Envelope1_Attack', 'Envelope1_Decay', 'Envelope1_Release',
    'Envelope2_Attack', 'Envelope2_Decay', 'Envelope2_Release'
  ];
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
    if (param === 'Filter_HiPassFrequency') refs.hicut = dial || slider;
    if (param === 'Filter_Type') refs.ftype = select;
    if (param === 'Global_Volume') refs.volume = dial || slider;

    if (param === 'Global_Volume') {
      const vol = 1.0;
      if (dial) {
        dial.value = vol;
        dial.dispatchEvent(new Event('input'));
      } else if (slider) {
        slider.dataset.value = vol;
        if (typeof slider._sliderUpdate === 'function') slider._sliderUpdate(vol);
      }
      return;
    }

    if (dial) {
      const min = parseFloat(dial.min || '0');
      const max = parseFloat(dial.max || '1');
      const step = parseFloat(dial.step || '1');
      const unit = dial.dataset.unit || '';
      const shouldScale = unit === '%' && Math.abs(max) <= 1 && Math.abs(min) <= 1;
      let lo = min;
      if (param === 'Mixer_OscillatorGain1' || param === 'Mixer_OscillatorGain2') lo = Math.max(min, 0.3);
      if (param === 'Filter_Frequency') lo = Math.max(min, 100);
      let hiCap = max;
      if (param === 'Filter_HiPassFrequency') hiCap = Math.min(max, 1000);
      if (adsrParams.includes(param)) hiCap = Math.min(max, 15);
      let val = Math.random() * (hiCap - lo) + lo;
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
      if (param === 'Filter_Frequency') lo = Math.max(min, 100);
      let hiCapS = max;
      if (param === 'Filter_HiPassFrequency') hiCapS = Math.min(max, 1000);
      if (adsrParams.includes(param)) hiCapS = Math.min(max, 15);
      let val = Math.random() * (hiCapS - lo) + lo;
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

  function getVal(ctrl) {
    if (!ctrl) return 0;
    if (ctrl.classList && ctrl.classList.contains('rect-slider')) {
      return parseFloat(ctrl.dataset.value || '0');
    }
    return parseFloat(ctrl.value || '0');
  }

  function setVal(ctrl, v) {
    if (!ctrl) return;
    if (ctrl.classList && ctrl.classList.contains('rect-slider')) {
      ctrl.dataset.value = v;
      if (typeof ctrl._sliderUpdate === 'function') ctrl._sliderUpdate(v);
    } else {
      ctrl.value = v;
      ctrl.dispatchEvent(new Event('input'));
    }
  }

  if (refs.gain1 || refs.gain2) {
    const g1 = getVal(refs.gain1);
    const g2 = getVal(refs.gain2);
    const maxG = Math.max(g1, g2);
    if (maxG > 0 && maxG !== 1) {
      const factor = 1 / maxG;
      if (refs.gain1) setVal(refs.gain1, Math.min(g1 * factor, 1));
      if (refs.gain2) setVal(refs.gain2, Math.min(g2 * factor, 1));
    }

    const only1 = refs.oscOn1 && refs.oscOn1.checked && (!refs.oscOn2 || !refs.oscOn2.checked);
    const only2 = refs.oscOn2 && refs.oscOn2.checked && (!refs.oscOn1 || !refs.oscOn1.checked);
    if (only1 && refs.gain1) setVal(refs.gain1, 1);
    if (only2 && refs.gain2) setVal(refs.gain2, 1);
  }

  if (refs.cutoff && refs.hicut) {
    let lo = getVal(refs.hicut);
    let hi = getVal(refs.cutoff);
    if (lo >= hi - 50) {
      lo = Math.max(10, hi - 200);
      setVal(refs.hicut, lo);
    }
    if (hi <= lo + 80) {
      hi = lo + 80;
      setVal(refs.cutoff, hi);
    }
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
