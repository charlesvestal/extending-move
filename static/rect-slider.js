(function(){
function clamp(v,min,max){return v<min?min:v>max?max:v;}
function initSlider(el){
  if(el._sliderInit)return;
  el._sliderInit=true;
  const min=parseFloat(el.dataset.min||0);
  const max=parseFloat(el.dataset.max||1);
  const step=parseFloat(el.dataset.step||1);
  const decimals=parseInt(el.dataset.decimals||2,10);
  const unit=el.dataset.unit||'';
  const displayDecimals=unit==='%'?0:decimals;
  const shouldScale=unit==='%' && Math.abs(max)<=1 && Math.abs(min)<=1;
  let value=parseFloat(el.dataset.value||min);
  const centered=el.classList.contains('center')||el.dataset.centered==='true';
  const targetId=el.dataset.target;
  const target=targetId?document.querySelector(`#${targetId}, input[name="${targetId}"]`):null;
  el.innerHTML='';
  el.classList.add('rect-slider-container');
  const fill=document.createElement('div');
  fill.className='rect-slider-fill';
  el.appendChild(fill);
  const label=document.createElement('span');
  label.className='rect-slider-label';
  el.appendChild(label);
  function format(v){
    const displayVal=shouldScale?v*100:v;
    return Number(displayVal).toFixed(displayDecimals)+(unit?` ${unit}`:'');
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
  function start(ev){
    ev.preventDefault();
    const startY=ev.touches?ev.touches[0].clientY:ev.clientY;
    const startVal=value;
    function move(e){
      const y=e.touches?e.touches[0].clientY:e.clientY;
      const dy=startY-y;
      const scale=(max-min)/100;
      let v=startVal+dy*scale;
      v=Math.round(v/step)*step;
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
  update();
}

document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.rect-slider').forEach(initSlider);
});
})();
