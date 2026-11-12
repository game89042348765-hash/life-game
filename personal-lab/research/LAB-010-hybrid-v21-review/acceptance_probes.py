#!/usr/bin/env python3
"""Independent LAB-010 observations on pinned Hybrid v2.1. Local fictional fixtures only.

Success means every observation was reproduced, not that the candidate is accepted.
The report distinguishes fixed defects from residual issues. No network/API calls.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
ZIP_SHA = 'f6262b4db13149cd58d6a7d4421d0fe535ea81bd9ea424a39b977dccaabcb614'
TOOL_SHA = '10c3e098c2d7a554bb254148eb3e70b8c0e3850749e1cd0f8eaec78465cb152c'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--zip', type=Path, default=Path(__file__).parent/'incoming/LifeGame-Atlas-Hybrid-v2.1.zip')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    assert not args.out.exists(), 'Choose a new report; previous evidence is immutable'
    assert digest(args.zip) == ZIP_SHA, 'Wrong source ZIP'
    observations = []

    def record(code, status, detail):
        observations.append({'probe': code, 'status': status, **detail})
        args.out.parent.mkdir(parents=True, exist_ok=True)
        report = {'task': 'LAB-010', 'meaning': 'reproduced_observations_not_blanket_acceptance',
                  'candidate_zip_sha256': ZIP_SHA, 'candidate_tool_sha256': TOOL_SHA,
                  'observations': observations, 'executed': len(observations),
                  'residual_issues': [x['probe'] for x in observations if x['status']=='residual_issue'],
                  'network_requests': 0}
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        print(code, status, json.dumps(detail, ensure_ascii=False), flush=True)

    def refuses(fn):
        try:
            fn()
        except ValueError as exc:
            return str(exc)
        raise AssertionError('Expected refusal')

    with tempfile.TemporaryDirectory(prefix='lab010-acceptance-') as temporary:
        tmp = Path(temporary)
        with zipfile.ZipFile(args.zip) as z:
            names = set()
            for entry in z.infolist():
                p = Path(entry.filename)
                assert not p.is_absolute() and '..' not in p.parts and '\\' not in entry.filename
                assert not stat.S_ISLNK(entry.external_attr>>16) and entry.filename not in names
                names.add(entry.filename)
            assert z.testzip() is None
            z.extractall(tmp/'clean')
        root = tmp/'clean/LifeGame-Atlas-Hybrid-v2.1'
        assert digest(root/'tools/atlas.py') == TOOL_SHA
        atlas = module('lab010_atlas', root/'tools/atlas.py')
        fixture = module('lab010_fixture', root/'tools/verify_tools.py').fixture
        cats, jobs, domains, phases, frictions = atlas.taxonomy(root/'taxonomy.json')

        def valid(data, complete=False):
            errors = atlas.validate(data, cats, jobs, complete, domains, phases, frictions)
            assert errors == [], errors[:5]

        def dataset(name, data):
            path = tmp/name
            atlas.write_data(path, data)
            return path

        config = atlas.configuration()
        config['mode'] = 'synthetic_demo'
        manifest = json.loads((root/'BUNDLE_MANIFEST.json').read_text())
        listed = {r['path'] for r in manifest['files']}
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}-{'BUNDLE_MANIFEST.json'}
        assert listed == actual and not any('__pycache__' in p for p in actual)
        command = subprocess.run([sys.executable, '-B', str(root/'tools/atlas.py'), 'verify', str(root)], capture_output=True, text=True, timeout=15)
        assert command.returncode == 0, command.stderr
        record('A01_final_zip_integrity', 'fixed', {'verified_files': len(actual), 'missing_or_extra': 0, 'clean_zip_cli_exit': 0})

        data = fixture(1)
        for r in data['ratings']:
            r['scores'] = dict.fromkeys(atlas.DIMS, 3)
        data['ratings'][0]['scores']['value'] = 2
        partial = copy.deepcopy(data['ratings'][1])
        partial.update(id='R-PART', reviewer_id='C', context_id='C')
        partial['scores']['composability'] = None
        data['ratings'].append(partial)
        valid(data, True)
        ranked, _, _ = atlas.calculate(data, cats, jobs, config)
        assert ranked[0]['Q'] == 71.25
        record('A02_complete_review_aggregation', 'fixed', {'Q': ranked[0]['Q'], 'Q_min': ranked[0]['Q_min'], 'Q_max': ranked[0]['Q_max'], 'known_counts': ranked[0]['known_scores_per_dim']})

        partial['scores']['value'] = 0
        valid(data, True)
        ranked, _, audit = atlas.calculate(data, cats, jobs, config)
        assert not ranked and 'unresolved_rating_disagreement' in audit['excluded'][0]['reasons']
        data['decisions'].append({'id':'D-RESOLVE','element_id':data['elements'][0]['id'], 'type':'rating_resolution','resolved':True,'reason':'Synthetic: deliberately omit dissenting reviewer.', 'reviewer_ids':['synthetic-A','synthetic-B'], 'source_ids':[]})
        errors = atlas.validate(data, cats, jobs, True, domains, phases, frictions)
        assert any('omits disagreeing reviewers' in e for e in errors)
        data['decisions'][0]['reviewer_ids'].append('C')
        valid(data, True)
        ranked, _, _ = atlas.calculate(data, cats, jobs, config)
        assert len(ranked) == 1
        record('A03_partial_objection_and_resolution', 'fixed', {'partial_dissent_blocks':True,'omitted_dissenter_rejected':True,'all_disputants_resolution_accepted':True})

        seed = fixture(1)
        raw = {k:[] for k in atlas.TABLES}
        raw['sources'] = copy.deepcopy(seed['sources'])
        for i in range(10000):
            f = copy.deepcopy(seed['findings'][0])
            f['id'] = f'F-SHARD-{i:05d}'
            raw['findings'].append(f)
        valid(raw)
        inp = dataset('raw-10k', raw)
        out = tmp/'shards-10k'
        atlas.shard_findings(inp, out)
        receipt = json.loads((out/'shards_manifest.json').read_text())
        ids = [v for part in receipt['shards'].values() for v in part['finding_ids']]
        assert len(ids) == len(set(ids)) == 10000
        assert receipt['largest_part_records'] <= 60 and receipt['largest_standard_part_bytes'] <= 120000
        for part in receipt['shards'].values():
            rows = [json.loads(line) for line in (out/part['sources_file']).read_text().splitlines()]
            assert {s['id'] for s in rows} == set(part['source_ids'])
        record('A04_normal_10k_sharding', 'fixed', {'findings':10000,'parts':len(receipt['shards']),'max_records':receipt['largest_part_records'],'max_findings_file_bytes':receipt['largest_standard_part_bytes'],'all_source_ids_attached':True,'index_parts':len(receipt['index_parts'])})

        before = {p.relative_to(out).as_posix():digest(p) for p in out.rglob('*') if p.is_file()}
        refuses(lambda: atlas.shard_findings(inp, out))
        assert before == {p.relative_to(out).as_posix():digest(p) for p in out.rglob('*') if p.is_file()}
        refuses(lambda: atlas.shard_findings(inp, inp/'new-child'))
        bad = copy.deepcopy(raw)
        bad['findings'] = bad['findings'][:1]
        bad['findings'][0]['phase_code'] = 'X/../../escaped'
        bad_input = dataset('unsafe', bad)
        refuses(lambda: atlas.shard_findings(bad_input, tmp/'new-unsafe-output'))
        assert not (tmp/'new-unsafe-output').exists()
        record('A05_shard_preservation_and_path_validation', 'fixed', {'existing_bytes_unchanged':True,'input_descendant_refused':True,'unsafe_code_refused_before_output':True})

        full_input = dataset('full', seed)
        saved = (full_input/'elements.jsonl').read_bytes()
        refuses(lambda: atlas.prepare_blind_packet(full_input, full_input/'elements.jsonl'))
        refuses(lambda: atlas.prepare_blind_packet(full_input, full_input/'new.jsonl'))
        existing = tmp/'existing-blind.jsonl'
        existing.write_text('KEEP_EXISTING')
        refuses(lambda: atlas.prepare_blind_packet(full_input, existing))
        assert existing.read_text() == 'KEEP_EXISTING' and (full_input/'elements.jsonl').read_bytes() == saved
        record('A06_blind_default_preservation', 'fixed', {'input_alias_refused':True,'new_child_refused':True,'existing_external_file_preserved':True})

        for i, quota in enumerate([-1,True,False,1.5,'10',101]):
            run = tmp/f'bad-{i}.json'
            atlas.dump(run, {'rubric_version':'2.1','taxonomy_version':'2.1','selection':{'rare_gems_quota':quota}})
            refuses(lambda: atlas.configuration(run))
        assert atlas.configuration()['rare_gems_quota'] == 0
        record('A07_strict_quota', 'fixed', {'default':0,'negative_bool_float_string_over_limit_rejected':True})

        scoring = (root/'SCORING.md').read_text().strip()
        contract = (root/'DATA_CONTRACT.md').read_text().strip()
        for file in ['02-ANALYZE.txt','03-SELECT.txt','05-COORDINATE.txt']:
            text = (root/'PASTE'/file).read_text()
            assert scoring in text and contract in text
        for p in (root/'starter_tasks').glob('*.json'):
            task = json.loads(p.read_text())
            assert task['protocol_version'] == '2.1'
            assert all(digest(root/f) == h for f,h in task['input_hashes'].items())
        record('A08_mechanical_paste_and_task_sync', 'fixed', {'three_paste_files_contain_current_scoring_and_contract':True,'starter_hashes_match':True,'meaning':'byte synchronization does not prove internal consistency'})

        data = fixture(240)
        for i,r in enumerate(data['ratings']):
            r['scores'] = dict.fromkeys(atlas.DIMS, 3)
            r['scores']['value'] = 4 if i//2%2 == 0 else 2
            r['scores']['burden'] = 2 if i//2%2 == 0 else 4
        valid(data, True)
        _, _, audit = atlas.calculate(data, cats, jobs, config)
        assert all('core_ids' in s and 'full_atlas_ids' in s for s in audit['sensitivity'].values())
        assert audit['sensitivity']['low_effort']['full_atlas_jaccard_with_baseline'] < 1
        record('A09_full_atlas_sensitivity', 'fixed', {'scenarios':len(audit['sensitivity']),'low_effort_full_atlas_jaccard':audit['sensitivity']['low_effort']['full_atlas_jaccard_with_baseline']})

        assert '(по умолчанию 25)' in scoring and 'по умолчанию `0`' in scoring
        record('R01_conflicting_default_in_shared_rubric', 'residual_issue', {'priority':'P2','code_default':0,'document_defaults':[25,0],'copied_to':['PASTE/02-ANALYZE.txt','PASTE/03-SELECT.txt','PASTE/05-COORDINATE.txt'],'location':'SCORING.md:95 and SCORING.md:98','note':'The older G formula is explicitly replaced later; the two defaults within the same current clarification remain contradictory.'})

        large = {k:[] for k in atlas.TABLES}
        large['sources'] = copy.deepcopy(seed['sources'])
        large['findings'] = copy.deepcopy(seed['findings'])
        large['findings'][0]['description'] = 'Я'*150000
        valid(large)
        large_input = dataset('oversized', large)
        large_out = tmp/'oversized-shards'
        atlas.shard_findings(large_input, large_out, max_bytes=4096, index_max_records=1)
        receipt = json.loads((large_out/'shards_manifest.json').read_text())
        assert len(receipt['oversized_single_records']) == 1
        assert max(x['bytes'] for x in receipt['index_parts']) > 300000
        record('R02_compact_index_repeats_oversized_body', 'residual_issue', {'priority':'P1','finding_flagged_oversized':True,'finding_limit_bytes':4096,'index_bytes':receipt['index_parts'][0]['bytes'],'index_oversized_status':receipt['index_parts'][0].get('oversized_single_record'),'raw_description_preserved':True,'problem':'The navigation index repeats the entire oversized description; it has no byte bound or per-entry oversized status.'})

        source_heavy = fixture(60)
        source_heavy['elements'] = []
        source_heavy['ratings'] = []
        source_heavy['merge_map'] = []
        for s in source_heavy['sources']:
            s['notes'] = 'synthetic analysis note. '*250
        valid(source_heavy)
        heavy_input = dataset('source-heavy', source_heavy)
        heavy_out = tmp/'source-heavy-shards'
        atlas.shard_findings(heavy_input, heavy_out)
        receipt = json.loads((heavy_out/'shards_manifest.json').read_text())
        part = next(iter(receipt['shards'].values()))
        finding_bytes = (heavy_out/part['file']).stat().st_size
        source_bytes = (heavy_out/part['sources_file']).stat().st_size
        assert finding_bytes < 120000 < source_bytes and not receipt['oversized_single_records']
        record('R03_sources_escape_packet_budget', 'residual_issue', {'priority':'P1','records':part['count'],'finding_bytes':finding_bytes,'sources_bytes':source_bytes,'combined_bytes':finding_bytes+source_bytes,'configured_max_bytes':120000,'oversized_flags':receipt['oversized_single_records'],'problem':'Byte limit and manifest bytes cover only findings, not their attached sources; an ordinary unflagged job exceeds the budget.'})

        race_out = tmp/'race-blind.jsonl'
        original_replace = atlas.os.replace
        marker = 'NEWER_CONCURRENT_RELEASE'
        def concurrent_publish(src, dest):
            Path(dest).write_text(marker)
            return original_replace(src, dest)
        atlas.os.replace = concurrent_publish
        try:
            result = atlas.prepare_blind_packet(full_input, race_out)
        finally:
            atlas.os.replace = original_replace
        assert race_out.read_text() != marker and result['blind_elements_prepared'] == 1
        record('R04_blind_publication_can_replace_concurrent_output', 'residual_issue', {'priority':'P2','existing_before_call_refused':True,'file_published_after_last_exists_check_overwritten':True,'interleaving':'controlled concurrent file creation immediately before actual os.replace; all paths inside TemporaryDirectory','problem':'Atomic replacement is not atomic no-overwrite publication.'})

    print(json.dumps({'observations':len(observations),'residual_issues':[x['probe'] for x in observations if x['status']=='residual_issue'],'report':str(args.out)},ensure_ascii=False))


if __name__ == '__main__':
    main()
