/* LifeGame Strategy: references to real records, future drafts, and a disposable map view. */
'use strict';
(() => {
  const kinds = ['cause','meaning','goal','task'];
  const labels = {root:'Я сейчас',block:'Сфера',cause:'Причина',meaning:'Смысл',goal:'Цель',task:'Дело'};
  const glyphs = {root:'◎',block:'◈',cause:'!',meaning:'♡',goal:'⚑',task:'✓'};
  const colors = {root:'var(--accent)',block:'#7fd5df',cause:'#f19aaa',meaning:'#c0a0f0',goal:'#8fb7ff',task:'#edc671'};
  const blank = () => ({version:1,drafts:[],links:[]});
  const ref = (kind,id) => kind+':'+id;
  const split = key => [key.slice(0,key.indexOf(':')),key.slice(key.indexOf(':')+1)];
  const object = x => x && typeof x==='object' && !Array.isArray(x);
  const idOK = x => typeof x==='string' && x.length>0 && x.length<=2048;
  const refOK = x => idOK(x) && ['block','meaning','goal','task','draft'].includes(split(x)[0]) && !!split(x)[1];
  function validate(data) {
    if (data.strategy===undefined) data.strategy=blank();
    const s=data.strategy, bad=()=>{throw new Error('Повреждены данные Стратегии.');};
    if(!object(s)||s.version!==1||!Array.isArray(s.drafts)||!Array.isArray(s.links)||s.drafts.length>2000||s.links.length>10000)bad();
    const ids=new Set(), actuals=new Set(), byId=new Map();
    for(const n of s.drafts){
      if(!object(n)||!idOK(n.id)||ids.has(n.id)||!kinds.includes(n.kind)||typeof n.name!=='string'||!n.name.trim()||n.name.length>120||typeof n.description!=='string'||n.description.length>2000||(n.blockId!==null&&!idOK(n.blockId))||!['all','any'].includes(n.reqMode))bad();
      if(n.actual!==null){
        if(!object(n.actual)||!['goal','task'].includes(n.kind)||n.actual.kind!==n.kind||!idOK(n.actual.id)||actuals.has(ref(n.actual.kind,n.actual.id)))bad();
        actuals.add(ref(n.actual.kind,n.actual.id));
      }
      ids.add(n.id);byId.set(n.id,n);
    }
    ids.clear();const pairs=new Set(), adj=new Map();
    const aliases=new Map(s.drafts.filter(d=>d.actual).map(d=>[ref(d.actual.kind,d.actual.id),ref("draft",d.id)]));
    const canonical=k=>aliases.get(k)||k;
    for(const e of s.links){
      if(!object(e)||!idOK(e.id)||ids.has(e.id)||!refOK(e.from)||!refOK(e.to)||e.from===e.to||!['related','helpful','required'].includes(e.kind))bad();
      for(const k of [e.from,e.to])if(split(k)[0]==='draft'&&!byId.has(split(k)[1]))bad();
      if(canonical(e.from)===canonical(e.to))bad();
      const pair=JSON.stringify([canonical(e.from),canonical(e.to)]);if(pairs.has(pair))bad();pairs.add(pair);ids.add(e.id);
      if(e.kind==='required'){
        const [fk,fi]=split(e.from),[tk,ti]=split(e.to);
        if(!['task','goal','draft'].includes(fk)||(fk==='draft'&&!['goal','task'].includes(byId.get(fi).kind))||tk!=='draft'||!['goal','task'].includes(byId.get(ti).kind))bad();
        const a=canonical(e.from),b=canonical(e.to);if(!adj.has(a))adj.set(a,[]);adj.get(a).push(b);
      }
    }
    // Iterative topological check: no recursion limit, including imported graphs.
    const indegree=new Map();for(const [a,bs]of adj){if(!indegree.has(a))indegree.set(a,0);for(const b of bs)indegree.set(b,(indegree.get(b)||0)+1);}
    const queue=[...indegree].filter(([,d])=>!d).map(([a])=>a);let count=0;
    for(let i=0;i<queue.length;i++){count++;for(const b of adj.get(queue[i])||[]){indegree.set(b,indegree.get(b)-1);if(!indegree.get(b))queue.push(b);}}
    if(count!==indegree.size)throw new Error('Условия образуют замкнутый круг. Удали одну из обязательных связей.');
    return s;
  }
  function project(data,date) {
    const s=data.strategy||blank(),nodes=new Map(), structural=[], aliases=new Map();
    for(const d of s.drafts)if(d.actual)aliases.set(ref(d.actual.kind,d.actual.id),ref('draft',d.id));
    const key=(kind,id)=>aliases.get(ref(kind,id))||ref(kind,id);
    const blocks=new Map(data.blocks.map(b=>[b.id,b]));
    const blockActive=id=>id==='lifegame:inbox'||blocks.get(id)?.archivedAt===null;
    const add=(n)=>nodes.set(n.key,n);
    add({key:'root',kind:'root',name:'Я сейчас',active:true,done:false,blockId:null});
    for(const b of data.blocks)if(b.archivedAt===null){
      add({key:ref('block',b.id),kind:'block',id:b.id,name:b.name,blockId:b.id,active:true,done:false});
      structural.push({from:'root',to:ref('block',b.id),kind:'structural'});
      if(b.meaning){add({key:ref('meaning',b.id),kind:'meaning',id:b.id,name:b.meaning,blockId:b.id,active:true,done:false});structural.push({from:ref('block',b.id),to:ref('meaning',b.id),kind:'structural'});}
    }
    if(data.tasks.some(t=>t.block==='lifegame:inbox'&&t.archivedAt===null)){
      add({key:ref('block','lifegame:inbox'),kind:'block',id:'lifegame:inbox',name:'Входящие',blockId:'lifegame:inbox',active:true,done:false});structural.push({from:'root',to:ref('block','lifegame:inbox'),kind:'structural'});
    }
    const actualNode=(kind,id)=>{
      const obj=(kind==='goal'?data.goals:data.tasks).find(x=>x.id===id),blockId=obj?(kind==='goal'?obj.blockId:obj.block):null;
      const active=!!obj&&blockActive(blockId)&&(kind==='goal'||obj.archivedAt===null);
      let done=false;
      if(kind==='goal')done=!!obj?.completedDate||data.diamondRecords.some(r=>r.goalId===id);
      else if(obj)done=data.completions.some(r=>r.taskId===id&&(r.date===date||(obj.type==='once'&&(r.taskType==='once'||(r.taskType===undefined&&!obj.historySeparated)))));
      else done=data.completions.some(r=>r.taskId===id&&r.taskType==='once');
      return {key:key(kind,id),kind,id,name:obj?.name||(kind==='goal'?'Недоступная цель':'Недоступное дело'),blockId,active,done,repeat:kind==='task'&&obj?.type==='daily',gate:kind==='goal'||(obj?obj.type==='once':done),missing:!obj};
    };
    for(const g of data.goals){const n=actualNode('goal',g.id);if(n.active)add(n);}
    for(const t of data.tasks){const n=actualNode('task',t.id);if(n.active)add(n);}
    for(const d of s.drafts){
      const n=d.actual?actualNode(d.actual.kind,d.actual.id):{key:ref('draft',d.id),kind:d.kind,name:d.name,blockId:d.blockId,active:false,done:false,gate:['goal','task'].includes(d.kind)};
      Object.assign(n,{draftId:d.id,description:d.description,reqMode:d.reqMode,future:!d.actual});add(n);
    }
    const links=s.links.map(e=>({...e,from:aliases.get(e.from)||e.from,to:aliases.get(e.to)||e.to}));
    for(const e of links)for(const k of [e.from,e.to])if(!nodes.has(k)){
      const [kind,id]=split(k);
      if(['goal','task'].includes(kind))add({...actualNode(kind,id),key:k});
      else add({key:k,kind,name:'Недоступный элемент',blockId:null,active:false,done:false,missing:true});
    }
    for(const n of nodes.values()){
      if(['root','block'].includes(n.kind)||(!n.active&&!n.future))continue;
      let parent=n.blockId&&nodes.has(ref('block',n.blockId))?ref('block',n.blockId):'root';
      if(n.kind==='task'&&n.active){const task=data.tasks.find(t=>t.id===n.id);if(task?.goalId&&nodes.has(key('goal',task.goalId)))parent=key('goal',task.goalId);}
      if(!structural.some(e=>e.to===n.key))structural.push({from:parent,to:n.key,kind:'structural'});
    }
    const incoming=new Map(),children=new Map();
    for(const e of links)if(e.kind==='required'){if(!incoming.has(e.to))incoming.set(e.to,[]);incoming.get(e.to).push(e);}
    for(const e of structural){if(!children.has(e.from))children.set(e.from,[]);children.get(e.from).push(e.to);}
    const satisfied=k=>{const n=nodes.get(k);return !!n?.done&&!!n.gate;};
    const requirements=k=>incoming.get(k)||[];
    const unmet=k=>{const es=requirements(k);return nodes.get(k)?.reqMode==='any'&&es.some(e=>satisfied(e.from))?[]:es.filter(e=>!satisfied(e.from));};
    const ready=k=>unmet(k).length===0;
    // Only concrete unfinished real tasks are executable steps. Context never becomes a checkbox.
    function path(target,includeHistory=false){
      const keep=new Set([target]),todo=[target],seen=new Set();
      for(let i=0;i<todo.length;i++){
        const k=todo[i];if(seen.has(k))continue;seen.add(k);
        for(const e of includeHistory?requirements(k):unmet(k)){keep.add(e.from);todo.push(e.from);}
        const n=nodes.get(k);
        if(n?.active&&n.kind==='goal'&&!n.done)for(const child of children.get(k)||[]){const c=nodes.get(child);if(c?.kind==='task'&&(includeHistory||!c.done)&&c.active){keep.add(child);todo.push(child);}}
      }
      const tasks=[...keep].map(k=>nodes.get(k)).filter(n=>n?.kind==='task'&&n.active&&!n.done);
      const drafts=[...keep].map(k=>nodes.get(k)).filter(n=>n?.future&&['goal','task'].includes(n.kind)&&ready(n.key));
      return {keys:keep,tasks,drafts};
    }
    return {nodes,links,structural,children,requirements,unmet,ready,satisfied,path};
  }
  const api={blank,validate,project};
  globalThis.LifeGameStrategy=api;
})();

(() => {
  const API=globalThis.LifeGameStrategy;
  const titles={root:'Я сейчас',block:'Сфера',cause:'Причина',meaning:'Смысл',goal:'Цель',task:'Дело'};
  const marks={root:'◎',block:'◈',cause:'!',meaning:'♡',goal:'⚑',task:'✓'};
  const tones={root:'var(--accent)',block:'#7fd5df',cause:'#f19aaa',meaning:'#c0a0f0',goal:'#8fb7ff',task:'#edc671'};
  const make=(tag,cls='',text)=>{const e=document.createElement(tag);e.className=cls;if(text!==undefined)e.textContent=text;return e;};
  const button=(text,fn,primary=false)=>{const b=make('button','button'+(primary?'':' secondary'),text);b.type='button';b.addEventListener('click',fn);return b;};
  const svg=(tag,attrs)=>{const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v]of Object.entries(attrs||{}))e.setAttribute(k,v);return e;};
  const copy=x=>JSON.parse(JSON.stringify(x));
  API.create=host=>{
    let selected=null,scope='overview',past=false,query='',undo=[],dialogSerial=0,observer=null,abort=null,camera=null,lastKeys='';
    try{const p=JSON.parse(localStorage.getItem('lifegame-strategy-view-v1'));if(p?.version===1){selected=typeof p.selected==='string'?p.selected:null;scope=['overview','branch','path','actions'].includes(p.scope)?p.scope:'overview';past=p.past===true;}}catch{}
    const saveView=()=>{try{localStorage.setItem('lifegame-strategy-view-v1',JSON.stringify({version:1,selected,scope,past}));}catch{}};
    const refresh=()=>{saveView();host.redraw();};
    const model=()=>{const r=host.read();return {...r,graph:API.project(r.data,r.date)};};
    const choose=(key,mode)=>{selected=key;if(mode)scope=mode;query='';camera=null;refresh();requestAnimationFrame(()=>document.querySelector('.lg-s-details')?.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));};
    function mutate(change,expected,record=true){
      const before=copy(host.read().data.strategy);
      const ok=host.change(s=>{if(expected&&JSON.stringify(s)!==expected)throw new Error('Карта изменилась. Открой окно заново и повтори действие.');change(s);});
      if(ok&&record){undo.push({before,after:JSON.stringify(host.read().data.strategy)});if(undo.length>25)undo.shift();refresh();}return ok;
    }
    function dialog(title,build){
      const d=make('dialog','lg-strategy-dialog'),form=make('form'),h=make('h2','',title),error=make('p','ui-dialog-error');error.hidden=true;error.setAttribute('role','alert');
      d.setAttribute('aria-label',title);form.append(h);d.append(form);document.body.append(d);d.addEventListener('close',()=>d.remove(),{once:true});
      const serial=++dialogSerial;let index=0;
      const field=(label,input)=>{const l=make('label','',label);input.id='lg-strategy-field-'+serial+'-'+(++index);l.htmlFor=input.id;form.append(l,input);return input;};
      const finish=(label,submit)=>{
        const actions=make('div','form-actions');actions.append(button('Отмена',()=>d.close()));const save=make('button','button',label);save.type='submit';actions.append(save);form.append(error,actions);
        form.addEventListener('submit',e=>{e.preventDefault();try{if(submit()===true)d.close();else{error.hidden=false;error.textContent='Изменение не сохранено. Проверь сообщение приложения и повтори после обновления данных.';}}catch(ex){error.hidden=false;error.textContent=ex.message;}});
      };
      build({d,form,field,finish});host.showDialog(d);return d;
    }
    const input=(value='',type='text')=>{const e=make('input');e.type=type;e.value=String(value);return e;};
    const select=(values,value)=>{const e=make('select');for(const [id,label]of values){const o=make('option','',label);o.value=id;e.append(o);}e.value=value;return e;};
    function editDraft(key=null){
      const r=model(),old=key?r.data.strategy.drafts.find(d=>'draft:'+d.id===key):null,expected=JSON.stringify(r.data.strategy);
      if(old?.actual)return;
      dialog(old?'Изменить набросок':'Будущая ветка',({form,field,finish})=>{
        form.append(make('p','meta','Сохраняется в стратегии. Реальное дело или цель появится после «Взять в работу».'));
        const kind=field('Что добавить',select([['task','Дело'],['goal','Цель'],['meaning','Смысл'],['cause','Причина']],old?.kind||'task'));
        if(old)kind.disabled=true;
        const name=field('Название *',input(old?.name||''));name.maxLength=120;name.required=true;
        const description=field('Подробности · необязательно',make('textarea'));description.maxLength=2000;description.value=old?.description||'';
        const block=field('Сфера',select([['','Без выбранной сферы'],...r.data.blocks.filter(b=>b.archivedAt===null).map(b=>[b.id,b.name])],old?.blockId||r.graph.nodes.get(selected)?.blockId||''));
        finish(old?'Сохранить':'Добавить',()=>{
          if(!name.value.trim())throw new Error('Напиши название.');
          return mutate(s=>{
            if(old){const actual=s.drafts.find(d=>d.id===old.id);if(!actual||actual.actual)throw new Error('Набросок уже изменён.');Object.assign(actual,{name:name.value.trim(),description:description.value.trim(),blockId:block.value||null});}
            else {const id=host.uid();s.drafts.push({id,kind:kind.value,name:name.value.trim(),description:description.value.trim(),blockId:block.value||null,reqMode:'all',actual:null});selected='draft:'+id;scope='branch';}
          },expected);
        });
      });
    }
    function connect(key,edit=null){
      const r=model(),n=r.graph.nodes.get(key),expected=JSON.stringify(r.data.strategy);
      dialog(edit?'Изменить связь':'Связать элементы',({form,field,finish})=>{
        form.append(make('p','meta','«Связано» и «Помогает» ничего не блокируют. Для условия выбери направление: результат → будущая ветка.'));
        const choices=[...r.graph.nodes.values()].filter(n=>n.kind!=='root'&&!n.missing).map(n=>[n.key,titles[n.kind]+' · '+n.name.slice(0,100)]);
        const from=field('Откуда',select(choices,edit?.from||key));
        const to=field('Куда',select(choices,edit?.to||choices.find(([k])=>k!==key)?.[0]));
        const kind=field('Роль связи',select([['related','Связано'],['helpful','Помогает'],['required','Обязательное условие']],edit?.kind||'related'));
        finish('Сохранить связь',()=>{
          const a=r.graph.nodes.get(from.value),b=r.graph.nodes.get(to.value);
          if(from.value===to.value)throw new Error('Выбери два разных элемента.');
          if(kind.value==='required'&&(!a?.gate||a.repeat||(!a.active&&!a.future)||!b?.future||!['goal','task'].includes(b.kind)))throw new Error('Условие: достигнутая цель или разовое дело → будущая цель или дело. Повторяемое дело не завершается навсегда.');
          return mutate(s=>{if(edit)s.links=s.links.filter(e=>e.id!==edit.id);s.links.push({id:edit?.id||host.uid(),from:from.value,to:to.value,kind:kind.value});},expected);
        });
      });
    }
    function activate(key){
      const r=model(),n=r.graph.nodes.get(key),expected=JSON.stringify(r.data.strategy);
      if(!n?.future||!['task','goal'].includes(n.kind))return;
      dialog('Взять в работу',({form,field,finish})=>{
        form.append(make('p','',n.name),make('p','meta','Создаст '+(n.kind==='goal'?'цель':'разовое дело')+' в LifeGame. В план дня автоматически не добавляется. Выплат сейчас не будет.'));
        const options=r.data.blocks.filter(b=>b.archivedAt===null).map(b=>[b.id,b.name]);if(n.kind==='task')options.unshift(['lifegame:inbox','Входящие']);
        const block=field('Где создать *',select(options,n.blockId||options[0]?.[0]||''));block.required=true;
        const name=field('Название *',input(n.name));name.maxLength=120;name.required=true;
        const reward=field(n.kind==='goal'?'Награда за достижение · алмазы':'Награда за выполнение · монеты',input(n.kind==='goal'?5:15,'number'));reward.min='1';reward.max='100000';reward.step='1';reward.required=true;
        let goal=null;
        if(n.kind==='task'){
          goal=field('Связать с целью · необязательно',select([['','Без цели']],''));
          const fill=()=>{goal.replaceChildren();const opts=[['','Без цели'],...r.data.goals.filter(g=>g.blockId===block.value&&g.completedDate===null).map(g=>[g.id,g.name])];for(const [id,name]of opts){const o=make('option','',name);o.value=id;goal.append(o);}};
          block.addEventListener('change',fill);fill();
        }
        finish('Создать в LifeGame',()=>{
          const amount=Number(reward.value);if(!Number.isSafeInteger(amount)||amount<1||amount>100000)throw new Error('Награда — целое число от 1 до 100000.');
          const ok=host.activate(n.draftId,{blockId:block.value,name:name.value.trim(),reward:amount,goalId:goal?.value||null},expected,r.date);
          if(ok){undo=[];scope='branch';refresh();}return ok;
        });
      });
    }
    function removeDraft(n){
      dialog('Удалить набросок?',({form,finish})=>{
        const expected=JSON.stringify(host.read().data.strategy);form.append(make('p','',n.name),make('p','meta','Удалится только этот набросок и его линии. Остальные элементы, реальные дела и история останутся.'));
        finish('Удалить набросок',()=>mutate(s=>{const d=s.drafts.find(d=>d.id===n.draftId);if(!d||d.actual)throw new Error('Действующий элемент нельзя удалить через карту.');s.drafts=s.drafts.filter(d=>d.id!==n.draftId);s.links=s.links.filter(e=>e.from!==n.key&&e.to!==n.key);selected=null;scope='overview';},expected));
      });
    }
    function status(n,g){
      if(n.missing)return n.done?'Есть факт в истории · объект недоступен':'Объект недоступен';
      if(n.done)return n.repeat?'Выполнено сегодня':'Выполнено';
      if(n.future)return ['goal','task'].includes(n.kind)?g.ready(n.key)?'Будущее · доступно':'Будущее · есть условия':'Набросок';
      if(!n.active)return 'В архиве';
      return n.repeat?'Повторяемое дело':'В моей жизни';
    }
    function nodeButton(n,mode){const b=button(marks[n.kind]+' '+n.name,()=>choose(n.key,mode));b.classList.add('lg-s-node-link');return b;}
    function list(container,ns,mode){
      if(!ns.length){container.append(make('p','meta','Здесь пока нет элементов.'));return;}
      for(const n of ns){const row=make('div','lg-s-list-row');row.append(nodeButton(n,mode));container.append(row);}
    }
    function mount(container){
      unmount();const r=model(),g=r.graph;if(selected&&!g.nodes.has(selected)){selected=null;scope='overview';}
      const section=make('section','lg-strategy');container.append(section);
      const head=make('div','lg-s-heading'),add=button('＋ Ветка',()=>editDraft(),true);add.disabled=!r.healthy;head.append(make('h1','','Стратегия'),add);section.append(head,make('p','meta','Выбери сферу, чтобы увидеть её цели и дела. Кнопка «Ветка» добавляет набросок будущего.'));
      const tabs=make('div','lg-s-tabs');
      for(const [id,label]of [['overview','Сферы'],['actions','Что делать сейчас'],['path','Путь']]){
        const b=button(label,()=>{scope=id;camera=null;refresh();});b.setAttribute('aria-pressed',String(scope===id));if(id==='path')b.disabled=!selected;tabs.append(b);
      }
      const historyLabel=make('label','lg-s-history'),check=input('','checkbox');check.checked=past;check.addEventListener('change',()=>{past=check.checked;camera=null;refresh();});historyLabel.append(check,document.createTextNode('Показать выполненное'));tabs.append(historyLabel);section.append(tabs);
      const search=input(query,'search');search.placeholder='Найти цель, дело или набросок';search.setAttribute('aria-label','Поиск в стратегии');section.append(search);
      const results=make('div','lg-s-search');section.append(results);const drawSearch=()=>{results.replaceChildren();if(query.trim())list(results,[...g.nodes.values()].filter(n=>n.name.toLocaleLowerCase().includes(query.toLocaleLowerCase())).slice(0,30),'branch');};
      search.addEventListener('input',()=>{query=search.value;drawSearch();});drawSearch();
      if(scope==='actions'){
        const tasks=[...g.nodes.values()].filter(n=>n.active&&n.kind==='task'&&!n.done);
        const ready=[...g.nodes.values()].filter(n=>n.future&&['goal','task'].includes(n.kind)&&g.ready(n.key));
        section.append(make('h2','','Доступные дела'));list(section,tasks,'branch');section.append(make('h2','','Можно взять в работу'));list(section,ready,'path');
        if(!tasks.length&&!ready.length)section.append(make('p','','Выбери сферу, создай обычное дело или набросок будущего.'));
      } else {
        let ns=[];
        if(scope==='overview')ns=[...g.nodes.values()].filter(n=>['root','block'].includes(n.kind));
        else if(scope==='path'&&selected){
          const p=g.path(selected,past),keys=new Set(['root',...p.keys]);for(const k of p.keys){const n=g.nodes.get(k);if(n?.blockId&&g.nodes.has('block:'+n.blockId))keys.add('block:'+n.blockId);}ns=[...keys].map(k=>g.nodes.get(k)).filter(Boolean);
          const steps=make('div','lg-s-next');steps.append(make('h2','','Ближайшие действия'));list(steps,p.tasks,'branch');
          if(p.drafts.length){steps.append(make('p','meta','Эти ветки уже доступны:'));list(steps,p.drafts,'branch');}
          if(!p.tasks.length&&!p.drafts.length)steps.append(make('p','meta','Проверь результат цели или добавь конкретное дело. Смыслы и причины не требуют галочки выполнения.'));
          section.append(steps);
        } else if(selected){
          const n=g.nodes.get(selected),keys=new Set(['root',selected]);
          if(n.blockId){keys.add('block:'+n.blockId);for(const v of g.nodes.values())if(v.blockId===n.blockId)keys.add(v.key);}
          else for(const k of g.children.get(selected)||[])keys.add(k);
          for(const e of g.requirements(selected))keys.add(e.from);
          ns=[...keys].map(k=>g.nodes.get(k)).filter(Boolean);
        }
        const completed=ns.filter(n=>n.done&&n.key!==selected);
        if(!past)ns=ns.filter(n=>!n.done||n.key===selected);
        if(!ns.length)ns=[g.nodes.get('root')];
        const fullCount=ns.length;ns=ns.slice(0,120);
        section.append(make('p','meta',(!past&&completed.length?'Пройдено: '+completed.length+' · скрыто из карты. ':'')+(fullCount>120?'На карте первые 120 элементов; остальные доступны через поиск.':'Нажми круг, чтобы увидеть детали. Карту можно двигать и увеличивать.')));
        const mapBox=make('div','lg-s-map');section.append(mapBox);drawMap(mapBox,ns,g);
        const accessible=make('details','lg-s-text-map');accessible.append(make('summary','','Элементы карты списком'));list(accessible,ns.filter(n=>n.kind!=='root'),'branch');section.append(accessible);
      }
      if(selected&&g.nodes.has(selected))details(section,g.nodes.get(selected),r);
      const bottom=make('div','lg-s-bottom');const back=button('К сферам',()=>{selected=null;scope='overview';camera=null;refresh();});bottom.append(back);
      const undoButton=button('Отменить правку карты',()=>{
        const item=undo[undo.length-1];if(!item)return;
        if(JSON.stringify(host.read().data.strategy)!==item.after){undo=[];host.notify('Карта уже изменилась. Отмена старой правки недоступна.');refresh();return;}
        const ok=mutate(s=>{s.drafts=copy(item.before.drafts);s.links=copy(item.before.links);},item.after,false);if(ok){undo.pop();refresh();}
      });undoButton.disabled=!undo.length||!r.healthy;bottom.append(undoButton);section.append(bottom);

    }
    function details(section,n,r){
      const g=r.graph,box=make('article','card lg-s-details');box.dataset.strategyNode=n.key;box.setAttribute('aria-label','Выбранный элемент');
      box.append(make('p','lg-s-kind',marks[n.kind]+' '+titles[n.kind]+' · '+status(n,g)),make('h2','',n.name));
      if(n.description)box.append(make('p','',n.description));
      if(n.repeat)box.append(make('p','meta','Выполнение относится к сегодняшнему дню. Это дело не завершается навсегда и не используется как постоянное условие.'));
      const req=g.requirements(n.key);
      if(req.length){
        box.append(make('h3','','Условия · '+(n.reqMode==='any'?'достаточно любого':'нужны все')));
        if(n.future&&['goal','task'].includes(n.kind)){
          const mode=select([['all','Все условия'],['any','Любое условие']],n.reqMode);mode.setAttribute('aria-label','Правило открытия');mode.disabled=!r.healthy;
          mode.addEventListener('change',()=>mutate(s=>{const d=s.drafts.find(d=>d.id===n.draftId);d.reqMode=mode.value;},JSON.stringify(r.data.strategy)));box.append(mode);
        }
        for(const e of req){const source=g.nodes.get(e.from),row=make('div','lg-s-condition');row.append(make('span','',g.satisfied(e.from)?'✓':'○'),nodeButton(source,'branch'));box.append(row);}
        if(!n.future&&!g.ready(n.key))box.append(make('p','meta','Условие изменилось. Действующий элемент остаётся доступным; проверь свой путь.'));
      }
      const actions=make('div','lg-s-actions');
      const write=(label,fn,primary=false)=>{const b=button(label,fn,primary);b.dataset.write='';b.disabled=!r.healthy;actions.append(b);return b;};
      if(n.active&&['task','goal','block','meaning'].includes(n.kind))actions.append(button('Открыть в LifeGame',()=>host.open(n)));
      if(n.active&&n.kind==='task'){
        const planned=r.planned.includes(n.id),plan=write(planned?'В плане на сегодня':'На сегодня',()=>host.plan(n.id,r.date));plan.disabled=planned||n.done||!r.healthy||!r.scheduled.includes(n.id);
        const start=write('Начать 2 минуты',()=>host.start(n.id,r.date),true);start.disabled=!planned||n.done||!r.healthy||!r.focusReady;
        write(n.done?'Отменить выполнение':'Выполнить дело',()=>host.complete(n.kind,n.id,r.date,n.done));
      }
      if(n.active&&n.kind==='goal'){
        write(n.done?'Отменить достижение':'Цель достигнута',()=>host.complete(n.kind,n.id,r.date,n.done));
        if(!n.done)write('Добавить дело к цели',()=>host.createTask(n));
      }
      if(n.future){
        if(['task','goal'].includes(n.kind)){const b=write(g.ready(n.key)?'Взять в работу':'Сначала выполни условия',()=>activate(n.key),true);b.disabled=!g.ready(n.key)||!r.healthy;}
        write('Изменить набросок',()=>editDraft(n.key));write('Удалить набросок',()=>removeDraft(n));
      }
      if(n.kind!=='root')write('Связать элементы',()=>connect(n.key));
      actions.append(button('Показать путь',()=>choose(n.key,'path')));box.append(actions);
      const links=g.links.filter(e=>e.from===n.key||e.to===n.key);
      if(links.length){
        const listBox=make('details','lg-s-links');listBox.append(make('summary','','Связи ('+links.length+')'));
        for(const e of links){const row=make('div','lg-s-link-row');row.append(make('p','',(g.nodes.get(e.from)?.name||'Недоступный элемент')+' → '+(g.nodes.get(e.to)?.name||'Недоступный элемент')+' · '+({related:'Связано',helpful:'Помогает',required:'Условие'}[e.kind])));
          const edit=button('Изменить',()=>connect(n.key,e)),remove=button('Убрать линию',()=>mutate(s=>{s.links=s.links.filter(x=>x.id!==e.id);},JSON.stringify(r.data.strategy)));edit.disabled=remove.disabled=!r.healthy;row.append(edit,remove);listBox.append(row);}
        box.append(listBox);
      }
      section.append(box);
    }
    function drawMap(box,ns,g){
      const map=svg('svg',{role:'group','aria-label':'Карта стратегии'}),world=svg('g'),edgeLayer=svg('g'),nodeLayer=svg('g');world.append(edgeLayer,nodeLayer);map.append(world);box.append(map);
      const control=make('div','lg-s-map-tools');box.append(control);
      let width=box.clientWidth||350,height=460,points=new Map(),drag=null,pointers=new Map(),pinch=null;
      const signature=scope+'|'+selected+'|'+past+'|'+Math.round(box.clientWidth)+'|'+ns.map(n=>n.key).join('|');if(signature!==lastKeys){camera=null;lastKeys=signature;}
      function layout(){
        const nextWidth=box.clientWidth||350;if(Math.abs(nextWidth-width)>1)camera=null;width=nextWidth;map.setAttribute('viewBox','0 0 '+width+' '+height);points.clear();
        const cols=width<600?2:4,cell=160;let row=0;
        const roots=ns.filter(n=>n.kind==='root');for(const n of roots)points.set(n.key,{x:0,y:0});
        const others=ns.filter(n=>n.kind!=='root');
        // Remaining obligations determine rows. Completed history is never used as extra distance.
        const parents=new Map(g.structural.map(e=>[e.to,e.from]));
        const rank=new Map();for(const n of others){let depth=1,parent=parents.get(n.key),seen=new Set([n.key]);while(parent&&parent!=='root'&&points.has(parent)===false&&!seen.has(parent)){seen.add(parent);if(others.some(v=>v.key===parent))depth++;parent=parents.get(parent);}rank.set(n.key,depth);}
        for(let i=0;i<others.length;i++){let changed=false;for(const n of others)for(const e of g.unmet(n.key))if(rank.has(e.from)){const next=(rank.get(e.from)||1)+1;if(next>rank.get(n.key)){rank.set(n.key,next);changed=true;}}if(!changed)break;}
        const groups=new Map();for(const n of others){const r=rank.get(n.key);if(!groups.has(r))groups.set(r,[]);groups.get(r).push(n);}
        for(const [,group]of [...groups].sort((a,b)=>a[0]-b[0]))for(let offset=0;offset<group.length;offset+=cols){row++;const slice=group.slice(offset,offset+cols);slice.forEach((n,i)=>points.set(n.key,{x:(i-(slice.length-1)/2)*cell,y:row*155}));}
        const totalHeight=Math.max(180,(row+1)*155),spanWidth=Math.min(cols,Math.max(1,others.length))*cell;
        if(!camera)camera={scale:Math.min(1,(width-30)/spanWidth),x:width/2,y:75};
        edgeLayer.replaceChildren();nodeLayer.replaceChildren();
        const keys=new Set(ns.map(n=>n.key));
        for(const e of [...g.structural,...g.links]){
          if(!keys.has(e.to))continue;let from=e.from;
          if(e.kind==='structural'){const seen=new Set();while(!keys.has(from)&&parents.has(from)&&!seen.has(from)){seen.add(from);from=parents.get(from);}}
          if(!keys.has(from))continue;const a=points.get(from),b=points.get(e.to);if(!a||!b)continue;
          const path=svg('path',{d:`M ${a.x} ${a.y+52} L ${b.x} ${b.y-52}`,class:'lg-s-edge '+e.kind});
          const title=svg('title');title.textContent=({structural:'Принадлежность',required:'Обязательное условие',related:'Связано',helpful:'Помогает'}[e.kind]);path.append(title);edgeLayer.append(path);
          if(e.kind!=='structural'){const t=svg('text',{x:(a.x+b.x)/2,y:(a.y+b.y)/2,'text-anchor':'middle',class:'lg-s-edge-label'});t.textContent={required:'Условие ↓',related:'Связано',helpful:'Помогает'}[e.kind];edgeLayer.append(t);}
        }
        for(const n of ns){
          const p=points.get(n.key),node=svg('g',{transform:`translate(${p.x} ${p.y})`,role:'button',tabindex:'0','aria-label':titles[n.kind]+': '+n.name+' · '+status(n,g),class:'lg-s-node'+(n.future?' future':'')+(n.key===selected?' selected':''),'data-strategy-key':n.key,'data-ui-key':'strategy-node:'+n.key});
          node.style.setProperty('--node-tone',tones[n.kind]||'var(--accent)');
          node.append(svg('circle',{r:59}));const icon=svg('text',{y:-29,'text-anchor':'middle',class:'lg-s-glyph'});icon.textContent=marks[n.kind];node.append(icon);
          // Character chunks also wrap long unbroken words; full text remains in the accessible name/details.
          const words=n.name.trim().split(/\s+/).flatMap(word=>word.match(/.{1,14}/gu)||[]),lines=[];let line='';
          for(const word of words){if(line&&line.length+word.length+1>14){lines.push(line);line='';}line+=(line?' ':'')+word;}if(line)lines.push(line);
          if(lines.length>3){lines.length=3;lines[2]=lines[2].slice(0,12)+'…';}
          lines.forEach((line,i)=>{const t=svg('text',{y:-8+i*16,'text-anchor':'middle',class:'lg-s-name'});t.textContent=line;node.append(t);});
          const flag=svg('text',{y:49,'text-anchor':'middle',class:'lg-s-status'});flag.textContent=n.done?'✓':n.future?g.ready(n.key)?'Будущее':'Закрыто':n.kind==='block'?[...g.nodes.values()].filter(v=>v.active&&!v.done&&v.kind==='task'&&v.blockId===n.blockId).length+' дел':n.kind==='root'?'Выбери сферу':' ';node.append(flag);
          node.addEventListener('click',()=>{if(drag?.moved)return;choose(n.key,n.kind==='block'?'branch':scope==='overview'?'branch':scope);});node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(n.key,n.kind==='block'?'branch':scope);}});nodeLayer.append(node);
        }
        transform();
      }
      function transform(){world.setAttribute('transform',`translate(${camera.x} ${camera.y}) scale(${camera.scale})`);}
      function zoom(f,x=width/2,y=height/2){const scale=Math.max(.25,Math.min(2,camera.scale*f)),ratio=scale/camera.scale;camera.x=x-(x-camera.x)*ratio;camera.y=y-(y-camera.y)*ratio;camera.scale=scale;transform();}
      control.append(button('＋',()=>zoom(1.2)),button('−',()=>zoom(1/1.2)),button('К центру',()=>{camera=null;layout();}));
      abort=new AbortController();const opts={signal:abort.signal};
      map.addEventListener('wheel',e=>{e.preventDefault();zoom(e.deltaY<0?1.1:1/1.1);},{...opts,passive:false});
      map.addEventListener('pointerdown',e=>{if(e.button!==0)return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});map.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY,cx:camera.x,cy:camera.y,moved:false,nodeKey:e.target.closest('[data-strategy-key]')?.dataset.strategyKey};if(pointers.size===2){const [a,b]=[...pointers.values()];pinch={distance:Math.hypot(a.x-b.x,a.y-b.y)};drag.moved=true;}},opts);
      map.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2&&pinch){const [a,b]=[...pointers.values()],distance=Math.hypot(a.x-b.x,a.y-b.y);zoom(distance/Math.max(1,pinch.distance));pinch.distance=distance;if(drag)drag.moved=true;}else if(drag){const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>6)drag.moved=true;if(drag.moved){camera.x=drag.cx+dx;camera.y=drag.cy+dy;transform();}}},opts);
      const end=e=>{const tapped=e.type==='pointerup'&&pointers.size===1&&!drag?.moved&&drag?.nodeKey;pointers.delete(e.pointerId);pinch=null;if(tapped){const n=g.nodes.get(tapped);choose(tapped,n?.kind==='block'?'branch':scope==='overview'?'branch':scope);return;}if(!pointers.size)setTimeout(()=>{drag=null;},0);else{const p=[...pointers.values()][0];drag={x:p.x,y:p.y,cx:camera.x,cy:camera.y,moved:true};}};
      map.addEventListener('pointerup',end,opts);map.addEventListener('pointercancel',end,opts);
      observer=new ResizeObserver(()=>layout());observer.observe(box);layout();
    }
    function unmount(){observer?.disconnect();observer=null;abort?.abort();abort=null;}
    function widget(){
      const r=model(),nodes=[...r.graph.nodes.values()],box=make('div','lg-s-widget');
      box.append(make('h3','','Какую жизнь я строю?'),make('p','meta',nodes.filter(n=>n.active&&n.kind==='goal'&&!n.done).length+' активных целей · '+nodes.filter(n=>n.future).length+' набросков будущего'),button('Открыть стратегию',()=>host.navigate(),true));return box;
    }
    return {mount,unmount,widget};
  };
})();
