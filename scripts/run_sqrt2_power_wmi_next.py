#!/usr/bin/env python3
"""AP091 WMI preparation and full verification, with no automatic retries."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
import time

from package_sqrt2_power_wmi import ROOT, verify_snapshot
import sqrt2_power_wmi_resources as resources

OBS="research/arithmetic-library/sqrt2-power/observations/"
HA_FOLDER=OBS+"shared-wave-fixed-half-log-root-witness-v1"
LEAN_FOLDER=OBS+"shared-wave-fixed-half-log-root-witness-lean-wmi-v1"
PREPARATION_JOB='268994'
PREPARATION_SNAPSHOT='5d3a7f7ab86e1fb9a9b37eb1281556463b914028d35ca9d432e34c900b5f0642'
PREPARATION_ROOT=Path('/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots')/PREPARATION_SNAPSHOT
PREPARATION_COST_FIELDS=('case','target_ast_sha256','definition_count','definition_names','source_pin_count',
    'endpoints','new_body','actual_retained_nodes','actual_retained_constructors','actual_canonical_bytes',
    'actual_bundle_sha256','new_induction_count','new_definition_ids','IR_parents_closed')


def preparation_cost(report):
    """The queue dependency is not evidence: require the exact successful preflight."""
    cost=report.get('cost',{})
    if (report.get('schema')!='sqrt2-power-wmi-AP091-v1' or report.get('case')!='AP091'
            or report.get('phase')!='prepare' or report.get('job_id')!=PREPARATION_JOB
            or report.get('source_snapshot_sha256')!=PREPARATION_SNAPSHOT
            or report.get('status')!='prepared_not_theorem_checked'
            or report.get('full_attempt_started') is not False
            or cost.get('status')!='prepared' or cost.get('original_native_curried_goal_checked') is not True
            or cost.get('full_dependency_closed_theorem_checked') is not False
            or not set(PREPARATION_COST_FIELDS)<=cost.keys()):
        raise ValueError('exact successful AP091 native preflight required before any full attempt')
    return {key:cost[key] for key in PREPARATION_COST_FIELDS}


def read_preparation(supervisor):
    from run_sqrt2_power_pilot import successful
    path=PREPARATION_ROOT/'evidence/pilot-report.json'
    raw=path.read_bytes();report=json.loads(raw);cost=preparation_cost(report)
    process=report['processes']['native-and-cost-preflight']
    supervisor.validate_process_record(process,command=tuple(process['command']),
        limits=supervisor.ProcessLimits(cpu_seconds=60,wall_seconds=90,
            rss_bytes=resources.WORKER_RSS_BYTES,output_bytes=1024**2))
    if not successful(process) or json.loads(process['stdout'])!=report['cost']:
        raise ValueError('native preparation process did not succeed on its recorded exact target')
    return dict(job_id=PREPARATION_JOB,snapshot_sha256=PREPARATION_SNAPSHOT,
        report_sha256=sha256(raw).hexdigest(),cost=cost)


def inspect(*,check_native=True):
    import sqrt2_power_fixed_half_log_root_witness as p
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from sqrt2_power_quadratic_trace_exists import _inert_metrics
    from peano_lab.library.proof_bundle import encode_formula,encode_proof
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp,Bot
    registry=p.definition_registry();target=parse_named(p.NAMED_SOURCE,registry=registry)
    rows=p.read_mixed_archive(p.FIXED_ARCHIVE);endpoints={}
    for name,source in p.ENDPOINT_SOURCES.items():
        formula=encode_formula(parse_named(source,registry=registry))
        matches=[i for i,row in enumerate(rows) if row[1]==formula]
        if len(matches)!=1:
            raise ValueError("missing or ambiguous AP090 archive endpoint: "+name+" "+str(matches))
        endpoints[name]=matches[0]
    body=p.introduce(p.Scope(),(),p.HELPER_DEPENDENCIES['AP091'],p._root)
    goal=target
    for name in reversed(p.HELPER_DEPENDENCIES['AP091']):
        goal=Imp(parse_named(p.ENDPOINT_SOURCES[name],registry=registry),goal)
    if check_native and (not check((),body,goal) or check((),body,Bot())):
        raise ValueError("new closed native witness body failed")
    limits=BinaryDAGLimits();count,depth=_body_metrics(body,limits)
    _row_preflight(target,body,limits)
    rows.append([8*count+16,encode_formula(target),[endpoints[d] for d in p.HELPER_DEPENDENCIES['AP091']],encode_proof(body)])
    total=sum(_inert_metrics(row[3],limits)[0] for row in rows)
    payload=p.canonical(['peano-lab-bundle-v1',len(rows)-1,encode_formula(target),rows])+b'\n'
    if len(rows)>limits.max_nodes or total>limits.max_total_body_nodes or len(payload)>limits.max_payload_bytes:
        raise ValueError("original certificate bounds exceeded")
    if 'peano_lab.library.theorems' in sys.modules:
        raise ValueError("unexpected full catalogue import")
    return dict(status='prepared' if check_native else 'metadata_only',case='AP091',target_ast_sha256=p.json_hash(encode_formula(target)),
        producer_source_pin=dict(bytes=(ROOT/'scripts/sqrt2_power_fixed_half_log_root_witness.py').stat().st_size,
            sha256=sha256((ROOT/'scripts/sqrt2_power_fixed_half_log_root_witness.py').read_bytes()).hexdigest()),
        definition_count=len(registry),definition_names=list(registry),source_pin_count=len(p.fixed_half_log_root_witness_source_pins()),
        endpoints=endpoints,new_body=dict(constructors=count,depth=depth,sha256=p.json_hash(encode_proof(body))),
        actual_retained_nodes=len(rows),actual_retained_constructors=total,actual_canonical_bytes=len(payload),
        actual_bundle_sha256=sha256(payload).hexdigest(),original_native_curried_goal_checked=check_native,
        full_dependency_closed_theorem_checked=False,new_induction_count=0,new_definition_ids=[],IR_parents_closed=0)


def execute(stage,evidence,phase):
    from run_sqrt2_power_pilot import save_new,successful
    from sqrt2_power_automation_baseline import runtime
    from run_sqrt2_power_wmi import run_wmi_wave,LEAN
    import check_sqrt2_power_fresh_lean as fresh
    import sqrt2_power_fixed_half_log_root_witness as p
    resources.require_allocation()
    if phase not in ('prepare','full') or evidence.exists():
        raise ValueError("new explicit campaign observation required")
    evidence.mkdir();supervisor=runtime();started=time.monotonic()
    report=dict(schema='sqrt2-power-wmi-AP091-v1',case='AP091',phase=phase,status='not_checked',
        job_id=os.environ['SLURM_JOB_ID'],source_snapshot_sha256=os.environ['PEANO_SQRT2_SNAPSHOT_SHA256'],
        host=platform.node(),python=sys.version,full_attempt_started=False,IR_parents_closed=0,library_admissions=0,
        authority='research_observation_not_library_admission',requested=dict(resources.REQUESTED),processes={})
    if phase=='prepare':report['requested']['wall_seconds']=300
    report['requested']['partition']=os.environ['SLURM_JOB_PARTITION']
    def run(command,label,cpu=120,wall=180):
        limits=supervisor.ProcessLimits(cpu_seconds=cpu,wall_seconds=wall,rss_bytes=resources.WORKER_RSS_BYTES,output_bytes=1024**2)
        process=supervisor.run_bounded(tuple(command),cwd=ROOT,limits=limits)
        supervisor.validate_process_record(process,command=tuple(command),limits=limits)
        save_new(evidence/(label+'.json'),json.dumps(process,sort_keys=True,indent=2).encode()+b'\n')
        report['processes'][label]=process
        if not successful(process):
            raise ValueError('failed bounded phase: '+label)
        return process
    try:
        report['snapshot_before']=verify_snapshot(stage)
        if phase=='full':report['preparation']=read_preparation(supervisor)
        process=run((sys.executable,'-B',str(Path(__file__).resolve()),'--inspect'),'native-and-cost-preflight',60,90)
        cost=json.loads(process['stdout']);report['cost']=cost
        if phase=='prepare':
            report['status']='prepared_not_theorem_checked'
        else:
            if cost['target_ast_sha256']!=p.TARGET_SHA256:
                raise ValueError('AP091 target is not independently frozen')
            if {key:cost[key] for key in PREPARATION_COST_FIELDS}!=report['preparation']['cost']:
                raise ValueError('frozen full attempt differs from the successful preparation')
            run((sys.executable,'-B','-m','unittest','discover','-s','scripts','-p','test_sqrt2_power_wmi.py','-v'),'migration-tests',25,35)
            run((sys.executable,'-B','-m','unittest','discover','-s','scripts','-p','test_sqrt2_power_wmi_campaign.py','-v'),'campaign-routing-tests',25,35)
            report['full_attempt_started']=True
            save_new(evidence/'AP091-attempt-started.json',json.dumps(dict(job_id=report['job_id'],case='AP091')).encode()+b'\n')
            report['ha']=run_wmi_wave(ROOT/HA_FOLDER,case='AP091')
            if report['ha']['status']!='fresh_ordinary_HA_checked':
                raise ValueError('complete HA generation/replay failed')
            _,bound=fresh.exact_bundle(ROOT/HA_FOLDER)
            if bound['bundle_sha256']!=cost['actual_bundle_sha256']:
                raise ValueError('full proof bytes differ from preflight DAG')
            report['lean']=fresh.execute(ROOT/LEAN_FOLDER,[ROOT/HA_FOLDER],lean=LEAN,lean_repo=stage/'lean',resource_profile=resources.NAME)
            if report['lean']['status']!='fresh_lean_checked':
                raise ValueError('independent fresh Lean failed')
            from verify_sqrt2_power_wmi_regressions import WHEELS
            wheels=[]
            for name,digest in WHEELS.items():
                path=ROOT/'wmi-test-wheels'/name
                if sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('changed offline wheel')
                wheels.append(str(path))
            dependencies=Path(os.environ['TMPDIR'])/'pytest-dependencies'
            if dependencies.exists():raise ValueError('fresh dependency directory required')
            run((sys.executable,'-B','-m','pip','install','--disable-pip-version-check','--no-index','--no-deps',
                '--no-compile','--target',str(dependencies),*wheels),'offline-test-dependencies',60,90)
            os.environ['PYTHONPATH']=os.pathsep.join((str(dependencies),str(ROOT/'scripts'),str(ROOT/'peano-lab/py')))
            os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
            report['regressions']=[]
            for name in ('test_sqrt2_power_fixed_half_log_root_witness.py','test_sqrt2_power_fixed_half_log_root.py',
                    'test_sqrt2_power_half_log_root_uniform.py','test_sqrt2_power_wave.py'):
                command=(sys.executable,'-B','-m','pytest','-q','-x','--tb=short','--disable-warnings','-p','no:cacheprovider','scripts/'+name)
                result=run(command,name.removesuffix('.py'))
                report['regressions'].append(dict(file='scripts/'+name,pin=supervisor.hash_file(ROOT/'scripts'/name),process=result))
            report['status']='HA_Lean_and_regressions_checked'
    except BaseException as error:
        report['status']='failed_or_incomplete'
        report['exception']=dict(type=type(error).__name__,message=str(error)[:2000])
    finally:
        try:
            report['snapshot_after']=verify_snapshot(stage)
            if report.get('snapshot_before')!=report['snapshot_after']:raise ValueError('snapshot changed during execution')
        except BaseException as error:
            report['status']='failed_or_incomplete';report['snapshot_exception']=dict(type=type(error).__name__,message=str(error)[:2000])
        report['elapsed_wall_seconds']=time.monotonic()-started
        save_new(evidence/'pilot-report.json',json.dumps(report,sort_keys=True,indent=2).encode()+b'\n')
    print(json.dumps({k:report[k] for k in ('case','status','phase','job_id','full_attempt_started','elapsed_wall_seconds')}),flush=True)
    return report['status'] in ('prepared_not_theorem_checked','HA_Lean_and_regressions_checked')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--metadata-only',action='store_true')
    parser.add_argument('--stage',type=Path)
    parser.add_argument('--evidence',type=Path)
    parser.add_argument('--phase',choices=('prepare','full'))
    args=parser.parse_args()
    if args.inspect or args.metadata_only:print(json.dumps(inspect(check_native=not args.metadata_only),sort_keys=True))
    else:raise SystemExit(0 if execute(args.stage.resolve(),args.evidence.resolve(),args.phase) else 1)
