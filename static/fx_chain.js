document.addEventListener('DOMContentLoaded', () => {
  const dataEl = document.getElementById('fx-presets-data');
  if (!dataEl) return;
  const fxPresets = JSON.parse(dataEl.value || '{}');

  function getParams(effectIdx) {
    const kindSel = document.getElementById(`effect${effectIdx}`);
    const presetSel = document.getElementById(`effect${effectIdx}_preset`);
    const kind = kindSel ? kindSel.value : '';
    const presetName = presetSel ? presetSel.options[presetSel.selectedIndex]?.text : '';
    if (kind && presetName && fxPresets[kind] && fxPresets[kind][presetName]) {
      return fxPresets[kind][presetName].parameters;
    }
    return null;
  }

  function updatePresetOptions(effectIdx) {
    const presetSel = document.getElementById(`effect${effectIdx}_preset`);
    if (!presetSel) return;
    const kind = document.getElementById(`effect${effectIdx}`).value;
    presetSel.innerHTML = '<option value="">-- Select Preset --</option>';
    if (fxPresets[kind]) {
      Object.keys(fxPresets[kind]).sort().forEach(name => {
        const path = fxPresets[kind][name].path;
        presetSel.innerHTML += `<option value="${path}">${name}</option>`;
      });
    }
    updateParams(effectIdx);
    updateKnobParamOptions(effectIdx);
  }

  function updateParams(effectIdx) {
    const params = getParams(effectIdx);
    const container = document.getElementById(`effect${effectIdx}_params`);
    if (!container) return;
    container.innerHTML = '';
    if (!params) return;
    Object.keys(params).forEach(name => {
      const val = params[name];
      container.innerHTML += `<label>${name}: <input type="text" name="effect${effectIdx}_param_${name}" value="${val}"></label><br>`;
    });
  }

  function updateKnobParamOptions(effectIdx) {
    const params = getParams(effectIdx);
    const names = params ? Object.keys(params) : [];
    document.querySelectorAll(`select.knob-param[data-effect-slot="${effectIdx}"]`).forEach(sel => {
      const cur = sel.value;
      sel.innerHTML = '<option value="">-- Select Parameter --</option>' +
        names.map(p => `<option value="${p}">${p}</option>`).join('');
      if (names.includes(cur)) sel.value = cur;
    });
  }

  for (let i = 1; i <= 4; i++) {
    const eSel = document.getElementById(`effect${i}`);
    const pSel = document.getElementById(`effect${i}_preset`);
    if (eSel) eSel.addEventListener('change', () => updatePresetOptions(i));
    if (pSel) pSel.addEventListener('change', () => { updateParams(i); updateKnobParamOptions(i); });
    updatePresetOptions(i);
  }

  document.querySelectorAll('.knob-effect').forEach(sel => {
    sel.addEventListener('change', () => {
      const knob = sel.dataset.knob;
      const slot = sel.value || '1';
      const paramSelect = document.querySelector(`select.knob-param[data-knob="${knob}"]`);
      if (paramSelect) {
        paramSelect.setAttribute('data-effect-slot', slot);
        updateKnobParamOptions(slot);
      }
    });
  });
});
