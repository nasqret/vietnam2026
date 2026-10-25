"""One scheduled local P7 authored fixture, never a teacher/model result.

The only proof computation is teacher_native.execute for one prepared request,
including its required independent original-theorem replay. The follow-up uses
the exact selection already admitted in local-native-01, without changing it.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
APP = ROOT / "hydra-playground"
STAGED = HERE / "staged"
DATASET = "output/hydra-implementation-2026-09-04/decisions-v2-01/manifest.json"
DATASET_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
FIXTURE_STATE = "5c2e1f7885846af7ea8e7be54001edcebcf04cc191342ec5aeeb5336881211f1"
CPU, WALL, RSS, OUTPUT = 35, 45, 2 * 1024**3, 16 * 1024**2


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def pins():
    sys.path.insert(0, str(STAGED))
    from teacher_campaign import sources
    value = sources(APP)
    value[str(Path(__file__).relative_to(ROOT))] = sha256(Path(__file__).read_bytes()).hexdigest()
    return value


def worker(out):
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT, OUTPUT))
    signal.alarm(WALL)

    def no_external(event, args):
        if event in {"subprocess.Popen", "os.system", "os.exec", "socket.connect", "socket.bind"}:
            raise RuntimeError("This authored native fixture cannot spawn advisers or access a network.")
    sys.addaudithook(no_external)
    sys.path.insert(0, str(STAGED))
    from teacher_campaign import bootstrap
    from make_native_fixture import main as prepare_fixture
    bootstrap(APP)
    began = time.monotonic()
    original = HERE / "local-native-01"
    preparation = json.loads((original / "preparation.json").read_bytes())
    raw = (original / "selection.json").read_bytes()
    if sha256(raw).hexdigest() != preparation["sha256"]:
        raise ValueError("The previously admitted frozen selection changed.")
    with (out / "selection.json").open("xb") as stream:
        stream.write(raw)
    save(out / "preparation.json", {**preparation, "reused_without_changes": True,
        "previous_admission_record": str((original / "preparation.json").relative_to(ROOT)),
        "source_selection_sha256": sha256(raw).hexdigest(),
        "native_proof_runs": 0, "model_calls": 0})
    prepare_fixture(["--selection", str(out / "selection.json"), "--selection-sha256",
                     preparation["sha256"], "--state-id", FIXTURE_STATE,
                     "--output-directory", str(out / "fixtures")])
    from teacher_native import bootstrap as native_bootstrap, execute
    native_bootstrap(APP)
    request = json.loads((out / "fixtures/positive.json").read_bytes())
    audit = {}
    native_began = time.monotonic()
    try:
        result = execute(request, app=APP, deadline=min(began + WALL - 2, native_began + 35), audit=audit)
    except BaseException as error:
        save(out / "native-error.json", {**audit, "error_type": type(error).__name__,
            "error": str(error)[:1024], "elapsed_seconds": time.monotonic() - native_began,
            "kernel_checked": False, "model_calls": 0, "solver_calls": 0})
        raise
    save(out / "native-result.json", result)
    accepted = (result.get("status") == "proved" and result.get("kernel_checked") is True
        and result.get("independent_replay_checked") is True
        and result.get("positive_distillation_eligible") is False
        and result["counts"]["model_calls"] == result["counts"]["solver_calls"] == 0
        and result["counts"]["teacher_steps_accepted"] >= 1
        and any(row["source"] == "manual_fixture" for row in result["provenance"]))
    save(out / "fixture-check.json", {"accepted": accepted, "status": result["status"],
        "full_steps": len(result.get("commands", ())), "proof_cost": result.get("proof_cost"),
        "native_elapsed_seconds": time.monotonic() - native_began,
        "total_child_seconds": time.monotonic() - began, "provenance": "manual_fixture",
        "teacher_model_executed": False, "distillation_eligible": False,
        "wrong_original_fixture_executed": False, "benchmark_claim": False})
    return 0 if accepted else 1


def parent(attempt):
    if not attempt.isascii() or not attempt.replace("-", "").isalnum():
        raise ValueError("Use one fresh local attempt name.")
    out = HERE / attempt
    out.mkdir(exist_ok=False)
    before = pins()
    save(out / "request.json", {"schema": "hydra-p7-local-authored-native-gate-v1",
        "source_pins_before": before, "dataset_manifest": DATASET, "dataset_sha256": DATASET_SHA,
        "limits": {"cpu_seconds": CPU, "wall_seconds": WALL, "rss_bytes": RSS, "output_bytes": OUTPUT},
        "model_calls": 0, "solver_calls": 0, "automatic_retry": False,
        "diagnosed_followup_to": "local-native-01", "fixture_state_id": FIXTURE_STATE,
        "fixture_provenance": "manual_fixture", "teacher_distillation_eligible": False})
    process, peak, stopped = None, 0, None
    began = time.monotonic()
    try:
        sys.path.insert(0, str(APP))
        from vampire_process import _owned_child_rss, _resident_size
        _resident_size(os.getpid())  # read-only self ABI check; no solver work
        with (out / "child.log").open("xb") as log:
            process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                "--worker", str(out)], cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"})
            while process.poll() is None:
                rss = _owned_child_rss(process)
                if rss is not None:
                    peak = max(peak, rss)
                    if rss > RSS:
                        stopped = "owned_child_rss_limit"
                if time.monotonic() - began > WALL:
                    stopped = stopped or "wall_limit"
                if sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) > OUTPUT:
                    stopped = stopped or "output_limit"
                if stopped:
                    process.kill()
                    break
                time.sleep(0.02)
            process.wait(timeout=5)
    except BaseException as error:
        stopped = stopped or (type(error).__name__ + ": " + str(error)[:240])
        raise
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        after = pins()
        receipt = {"actual_child_exit_code": None if process is None else process.returncode,
            "owned_pid": None if process is None else process.pid,
            "quiescent": process is None or process.poll() is not None,
            "sampled_peak_rss_bytes": peak, "elapsed_seconds": time.monotonic() - began,
            "stopped_for": stopped, "source_pins_after": after, "sources_unchanged": after == before,
            "model_calls": 0, "solver_calls": 0, "automatic_retry": False}
        save(out / "actual-completion.json", receipt)
        print(json.dumps({k: v for k, v in receipt.items() if k != "source_pins_after"}), flush=True)
    return 0 if process is not None and process.returncode == 0 and not stopped and before == after else 1


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        destination = Path(sys.argv[2]).resolve(strict=True)
        if destination.parent != HERE:
            raise ValueError("Worker output must be this gate's owned attempt directory.")
        raise SystemExit(worker(destination))
    if len(sys.argv) != 2:
        raise SystemExit("usage: local_native_gate.py <fresh-attempt-name>")
    raise SystemExit(parent(sys.argv[1]))
