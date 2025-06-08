document.addEventListener('DOMContentLoaded', () => {
    function setupControl(el) {
        const target = el.dataset.target;
        const decimals = parseInt(el.dataset.decimals || '2', 10);
        const unit = el.dataset.unit || '';
        const displayDecimals = unit === '%' ? 0 : decimals;
        const displayId = el.dataset.display;
        const hidden = document.querySelector(`input[name="${target}"]`);
        const displayEl = displayId ? document.getElementById(displayId) : null;
        const min = parseFloat(el.min);
        const max = parseFloat(el.max);
        const shouldScale = unit === '%' && Math.abs(max) <= 1 && Math.abs(min) <= 1;
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
                return Number(displayVal).toFixed(displayDecimals) + ' s';
            }
            return Number(displayVal).toFixed(displayDecimals) + (unit ? ' ' + unitLabel : '');
        };
        if (displayEl) {
            displayEl.textContent = isNaN(el.value) ? 'not set' : format(parseFloat(el.value));
        }
        if (hidden) {
            el.addEventListener('input', () => {
                const v = parseFloat(el.value);
                const m = Math.pow(10, decimals);
                const q = Math.round(v * m) / m;
                hidden.value = q;
                if (displayEl) displayEl.textContent = format(q);
                hidden.dispatchEvent(new Event('change'));
            });
        }
    }

    document.querySelectorAll('input.param-dial').forEach(setupControl);
    document.querySelectorAll('input.param-slider').forEach(setupControl);
    document.querySelectorAll('input.macro-dial').forEach(setupControl);

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
});
