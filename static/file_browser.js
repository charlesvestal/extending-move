export function initFileBrowser() {
  document.querySelectorAll('.file-tree .dir > span').forEach(el => {
    el.addEventListener('click', () => {
      const next = el.nextElementSibling;
      if (next) {
        next.classList.toggle('hidden');
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', initFileBrowser);
