document.addEventListener('DOMContentLoaded', () => {
  const paramsData = document.getElementById('effect-params-data');
  if (!paramsData) return;
  const effectParams = JSON.parse(paramsData.value || '{}');

  function updateKnobParamOptions(effectIdx) {
    const params = effectParams[document.getElementById(`effect${effectIdx}`).value] || [];
    document.querySelectorAll(`select.knob-param[data-effect-slot="${effectIdx}"]`).forEach(sel => {
      const cur = sel.value;
      sel.innerHTML = '<option value="">-- Select Parameter --</option>' +
        params.map(p => `<option value="${p}">${p}</option>`).join('');
      if (params.includes(cur)) sel.value = cur;
    });
  }

  for (let i = 1; i <= 4; i++) {
    const sel = document.getElementById(`effect${i}`);
    if (!sel) continue;
    sel.addEventListener('change', () => updateKnobParamOptions(i));
    updateKnobParamOptions(i);
  }

  document.querySelectorAll('.knob-effect').forEach(sel => {
    sel.addEventListener('change', () => {
      const knob = sel.dataset.knob;
      const effectSlot = sel.value || '1';
      const paramSelect = document.querySelector(`select.knob-param[data-knob="${knob}"]`);
      if (paramSelect) {
        paramSelect.setAttribute('data-effect-slot', effectSlot);
        updateKnobParamOptions(effectSlot);
      }
    });
  });
});
