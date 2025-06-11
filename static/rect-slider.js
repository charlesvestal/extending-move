(function(global){
function clamp(v,min,max){return v<min?min:v>max?max:v;}
function initSlider(el){
  if(el._sliderInit)return;
  el._sliderInit=true;
  const min=parseFloat(el.dataset.min||0);
  const max=parseFloat(el.dataset.max||1);
  const step=parseFloat(el.dataset.step||1);
  const unit=el.dataset.unit||'';
  const curve=el.dataset.curve||'linear';
  const rangeMin=parseFloat(el.dataset.rangeMin||min);
  const rangeMax=parseFloat(el.dataset.rangeMax||max);
  const defaultValue=el.dataset.default!==undefined?parseFloat(el.dataset.default):0;
  function toActual(v){
    if(curve==='log'){
      const t=(v-min)/(max-min);
      return Math.exp(Math.log(rangeMin)+t*(Math.log(rangeMax)-Math.log(rangeMin)));
    }
    return v;
  }
  function fromActual(v){
    if(curve==='log'){
      const t=(Math.log(v)-Math.log(rangeMin))/(Math.log(rangeMax)-Math.log(rangeMin));
      return min+t*(max-min);
    }
    return v;
  }
  function getStep(v){
    return getPercentStep(v, unit, step, shouldScale);
  }
  const decimals=parseInt(el.dataset.decimals||2,10);
  const displayDecimalsDefault=(unit==='%'||unit==='ct')?0:decimals;
  const shouldScale=(unit==='%'||unit==='ct') && Math.abs(rangeMax)<=1 && Math.abs(rangeMin)<=1;
  let normValue=parseFloat(el.dataset.value||min);
  let value=toActual(normValue);
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
    let disp=normValue;
    if(centered){
      const mid=(max+min)/2;
      if(disp>=mid){
        const pct=(disp-mid)/(max-mid);
        fill.style.left='50%';
        fill.style.width=(pct*50)+'%';
      }else{
        const pct=(mid-disp)/(mid-min);
        fill.style.left=(50-pct*50)+'%';
        fill.style.width=(pct*50)+'%';
      }
    }else{
      const pct=(disp-min)/range;
      fill.style.left='0%';
      fill.style.width=(pct*100)+'%';
    }
  }
  el._sliderUpdate = (v)=>{ normValue = clamp(parseFloat(v),min,max); value = toActual(normValue); update(); };
  function start(ev){
    if(el.classList.contains('disabled') || el.dataset.disabled==='true') return;
    ev.preventDefault();
    const startY=ev.touches?ev.touches[0].clientY:ev.clientY;
    const startX=ev.touches?ev.touches[0].clientX:ev.clientX;
    const startVal=normValue;
    function move(e){
      const y=e.touches?e.touches[0].clientY:e.clientY;
      const x=e.touches?e.touches[0].clientX:e.clientX;
      const dy=startY-y;
      const dx=x-startX;
      const isShift = e.shiftKey;
      // slower movement when holding Shift
      const sens=parseFloat(el.dataset.sensitivity||'1');
      const dragSense = (isShift ? 2000 : 200) * sens;
      const scale=(max-min)/dragSense;
      const drag=Math.abs(dy)>Math.abs(dx)?dy:dx;
      let v=startVal+drag*scale;
      let act=toActual(v);
      let st=getStep(act);
      act=Math.round((act-rangeMin)/st)*st+rangeMin;
      act=clamp(act,rangeMin,rangeMax);
      normValue=fromActual(act);
      value=act;
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
    value=clamp(defaultValue,rangeMin,rangeMax);
    normValue=fromActual(value);
    update();
  });
  el.addEventListener('keydown',(e)=>{
    if(['ArrowUp','ArrowRight'].includes(e.key)){
      let st=getStep(value);
      value=clamp(value+st,rangeMin,rangeMax);
      normValue=fromActual(value);
      update();
      e.preventDefault();
    }else if(['ArrowDown','ArrowLeft'].includes(e.key)){
      let st=getStep(value);
      value=clamp(value-st,rangeMin,rangeMax);
      normValue=fromActual(value);
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
