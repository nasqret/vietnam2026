"""Bounded local completion of AP094's fourteen controller tests only.

Its WMI proof and all proof regressions already passed. The cluster snapshot
omitted the RF001 historical controller fixture; authenticate the existing
local fixture against AP093's accepted snapshot, without a new proof attempt.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

from run_sqrt2_power_pilot import ROOT,save_new,successful

OBS='research/arithmetic-library/sqrt2-power/observations/'
TEST='scripts/test_sqrt2_power_wave.py'
FIXTURE=OBS+'shared-wave-rf001-v1/generation-process.json.gz'
TEST_MANIFEST=OBS+'wmi-ap094-full-v1/snapshot-manifest.json'
FIXTURE_MANIFEST=OBS+'wmi-ap093-full-v1/snapshot-manifest.json'
TEST_MANIFEST_SHA256='cde5d41aaa70ca0eecbd708d6189aedddc336bc274b73a2cf2d590d6213d1d28'
FIXTURE_MANIFEST_SHA256='0615edb9f36aac2849f2d00f5cdb4b72ff8ef67adf0562dc5bc8bcae77457cc3'


def verify(output,wheels,dependencies):
    from sqrt2_power_automation_baseline import runtime
    from sqrt2_power_offline_wheels import collect,WHEELS
    import run_sqrt2_power_wave as wave
    if output.exists() or output.is_symlink():raise ValueError('fresh controller observation required')
    s=runtime();pins={}
    for manifest,digest,target in ((TEST_MANIFEST,TEST_MANIFEST_SHA256,TEST),(FIXTURE_MANIFEST,FIXTURE_MANIFEST_SHA256,FIXTURE)):
        raw=(ROOT/manifest).read_bytes()
        if sha256(raw).hexdigest()!=digest:raise ValueError('authenticated source manifest changed')
        expected=json.loads(raw)['files']['source/'+target]
        if s.hash_file(ROOT/target)!=expected:raise ValueError('test or historical fixture changed')
        pins[target]=expected
    before=wave.pins('AP094')
    if before!=json.loads((ROOT/OBS/'shared-wave-exp-log-root-half-transport-v1/report.json').read_bytes())['source_pins']:
        raise ValueError('original AP094 proof/checker source changed')
    files=collect(wheels,WHEELS)
    def verify_dependencies():
        for name,raw in files.items():
            path=dependencies/name
            if path.is_symlink() or path.read_bytes()!=raw:raise ValueError('staged test dependency differs from pinned wheel')
    verify_dependencies()
    os.environ['PYTHONPATH']=os.pathsep.join((str(dependencies),str(ROOT/'scripts'),str(ROOT/'peano-lab/py')))
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
    command=(sys.executable,'-B','-m','pytest','-q','-x','--tb=short','--disable-warnings','-p','no:cacheprovider',TEST)
    limits=s.ProcessLimits(cpu_seconds=20,wall_seconds=30,rss_bytes=768*1024**2,output_bytes=1024**2)
    process=s.run_bounded(command,cwd=ROOT,limits=limits)
    s.validate_process_record(process,command=command,limits=limits)
    verify_dependencies()
    stable=before==wave.pins('AP094') and all(s.hash_file(ROOT/name)==pin for name,pin in pins.items())
    passed=stable and successful(process) and '14 passed' in process['stdout'] and ' skipped' not in process['stdout']
    report=dict(schema='sqrt2-power-AP094-controller-v1',case='AP094',status='passed' if passed else 'failed_or_incomplete',
        expected_tests=14,process=process,source_pins=pins,proof_and_checker_source_pins=before,
        source_manifests={TEST_MANIFEST:TEST_MANIFEST_SHA256,FIXTURE_MANIFEST:FIXTURE_MANIFEST_SHA256},
        source_pins_unchanged=stable,wheels=WHEELS,certificate_generation_calls=0,Lean_rebuild_calls=0,
        original_failed_jobs_preserved=['284694','284696'],IR_parents_closed=0,library_admissions=0,
        authority='controller_regression_evidence_not_new_proof_authority')
    save_new(output,json.dumps(report,sort_keys=True,indent=2).encode()+b'\n')
    print(json.dumps(dict(status=report['status'],reason=process['reason'],stdout=process['stdout'],resources=process['resources'])))
    return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--wheels',required=True,type=Path)
    parser.add_argument('--dependencies',required=True,type=Path);args=parser.parse_args()
    raise SystemExit(0 if verify(args.output,args.wheels.resolve(),args.dependencies.resolve()) else 1)
