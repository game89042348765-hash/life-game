/* Stage map: a small camera over canonical block stages, goals and their conditions. */
'use strict';
(()=>{
  const M=globalThis.LifeGameStages,NS='http://www.w3.org/2000/svg';
  const colors=['#b8a0dc','#8bceac','#e2c77b','#92b7ee','#e6a6aa','#83c7d0','#c2b58f','#adbdc7'];
  const el=(tag,cls='',text)=>{const n=document.createElement(tag);n.className=cls;if(text!==undefined)n.textContent=text;return n;};
  const paths={close:'m6 6 12 12M6 18 18 6',back:'m15 5-7 7 7 7',lock:'M6 10h12v11H6ZM8 10V6a4 4 0 0 1 8 0v4',plus:'M5 12h14M12 5v14',minus:'M5 12h14',reset:'M4 10a8 8 0 1 1 0 5M4 4v6h6',arrow:'M4 12h15m-5-5 5 5-5 5',chevron:'m9 5 7 7-7 7',check:'m5 12 4 4L20 5',more:'M5 12h.01M12 12h.01M19 12h.01',list:'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01'};
  function icon(name,cls=''){const n=document.createElementNS(NS,'svg');n.setAttribute('viewBox','0 0 24 24');n.setAttribute('aria-hidden','true');if(cls)n.setAttribute('class',cls);const p=document.createElementNS(NS,'path');p.setAttribute('d',paths[name]||paths.arrow);n.append(p);return n;}
  function button(text,cls,action,glyph){const n=el('button',cls);n.type='button';if(glyph)n.append(icon(glyph));if(text)n.append(document.createTextNode(text));n.addEventListener('click',action);return n;}
  function titledButton(glyph,title,action){const b=button('','',action,glyph);b.setAttribute('aria-label',title);return b;}
  function textDialog(host,title,build){const d=el('dialog','lg-stage-dialog');d.append(el('h2','',title));build(d);d.append(button('Закрыть','button secondary full spaced',()=>d.close()));d.addEventListener('close',()=>d.remove(),{once:true});document.body.append(d);host.showDialog(d);return d;}
  function create(host){
    let root,board,wrap,world,layer,panel,panelContent,select,controls,status,observer,abort,data,blocks=[],nodes=[],dependencies=[],W=440,H=680,selectedId=null,scope='all',linked=null,linkedStageIds=[],ready=false,panMoved=false;
    const camera={x:12,y:25,scale:1};let savedCamera=null;
    const snap=()=>host.read(),stageKey=id=>'stage:'+id;
    const label=(value,max=30)=>value.length>max?value.slice(0,max-1)+'…':value;
    function mount(target){
      const snapshot=snap();data=snapshot.data;blocks=data.blocks.filter(b=>b.archivedAt===null);abort=new AbortController();const opts={signal:abort.signal};
      root=el('section','lg-sm');root.setAttribute('aria-label','Стратегия — карта этапов');const shell=el('div','sm-shell'),header=el('header','sm-header'),top=el('div','sm-top');
      const back=titledButton('back','Закрыть карту стратегии',()=>host.back());back.className='sm-round';
      const add=titledButton('plus','Добавить этап на карте',addStage);add.className='sm-round';add.disabled=!snapshot.healthy;top.append(back,el('h1','','Стратегия'),add);header.append(top);
      select=el('select','sm-select');select.setAttribute('aria-label','Блоки на карте');updateOptions();select.addEventListener('change',()=>{scope=select.value;linked=null;selectedId=null;layout();reset();});const filters=el('div','sm-filter-row'),openList=titledButton('list','Список этапов',stageList);openList.className='sm-round';filters.append(select,openList);header.append(filters);
      const legend=el('div','sm-legend');for(const [type,text]of [['stage-symbol','Этап'],['goal-symbol','Цель'],['link-symbol','Условие']]){const span=el('span');span.append(el('i',type),document.createTextNode(text));legend.append(span);}header.append(legend);shell.append(header);
      wrap=el('div','sm-board-wrap');board=el('div','sm-board');board.setAttribute('role','region');board.setAttribute('aria-label','Карта этапов и целей');board.setAttribute('aria-describedby','sm-hint');board.tabIndex=0;
      const edges=document.createElementNS(NS,'svg');edges.setAttribute('class','sm-edges');edges.setAttribute('aria-hidden','true');const defs=document.createElementNS(NS,'defs');for(const [id,color]of [['sm-arrow','#777c7d'],['sm-lock-arrow','#e6b86d']]){const m=document.createElementNS(NS,'marker');for(const [k,v]of Object.entries({id,markerWidth:'7',markerHeight:'7',refX:'6',refY:'3.5',orient:'auto'}))m.setAttribute(k,v);const p=document.createElementNS(NS,'path');p.setAttribute('d','M0 0 6 3.5 0 7');p.setAttribute('stroke',color);p.setAttribute('stroke-width','1');p.setAttribute('fill','none');m.append(p);defs.append(m);}world=document.createElementNS(NS,'g');edges.append(defs,world);layer=el('div','sm-node-layer');board.append(edges,layer);wrap.append(board);
      controls=el('div','sm-controls');for(const [name,title,action]of [['plus','Приблизить карту',()=>zoom(1.22)],['minus','Отдалить карту',()=>zoom(1/1.22)],['reset','Вернуться к текущим этапам',reset]])controls.append(titledButton(name,title,action));wrap.append(controls);
      panel=el('section','sm-details');panel.id='sm-details';panel.hidden=true;panel.setAttribute('aria-labelledby','sm-detail-title');panelContent=el('div');panel.append(panelContent);wrap.append(panel);shell.append(wrap);
      const footer=el('div','sm-footer');footer.append(el('p','','Нажми на точку · двигай карту пальцем'));if(data.strategy?.drafts?.length){footer.append(button('Прежние наброски · '+data.strategy.drafts.length,'sm-legacy',legacy));}shell.append(footer);
      status=el('span','sm-sr');status.setAttribute('role','status');status.setAttribute('aria-live','polite');shell.append(status);root.append(shell);target.append(root);
      const pending=selectedId;layout();const old=savedCamera;if(old){Object.assign(camera,old);paint();}else reset();selectedId=pending;
      document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!document.querySelector('dialog[open]')&&!panel.hidden){e.preventDefault();closePanel();}},{signal:abort.signal});
      const pointers=new Map();let gesture=null;
      board.addEventListener('pointerdown',e=>{if(e.button!==0)return;panMoved=false;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===1)gesture={x:e.clientX,y:e.clientY,startX:camera.x,startY:camera.y};else if(pointers.size===2){const [a,b]=[...pointers.values()];gesture={distance:Math.hypot(a.x-b.x,a.y-b.y),scale:camera.scale,cx:(a.x+b.x)/2,cy:(a.y+b.y)/2,startX:camera.x,startY:camera.y};panMoved=true;}},opts);
      window.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2&&gesture?.distance){const [a,b]=[...pointers.values()],r=board.getBoundingClientRect(),cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top,ox=gesture.cx-r.left,oy=gesture.cy-r.top;camera.scale=Math.max(.65,Math.min(1.8,gesture.scale*Math.hypot(a.x-b.x,a.y-b.y)/gesture.distance));const ratio=camera.scale/gesture.scale;camera.x=cx-(ox-gesture.startX)*ratio;camera.y=cy-(oy-gesture.startY)*ratio;panMoved=true;}else if(pointers.size===1&&gesture?.x!==undefined){const dx=e.clientX-gesture.x,dy=e.clientY-gesture.y;if(!panMoved&&Math.hypot(dx,dy)<6)return;panMoved=true;camera.x=gesture.startX+dx;camera.y=gesture.startY+dy;}if(panMoved){clamp();paint();}},opts);
      const end=e=>{pointers.delete(e.pointerId);if(pointers.size===1){const a=[...pointers.values()][0];gesture={x:a.x,y:a.y,startX:camera.x,startY:camera.y};}else if(!pointers.size)gesture=null;};window.addEventListener('pointerup',end,opts);window.addEventListener('pointercancel',end,opts);
      board.addEventListener('wheel',e=>{e.preventDefault();const r=board.getBoundingClientRect();if(e.ctrlKey)zoom(Math.exp(-e.deltaY*.007),e.clientX-r.left,e.clientY-r.top);else{camera.x-=e.deltaX;camera.y-=e.deltaY;clamp();paint();}},{passive:false,signal:abort.signal});
      board.addEventListener('keydown',e=>{if(e.target!==board)return;const move={ArrowDown:[0,-70],ArrowUp:[0,70],ArrowLeft:[70,0],ArrowRight:[-70,0]}[e.key];if(move){e.preventDefault();camera.x+=move[0];camera.y+=move[1];clamp();paint();}if(e.key==='+'||e.key==='=')zoom(1.22);if(e.key==='-')zoom(1/1.22);},opts);
      observer=new ResizeObserver(()=>{if(!ready)return;paint();const p=nodes.find(n=>n.id===selectedId);if(p)ensureVisible(p);});observer.observe(board);ready=true;
      if(selectedId){const p=nodes.find(n=>n.id===selectedId);if(p)show(p);else if(selectedId.startsWith('stage:'))focusStage(selectedId.slice(6));else selectedId=null;}
    }
    function updateOptions(){select.replaceChildren();const all=el('option','','Все блоки · '+blocks.length);all.value='all';select.append(all);for(const b of blocks){const o=el('option','',b.name);o.value=b.id;select.append(o);}if(linked){const o=el('option','','Связанные этапы');o.value='linked';select.append(o);}if(scope!=='all'&&scope!=='linked'&&!blocks.some(b=>b.id===scope))scope='all';select.value=scope;}
    function layout(){
      nodes=[];dependencies=[];layer.replaceChildren();world.replaceChildren();panel.hidden=true;wrap.classList.remove('has-details');
      const shown=scope==='all'?blocks:scope==='linked'?blocks.filter(b=>linked?.includes(b.id)):blocks.filter(b=>b.id===scope);
      const counts=new Map();for(const g of data.goals)counts.set(g.stageId,(counts.get(g.stageId)||0)+1);
      const lists=shown.map(b=>M.list(data,b.id).filter(s=>scope!=='linked'||linkedStageIds.includes(s.id))),rows=Math.max(0,...lists.map(s=>s.length));let rowY=130;const ys=[];
      for(let i=0;i<rows;i++){ys.push(rowY);const goals=Math.max(0,...lists.map(s=>counts.get(s[i]?.id)||0));rowY+=Math.max(210,105+goals*65);}
      H=Math.max(350,rowY+10);W=Math.max(220,shown.length*215+10);
      const add=(kind,b,s,x,y,extra={})=>{const n={kind,b,s,x,y,id:kind==='block'?'block:'+b.id:kind==='goal'?'goal:'+extra.goal.id:stageKey(s.id),...extra};nodes.push(n);return n;};
      shown.forEach((b,index)=>{const x=30+index*215,color=colors[(Number(/^block-(\d+)$/.exec(b.id)?.[1]??[...b.id].reduce((n,c)=>n+c.charCodeAt(0),0)))%colors.length],stages=lists[index];b.mapColor=color;add('block',b,null,x,32);if(stages.length)edge(`M${x} 58V${ys[0]-23}`,color,'order',true);
        stages.forEach((s,i)=>{const y=ys[i];add('stage',b,s,x,y,{index:M.list(data,b.id).findIndex(actual=>actual.id===s.id)});const goals=data.goals.filter(g=>g.stageId===s.id);goals.forEach((goal,j)=>{const gy=y+82+j*65;add('goal',b,s,x+20,gy,{goal});edge(`M${x} ${j?gy-57:y+15}V${gy-16}Q${x} ${gy} ${x+14} ${gy}`,color,'goal-edge');});if(i<stages.length-1)edge(`M${x} ${y+Math.max(28,82+(goals.length-1)*65+16)}V${ys[i+1]-22}`,color,'order',true);});
      });
      for(const n of nodes.filter(n=>n.kind==='stage'&&n.s.lock.mode==='stage')){
        const source=nodes.find(p=>p.kind==='stage'&&p.s.id===n.s.lock.stageId);if(!source)continue;const rail=source.x===n.x?n.x-26:Math.max(source.x,n.x)-28,d=`M${source.x} ${source.y+14}V${source.y+48}H${rail}V${n.y-36}H${n.x}V${n.y-14}`;
        const path=edge(d,'var(--sm-lock)','dependency',true);dependencies.push({path,target:n.s.id,source:source.s.id});
      }
      if(!shown.length){const e=el('p','sm-empty','Создай первый блок времени, затем добавь этапы.');layer.append(e);}paint();
    }
    function edge(d,color,cls,arrow=false){const p=document.createElementNS(NS,'path');p.setAttribute('d',d);p.setAttribute('stroke',color);p.setAttribute('class',cls);if(arrow)p.setAttribute('marker-end','url(#'+(cls==='dependency'?'sm-lock-arrow':'sm-arrow')+')');world.append(p);return p;}
    function nodeButton(n){
      const current=n.s&&M.current(data,n.b.id).id===n.s.id,locked=n.s&&!M.unlocked(data,n.s),b=button('','sm-node '+n.kind+(current&&n.kind==='stage'?' current':'')+(locked?' locked':''),e=>{if(panMoved&&e.detail!==0)return;show(n);});
      b.dataset.node=n.id;b.setAttribute('aria-controls','sm-details');b.setAttribute('aria-expanded',String(n.id===selectedId));b.setAttribute('aria-label',n.kind==='block'?'Блок: '+n.b.name:n.kind==='goal'?'Цель: '+n.goal.name:(locked?'Заблокированный этап: ':current?'Текущий этап: ':'Этап: ')+n.s.name);b.style.setProperty('--c',n.kind==='goal'?'var(--sm-goal)':n.b.mapColor);
      const dot=el('span','sm-dot'),copy=el('span','sm-label');if(n.kind==='block')copy.textContent=label(n.b.name,44);else if(n.kind==='goal'){copy.textContent=label(n.goal.name,35);if(n.goal.completedDate)copy.append(document.createTextNode(' ✓'));}else{copy.append(el('span','sm-name',label(n.s.name,38)));const sub=el('span','sm-sub');if(locked)sub.append(icon('lock','sm-tiny-lock'));sub.append(document.createTextNode((current?'Сейчас · ':'')+'Этап '+(n.index+1)+(locked?' · закрыт':'')));copy.append(sub);}b.append(dot,copy);b.addEventListener('focus',()=>{if(b.matches(':focus-visible'))ensureVisible(n);});return b;
    }
    function paint(){if(!board)return;const w=board.clientWidth,h=board.clientHeight;world.setAttribute('transform',`translate(${camera.x} ${camera.y}) scale(${camera.scale})`);layer.style.setProperty('--label-width',Math.max(98,Math.min(142,215*camera.scale-40))+'px');
      for(const n of nodes){const x=camera.x+n.x*camera.scale,y=camera.y+n.y*camera.scale,visible=x>-180&&x<w+160&&y>-100&&y<h+100;
        if(visible){if(!n.button){n.button=nodeButton(n);layer.append(n.button);}n.button.style.left=x+'px';n.button.style.top=y+'px';n.button.classList.toggle('selected',n.id===selectedId);n.button.setAttribute('aria-expanded',String(n.id===selectedId));}else if(n.button){n.button.remove();n.button=null;}}
      for(const d of dependencies)d.path.classList.toggle('emphasis',d.target===selectedId?.slice(6)||d.source===selectedId?.slice(6));
      controls.children[0].disabled=camera.scale>=1.8;controls.children[1].disabled=camera.scale<=.65;
    }
    function clamp(){const w=board.clientWidth,h=board.clientHeight;camera.x=Math.min(w-65,Math.max(65-W*camera.scale,camera.x));camera.y=Math.min(h-60,Math.max(60-H*camera.scale,camera.y));}
    function reset(){closePanel(false);camera.scale=Math.max(.65,Math.min(1.1,(Math.min(board.clientWidth,580)-25)/440));camera.x=W<=240?(board.clientWidth-W*camera.scale)/2:12;camera.y=26;const currents=nodes.filter(n=>n.kind==='stage'&&M.current(data,n.b.id).id===n.s.id);if(currents.length){const y=Math.min(...currents.map(n=>n.y));camera.y=Math.min(26,120-y*camera.scale);}paint();}
    function zoom(factor,cx=board.clientWidth/2,cy=board.clientHeight/2){const next=Math.max(.65,Math.min(1.8,camera.scale*factor)),ratio=next/camera.scale;camera.x=cx-(cx-camera.x)*ratio;camera.y=cy-(cy-camera.y)*ratio;camera.scale=next;clamp();paint();}
    function ensureVisible(n){const side=!panel.hidden&&board.clientWidth>=650,left=18,right=side?panel.offsetLeft-24:board.clientWidth-12,top=24,bottom=panel.hidden||side?board.clientHeight-68:Math.max(80,panel.offsetTop-18),x=camera.x+n.x*camera.scale,y=camera.y+n.y*camera.scale;if(x<left)camera.x+=left-x;if(x+145>right)camera.x-=x+145-right;if(y<top)camera.y+=top-y;if(y+22>bottom)camera.y-=y+22-bottom;paint();}
    function closePanel(focus=true){const n=nodes.find(p=>p.id===selectedId);panel.hidden=true;wrap.classList.remove('has-details');selectedId=null;paint();if(focus){if(n?.button)n.button.focus({preventScroll:true});else board.focus({preventScroll:true});}}
    function writeButton(text,cls,action,glyph){const n=button(text,cls,action,glyph);n.disabled=!snap().healthy;return n;}
    function section(label,text,cls=''){const n=el('section','sm-section '+cls);n.append(el('p','sm-eyebrow',label));if(text)n.append(el('p','sm-copy',text));return n;}
    function lockBox(s){const n=el('div','sm-lock-box'),title=el('p','sm-lock-title');title.append(icon('lock'),document.createTextNode(M.unlocked(data,s)?'Условие выполнено':'Этап пока закрыт'));n.append(title);
      if(s.lock.mode==='manual'){n.append(el('p','','Закрыт вручную. Открыть его можно в настройках этапа.'));}
      else{const req=M.get(data,s.lock.stageId),owner=data.blocks.find(b=>b.id===req?.blockId);n.append(el('p','','Дойти до этапа «'+req.name+'» в блоке «'+owner.name+'».'));n.append(button('Показать связь на карте','sm-text-link',()=>{
        linked=[...new Set([s.blockId,req.blockId])];linkedStageIds=[s.id,req.id];scope='linked';updateOptions();layout();const target=nodes.find(n=>n.id===stageKey(s.id));selectedId=target.id;camera.x=12;camera.y=26;camera.scale=Math.max(.65,Math.min(1.1,(Math.min(board.clientWidth,580)-25)/440));show(target);
      },'arrow'));n.append(button('Показать нужный этап','sm-text-link',()=>focusStage(req.id),'arrow'));if(owner.archivedAt!==null){n.append(el('p','','Блок условия находится в архиве. Его можно восстановить в списке блоков.'));for(const b of n.querySelectorAll('button'))b.disabled=true;}}return n;
    }
    function show(n){
      selectedId=n.id;panelContent.replaceChildren();panel.style.setProperty('--c',n.b.mapColor);const head=el('div','sm-details-head'),copy=el('div');copy.append(el('p','sm-crumb',n.kind==='block'?'Блок времени':n.b.name+' · '+(n.kind==='goal'?'цель этапа':'этап '+(n.index+1))));const title=el('h2','',n.kind==='block'?n.b.name:n.kind==='goal'?n.goal.name:n.s.name);title.id='sm-detail-title';copy.append(title);const close=titledButton('close','Закрыть подробности',()=>closePanel());close.className='sm-close';head.append(copy,close);panelContent.append(head);
      if(n.kind==='block'){
        const stages=M.list(data,n.b.id),list=el('div','sm-stage-list');for(const s of stages){const b=button('','',()=>focusStage(s.id));b.append(el('span','',s.name),el('small','',M.current(data,n.b.id).id===s.id?'Сейчас':!M.unlocked(data,s)?'Закрыт':s.reached?'Уже был текущим':'Будущий'));list.append(b);}panelContent.append(list,writeButton('+ Добавить этап','button secondary full spaced',()=>host.addStage(n.b.id)));
      }else{
        const current=M.current(data,n.b.id).id===n.s.id;panelContent.append(el('p','sm-status',current?'Текущий этап':n.s.reached?'Этот этап уже был текущим':'Будущий этап'));
        if(n.s.lock.mode!=='open')panelContent.append(lockBox(n.s));
        if(n.kind==='goal'){
          panelContent.append(button('Открыть весь этап','sm-text-link',()=>focusStage(n.s.id),'arrow'));
          if(current||n.goal.completedDate)panelContent.append(writeButton(n.goal.completedDate?'Отменить достижение':'Цель достигнута','button secondary full spaced',()=>host.complete('goal',n.goal.id)));
        }else{
          if(n.s.meaning)panelContent.append(section('Смысл этапа',n.s.meaning));const goals=data.goals.filter(g=>g.stageId===n.s.id);for(const g of goals)panelContent.append(section(g.completedDate?'Цель · достигнута':'Цель',g.name,'goal-copy'));
          const tasks=data.tasks.filter(t=>t.stageId===n.s.id&&t.archivedAt===null);if(tasks.length){const part=section('Задания этапа');for(const t of tasks){const done=host.done(t),row=el('div','sm-task-row');if(current||done){const b=titledButton('check',(done?'Отменить выполнение: ':'Выполнить: ')+t.name,()=>host.complete('task',t.id));b.className='sm-task-check'+(done?' done':'');b.disabled=!snap().healthy;if(!done)b.setAttribute('aria-label','Выполнить: '+t.name);row.append(b);}else row.append(el('i','sm-task-dot'));row.append(el('span',done?'done-text':'',t.name));part.append(row);}panelContent.append(part);}
          if(!n.s.meaning&&!goals.length&&!tasks.length)panelContent.append(el('p','sm-copy','Этап пока пустой. Добавь смысл, цели или задания в блоке.'));
          const actions=el('div','sm-stage-actions');actions.append(button('Открыть этап в блоке','button secondary full',()=>host.openStage(n.s.id)));if(!current&&M.unlocked(data,n.s))actions.append(writeButton('Сделать текущим','button full',()=>host.makeCurrent(n.s.id)));actions.append(writeButton('Настроить этап','sm-text-link',()=>host.editStage(n.s.id),'more'));panelContent.append(actions);
        }
      }
      panel.hidden=false;panel.scrollTop=0;wrap.classList.add('has-details');status.textContent=title.textContent;paint();requestAnimationFrame(()=>{if(ready&&selectedId===n.id&&nodes.includes(n))ensureVisible(n);});
    }
    function focusStage(id){selectedId=stageKey(id);if(!ready)return;const s=M.get(data,id);if(!s)return;
      if(!nodes.some(n=>n.id===selectedId)){scope=s.blockId;linked=null;updateOptions();layout();camera.x=(board.clientWidth-W*camera.scale)/2;}
      const n=nodes.find(n=>n.id===selectedId);if(n)show(n);
    }
    function stageList(){
      if(scope!=='all'&&scope!=='linked'){const n=nodes.find(n=>n.kind==='block');if(n)show(n);return;}
      textDialog(host,'Этапы какого блока?',dialog=>{const choice=el('select');choice.setAttribute('aria-label','Выбрать блок для списка этапов');for(const b of blocks){const option=el('option','',b.name);option.value=b.id;choice.append(option);}const open=button('Показать этапы','button full spaced',()=>{scope=choice.value;linked=null;selectedId=null;updateOptions();layout();reset();dialog.close();const n=nodes.find(n=>n.kind==='block');if(n)show(n);});open.disabled=!blocks.length;dialog.append(choice,open);});
    }
    function addStage(){if(scope!=='all'&&scope!=='linked'){host.addStage(scope);return;}textDialog(host,'В каком блоке добавить этап?',dialog=>{const select=el('select');select.setAttribute('aria-label','Блок для нового этапа');for(const b of blocks){const option=el('option','',b.name);option.value=b.id;select.append(option);}const next=button('Продолжить','button full spaced',()=>{const value=select.value;dialog.close();host.addStage(value);});next.disabled=!blocks.length;dialog.append(select,next);});}
    function legacy(){textDialog(host,'Прежние наброски',dialog=>{dialog.append(el('p','meta','Сохранены из предыдущей версии. Они не меняют этапы автоматически.'));for(const d of data.strategy.drafts){const article=el('article','card');article.append(el('h3','',d.name));if(d.description)article.append(el('p','meta',d.description));dialog.append(article);}});}
    function unmount(){if(ready)savedCamera={...camera};ready=false;observer?.disconnect();observer=null;abort?.abort();abort=null;root=null;}
    function widget(){const {data}=snap(),blocks=data.blocks.filter(b=>b.archivedAt===null),stages=data.blockStages.items.filter(s=>blocks.some(b=>b.id===s.blockId)),box=el('div','lg-s-widget');box.append(el('h3','','Мой путь по этапам'),el('p','meta',blocks.length+' блоков · '+stages.length+' этапов · '+stages.filter(s=>!M.unlocked(data,s)).length+' закрыто'),button('Открыть стратегию','button secondary full',()=>host.navigate()));return box;}
    return {mount,unmount,widget,focusStage};
  }
  globalThis.LifeGameStageMap={create};
})();
