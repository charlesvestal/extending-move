document.addEventListener('DOMContentLoaded', () => {
    const dialMap = {};
    document.querySelectorAll('.param-dial').forEach(el => {
        // Read range and initial value from data attributes
        const min = parseFloat(el.dataset.min);
        const max = parseFloat(el.dataset.max);
        const val = parseFloat(el.dataset.value);
        const target = el.dataset.target;
        const numId = el.dataset.number;
        const param = el.dataset.param;
        const dial = new Nexus.Dial(el, {
            size: [60, 60],
            min: isNaN(min) ? 0 : min,
            max: isNaN(max) ? 1 : max,
            value: isNaN(val) ? 0 : val,
        });
        dialMap[param] = dial;
        const input = document.querySelector(`input[name="${target}"]`);
        dial.on('change', v => {
            if (input) {
                input.value = v;
            }
        });

        if (numId) {
            const numElem = document.getElementById(numId);
            if (numElem) {
                const num = new Nexus.Number(numElem, { size: [50, 20], value: dial.value, min: dial.min, max: dial.max });
                num.link(dial);
                num.element.readOnly = true;
                num.element.style.pointerEvents = 'none';
            }
        }
    });

    const env1Elem = document.getElementById('env1-display');
    const env2Elem = document.getElementById('env2-display');

    function norm(d) {
        if (!d) return 0;
        return (d.value - d.min) / (d.max - d.min);
    }

    function makeEnv(selector, prefix) {
        const atk = dialMap[`${prefix}_Attack`];
        const dec = dialMap[`${prefix}_Decay`];
        const sus = dialMap[`${prefix}_Sustain`];
        const rel = dialMap[`${prefix}_Release`];
        return new Nexus.Envelope(selector, {
            size: [180, 100],
            points: [
                { x: 0, y: 0 },
                { x: norm(atk), y: 1 },
                { x: norm(dec), y: sus ? sus.value : 0.5 },
                { x: norm(rel), y: 0 },
            ],
        });
    }

    const env1 = env1Elem ? makeEnv('#env1-display', 'Envelope1') : null;
    const env2 = env2Elem ? makeEnv('#env2-display', 'Envelope2') : null;

    function updateEnv(env, prefix) {
        if (!env) return;
        const atk = dialMap[`${prefix}_Attack`];
        const dec = dialMap[`${prefix}_Decay`];
        const sus = dialMap[`${prefix}_Sustain`];
        const rel = dialMap[`${prefix}_Release`];
        if (atk && dec && sus && rel) {
            env.points[1].x = norm(atk);
            env.points[2].x = norm(dec);
            env.points[2].y = sus.value;
            env.points[3].x = norm(rel);
            env.draw();
        }
    }

    updateEnv(env1, 'Envelope1');
    updateEnv(env2, 'Envelope2');

    ['Attack', 'Decay', 'Sustain', 'Release'].forEach(part => {
        const d1 = dialMap[`Envelope1_${part}`];
        if (d1) {
            d1.on('change', () => updateEnv(env1, 'Envelope1'));
        }
        const d2 = dialMap[`Envelope2_${part}`];
        if (d2) {
            d2.on('change', () => updateEnv(env2, 'Envelope2'));
        }
    });
});

