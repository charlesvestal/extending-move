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

    return container;
  }

  function buildRow(row, idx) {
    const tr = document.createElement('tr');
    const tdSel = document.createElement('td');
    const dropdown = buildDropdown(row.name, val => {
      row.name = val;
      save();
    });
    tdSel.appendChild(dropdown);
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.textContent = 'X';
    removeBtn.addEventListener('click', () => {
      matrix.splice(idx, 1);
      save();
      rebuild();
    });
    tdSel.appendChild(removeBtn);
    tr.appendChild(tdSel);

    row.values = row.values || Array(headers.length).fill(0);
    row.values.forEach((v, col) => {
      const td = document.createElement('td');
      td.className = 'mod-source-cell';
      const slider = document.createElement('div');
      slider.className = 'rect-slider center';
      slider.dataset.min = '-1';
      slider.dataset.max = '1';
      slider.dataset.step = '0.01';
      slider.dataset.value = v;
      slider.addEventListener('change', () => {
        row.values[col] = parseFloat(slider.querySelector('input')?.value || 0);
        save();
      });
      td.appendChild(slider);
      tr.appendChild(td);
    });

    return tr;
  }

  function rebuild() {
    tableBody.innerHTML = '';
    matrix.forEach((row, idx) => {
      tableBody.appendChild(buildRow(row, idx));
    });
    if (window.initRectSliders) window.initRectSliders();
  }

  function save() {
    matrixInput.value = JSON.stringify(matrix);
    matrixInput.dispatchEvent(new Event('change'));
  }

  if (addBtn) {
    addBtn.addEventListener('click', () => {
      matrix.push({ name: '', values: Array(headers.length).fill(0) });
      save();
      rebuild();
    });
  }

  rebuild();
}

document.addEventListener('DOMContentLoaded', initModMatrix);
