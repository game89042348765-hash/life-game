/* Light feedback for completed steps. Visuals only; the application owns all receipts. */
'use strict';
(()=>{
let current=null;
function init(line){
  if(current?.line===line)return;
  clear();if(!line)return;
  const back=document.createElement('div');back.className='lg-dawn-back';back.setAttribute('aria-hidden','true');line.prepend(back);
  let disposed=false,busy=false;
  const timers=new Set(),waiters=new Map(),animations=new Set(),frames=new Set();
  const aborted=()=>new DOMException('Path replaced','AbortError');
  const later=(fn,ms)=>{const id=setTimeout(()=>{timers.delete(id);if(!disposed)fn();},ms);timers.add(id);return id;};
  const wait=ms=>new Promise((resolve,reject)=>{if(disposed){reject(aborted());return;}const id=later(()=>{waiters.delete(id);resolve();},ms);waiters.set(id,reject);});
  const requestFrame=fn=>{const id=requestAnimationFrame(t=>{frames.delete(id);if(!disposed)fn(t);});frames.add(id);return id;};
  const animate=(node,keyframes,options)=>{if(disposed)throw aborted();const a=node.animate(keyframes,options);animations.add(a);a.finished.then(()=>animations.delete(a),()=>animations.delete(a));return a;};
  const pick=sel=>line.querySelector(':scope>'+sel);
  function marker(node){
    const cs=getComputedStyle(line),rail=parseFloat(cs.getPropertyValue('--lg-path-rail'))||0,lane=parseFloat(cs.getPropertyValue('--lg-path-lane'))||0;
    const box=line.getBoundingClientRect(),r=node.getBoundingClientRect();
    return {x:r.left-box.left+rail-lane,y:r.top-box.top+26};
  }
  function put(cls,p){const n=document.createElement('div');n.className='lg-path-effect '+cls;n.style.left=p.x+'px';n.style.top=p.y+'px';n.setAttribute('aria-hidden','true');line.append(n);return n;}
  function echo(node,reduced=false){
    const ring=put('lg-path-arrival',marker(node));
    animate(ring,[{transform:'translate(-50%,-50%) scale('+ (reduced?'1':'.45') +')',opacity:.8},{transform:'translate(-50%,-50%) scale('+ (reduced?'1':'2.6') +')',opacity:0}],{duration:reduced?220:760,easing:'ease-out'}).onfinish=()=>ring.remove();
  }
  function lightMarker(node){
    node.classList.add('lg-pass');later(()=>node.classList.remove('lg-pass'),850);
    if(node.classList.contains('is-optimal'))echo(node);
  }
  async function recover(article){
    // Closing an unfinished loop: scattered points converge and the open ring becomes whole.
    const recovery=put('lg-path-recovery',marker(article));recovery.dataset.phase='restore';
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 28 28');
    const circle=document.createElementNS(svg.namespaceURI,'circle');circle.setAttribute('cx','14');circle.setAttribute('cy','14');circle.setAttribute('r','10');svg.append(circle);recovery.append(svg);
    animate(circle,[{strokeDashoffset:63,opacity:.25},{strokeDashoffset:0,opacity:1}],{duration:780,easing:'cubic-bezier(.3,0,.3,1)',fill:'forwards'});
    for(const [x,y] of [[-23,-17],[22,-20],[-24,17],[23,19]]){
      const point=document.createElement('i');recovery.append(point);
      animate(point,[{transform:`translate(${x}px,${y}px) scale(.6)`,opacity:0},{opacity:1,offset:.2},{transform:'translate(0,0) scale(.3)',opacity:0}],{duration:780,easing:'cubic-bezier(.4,0,.5,1)',fill:'forwards'});
    }
    await wait(850);echo(article);
    animate(recovery,[{opacity:1},{opacity:0}],{duration:320,fill:'forwards'}).onfinish=()=>recovery.remove();
  }
  async function travel(article,mode){
    const start=marker(article),end=pick('.is-maximum')||[...line.querySelectorAll(':scope>.lg-level')].at(-1),distance=Math.max(0,marker(end).y-start.y);
    const pulse=put('lg-path-pulse '+(mode==='MISSED'?'is-restored':'is-forward'),start);pulse.dataset.mode=mode;
    for(const tag of ['s','i','b'])pulse.append(document.createElement(tag));
    const origin=put('lg-path-origin',start);
    animate(origin,[{transform:'translate(-50%,-50%) scale(.45)',opacity:.9},{transform:'translate(-50%,-50%) scale(2.1)',opacity:0}],{duration:520,easing:'ease-out'}).onfinish=()=>origin.remove();
    const duration=Math.min(2500,1050+distance*.65),options={duration,easing:'cubic-bezier(.35,0,.25,1)',fill:'forwards'};
    animate(pulse.querySelector('s'),[{height:'18px',opacity:0},{height:'120px',opacity:.9,offset:.3},{height:'180px',opacity:.8,offset:.8},{height:'36px',opacity:0}],options);
    animate(pulse.querySelector('i'),[{transform:'translate(-50%,-50%) scale(.6)',opacity:.5},{transform:'translate(-50%,-50%) scale(1.3)',opacity:1,offset:.6},{transform:'translate(-50%,-50%) scale(1.8)',opacity:0}],options);
    const flight=animate(pulse,[{transform:'translateY(0)',opacity:1},{transform:`translateY(${distance}px)`,opacity:0}],options);
    const rail=put('lg-rail-glow',start),marks=[...line.querySelectorAll(':scope>.lg-level')].filter(n=>n!==article).map(node=>({node,y:marker(node).y,lit:false})).filter(m=>m.y>start.y);
    const tick=()=>{
      if(flight.playState!=='running')return;
      const front=pulse.getBoundingClientRect().top-line.getBoundingClientRect().top;
      rail.style.height=Math.max(0,front-start.y)+'px';
      for(const m of marks)if(!m.lit&&front>=m.y){m.lit=true;lightMarker(m.node);}
      requestFrame(tick);
    };requestFrame(tick);
    await flight.finished;pulse.remove();
    for(const m of marks)if(!m.lit)lightMarker(m.node);
    animate(rail,[{opacity:1},{opacity:0}],{duration:750,fill:'forwards'}).onfinish=()=>rail.remove();
    echo(end);
  }
  async function launch(source){
    if(disposed||busy||!line.isConnected)return;
    const article=typeof source==='string'?pick(source==='MISSED'?'.lg-path-missed':'.is-current'):source?.closest('.lg-path-aesthetics>.lg-level');
    if(!article||!line.contains(article)||!pick('.is-maximum'))return;
    const mode=article.classList.contains('lg-path-missed')?'MISSED':'NOW';busy=true;
    try{
      if(matchMedia('(prefers-reduced-motion: reduce)').matches){echo(article,true);return;}
      if(mode==='MISSED')await recover(article);
      await travel(article,mode);
    }catch(error){if(error.name!=='AbortError')console.warn('Эффект пути недоступен:',error);}
    finally{busy=false;}
  }
  function dispose(){
    disposed=true;
    for(const reject of waiters.values())reject(aborted());waiters.clear();
    for(const id of timers)clearTimeout(id);timers.clear();
    for(const id of frames)cancelAnimationFrame(id);frames.clear();
    for(const a of animations)a.cancel();animations.clear();
    line.querySelectorAll('.lg-path-effect,.lg-dawn-back').forEach(n=>n.remove());
    line.querySelectorAll('.lg-pass').forEach(n=>n.classList.remove('lg-pass'));
  }
  current={line,launch,dispose};
}
function clear(){current?.dispose();current=null;}
// Keep the existing application integration; only the visual language has changed.
window.LifeGamePathStar=Object.freeze({init,clear,launch:source=>current?.launch(source)});
})();
