// Modulation matrix UI script
function initModMatrix() {
  const matrixInput = document.getElementById('mod-matrix-data-input');
  const addBtn = document.getElementById('mod-matrix-add');
  const tableBody = document.querySelector('#mod-matrix-table tbody');
  const paramList = JSON.parse(document.getElementById('available-params-input')?.value || '[]');
  const headers = [
    'Amp Env','Env 2','Env 3','LFO 1','LFO 2','Velocity','Key','Pitch Bend','Pressure','Mod Wheel','Random'
  ];
  if (!matrixInput || !tableBody) return;
  let matrix = [];
  try { matrix = JSON.parse(matrixInput.value || '[]'); } catch (e) {}

  function buildSelect(name) {
    const sel = document.createElement('select');
    sel.className = 'mod-dest-select';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = 'Choose…';
    sel.appendChild(opt);
    paramList.forEach(p => {
      const o = document.createElement('option');
      o.value = p;
      o.textContent = p;
      sel.appendChild(o);
    });
    sel.value = name || '';
    return sel;
  }

  function buildRow(row, idx) {
    const tr = document.createElement('tr');
    const tdSel = document.createElement('td');
    const sel = buildSelect(row.name);
    tdSel.appendChild(sel);
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

    sel.addEventListener('change', () => {
      row.name = sel.value;
      save();
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
