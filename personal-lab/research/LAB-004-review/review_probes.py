from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import ast, json, os, hashlib, tempfile, fcntl, sys, time, traceback

import argparse
parser = argparse.ArgumentParser(description='Reproduce two defects in the exact returned candidate; not acceptance tests for a repaired driver')
parser.add_argument('--root', type=Path, default=Path.cwd())
parser.add_argument('--candidate', type=Path)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--skip-browser', action='store_true')
parser.add_argument('--app-url', default='http://127.0.0.1:8141/personal-lab/')
args = parser.parse_args()
ROOT = args.root.resolve()
SOURCE = args.candidate or Path(__file__).resolve().parent / 'incoming/driver.py.txt'
OUT = args.output.resolve()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == '557f780b6f90d65dd8504a836cd20d37ccce3d3f6247fe6f5ff434be7ac45ab1', 'Baseline-only reproduction: candidate hash changed'
OUT.mkdir(parents=True, exist_ok=False)
tree = ast.parse(SOURCE.read_text())
functions = {'utc_now', 'dump', 'canonical_sha256', 'file_sha256',
             '_check_chromium_singleton_lock', '_probe_lock_free', 'compute_app_manifest'}
classes = {'_ExclusiveFileLock', 'Driver'}
constants = {'SNAPSHOT', 'CORE_APP_FILES'}
nodes = []
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in functions:
        nodes.append(n)
    elif isinstance(n, ast.ClassDef) and n.name in classes:
        nodes.append(n)
    elif isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in n.targets):
        nodes.append(n)

class NativeOnly(ast.NodeTransformer):
    def visit_If(self, node):
        if '_needs_loopback_alias' in ast.unparse(node.test):
            return None
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if any(isinstance(t, ast.Name) and t.id == 'allowed_origins' for t in node.targets):
            node.value = ast.parse("(self.origin + '/',)", mode='eval').body
        if any(isinstance(t, ast.Name) and t.id == 'backend_name' for t in node.targets):
            node.value = ast.Constant('playwright-native-review')
        return self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == '_rewrite_loopback_url':
            return self.visit(node.args[0])
        return self.generic_visit(node)

module = ast.fix_missing_locations(NativeOnly().visit(ast.Module(body=nodes, type_ignores=[])))
prefix = '''import argparse, fcntl, hashlib, json, os, signal, sys, time, traceback, urllib.error, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
def sync_playwright():
    from playwright.sync_api import sync_playwright as native
    return native()
HAS_PLAYWRIGHT=True
'''
derived = prefix + ast.unparse(module) + '\n'
assert all(word not in derived for word in ['_CDP', 'selenium', 'lifegame.local', '_needs_loopback_alias', '_rewrite_loopback_url'])
path = OUT / 'native_specimen.py'
path.write_text(derived)
ns = {'__file__': str(path), '__name__': 'review_native_specimen'}
exec(compile(derived, str(path), 'exec'), ns)
Driver, Lock = ns['Driver'], ns['_ExclusiveFileLock']
findings = []

# Deterministic interleaving of three actual lock-file open/acquire operations.
lockpath = OUT / 'lock-probe' / 'owner.lock'
first = Lock(lockpath, {'owner': 'A'}).acquire('review lock')
waiting_fd = lockpath.open('a+')
old_inode = os.fstat(waiting_fd.fileno()).st_ino
first.release()
fcntl.flock(waiting_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
third = Lock(lockpath, {'owner': 'C'}).acquire('review lock')
new_inode = os.fstat(third.handle.fileno()).st_ino
assert old_inode != new_inode
findings.append({'id': 'R1', 'reproduced': True, 'issue': 'B and C simultaneously hold exclusive locks for the same pathname on different inodes', 'old_inode': old_inode, 'new_inode': new_inode})
third.release(); fcntl.flock(waiting_fd.fileno(), fcntl.LOCK_UN); waiting_fd.close()

# SIGKILL-equivalent loss of process memory at the precise post-event/pre-checkpoint boundary.
folder = OUT / 'skip-crash'; folder.mkdir()
world = {'start_date': '2026-11-16', 'sessions': {'P01': {'1': {'available': False, 'context': 'no time', 'hour': 9}}}}
pid = os.fork()
if pid == 0:
    obj = Driver.__new__(Driver)
    obj.actors = {'P01': obj._default_actor_state()}
    obj.world, obj.zone, obj.directory = world, ZoneInfo('Europe/Moscow'), folder
    obj.read_only, obj.finished, obj.sequence, obj._resume_event_path = False, False, 0, None
    obj.save_checkpoint = lambda: os._exit(86)
    obj.skip('P01', 1, outcome='unavailable', memory='REMEMBER_THIS_AFTER_RESTART')
    os._exit(87)
_, status = os.waitpid(pid, 0)
assert os.waitstatus_to_exitcode(status) == 86
events = [json.loads(line) for line in (folder / 'events.jsonl').read_text().splitlines()]
obj = Driver.__new__(Driver)
obj.actors = {'P01': obj._default_actor_state()}; obj.world, obj.directory = world, folder
obj._reconcile_from_events(events)
actor = obj.actors['P01']
assert events[-1]['kind'] == 'no_use' and actor['last_day'] == 1
assert actor['sessions'] == [] and actor['memory'] == ''
findings.append({'id': 'R2', 'reproduced': True, 'issue': 'Durable no_use advances last_day but its session record and memory disappear if daemon dies before checkpoint', 'child_exit': 86, 'last_day': actor['last_day'], 'sessions': actor['sessions'], 'memory': actor['memory'], 'durable_event': events[-1]})

report = {'original_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'scope': 'Only selected checkpoint/lock code executed. Unsupported CDP/alias layer excluded. These are technical failure probes, not an AI-user run.',
          'findings': findings}
(OUT / 'probe-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False, indent=2))

if args.skip_browser:
    raise SystemExit(0)

# One bounded native browser readiness path; no source hooks or direct state writes.
world = json.loads((ROOT / 'personal-lab/research/LAB-002-digital-month/world.pilot.json').read_text())
world['app_url'] = args.app_url
worldpath = OUT / 'native-world.json'; worldpath.write_text(json.dumps(world))
run = OUT / 'native-smoke'
driver = Driver(worldpath, run, app_dir=ROOT / 'personal-lab')
try:
    obs = driver.session('P01', 1)['observation']
    def click_substring(text):
        global obs
        el = next(e for e in obs['elements'] if text in e['label'])
        result = driver.action({'op': 'act', 'actor': 'P01', 'observation_id': obs['observation_id'], 'element': el['element'], 'action': 'click', 'intent': 'technical smoke: '+text})
        assert result['success'], result
        obs = result['observation']
    click_substring('Начать свою жизнь')
    click_substring('Начать')
    driver.end('P01', outcome='technical smoke', memory='NATIVE_MEMORY')
finally:
    driver.suspend_on_shutdown()
driver = Driver(worldpath, run, resume=True, app_dir=ROOT / 'personal-lab')
try:
    assert driver.brief('P01', 2)['memory'] == 'NATIVE_MEMORY'
    assert driver.brief('P01', 2)['last_day'] == 1
    driver.session('P01', 2)
    driver.end('P01', outcome='native resume smoke', memory='NATIVE_MEMORY_DAY_2')
finally:
    driver.suspend_on_shutdown()
report['native_smoke'] = {'passed': True, 'days': [1, 2], 'ui_actions': 2, 'retained_memory': True, 'backend': 'native Playwright; filtered specimen, not integrated patch'}
(OUT / 'probe-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print('PASS native browser smoke. The two reproduced recovery defects remain blockers.')
