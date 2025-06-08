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
  const listDiv = document.querySelector('.macro-params-list');
  const closeBtn = document.getElementById('macro-sidebar-close');

  let currentIndex = null;

  function saveState() {
    macrosInput.value = JSON.stringify(macros);
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
  }

  function openSidebar(idx) {
    currentIndex = idx;
    const macro = macros.find(m=>m.index===idx) || {index: idx, name: `Macro ${idx}`, parameters: []};
    if (!macros.find(m=>m.index===idx)) macros.push(macro);
    titleEl.textContent = `Macro ${idx}`;
    nameInput.value = macro.name.startsWith('Macro ') ? '' : macro.name;
    listDiv.innerHTML = '';
    availableParams.forEach(p => {
      const div = document.createElement('div');
      div.className = 'map-item';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = macro.parameters.some(mp=>mp.name===p);
      cb.addEventListener('change', () => {
        if (cb.checked) {
          if (!macro.parameters.some(mp=>mp.name===p)) {
            macro.parameters.push({name:p, path:paramPaths[p]});
          }
        } else {
          macro.parameters = macro.parameters.filter(mp=>mp.name!==p);
        }
        updateHighlights();
        saveState();
      });
      const label = document.createElement('label');
      label.textContent = p;
      div.appendChild(cb);
      div.appendChild(label);
      listDiv.appendChild(div);
    });
    overlay.classList.remove('hidden');
    sidebar.classList.remove('hidden');
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
    }
    overlay.classList.add('hidden');
    sidebar.classList.add('hidden');
    currentIndex = null;
  }

  closeBtn.addEventListener('click', closeSidebar);
  overlay.addEventListener('click', closeSidebar);

  document.querySelectorAll('.macro-label').forEach(lbl => {
    lbl.addEventListener('click', () => {
      const idx = parseInt(lbl.dataset.index, 10);
      openSidebar(idx);
    });
  });

  updateHighlights();
});
