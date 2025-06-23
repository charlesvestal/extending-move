document.addEventListener('DOMContentLoaded', () => {
  const dataEl = document.getElementById('effects-data');
  if (!dataEl) return;
  const mapping = JSON.parse(dataEl.textContent || '{}');
  for (let i = 0; i < 4; i++) {
    const eff = document.getElementById(`effect_${i}`);
    const param = document.getElementById(`macro_${i}_param`);
    if (!eff || !param) continue;
    function update() {
      const params = mapping[eff.value] || [];
      param.innerHTML = '<option value="">--None--</option>';
      params.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p;
        param.appendChild(opt);
      });
    }
    eff.addEventListener('change', update);
    update();
  }
});
