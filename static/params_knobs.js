document.addEventListener('DOMContentLoaded', () => {
    function setupControl(el) {
        const target = el.dataset.target;
        const decimals = parseInt(el.dataset.decimals || '2', 10);
        const unit = el.dataset.unit || '';
        const step = parseFloat(el.step || el.dataset.step || '1');
        const percentUnit = unit === '%' || unit === 'ct';
        const displayDecimalsDefault = percentUnit ? 0 : decimals;
        const displayId = el.dataset.display;
        const hidden = document.querySelector(`input[name="${target}"]`);
        const displayEl = displayId ? document.getElementById(displayId) : null;
        const min = parseFloat(el.min);
        const max = parseFloat(el.max);
        const oscGain = unit === 'dB' && !isNaN(min) && !isNaN(max) && min === 0 && max === 2;
        if (oscGain) {
            // allow smooth input; actual rounding happens in handler
            el.step = '0.001';
        }
        const shouldScale = (unit === '%' || unit === 'ct') && Math.abs(max) <= 1 && Math.abs(min) <= 1;
        const getStep = (v) => getPercentStep(v, unit, step, shouldScale);
        const getDisplayDecimals = (v) => getPercentDecimals(v, unit, displayDecimalsDefault, shouldScale);
        const oscValToDb = (val) => {
            if (val <= 0) return -Infinity;
            if (val <= 1) return val * 64 - 64;
            return (val - 1) * 6;
        };
        const dbToOscVal = (db) => {
            if (!isFinite(db) || db <= -64) return 0;
            if (db <= 0) return (db + 64) / 64;
            return 1 + db / 6;
        };
        const format = (v) => {
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
                const db = oscValToDb(v);
                return db.toFixed(1) + ' dB';
            }
            return Number(displayVal).toFixed(getDisplayDecimals(v)) + (unit ? ' ' + unitLabel : '');
        };
        if (displayEl) {
            displayEl.textContent = isNaN(el.value) ? 'not set' : format(parseFloat(el.value));
        }
        if (hidden) {
            el.addEventListener('input', () => {
                let v = parseFloat(el.value);
                let q;
                if (oscGain) {
                    let db = oscValToDb(v);
                    if (isFinite(db)) {
                        db = Math.round(db * 10) / 10;
                        q = dbToOscVal(db);
                    } else {
                        q = 0;
                    }
                } else {
                    const st = getStep(v);
                    q = Math.round((v - min) / st) * st + min;
                }
                hidden.value = q;
                if (displayEl) displayEl.textContent = format(q);
                hidden.dispatchEvent(new Event('change'));
            });
        }
    }

    document.querySelectorAll('input.param-dial').forEach(setupControl);
    document.querySelectorAll('input.param-slider').forEach(setupControl);
    document.querySelectorAll('input.macro-dial').forEach(setupControl);

    // Keep hidden input values in sync with dropdown selections
    document.querySelectorAll('select.param-select').forEach(sel => {
        const hidden = sel.parentElement.querySelector(
            `input[type="hidden"][name="${sel.name}"]`
        );
        if (hidden) {
            sel.addEventListener('change', () => {
                hidden.value = sel.value;
                hidden.dispatchEvent(new Event('change'));
            });
        }
    });

    document.querySelectorAll('input.param-toggle').forEach(el => {
        const target = el.dataset.target;
        const hidden = document.querySelector(`input[name="${target}"]`);
        const trueVal = el.dataset.trueValue ?? '1';
        const falseVal = el.dataset.falseValue ?? '0';
        if (hidden) {
            el.checked = hidden.value === trueVal;
            el.addEventListener('change', () => {
                hidden.value = el.checked ? trueVal : falseVal;
                hidden.dispatchEvent(new Event('change'));
            });
        }
    });

    const env2Input = document.querySelector('.param-item[data-name="Global_Envelope2Mode"] input[type="hidden"]');
    const cyclingRow = document.querySelector('.env2-cycling');
    const adsrRow = document.querySelector('.env2-adsr');
    function updateCycling() {
        if (!env2Input) return;
        const show = env2Input.value === 'Cyc';
        if (cyclingRow) {
            cyclingRow.classList.toggle('hidden', !show);
        }
        if (adsrRow) {
            adsrRow.classList.toggle('hidden', show);
        }
    }
    if (env2Input) {
        env2Input.addEventListener('change', updateCycling);
        updateCycling();
    }

    const modeSelect = document.querySelector('.param-item[data-name="CyclingEnvelope_Mode"] select');
    const cycleRateMap = {
        Freq: document.querySelector('.cycle-rate.freq-rate'),
        Ratio: document.querySelector('.cycle-rate.ratio-rate'),
        Time: document.querySelector('.cycle-rate.time-rate'),
        Sync: document.querySelector('.cycle-rate.sync-rate'),
    };
    function updateCycleRateDisplay() {
        if (!modeSelect) return;
        const mode = modeSelect.value;
        Object.entries(cycleRateMap).forEach(([key, el]) => {
            if (el) el.classList.toggle('hidden', key !== mode);
        });
    }
    if (modeSelect) {
        modeSelect.addEventListener('change', updateCycleRateDisplay);
        updateCycleRateDisplay();
    }

    const lfoModeSelect = document.querySelector('.param-item[data-name="Lfo_Mode"] select');
    const lfoRateMap = {
        Freq: document.querySelector('.lfo-rate.freq-rate'),
        Ratio: document.querySelector('.lfo-rate.ratio-rate'),
        Time: document.querySelector('.lfo-rate.time-rate'),
        Sync: document.querySelector('.lfo-rate.sync-rate'),
    };
    function updateLfoRateDisplay() {
        if (!lfoModeSelect) return;
        const mode = lfoModeSelect.value;
        Object.entries(lfoRateMap).forEach(([key, el]) => {
            if (el) el.classList.toggle('hidden', key !== mode);
        });
    }
    if (lfoModeSelect) {
        lfoModeSelect.addEventListener('change', updateLfoRateDisplay);
        updateLfoRateDisplay();
    }

    document.querySelectorAll('.param-item[data-name^="Voice_Filter"][data-name$="_Type"] select').forEach(sel => {
        const match = sel.parentElement.dataset.name.match(/Voice_Filter(\d)_/);
        if (!match) return;
        const idx = match[1];
        const morphEl = sel.closest('.param-items').querySelector(`.filter${idx}-morph`);
        function updateMorph() {
            if (!morphEl) return;
            const disable = sel.value !== 'Morph';
            const slider = morphEl.querySelector('.rect-slider-container');
            if (slider) {
                slider.classList.toggle('disabled', disable);
                slider.dataset.disabled = disable ? 'true' : 'false';
            }
        }
        sel.addEventListener('change', updateMorph);
        setTimeout(updateMorph, 0);
    });

    // Update oscillator FX knob labels when the effect mode changes
    document.querySelectorAll('.param-item[data-name$="Effects_EffectMode"] select').forEach(sel => {
        const match = sel.parentElement.dataset.name.match(/Voice_Oscillator(\d)_/);
        if (!match) return;
        const idx = match[1];
        const item = sel.closest('.param-items');
        const knob1 = item.querySelector(`.param-item[data-name="Voice_Oscillator${idx}_Effects_Effect1"] .param-label`);
        const knob2 = item.querySelector(`.param-item[data-name="Voice_Oscillator${idx}_Effects_Effect2"] .param-label`);
        const labelMap = {
            'None': ['FX 1', 'FX 2'],
            'Fm': ['Tune', 'Amt'],
            'Classic': ['PW', 'Sync'],
            'Modern': ['Warp', 'Fold'],
        };
        function updateFxLabels() {
            const mode = sel.value;
            const labels = labelMap[mode] || labelMap['None'];
            if (knob1) knob1.textContent = labels[0];
            if (knob2) knob2.textContent = labels[1];
        }
        sel.addEventListener('change', updateFxLabels);
        updateFxLabels();
    });
});
