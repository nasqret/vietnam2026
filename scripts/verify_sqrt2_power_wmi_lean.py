#!/usr/bin/env python3
"""Fresh Lean verification of job 258959's completed HA bytes; no generation."""
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

HA_FOLDER = "research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-v1"
LEAN_FOLDER = "research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-lean-wmi-v2"
HA_REPORT_SHA256 = "d97afbf151e451450e0551b8d49e8c0e0f6ac074c43c42d44b716d6f685ebf86"
BUNDLE_SHA256 = "603a7c00633d251a1f6b4476247eb6e48a8d13d47b47b4dbf75b5eab5747ef8c"
TARGET_SHA256 = "41651cb7c7afc07ceb0eaeab7bf02392001a704ec0891d7bf1db0ed4aa33211f"


def verify(stage, evidence):
    from run_sqrt2_power_pilot import save_new, successful
    from sqrt2_power_automation_baseline import runtime
    from sqrt2_power_wmi_lean_guard import LEAN_EXECUTABLE
    import check_sqrt2_power_fresh_lean as fresh
    resources.require_allocation()
    if evidence.exists() or evidence.is_symlink():
        raise ValueError("new evidence directory required")
    evidence.mkdir()
    report = dict(schema="sqrt2-power-wmi-lean-followup-v1", case="AP090", status="not_checked",
        job_id=os.environ["SLURM_JOB_ID"], host=platform.node(), python=sys.version,
        source_snapshot_sha256=os.environ["PEANO_SQRT2_SNAPSHOT_SHA256"],
        authority="remote_verification_not_library_admission", IR_parents_closed=0,
        library_admissions=0, full_attempt_started=False, certificate_generation_calls=0,
        predecessor_job_id="258959", requested=dict(resources.REQUESTED),
        resource_profile=resources.NAME, node_local_scratch=True, source_root=str(ROOT))
    started=time.monotonic()
    try:
        report["snapshot_before"]=verify_snapshot(stage)
        if sha256((ROOT/HA_FOLDER/"report.json").read_bytes()).hexdigest()!=HA_REPORT_SHA256:
            raise ValueError("not the completed job 258959 HA observation")
        tests=(sys.executable,"-B","-m","unittest","discover","-s","scripts","-p","test_sqrt2_power_wmi.py","-v")
        limits=runtime().ProcessLimits(cpu_seconds=25,wall_seconds=35,rss_bytes=512*1024**2,output_bytes=1024**2)
        process=runtime().run_bounded(tests,cwd=ROOT,limits=limits)
        runtime().validate_process_record(process,command=tests,limits=limits)
        report["migration_tests"]=process
        if not successful(process):
            raise ValueError("migration tests failed before Lean verification")
        _, bound=fresh.exact_bundle(ROOT/HA_FOLDER)
        if (bound["report_sha256"]!=HA_REPORT_SHA256 or bound["bundle_sha256"]!=BUNDLE_SHA256
                or bound["target_ast_sha256"]!=TARGET_SHA256 or bound["nodes"]!=585):
            raise ValueError("completed AP090 certificate identity changed")
        report["existing_ha"]=bound
        report["lean"]=fresh.execute(ROOT/LEAN_FOLDER,[ROOT/HA_FOLDER],lean=Path(LEAN_EXECUTABLE),
            lean_repo=stage/"lean",resource_profile=resources.NAME)
        if report["lean"]["status"]!="fresh_lean_checked":
            raise ValueError("fresh independent Lean verification failed")
        report["status"]="existing_HA_and_fresh_Lean_checked"
    except BaseException as error:
        report["status"]="failed_or_incomplete"
        report["exception"]=dict(type=type(error).__name__,message=str(error)[:2000])
    finally:
        try:
            report["snapshot_after"]=verify_snapshot(stage)
            if report.get("snapshot_before")!=report["snapshot_after"]:
                raise ValueError("verification input snapshot changed")
        except BaseException as error:
            report["status"]="failed_or_incomplete"
            report["snapshot_exception"]=dict(type=type(error).__name__,message=str(error)[:2000])
        report["elapsed_wall_seconds"]=time.monotonic()-started
        save_new(evidence/"pilot-report.json",json.dumps(report,sort_keys=True,indent=2).encode()+b"\n")
    print(json.dumps({k:report[k] for k in ("case","status","job_id","full_attempt_started","elapsed_wall_seconds")}),flush=True)
    return report["status"]=="existing_HA_and_fresh_Lean_checked"


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",type=Path,required=True)
    parser.add_argument("--evidence",type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(0 if verify(args.stage.resolve(),args.evidence.resolve()) else 1)
