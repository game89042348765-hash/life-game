#!/usr/bin/env python3
"""Local, observable browser transport for synthetic users; no model or app API calls."""
import argparse
import json
import sys
import time
import traceback
import urllib.request
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright


SNAPSHOT = r"""() => {
  const displayed = el => {
    const r=el.getBoundingClientRect(),s=getComputedStyle(el);
    return r.width>0&&r.height>0&&r.bottom>0&&r.right>0&&r.top<innerHeight&&r.left<innerWidth&&s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0;
  };
  const overlays=[...document.querySelectorAll('.overlay,dialog[open]')].filter(displayed);
  const root=overlays.at(-1)||document.body;
  const exposed = el => {
    if(!displayed(el))return false;
    const r=el.getBoundingClientRect(),x=(Math.max(0,r.left)+Math.min(innerWidth,r.right))/2,y=(Math.max(0,r.top)+Math.min(innerHeight,r.bottom))/2;
    const hit=document.elementFromPoint(x,y);
    return !!hit&&(hit===el||el.contains(hit));
  };
  const controls=[...root.querySelectorAll('button,input:not([type=hidden]),textarea,select,a[href],[role=button],[role=checkbox]')].filter(exposed);
  const items=controls.map((el,i)=>{
    const prev=el.previousElementSibling;
    const associated=[...(el.labels||[])].map(l=>l.innerText.trim()).join(' ');
    const label=(el.getAttribute('aria-label')||associated||(prev?.tagName==='LABEL'?prev.innerText:'')||el.getAttribute('placeholder')||el.innerText||el.getAttribute('title')||el.tagName).trim().slice(0,240);
    const r=el.getBoundingClientRect(),isSelect=el.tagName==='SELECT';
    const d={element:'e'+(i+1),label,type:el.getAttribute('type')||el.tagName.toLowerCase(),disabled:!!el.disabled,rect:{x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)}};
    if('value'in el)d.value=isSelect?(el.selectedOptions[0]?.textContent||''):el.value;
    if('checked'in el)d.checked=el.checked;
    if(isSelect)d.options=[...el.options].filter(o=>!o.hidden).map(o=>({label:o.textContent.trim(),disabled:o.disabled}));
    return d;
  });
  const texts=[],walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){
    const node=walker.currentNode,p=node.parentElement,t=node.textContent.trim();
    if(!t||!p||['SCRIPT','STYLE','OPTION'].includes(p.tagName)||!displayed(p))continue;
    // Report fully exposed words, not the entire contents of a partly covered node.
    // A viewport intersection alone leaks text under fixed navigation or below fold.
    const range=document.createRange(),words=[];
    for(const match of node.textContent.matchAll(/\S+/gu)){
      range.setStart(node,match.index);range.setEnd(node,match.index+match[0].length);
      const rects=[...range.getClientRects()].filter(r=>r.width&&r.height);
      const visible=rects.length&&rects.every(r=>{
        if(r.left<0||r.top<0||r.right>innerWidth||r.bottom>innerHeight)return false;
        return [.15,.5,.85].every(f=>{
          const hit=document.elementFromPoint(r.left+r.width*f,r.top+r.height/2);
          return !!hit&&(hit===p||p.contains(hit));
        });
      });
      if(visible)words.push(match[0]);
    }
    if(words.length)texts.push(words.join(' '));
  }
  window.__syntheticViewControls=controls;
  return {title:document.title,url:location.href,virtual_time_observed:new Date().toISOString(),modal:!!overlays.length,viewport:{width:innerWidth,height:innerHeight},visible_text:texts.join('\n').slice(0,7500),elements:items};
}"""


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class Driver:
    def __init__(self, world_path, run_dir):
        self.world = json.loads(world_path.read_text())
        self.directory = run_dir.resolve()
        if (self.directory / 'run.json').exists():
            raise ValueError('run.json already exists: choose a fresh run-dir; do not overwrite evidence')
        self.directory.mkdir(parents=True, exist_ok=True)
        dump(self.directory / 'world.json', self.world)
        self.url = self.world.get('app_url', 'http://127.0.0.1:8041/personal-lab/')
        self.origin = '/'.join(self.url.split('/')[:3])
        self.zone = ZoneInfo(self.world.get('timezone', 'Europe/Moscow'))
        self.personas = {p['id']: p for p in self.world['personas']}
        self.actors = {k: {'last_day': 0, 'memory': '', 'context': None, 'page': None,
                           'observation': None, 'elements': {}, 'sequence': 0, 'day': None,
                           'steps': 0, 'sessions': [], 'active': False} for k in self.personas}
        self.sequence = 0
        self.finished = False
        self.pw = sync_playwright().start()
        dump(self.directory / 'run.json', {'started_at': utc_now(), 'app_url': self.url,
                                          'mode': 'actual-browser-no-application-hooks'})

    def log(self, kind, actor=None, **data):
        self.sequence += 1
        a = self.actors.get(actor, {})
        record = {'sequence': self.sequence, 'real_time_utc': utc_now(), 'kind': kind,
                  'actor': actor, 'day': a.get('day'), 'virtual_time': a.get('virtual_time'), **data}
        with (self.directory / 'events.jsonl').open('a') as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')

    def plan(self, actor, day):
        if actor not in self.actors:
            raise ValueError('unknown actor')
        planned = self.world['sessions'].get(actor, {}).get(str(day))
        if planned is None:
            raise ValueError('day absent from predeclared world')
        a = self.actors[actor]
        return a, planned

    def brief(self, actor, day):
        a, p = self.plan(actor, day)
        when = date.fromisoformat(self.world['start_date']) + timedelta(days=int(day) - 1)
        return {'actor': actor, 'day': int(day), 'date': when.isoformat(),
                'context': p.get('context', ''), 'available': p.get('available', True),
                'budget': p.get('budget', 18), 'memory': a['memory'],
                'past_days': [{'day': s['day'], 'status': s['status'], 'outcome': s.get('outcome')}
                              for s in a['sessions']]}

    def check_day(self, actor, day):
        a, p = self.plan(actor, day)
        if self.finished:
            raise ValueError('run has finished')
        if a['active']:
            raise ValueError('end current session before a new day')
        if int(day) != a['last_day'] + 1:
            raise ValueError(f"next day must be {a['last_day'] + 1}; repeated or out-of-order day rejected")
        return a, p

    def skip(self, actor, day, outcome='', memory=None):
        a, p = self.check_day(actor, day)
        a['day'] = int(day)
        a['last_day'] = int(day)
        day_date = date.fromisoformat(self.world['start_date']) + timedelta(days=int(day) - 1)
        a['virtual_time'] = (datetime.combine(day_date, datetime.min.time(), self.zone)
                             + timedelta(hours=float(p.get('hour', 9)))).isoformat()
        if memory is not None:
            a['memory'] = memory
        record = {'day': int(day), 'status': 'no_use', 'reason': 'unavailable' if not p.get('available', True) else 'actor_choice',
                  'outcome': outcome, 'actions': 0, 'context': p.get('context', '')}
        a['sessions'].append(record)
        self.log('no_use', actor, **{k: v for k, v in record.items() if k != 'day'})
        self.save_summary()
        return {'actor': actor, 'day': int(day), 'no_use': True, 'memory': a['memory'], 'reason': record['reason']}

    def ensure_context(self, actor):
        a = self.actors[actor]
        if a['context'] is None:
            viewport = self.personas[actor].get('viewport', {'width': 390, 'height': 844})
            context = self.pw.chromium.launch_persistent_context(
                str(self.directory / 'profiles' / actor), executable_path='/usr/bin/chromium',
                headless=True, args=['--no-sandbox'], viewport=viewport, locale='ru-RU',
                timezone_id=self.world.get('timezone', 'Europe/Moscow'),
                accept_downloads=True)
            context.route('**/*', lambda route: route.continue_()
                          if route.request.url.startswith(self.origin + '/') else route.abort())
            context.tracing.start(screenshots=True, snapshots=True, sources=False)
            for page in context.pages:
                page.close()
            a['context'] = context
        return a['context']

    def session(self, actor, day):
        a, p = self.check_day(actor, day)
        if not p.get('available', True):
            return self.skip(actor, day, outcome='Unavailable in predeclared world')
        context = self.ensure_context(actor)
        context.set_offline(p.get('network', 'online') == 'offline')
        a['day'], a['steps'], a['active'] = int(day), 0, True
        day_date = date.fromisoformat(self.world['start_date']) + timedelta(days=int(day) - 1)
        hour = float(p.get('hour', 9))
        moment = datetime.combine(day_date, datetime.min.time(), self.zone) + timedelta(hours=hour)
        a['virtual_time'] = moment.isoformat()
        a['budget'] = int(p.get('budget', 18))
        context.tracing.start_chunk(title=f'{actor} day {day}')
        page = context.new_page()
        a['page'] = page
        page.set_default_timeout(4000)
        page.on('pageerror', lambda error: self.log('pageerror', actor, error=str(error)))
        page.on('console', lambda message: self.log('console', actor, level=message.type, text=message.text)
                if message.type in ('error', 'warning') else None)
        page.on('dialog', lambda dialog: (self.log('native_dialog_dismissed_by_transport', actor,
                                                  message=dialog.message), dialog.dismiss()))
        page.on('download', lambda download: self.capture_download(actor, download))
        page.clock.install(time=moment)
        page.goto(self.url, wait_until='networkidle')
        self.log('session_opened', actor, context=p.get('context', ''), budget=a['budget'])
        return {**self.brief(actor, day), 'observation': self.observe(actor)}

    def capture_download(self, actor, download):
        path = self.directory / actor / f'day-{self.actors[actor]["day"]:02d}' / 'downloads' / Path(download.suggested_filename).name
        path.parent.mkdir(parents=True, exist_ok=True)
        download.save_as(str(path))
        self.log('download', actor, path=str(path))

    def observe(self, actor):
        a = self.actors[actor]
        if not a['active'] or a['page'] is None:
            raise ValueError('no active page; open session first')
        page = a['page']
        page.wait_for_timeout(90)
        data = page.evaluate(SNAPSHOT)
        a['virtual_time'] = data['virtual_time_observed']
        # Element handles are held by the transport, never application state/functions.
        handles = page.evaluate_handle('window.__syntheticViewControls')
        a['elements'] = {item['element']: handles.get_property(str(i)).as_element()
                         for i, item in enumerate(data['elements'])}
        handles.dispose()
        a['sequence'] += 1
        identifier = f'{actor}-d{a["day"]:02d}-o{a["sequence"]:04d}'
        folder = self.directory / actor / f'day-{a["day"]:02d}'
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f'{identifier}.png'
        page.screenshot(path=str(path), animations='disabled')
        data.update({'observation_id': identifier, 'screenshot': str(path),
                     'actions_used': a['steps'], 'action_budget': a['budget']})
        a['observation'] = data
        dump(folder / f'{identifier}.json', data)
        self.log('observation', actor, observation_id=identifier, screenshot=str(path), snapshot=str(path.with_suffix('.json')))
        return data

    def action(self, command):
        actor = command['actor']
        a = self.actors[actor]
        if not a['active']:
            raise ValueError('no active session')
        if a['steps'] >= a['budget']:
            return {'error': 'action_budget_exhausted', 'actions_used': a['steps'],
                    'allowed': ['observe', 'end']}
        if command.get('observation_id') != a['observation']['observation_id']:
            raise ValueError('stale observation_id; observe again before acting')
        before = a['observation']['screenshot']
        start = time.monotonic()
        a['steps'] += 1
        error = None
        try:
            if command['op'] == 'scroll':
                page = a['page']
                page.mouse.move(page.viewport_size['width'] / 2, page.viewport_size['height'] / 2)
                page.mouse.wheel(0, max(-1000, min(1000, int(command.get('dy', 500)))))
            else:
                element = a['elements'].get(command.get('element'))
                if element is None:
                    raise ValueError('unknown visible element')
                action = command.get('action')
                if action == 'click':
                    element.click()
                elif action == 'fill':
                    element.fill(str(command.get('value', '')))
                elif action == 'select':
                    element.select_option(label=str(command['value']))
                elif action == 'check':
                    element.set_checked(bool(command.get('value', True)))
                else:
                    raise ValueError('unsupported action')
        except Exception as exc:
            error = str(exc)
        duration = round((time.monotonic() - start) * 1000, 1)
        observation = self.observe(actor)
        self.log('action', actor, command=command, success=error is None, error=error,
                 duration_ms=duration, before=before, after=observation['screenshot'],
                 observation_id=observation['observation_id'])
        return {'success': error is None, 'error': error, 'duration_ms': duration,
                'observation': observation}

    def snapshot_state(self, actor):
        a = self.actors[actor]
        raw = a['page'].evaluate('''() => Object.fromEntries(Object.keys(localStorage).sort().map(key => [key,localStorage.getItem(key)]))''')
        parsed = {}
        for key, value in raw.items():
            try:
                parsed[key] = json.loads(value)
            except (TypeError, ValueError):
                parsed[key] = value
        path = self.directory / actor / f'day-{a["day"]:02d}' / 'observer-state.json'
        dump(path, parsed)
        primary = parsed.get('lifegame-personal-lab-my-v1')
        summary = {'keys': list(parsed), 'path': str(path), 'primary_valid_json': isinstance(primary, dict)}
        if isinstance(primary, dict):
            ledger = primary.get('ledger', [])
            summary.update({'lastProcessed': primary.get('lastProcessed'), 'revision': primary.get('revision'),
                            'counts': {k: len(primary.get(k, [])) for k in ('tasks','habits','quests','cal','goals','facts','ledger','misses')},
                            'coins': sum(item.get('coins', 0) for item in ledger),
                            'xp': sum(item.get('xp', 0) for item in ledger)})
        a['latest_state'] = summary
        return summary

    def end(self, actor, outcome='', memory='', frictions=None):
        a = self.actors[actor]
        if not a['active']:
            raise ValueError('no active session')
        state = self.snapshot_state(actor)
        folder = self.directory / actor / f'day-{a["day"]:02d}'
        trace_path = folder / 'trace.zip'
        a['context'].tracing.stop_chunk(path=str(trace_path))
        record = {'day': a['day'], 'status': 'completed', 'outcome': outcome,
                  'actions': a['steps'], 'frictions': frictions or [], 'state': state, 'trace': str(trace_path)}
        a['sessions'].append(record)
        a['memory'], a['last_day'], a['active'] = memory, a['day'], False
        a['page'].close()
        a['page'], a['elements'], a['observation'] = None, {}, None
        self.log('session_ended', actor, **{k: v for k, v in record.items() if k != 'day'}, memory=memory)
        self.save_summary()
        # Internal snapshots intentionally absent from the actor response.
        return {'actor': actor, 'day': a['day'], 'status': 'completed', 'actions': a['steps'],
                'memory': memory, 'outcome': outcome}

    def save_summary(self):
        summary = {'app_url': self.url, 'finished': self.finished, 'updated_at': utc_now(), 'actors': {}}
        for actor, a in self.actors.items():
            plans = self.world['sessions'].get(actor, {})
            sessions = a['sessions']
            summary['actors'][actor] = {
                'planned': len(plans), 'opened': sum(s['status'] == 'completed' for s in sessions) + int(a['active']),
                'completed': sum(s['status'] == 'completed' for s in sessions),
                'no_use': sum(s['status'] == 'no_use' for s in sessions),
                'actions': sum(s.get('actions', 0) for s in sessions) + (a['steps'] if a['active'] else 0),
                'last_day': a['last_day'], 'active': a['active'], 'sessions': sessions,
                'latest_state': a.get('latest_state'), 'profile': str(self.directory / 'profiles' / actor)}
        dump(self.directory / 'summary.json', summary)
        return summary

    def finish(self):
        if any(a['active'] for a in self.actors.values()):
            raise ValueError('end each active session before finish')
        if not self.finished:
            for a in self.actors.values():
                if a['context']:
                    a['context'].tracing.stop()
                    a['context'].close()
            self.pw.stop()
            self.finished = True
            self.log('run_finished')
        return self.save_summary()

    def dispatch(self, command):
        op = command.get('op')
        if op == 'brief':
            return self.brief(command['actor'], int(command['day']))
        if op == 'session':
            return self.session(command['actor'], int(command['day']))
        if op == 'skip':
            return self.skip(command['actor'], int(command['day']), command.get('outcome', ''), command.get('memory'))
        if op == 'observe':
            return self.observe(command['actor'])
        if op in ('act', 'scroll'):
            return self.action(command)
        if op == 'end':
            return self.end(command['actor'], command.get('outcome', ''), command.get('memory', ''), command.get('frictions'))
        if op == 'audit':
            return self.save_summary()
        if op == 'finish':
            return self.finish()
        raise ValueError('unsupported op')


def serve(args):
    driver = Driver(args.world, args.run_dir)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused):
            pass

        def do_POST(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size < 131072:
                    raise ValueError('invalid request size')
                command = json.loads(self.rfile.read(size))
                result = driver.dispatch(command)
                code = 200
            except Exception as error:
                result = {'transport_error': str(error)}
                driver.log('transport_error', error=str(error), traceback=traceback.format_exc())
                code = 400
            payload = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print(json.dumps({'status': 'listening', 'port': args.port, 'run_dir': str(driver.directory)}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        if not driver.finished:
            for actor, a in driver.actors.items():
                if a['active']:
                    driver.end(actor, 'transport shutdown', a['memory'], ['session interrupted by shutdown'])
            driver.finish()


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='mode', required=True)
    server = sub.add_parser('serve')
    server.add_argument('--world', type=Path, required=True)
    server.add_argument('--run-dir', type=Path, required=True)
    server.add_argument('--port', type=int, default=8052)
    client = sub.add_parser('request')
    client.add_argument('--port', type=int, default=8052)
    client.add_argument('json')
    args = parser.parse_args()
    if args.mode == 'serve':
        serve(args)
    else:
        payload = json.dumps(json.loads(args.json), ensure_ascii=False).encode()
        request = urllib.request.Request(f'http://127.0.0.1:{args.port}/', data=payload,
                                         headers={'Content-Type': 'application/json'})
        # Explicitly bypass inherited proxies for the local-only driver.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=45) as response:
                print(response.read().decode())
        except urllib.error.HTTPError as error:
            print(error.read().decode())
            raise SystemExit(1)


if __name__ == '__main__':
    main()
