"""Bind AP095's WMI proof and tests to current sources; no proof generation."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

from audit_sqrt2_power_wmi_ap091 import ROOT,OBS,require,read,bind_current_case
from run_sqrt2_power_pilot import save_new,successful

RUN='wmi-ap095-full-v1'
JOB='284698'
SNAPSHOT='ad4ebd383f177ad1989942b3d643d9b86af632e8ab00a53c12c7589025c06d2e'
MANIFEST='e8878f638500147596d32e52ad8d94dec252da3d76c5ae2c1a1af44ecc3d2cee'
HA='shared-wave-requested-half-transport-v1'
LEAN='shared-wave-requested-half-transport-lean-wmi-v1'
BUNDLE='07d48fca1276244b05d415dc9c46a505b1fd357dc8178abea55a624e7347ff7e'
BODY_HASHES=('8a85f32a4f9dd943aba616ca3a33b534da82731b85563c5567f7a1ec7f64e24a',
    'ae587c19b63b2a1e4959ce160c69a6fb88a20e28f86785b94b8cfdd526f5cd79')


def audit():
    from sqrt2_power_automation_baseline import runtime
    from sqrt2_power_wmi_lean_runtime import lean_runtime
    from check_sqrt2_power_fresh_lean import exact_bundle,MODULES,SOURCE_SHA256,AUDIT_OUTPUT
    import run_sqrt2_power_wave as wave
    import sqrt2_power_requested_half_transport as proof
    s=runtime();ls=lean_runtime();folder=OBS/RUN
    c=read(folder/'collection.json');report=read(folder/'evidence/pilot-report.json')
    require(c['job_id']==report['job_id']==JOB and c['snapshot_sha256']==report['source_snapshot_sha256']==SNAPSHOT
        and c['downloaded_bytes_match'] is True and c['accounting'].startswith(JOB+'|COMPLETED|0:0|')
        and c['pilot_status']==report['status']=='HA_Lean_and_regressions_checked','run identity changed or incomplete')
    for name,pin in c['remote_artifact_manifest'].items():require(s.hash_file(folder/name)==pin,'downloaded artifact changed: '+name)
    require(report['snapshot_before']==report['snapshot_after'] and report['full_attempt_started'] is True,'input or attempt changed')
    require(s.hash_file(folder/'snapshot-manifest.json')['sha256']==MANIFEST,'snapshot manifest changed')
    manifest=read(folder/'snapshot-manifest.json')['files']
    for name in ('scripts/run_sqrt2_power_wmi_ap095.py','scripts/sqrt2_power_offline_wheels.py',
            'scripts/test_sqrt2_power_offline_wheels.py','scripts/sqrt2_power_wmi_resources.py',
            'scripts/submit_sqrt2_power_wmi_ap095.sh','slurm/peano_wmi_sqrt2_ap095.sbatch'):
        require(s.hash_file(ROOT/name)==manifest['source/'+name],'controller source changed: '+name)
    for label,p in report['processes'].items():
        s.validate_process_record(p,command=tuple(p['command']),limits=s.ProcessLimits(**p['limits']))
        require(successful(p) and read(folder/'evidence'/(label+'.json'))==p,'failed or changed process: '+label)
    require('Ran 19 tests' in report['processes']['migration-tests']['stderr']
        and 'Ran 8 tests' in report['processes']['offline-staging-tests']['stderr'],'infrastructure tests incomplete')
    staging=report['dependency_staging'];installer=report['processes']['offline-test-dependencies']
    require(staging['status']=='staged' and staging['files']==453 and staging['bytes']==5872264
        and staging['manifest_sha256']=='ce0debf75bda76a051731347fce4f3fc8460972553faad22e97fc79f9e35ab2f'
        and staging['network_calls']==staging['child_processes']==staging['installation_hooks_executed']==0
        and installer['observed_descendant_count']==0,'offline preparation changed')
    from verify_sqrt2_power_wmi_regressions import WHEELS
    require(staging['wheels']==WHEELS,'offline dependencies changed')
    for leaf in (HA,LEAN):
        for path in (OBS/leaf).rglob('*'):
            if path.is_file():require(s.hash_file(path)==s.hash_file(folder/'source'/path.relative_to(ROOT)),'canonical copy changed')
    raw,bound=exact_bundle(OBS/HA);ha=read(OBS/HA/'report.json');values={};processes={}
    require(bound['case']=='AP095' and bound['bundle_sha256']==BUNDLE and bound['target_ast_sha256']==proof.TARGET_SHA256
        and bound['nodes']==231 and bound['root']==230 and bound['bundle_bytes']==969777,'checked certificate identity changed')
    require(report['cost']['actual_bundle_sha256']==BUNDLE and report['cost']['original_native_curried_goals_checked'] is True,
        'native preflight did not agree with full proof')
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
    require(replay['kernel_calls']==replay['local_nodes']==231 and replay['proof_nodes']==21056,'full replay coverage changed')
    def signature(row,rows):
        return proof.canonical((row[0],row[1],[rows[d][1] for d in row[2]],row[3]))
    old_rows=[proof.read_mixed_archive(pin) for pin in proof.ARCHIVES]
    require(tree[3][:214]==old_rows[0],'actual AP094 dependency prefix changed')
    allowed={signature(row,rows) for rows in old_rows for row in rows}
    require(all(signature(row,tree[3]) in allowed for row in tree[3][:-2]),'changed inherited body or dependency')
    arithmetic=old_rows[1][301]
    require(sum(signature(row,tree[3])==signature(arithmetic,old_rows[1]) for row in tree[3])==1,
        'AP015 arithmetic was duplicated or replaced instead of replayed')
    reached=set();pending=[230]
    while pending:
        i=pending.pop()
        if i not in reached:reached.add(i);pending.extend(tree[3][i][2])
    require(reached==set(range(231)),'irrelevant or disconnected certificate node')
    require(tuple(proof.json_hash(row[3]) for row in tree[3][-2:])==BODY_HASHES,'new native proof bodies changed')
    require(all(all(type(d) is int and 0<=d<i for d in row[2]) for i,row in enumerate(tree[3])),'non-topological proof DAG')
    require(diagnostics['new_induction_count']==0 and diagnostics['new_definition_ids']==[] and diagnostics['new_axioms']==[]
        and diagnostics['helper_statement_ast_sha256']==proof.HELPER_TARGET_SHA256,'new assumptions or helper mismatch')
    registry=proof.definition_registry();seen=set();ids=set()
    for name,spec in registry.items():
        require(set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids,'definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    require(len(registry)==23,'definition count changed')
    old=OBS/'shared-wave-exp-log-root-half-transport-v1';bind_current_case(read(old/'report.json'),old)
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
    expected={'scripts/test_sqrt2_power_requested_half_transport.py':13,
        'scripts/test_sqrt2_power_exp_log_root_half_transport.py':13,
        'scripts/test_sqrt2_power_fixed_half_log_root.py':13,'scripts/test_sqrt2_power_wave.py':14}
    require({r['file'] for r in report['regressions']}==expected.keys(),'missing regression batch')
    for row in report['regressions']:
        require(s.hash_file(ROOT/row['file'])==row['pin']==manifest['source/'+row['file']]
            and str(expected[row['file']])+' passed' in row['process']['stdout'] and ' skipped' not in row['process']['stdout'],
            'regression identity changed')
    require('peano_lab.library.theorems' not in sys.modules,'unexpected theorem catalogue import')
    return dict(status='passed',authority='metadata_consistency_not_new_proof_authority',case='AP095',job_id=JOB,
        ha=bound,Lean_report_sha256=s.hash_file(OBS/LEAN/'report.json')['sha256'],
        definition_count=23,minimal_actual_dependency_closure=True,constructors=21056,new_inductions=0,new_definition_ids=[],
        AP094_prefix_preserved=True,AP015_arithmetic_body_reused_once=True,
        HA_generation_cpu=processes['generation']['resources']['cpu_seconds'],HA_replay_cpu=processes['fresh_replay']['resources']['cpu_seconds'],
        Lean_total_cpu=lean['measured_cpu_seconds'],Lean_total_wall=lean['elapsed_wall_seconds'],
        new_focused_tests=13,older_proof_regressions_rerun=26,controller_tests=14,migration_tests=19,offline_staging_tests=8,
        total_additional_statements=212,total_distinct_checked_statements=245,focused_proof_regressions=1619,
        IR072_open=True,IR_parents_closed=0,library_admissions=0,publication_performed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=audit()
    if args.output:save_new(args.output,json.dumps(result,sort_keys=True,indent=2).encode()+b'\n')
    print(json.dumps(result,sort_keys=True))
