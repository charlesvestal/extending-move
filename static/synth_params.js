function initNewPresetModal() {
  const modal = document.getElementById('newPresetModal');
  const openBtn = document.getElementById('create-new-btn');
  if (!modal || !openBtn) return;
  const closeBtn = modal.querySelector('.modal-close');
  const modalInput = modal.querySelector('input[name="new_preset_name"]');
  openBtn.addEventListener('click', (e) => {
    e.preventDefault();
    if (modalInput) modalInput.value = generateRandomName();
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
      const percentUnit = unit === '%' || unit === 'ct';
      const baseScale = percentUnit && Math.abs(max) <= 1 && Math.abs(min) <= 1 ? 100 : 1;
      const displayScale = parseFloat(dial.dataset.displayScale || baseScale);
      const shouldScale = displayScale !== 1;
      const val = Math.random() * (max - min) + min;
      const st = getPercentStep(val, unit, step, shouldScale, displayScale);
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
      const percentUnit = unit === '%' || unit === 'ct';
      const baseScale = percentUnit && Math.abs(max) <= 1 && Math.abs(min) <= 1 ? 100 : 1;
      const displayScale = parseFloat(slider.dataset.displayScale || baseScale);
      const shouldScale = displayScale !== 1;
      let val = Math.random() * (max - min) + min;
      const st = getPercentStep(val, unit, step, shouldScale, displayScale);
      val = Math.round((val - min) / st) * st + min;
      slider.dataset.value = val;
      if (typeof slider._sliderUpdate === 'function') slider._sliderUpdate(val);
    }
  });

  const sprites = window.spriteDropdowns || {};
  if (sprites.sprite1) {
    const opts = sprites.sprite1.options;
    sprites.sprite1.setValue(opts[Math.floor(Math.random() * opts.length)]);
  }
  if (sprites.sprite2) {
    const opts = sprites.sprite2.options;
    sprites.sprite2.setValue(opts[Math.floor(Math.random() * opts.length)]);
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

function generateRandomName() {
  const adjectives = [
    'Fluffy', 'Spicy', 'Zesty', 'Creamy', 'Crunchy', 'Savory', 'Sweet',
    'Tangy', 'Juicy', 'Smoky', 'Fiery', 'Buttery', 'Tender', 'Crispy',
    'Silky', 'Gooey', 'Fruity', 'Saucy', 'Glazed', 'Wholesome',
    'Bouncy', 'Chilled', 'Crumbly', 'Delightful', 'Earthy', 'Fizzy',
    'Garlicky', 'Hearty', 'Icy', 'Jumbo', 'Luscious', 'Minty', 'Nutty',
    'Peppy', 'Quirky', 'Roasted', 'Sugary', 'Toasty', 'Velvety', 'Zingy'
  ];
  const foods = [
    'Cheeseburger', 'Pizza', 'Tiramisu', 'Sushi', 'Pancake', 'Brownie',
    'Curry', 'Taco', 'Donut', 'Risotto', 'Ramen', 'Gnocchi', 'Quiche',
    'Falafel', 'Burrito', 'Lasagna', 'Muffin', 'Chowder', 'Waffle', 'Scone',
    'Omelette', 'Pasta', 'Cupcake', 'Cookie', 'Gelato', 'Bagel', 'Samosa',
    'Dumpling', 'Paella', 'Kebab', 'Steak', 'Salad', 'Stew', 'Poutine',
    'Croissant', 'Baguette', 'Frittata', 'Pudding', 'Sandwich', 'Chili'
  ];
  const adj = adjectives[Math.floor(Math.random() * adjectives.length)];
  const food = foods[Math.floor(Math.random() * foods.length)];
  return `${adj} ${food}`;
}

function initRandomNameFields() {
  const nameInput = document.getElementById('new-preset-name');
  const renameCb = document.getElementById('rename-checkbox');

  function ensureRenameChecked() {
    if (renameCb && nameInput) {
      const origBase = nameInput.dataset.originalBase || nameInput.dataset.originalName.replace(/\.[^.]+$/, '');
      const changed = nameInput.value.trim() !== origBase;
      if (changed !== renameCb.checked) {
        renameCb.checked = changed;
        renameCb.dispatchEvent(new Event('change'));
      }
    }
  }

  if (renameCb && nameInput) {
    renameCb.addEventListener('change', () => {
      nameInput.disabled = !renameCb.checked;
      if (renameCb.checked) {
        const origBase = nameInput.dataset.originalBase || nameInput.dataset.originalName.replace(/\.[^.]+$/, '');
        if (nameInput.value.trim() === origBase) {
          nameInput.value = generateRandomName();
          nameInput.dispatchEvent(new Event('input'));
        }
      } else {
        const origBase = nameInput.dataset.originalBase || nameInput.dataset.originalName.replace(/\.[^.]+$/, '');
        if (nameInput.value !== origBase) {
          nameInput.value = origBase;
          nameInput.dispatchEvent(new Event('input'));
        }
      }
    });
    nameInput.addEventListener('input', ensureRenameChecked);
  }
}

function initSynthParams() {
  initNewPresetModal();
  initRandomizeButton();
  initRandomNameFields();
}

document.addEventListener('DOMContentLoaded', initSynthParams);
