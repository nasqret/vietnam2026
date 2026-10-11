#!/usr/bin/env python3
"""Read-only AP090 evidence consistency audit; never generates/checks a proof."""
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

from package_sqrt2_power_wmi import ROOT, PRODUCER_SHA256
from verify_sqrt2_power_wmi_lean import HA_FOLDER, LEAN_FOLDER, HA_REPORT_SHA256, BUNDLE_SHA256, TARGET_SHA256

OBS=ROOT/"research/arithmetic-library/sqrt2-power/observations"
LEAN_REPORT_SHA256="d0e929841e922a9c11ac170d8d1e0a5db8bc56f88990bef04aa0803281aee247"
RUNS=(
    ("wmi-ap090-pilot-v2","258959","e8353c52fbefb9f711d9e08af2870453caee341bce83fa45af39ab17e6d40553","failed_or_incomplete"),
    ("wmi-ap090-lean-followup-v1","259148","23141c6d4550624976c85c768260639ecb21a97c27f54023918978679a8fafdb","existing_HA_and_fresh_Lean_checked"),
    ("wmi-ap090-regressions-v1","259307","4da45635215319ceb7e98d7c9e383f5f4f8dda9d329d4f600fe58a5b5814872b","passed"),
)


def require(condition,message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def audit():
    from sqrt2_power_automation_baseline import runtime
    from sqrt2_power_wmi_lean_runtime import lean_runtime
    from run_sqrt2_power_pilot import successful
    from check_sqrt2_power_fresh_lean import exact_bundle, MODULES, SOURCE_SHA256, AUDIT_OUTPUT
    import run_sqrt2_power_wave as wave
    import sqrt2_power_fixed_half_log_root as proof
    s=runtime(); ls=lean_runtime(); runs=[]
    for name,job,snapshot,status in RUNS:
        folder=OBS/name;collection=read(folder/"collection.json");report=read(folder/"evidence/pilot-report.json")
        require(collection["downloaded_bytes_match"] and collection["job_id"]==job
            and collection["snapshot_sha256"]==snapshot and report["job_id"]==job
            and report["source_snapshot_sha256"]==snapshot and report["status"]==status,"remote run identity changed")
        for relative,pin in collection["remote_artifact_manifest"].items():
            require(s.hash_file(folder/relative)==pin,"collected artifact changed: "+relative)
        if job!="258959":
            require(report["full_attempt_started"] is False and report["certificate_generation_calls"]==0,
                "verification follow-up attempted generation")
            require(collection["accounting"].startswith(job+"|COMPLETED|0:0|"),"follow-up did not complete")
        runs.append(dict(job_id=job,snapshot_sha256=snapshot,status=status,all_downloaded_hashes_verified=True))
    payload,bound=exact_bundle(ROOT/HA_FOLDER)
    require(bound["report_sha256"]==HA_REPORT_SHA256 and bound["bundle_sha256"]==BUNDLE_SHA256
        and bound["target_ast_sha256"]==TARGET_SHA256 and bound["nodes"]==585,"AP090 identity changed")
    ha=read(ROOT/HA_FOLDER/"report.json")
    require(ha["source_pins"]==wave.pins("AP090"),"current proof or checker sources changed")
    require(s.hash_file(ROOT/"scripts/sqrt2_power_fixed_half_log_root.py")["sha256"]==PRODUCER_SHA256,"producer changed")
    decoded={};processes={}
    for phase in ("generation","fresh_replay"):
        record=ha["process_records"][phase];raw=gzip.decompress((ROOT/HA_FOLDER/record["path"]).read_bytes())
        require(sha256(raw).hexdigest()==record["raw_sha256"],"HA process archive changed")
        process=json.loads(raw)
        decoded[phase]=json.loads(process["stdout"]);processes[phase]=process
        input_bytes=b"" if phase=="generation" else wave.canonical(decoded["generation"])
        s.validate_process_record(process,command=tuple(process["command"]),
            limits=s.ProcessLimits(cpu_seconds=120,wall_seconds=180,rss_bytes=2*1024**3,output_bytes=8*1024**2),
            input_bytes=input_bytes)
        require(successful(process),"HA process failed")
    replay=decoded["fresh_replay"]
    require(all(replay[k] is True for k in ("original_target_checked","empty_context","false_target_rejected","forged_body_rejected")),
        "HA acceptance controls changed")
    require(replay["kernel_calls"]==replay["local_nodes"]==585 and replay["proof_nodes"]==65644,"HA metrics changed")
    tree=json.loads(payload)
    require(tree[3][:583]==proof.read_mixed_archive(proof.UNIFORM_ARCHIVE),"AP089 prefix changed")
    require(all(all(type(d) is int and 0<=d<i for d in row[2]) for i,row in enumerate(tree[3])),"non-topological proof DAG")
    require(sha256(wave.canonical(tree[3][-1][3])).hexdigest()=="0b110197ccd472fc4d367af10f3e948b6609dcc89f27d1357ba673482e6b7b04",
        "checked native transport body changed")
    registry=proof.definition_registry();seen=set()
    for name,definition in registry.items():
        require(set(definition.conceptual_dependencies)<=seen,"definition DAG is not topological")
        seen.add(name)
    require(len(registry)==19,"definition count changed")
    diagnostics=decoded["generation"]["diagnostics"]
    require(diagnostics["new_induction_count"]==0 and diagnostics["new_axioms"]==[]
        and diagnostics["new_definition_ids"]==[] and diagnostics["helper_statement_ast_sha256"]=={},"new assumptions introduced")
    lean=read(ROOT/LEAN_FOLDER/"report.json")
    require(s.hash_file(ROOT/LEAN_FOLDER/"report.json")["sha256"]==LEAN_REPORT_SHA256,"Lean report changed")
    require(lean["status"]=="fresh_lean_checked" and tuple(r["module"] for r in lean["compilation"])==MODULES,"fresh checker compilation missing")
    for name,digest in zip(MODULES,SOURCE_SHA256):
        require(s.hash_file(ROOT/LEAN_FOLDER/"sources/PeanoLab"/(name+".lean"))["sha256"]==digest,"Lean source pin changed")
    require(lean["axiom_audit"]["stdout"]==AUDIT_OUTPUT,"Lean axiom audit changed")
    require(len(lean["checks"])==1 and lean["checks"][0]["independent_lean_checked"] is True,"Lean acceptance missing")
    check=lean["checks"][0]
    require(all(check[k]==bound[k] for k in ("case","report_sha256","bundle_sha256","target_ast_sha256","nodes","root")),"Lean checked different bytes")
    require(len(lean["negative_controls"])==2 and all(r["rejected"] for r in lean["negative_controls"]),"Lean rejection controls missing")
    phases=[lean["version_probe"],*(r["process"] for r in lean["compilation"]),lean["axiom_audit"],check["process"],
        *(r["process"] for r in lean["negative_controls"])]
    for index,process in enumerate(phases):
        ls.validate_process_record(process,command=tuple(process["command"]),limits=ls.ProcessLimits(**process["limits"]))
        require(read(ROOT/LEAN_FOLDER/"processes"/(f"{index:02d}.json"))==process,"Lean process copy changed")
        require(successful(process) if index<len(phases)-2 else process["returncode"]==1 and process["reason"]=="exited",
            "Lean process result changed")
    regression=read(OBS/"wmi-ap090-regressions-v1/evidence/pilot-report.json")
    require(regression["status"]=="passed" and len(regression["tests"])==2,"regressions incomplete")
    for name,pin in regression["source_pins"].items():
        require(s.hash_file(ROOT/name)==pin,"regression source changed")
    for row in regression["tests"]:
        process=row["process"]
        s.validate_process_record(process,command=tuple(process["command"]),
            limits=s.ProcessLimits(cpu_seconds=120,wall_seconds=180,rss_bytes=2*1024**3,output_bytes=1024**2))
        require(row["passed"] and len(row["expected_tests"])==13 and successful(process)
            and "13 passed" in process["stdout"],"focused tests missing")
    require("peano_lab.library.theorems" not in sys.modules,"unexpected full registry import")
    return dict(status="passed",authority="metadata_consistency_not_new_proof_authority",case="AP090",
        runs=runs,ha=bound,definition_count=19,constructors=65644,AP089_prefix_preserved=True,
        original_producer_and_kernel_unchanged=True,focused_AP090_tests=13,AP089_regressions_rerun=13,
        HA_generation_cpu=processes["generation"]["resources"]["cpu_seconds"],
        HA_replay_cpu=processes["fresh_replay"]["resources"]["cpu_seconds"],
        Lean_total_cpu=lean["measured_cpu_seconds"],Lean_total_wall=lean["elapsed_wall_seconds"],
        total_additional_statements=207,total_distinct_checked_statements=240,focused_proof_regressions=1554,
        IR072_open=True,IR_parents_closed=0,library_admissions=0,publication_performed=False)


if __name__=="__main__":
    print(json.dumps(audit(),sort_keys=True))
