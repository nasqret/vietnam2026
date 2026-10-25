"""One scheduled portable export, one fit and one admission; never retry."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
APP = ROOT/"hydra-playground"
PYTHON = APP/".runtime/venv/bin/python3"
DATA = ROOT/"output/hydra-implementation-2026-09-04/decisions-v2-01"
OLD = ROOT/"output/hydra-implementation-2026-09-04/decisions-v1-02"
OLD_SHA = "6ffc5d54678bbe43cdbf7178b4fd6d8493f661ba437526d36d4278111ad8f930"
SPEC = "hydra-playground/training-v5/configs/decision-inputs-v1.json"
SPEC_SHA = "f21200dadbfae992a1fbb4095d724864ee1fefeae7104920aa2275fef14b6c07"
CONFIG = "hydra-playground/training-v5/configs/qwen3_4b_decisions_v2_pilot.toml"


def pin(path):
    raw = path.read_bytes()
    return {"path":str(path.relative_to(ROOT)),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}


def save(name,value):
    with (HERE/name).open("x") as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False);stream.write("\n")


def run(name,module,args,cpu,wall):
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu))
        resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024*1024,8*1024*1024))
    code = ("import sys;sys.path[:0]="+repr([str(APP),str(APP/"training-v5")])+
            ";from "+module+" import main;raise SystemExit(main())")
    command=[str(PYTHON),"-I","-B","-c",code,*args]
    started=time.monotonic();reason=None;peak=0;samples=0;monitor_error=None
    with (HERE/(name+".stdout")).open("xb") as out,(HERE/(name+".stderr")).open("xb") as err:
        child=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=err,start_new_session=True,preexec_fn=limits)
        try:
            while child.poll() is None:
                reading=subprocess.run(["/bin/ps","-o","rss=","-p",str(child.pid)],
                    capture_output=True,text=True,timeout=2)
                if reading.stdout.strip().isdigit():
                    samples+=1;peak=max(peak,int(reading.stdout.strip())*1024)
                elif child.poll() is None:
                    raise RuntimeError("The owned child RSS sample is unavailable.")
                if peak > 2*1024**3:reason="sampled_rss_2gib"
                if time.monotonic()-started > wall:reason="wall_limit"
                if reason:
                    if child.poll() is None:os.killpg(child.pid,signal.SIGKILL)
                    break
                time.sleep(0.1)
            child.wait(timeout=10)
        except BaseException as error:
            monitor_error={"type":type(error).__name__,"message":str(error)[:500]};reason="monitor_error"
        finally:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
    record={"command":command,"child_pid":child.pid,"actual_child_exit_code":child.returncode,
        "elapsed_seconds":time.monotonic()-started,"peak_sampled_rss_bytes":peak,"rss_samples":samples,
        "cpu_limit_seconds":cpu,"wall_limit_seconds":wall,"sampled_rss_stop_bytes":2*1024**3,
        "stop_reason":reason,"monitor_error":monitor_error,"quiescent":child.poll() is not None,
        "cleanup_scope":"owned direct child reaped; these data modules do not spawn children",
        "stdout":pin(HERE/(name+".stdout")),"stderr":pin(HERE/(name+".stderr")),"automatic_retry":False}
    save(name+".json",record)
    print(json.dumps({"stage":name,**{key:record[key] for key in (
        "actual_child_exit_code","elapsed_seconds","peak_sampled_rss_bytes","rss_samples","stop_reason")}}),flush=True)
    return record


def passed(record):
    return record is not None and record["actual_child_exit_code"]==0 and record["stop_reason"] is None


def main():
    tracked=[APP/"export_decisions.py",APP/"branch_ranker.py",APP/"certificate_codec.py",ROOT/SPEC,
        APP/"training-v5/BASELINE.json",ROOT/CONFIG,Path(__file__),
        *[APP/"training-v5/hydra_training_v5"/name for name in ("decision_data.py","decision_pilot.py","pilot_config.py")]]
    before=[pin(path) for path in tracked];save("source-pins-before.json",before)
    save("plan.json",{"schema":"hydra-p5-portable-data-gate-v2","input_spec":SPEC,"input_sha256":SPEC_SHA,
        "source_pins":before,"revision_reason":"Confirmed platform libm differences; explicit portable v2 encoding and retained admission mismatch evidence",
        "max_export_calls":1,"max_fit_calls":1,"max_admission_calls":1,
        "native_proof_checks":0,"native_parsing_for_exclusions":True,"model_calls":0,"gpu_allocations":0,
        "old_dataset_manifest_sha256":OLD_SHA,"automatic_retry":False})
    export=fit=admission=None;comparison=None;failure=None
    try:
        export=run("export","export_decisions",["--inputs",SPEC,"--inputs-sha256",SPEC_SHA,
            "--output",str(DATA)],90,120)
        if passed(export):
            assert pin(OLD/"manifest.json")["sha256"]==OLD_SHA,"Historical manifest changed."
            old=json.loads((OLD/"manifest.json").read_bytes());new=json.loads((DATA/"manifest.json").read_bytes())
            stable=[name for name in old["files"] if not name.startswith("ranker-")]
            for name in stable:
                assert old["files"][name]==new["files"][name],"Non-ranking bytes changed: "+name
                for directory in (OLD,DATA):
                    actual=pin(directory/name)
                    assert actual["sha256"]==old["files"][name]["sha256"] and actual["bytes"]==old["files"][name]["bytes"]
            for key in ("counts_before_dedupe","counts_after_dedupe","primitive_coverage","groups"):
                assert old[key]==new[key],"Selection or family split changed: "+key
            comparison={"schema":"hydra-portable-primitive-preservation-v1","passed":True,
                "old_manifest":pin(OLD/"manifest.json"),"new_manifest":pin(DATA/"manifest.json"),
                "byte_identical_files":stable,"primitive_byte_content_unchanged":True,
                "changed_file_pins":[name for name in old["files"] if old["files"][name]!=new["files"][name]],
                "selection_and_family_split_unchanged":True}
            save("primitive-preservation.json",comparison)
            fit=run("fit","branch_ranker",["--data",str(DATA/"ranker-train.jsonl"),
                "--data-sha256",new["files"]["ranker-train.jsonl"]["sha256"],"--output",
                str(ROOT/"output/hydra-implementation-2026-09-04/ranker-v2-01.json")],30,45)
            if passed(fit):
                admission=run("admission","hydra_training_v5.decision_pilot",["--config",CONFIG,
                    "--dataset-manifest",str(DATA/"manifest.json"),"--dataset-sha256",pin(DATA/"manifest.json")["sha256"],
                    "--output",str(HERE/"pilot-plan-4b.json"),"--failure-output",str(HERE/"admission-failure")],90,120)
    except BaseException as error:
        failure={"type":type(error).__name__,"message":str(error)[:1000]}
    after=[pin(path) for path in tracked];save("source-pins-after.json",after)
    ok=all(passed(item) for item in (export,fit,admission)) and comparison is not None and before==after and failure is None
    save("result.json",{"schema":"hydra-p5-portable-data-gate-result-v2","status":"complete" if ok else "failed",
        "export":export,"fit":fit,"admission":admission,"primitive_preservation":comparison,"error":failure,
        "source_pins_unchanged":before==after,"native_proof_checks":0,"model_calls":0,"gpu_allocations":0,
        "automatic_retry":False,"gpu_training_performed":False})
    print(json.dumps({"status":"complete" if ok else "failed","sources_unchanged":before==after,"error":failure}),flush=True)
    return 0 if ok else 1


if __name__=="__main__":raise SystemExit(main())
