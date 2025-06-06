export function initFileBrowser() {
  document.querySelectorAll('.file-browser').forEach(container => {
    const browseUrl = container.dataset.browseUrl || '/browse-dir';
    function bind(span) {
      span.addEventListener('click', async () => {
        const li = span.parentElement;
        const ul = li.querySelector('ul');
        if (!ul) return;
        if (!ul.dataset.loaded) {
          const params = new URLSearchParams({
            root: container.dataset.root,
            path: li.dataset.path || '',
            action_url: container.dataset.action,
            field_name: container.dataset.field,
            action_value: container.dataset.value,
            filter: container.dataset.filter || ''
          });
          const resp = await fetch(`${browseUrl}?${params.toString()}`);
          if (resp.ok) {
            ul.innerHTML = await resp.text();
            ul.dataset.loaded = 'true';
            ul.querySelectorAll('.dir > span').forEach(s => bind(s));
          }
        }
        ul.classList.toggle('hidden');
        li.classList.toggle('open');
        li.classList.toggle('closed');
      });
    }
    container.querySelectorAll('.file-tree.root .dir > span').forEach(bind);
  });
}

document.addEventListener('DOMContentLoaded', initFileBrowser);
