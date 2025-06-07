document.addEventListener('DOMContentLoaded', () => {
    const dials = document.querySelectorAll('.param-dial');
    dials.forEach(el => {
        const min = parseFloat(el.dataset.min);
        const max = parseFloat(el.dataset.max);
        const val = parseFloat(el.dataset.value);
        const target = el.dataset.target;
        const displayId = el.dataset.display;
        const dial = new Nexus.Dial(el, {
            size: [60,60],
            min: isNaN(min) ? 0 : min,
            max: isNaN(max) ? 1 : max,
            value: isNaN(val) ? 0 : val,
        });
        const valueElem = displayId ? document.getElementById(displayId) : null;
        if (valueElem) {
            valueElem.textContent = dial.value;
        }
        const input = document.querySelector(`input[name="${target}"]`);
        dial.on('change', v => {
            if (input) {
                input.value = v;
            }
            if (valueElem) {
                valueElem.textContent = parseFloat(v).toFixed(2);
            }
        });
    });
});
