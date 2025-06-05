Document.addEventListener('DOMContentLoaded', () => {
  const listEl = document.getElementById('file-list');
  const bcEl = document.getElementById('breadcrumb');
  const wavInput = document.getElementById('wav_file');
  let currentPath = '';

  function load(path) {
    fetch(`${window.location.origin}/reverse/list?path=${encodeURIComponent(path)}`)
      .then(r => r.json())
      .then(data => {
        if (!data.success) {
          alert(data.message || 'Error loading directory');
          return;
        }
        currentPath = data.path || '';
        render(data);
      })
      .catch(err => {
        console.error(err);
        alert('Error loading directory');
      });
  }

  function render(data) {
    bcEl.textContent = '/' + (currentPath || '');
    listEl.innerHTML = '';
    if (currentPath) {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = '#';
      a.textContent = '..';
      a.addEventListener('click', e => {
        e.preventDefault();
        const parent = currentPath.split('/').slice(0, -1).join('/');
        load(parent);
      });
      li.appendChild(a);
      listEl.appendChild(li);
    }
    data.dirs.forEach(d => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = '#';
      a.textContent = d + '/';
      a.addEventListener('click', e => {
        e.preventDefault();
        load(currentPath ? currentPath + '/' + d : d);
      });
      li.appendChild(a);
      listEl.appendChild(li);
    });
    data.files.forEach(f => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = '#';
      a.textContent = f;
      a.addEventListener('click', e => {
        e.preventDefault();
        wavInput.value = currentPath ? currentPath + '/' + f : f;
        const sel = listEl.querySelector('.selected');
        if (sel) sel.classList.remove('selected');
        li.classList.add('selected');
      });
      li.appendChild(a);
      listEl.appendChild(li);
    });
  }

  load('');
});
