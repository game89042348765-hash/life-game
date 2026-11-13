"""Read-only public GET probes; no authentication, policy changes or paid APIs."""
from pathlib import Path
import concurrent.futures, subprocess, json, datetime, hashlib, tempfile, sys
from lxml import html
BASE=Path(__file__).resolve().parents[1]
URLS=[
('homepage','https://todoist.com/'),('homepage','https://www.notion.so/'),
('homepage','https://www.wikipedia.org/'),('homepage','https://github.com/'),
('content','https://www.todoist.com/help/articles/introduction-to-quick-add-in-todoist-O53oLZwM'),
('content','https://www.notion.com/help/export-your-content'),
('content','https://en.wikipedia.org/wiki/Implementation_intention'),
('content','https://docs.github.com/en/repositories/working-with-files/using-files/viewing-a-file'),
('search','https://www.google.com/search?q=planning+implementation+intentions+review'),
('search','https://www.bing.com/search?q=planning+implementation+intentions+review'),
('search','https://html.duckduckgo.com/html/?q=planning+implementation+intentions+review')]
def probe(item):
 kind,url=item;at=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with tempfile.TemporaryDirectory(prefix='hydra-probe-') as td:
  p=Path(td);args=['curl','-sS','-L','--max-time','35','--max-redirs','7','-D',str(p/'headers'),'-o',str(p/'body'),'-w','%{json}',url]
  c=subprocess.run(args,text=True,capture_output=True)
  try: meta=json.loads(c.stdout)
  except ValueError: meta={}
  data=(p/'body').read_bytes() if (p/'body').exists() else b''
  headers=(p/'headers').read_text(errors='replace') if (p/'headers').exists() else ''
  try:
   tree=html.fromstring(data)
   for n in tree.xpath('//script|//style|//noscript'): n.drop_tree()
   content=' '.join(tree.text_content().split());title=tree.xpath('string(//title)')
  except Exception: content=data.decode(errors='replace');title=None
  (Path('/tmp')/('hydra-access-'+hashlib.sha256(url.encode()).hexdigest()[:12]+'.txt')).write_text(content)
  return {'kind':kind,'original_url':url,'final_url':meta.get('url_effective'),'retrieved_at':at,'http_status':meta.get('http_code'),'http_connect':meta.get('http_connect'),'redirect_count':meta.get('num_redirects'),'redirect_statuses':[s.splitlines()[0] for s in headers.split('\r\n\r\n') if s.startswith('HTTP/')], 'curl_exit':c.returncode,'error':c.stderr.strip() or None,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'title':title,'extracted_characters':len(content),'text_preview':content[:600],'useful_text_review':'pending_manual_review'}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex: results=list(ex.map(probe,URLS))
 report={'run_id':'HYDRA-INTERNET-001','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'curl GET, redirects followed, inherited proxy and TLS verification retained; lxml text extraction','specialized_search_tool':False,'file_io':{'write_read_round_trip':True,'path':'ACCESS-AUDIT.json'},'python':sys.version,'separate_contexts':{'tool':'collaboration.spawn_agent','observed_search_agents':['/root/cal_search_01','/root/cal_search_02','/root/cal_search_03','/root/cal_search_04'],'fork_turns':'none'},'requests':results}
 (BASE/'ACCESS-AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 for x in results: print(json.dumps(x,ensure_ascii=False))
