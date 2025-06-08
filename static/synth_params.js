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
  document.querySelectorAll('.param-item').forEach(item => {
    const dial = item.querySelector('input.param-dial');
    const select = item.querySelector('select.param-select');
    const toggle = item.querySelector('input.param-toggle');
    const slider = item.querySelector('.rect-slider');

    if (dial) {
      const min = parseFloat(dial.min || '0');
      const max = parseFloat(dial.max || '1');
      const step = parseFloat(dial.step || '1');
      const unit = dial.dataset.unit || '';
      const shouldScale = unit === '%' && Math.abs(max) <= 1 && Math.abs(min) <= 1;
      const val = Math.random() * (max - min) + min;
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
      let val = Math.random() * (max - min) + min;
      const st = getPercentStep(val, unit, step, shouldScale);
      val = Math.round((val - min) / st) * st + min;
      slider.dataset.value = val;
      if (typeof slider._sliderUpdate === 'function') slider._sliderUpdate(val);
    }
  });
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
