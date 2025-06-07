function initDriftParams() {
  const osc1Semi = new Nexus.Dial('#osc1_semitone', {size:[60,60],min:-24,max:24,value:0});
  const osc1Shape = new Nexus.Dial('#osc1_shape', {size:[60,60],min:0,max:1,value:0});
  const osc2Semi = new Nexus.Dial('#osc2_semitone', {size:[60,60],min:-24,max:24,value:0});
  const osc2Shape = new Nexus.Dial('#osc2_shape', {size:[60,60],min:0,max:1,value:0});
  const osc2Detune = new Nexus.Dial('#osc2_detune', {size:[60,60],min:-50,max:50,value:0});
  const shapeModAmt = new Nexus.Slider('#osc1_shape_mod_amt', {size:[120,20],mode:'absolute',min:0,max:1,value:0});
  const pitchAmt1 = new Nexus.Slider('#pitch_mod_amt1', {size:[120,20],mode:'absolute',min:0,max:1,value:0});
  const pitchAmt2 = new Nexus.Slider('#pitch_mod_amt2', {size:[120,20],mode:'absolute',min:0,max:1,value:0});

  osc1Semi.on('change', v => document.getElementById('osc1_semitone_val').textContent = v.toFixed(0));
  osc1Shape.on('change', v => document.getElementById('osc1_shape_val').textContent = (v*100).toFixed(0)+'%');
  osc2Semi.on('change', v => document.getElementById('osc2_semitone_val').textContent = v.toFixed(0));
  osc2Shape.on('change', v => document.getElementById('osc2_shape_val').textContent = (v*100).toFixed(0)+'%');
  osc2Detune.on('change', v => document.getElementById('osc2_detune_val').textContent = v.toFixed(1)+'c');
}
