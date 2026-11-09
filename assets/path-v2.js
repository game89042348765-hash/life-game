/* Supplied path-v2 animation frames, with lifecycle cleanup for real application renders. */
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
function marker(el){const cs=getComputedStyle(line),rail=parseFloat(cs.getPropertyValue('--lg-path-rail'))||0,lane=parseFloat(cs.getPropertyValue('--lg-path-lane'))||0;
  const box=line.getBoundingClientRect(),r=el.getBoundingClientRect();return {x:r.left-box.left+rail-lane,y:r.top-box.top+26}}
const put=(cls,p)=>{const e=document.createElement('div');e.className=cls;e.style.left=p.x+'px';e.style.top=p.y+'px';e.setAttribute('aria-hidden','true');line.append(e);return e};
const glow=(px,warm=1)=>`drop-shadow(0 0 ${px}px rgba(${warm?'255,213,74':'239,107,116'},1)) drop-shadow(0 0 ${px*2}px rgba(${warm?'255,213,74,.8':'239,107,116,.7'}))`;

// Звезда рождается на линии — на знаке этапа, где выполнено задание («Сейчас» или «Невыполненное»), и летит вниз.
function route(check,article){const p0=marker(article),end=pick('.is-maximum')||[...line.querySelectorAll(':scope>.lg-level')].at(-1),pE=marker(end);
  return {p0,dx:0,dy:0,d:pE.y-p0.y,k:0,end,len:pE.y-p0.y}}
const T=(r,x,y,sc)=>`translate(${x}px,${y}px) scale(${sc})`;
function arrive(end){end.classList.remove('lg-star-arrived');void end.offsetWidth;end.classList.add('lg-star-arrived');later(()=>end.classList.remove('lg-star-arrived'),800)}
const MODES={
  // «Сейчас»: звезда ярко вспыхивает на знаке, летит вниз и разгорается; линия за ней загорается золотом,
  // пройденные знаки на миг вспыхивают; у цели золотая линия плавно гаснет.
  async NOW(check,article){const r=route(check,article);
    const star=put('lg-flying-star lg-bright',r.p0),tail=document.createElement('s'),rays=document.createElement('i'),core=document.createElement('b');star.append(tail,rays,core);
    // вспышка на знаке «Сейчас» — звезда загорается сразу ярко
    const halo=put('lg-charge',r.p0);animate(halo,[{transform:'scale(.2)',opacity:1},{transform:'scale(2.2)',opacity:0}],{duration:700,easing:'cubic-bezier(.2,.7,.3,1)'}).onfinish=()=>halo.remove();
    animate(core,[{transform:'translate(-50%,-50%) scale(.3)',opacity:0,filter:glow(4)},{transform:'translate(-50%,-50%) scale(2.2) rotate(25deg)',opacity:1,filter:glow(16),offset:.5},{transform:'translate(-50%,-50%) scale(1.5)',opacity:1,filter:glow(12)}],{duration:380,easing:'ease-out',fill:'forwards'});
    animate(rays,[{opacity:0,transform:'translate(-50%,-50%) scale(.4)'},{opacity:1,transform:'translate(-50%,-50%) scale(1.5)'}],{duration:380,fill:'forwards'});
    await wait(330);
    const F=Math.min(2600,1100+r.d*.8),o={duration:F,easing:'cubic-bezier(.4,0,.3,1)',fill:'forwards'};
    animate(core,[{transform:'translate(-50%,-50%) scale(1.5)',filter:glow(12)},{transform:'translate(-50%,-50%) scale(2.1)',filter:glow(18)}],o);
    animate(rays,[{opacity:1,transform:'translate(-50%,-50%) scale(1.5)'},{opacity:1,transform:'translate(-50%,-50%) scale(2.2)',offset:.9},{opacity:0,transform:'translate(-50%,-50%) scale(2.6)'}],o);
    animate(tail,[{opacity:.6,height:'30px'},{opacity:1,height:'210px',offset:.7},{opacity:0,height:'40px'}],o);
    const a=animate(star,[{transform:T(r,0,0,1)},{transform:T(r,0,r.d*.93,1),offset:.92},{transform:T(r,0,r.d,1),opacity:0}],o);
    // линия загорается за звездой, пройденные знаки вспыхивают
    const markers=[...line.querySelectorAll(':scope>.lg-level')].filter(el=>el!==article).map(el=>({el,y:marker(el).y})).filter(m=>m.y>r.p0.y);
    const railGlow=put('lg-rail-glow',r.p0);
    const box0=()=>line.getBoundingClientRect();
    const tick=t=>{if(a.playState!=='running')return;const cy=core.getBoundingClientRect().top+core.getBoundingClientRect().height/2-box0().top;
      railGlow.style.height=Math.max(0,cy-r.p0.y)+'px';
      for(const m of markers)if(!m.done&&cy>=m.y){m.done=true;m.el.classList.add('lg-pass');later(()=>m.el.classList.remove('lg-pass'),900)}
      requestFrame(tick)};requestFrame(tick);
    await a.finished;star.remove();
    animate(railGlow,[{opacity:1},{opacity:0}],{duration:900,fill:'forwards'}).onfinish=()=>railGlow.remove();
    arrive(r.end)},

  // «Невыполненное»: звезда набирает свет на месте (сияние, лучи), затем летит вниз, пролетая «Сейчас» насквозь; у цели растворяется
  async MISSED(check,article){const r=route(check,article);
    const star=put('lg-flying-star',r.p0),tail=document.createElement('s'),rays=document.createElement('i'),core=document.createElement('b');star.append(tail,rays,core);
    const halo=put('lg-charge',r.p0),C=1400;
    animate(halo,[{transform:'scale(.2)',opacity:0},{transform:'scale(1.6)',opacity:.9}],{duration:C,easing:'ease-in',fill:'forwards'});
    animate(core,[{transform:'translate(-50%,-50%) scale(.2)',opacity:0,filter:glow(1)},{transform:'translate(-50%,-50%) scale(1.3)',opacity:1,filter:glow(9)}],{duration:C,easing:'ease-in',fill:'forwards'});
    animate(rays,[{opacity:0,transform:'translate(-50%,-50%) scale(.3)'},{opacity:.8,transform:'translate(-50%,-50%) scale(1.2)'}],{duration:C,easing:'ease-in',fill:'forwards'});
    await wait(C+50);
    animate(halo,[{opacity:.9},{opacity:0,transform:'scale(2.4)'}],{duration:900,fill:'forwards'}).onfinish=()=>halo.remove();
    const F=Math.min(2800,1000+r.len*.85),o={duration:F,easing:'cubic-bezier(.45,0,.3,1)',fill:'forwards'};
    animate(core,[{transform:'translate(-50%,-50%) scale(1.3)',filter:glow(9)},{transform:'translate(-50%,-50%) scale(1.8)',filter:glow(13)}],o);
    animate(tail,[{opacity:0,height:'0px'},{opacity:.7,height:'60px',offset:.3},{opacity:1,height:'130px',offset:.85},{opacity:0,height:'30px'}],o);
    animate(rays,[{opacity:.8},{opacity:1,offset:.9},{opacity:0}],o);
    await animate(star,[{transform:T(r,0,0,1)},{transform:T(r,r.dx,r.dy+r.d*.92,1),offset:.92},{transform:T(r,r.dx,r.dy+r.d,1),opacity:0}],o).finished;
    star.remove();arrive(r.end)}
};

  async function launch(mode){
    if(disposed||busy||!line.isConnected)return;
    const article=typeof mode==='string'?pick(mode==='MISSED'?'.lg-path-missed':'.is-current'):mode?.closest('.lg-path-aesthetics>.lg-level');
    if(!article||!line.contains(article)||!pick('.is-maximum'))return;
    busy=true;
    try{await (article.classList.contains('lg-path-missed')?MODES.MISSED:MODES.NOW)(null,article);}
    catch(error){if(error.name!=='AbortError')console.warn('Эффект пути недоступен:',error);}
    finally{busy=false;}
  }
  function dispose(){
    disposed=true;
    for(const reject of waiters.values())reject(aborted());waiters.clear();
    for(const id of timers)clearTimeout(id);timers.clear();
    for(const id of frames)cancelAnimationFrame(id);frames.clear();
    for(const a of animations)a.cancel();animations.clear();
    line.querySelectorAll('.lg-flying-star,.lg-charge,.lg-rail-glow,.lg-dawn-back').forEach(n=>n.remove());
    line.querySelectorAll('.lg-pass,.lg-star-arrived').forEach(n=>n.classList.remove('lg-pass','lg-star-arrived'));
  }
  current={line,launch,dispose};
}
function clear(){current?.dispose();current=null;}
window.LifeGamePathStar=Object.freeze({init,clear,launch:source=>current?.launch(source)});
})();
