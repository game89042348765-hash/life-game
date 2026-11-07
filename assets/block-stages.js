/* Canonical block stages. Real goals/tasks retain their IDs and economic history. */
'use strict';
(()=>{
  const object=x=>x&&typeof x==='object'&&!Array.isArray(x),id=x=>typeof x==='string'&&x.length>0;
  const fail=text=>{throw new Error(text||'Повреждены этапы блоков.');};
  const list=(data,blockId)=>data.blockStages.items.filter(s=>s.blockId===blockId);
  const get=(data,id)=>data.blockStages.items.find(s=>s.id===id)||null;
  const current=(data,blockId)=>get(data,data.blockStages.current[blockId]);
  const active=(data,item)=>item.block==='lifegame:inbox'?item.stageId===null:!!item.stageId&&data.blockStages.current[item.block??item.blockId]===item.stageId;
  const unlocked=(data,stage)=>stage.lock.mode==='open'||stage.lock.mode==='stage'&&get(data,stage.lock.stageId)?.reached===true;
  const lockText=(data,stage)=>stage.lock.mode==='manual'?'Этап закрыт вручную':stage.lock.mode==='stage'?'Дойти до этапа «'+(get(data,stage.lock.stageId)?.name||'Недоступный этап')+'»':'';
  function validate(data){
    if(data.blockStages===undefined)data.blockStages={version:1,items:[],current:{}};
    const model=data.blockStages;if(!object(model)||model.version!==1||!Array.isArray(model.items)||!object(model.current))fail();
    const blocks=new Map(data.blocks.map(b=>[b.id,b])),ids=new Set(),byBlock=new Map();
    for(const s of model.items){
      if(!object(s)||!id(s.id)||ids.has(s.id)||!blocks.has(s.blockId)||typeof s.name!=='string'||!s.name.trim()||s.name.length>120||typeof s.meaning!=='string'||s.meaning.length>2000||typeof s.reached!=='boolean'||!object(s.lock)||!['open','manual','stage'].includes(s.lock.mode)||(s.lock.mode==='stage'?!id(s.lock.stageId):s.lock.stageId!==null))fail();
      ids.add(s.id);s.name=s.name.trim();s.meaning=s.meaning.trim();if(!byBlock.has(s.blockId))byBlock.set(s.blockId,[]);byBlock.get(s.blockId).push(s);
    }
    for(const b of data.blocks){
      if(!byBlock.has(b.id)){
        // Deterministic migration, including a newly created block. Never generates fresh IDs on reload.
        let stageId='initial-stage:'+b.id;while(ids.has(stageId))stageId='initial:'+stageId;
        const s={id:stageId,blockId:b.id,name:'Текущий этап',meaning:b.meaning||'',reached:true,lock:{mode:'open',stageId:null}};model.items.push(s);ids.add(s.id);byBlock.set(b.id,[s]);Object.defineProperty(model.current,b.id,{value:s.id,writable:true,enumerable:true,configurable:true});
      }
      if(!Object.hasOwn(model.current,b.id)||!id(model.current[b.id]))fail('У блока не выбран текущий этап.');
      const s=get(data,model.current[b.id]);if(!s||s.blockId!==b.id||!s.reached)fail('Неверный текущий этап блока.');
      b.meaning=s.meaning; // Compatibility mirror; stage meaning is authoritative.
    }
    for(const key of Object.keys(model.current))if(!blocks.has(key))fail('У текущего этапа нет блока.');
    const indegree=new Map(model.items.map(s=>[s.id,0])),edges=new Map();
    for(const s of model.items){
      if(s.lock.mode==='stage'){
        const required=get(data,s.lock.stageId);if(!required||required.id===s.id)fail('Выбери другой существующий этап.');
        if(!edges.has(required.id))edges.set(required.id,[]);edges.get(required.id).push(s.id);indegree.set(s.id,indegree.get(s.id)+1);
      }
      if(model.current[s.blockId]===s.id&&!unlocked(data,s))fail('Текущий этап нельзя закрыть. Сначала перейди к другому этапу.');
    }
    const queue=[...indegree].filter(([,degree])=>!degree).map(([key])=>key);for(let i=0;i<queue.length;i++)for(const to of edges.get(queue[i])||[]){indegree.set(to,indegree.get(to)-1);if(!indegree.get(to))queue.push(to);}if(queue.length!==model.items.length)fail('Условия этапов образуют замкнутый круг.');
    for(const goal of data.goals){
      if(goal.stageId===undefined)goal.stageId=model.current[goal.blockId];const s=get(data,goal.stageId);if(!s||s.blockId!==goal.blockId)fail('Цель связана с неверным этапом.');
    }
    const goals=new Map(data.goals.map(g=>[g.id,g]));
    for(const task of data.tasks){
      if(task.stageId===undefined)task.stageId=task.block==='lifegame:inbox'?null:goals.get(task.goalId)?.stageId||model.current[task.block];
      const s=task.stageId===null?null:get(data,task.stageId);
      if(task.block==='lifegame:inbox'?task.stageId!==null:!s||s.blockId!==task.block)fail('Задание связано с неверным этапом.');
      if(task.goalId&&goals.get(task.goalId)?.stageId!==task.stageId)fail('Задание и его цель должны относиться к одному этапу.');
    }
    return model;
  }
  function switchTo(data,stageId){const s=get(data,stageId),block=s&&data.blocks.find(b=>b.id===s.blockId);if(!s||!block||block.archivedAt!==null)fail('Этап недоступен.');if(!unlocked(data,s))fail(lockText(data,s));data.blockStages.current[s.blockId]=s.id;s.reached=true;block.meaning=s.meaning;}
  globalThis.LifeGameStages={validate,list,get,current,active,unlocked,lockText,switchTo};
})();
