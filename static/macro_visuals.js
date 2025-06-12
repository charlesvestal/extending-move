// Derived from macro_sidebar.js without sidebar editing features
// Handles highlighting of mapped parameters and applying macro knob values
// to parameter controls for pages where macros are fixed.

document.addEventListener('DOMContentLoaded', () => {
  const macrosInput = document.getElementById('macros-data-input');
  if (!macrosInput) return;

  const paramPaths = JSON.parse(document.getElementById('param-paths-input').value || '{}');
  const availableParams = JSON.parse(document.getElementById('available-params-input').value || '[]');
  const schema = window.driftSchema || {};

  const paramInfo = {};
  availableParams.forEach(p => { paramInfo[p] = schema[p] || {}; });

  let macros = [];
  try { macros = JSON.parse(macrosInput.value || '[]'); } catch (e) {}

  // Capture base parameter values so they can be restored when macros change
  const baseParamValues = {};
  document.querySelectorAll('.param-item').forEach(item => {
    const name = item.dataset.name;
    let val = null;
    const hid = item.querySelector('input[type="hidden"][name$="_value"]');
    if (hid) {
      const num = parseFloat(hid.value);
      val = isNaN(num) ? hid.value : num;
    } else {
      const sl = item.querySelector('.rect-slider');
      if (sl) {
        val = parseFloat(sl.dataset.value || '0');
      } else {
        const sel = item.querySelector('select.param-select');
        if (sel) val = sel.value;
      }
    }
    if (name && val !== null) baseParamValues[name] = val;

    function getCurrent() {
      let cur = null;
      const hid = item.querySelector('input[type="hidden"][name$="_value"]');
      if (hid) {
        const num = parseFloat(hid.value);
        cur = isNaN(num) ? hid.value : num;
      } else {
        const sl = item.querySelector('.rect-slider');
        if (sl) {
          cur = parseFloat(sl.dataset.value || '0');
        } else {
          const sel = item.querySelector('select.param-select');
          if (sel) cur = sel.value;
        }
      }
      return cur;
    }

    function updateBase() {
      const v = getCurrent();
      if (v !== null) baseParamValues[name] = v;
    }

    item.querySelectorAll('input.param-dial, input.param-slider, input.param-toggle, select.param-select, .rect-slider').forEach(ctrl => {
      ctrl.addEventListener('input', updateBase);
      ctrl.addEventListener('change', updateBase);
    });
  });

  function formatDialValue(dial, v) {
    if (isNaN(v)) return 'not set';
    const valueLabels = dial.dataset.values ? dial.dataset.values.split(',') : null;
    if (valueLabels) {
      const idx = Math.round(v);
      if (idx >= 0 && idx < valueLabels.length) {
        return valueLabels[idx];
      }
    }
    const unit = dial.dataset.unit || '';
    const decimals = parseInt(dial.dataset.decimals || '2', 10);
    const min = parseFloat(dial.min || '0');
    const max = parseFloat(dial.max || '0');
    const oscGain = unit === 'dB' && !isNaN(min) && !isNaN(max) && min === 0 && max <= 2;
    const shouldScale = (unit === '%' || unit === 'ct') && Math.abs(max) <= 1 && Math.abs(min) <= 1;
    const displayDecimalsDefault = (unit === '%' || unit === 'ct') ? 0 : decimals;
    const getDisplayDecimals = (val) => window.getPercentDecimals(val, unit, displayDecimalsDefault, shouldScale);

    let displayVal = shouldScale ? v * 100 : v;
    let unitLabel = unit;
    if (unit === 'Hz') {
      displayVal = Number(displayVal);
      if (displayVal >= 1000) {
        displayVal = displayVal / 1000;
        unitLabel = 'kHz';
      }
      return displayVal.toFixed(1) + ' ' + unitLabel;
    } else if (unit === 's') {
      if (displayVal < 1) {
        return (displayVal * 1000).toFixed(0) + ' ms';
      }
      return Number(displayVal).toFixed(getDisplayDecimals(v)) + ' s';
    } else if (oscGain) {
      if (v <= 0) return '-inf dB';
      const oscValToDb = (val) => {
        if (val <= 0) return -Infinity;
        if (val <= 1) return val * 64 - 64;
        return (val - 1) * 6;
      };
      const db = oscValToDb(v);
      return db.toFixed(1) + ' dB';
    }
    return Number(displayVal).toFixed(getDisplayDecimals(v)) + (unit ? ' ' + unitLabel : '');
  }

  function updateParamVisual(name, value) {
    const item = document.querySelector(`.param-item[data-name="${name}"]`);
    if (!item) return;
    const dial = item.querySelector('input.param-dial');
    if (dial) {
      dial.value = value;
      dial.setAttribute('value', value);
      if (dial.inputKnobs && typeof dial.redraw === 'function') dial.redraw(true);
      const dispId = dial.dataset.display;
      if (dispId) {
        const dispEl = document.getElementById(dispId);
        if (dispEl) dispEl.textContent = formatDialValue(dial, value);
      }
      const target = dial.dataset.target;
      if (target) {
        const hidden = document.querySelector(`input[name="${target}"]`);
        if (hidden) {
          hidden.value = value;
          hidden.dispatchEvent(new Event('change'));
        }
      }
      dial.dispatchEvent(new Event('input'));
      return;
    }
    const select = item.querySelector('select.param-select');
    if (select) {
      select.value = value;
      const hid = item.querySelector('input[type="hidden"][name$="_value"]');
      if (hid) hid.value = value;
      select.dispatchEvent(new Event('change'));
      return;
    }
    const toggle = item.querySelector('input.param-toggle');
    if (toggle) {
      const hid = item.querySelector('input[type="hidden"][name$="_value"]');
      const trueVal = toggle.dataset.trueValue ?? '1';
      const falseVal = toggle.dataset.falseValue ?? '0';
      const isOn = String(value) === trueVal || (!isNaN(value) && parseFloat(value) >= 1);
      toggle.checked = isOn;
      if (hid) {
        hid.value = isOn ? trueVal : falseVal;
        hid.dispatchEvent(new Event('change'));
      }
      toggle.dispatchEvent(new Event('change'));
      return;
    }
    const slider = item.querySelector('.rect-slider');
    if (slider) {
      if (typeof slider._sliderUpdate === 'function') {
        slider._sliderUpdate(value);
      }
      slider.dispatchEvent(new Event('input'));
    }
  }

  function applyMacroVisuals(targetIndices = null) {
    const indicesToProcess = new Set();
    if (targetIndices !== null) {
      (Array.isArray(targetIndices) ? targetIndices : [targetIndices]).forEach(i => indicesToProcess.add(i));
    }

    const macroValues = {};
    document.querySelectorAll('input[name^="macro_"][name$="_value"]').forEach(h => {
      const m = h.name.match(/macro_(\d+)_value/);
      if (m) macroValues[parseInt(m[1], 10)] = parseFloat(h.value);
    });

    const mappedNow = new Set();
    macros.forEach(m => {
      if (indicesToProcess.size && !indicesToProcess.has(m.index)) return;
      const mval = macroValues[m.index] ?? 0;
      (m.parameters || []).forEach(p => {
        const info = paramInfo[p.name] || {};
        if (info.type === 'enum' && Array.isArray(info.options)) {
          const opts = info.options;
          const idx = Math.min(Math.floor((mval / 127) * opts.length), opts.length - 1);
          const val = opts[idx];
          updateParamVisual(p.name, val);
          mappedNow.add(p.name);
          return;
        } else if (info.type === 'boolean') {
          const val = mval >= 64 ? 1 : 0;
          updateParamVisual(p.name, val);
          mappedNow.add(p.name);
          return;
        }
        let min = p.rangeMin !== undefined ? parseFloat(p.rangeMin) : (info.min !== undefined ? parseFloat(info.min) : 0);
        let max = p.rangeMax !== undefined ? parseFloat(p.rangeMax) : (info.max !== undefined ? parseFloat(info.max) : 127);
        const val = min + (max - min) * (mval / 127);
        updateParamVisual(p.name, val);
        mappedNow.add(p.name);
      });
    });

    if (!indicesToProcess.size) {
      Object.keys(baseParamValues).forEach(name => {
        if (!mappedNow.has(name)) {
          updateParamVisual(name, baseParamValues[name]);
        }
      });
    }
  }

  function updateHighlights() {
    const mapped = {};
    macros.forEach(m => m.parameters.forEach(p => { mapped[p.name] = m.index; }));

    document.querySelectorAll('.param-item').forEach(item => {
      const name = item.dataset.name;
      const idx = mapped[name];
      item.classList.remove('param-mapped', ...Array.from({length:8},(_,i)=>'macro-'+i));
      const isMapped = idx !== undefined;
      if (isMapped) {
        item.classList.add('param-mapped');
        item.classList.add('macro-' + idx);
      }
    });

    document.querySelectorAll('.macro-knob').forEach(knob => {
      const idx = parseInt(knob.dataset.index,10);
      knob.classList.toggle('macro-'+idx, (macros.find(m=>m.index===idx)?.parameters.length||0)>0);
    });
  }

  macrosInput.addEventListener('change', () => {
    try { macros = JSON.parse(macrosInput.value || '[]'); } catch (e) {}
    applyMacroVisuals();
    updateHighlights();
  });

  document.querySelectorAll('.macro-dial').forEach(d => {
    d.addEventListener('input', () => {
      const m = d.dataset.target.match(/macro_(\d+)_value/);
      const idx = m ? parseInt(m[1], 10) : NaN;
      applyMacroVisuals(idx);
    });
  });

  applyMacroVisuals();
  updateHighlights();
});

