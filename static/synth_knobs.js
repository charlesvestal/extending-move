document.addEventListener('DOMContentLoaded', () => {
    function createDial(id, options = {}) {
        const elem = document.querySelector(id);
        const valueElem = document.querySelector(id + '-val');
        const opts = Object.assign({ size: [60,60], min: 0, max: 1, value: 0 }, options);
        const dial = new Nexus.Dial(elem, opts);
        if (valueElem) {
            valueElem.textContent = dial.value;
        }
        dial.on('change', v => {
            if (valueElem) {
                valueElem.textContent = parseFloat(v).toFixed(2);
            }
            if (options.onChange) {
                options.onChange(v);
            }
        });
        return dial;
    }

    const env1 = new Nexus.Envelope('#env1-display', {size: [180, 100]});
    const env2 = new Nexus.Envelope('#env2-display', {size: [180, 100]});

    function updateEnv(env, atk, dec, sus, rel) {
        env.attack = atk.value;
        env.decay = dec.value;
        env.sustain = sus.value;
        env.release = rel.value;
        env.draw();
    }

    createDial('#osc1-octave', {min: -2, max: 2, value: 0});
    createDial('#osc1-shape', {min: 0, max: 1, value: 0});
    createDial('#osc2-octave', {min: -2, max: 2, value: 0});
    createDial('#osc2-detune', {min: -50, max: 50, value: 0});
    createDial('#mix-osc1', {min: 0, max: 1, value: 0.5});
    createDial('#mix-osc2', {min: 0, max: 1, value: 0.5});
    createDial('#mix-noise', {min: 0, max: 1, value: 0});
    createDial('#filter-freq', {min: 20, max: 20000, value: 1000});
    createDial('#filter-res', {min: 0.1, max: 10, value: 1});
    createDial('#filter-hp', {min: 20, max: 5000, value: 20});

    const env1Attack = createDial('#env1-attack', {min: 0, max: 5, value: 0.01, onChange: () => updateEnv(env1, env1Attack, env1Decay, env1Sustain, env1Release)});
    const env1Decay = createDial('#env1-decay', {min: 0, max: 5, value: 0.5, onChange: () => updateEnv(env1, env1Attack, env1Decay, env1Sustain, env1Release)});
    const env1Sustain = createDial('#env1-sustain', {min: 0, max: 1, value: 0.7, onChange: () => updateEnv(env1, env1Attack, env1Decay, env1Sustain, env1Release)});
    const env1Release = createDial('#env1-release', {min: 0, max: 5, value: 1, onChange: () => updateEnv(env1, env1Attack, env1Decay, env1Sustain, env1Release)});

    const env2Attack = createDial('#env2-attack', {min: 0, max: 5, value: 0.01, onChange: () => updateEnv(env2, env2Attack, env2Decay, env2Sustain, env2Release)});
    const env2Decay = createDial('#env2-decay', {min: 0, max: 5, value: 0.5, onChange: () => updateEnv(env2, env2Attack, env2Decay, env2Sustain, env2Release)});
    const env2Sustain = createDial('#env2-sustain', {min: 0, max: 1, value: 0.7, onChange: () => updateEnv(env2, env2Attack, env2Decay, env2Sustain, env2Release)});
    const env2Release = createDial('#env2-release', {min: 0, max: 5, value: 1, onChange: () => updateEnv(env2, env2Attack, env2Decay, env2Sustain, env2Release)});

    updateEnv(env1, env1Attack, env1Decay, env1Sustain, env1Release);
    updateEnv(env2, env2Attack, env2Decay, env2Sustain, env2Release);
    createDial('#lfo-ratio', {min: 0.1, max: 10, value: 1});
    createDial('#lfo-amount', {min: 0, max: 1, value: 0});
    createDial('#mixer-volume', {min: 0, max: 1, value: 0.8});
});
