"""Create identical sterile assessment inputs; never replace an existing packet."""
from pathlib import Path
import argparse,subprocess,json,hashlib,shutil,datetime
p=argparse.ArgumentParser();p.add_argument('snapshot');p.add_argument('--out',required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[1];repo=r.parents[2];bundle=repo/'personal-lab/research/LAB-011-hybrid-v211-review/release';source=Path(a.snapshot).resolve();out=Path(a.out).resolve()
if out.exists():raise SystemExit('Refusing existing assessment input directory')
# Native prepare-blind publishes a new FILE, not a directory.
subprocess.run(['python3','-B',str(bundle/'tools/atlas.py'),'prepare-blind',str(source),'--out',str(out/'blind-native.jsonl')],check=True)
def read(path):return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
def write(path,rows):path.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
elements=read(source/'elements.jsonl');prepared=read(out/'blind-native.jsonl');seen={x['id'] for x in prepared}
keys=['id','name','kind','primary_category','category_ids','jobs','description','mechanism','mechanism_triad','vendor_claim','evidence_effect','evidence_grade','evidence_summary','contexts','conditions','costs','risks','source_ids']
# Same whitelist for supplementary reference/composite review. These do not
# gain rank eligibility: original kind/selection track remain in full dataset.
supplement=[{k:e.get(k) for k in keys} for e in elements if e['id'] not in seen]
write(out/'blind-supplement.jsonl',supplement);all_rows=sorted(prepared+supplement,key=lambda x:x['id'])
assert len(all_rows)==len(elements) and len({e['id'] for e in all_rows})==len(elements)
index=[]
for i in range(0,len(all_rows),26):
 name=f'blind-part-{i//26+1:03}.jsonl';part=all_rows[i:i+26];write(out/name,part)
 index.extend({'id':e['id'],'name':e['name'],'part':name} for e in part)
write(out/'INDEX.jsonl',index);shutil.copy2(source/'sources.jsonl',out/'sources.jsonl')
facts=[{'raw_id':f['id'],'name':f['name'],'source_ids':f['source_ids'],'verification':f['verification'],'claims':f['claims']} for f in read(source/'findings.jsonl')]
write(out/'evidence-claims.jsonl',facts)
for src,name in [(r/'tasks/RATING-INSTRUCTIONS.md','RATING-INSTRUCTIONS.md'),(bundle/'SCORING.md','SCORING.md'),(bundle/'DATA_CONTRACT.md','DATA_CONTRACT.md'),(bundle/'PROMPTS/02-ANALYZE.md','PROMPT-RATE.md')]:shutil.copy2(src,out/name)
manifest={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_snapshot':str(source.relative_to(r)),'source_hashes':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in source.glob('*.jsonl')},'native_count':len(prepared),'supplement_count':len(supplement),'total_units_for_descriptive_rating':len(all_rows),'part_size_limit':26,'policy':'Identical inputs for two fresh contexts; no foreign scores, selection, rank or application inventory. Supplement permits complete descriptive review without changing rank eligibility. Original full dataset controls eligibility.','native_payload_unchanged':True,'removed_fields':['selection_track','review_status','risk_status','family_id','raw_ids','analyst_id','analysis_context_id','alternatives','questions','ratings'],'rubric_version':'2.1','token_context_limit':None,'bytes_not_tokens':True,'files_before_seal':{x.name:{'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in out.iterdir() if x.is_file()}}
(out/'BLIND-INPUTS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['python3','-B',str(bundle/'tools/atlas.py'),'seal',str(out),'--manifest','FILES.json'],check=True)
subprocess.run(['python3','-B',str(bundle/'tools/atlas.py'),'verify',str(out),'--manifest','FILES.json'],check=True)
print(json.dumps({'native':len(prepared),'supplement':len(supplement),'total':len(all_rows),'out':str(out)}))
