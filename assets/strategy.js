/* Previous Strategy data contract, preserved for existing JSON copies. The UI now uses block stages. */
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
