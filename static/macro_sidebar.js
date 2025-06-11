document.addEventListener('DOMContentLoaded', () => {
  const macrosInput = document.getElementById('macros-data-input');
  if (!macrosInput) return;
  const paramPaths = JSON.parse(document.getElementById('param-paths-input').value || '{}');
  const availableParams = JSON.parse(document.getElementById('available-params-input').value || '[]');
  const schema = window.driftSchema || {};
  const paramDisplay = {};
  const paramInfo = {};
  function addSpaces(str) {
    return str
      .replace(/([A-Za-z])([0-9])/g, '$1 $2')
      .replace(/([a-z])([A-Z])/g, '$1 $2');
  }
  function friendly(name) {
    if (!name) return '';
    return name
      .split('_')
      .map(p => addSpaces(p))
      .join(': ');
  }
  availableParams.forEach(p => {
    paramDisplay[p] = friendly(p);
    paramInfo[p] = schema[p] || {};
  });
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
  const addBtn = document.getElementById('macro-add-param');
  const closeBtn = document.getElementById('macro-sidebar-close');

  let openMacro = null;
  let openMacroNew = false;

  function updateAddBtn() {
    if (!openMacro) return;
    addBtn.disabled = openMacro.parameters.length >= availableParams.length;
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
        label.classList.add('placeholder');
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

  function buildParamTree() {
    const tree = {};
    availableParams.forEach(p => {
      const parts = friendly(p).split(':').map(s => s.trim());
      let node = tree;
      for (let i = 0; i < parts.length - 1; i++) {
        const part = parts[i];
        if (!node[part]) node[part] = {};
        node = node[part];
      }
      if (!node._items) node._items = [];
      node._items.push({ value: p, text: parts[parts.length - 1] });
    });
    return tree;
  }

  const paramTree = buildParamTree();

  function buildDropdown(current, onChange) {
    const container = document.createElement('div');
    container.className = 'nested-dropdown';
    const toggle = document.createElement('div');
    toggle.className = 'dropdown-toggle';
    const label = document.createElement('span');
    label.className = 'selected-label';
    const arrow = document.createElement('span');
    arrow.className = 'arrow';
    arrow.innerHTML = '&#9662;';
    toggle.appendChild(label);
    toggle.appendChild(arrow);
    container.appendChild(toggle);
    const menu = document.createElement('div');
    menu.className = 'dropdown-menu';
    menu.style.display = 'none';
    const ulRoot = document.createElement('ul');
    ulRoot.className = 'file-tree root';
    menu.appendChild(ulRoot);
    container.appendChild(menu);
    const hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.value = current || '';
    container.appendChild(hidden);

    function buildMenu(node, ul) {
      Object.keys(node)
        .filter(k => k !== '_items')
        .sort()
        .forEach(k => {
          const li = document.createElement('li');
          li.className = 'dir closed';
          const span = document.createElement('span');
          span.textContent = k;
          const child = document.createElement('ul');
          child.classList.add('hidden');
          buildMenu(node[k], child);
          span.addEventListener('click', e => {
            e.stopPropagation();
            child.classList.toggle('hidden');
            li.classList.toggle('open');
            li.classList.toggle('closed');
          });
          li.appendChild(span);
          li.appendChild(child);
          ul.appendChild(li);
        });
      (node._items || []).forEach(it => {
        const li = document.createElement('li');
        li.className = 'file-entry';
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = it.text;
        btn.addEventListener('click', () => {
          hidden.value = it.value;
          label.textContent = friendly(it.value);
          if (onChange) onChange(it.value);
          close();
        });
        li.appendChild(btn);
        ul.appendChild(li);
      });
    }

    buildMenu(paramTree, ulRoot);

    function updateLabel() {
      label.textContent = hidden.value ? friendly(hidden.value) : 'Choose…';
    }
    updateLabel();

    let open = false;
    function openMenu() {
      menu.style.display = 'block';
      open = true;
    }
    function close() {
      menu.style.display = 'none';
      open = false;
    }
    toggle.addEventListener('click', e => {
      e.stopPropagation();
      open ? close() : openMenu();
    });
    document.addEventListener('click', e => {
      if (open && !container.contains(e.target)) close();
    });

    return container;
  }

  function rebuildLists(macro) {
    assignedDiv.innerHTML = '';
    macro.parameters.forEach((p, idx) => {
      const div = document.createElement('div');
      div.className = 'assign-item';
      const dropdown = buildDropdown(p.name, val => {
        p.name = val;
        p.path = paramPaths[val];
        p.rangeMin = undefined;
        p.rangeMax = undefined;
        rebuildRange();
        updateAddBtn();
        updateHighlights();
        updateKnobLabels();
        saveState();
      });
      const rangeDiv = document.createElement('div');
      rangeDiv.className = 'range-inputs';

      function rebuildRange() {
        rangeDiv.innerHTML = '';
        const info = paramInfo[p.name] || {};
        const isNumber = p.name && (!info.type || info.type === 'number');
        if (!isNumber) return;
        const minInput = document.createElement('input');
        minInput.type = 'text';
        minInput.placeholder = info.min !== undefined && info.min !== null ? info.min : 'min';
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
        maxInput.placeholder = info.max !== undefined && info.max !== null ? info.max : 'max';
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
      }

      rebuildRange();

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = 'Remove';
      btn.addEventListener('click', () => {
        macro.parameters.splice(idx, 1);
        rebuildLists(macro);
        updateHighlights();
        saveState();
      });

      div.appendChild(dropdown);
      if (rangeDiv.childNodes.length) div.appendChild(rangeDiv);
      div.appendChild(btn);
      assignedDiv.appendChild(div);
    });
    updateAddBtn();
  }

  function openSidebar(idx) {
    currentIndex = idx;
    openMacro = macros.find(m => m.index === idx);
    openMacroNew = false;
    if (!openMacro) {
      openMacro = { index: idx, name: "", parameters: [] };
      openMacroNew = true;
    }
    if (openMacro.parameters.length === 0) {
      openMacro.parameters.push({ name: "", path: undefined, rangeMin: undefined, rangeMax: undefined });
    }
    titleEl.textContent = `Knob ${idx + 1}`;
    nameInput.value = openMacro.name || '';
    rebuildLists(openMacro);
    updateAddBtn();
    overlay.classList.remove('hidden');
    sidebar.classList.remove('hidden');
    nameInput.focus();
  }

  function closeSidebar() {
    if (currentIndex !== null && openMacro) {
      openMacro.name = nameInput.value.trim();
      openMacro.parameters = openMacro.parameters.filter(p => p.name);
      const existing = macros.findIndex(m => m.index === openMacro.index);
      if (openMacro.parameters.length === 0 && !openMacro.name) {
        if (existing !== -1) macros.splice(existing, 1);
      } else if (existing === -1) {
        macros.push(openMacro);
      } else {
        macros[existing] = openMacro;
      }
      saveState();
      updateHighlights();
      updateKnobLabels();
    }
    overlay.classList.add('hidden');
    sidebar.classList.add('hidden');
    currentIndex = null;
    openMacro = null;
    openMacroNew = false;
  }

  closeBtn.addEventListener('click', closeSidebar);
  overlay.addEventListener('click', closeSidebar);
  addBtn.addEventListener('click', () => {
    if (currentIndex === null || !openMacro) return;
    openMacro.parameters.push({ name: "", path: undefined, rangeMin: undefined, rangeMax: undefined });
    rebuildLists(openMacro);
    updateAddBtn();
  });

  // Only open the sidebar when the macro name is clicked so that
  // the knob itself can be used without interference.
  document.querySelectorAll('.macro-label').forEach(label => {
    label.addEventListener('click', () => {
      const idx = parseInt(label.dataset.index, 10);
      if (!isNaN(idx)) openSidebar(idx);
    });
  });

  // --- Macro visualization support ---
  const baseParamValues = {};
  document.querySelectorAll('.param-item').forEach(item => {
    const name = item.dataset.name;
    let val = null;
    const hid = item.querySelector('input[type="hidden"][name$="_value"]');
    if (hid) {
      const num = parseFloat(hid.value);
      val = isNaN(num) ? hid.value : num;
    } else {
      const sl = item.querySelector('.rect-slider');
      if (sl) {
        val = parseFloat(sl.dataset.value || '0');
      } else {
        const sel = item.querySelector('select.param-select');
        if (sel) val = sel.value;
      }
    }
    if (name && val !== null) baseParamValues[name] = val;
  });

  function simpleFormat(v, dec) {
    if (isNaN(v)) return 'not set';
    const d = dec === undefined ? 2 : dec;
    return Number(v).toFixed(d);
  }

  function updateParamVisual(name, value) {
    const item = document.querySelector(`.param-item[data-name="${name}"]`);
    if (!item) return;
    const dial = item.querySelector('input.param-dial');
    if (dial) {
      dial.value = value;
      dial.setAttribute('value', value);
      if (dial.inputKnobs && typeof dial.redraw === 'function') dial.redraw(true);
      const dispId = dial.dataset.display;
      if (dispId) {
        const dispEl = document.getElementById(dispId);
        if (dispEl) dispEl.textContent = simpleFormat(value);
      }
      return;
    }
    const select = item.querySelector('select.param-select');
    if (select) {
      select.value = value;
      const hid = item.querySelector('input[type="hidden"][name$="_value"]');
      if (hid) hid.value = value;
      return;
    }
    const slider = item.querySelector('.rect-slider');
    if (slider) {
      const label = slider.querySelector('.rect-slider-label');
      const fill = slider.querySelector('.rect-slider-fill');
      const min = parseFloat(slider.dataset.min || '0');
      const max = parseFloat(slider.dataset.max || '1');
      const centered = slider.classList.contains('center') || slider.dataset.centered === 'true';
      const range = max - min;
      let v = Math.min(Math.max(value, min), max);
      slider.dataset.value = v;
      if (label) label.textContent = simpleFormat(v);
      if (fill) {
        if (centered) {
          const mid = (max + min) / 2;
          if (v >= mid) {
            const pct = (v - mid) / (max - mid);
            fill.style.left = '50%';
            fill.style.width = pct * 50 + '%';
          } else {
            const pct = (mid - v) / (mid - min);
            fill.style.left = 50 - pct * 50 + '%';
            fill.style.width = pct * 50 + '%';
          }
        } else {
          const pct = (v - min) / range;
          fill.style.left = '0%';
          fill.style.width = pct * 100 + '%';
        }
      }
    }
  }

  function applyMacroVisuals() {
    const macroValues = {};
    document.querySelectorAll('input[name^="macro_"][name$="_value"]').forEach(h => {
      const m = h.name.match(/macro_(\d+)_value/);
      if (m) macroValues[parseInt(m[1], 10)] = parseFloat(h.value);
    });

    const mappedNow = new Set();
    macros.forEach(m => {
      const mval = macroValues[m.index] ?? 0;
      (m.parameters || []).forEach(p => {
        const info = paramInfo[p.name] || {};
        if (info.type === 'enum' && Array.isArray(info.options)) {
          const opts = info.options;
          const idx = Math.min(Math.floor((mval / 127) * opts.length), opts.length - 1);
          const val = opts[idx];
          updateParamVisual(p.name, val);
          mappedNow.add(p.name);
          return;
        }
        let min = p.rangeMin !== undefined ? parseFloat(p.rangeMin) : (info.min !== undefined ? parseFloat(info.min) : 0);
        let max = p.rangeMax !== undefined ? parseFloat(p.rangeMax) : (info.max !== undefined ? parseFloat(info.max) : 127);
        const val = min + (max - min) * (mval / 127);
        updateParamVisual(p.name, val);
        mappedNow.add(p.name);
      });
    });

    Object.keys(baseParamValues).forEach(name => {
      if (!mappedNow.has(name)) {
        updateParamVisual(name, baseParamValues[name]);
      }
    });
  }

  macrosInput.addEventListener('change', applyMacroVisuals);
  document.querySelectorAll('.macro-dial').forEach(d => {
    d.addEventListener('input', applyMacroVisuals);
  });

  applyMacroVisuals();

  updateHighlights();
  updateAddBtn();
});
