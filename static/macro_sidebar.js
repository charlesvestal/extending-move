document.addEventListener('DOMContentLoaded', () => {
  const macrosInput = document.getElementById('macros-data-input');
  if (!macrosInput) return;
  const paramPaths = JSON.parse(document.getElementById('param-paths-input').value || '{}');
  const availableParams = JSON.parse(document.getElementById('available-params-input').value || '[]');
  let macros = [];
  try { macros = JSON.parse(macrosInput.value || '[]'); } catch (e) {}

  const overlay = document.getElementById('sidebar-overlay');
  const sidebar = document.getElementById('macro-sidebar');
  const titleEl = document.getElementById('macro-sidebar-title');
  const nameInput = document.getElementById('macro-name-input');
  const assignedDiv = document.querySelector('.macro-assigned-list');
  const selectEl = document.getElementById('macro-param-select');
  const addBtn = document.getElementById('macro-add-param');
  const closeBtn = document.getElementById('macro-sidebar-close');

  function updateAddBtn() {
    addBtn.disabled = !selectEl.value;
  }

  nameInput.addEventListener('input', () => {
    if (currentIndex !== null) {
      const macro = macros.find(m => m.index === currentIndex);
      if (macro) {
        macro.name = nameInput.value.trim() || `Macro ${currentIndex}`;
        const label = document.querySelector(`.macro-label[data-index="${currentIndex}"]`);
        if (label) label.textContent = macro.name;
      }
    }
  });

  function allAssigned() {
    const arr = [];
    macros.forEach(m => m.parameters.forEach(p => arr.push(p.name)));
    return arr;
  }

  let currentIndex = null;

  function saveState() {
    macrosInput.value = JSON.stringify(macros);
    macrosInput.dispatchEvent(new Event('change'));
  }

  function updateKnobLabels() {
    macros.forEach(m => {
      const label = document.querySelector(`.macro-label[data-index="${m.index}"]`);
      if (label) label.textContent = m.name;
    });
  }

  function updateHighlights() {
    document.querySelectorAll('.param-item').forEach(item => {
      const name = item.dataset.name;
      item.classList.remove(...Array.from({length:8},(_,i)=>'macro-'+i));
      for (const m of macros) {
        if (m.parameters.some(p => p.name === name)) {
          item.classList.add('macro-'+m.index);
        }
      }
    });
    document.querySelectorAll('.macro-knob').forEach(knob => {
      const idx = parseInt(knob.dataset.index,10);
      knob.classList.toggle('macro-'+idx, (macros.find(m=>m.index===idx)?.parameters.length||0)>0);
    });
    updateKnobLabels();
  }

  function rebuildLists(macro) {
    assignedDiv.innerHTML = '';
    macro.parameters.forEach(p => {
      const div = document.createElement('div');
      div.className = 'assign-item';
      const span = document.createElement('span');
      span.textContent = p.name;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = 'Remove';
      btn.addEventListener('click', () => {
        macro.parameters = macro.parameters.filter(mp => mp.name !== p.name);
        rebuildLists(macro);
        updateHighlights();
        saveState();
      });
      div.appendChild(span);
      div.appendChild(btn);
      assignedDiv.appendChild(div);
    });

    selectEl.innerHTML = '';
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Choose a parameter...';
    selectEl.appendChild(placeholder);
    const taken = allAssigned();
    availableParams.forEach(p => {
      if (!taken.includes(p)) {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p;
        selectEl.appendChild(opt);
      }
    });
    updateAddBtn();
  }

  function openSidebar(idx) {
    currentIndex = idx;
    let macro = macros.find(m => m.index === idx);
    if (!macro) {
      macro = { index: idx, name: `Macro ${idx}`, parameters: [] };
      macros.push(macro);
    }
    titleEl.textContent = `Macro ${idx}`;
    nameInput.value = macro.name.startsWith('Macro ') ? '' : macro.name;
    rebuildLists(macro);
    updateAddBtn();
    overlay.classList.remove('hidden');
    sidebar.classList.remove('hidden');
    nameInput.focus();
  }

  function closeSidebar() {
    if (currentIndex !== null) {
      const macro = macros.find(m=>m.index===currentIndex);
      if (macro) {
        const name = nameInput.value.trim();
        macro.name = name || `Macro ${currentIndex}`;
      }
      saveState();
      updateHighlights();
      updateKnobLabels();
    }
    overlay.classList.add('hidden');
    sidebar.classList.add('hidden');
    currentIndex = null;
  }

  closeBtn.addEventListener('click', closeSidebar);
  overlay.addEventListener('click', closeSidebar);
  selectEl.addEventListener('change', updateAddBtn);
  addBtn.addEventListener('click', () => {
    if (currentIndex === null) return;
    const macro = macros.find(m => m.index === currentIndex);
    const val = selectEl.value;
    if (val && !macro.parameters.some(p => p.name === val)) {
      macro.parameters.push({ name: val, path: paramPaths[val] });
      rebuildLists(macro);
      updateHighlights();
      saveState();
      updateAddBtn();
    }
  });

  document.querySelectorAll('.macro-label, .macro-knob').forEach(el => {
    el.addEventListener('click', () => {
      const idx = parseInt(el.dataset.index, 10);
      if (!isNaN(idx)) openSidebar(idx);
    });
  });

  updateHighlights();
  updateAddBtn();
});
