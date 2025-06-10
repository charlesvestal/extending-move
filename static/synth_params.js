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

  const s1 = document.getElementById('sprite1-select');
  const s2 = document.getElementById('sprite2-select');
  if (s1 && s1.options.length > 0) {
    const opts = Array.from(s1.options).map(o => o.value);
    s1.value = opts[Math.floor(Math.random() * opts.length)];
    s1.dispatchEvent(new Event('change'));
  }
  if (s2 && s2.options.length > 0) {
    const opts = Array.from(s2.options).map(o => o.value);
    s2.value = opts[Math.floor(Math.random() * opts.length)];
    s2.dispatchEvent(new Event('change'));
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

function initRandomNameButtons() {
  const mainBtn = document.getElementById('generate-name-btn');
  const modalBtn = document.getElementById('modal-generate-name-btn');
  const nameInput = document.getElementById('new-preset-name');
  const modalInput = document.querySelector('#newPresetModal input[name="new_preset_name"]');
  const renameCb = document.getElementById('rename-checkbox');

  function ensureRenameChecked() {
    if (renameCb && nameInput) {
      const orig = nameInput.dataset.originalName;
      const changed = nameInput.value.trim() !== orig;
      if (changed !== renameCb.checked) {
        renameCb.checked = changed;
        renameCb.dispatchEvent(new Event('change'));
      }
    }
  }

  if (mainBtn && nameInput) {
    mainBtn.addEventListener('click', (e) => {
      e.preventDefault();
      nameInput.value = generateRandomName();
      nameInput.dispatchEvent(new Event('input'));
      ensureRenameChecked();
    });
  }

  if (modalBtn && modalInput) {
    modalBtn.addEventListener('click', (e) => {
      e.preventDefault();
      modalInput.value = generateRandomName();
    });
  }

  if (nameInput) {
    nameInput.addEventListener('input', ensureRenameChecked);
  }
}

function initSynthParams() {
  initNewPresetModal();
  initRandomizeButton();
  initRandomNameButtons();
}

document.addEventListener('DOMContentLoaded', initSynthParams);
