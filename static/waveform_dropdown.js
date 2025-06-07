document.addEventListener('DOMContentLoaded', () => {
  const dropdown = document.getElementById('waveformDropdown');
  if (!dropdown) return;

  const toggle = dropdown.querySelector('.dropdown-toggle');
  const menu = dropdown.querySelector('.dropdown-menu');
  const options = Array.from(menu.querySelectorAll('li'));

  let selected = options.find(opt => opt.dataset.waveform === 'sine');
  let focusedIndex = 0;

  function closeMenu() {
    menu.style.display = 'none';
    toggle.setAttribute('aria-expanded', 'false');
  }

  function openMenu() {
    menu.style.display = 'block';
    toggle.setAttribute('aria-expanded', 'true');
    menu.focus();
  }

  function updateSelection(option) {
    selected = option;
    const use = toggle.querySelector('use');
    const newHref = `${use.getAttribute('xlink:href').split('#')[0]}#${option.dataset.waveform}`;
    use.setAttribute('xlink:href', newHref);
    toggle.querySelector('.visually-hidden').textContent = option.querySelector('.visually-hidden').textContent;
    options.forEach(opt => opt.removeAttribute('aria-selected'));
    option.setAttribute('aria-selected', 'true');
  }

  toggle.addEventListener('click', (e) => {
    e.preventDefault();
    if (menu.style.display === 'block') {
      closeMenu();
    } else {
      openMenu();
    }
  });

  options.forEach((opt, idx) => {
    opt.addEventListener('click', () => {
      updateSelection(opt);
      closeMenu();
      toggle.focus();
    });
    if (opt.dataset.waveform === 'sine') {
      opt.setAttribute('aria-selected', 'true');
      focusedIndex = idx;
    }
  });

  menu.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      focusedIndex = (focusedIndex + 1) % options.length;
      options[focusedIndex].focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      focusedIndex = (focusedIndex - 1 + options.length) % options.length;
      options[focusedIndex].focus();
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      updateSelection(options[focusedIndex]);
      closeMenu();
      toggle.focus();
    } else if (e.key === 'Escape') {
      closeMenu();
      toggle.focus();
    }
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
      closeMenu();
    }
  });
});
