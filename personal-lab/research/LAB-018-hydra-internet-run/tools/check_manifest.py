"""Check submitted manifest bytes and SHA without executing returned helper code."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory');args=p.parse_args()
root=Path(args.directory).resolve();m=json.loads((root/'RESULT_MANIFEST.json').read_text());errors=[]
for f in m['files']:
 name=f['path'];path=(root/name).resolve()
 if not path.is_relative_to(root) or not path.is_file(): errors.append(f'unsafe/missing {name}');continue
 data=path.read_bytes()
 if len(data)!=f['bytes']:errors.append(f'bytes {name}')
 if hashlib.sha256(data).hexdigest()!=f['sha256']:errors.append(f'sha256 {name}')
print(json.dumps({'task_id':m['task_id'],'files_checked':len(m['files']),'errors':errors},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
