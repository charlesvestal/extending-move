export function initSynthKnobs() {
  document.querySelectorAll('.nexus-knob').forEach(el => {
    const min = parseFloat(el.dataset.min);
    const max = parseFloat(el.dataset.max);
    const step = parseFloat(el.dataset.step);
    const targetId = el.dataset.target;
    const target = document.getElementById(targetId);
    const knob = new Nexus.Knob(el, { min, max, step });
    if (target) {
      knob.value = parseFloat(target.value);
      knob.on('change', v => {
        target.value = v;
      });
    }
  });
}
