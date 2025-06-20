// Modulation matrix UI script
function initModMatrix() {
  const matrixInput = document.getElementById('mod-matrix-data-input');
  const addBtn = document.getElementById('mod-matrix-add');
  const tableBody = document.querySelector('#mod-matrix-table tbody');
  const paramList = JSON.parse(document.getElementById('available-params-input')?.value || '[]');
  const headers = [
    'Amp','Env 2','Env 3','LFO 1','LFO 2','Velocity','Key','PB','Press','Mod','Rand'
  ];
  if (!matrixInput || !tableBody) return;
  let matrix = [];
  try { matrix = JSON.parse(matrixInput.value || '[]'); } catch (e) {}

  function addSpaces(str) {
    return str
      .replace(/([A-Za-z])([0-9])/g, '$1 $2')
      .replace(/([a-z])([A-Z])/g, '$1 $2');
  }

  function friendly(n) {
    if (!n) return '';
    return n.split('_').map(p => addSpaces(p)).join(': ');
  }

  function buildParamTree() {
    const tree = {};
    paramList.forEach(p => {
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

  function buildValueSlider(paramName) {
    if (!paramName) return null;
    const item = document.querySelector(`.param-item[data-name="${paramName}"]`);
    const hidden = item?.querySelector('input[type="hidden"][name^="param_"][name$="_value"]');
    const srcSlider = item?.querySelector('.rect-slider');
    const dial = item?.querySelector('input.param-dial');
    const slider = document.createElement('div');
    slider.className = 'rect-slider center mod-dest-value';
    slider.dataset.disabled = 'true';
    slider.classList.add('disabled');
    if (srcSlider) {
      if (srcSlider.dataset.min) slider.dataset.min = srcSlider.dataset.min;
      if (srcSlider.dataset.max) slider.dataset.max = srcSlider.dataset.max;
      if (srcSlider.dataset.step) slider.dataset.step = srcSlider.dataset.step;
      if (srcSlider.dataset.decimals) slider.dataset.decimals = srcSlider.dataset.decimals;
      if (srcSlider.dataset.unit) slider.dataset.unit = srcSlider.dataset.unit;
      if (srcSlider.classList.contains('center')) slider.classList.add('center');
    } else if (dial) {
      if (dial.min) slider.dataset.min = dial.min;
      if (dial.max) slider.dataset.max = dial.max;
      if (dial.step) slider.dataset.step = dial.step;
      if (dial.dataset.decimals) slider.dataset.decimals = dial.dataset.decimals;
      if (dial.dataset.unit) slider.dataset.unit = dial.dataset.unit;
    }
    slider.dataset.value = hidden ? hidden.value : '0';
    if (window.initRectSlider) window.initRectSlider(slider);
    if (hidden) {
      const update = () => {
        if (typeof slider._sliderUpdate === 'function') {
          slider._sliderUpdate(hidden.value);
        }
      };
      hidden.addEventListener('change', update);
    }
    return slider;
  }

  function buildDropdown(name, onChange) {
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
    hidden.value = name || '';
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

    container._close = close;
    return container;
  }

  function buildRow(row, idx) {
    const tr = document.createElement('tr');
    const tdSel = document.createElement('td');
    let valueSlider = null;
    function attachValueSlider(name) {
      if (valueSlider && valueSlider.parentElement) {
        valueSlider.parentElement.removeChild(valueSlider);
      }
      valueSlider = buildValueSlider(name);
      if (valueSlider) tdSel.appendChild(valueSlider);
    }
    const dropdown = buildDropdown(row.name, val => {
      row.name = val;
      save();
      attachValueSlider(val);
    });
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.textContent = 'X';
    removeBtn.className = 'close-x'; // Add this line
    removeBtn.addEventListener('click', () => {
      matrix.splice(idx, 1);
      save();
      rebuild();
    });
    tdSel.appendChild(removeBtn);
    tdSel.appendChild(dropdown);
    attachValueSlider(row.name);
    tr.appendChild(tdSel);

    row.values = row.values || Array(headers.length).fill(0);
    row.extra = row.extra || [];
    row.values.forEach((v, col) => {
      const td = document.createElement('td');
      td.className = 'mod-source-cell';
      const slider = document.createElement('div');
      slider.className = 'rect-slider center';
      slider.dataset.min = '-1';
      slider.dataset.max = '1';
      slider.dataset.step = '0.01';
      slider.dataset.value = v;

      const hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.value = v;
      const hidId = `mod-mtx-${idx}-${col}`;
      hidden.id = hidId;
      slider.dataset.target = hidId;

      hidden.addEventListener('change', () => {
        row.values[col] = parseFloat(hidden.value || 0);
        save();
      });

      td.appendChild(slider);
      td.appendChild(hidden);
      tr.appendChild(td);
    });

    return tr;
  }

  function collapseAllDropdowns() {
    tableBody.querySelectorAll('.nested-dropdown').forEach(dd => {
      if (typeof dd._close === 'function') dd._close();
    });
  }

  function rebuild() {
    tableBody.innerHTML = '';
    matrix.forEach((row, idx) => {
      tableBody.appendChild(buildRow(row, idx));
    });
    if (window.initRectSliders) window.initRectSliders();
    collapseAllDropdowns();
  }

  function save() {
    matrixInput.value = JSON.stringify(matrix);
    matrixInput.dispatchEvent(new Event('change'));
  }

  if (addBtn) {
    addBtn.addEventListener('click', () => {
      matrix.push({ name: '', values: Array(headers.length).fill(0), extra: [] });
      save();
      rebuild();
    });
  }

  rebuild();
}

document.addEventListener('DOMContentLoaded', initModMatrix);
