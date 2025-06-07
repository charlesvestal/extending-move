document.addEventListener('DOMContentLoaded', () => {
    function createDial(selector, options = {}) {
        const opts = Object.assign({ size: [30,30], min: 0, max: 1, value: 0 }, options);
        return new Nexus.Dial(selector, opts);
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
    createDial('#env1-attack', {min: 0, max: 5, value: 0.01});
    createDial('#env1-decay', {min: 0, max: 5, value: 0.5});
    createDial('#env1-sustain', {min: 0, max: 1, value: 0.7});
    createDial('#env1-release', {min: 0, max: 5, value: 1});
    createDial('#env2-attack', {min: 0, max: 5, value: 0.01});
    createDial('#env2-decay', {min: 0, max: 5, value: 0.5});
    createDial('#env2-sustain', {min: 0, max: 1, value: 0.7});
    createDial('#env2-release', {min: 0, max: 5, value: 1});
    createDial('#lfo-ratio', {min: 0.1, max: 10, value: 1});
    createDial('#lfo-amount', {min: 0, max: 1, value: 0});
    createDial('#mixer-volume', {min: 0, max: 1, value: 0.8});
});
