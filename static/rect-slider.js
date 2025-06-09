(function(global){
function clamp(v,min,max){return v<min?min:v>max?max:v;}
function initSlider(el){
  if(el._sliderInit)return;
  el._sliderInit=true;
  const min=parseFloat(el.dataset.min||0);
  const max=parseFloat(el.dataset.max||1);
  const step=parseFloat(el.dataset.step||1);
  const unit=el.dataset.unit||'';
  const defaultValue=el.dataset.default!==undefined?parseFloat(el.dataset.default):0;
  function getStep(v){
    return getPercentStep(v, unit, step, shouldScale);
  }
  const decimals=parseInt(el.dataset.decimals||2,10);
  const displayDecimalsDefault=unit==='%'?0:decimals;
  const shouldScale=unit==='%' && Math.abs(max)<=1 && Math.abs(min)<=1;
  let value=parseFloat(el.dataset.value||min);
  const centered=el.classList.contains('center')||el.dataset.centered==='true';
  const targetId=el.dataset.target;
  const target=targetId?document.querySelector(`#${targetId}, input[name="${targetId}"]`):null;
  el.innerHTML='';
  el.classList.add('rect-slider-container');
  // Make focusable so keyboard interaction works
  if(!el.hasAttribute('tabindex')) el.tabIndex = 0;
  const fill=document.createElement('div');
  fill.className='rect-slider-fill';
  el.appendChild(fill);
  const label=document.createElement('span');
  label.className='rect-slider-label';
  el.appendChild(label);
  function getDisplayDecimals(v){
    return getPercentDecimals(v, unit, displayDecimalsDefault, shouldScale);
  }
  function format(v){
    let displayVal=shouldScale?v*100:v;
    let unitLabel=unit;
    if(unit==='Hz'){
      displayVal=Number(displayVal);
      if(displayVal>=1000){
        displayVal=displayVal/1000;
        unitLabel='kHz';
      }
      return displayVal.toFixed(1)+` ${unitLabel}`;
    }else if(unit==='s'){
      if(displayVal<1){
        return (displayVal*1000).toFixed(0)+` ms`;
      }
      return Number(displayVal).toFixed(getDisplayDecimals(v))+` s`;
    }
    return Number(displayVal).toFixed(getDisplayDecimals(v))+(unit?` ${unitLabel}`:'');
  }
  function update(){
    label.textContent=format(value);
    if(target){target.value=value;target.dispatchEvent(new Event('change'));}
    const range=max-min;
    if(centered){
      const mid=(max+min)/2;
      if(value>=mid){
        const pct=(value-mid)/(max-mid); //0..1
        fill.style.left='50%';
        fill.style.width=(pct*50)+'%';
      }else{
        const pct=(mid-value)/(mid-min);
        fill.style.left=(50-pct*50)+'%';
        fill.style.width=(pct*50)+'%';
      }
    }else{
      const pct=(value-min)/range;
      fill.style.left='0%';
      fill.style.width=(pct*100)+'%';
    }
  }
  el._sliderUpdate = (v)=>{ value = clamp(parseFloat(v),min,max); update(); };
  function start(ev){
    if(el.classList.contains('disabled') || el.dataset.disabled==='true') return;
    ev.preventDefault();
    const startY=ev.touches?ev.touches[0].clientY:ev.clientY;
    const startX=ev.touches?ev.touches[0].clientX:ev.clientX;
    const startVal=value;
    function move(e){
      const y=e.touches?e.touches[0].clientY:e.clientY;
      const x=e.touches?e.touches[0].clientX:e.clientX;
      const dy=startY-y;
      const dx=x-startX;
      const isShift = e.shiftKey;
      // slower movement when holding Shift
      const dragSense = isShift ? 2000 : 200;
      const scale=(max-min)/dragSense;
      const drag=Math.abs(dy)>Math.abs(dx)?dy:dx;
      let v=startVal+drag*scale;
      let st=getStep(v);
      v=Math.round(v/st)*st;
      value=clamp(v,min,max);
      update();
    }
    function end(){
      document.removeEventListener('mousemove',move);
      document.removeEventListener('mouseup',end);
      document.removeEventListener('touchmove',move);
      document.removeEventListener('touchend',end);
    }
    document.addEventListener('mousemove',move);
    document.addEventListener('mouseup',end);
    document.addEventListener('touchmove',move);
    document.addEventListener('touchend',end);
  }
  el.addEventListener('mousedown',start);
  el.addEventListener('touchstart',start);
  el.addEventListener('dblclick',()=>{
    value=clamp(defaultValue,min,max);
    update();
  });
  el.addEventListener('keydown',(e)=>{
    if(['ArrowUp','ArrowRight'].includes(e.key)){
      let st=getStep(value);
      value=clamp(value+st,min,max);
      update();
      e.preventDefault();
    }else if(['ArrowDown','ArrowLeft'].includes(e.key)){
      let st=getStep(value);
      value=clamp(value-st,min,max);
      update();
      e.preventDefault();
    }
  });
  update();
}

function initAll(){
  document.querySelectorAll('.rect-slider').forEach(initSlider);
}
global.initRectSlider = initSlider;
global.initRectSliders = initAll;
document.addEventListener('DOMContentLoaded', initAll);
})(window);
