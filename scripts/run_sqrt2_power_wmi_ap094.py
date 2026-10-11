"""AP094: one bounded WMI construction, replay, fresh Lean and regressions."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

from package_sqrt2_power_wmi import ROOT,verify_snapshot
from run_sqrt2_power_pilot import save_new,successful
import sqrt2_power_wmi_resources as resources

OBS='research/arithmetic-library/sqrt2-power/observations/'
HA_FOLDER=OBS+'shared-wave-exp-log-root-half-transport-v1'
LEAN_FOLDER=OBS+'shared-wave-exp-log-root-half-transport-lean-wmi-v1'


def inspect(*,check_native=True):
    import sqrt2_power_exp_log_root_half_transport as p
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from sqrt2_power_quadratic_trace_exists import _inert_metrics
    from peano_lab.library.proof_bundle import encode_formula,encode_proof
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp,Bot
    registry=p.definition_registry();target=p.frozen_exp_log_root_half_transport_target()
    formulas={name:parse_named(source,registry=registry) for name,source in p.ENDPOINT_SOURCES.items()}
    formulas.update({name:parse_named(source,registry=registry) for name,source in p.HELPER_SOURCES.items()})
    if {name:p.json_hash(encode_formula(formulas[name])) for name in p.HELPER_SOURCES}!=p.HELPER_TARGET_SHA256:
        raise ValueError('frozen arithmetic target changed')
    formulas['AP094']=target;rows=[];keys={};endpoints={};owners={};limits=BinaryDAGLimits()
    for pin in p.ARCHIVES:
        original=p.read_mixed_archive(pin);remap={}
        for i,row in enumerate(original):
            linked=[row[0],row[1],[remap[d] for d in row[2]],row[3]];key=p.canonical(linked)
            if key not in keys:keys[key]=len(rows);rows.append(linked)
            remap[i]=keys[key]
        for name in p.ENDPOINT_SOURCES:
            if p.ENDPOINT_OWNERS[name]!=pin['case']:continue
            matches=[i for i,row in enumerate(original) if row[1]==encode_formula(formulas[name])]
            if len(matches)!=1:raise ValueError('ambiguous actual endpoint: '+name+str(matches))
            endpoints[name]=remap[matches[0]];owners[name]=dict(case=pin['case'],node=matches[0])
    bodies={};factories=p.factories(registry)
    for name,deps in p.HELPER_DEPENDENCIES.items():
        body=p.introduce(p.Scope(),(),deps,factories[name]);goal=formulas[name]
        for dep in reversed(deps):goal=Imp(formulas[dep],goal)
        if check_native and (not check((),body,goal) or check((),body,Bot())):
            raise ValueError('native curried proof failed: '+name)
        count,depth=_body_metrics(body,limits);_row_preflight(formulas[name],body,limits)
        endpoints[name]=len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in deps],encode_proof(body)])
        bodies[name]=dict(constructors=count,depth=depth,sha256=p.json_hash(encode_proof(body)))
    reached=set();pending=[len(rows)-1]
    while pending:
        i=pending.pop()
        if i not in reached:reached.add(i);pending.extend(rows[i][2])
    keep=sorted(reached);remap={old:new for new,old in enumerate(keep)}
    rows=[[rows[i][0],rows[i][1],[remap[d] for d in rows[i][2]],rows[i][3]] for i in keep]
    total=sum(_inert_metrics(row[3],limits)[0] for row in rows)
    payload=p.canonical(['peano-lab-bundle-v1',len(rows)-1,encode_formula(target),rows])+b'\n'
    if len(rows)>limits.max_nodes or total>limits.max_total_body_nodes or len(payload)>limits.max_payload_bytes:
        raise ValueError('original certificate bounds exceeded')
    if 'peano_lab.library.theorems' in sys.modules:raise ValueError('unexpected full catalogue import')
    return dict(status='native_prepared' if check_native else 'metadata_only',case='AP094',target_ast_sha256=p.TARGET_SHA256,
        helper_ast_sha256=p.HELPER_TARGET_SHA256,definition_count=len(registry),endpoints=owners,new_bodies=bodies,
        actual_retained_nodes=len(rows),actual_retained_constructors=total,actual_canonical_bytes=len(payload),
        actual_bundle_sha256=sha256(payload).hexdigest(),source_pin_count=len(p.exp_log_root_half_transport_source_pins()),
        original_native_curried_goals_checked=check_native,full_dependency_closed_theorem_checked=False,
        new_induction_count=0,new_definition_ids=[],IR_parents_closed=0)


def execute(stage,evidence):
    from sqrt2_power_automation_baseline import runtime
    from run_sqrt2_power_wmi import run_wmi_wave,LEAN
    import check_sqrt2_power_fresh_lean as fresh
    from verify_sqrt2_power_wmi_regressions import WHEELS
    resources.require_allocation()
    if evidence.exists():raise ValueError('new observation required')
    evidence.mkdir();s=runtime();started=time.monotonic()
    report=dict(schema='sqrt2-power-wmi-AP094-v1',case='AP094',status='not_checked',job_id=os.environ['SLURM_JOB_ID'],
        source_snapshot_sha256=os.environ['PEANO_SQRT2_SNAPSHOT_SHA256'],full_attempt_started=False,
        requested=dict(resources.REQUESTED,partition=os.environ['SLURM_JOB_PARTITION']),processes={},regressions=[],
        authority='research_observation_not_library_admission',IR_parents_closed=0,library_admissions=0)
    def run(command,label,cpu=120,wall=180):
        limits=s.ProcessLimits(cpu_seconds=cpu,wall_seconds=wall,rss_bytes=resources.WORKER_RSS_BYTES,output_bytes=1024**2)
        process=s.run_bounded(tuple(command),cwd=ROOT,limits=limits)
        s.validate_process_record(process,command=tuple(command),limits=limits)
        save_new(evidence/(label+'.json'),json.dumps(process,sort_keys=True,indent=2).encode()+b'\n')
        report['processes'][label]=process
        if not successful(process):raise ValueError('failed bounded phase: '+label)
        return process
    try:
        report['snapshot_before']=verify_snapshot(stage)
        process=run((sys.executable,'-B',str(Path(__file__).resolve()),'--inspect'),'native-and-cost-preflight',60,90)
        report['cost']=json.loads(process['stdout'])
        run((sys.executable,'-B','-m','unittest','discover','-s','scripts','-p','test_sqrt2_power_wmi.py','-v'),'migration-tests',25,35)
        report['full_attempt_started']=True
        save_new(evidence/'AP094-attempt-started.json',json.dumps(dict(job_id=report['job_id'],case='AP094')).encode()+b'\n')
        report['ha']=run_wmi_wave(ROOT/HA_FOLDER,case='AP094')
        if report['ha']['status']!='fresh_ordinary_HA_checked':raise ValueError('full HA check failed')
        _,bound=fresh.exact_bundle(ROOT/HA_FOLDER)
        if bound['bundle_sha256']!=report['cost']['actual_bundle_sha256']:raise ValueError('preflight differs from actual certificate')
        report['lean']=fresh.execute(ROOT/LEAN_FOLDER,[ROOT/HA_FOLDER],lean=LEAN,lean_repo=stage/'lean',resource_profile=resources.NAME)
        if report['lean']['status']!='fresh_lean_checked':raise ValueError('fresh Lean failed')
        dependencies=Path(os.environ['TMPDIR'])/'pytest-dependencies';wheels=[]
        if dependencies.exists():raise ValueError('new dependency directory required')
        for name,digest in WHEELS.items():
            path=ROOT/'wmi-test-wheels'/name
            if sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('changed offline dependency')
            wheels.append(str(path))
        run((sys.executable,'-B','-m','pip','install','--disable-pip-version-check','--no-index','--no-deps','--no-compile',
            '--target',str(dependencies),*wheels),'offline-test-dependencies',60,90)
        os.environ['PYTHONPATH']=os.pathsep.join((str(dependencies),str(ROOT/'scripts'),str(ROOT/'peano-lab/py')))
        os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
        for name in ('test_sqrt2_power_exp_log_root_half_transport.py','test_sqrt2_power_log_root_half_argument.py','test_sqrt2_power_fixed_half_log_root.py','test_sqrt2_power_wave.py'):
            command=(sys.executable,'-B','-m','pytest','-q','-x','--tb=short','--disable-warnings','-p','no:cacheprovider','scripts/'+name)
            result=run(command,name.removesuffix('.py'))
            report['regressions'].append(dict(file='scripts/'+name,pin=s.hash_file(ROOT/'scripts'/name),process=result))
        report['status']='HA_Lean_and_regressions_checked'
    except BaseException as error:
        report['status']='failed_or_incomplete';report['exception']=dict(type=type(error).__name__,message=str(error)[:2000])
    finally:
        try:
            report['snapshot_after']=verify_snapshot(stage)
            if report.get('snapshot_before')!=report['snapshot_after']:raise ValueError('snapshot changed')
        except BaseException as error:
            report['status']='failed_or_incomplete';report['snapshot_exception']=str(error)[:2000]
        report['elapsed_wall_seconds']=time.monotonic()-started
        save_new(evidence/'pilot-report.json',json.dumps(report,sort_keys=True,indent=2).encode()+b'\n')
    print(json.dumps({key:report[key] for key in ('case','status','job_id','full_attempt_started','elapsed_wall_seconds')}),flush=True)
    return report['status']=='HA_Lean_and_regressions_checked'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--metadata-only',action='store_true');parser.add_argument('--stage',type=Path);parser.add_argument('--evidence',type=Path)
    args=parser.parse_args()
    if args.inspect or args.metadata_only:print(json.dumps(inspect(check_native=not args.metadata_only),sort_keys=True))
    else:raise SystemExit(0 if execute(args.stage.resolve(),args.evidence.resolve()) else 1)
