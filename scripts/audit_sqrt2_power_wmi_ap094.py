"""Audit AP094's collected HA/Lean/test evidence; never generate a proof."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

from audit_sqrt2_power_wmi_ap091 import ROOT,OBS,require,read,bind_current_case
from run_sqrt2_power_pilot import save_new,successful

RUN='wmi-ap094-full-v1'
JOB='284694'
SNAPSHOT='8661c34d98d55bfd2239a9c03a9eb7ec6f77f83b9256296d4d5ecca8584bd532'
TEST_RUN='wmi-ap094-tests-v1'
TEST_JOB='284696'
TEST_SNAPSHOT='edefdd8629a58fdf140b660647cbd7bb95dbdb5284ba5c1416d7d03111ca7610'
HA='shared-wave-exp-log-root-half-transport-v1'
LEAN='shared-wave-exp-log-root-half-transport-lean-wmi-v1'
BUNDLE='b234e8883d2975dd2cb5ab32133703fb623196946051fffc74181f9e8a7d3f6c'
BODY_HASHES=('9c88aed964cd522c22b61c66474d3f6bd34bb7bd67427314f30e87b71da854fa',
    'e27202e9d8fc4f65da859ba644d5cd23c2f0e0b06bf0fd7cfc89cf450cec04b3',
    'ccb2a44f1c6b5f621ceae6e3ee062c5cd7a31179574e7d35e6bb491ece40b43e')


def audit():
    from sqrt2_power_automation_baseline import runtime
    from sqrt2_power_wmi_lean_runtime import lean_runtime
    from check_sqrt2_power_fresh_lean import exact_bundle,MODULES,SOURCE_SHA256,AUDIT_OUTPUT
    import run_sqrt2_power_wave as wave
    import sqrt2_power_exp_log_root_half_transport as proof
    s=runtime();ls=lean_runtime();folder=OBS/RUN
    c=read(folder/'collection.json');report=read(folder/'evidence/pilot-report.json')
    require(c['job_id']==report['job_id']==JOB and c['snapshot_sha256']==report['source_snapshot_sha256']==SNAPSHOT
        and c['downloaded_bytes_match'] is True and c['accounting'].startswith(JOB+'|FAILED|1:0|')
        and c['pilot_status']==report['status']=='failed_or_incomplete','original failed run identity changed')
    require(report['exception']['message']=='failed bounded phase: offline-test-dependencies'
        and report['ha']['status']=='fresh_ordinary_HA_checked' and report['lean']['status']=='fresh_lean_checked'
        and report['regressions']==[],'original failure was not confined to test preparation')
    for name,pin in c['remote_artifact_manifest'].items():require(s.hash_file(folder/name)==pin,'downloaded artifact changed: '+name)
    require(report['snapshot_before']==report['snapshot_after'] and report['full_attempt_started'] is True,'input or attempt changed')
    for label,p in report['processes'].items():
        s.validate_process_record(p,command=tuple(p['command']),limits=s.ProcessLimits(**p['limits']))
        require(read(folder/'evidence'/(label+'.json'))==p,'changed original process: '+label)
        if label=='offline-test-dependencies':
            require(p['reason']=='unexpected_descendant' and p['returncode']==-9 and p['observed_descendant_count']==1,
                'original guarded installer failure changed')
        else:require(successful(p),'failed proof preflight: '+label)
    test_folder=OBS/TEST_RUN;tc=read(test_folder/'collection.json');tests=read(test_folder/'evidence/pilot-report.json')
    require(tc['job_id']==tests['job_id']==TEST_JOB and tc['snapshot_sha256']==tests['source_snapshot_sha256']==TEST_SNAPSHOT
        and tc['downloaded_bytes_match'] is True and tc['accounting'].startswith(TEST_JOB+'|FAILED|1:0|')
        and tc['pilot_status']==tests['status']=='failed_or_incomplete','original regression run identity changed')
    require(tests['exception']['message']=='failed regression-only phase: test_sqrt2_power_wave',
        'follow-up had a different failure')
    for name,pin in tc['remote_artifact_manifest'].items():require(s.hash_file(test_folder/name)==pin,'changed follow-up artifact: '+name)
    require(tests['predecessor_job_id']==JOB and tests['full_attempt_started'] is False
        and tests['certificate_generation_calls']==tests['Lean_rebuild_calls']==0
        and tests['snapshot_before']==tests['snapshot_after'],'follow-up repeated proofs or changed inputs')
    for label,p in tests['processes'].items():
        s.validate_process_record(p,command=tuple(p['command']),limits=s.ProcessLimits(**p['limits']))
        require(read(test_folder/'evidence'/(label+'.json'))==p,'changed follow-up process: '+label)
        if label=='test_sqrt2_power_wave':
            require(p['reason']=='exited' and p['returncode']==1 and 'FileNotFoundError' in p['stdout']
                and 'shared-wave-rf001-v1/generation-process.json.gz' in p['stdout'],'controller failure was not the omitted fixture')
        else:require(successful(p),'failed proof regression or staging process: '+label)
    staging=tests['dependency_staging'];installer=tests['processes']['offline-test-dependencies']
    require(staging['status']=='staged' and staging['files']==453 and staging['bytes']==5872264
        and staging['manifest_sha256']=='ce0debf75bda76a051731347fce4f3fc8460972553faad22e97fc79f9e35ab2f'
        and staging['network_calls']==staging['child_processes']==staging['installation_hooks_executed']==0
        and installer['observed_descendant_count']==0 and 'scripts/sqrt2_power_offline_wheels.py' in installer['command'],
        'dependency preparation did not use the exact child-free pure-wheel strategy')
    from verify_sqrt2_power_wmi_regressions import WHEELS
    require(staging['wheels']==WHEELS,'offline dependencies changed')
    follow_manifest=read(test_folder/'snapshot-manifest.json')['files']
    for name in ('scripts/sqrt2_power_offline_wheels.py','scripts/test_sqrt2_power_offline_wheels.py',
            'scripts/verify_sqrt2_power_wmi_ap094_tests.py','scripts/sqrt2_power_wmi_resources.py'):
        require(s.hash_file(ROOT/name)==follow_manifest['source/'+name],'follow-up controller source changed: '+name)
    require('Ran 8 tests' in tests['processes']['offline-staging-tests']['stderr']
        and 'Ran 19 tests' in tests['processes']['migration-tests']['stderr'],'infrastructure regression count changed')
    for leaf in (HA,LEAN):
        for path in (OBS/leaf).rglob('*'):
            if path.is_file():
                pin=s.hash_file(path)
                require(pin==s.hash_file(folder/'source'/path.relative_to(ROOT))
                    and pin==s.hash_file(test_folder/'source'/path.relative_to(ROOT)),'canonical certificate or follow-up copy changed')
    raw,bound=exact_bundle(OBS/HA);ha=read(OBS/HA/'report.json');values={};processes={}
    require(bound['case']=='AP094' and bound['bundle_sha256']==BUNDLE and bound['target_ast_sha256']==proof.TARGET_SHA256
        and bound['nodes']==214 and bound['root']==213 and bound['bundle_bytes']==817481,'checked certificate identity changed')
    bind_current_case(ha,OBS/HA)
    require(tests['already_checked_certificate']==bound and tests['HA_report_sha256']==s.hash_file(OBS/HA/'report.json')['sha256']
        and tests['Lean_report_sha256']==s.hash_file(OBS/LEAN/'report.json')['sha256'],'regressions used different proof evidence')
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
    require(replay['kernel_calls']==replay['local_nodes']==214 and replay['proof_nodes']==18440,'full replay coverage changed')
    def signature(row,rows):
        return proof.canonical((row[0],row[1],[rows[d][1] for d in row[2]],row[3]))
    old_rows=[proof.read_mixed_archive(pin) for pin in proof.ARCHIVES]
    allowed={signature(row,rows) for rows in old_rows for row in rows}
    require(all(signature(row,tree[3]) in allowed for row in tree[3][:-3]),'changed inherited body or dependency')
    reached=set();pending=[213]
    while pending:
        i=pending.pop()
        if i not in reached:reached.add(i);pending.extend(tree[3][i][2])
    require(reached==set(range(214)),'irrelevant or disconnected certificate node')
    require(tuple(proof.json_hash(row[3]) for row in tree[3][-3:])==BODY_HASHES,'new native proof bodies changed')
    require(all(all(type(d) is int and 0<=d<i for d in row[2]) for i,row in enumerate(tree[3])),'non-topological proof DAG')
    require(diagnostics['new_induction_count']==0 and diagnostics['new_definition_ids']==[] and diagnostics['new_axioms']==[]
        and diagnostics['helper_statement_ast_sha256']==proof.HELPER_TARGET_SHA256,'new assumptions or helper mismatch')
    registry=proof.definition_registry();seen=set();ids=set()
    for name,spec in registry.items():
        require(set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids,'definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    require(len(registry)==23,'definition count changed')
    old=OBS/'shared-wave-log-root-half-argument-v1';bind_current_case(read(old/'report.json'),old)
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
    expected={'scripts/test_sqrt2_power_exp_log_root_half_transport.py':13,
        'scripts/test_sqrt2_power_log_root_half_argument.py':13,
        'scripts/test_sqrt2_power_fixed_half_log_root.py':13}
    original_manifest=read(folder/'snapshot-manifest.json')['files']
    require({r['file'] for r in tests['regressions']}==expected.keys(),'missing regression batch')
    for row in tests['regressions']:
        require(s.hash_file(ROOT/row['file'])==row['pin'] and str(expected[row['file']])+' passed' in row['process']['stdout']
            and ' skipped' not in row['process']['stdout'],'regression identity changed')
        require(row['pin']==original_manifest['source/'+row['file']]==follow_manifest['source/'+row['file']],
            'follow-up altered an original proof test')
    controller=read(OBS/'exp-log-root-half-transport-controller-v1.json');p=controller['process']
    require(controller['status']=='passed' and controller['expected_tests']==14
        and controller['certificate_generation_calls']==controller['Lean_rebuild_calls']==0
        and controller['source_pins_unchanged'] is True
        and controller['proof_and_checker_source_pins']==ha['source_pins'],'local controller evidence differs')
    limits=s.ProcessLimits(cpu_seconds=20,wall_seconds=30,rss_bytes=768*1024**2,output_bytes=1024**2)
    s.validate_process_record(p,command=tuple(p['command']),limits=limits)
    require(successful(p) and '14 passed' in p['stdout'] and ' skipped' not in p['stdout'],
        'controller checks did not pass under the original local cap')
    require(controller['source_pins']['scripts/test_sqrt2_power_wave.py']==original_manifest['source/scripts/test_sqrt2_power_wave.py']
        ==follow_manifest['source/scripts/test_sqrt2_power_wave.py'],'controller tests changed after failure')
    for name,pin in controller['source_pins'].items():require(s.hash_file(ROOT/name)==pin,'changed controller input')
    for name,digest in controller['source_manifests'].items():require(s.hash_file(ROOT/name)['sha256']==digest,'changed source manifest')
    fixture='research/arithmetic-library/sqrt2-power/observations/shared-wave-rf001-v1/generation-process.json.gz'
    prior=read(OBS/'wmi-ap093-full-v1/snapshot-manifest.json')['files']
    require(controller['source_pins'][fixture]==prior['source/'+fixture] and 'source/'+fixture not in follow_manifest,
        'missing fixture diagnosis or exact historical fixture binding changed')
    require('peano_lab.library.theorems' not in sys.modules,'unexpected theorem catalogue import')
    return dict(status='passed',authority='metadata_consistency_not_new_proof_authority',case='AP094',
        proof_job_id=JOB,regression_job_id=TEST_JOB,original_installer_failure_preserved=True,
        original_missing_fixture_failure_preserved=True,controller_checks_completed_locally=True,
        followup_certificate_generation_calls=0,followup_Lean_rebuild_calls=0,
        ha=bound,Lean_report_sha256=s.hash_file(OBS/LEAN/'report.json')['sha256'],
        definition_count=23,minimal_actual_dependency_closure=True,constructors=18440,new_inductions=0,new_definition_ids=[],
        HA_generation_cpu=processes['generation']['resources']['cpu_seconds'],HA_replay_cpu=processes['fresh_replay']['resources']['cpu_seconds'],
        Lean_total_cpu=lean['measured_cpu_seconds'],Lean_total_wall=lean['elapsed_wall_seconds'],
        new_focused_tests=13,older_proof_regressions_rerun=26,controller_tests=14,migration_tests=19,offline_staging_tests=8,
        total_additional_statements=211,total_distinct_checked_statements=244,focused_proof_regressions=1606,
        IR072_open=True,IR_parents_closed=0,library_admissions=0,publication_performed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=audit()
    if args.output:save_new(args.output,json.dumps(result,sort_keys=True,indent=2).encode()+b'\n')
    print(json.dumps(result,sort_keys=True))
