"""One AP094 regression-only follow-up on the already HA/Lean-checked bytes.

Replace only the failed pip preparation with authenticated pure-wheel staging.
No certificate generation or Lean rebuild. Preserve the original failed job.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

from package_sqrt2_power_wmi import ROOT,verify_snapshot
from run_sqrt2_power_pilot import save_new,successful,controller_deadline
import sqrt2_power_wmi_resources as resources

OBS='research/arithmetic-library/sqrt2-power/observations/'
HA=OBS+'shared-wave-exp-log-root-half-transport-v1'
LEAN=OBS+'shared-wave-exp-log-root-half-transport-lean-wmi-v1'
HA_SHA256='d3a7c127b6ac9f241009ab6faefeff6c80ba0342c01fbbf26582f9e8dfcc4864'
LEAN_SHA256='91c0c82efa1f01eb37d46049d239fe20937aff9edc42833b3a6e84e6d5983c9d'
ORIGINAL_MANIFEST=OBS+'wmi-ap094-full-v1/snapshot-manifest.json'
ORIGINAL_MANIFEST_SHA256='cde5d41aaa70ca0eecbd708d6189aedddc336bc274b73a2cf2d590d6213d1d28'
FILES={'scripts/test_sqrt2_power_exp_log_root_half_transport.py':13,
    'scripts/test_sqrt2_power_log_root_half_argument.py':13,
    'scripts/test_sqrt2_power_fixed_half_log_root.py':13,'scripts/test_sqrt2_power_wave.py':14}


def verify(stage,evidence):
    from sqrt2_power_automation_baseline import runtime
    from check_sqrt2_power_fresh_lean import exact_bundle
    resources.require_allocation()
    if evidence.exists() or evidence.is_symlink():raise ValueError('fresh regression evidence directory required')
    evidence.mkdir();s=runtime();started=time.monotonic()
    report=dict(schema='sqrt2-power-wmi-AP094-tests-v1',case='AP094',status='not_checked',
        job_id=os.environ['SLURM_JOB_ID'],source_snapshot_sha256=os.environ['PEANO_SQRT2_SNAPSHOT_SHA256'],
        predecessor_job_id='284694',full_attempt_started=False,certificate_generation_calls=0,Lean_rebuild_calls=0,
        requested=dict(resources.REQUESTED,partition=os.environ['SLURM_JOB_PARTITION']),processes={},regressions=[],
        authority='regression_observation_not_library_admission',IR_parents_closed=0,library_admissions=0)
    def run(command,label,cpu=120,wall=180):
        limits=s.ProcessLimits(cpu_seconds=cpu,wall_seconds=wall,rss_bytes=resources.WORKER_RSS_BYTES,output_bytes=1024**2)
        p=s.run_bounded(tuple(command),cwd=ROOT,limits=limits)
        s.validate_process_record(p,command=tuple(command),limits=limits)
        save_new(evidence/(label+'.json'),json.dumps(p,sort_keys=True,indent=2).encode()+b'\n')
        report['processes'][label]=p
        if not successful(p):raise ValueError('failed regression-only phase: '+label)
        return p
    try:
        with controller_deadline(started+900):
            report['snapshot_before']=verify_snapshot(stage)
            for folder,digest in ((HA,HA_SHA256),(LEAN,LEAN_SHA256)):
                if s.hash_file(ROOT/folder/'report.json')['sha256']!=digest:raise ValueError('completed proof receipt changed')
            raw=(ROOT/ORIGINAL_MANIFEST).read_bytes()
            if sha256(raw).hexdigest()!=ORIGINAL_MANIFEST_SHA256:raise ValueError('original test source manifest changed')
            original=json.loads(raw)['files']
            for name in FILES:
                if s.hash_file(ROOT/name)!=original['source/'+name]:raise ValueError('original proof regression source changed')
            _,report['already_checked_certificate']=exact_bundle(ROOT/HA)
            if report['already_checked_certificate']['bundle_sha256']!='b234e8883d2975dd2cb5ab32133703fb623196946051fffc74181f9e8a7d3f6c':
                raise ValueError('follow-up certificate changed')
            report['HA_report_sha256']=HA_SHA256;report['Lean_report_sha256']=LEAN_SHA256
            run((sys.executable,'-B','-m','unittest','discover','-s','scripts','-p','test_sqrt2_power_offline_wheels.py','-v'),
                'offline-staging-tests',25,35)
            run((sys.executable,'-B','-m','unittest','discover','-s','scripts','-p','test_sqrt2_power_wmi.py','-v'),
                'migration-tests',25,35)
            dependencies=Path(os.environ['TMPDIR'])/'pytest-dependencies'
            process=run((sys.executable,'-B','scripts/sqrt2_power_offline_wheels.py','--wheels',str(ROOT/'wmi-test-wheels'),
                '--output',str(dependencies)),'offline-test-dependencies',60,90)
            report['dependency_staging']=json.loads(process['stdout'])
            if report['dependency_staging']['status']!='staged':raise ValueError('pure-wheel preparation incomplete')
            os.environ['PYTHONPATH']=os.pathsep.join((str(dependencies),str(ROOT/'scripts'),str(ROOT/'peano-lab/py')))
            os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
            for name,count in FILES.items():
                command=(sys.executable,'-B','-m','pytest','-q','-x','--tb=short','--disable-warnings','-p','no:cacheprovider',name)
                process=run(command,Path(name).stem)
                if str(count)+' passed' not in process['stdout'] or ' skipped' in process['stdout']:
                    raise ValueError('regression inventory incomplete')
                report['regressions'].append(dict(file=name,pin=s.hash_file(ROOT/name),process=process))
            report['status']='regressions_checked'
    except BaseException as error:
        report['status']='failed_or_incomplete';report['exception']=dict(type=type(error).__name__,message=str(error)[:2000])
    finally:
        try:
            report['snapshot_after']=verify_snapshot(stage)
            if report.get('snapshot_before')!=report['snapshot_after']:raise ValueError('test snapshot changed')
        except BaseException as error:
            report['status']='failed_or_incomplete';report['snapshot_exception']=str(error)[:2000]
        report['elapsed_wall_seconds']=time.monotonic()-started
        save_new(evidence/'pilot-report.json',json.dumps(report,sort_keys=True,indent=2).encode()+b'\n')
    print(json.dumps({key:report[key] for key in ('case','status','job_id','full_attempt_started','elapsed_wall_seconds')}),flush=True)
    return report['status']=='regressions_checked'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',required=True,type=Path);parser.add_argument('--evidence',required=True,type=Path)
    args=parser.parse_args();raise SystemExit(0 if verify(args.stage.resolve(),args.evidence.resolve()) else 1)
