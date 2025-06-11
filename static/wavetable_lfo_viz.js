export function initWavetableLfoViz() {
  function initFor(index) {
    const canvas = document.getElementById(`lfo${index}-canvas`);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const pref = `Voice_Modulators_Lfo${index}_`;
    const qRange = name => document.querySelector(`.param-item[data-name="${pref}${name}"] input[type="range"]`);
    const qSelect = name => document.querySelector(`.param-item[data-name="${pref}${name}"] select`);

    const rateEl = qRange('Time_Rate');
    const syncEl = qRange('Time_SyncedRate');
    const syncSel = qSelect('Time_Sync');
    const shapeSel = qSelect('Shape_Type');

    const SYNC_RATES = [
      8,6,4,3,2,1.5,1,0.75,0.5,0.375,1/3,5/16,
      0.25,3/16,1/6,1/8,1/12,1/16,1/24,1/32,1/48,1/64
    ];
    const BPM = 120;

    function knobRatio(el, maxOverride=null) {
      if (!el) return 0;
      const min = parseFloat(el.min||'0');
      const max = maxOverride!==null ? maxOverride : parseFloat(el.max||'1');
      const val = parseFloat(el.value||'0');
      return Math.min(Math.max((val-min)/(max-min),0),1);
    }

    function wave(shape, phase) {
      const p = phase%1;
      switch(shape) {
        case 'Sine': return Math.sin(2*Math.PI*p);
        case 'Triangle': return 1-4*Math.abs(Math.round(p-0.25)-(p-0.25));
        case 'Sawtooth': return 2*p-1;
        case 'Noise': return Math.random()*2-1;
        default: return 0;
      }
    }

    function getRateHz() {
      const mode = syncSel ? syncSel.value : 'Free';
      if (mode === 'Free' && rateEl) return parseFloat(rateEl.value||'0');
      if (mode !== 'Free' && syncEl) {
        const idx = parseInt(syncEl.value||'0',10);
        const bars = SYNC_RATES[idx] || 1;
        const beats = bars*4;
        const sec = (60/BPM)*beats;
        return sec>0 ? 1/sec : 0;
      }
      return 0;
    }

    function draw() {
      const rate = getRateHz();
      const mode = syncSel ? syncSel.value : 'Free';
      const shape = shapeSel ? shapeSel.value : 'Sine';
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0,0,w,h);
      ctx.beginPath();
      let duration = 1;
      let ratio = 0;
      if (mode === 'Free') ratio = knobRatio(rateEl);
      else ratio = knobRatio(syncEl, SYNC_RATES.length-1);
      const cycles = 1 + ratio*9;
      duration = rate>0 ? cycles/rate : 1;
      for (let i=0;i<=w;i++) {
        const t = (i/w)*duration;
        const ph = rate*t;
        let val = wave(shape, ph);
        val = val*0.5 + 0.5;
        const y = h - val*h;
        if (i===0) ctx.moveTo(i,y); else ctx.lineTo(i,y);
      }
      ctx.strokeStyle = '#f00';
      ctx.stroke();
    }

    [rateEl,syncEl,syncSel,shapeSel].forEach(el=>{
      if(!el) return; const evt = el.tagName==='SELECT'?'change':'input';
      el.addEventListener(evt, draw);
    });
    draw();
  }

  [1,2].forEach(initFor);
}

document.addEventListener('DOMContentLoaded', initWavetableLfoViz);
