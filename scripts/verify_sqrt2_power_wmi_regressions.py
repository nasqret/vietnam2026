#!/usr/bin/env python3
"""AP089/AP090 regressions on completed certificates, offline job-local pytest."""
import argparse
import ast
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
import time

from package_sqrt2_power_wmi import ROOT, verify_snapshot
from verify_sqrt2_power_wmi_lean import HA_FOLDER, HA_REPORT_SHA256
import sqrt2_power_wmi_resources as resources

FILES=("scripts/test_sqrt2_power_half_log_root_uniform.py","scripts/test_sqrt2_power_fixed_half_log_root.py")
EXTRA_FILES=("conftest.py","pytest.ini","scripts/constructive_historical_graph_test_support.py",
    "research/arithmetic-library/sqrt2-power/observations/half-log-root-uniform-solvers-v1.json",
    "research/arithmetic-library/sqrt2-power/observations/half-log-root-uniform-preconstruction-source-v1.py.gz",
    "research/arithmetic-library/sqrt2-power/observations/fixed-log-exp-convergence-solvers-v1.json")
WHEELS={
    "pytest-8.4.2-py3-none-any.whl":"872f880de3fc3a5bdc88a11b39c9710c3497a547cfa9320bc3c5e62fbf272e79",
    "iniconfig-2.3.0-py3-none-any.whl":"f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12",
    "packaging-24.0-py3-none-any.whl":"2ddfb553fdf02fb784c234c7ba6ccc288296ceabec964ad2eae3777778130bc5",
    "pluggy-1.6.0-py3-none-any.whl":"e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746",
    "pygments-2.17.2-py3-none-any.whl":"b27c2826c47d0f3219f29554824c30c5e8945175d888647acd804ddd04af846c",
}


def verify(stage,evidence):
    from run_sqrt2_power_pilot import save_new, successful, controller_deadline
    from sqrt2_power_automation_baseline import runtime
    resources.require_allocation()
    if evidence.exists() or evidence.is_symlink():
        raise ValueError("new regression evidence directory required")
    evidence.mkdir()
    report=dict(schema="sqrt2-power-wmi-regressions-v1",case="AP090",status="not_checked",
        job_id=os.environ["SLURM_JOB_ID"],source_snapshot_sha256=os.environ["PEANO_SQRT2_SNAPSHOT_SHA256"],
        host=platform.node(),python=sys.version,authority="regression_observation_not_library_admission",
        IR_parents_closed=0,library_admissions=0,full_attempt_started=False,certificate_generation_calls=0,
        max_workers=1,predecessor_job_id="259148",requested=dict(resources.REQUESTED),
        tests=[],source_pins={},wheels=WHEELS,controller_wall_seconds=540)
    start=time.monotonic();supervisor=runtime()
    def run(command,label,cpu,wall):
        limits=supervisor.ProcessLimits(cpu_seconds=cpu,wall_seconds=wall,rss_bytes=resources.WORKER_RSS_BYTES,output_bytes=1024**2)
        process=supervisor.run_bounded(command,cwd=ROOT,limits=limits)
        supervisor.validate_process_record(process,command=command,limits=limits)
        save_new(evidence/(label+".json"),json.dumps(process,sort_keys=True,indent=2).encode()+b"\n")
        return process
    try:
        with controller_deadline(start+540):
            report["snapshot_before"]=verify_snapshot(stage)
            if sha256((ROOT/HA_FOLDER/"report.json").read_bytes()).hexdigest()!=HA_REPORT_SHA256:
                raise ValueError("completed HA input changed")
            wheels=[]
            for name,digest in WHEELS.items():
                path=ROOT/"wmi-test-wheels"/name
                if sha256(path.read_bytes()).hexdigest()!=digest:
                    raise ValueError("offline wheel changed")
                wheels.append(str(path))
            dependencies=Path(os.environ["TMPDIR"])/"pytest-dependencies"
            if dependencies.exists():
                raise ValueError("fresh job-local dependency destination required")
            command=(sys.executable,"-B","-m","pip","install","--disable-pip-version-check",
                "--no-index","--no-deps","--no-compile","--target",str(dependencies),*wheels)
            install=run(command,"offline-test-dependencies",60,90)
            report["dependency_installation"]=install
            if not successful(install):
                raise ValueError("offline dependency installation failed")
            os.environ["PYTHONPATH"]=os.pathsep.join((str(dependencies),str(ROOT/"scripts"),str(ROOT/"peano-lab/py")))
            os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
            for name in (*FILES,*EXTRA_FILES):
                report["source_pins"][name]=supervisor.hash_file(ROOT/name)
            for index,name in enumerate(FILES):
                tree=ast.parse((ROOT/name).read_bytes())
                expected=[n.name for n in tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")]
                if len(expected)!=13:
                    raise ValueError("focused regression inventory changed")
                command=(sys.executable,"-B","-m","pytest","-q","-x","--tb=short","--disable-warnings",
                    "-p","no:cacheprovider",name)
                process=run(command,"proof-regressions-"+str(index),120,180)
                passed=successful(process) and "13 passed" in process["stdout"] and " skipped" not in process["stdout"]
                report["tests"].append(dict(file=name,expected_tests=expected,passed=passed,process=process))
                if not passed:
                    raise ValueError("focused regression batch failed: "+name)
            report["status"]="passed"
    except BaseException as error:
        report["status"]="failed_or_incomplete"
        report["exception"]=dict(type=type(error).__name__,message=str(error)[:2000])
    finally:
        try:
            report["snapshot_after"]=verify_snapshot(stage)
            if report.get("snapshot_before")!=report["snapshot_after"]:
                raise ValueError("regression input snapshot changed")
        except BaseException as error:
            report["status"]="failed_or_incomplete"
            report["snapshot_exception"]=dict(type=type(error).__name__,message=str(error)[:2000])
        report["elapsed_wall_seconds"]=time.monotonic()-start
        save_new(evidence/"pilot-report.json",json.dumps(report,sort_keys=True,indent=2).encode()+b"\n")
    print(json.dumps({k:report[k] for k in ("case","status","job_id","full_attempt_started","elapsed_wall_seconds")}),flush=True)
    return report["status"]=="passed"


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",type=Path,required=True)
    parser.add_argument("--evidence",type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(0 if verify(args.stage.resolve(),args.evidence.resolve()) else 1)
