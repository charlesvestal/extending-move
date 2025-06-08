document.addEventListener('DOMContentLoaded', () => {
  const macrosInput = document.getElementById('macros-data-input');
  if (!macrosInput) return;
  const paramPaths = JSON.parse(document.getElementById('param-paths-input').value || '{}');
  const availableParams = JSON.parse(document.getElementById('available-params-input').value || '[]');
  const paramDisplay = {};
  function addSpaces(str) {
    return str
      .replace(/([A-Za-z])([0-9])/g, '$1 $2')
      .replace(/([a-z])([A-Z])/g, '$1 $2');
  }
  function friendly(name) {
    if (!name) return '';
    const parts = name.split('_');
    if (parts.length >= 2) {
      const group = addSpaces(parts[0]);
      const rest = addSpaces(parts.slice(1).join('_'));
      return `${group}: ${rest}`;
    }
    return addSpaces(name);
  }
  availableParams.forEach(p => { paramDisplay[p] = friendly(p); });
  let macros = [];
  try { macros = JSON.parse(macrosInput.value || '[]'); } catch (e) {}
  macros.forEach(m => {
    if (/^Macro\s\d+$/.test(m.name)) m.name = '';
  });
  macrosInput.value = JSON.stringify(macros);

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
        macro.name = nameInput.value.trim();
        // Update the knob labels immediately so the fallback
        // parameter name is shown when the input is cleared.
        updateKnobLabels();
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
      if (!label) return;
      label.classList.remove('placeholder');
      let text;
      if (m.name && !/^(Macro|Knob)\s\d+$/.test(m.name)) {
        text = m.name;
      } else if ((m.parameters || []).length === 1) {
        const pname = m.parameters[0].name;
        text = paramDisplay[pname] || pname;
        label.classList.add('placeholder');
      } else {
        text = `Knob ${m.index + 1}`;
      }
      label.textContent = text;
    });
  }

  function updateHighlights() {
    const mapped = {};
    macros.forEach(m => m.parameters.forEach(p => { mapped[p.name] = m.index; }));

    document.querySelectorAll('.param-item').forEach(item => {
      const name = item.dataset.name;
      const idx = mapped[name];
      item.classList.remove('param-mapped', ...Array.from({length:8},(_,i)=>'macro-'+i));
      const isMapped = idx !== undefined;
      if (isMapped) {
        item.classList.add('param-mapped');
        item.classList.add('macro-' + idx);
      }
      item.querySelectorAll('input:not([type=hidden]):not(.macro-dial), select').forEach(inp => {
        inp.disabled = isMapped;
      });
      item.querySelectorAll('.rect-slider').forEach(sl => {
        if (isMapped) {
          sl.classList.add('disabled');
          sl.dataset.disabled = 'true';
        } else {
          sl.classList.remove('disabled');
          delete sl.dataset.disabled;
        }
      });
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
      span.textContent = paramDisplay[p.name] || p.name;
      const rangeDiv = document.createElement('div');
      rangeDiv.className = 'range-inputs';
      const minInput = document.createElement('input');
      minInput.type = 'text';
      minInput.placeholder = 'min';
      if (p.rangeMin !== undefined) {
        const n = parseFloat(p.rangeMin);
        if (!isNaN(n)) minInput.value = n.toFixed(2);
      }
      minInput.addEventListener('change', () => {
        p.rangeMin = minInput.value === '' ? undefined : parseFloat(minInput.value);
        saveState();
      });
      const dash = document.createElement('span');
      dash.textContent = '-';
      const maxInput = document.createElement('input');
      maxInput.type = 'text';
      maxInput.placeholder = 'max';
      if (p.rangeMax !== undefined) {
        const n = parseFloat(p.rangeMax);
        if (!isNaN(n)) maxInput.value = n.toFixed(2);
      }
      maxInput.addEventListener('change', () => {
        p.rangeMax = maxInput.value === '' ? undefined : parseFloat(maxInput.value);
        saveState();
      });
      rangeDiv.appendChild(minInput);
      rangeDiv.appendChild(dash);
      rangeDiv.appendChild(maxInput);
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
      div.appendChild(rangeDiv);
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
        opt.textContent = paramDisplay[p] || p;
        selectEl.appendChild(opt);
      }
    });
    selectEl.selectedIndex = 0;
    updateAddBtn();
  }

  function openSidebar(idx) {
    currentIndex = idx;
    let macro = macros.find(m => m.index === idx);
    if (!macro) {
      macro = { index: idx, name: "", parameters: [] };
      macros.push(macro);
    }
    titleEl.textContent = `Knob ${idx + 1}`;
    nameInput.value = macro.name || '';
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
        macro.name = name;
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
      macro.parameters.push({ name: val, path: paramPaths[val], rangeMin: undefined, rangeMax: undefined });
      rebuildLists(macro);
      updateHighlights();
      saveState();
      updateAddBtn();
    }
  });

  // Only open the sidebar when the macro name is clicked so that
  // the knob itself can be used without interference.
  document.querySelectorAll('.macro-label').forEach(label => {
    label.addEventListener('click', () => {
      const idx = parseInt(label.dataset.index, 10);
      if (!isNaN(idx)) openSidebar(idx);
    });
  });

  updateHighlights();
  updateAddBtn();
});
