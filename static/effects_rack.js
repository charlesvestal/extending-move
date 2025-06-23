document.addEventListener('DOMContentLoaded', () => {
  const dataEl = document.getElementById('effects-data');
  if (!dataEl) return;
  const mapping = JSON.parse(dataEl.textContent || '{}');
  for (let i = 0; i < 4; i++) {
    const deviceSel = document.getElementById(`effect_${i}`);
    const paramSel = document.getElementById(`macro_${i}_param`);
    if (!deviceSel || !paramSel) continue;
    function update() {
      const params = mapping[deviceSel.value] || [];
      paramSel.innerHTML = '<option value="">--None--</option>';
      params.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p;
        paramSel.appendChild(opt);
      });
    }
    deviceSel.addEventListener('change', update);
    update();
  }
});
