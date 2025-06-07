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
            size: [60,60],
            min: isNaN(min) ? 0 : min,
            max: isNaN(max) ? 1 : max,
            value: isNaN(val) ? 0 : val,
        });
        const format = (v) => Number(v).toFixed(decimals) + (unit ? ' ' + unit : '');
        const displayEl = displayId ? document.getElementById(displayId) : null;
        if (displayEl) {
            displayEl.textContent = format(val);
        }
        const input = document.querySelector(`input[name="${target}"]`);
        if (input) {
            dial.on('change', v => {
                input.value = v;
                if (displayEl) displayEl.textContent = format(v);
            });
        }
    });
});
