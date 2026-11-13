"""Deterministic stratified source re-GET. This does not certify semantic truth."""
from pathlib import Path
import argparse,json,subprocess,datetime,hashlib,concurrent.futures,tempfile
from lxml import html
p=argparse.ArgumentParser();p.add_argument('package');p.add_argument('--out',required=True);a=p.parse_args()
root=Path(a.package);out=Path(a.out)
if out.exists(): raise SystemExit('Refusing to overwrite prior intake evidence')
sources=[json.loads(l) for l in (root/'sources.jsonl').read_text().splitlines() if l.strip()]
findings=[json.loads(l) for l in (root/'findings.jsonl').read_text().splitlines() if l.strip()]
pool=[s for s in sources if s['accessed']];selected=[];types=set();origins=set()
while pool and len(selected)<min(max(5,(len(sources)+9)//10),len(sources)):
 pool.sort(key=lambda s:(-(s['source_type'] not in types),-(s['origin_group'] not in origins),s['id']))
 s=pool.pop(0);selected.append(s);types.add(s['source_type']);origins.add(s['origin_group'])
def probe(s):
 with tempfile.TemporaryDirectory(prefix='hydra-intake-') as td:
  d=Path(td);c=subprocess.run(['curl','-sS','-L','--max-time','40','--max-redirs','7','-o',str(d/'body'),'-w','%{json}',s['url']],capture_output=True,text=True)
  try:meta=json.loads(c.stdout)
  except ValueError:meta={}
  data=(d/'body').read_bytes() if (d/'body').exists() else b''
  text=''
  if data.startswith(b'%PDF'):
   v=subprocess.run(['pdftotext',str(d/'body'),'-'],text=True,capture_output=True);text=v.stdout
  else:
   try:
    tree=html.fromstring(data)
    for n in tree.xpath('//script|//style|//noscript'): n.drop_tree()
    text=' '.join(tree.text_content().split())
   except Exception:text=data.decode(errors='replace')
  temp_path=Path('/tmp')/f'hydra-intake-{s["id"]}.txt';temp_path.write_text(text)
  claims=[{'finding_id':f['id'],**cl} for f in findings for cl in f['claims'] if cl['source_id']==s['id']]
  return {'source_id':s['id'],'source_type':s['source_type'],'origin_group':s['origin_group'],'original_url':s['url'],'final_url':meta.get('url_effective'),'http_status':meta.get('http_code'),'connect_status':meta.get('http_connect'),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'curl_exit':c.returncode,'error':c.stderr or None,'body_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'extracted_characters':len(text),'short_preview':text[:350],'claims_to_review':claims,'local_text_path':str(temp_path),'semantic_review':'pending_root_review'}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex: results=list(ex.map(probe,selected))
report={'package':str(root),'sample_rule':'greedy new source type then new origin group then lexical source ID; min(max(5,ceil(source count/10)),source count); accessed sources only','required_minimum':min(max(5,(len(sources)+9)//10),len(sources)),'total_sources':len(sources),'probed':len(results),'results':results}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for x in results: print(json.dumps({k:v for k,v in x.items() if k!='short_preview'},ensure_ascii=False))
