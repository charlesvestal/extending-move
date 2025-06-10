/* Nested dropdown for wavetable sprites */
function initSpriteDropdown(containerId, hiddenId, spriteMap, selected) {
  const container = document.getElementById(containerId);
  const hidden = document.getElementById(hiddenId);
  if (!container || !hidden) return null;

  const allNames = [];
  Object.values(spriteMap).forEach(arr => { allNames.push(...arr); });

  container.classList.add('nested-dropdown');
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

  function buildMenu() {
    Object.keys(spriteMap).forEach(cat => {
      const li = document.createElement('li');
      li.className = 'dir closed';
      const span = document.createElement('span');
      span.textContent = cat;
      const child = document.createElement('ul');
      child.classList.add('hidden');
      spriteMap[cat].forEach(name => {
        const li2 = document.createElement('li');
        li2.className = 'file-entry';
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = name;
        btn.addEventListener('click', () => {
          setValue(name);
          close();
        });
        li2.appendChild(btn);
        child.appendChild(li2);
      });
      span.addEventListener('click', e => {
        e.stopPropagation();
        child.classList.toggle('hidden');
        li.classList.toggle('open');
        li.classList.toggle('closed');
      });
      li.appendChild(span);
      li.appendChild(child);
      ulRoot.appendChild(li);
    });
  }

  function setValue(val) {
    hidden.value = val;
    label.textContent = val || 'Choose…';
    hidden.dispatchEvent(new Event('change'));
  }

  buildMenu();
  setValue(selected || hidden.value || '');

  let open = false;
  function openMenu() { menu.style.display = 'block'; open = true; }
  function close() { menu.style.display = 'none'; open = false; }
  toggle.addEventListener('click', e => { e.stopPropagation(); open ? close() : openMenu(); });
  document.addEventListener('click', e => { if (open && !container.contains(e.target)) close(); });

  return { setValue, options: allNames };
}
if (typeof window !== 'undefined') {
  window.initSpriteDropdown = initSpriteDropdown;
}
