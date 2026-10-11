"""Audit collected AP091 evidence without constructing or rechecking a proof."""
import argparse
import ast
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

from package_sqrt2_power_wmi import ROOT
from run_sqrt2_power_pilot import save_new,successful

OBS=ROOT/'research/arithmetic-library/sqrt2-power/observations'
HA='shared-wave-fixed-half-log-root-witness-v1'
LEAN='shared-wave-fixed-half-log-root-witness-lean-wmi-v1'
HA_SHA='9a9889aa4290b7c3b769213620d4b2137eb01274a50fb994d7b66347d67adba3'
LEAN_SHA='ce93c0515cbace3963ec0d7961aabf293255ce209cfe4f6d28f313f01a775cf6'
RUNS=(('wmi-ap091-preflight-v2','268994','5d3a7f7ab86e1fb9a9b37eb1281556463b914028d35ca9d432e34c900b5f0642','prepared_not_theorem_checked'),
    ('wmi-ap091-full-v1','269156','4098461cc203b1a422961e1d18a08af283fd5619f492bbeee13c62e030498cc0','HA_Lean_and_regressions_checked'))


def require(condition,message):
    if not condition:raise ValueError(message)


def read(path):return json.loads(path.read_bytes())


def bind_current_case(report,folder):
    """Permit only unrelated dispatch additions, preserving actual proof inputs."""
    import run_sqrt2_power_wave as wave
    case=report['case'];driver='scripts/run_sqrt2_power_wave.py';current=wave.pins(case)
    require(current.keys()==report['source_pins'].keys(),'proof source set changed')
    require(all(current[name]==pin for name,pin in report['source_pins'].items() if name!=driver),'proof or kernel source changed')
    pin=report['source_pins'][driver];old=gzip.decompress((folder/report['source_snapshots'][driver]).read_bytes())
    require(len(old)==pin['bytes'] and sha256(old).hexdigest()==pin['sha256'],'archived driver changed')
    def functions(raw):return {n.name:n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
    before=functions(old);now=functions(wave.SCRIPT.read_bytes())
    for name in ('run','replay','check_forged_root_rejection','generation_phase_limits','replay_phase_limits'):
        require(ast.dump(before[name])==ast.dump(now[name]),'original verification function changed: '+name)
    def branch(function):
        matches=[]
        for node in ast.walk(function):
            if not isinstance(node,ast.If) or not isinstance(node.test,ast.Compare):continue
            test=node.test
            if (isinstance(test.left,ast.Name) and test.left.id=='identifier' and len(test.ops)==len(test.comparators)==1
                    and isinstance(test.ops[0],ast.Eq) and isinstance(test.comparators[0],ast.Constant)
                    and test.comparators[0].value==case):matches.append([ast.dump(n) for n in node.body])
        require(len(matches)==1,'missing or ambiguous exact case branch');return matches[0]
    for name in ('pins','target_for','worker'):
        require(branch(before[name])==branch(now[name]),'selected case changed: '+name)


def audit():
    from sqrt2_power_automation_baseline import runtime
    from sqrt2_power_wmi_lean_runtime import lean_runtime
    from check_sqrt2_power_fresh_lean import exact_bundle,MODULES,SOURCE_SHA256,AUDIT_OUTPUT
    import run_sqrt2_power_wave as wave
    import sqrt2_power_fixed_half_log_root_witness as proof
    s=runtime();ls=lean_runtime();reports=[]
    for name,job,snapshot,status in RUNS:
        folder=OBS/name;c=read(folder/'collection.json');r=read(folder/'evidence/pilot-report.json')
        require(c['job_id']==r['job_id']==job and c['snapshot_sha256']==r['source_snapshot_sha256']==snapshot
            and c['downloaded_bytes_match'] is True and c['accounting'].startswith(job+'|COMPLETED|0:0|')
            and c['pilot_status']==r['status']==status,'collection or scheduler mismatch')
        for relative,pin in c['remote_artifact_manifest'].items():
            require(s.hash_file(folder/relative)==pin,'collected artifact changed: '+relative)
        require(r['snapshot_before']==r['snapshot_after'],'input snapshot changed during execution')
        for label,p in r['processes'].items():
            s.validate_process_record(p,command=tuple(p['command']),limits=s.ProcessLimits(**p['limits']))
            require(successful(p) and read(folder/'evidence'/(label+'.json'))==p,'failed or changed phase')
        reports.append(r)
    pre,full=reports
    require(pre['full_attempt_started'] is False and full['full_attempt_started'] is True,'attempt identity changed')
    require(full['preparation']['report_sha256']==s.hash_file(OBS/RUNS[0][0]/'evidence/pilot-report.json')['sha256'],
        'preparation receipt changed')
    for folder,digest in ((HA,HA_SHA),(LEAN,LEAN_SHA)):
        require(s.hash_file(OBS/folder/'report.json')['sha256']==digest,'canonical report changed')
        for item in (OBS/folder).rglob('*'):
            if item.is_file():require(s.hash_file(item)==s.hash_file(OBS/RUNS[1][0]/'source'/item.relative_to(ROOT)),
                'canonical copy differs from collected artifact')
    raw,bound=exact_bundle(OBS/HA);ha=read(OBS/HA/'report.json')
    require(bound['case']=='AP091' and bound['target_ast_sha256']==proof.TARGET_SHA256
        and bound['nodes']==586 and bound['bundle_sha256']==full['cost']['actual_bundle_sha256'],'exact HA identity changed')
    bind_current_case(ha,OBS/HA)
    processes={};values={}
    for phase in ('generation','fresh_replay'):
        record=ha['process_records'][phase];encoded=gzip.decompress((OBS/HA/record['path']).read_bytes())
        require(sha256(encoded).hexdigest()==record['raw_sha256'],'changed HA process archive')
        p=json.loads(encoded);value=json.loads(p['stdout'])
        s.validate_process_record(p,command=tuple(p['command']),limits=s.ProcessLimits(**p['limits']),
            input_bytes=b'' if phase=='generation' else wave.canonical(values['generation']))
        require(successful(p),'HA process failed');processes[phase]=p;values[phase]=value
    replay=values['fresh_replay'];diagnostics=values['generation']['diagnostics'];tree=json.loads(raw)
    require(all(replay[k] is True for k in ('original_target_checked','empty_context','false_target_rejected','forged_body_rejected')),
        'missing ordinary HA acceptance controls')
    require(replay['kernel_calls']==replay['local_nodes']==586 and replay['proof_nodes']==66081,'changed HA coverage')
    require(tree[3][:-1]==proof.read_mixed_archive(proof.FIXED_ARCHIVE),'AP090 prefix changed')
    require(all(all(type(d) is int and 0<=d<i for d in row[2]) for i,row in enumerate(tree[3])),'non-topological proof DAG')
    require(proof.json_hash(tree[3][-1][3])=='5c6256486a737358bac092da81785679a518b47da5f66dd9a76d66f3a99ee175','native body changed')
    registry=proof.definition_registry();seen=set();ids=set()
    for name,spec in registry.items():
        require(set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids,'definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    require(len(registry)==21 and all(registry[k]==v for k,v in proof.fixed_registry().items()),'definition identity changed')
    require(diagnostics['new_induction_count']==0 and diagnostics['new_definition_ids']==[]
        and diagnostics['new_axioms']==[] and diagnostics['helper_statement_ast_sha256']=={},'new assumption introduced')
    lean=read(OBS/LEAN/'report.json')
    require(lean['status']=='fresh_lean_checked' and tuple(r['module'] for r in lean['compilation'])==MODULES
        and lean['axiom_audit']['stdout']==AUDIT_OUTPUT,'fresh Lean checks incomplete')
    for name,digest in zip(MODULES,SOURCE_SHA256):
        require(s.hash_file(OBS/LEAN/'sources/PeanoLab'/(name+'.lean'))['sha256']==digest,'Lean checker source changed')
    require(len(lean['checks'])==1 and lean['checks'][0]['independent_lean_checked'] is True,'Lean acceptance missing')
    checked=lean['checks'][0]
    require(all(checked[k]==bound[k] for k in ('case','report_sha256','bundle_sha256','target_ast_sha256','nodes','root')),'Lean checked different data')
    require(len(lean['negative_controls'])==2 and all(r['rejected'] for r in lean['negative_controls']),'negative controls missing')
    phases=[lean['version_probe'],*(r['process'] for r in lean['compilation']),lean['axiom_audit'],checked['process'],
        *(r['process'] for r in lean['negative_controls'])]
    for index,p in enumerate(phases):
        ls.validate_process_record(p,command=tuple(p['command']),limits=ls.ProcessLimits(**p['limits']))
        require(read(OBS/LEAN/'processes'/f'{index:02d}.json')==p,'Lean process copy changed')
        require(successful(p) if index<len(phases)-2 else p['returncode']==1 and p['reason']=='exited','Lean process failed')
    expected={'scripts/test_sqrt2_power_fixed_half_log_root_witness.py':13,'scripts/test_sqrt2_power_fixed_half_log_root.py':13,
        'scripts/test_sqrt2_power_half_log_root_uniform.py':13,'scripts/test_sqrt2_power_wave.py':14}
    require({r['file'] for r in full['regressions']}==expected.keys(),'regression files changed')
    for row in full['regressions']:
        require(s.hash_file(ROOT/row['file'])==row['pin'] and str(expected[row['file']])+' passed' in row['process']['stdout'],
            'regression source or result changed')
    require('peano_lab.library.theorems' not in sys.modules,'unexpected catalogue import')
    return dict(status='passed',case='AP091',authority='metadata_consistency_not_new_proof_authority',
        job_id='269156',ha=bound,definition_count=21,AP090_prefix_preserved=True,constructors=66081,
        HA_generation_cpu=processes['generation']['resources']['cpu_seconds'],HA_replay_cpu=processes['fresh_replay']['resources']['cpu_seconds'],
        Lean_total_cpu=lean['measured_cpu_seconds'],Lean_total_wall=lean['elapsed_wall_seconds'],
        new_focused_tests=13,older_proof_regressions_rerun=26,controller_tests=14,migration_tests=19,routing_tests=7,
        total_additional_statements=208,total_distinct_checked_statements=241,focused_proof_regressions=1567,
        IR072_open=True,IR_parents_closed=0,library_admissions=0,publication_performed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=audit()
    if args.output:save_new(args.output,json.dumps(result,sort_keys=True,indent=2).encode()+b'\n')
    print(json.dumps(result,sort_keys=True))
