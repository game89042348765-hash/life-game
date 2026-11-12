#!/usr/bin/env python3
"""Reproduce review observations on the pinned v1 and returned Hybrid v2, not acceptance tests."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
OLD_SHA = '0629856c6bb41a4f463ea1977f09e58e9765dbbb0c8a934e47f1fc528132cdc0'
NEW_SHA = '3bef0cc44cf58e6a46318b909efc5a345184be7a5b4c6a09813a3b985e287e91'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',required=True,type=Path)
    p.add_argument('--candidate',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    assert not args.out.exists(), 'Preserve previous results; choose a new output'
    assert digest(args.original/'tools/atlas.py')==OLD_SHA
    assert digest(args.candidate/'tools/atlas.py')==NEW_SHA
    original=module('old_atlas',args.original/'tools/atlas.py')
    hybrid=module('new_atlas',args.candidate/'tools/atlas.py')
    fixture=module('old_fixture',args.original/'tools/verify_tools.py').fixture
    hfixture=module('new_fixture',args.candidate/'tools/verify_tools.py').fixture
    cats,jobs=original.taxonomy(args.original/'taxonomy.json')
    hc,hj,domains,phases,frictions=hybrid.taxonomy(args.candidate/'taxonomy.json')
    old_config=original.configuration();old_config['mode']='synthetic_demo'
    new_config=hybrid.configuration();new_config['mode']='synthetic_demo'
    results=[]
    def record(name,data):
        results.append({'probe':name,**data})
        print(name,json.dumps(data,ensure_ascii=False),flush=True)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps({'status':'review_in_progress_not_acceptance','original_tool_sha256':OLD_SHA,'candidate_tool_sha256':NEW_SHA,'probes':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def third(data,complete=False,value=0):
        r=copy.deepcopy(data['ratings'][0]);r.update(id='R-THIRD',reviewer_id='reviewer-C',context_id='context-C')
        r['scores']=dict.fromkeys(original.DIMS,3);r['scores']['value']=value
        if not complete:r['scores']['composability']=None
        data['ratings'].append(r)
    data=fixture(1)
    for r in data['ratings']:r['scores']=dict.fromkeys(original.DIMS,3)
    third(data,value=0)
    assert not original.validate(data,cats,jobs,True)
    assert not hybrid.validate(data,hc,hj,True,domains,phases,frictions)
    a,_,aa=original.calculate(data,cats,jobs,old_config)
    b,_,bb=hybrid.calculate(data,hc,hj,new_config)
    assert len(a)==1 and not b
    record('O1_partial_objection',{'original_admits':True,'hybrid_blocks':True,'hybrid_reasons':bb['excluded'][0]['reasons']})

    data=fixture(1)
    for r in data['ratings']:r['scores']=dict.fromkeys(original.DIMS,3)
    third(data,complete=True,value=0)
    data['decisions'].append({'id':'D-RESOLVE','element_id':data['elements'][0]['id'],'type':'rating_resolution','resolved':True,'reason':'Synthetic check; dissenting reviewer deliberately omitted.','reviewer_ids':['synthetic-A','synthetic-B'],'source_ids':[]})
    a=original.validate(data,cats,jobs,True)
    b=hybrid.validate(data,hc,hj,True,domains,phases,frictions)
    assert not a and any('omits disagreeing reviewers' in e for e in b)
    record('O2_resolution_omits_dissenter',{'original_errors':a,'hybrid_errors':b})

    data=fixture(1)
    data['ratings'][0]['scores']['value']=2
    data['ratings'][1]['scores']['value']=3
    third(data,value=3)
    assert not hybrid.validate(data,hc,hj,True,domains,phases,frictions)
    ranked,_,_=hybrid.calculate(data,hc,hj,new_config)
    complete_medians={d:(data['ratings'][0]['scores'][d]+data['ratings'][1]['scores'][d])/2 for d in original.DIMS}
    expected=original.score(complete_medians,new_config['weights'])
    observed=ranked[0]['Q']
    assert expected==71.25 and observed==75
    record('H2_aggregation_contract',{'Q_from_documented_complete_reviews':expected,'Q_from_actual_known_scores':observed,'disagreement':False,'effect':'partial review changes Q, not just disagreement gate'})

    process=subprocess.run([sys.executable,str(args.candidate/'tools/atlas.py'),'verify',str(args.candidate)],text=True,capture_output=True,timeout=15)
    assert process.returncode==1 and '__pycache__' in process.stderr
    record('H1_bundle_manifest',{'exit_code':process.returncode,'stderr':process.stderr.strip()})

    with tempfile.TemporaryDirectory(prefix='lab008-probes-') as temp:
        temp=Path(temp)
        raw={k:[] for k in hybrid.TABLES}
        seed=hfixture(1)
        raw['sources']=copy.deepcopy(seed['sources'])
        for i in range(10000):
            f=copy.deepcopy(seed['findings'][0]);f['id']=f'F-RAW-{i:05d}'
            raw['findings'].append(f)
        dataset=temp/'raw';hybrid.write_data(dataset,raw)
        out=temp/'shards';summary=hybrid.shard_findings(dataset,out)
        receipt=json.loads((out/'shards_manifest.json').read_text())
        largest=max(v['count'] for v in receipt['shards'].values())
        assert summary['shards_count']==1 and largest==10000
        record('H3_unbounded_shard',{'input_findings':10000,'output_shards':1,'largest_shard':largest,'index_bytes':(out/'compact_findings_index.txt').stat().st_size})

        old_file=out/next(iter(receipt['shards'].values()))['file']
        previous_index=(out/'compact_findings_index.txt').read_bytes()
        second=copy.deepcopy(seed)
        second['findings'][0]['phase_code']=next(p for p in sorted(phases) if p!=seed['findings'][0]['phase_code'])
        raw2={k:[] for k in hybrid.TABLES};raw2['sources']=second['sources'];raw2['findings']=second['findings']
        dataset2=temp/'raw2';hybrid.write_data(dataset2,raw2)
        hybrid.shard_findings(dataset2,out)
        new_receipt=json.loads((out/'shards_manifest.json').read_text())
        listed={v['file'] for v in new_receipt['shards'].values()}
        assert old_file.exists() and old_file.name not in listed
        assert previous_index!=(out/'compact_findings_index.txt').read_bytes()
        record('H4_reused_shard_output',{'existing_index_overwritten':True,'old_shard_left_unlisted':True,'rerun_refused':False})

        unsafe={k:[] for k in hybrid.TABLES};unsafe['sources']=copy.deepcopy(seed['sources']);unsafe['findings']=copy.deepcopy(seed['findings'])
        unsafe['findings'][0]['phase_code']='X/../../escaped'
        unsafe['findings'][0]['primary_friction_code']='GENERAL'
        unsafe_dir=temp/'unsafe-data';hybrid.write_data(unsafe_dir,unsafe)
        target=temp/'unsafe-output';(target/'SHARD_X').mkdir(parents=True)
        marker=temp/'escaped__GENERAL.jsonl';marker.write_text('CONTROLLED TEMPORARY MARKER',encoding='utf-8')
        schema_errors=hybrid.validate(unsafe,hc,hj,False,domains,phases,frictions)
        hybrid.shard_findings(unsafe_dir,target)
        escaped='F-DEMO-' in marker.read_text(encoding='utf-8')
        assert escaped
        record('H5_shard_path_containment',{'schema_errors':schema_errors,'controlled_file_outside_target_overwritten':True,'precondition':'existing output contains SHARD_X subdirectory; all affected files were inside this test TemporaryDirectory'})

        blind_dataset=temp/'blind-dataset';hybrid.write_data(blind_dataset,seed)
        path=blind_dataset/'elements.jsonl';before=path.read_bytes()
        hybrid.prepare_blind_packet(blind_dataset,path)
        after=path.read_bytes();errors=hybrid.validate(hybrid.load(blind_dataset),hc,hj,False,domains,phases,frictions)
        assert before!=after and errors
        record('H6_blind_output_aliases_input',{'source_catalog_overwritten':True,'validation_errors_after_overwrite':errors[:8]})

        run=temp/'negative-quota.json'
        run.write_text(json.dumps({'rubric_version':'2.0','taxonomy_version':'2.0','selection':{'rare_gems_quota':-1,'mode':'synthetic_demo','core':1,'target':100}}),encoding='utf-8')
        cfg=hybrid.configuration(run)
        rows=[{'id':str(i),'Q':90-i,'element':{'id':str(i),'jobs':['J01'],'category_ids':['C01'],'family_id':str(i),'paradigm_novelty':3}} for i in range(8)]
        selected,*_=hybrid.run_selection_for_pool(rows,cfg)
        rare=sum(x['tier']=='rare_lateral_gem' for x in selected)
        assert cfg['rare_gems_quota']==-1 and rare==6
        record('H7_negative_rare_quota',{'configured_quota':-1,'configuration_rejected':False,'actual_rare_lane_seats':rare})

    old_gain=.50*(1/2)+.30+.20
    narrow_gain=.50+.30+.20
    record('O3_label_density_policy',{'v1_narrow_G':narrow_gain,'v1_with_one_extra_already_covered_job_G':old_gain,'classification':'declared policy with an incentive tradeoff, not an arithmetic implementation error'})
    data=fixture(240)
    for i,r in enumerate(data['ratings']):
        item=i//2
        r['scores']=dict.fromkeys(original.DIMS,3)
        r['scores']['value']=4 if item%2==0 else 2
        r['scores']['burden']=2 if item%2==0 else 4
    _,_,old_audit=original.calculate(data,cats,jobs,old_config)
    _,_,new_audit=hybrid.calculate(data,hc,hj,new_config)
    observed=new_audit['sensitivity']['low_effort']['full_atlas_jaccard_with_baseline']
    assert observed<1 and 'full_atlas_occurrences_in_declared_scenarios' in new_audit
    record('O4_full_atlas_sensitivity_improvement',{'original_has_full_atlas_metric':'full_atlas_jaccard_with_baseline' in old_audit['sensitivity']['low_effort'],'hybrid_full_atlas_jaccard_low_effort':observed,'candidate_elements':240,'selected':new_audit['selected']})
    shared=[]
    for paste in ['02-ANALYZE.txt','03-SELECT.txt','05-COORDINATE.txt']:
        shared.append({'paste':paste,'current_SCORING_embedded':(args.candidate/'SCORING.md').read_text() in (args.candidate/'PASTE'/paste).read_text()})
    assert not any(x['current_SCORING_embedded'] for x in shared)
    record('H8_stale_shared_instructions',{'standalone_texts':shared,'old_quarantine_contract_still_present':'для последних двух возможен пустой список' in (args.candidate/'DATA_CONTRACT.md').read_text()})
    report={'status':'review_observations_not_acceptance','original_tool_sha256':OLD_SHA,'candidate_tool_sha256':NEW_SHA,'real_research_performed':False,'probes':results}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
