"""One scheduled data export, then at most one ranker fit; no retries."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PYTHON = ROOT/"hydra-playground/.runtime/venv/bin/python3"
APP = ROOT/"hydra-playground"
DATA = ROOT/"output/hydra-implementation-2026-09-04/decisions-v1-02"
SPEC = "hydra-playground/training-v5/configs/decision-inputs-v1.json"
SPEC_SHA = "f21200dadbfae992a1fbb4095d724864ee1fefeae7104920aa2275fef14b6c07"


def pin(path):
    raw = path.read_bytes()
    return {"path":str(path.relative_to(ROOT)),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}


def save(name,value):
    with (HERE/name).open("x") as stream:json.dump(value,stream,sort_keys=True,indent=2);stream.write("\n")


def run(name,module,args,cpu,wall):
    stdout,stderr = HERE/(name+".stdout"),HERE/(name+".stderr")
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu))
        resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024*1024,8*1024*1024))
    code = "import sys;sys.path.insert(0,"+repr(str(APP))+");from "+module+" import main;raise SystemExit(main())"
    command = [str(PYTHON),"-I","-B","-c",code,*args]
    started = time.monotonic();reason=None;peak=0;samples=0;monitor_error=None
    with stdout.open("xb") as out,stderr.open("xb") as err:
        child = subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=err,start_new_session=True,preexec_fn=limits)
        try:
            while child.poll() is None:
                reading = subprocess.run(["/bin/ps","-o","rss=","-p",str(child.pid)],
                    capture_output=True,text=True,timeout=2)
                if reading.stdout.strip().isdigit():
                    samples += 1;peak=max(peak,int(reading.stdout.strip())*1024)
                if peak > 2*1024**3:reason="sampled_rss_2gib"
                if time.monotonic()-started > wall:reason="wall_limit"
                if reason:
                    os.killpg(child.pid,signal.SIGKILL);break
                time.sleep(0.1)
            exit_code=child.wait(timeout=10)
        except BaseException as error:
            monitor_error={"type":type(error).__name__,"message":str(error)[:500]}
            reason="monitor_error"
        finally:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
            exit_code=child.returncode
    record={"command":command,"child_pid":child.pid,"actual_child_exit_code":exit_code,
        "elapsed_seconds":time.monotonic()-started,"peak_sampled_rss_bytes":peak,"rss_samples":samples,
        "cpu_limit_seconds":cpu,"wall_limit_seconds":wall,"sampled_rss_stop_bytes":2*1024**3,
        "stop_reason":reason,"monitor_error":monitor_error,"quiescent":child.poll() is not None,"stdout":pin(stdout),"stderr":pin(stderr),
        "automatic_retry":False}
    save(name+".json",record);print(json.dumps({"stage":name,**record}),flush=True)
    return record


def main():
    tracked=[APP/"export_decisions.py",APP/"branch_ranker.py",ROOT/SPEC,APP/"training-v5/BASELINE.json",Path(__file__)]
    before=[pin(path)for path in tracked];save("source-pins-before.json",before)
    save("plan.json",{"schema":"hydra-p5-data-gate-v1","input_spec":SPEC,"input_sha256":SPEC_SHA,
        "source_pins":before,"revised_from":"p5-data-gate-01", "revision_reason":"sandbox denied RSS process inspection; authorized owned watcher now runs with reviewed escalation; resource caps and exporter/ranker unchanged", "max_export_calls":1,"max_fit_calls":1,"native_proof_checks":0,
        "native_parsing_for_exclusions":True,"model_calls":0,"gpu_allocations":0})
    export=run("export","export_decisions",["--inputs",SPEC,"--inputs-sha256",SPEC_SHA,
        "--output",str(DATA)],90,120)
    fit=None
    if export["actual_child_exit_code"] == 0 and export["stop_reason"] is None:
        manifest=json.loads((DATA/"manifest.json").read_bytes())
        data_sha=manifest["files"]["ranker-train.jsonl"]["sha256"]
        fit=run("fit","branch_ranker",["--data",str(DATA/"ranker-train.jsonl"),"--data-sha256",data_sha,
            "--output",str(ROOT/"output/hydra-implementation-2026-09-04/ranker-v1-02.json")],30,45)
    after=[pin(path)for path in tracked];save("source-pins-after.json",after)
    ok=export["actual_child_exit_code"]==0 and fit is not None and fit["actual_child_exit_code"]==0 and before==after and export["stop_reason"] is None and fit["stop_reason"] is None
    save("result.json",{"schema":"hydra-p5-data-gate-result-v1","status":"complete" if ok else "failed",
        "export":export,"fit":fit,"source_pins_unchanged":before==after,"native_proof_checks":0,
        "model_calls":0,"gpu_allocations":0,"automatic_retry":False})
    return 0 if ok else 1


if __name__=="__main__":raise SystemExit(main())
