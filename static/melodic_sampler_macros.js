// Highlight macro assignments for the melodic sampler editor without applying
// macro values to parameters. Macro knobs are disabled and serve only as labels.

document.addEventListener('DOMContentLoaded', () => {
  const macrosInput = document.getElementById('macros-data-input');
  if (!macrosInput) return;

  let macros = [];
  try { macros = JSON.parse(macrosInput.value || '[]'); } catch (e) {}

  function updateHighlights() {
    const mapped = {};
    macros.forEach(m => (m.parameters || []).forEach(p => { mapped[p.name] = m.index; }));

    document.querySelectorAll('.param-item').forEach(item => {
      const name = item.dataset.name;
      const idx = mapped[name];
      item.classList.remove('param-mapped', ...Array.from({length:8},(_,i)=>'macro-'+i));
      if (idx !== undefined) {
        item.classList.add('param-mapped');
        item.classList.add('macro-' + idx);
      }
    });

    document.querySelectorAll('.macro-knob').forEach(knob => {
      const idx = parseInt(knob.dataset.index, 10);
      const active = (macros.find(m => m.index === idx)?.parameters.length || 0) > 0;
      knob.classList.toggle('macro-' + idx, active);
      const dial = knob.querySelector('.macro-dial');
      if (dial) dial.disabled = true;
    });
  }

  updateHighlights();
});
