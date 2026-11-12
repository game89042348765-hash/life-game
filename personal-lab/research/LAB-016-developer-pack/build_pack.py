#!/usr/bin/env python3
"""Curated developer snapshot; repository originals are emitted byte-for-byte."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = '89112c29dacea254cd8f50c4197a8ee77e764917'
CLIENT_DATE = '2026-11-13'
ROOT_KEEP = {'.clinerules', 'AGENTS.md', 'LABORATORY_HANDOFF.md', 'LifeGame_CURRENT_WORK.md',
             'LifeGame_PROJECT_CONTEXT.md', 'index.html', 'lifegame_happiness_200_messages.json'}
LATEST_LABS = {'LAB-002-digital-month', 'LAB-013-daily-ux', 'LAB-014-repeat-pilot', 'LAB-015-live-pilot'}


def selection(name):
    p = Path(name); parts = p.parts
    if p.suffix.lower() in {'.zip', '.bundle', '.7z', '.tar', '.gz'}:
        return False, 'packed archives or heavy browser traces'
    if any(x in parts for x in ('backups', 'history', 'verification', 'profiles', '__pycache__', 'node_modules', '.git')):
        return False, 'backups, history, generated output, profiles or dependencies'
    if name in ROOT_KEEP:
        return True, 'root code and current context/rules'
    if parts[0] in {'assets', 'personal', 'next', 'tests'}:
        return True, 'current runtime, assets, docs or tests'
    if parts[0] == 'demo':
        return (False, 'superseded before-layout copy') if 'card-layout-before' in parts else (True, 'optional design/demo reference')
    if parts[0] == 'docs':
        if len(parts) == 2 or parts[1] in {'design', 'ux'}:
            return True, 'handoff and design/UX reference'
        return False, 'historical rebuild snapshots'
    if parts[0] == 'downloads':
        if len(parts) == 2 and p.suffix in {'.md', '.html', '.png'}:
            return True, 'concept/document or linked current demo asset'
        return False, 'old package indexes and distributions'
    if parts[0] == 'personal-lab':
        if len(parts) == 2 or parts[1] in {'fonts', 'tests', 'experiments'}:
            return True, 'current lab runtime, experiments, rules and tests'
        if parts[1] == 'research':
            lab = parts[2]
            if lab == 'ATLAS_CURRENT.md' or lab == 'LAB-012-development-priorities.md' or lab in LATEST_LABS:
                return True, 'current useful harness, priorities or latest UX work'
            if lab == 'LAB-005-resume' and len(parts) == 4:
                return True, 'current transport implementation/status'
            if lab == 'LAB-011-hybrid-v211-review' and (parts[3] == 'release' or len(parts) == 4 and p.name in
                   {'README.md', 'COORDINATOR-REVIEW.md', 'IMPLEMENTATION.md', 'SOURCE.json', 'VERIFICATION.json', 'DELIVERY.json'}):
                return True, 'current HYDRA release and acceptance context'
        return False, 'superseded lab inputs, original pilot bulk evidence or obsolete assignments'
    return False, 'superseded handoff or local recovery note'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(output):
    if output.exists():
        raise ValueError('choose a new output file')
    tree = subprocess.check_output(['git', 'ls-tree', '-r', '-z', BASE], cwd=REPO).split(b'\0')
    wanted, omitted = [], []
    for row in tree:
        if not row:
            continue
        meta, path = row.split(b'\t', 1); mode, kind, oid = meta.decode().split(); name = path.decode()
        keep, reason = selection(name)
        if keep:
            if kind != 'blob' or mode == '120000':
                raise ValueError('unsupported source entry: ' + name)
            wanted.append((name, oid, mode, reason))
        else:
            omitted.append({'path': name, 'reason': reason})
    raw = subprocess.run(['git', 'cat-file', '--batch'], input=('\n'.join(x[1] for x in wanted)+'\n').encode(),
                         cwd=REPO, capture_output=True, check=True).stdout
    files, metadata = {}, {}; offset = 0
    for name, oid, mode, reason in wanted:
        end = raw.index(b'\n', offset); header = raw[offset:end].decode().split(); size = int(header[2]); offset = end+1
        assert header[:2] == [oid, 'blob']
        data = raw[offset:offset+size]; offset += size+1
        files[name] = data; metadata[name] = {'origin': 'repository', 'reason': reason, 'git_blob': oid, 'mode': mode}
    assert offset == len(raw)
    for path in sorted((HERE / 'handout').glob('*.md')):
        files[path.name] = path.read_bytes(); metadata[path.name] = {'origin': 'LAB-016 handoff instructions'}
    files['tools/verify_package.py'] = (HERE / 'verify_package.py').read_bytes()
    metadata['tools/verify_package.py'] = {'origin': 'LAB-016 integrity utility'}
    source = {'task': 'LAB-016', 'client_date': CLIENT_DATE, 'client_timezone': 'Europe/Moscow',
              'source_repository': 'game89042348765-hash/life-game', 'source_branch': 'lab/synthetic-users', 'source_commit': BASE,
              'main_ref_at_selection': '90df9542bbffa5651fd31bdad12460a4c586c3ef',
              'source_scope': 'Selected working tree of this commit, not all refs/history; current main is included in its ancestry.',
              'repository_files_byte_identical': True, 'runtime_changed_for_packaging': False,
              'purpose': 'Code, context, current experiments, tests and concise evidence for an external developer model',
              'git_history_included': False, 'browser_profiles_or_real_user_data_included': False,
              'history_dependent_tests': ['personal-lab/tests/daily-ux.py', 'past packet builders using git show'],
              'omissions': 'OMITTED.json; existing historical documents can refer to intentionally excluded files.'}
    files['SOURCE.json'] = (json.dumps(source, ensure_ascii=False, indent=2)+'\n').encode()
    files['OMITTED.json'] = (json.dumps({'source_commit': BASE, 'excluded_tracked_files': omitted,
                                      'also_not_included': ['Git object database/all-ref backup', 'ignored local verification data/profiles/dependencies']},
                                     ensure_ascii=False, indent=2)+'\n').encode()
    groups = Counter(name.split('/')[0] if '/' in name else '[root]' for name in [*files, 'CONTENTS.md', 'MANIFEST.json'])
    contents = '# Состав рабочего пакета\n\n13 ноября 2026. Начать с 00_START_HERE.md. Подробные исходные пути/хеши — MANIFEST.json, исключения — OMITTED.json.\n\n'
    contents += '| Раздел | Файлов |\n|---|---:|\n' + ''.join(f'| {name} | {count} |\n' for name,count in sorted(groups.items()))
    contents += '\nПриложения — обычные исходные файлы с прежними путями; демо/исследования отмечены как справка. SOURCE фиксирует базу, а не выдаёт этот каталог за полный Git-репозиторий.\n'
    files['CONTENTS.md'] = contents.encode()
    for name in files:
        metadata.setdefault(name, {'origin': 'LAB-016 generated package metadata'})
    manifest = {'format': 1, 'source_commit': BASE, 'files': {name: {'sha256': sha(data), 'bytes': len(data), **metadata[name]}
                                                          for name,data in sorted(files.items())}}
    files['MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):
            entry = zipfile.ZipInfo('LifeGame-Developer-Pack/'+name, (2026,11,13,0,0,0)); entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr = (0o755 if metadata.get(name,{}).get('mode') == '100755' else 0o644) << 16
            archive.writestr(entry, data)
    if output.stat().st_size >= 100_000_000:
        raise ValueError('archive exceeds requested size budget')
    return {'task': 'LAB-016', 'file': str(output), 'bytes': output.stat().st_size, 'sha256': sha(output.read_bytes()),
            'zip_entries': len(files), 'manifest_entries': len(manifest['files']), 'repository_files': len(wanted),
            'excluded_tracked_files': len(omitted), 'uncompressed_bytes': sum(map(len,files.values())), 'source_commit': BASE}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True); args=parser.parse_args()
    print(json.dumps(build(args.output.resolve()), ensure_ascii=False, indent=2))
