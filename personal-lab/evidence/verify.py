#!/usr/bin/env python3
"""Verify portable fictional evidence with stdlib only; no app/model/network calls."""
import hashlib
import json
from pathlib import Path
import zipfile

folder = Path(__file__).resolve().parent / 'month-pilot-001'
manifest = json.loads((folder / 'MANIFEST.json').read_text())
included = [row for row in manifest['artifacts'] if row['included']]
for row in included:
    path = (folder / row['path']).resolve()
    assert path.is_relative_to(folder.resolve()), row['path']
    assert path.is_file(), row['path']
    assert path.stat().st_size == row['bytes'], row['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['path']
    if path.name == 'trace.zip':
        with zipfile.ZipFile(path) as trace:
            assert trace.testzip() is None, row['path']
            assert any(name.endswith('.trace') for name in trace.namelist()), row['path']
facts = json.loads((folder / 'facts-report.json').read_text())
assert facts['finished'] and facts['planned_persona_days'] == 21
assert facts['actions'] == 120 and facts['completed_sessions'] == 16
assert facts['no_use_days'] == 5 and facts['unrun_persona_days'] == 0
assert facts['all_captured_personal_states_schema_valid']
events = [json.loads(line) for line in (folder / 'events.jsonl').read_text().splitlines() if line]
assert sum(event['kind'] == 'action' for event in events) == 120
assert sum(event['kind'] == 'session_ended' for event in events) == 16
assert sum(event['kind'] == 'no_use' for event in events) == 5
print(f'PASS: {len(included)} original evidence files verified; 120 actions, 16 sessions, 5 no-use days.')
print('Excluded artifacts are catalogued, not claimed as transferred.')
