document.addEventListener('DOMContentLoaded', () => {
    const dials = document.querySelectorAll('.param-dial');
    dials.forEach(el => {
        const min = parseFloat(el.dataset.min);
        const max = parseFloat(el.dataset.max);
        const val = parseFloat(el.dataset.value);
        const target = el.dataset.target;
        const decimals = parseInt(el.dataset.decimals || '2', 10);
        const unit = el.dataset.unit || '';
        const displayId = el.dataset.display;
        const dial = new Nexus.Dial(el, {
            size: [30,30],
            min: isNaN(min) ? 0 : min,
            max: isNaN(max) ? 1 : max,
            value: isNaN(val) ? 0 : val,
        });
        const step = Math.pow(10, -decimals);
        dial.step = step;
        const shouldScale = unit === '%' && Math.abs(max) <= 1 && Math.abs(min) <= 1;
        const format = (v) => {
            const displayVal = shouldScale ? v * 100 : v;
            return Number(displayVal).toFixed(decimals) + (unit ? ' ' + unit : '');
        };
        const displayEl = displayId ? document.getElementById(displayId) : null;
        if (displayEl) {
            displayEl.textContent = isNaN(val) ? 'not set' : format(val);
        }
        const input = document.querySelector(`input[name="${target}"]`);
        if (input) {
            dial.on('change', v => {
                const m = Math.pow(10, decimals);
                const q = Math.round(v * m) / m;
                input.value = q;
                if (displayEl) displayEl.textContent = format(q);
            });
        }
    });

    const sliders = document.querySelectorAll('.param-slider');
    sliders.forEach(el => {
        const min = parseFloat(el.dataset.min);
        const max = parseFloat(el.dataset.max);
        const val = parseFloat(el.dataset.value);
        const target = el.dataset.target;
        const decimals = parseInt(el.dataset.decimals || '2', 10);
        const unit = el.dataset.unit || '';
        const displayId = el.dataset.display;
        const slider = new Nexus.Slider(el, {
            size: [80,20],
            mode: 'absolute',
            min: isNaN(min) ? 0 : min,
            max: isNaN(max) ? 1 : max,
            step: 0,
            value: isNaN(val) ? 0 : val,
            orientation: 'horizontal'
        });
        const step = Math.pow(10, -decimals);
        slider.step = step;
        const shouldScale = unit === '%' && Math.abs(max) <= 1 && Math.abs(min) <= 1;
        const format = (v) => {
            const displayVal = shouldScale ? v * 100 : v;
            return Number(displayVal).toFixed(decimals) + (unit ? ' ' + unit : '');
        };
        const displayEl = displayId ? document.getElementById(displayId) : null;
        if (displayEl) {
            displayEl.textContent = isNaN(val) ? 'not set' : format(val);
        }
        const input = document.querySelector(`input[name="${target}"]`);
        if (input) {
            slider.on('change', v => {
                const m = Math.pow(10, decimals);
                const q = Math.round(v * m) / m;
                input.value = q;
                if (displayEl) displayEl.textContent = format(q);
            });
        }
    });

    const toggles = document.querySelectorAll('.param-toggle');
    toggles.forEach(el => {
        const val = parseFloat(el.dataset.value);
        const target = el.dataset.target;
        const toggle = new Nexus.Toggle(el, {
            size: [30,15],
            state: val > 0,
        });
        const input = document.querySelector(`input[name="${target}"]`);
        if (input) {
            toggle.on('change', v => {
                input.value = v ? 1 : 0;
            });
        }
    });

    const env2Select = document.querySelector('.param-item[data-name="Global_Envelope2Mode"] select');
    const cyclingRows = document.querySelectorAll('.env2-cycling');
    function updateCycling() {
        if (!env2Select) return;
        const show = env2Select.value === 'Cyc';
        cyclingRows.forEach(r => {
            if (show) {
                r.classList.remove('hidden');
            } else {
                r.classList.add('hidden');
            }
        });
    }
    if (env2Select) {
        env2Select.addEventListener('change', updateCycling);
        updateCycling();
    }
});
