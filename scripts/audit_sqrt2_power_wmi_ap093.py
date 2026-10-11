"""Audit AP093's collected HA/Lean/test evidence; never generate a proof."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

from audit_sqrt2_power_wmi_ap091 import ROOT,OBS,require,read,bind_current_case
from run_sqrt2_power_pilot import save_new,successful

RUN='wmi-ap093-full-v1'
JOB='284690'
SNAPSHOT='dbe20831c2290caf4492dac7c66001ee4d5046a45675513e22b6cb7f2dc70dbb'
HA='shared-wave-log-root-half-argument-v1'
LEAN='shared-wave-log-root-half-argument-lean-wmi-v1'
BUNDLE='d8a884f082830521daf08ad2866919f91894adbf5dcff76af374cdc6049f2ec5'
BODY_HASHES=('eec17e6eb437cacfee5f6d24facb41fbae9a20cd97a13cbb53518349c29fd111',
    '18e8491aa09b0a1cb363002a0041766fd4a45fa6f8d5d9295738ea4282db1b69')


def audit():
    from sqrt2_power_automation_baseline import runtime
    from sqrt2_power_wmi_lean_runtime import lean_runtime
    from check_sqrt2_power_fresh_lean import exact_bundle,MODULES,SOURCE_SHA256,AUDIT_OUTPUT
    import run_sqrt2_power_wave as wave
    import sqrt2_power_log_root_half_argument as proof
    s=runtime();ls=lean_runtime();folder=OBS/RUN
    c=read(folder/'collection.json');report=read(folder/'evidence/pilot-report.json')
    require(c['job_id']==report['job_id']==JOB and c['snapshot_sha256']==report['source_snapshot_sha256']==SNAPSHOT
        and c['downloaded_bytes_match'] is True and c['accounting'].startswith(JOB+'|COMPLETED|0:0|')
        and c['pilot_status']==report['status']=='HA_Lean_and_regressions_checked','run identity changed or incomplete')
    for name,pin in c['remote_artifact_manifest'].items():require(s.hash_file(folder/name)==pin,'downloaded artifact changed: '+name)
    require(report['snapshot_before']==report['snapshot_after'] and report['full_attempt_started'] is True,'input or attempt changed')
    for label,p in report['processes'].items():
        s.validate_process_record(p,command=tuple(p['command']),limits=s.ProcessLimits(**p['limits']))
        require(successful(p) and read(folder/'evidence'/(label+'.json'))==p,'failed or changed process: '+label)
    for leaf in (HA,LEAN):
        for path in (OBS/leaf).rglob('*'):
            if path.is_file():require(s.hash_file(path)==s.hash_file(folder/'source'/path.relative_to(ROOT)),'canonical copy changed')
    raw,bound=exact_bundle(OBS/HA);ha=read(OBS/HA/'report.json');values={};processes={}
    require(bound['case']=='AP093' and bound['bundle_sha256']==BUNDLE and bound['target_ast_sha256']==proof.TARGET_SHA256
        and bound['nodes']==69 and bound['root']==68 and bound['bundle_bytes']==189044,'checked certificate identity changed')
    bind_current_case(ha,OBS/HA)
    for phase in ('generation','fresh_replay'):
        record=ha['process_records'][phase];encoded=gzip.decompress((OBS/HA/record['path']).read_bytes())
        require(sha256(encoded).hexdigest()==record['raw_sha256'],'HA process digest changed')
        p=json.loads(encoded);value=json.loads(p['stdout'])
        s.validate_process_record(p,command=tuple(p['command']),limits=s.ProcessLimits(**p['limits']),
            input_bytes=b'' if phase=='generation' else wave.canonical(values['generation']))
        require(successful(p),'HA phase failed');values[phase]=value;processes[phase]=p
    replay=values['fresh_replay'];diagnostics=values['generation']['diagnostics'];tree=json.loads(raw)
    require(all(replay[k] is True for k in ('original_target_checked','empty_context','false_target_rejected','forged_body_rejected')),
        'HA controls missing')
    require(replay['kernel_calls']==replay['local_nodes']==69 and replay['proof_nodes']==4933,'full replay coverage changed')
    def signature(row,rows):
        return proof.canonical((row[0],row[1],[rows[d][1] for d in row[2]],row[3]))
    old_rows=[proof.read_mixed_archive(pin) for pin in proof.ARCHIVES]
    allowed={signature(row,rows) for rows in old_rows for row in rows}
    require(all(signature(row,tree[3]) in allowed for row in tree[3][:-2]),'changed inherited body or dependency')
    reached=set();pending=[68]
    while pending:
        i=pending.pop()
        if i not in reached:reached.add(i);pending.extend(tree[3][i][2])
    require(reached==set(range(69)),'irrelevant or disconnected certificate node')
    require(tuple(proof.json_hash(row[3]) for row in tree[3][-2:])==BODY_HASHES,'new native proof bodies changed')
    require(all(all(type(d) is int and 0<=d<i for d in row[2]) for i,row in enumerate(tree[3])),'non-topological proof DAG')
    require(diagnostics['new_induction_count']==0 and diagnostics['new_definition_ids']==[] and diagnostics['new_axioms']==[]
        and diagnostics['helper_statement_ast_sha256']==proof.HELPER_TARGET_SHA256,'new assumptions or helper mismatch')
    registry=proof.definition_registry();seen=set();ids=set()
    for name,spec in registry.items():
        require(set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids,'definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    require(len(registry)==16,'definition count changed')
    old=OBS/'shared-wave-fixed-half-log-fine-root-v1';bind_current_case(read(old/'report.json'),old)
    lean=read(OBS/LEAN/'report.json')
    require(lean['status']=='fresh_lean_checked' and tuple(r['module'] for r in lean['compilation'])==MODULES
        and lean['axiom_audit']['stdout']==AUDIT_OUTPUT,'fresh checker or axiom audit incomplete')
    for name,digest in zip(MODULES,SOURCE_SHA256):
        require(s.hash_file(OBS/LEAN/'sources/PeanoLab'/(name+'.lean'))['sha256']==digest,'Lean checker source changed')
    require(len(lean['checks'])==1 and lean['checks'][0]['independent_lean_checked'] is True,'same-data Lean acceptance missing')
    checked=lean['checks'][0]
    require(all(checked[k]==bound[k] for k in ('case','report_sha256','bundle_sha256','target_ast_sha256','nodes','root')),'Lean checked different data')
    require(len(lean['negative_controls'])==2 and all(r['rejected'] for r in lean['negative_controls']),'Lean negative control missing')
    phases=[lean['version_probe'],*(r['process'] for r in lean['compilation']),lean['axiom_audit'],checked['process'],
        *(r['process'] for r in lean['negative_controls'])]
    for index,p in enumerate(phases):
        ls.validate_process_record(p,command=tuple(p['command']),limits=ls.ProcessLimits(**p['limits']))
        require(read(OBS/LEAN/'processes'/f'{index:02d}.json')==p,'Lean process copy changed')
        require(successful(p) if index<len(phases)-2 else p['returncode']==1 and p['reason']=='exited','Lean process failed')
    expected={'scripts/test_sqrt2_power_log_root_half_argument.py':13,
        'scripts/test_sqrt2_power_fixed_half_log_root.py':13,'scripts/test_sqrt2_power_wave.py':14}
    require({r['file'] for r in report['regressions']}==expected.keys(),'missing regression batch')
    for row in report['regressions']:
        require(s.hash_file(ROOT/row['file'])==row['pin'] and str(expected[row['file']])+' passed' in row['process']['stdout']
            and ' skipped' not in row['process']['stdout'],'regression identity changed')
    require('peano_lab.library.theorems' not in sys.modules,'unexpected theorem catalogue import')
    return dict(status='passed',authority='metadata_consistency_not_new_proof_authority',case='AP093',job_id=JOB,
        ha=bound,Lean_report_sha256=s.hash_file(OBS/LEAN/'report.json')['sha256'],
        definition_count=16,minimal_actual_dependency_closure=True,constructors=4933,new_inductions=0,new_definition_ids=[],
        HA_generation_cpu=processes['generation']['resources']['cpu_seconds'],HA_replay_cpu=processes['fresh_replay']['resources']['cpu_seconds'],
        Lean_total_cpu=lean['measured_cpu_seconds'],Lean_total_wall=lean['elapsed_wall_seconds'],
        new_focused_tests=13,older_proof_regressions_rerun=13,controller_tests=14,migration_tests=19,
        total_additional_statements=210,total_distinct_checked_statements=243,focused_proof_regressions=1593,
        IR072_open=True,IR_parents_closed=0,library_admissions=0,publication_performed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=audit()
    if args.output:save_new(args.output,json.dumps(result,sort_keys=True,indent=2).encode()+b'\n')
    print(json.dumps(result,sort_keys=True))
