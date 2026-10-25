"""Run ONE prepared native proof, with owned-child wall/RSS/output monitoring.

No model, Vampire, HTTP, library theorem import, or checker-limit changes.
The ordinary first proof and the independent run_proof replay have separate
records. A resource stop leaves accepted-prefix records and the actual child
exit; it is never counted as a proof.
"""
from pathlib import Path
import argparse
import gc
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = ROOT / "hydra-playground"
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
WALL_SECONDS = 180
CPU_SECONDS = 175
RSS_BYTES = 2 * 1024**3
OUTPUT_BYTES = 16 * 1024**2
SAMPLE_SECONDS = 0.02
SOURCE_PATHS = (Path(__file__), APP / "vampire_process.py", APP / "vampire_limits.py",
    SOURCE / "training/peano_policy/search.py", SOURCE / "peano-lab/py/peano_lab/batch.py",
    SOURCE / "peano-lab/py/peano_lab/ui/prove.py", SOURCE / "peano-lab/py/peano_lab/engine/ring.py",
    SOURCE / "peano-lab/py/peano_lab/engine/tactics.py", SOURCE / "peano-lab/py/peano_lab/kernel/checker.py")


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def pins():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in SOURCE_PATHS}


def worker(out):
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(WALL_SECONDS)

    def no_external_advice(event, args):
        if event in ("subprocess.Popen", "os.system", "os.exec", "socket.connect", "socket.bind"):
            raise RuntimeError("this native-only proof probe cannot start advice or network processes")

    sys.addaudithook(no_external_advice)
    sys.path[:0] = [str(SOURCE), str(SOURCE / "peano-lab/py")]
    from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
    from peano_lab.engine.state import proof_size
    from peano_lab.kernel.formulas import parse_formula_with_names
    from peano_lab.ui.prove import SurfaceCapabilities, checked_surface_final
    from training.peano_policy.search import _PrefixSnapshot, _canonical_goals, _new_owner, _replay

    request = json.loads((out / "request.json").read_text())
    theorem, commands = request["case"]["theorem"], tuple(request["case"]["commands"])
    capabilities = SurfaceCapabilities(label="hydra-polynomial-chunk-prototype-no-imports",
        allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
    target, names = parse_formula_with_names(theorem)
    owner = _new_owner(target, names, theorem, classical=False, replay_id=0)
    prefix = _PrefixSnapshot.capture(owner, commands=(), goals=_canonical_goals(owner), capabilities=capabilities)
    started = time.monotonic()
    with (out / "native-edges.jsonl").open("x", encoding="utf-8") as stream:
        for index, command in enumerate(commands):
            step_started = time.monotonic()
            following, failed, error = _replay(target, names, theorem, prefix.commands + (command,),
                classical=False, capabilities=capabilities, replay_id=index + 1,
                prefix=prefix, expected_goals=prefix.goals)
            row = {"step": index + 1, "command": command,
                   "elapsed_seconds": round(time.monotonic() - step_started, 6),
                   "accepted": following is not None, "error": None if error is None else str(error)}
            if following is not None:
                row["goals_after"] = list(_canonical_goals(following))
                prefix = _PrefixSnapshot.capture(following, commands=prefix.commands + (command,),
                    goals=tuple(row["goals_after"]), capabilities=capabilities)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
            print(json.dumps({k: v for k, v in row.items() if k != "goals_after"}), flush=True)
            if following is None:
                write_json(out / "native-final.json", {"kernel_checked": False,
                    "accepted_steps": len(prefix.commands), "failed_step": index + 1,
                    "error": row["error"], "goals": list(prefix.goals),
                    "elapsed_seconds": time.monotonic() - started})
                return 2
    if not prefix.state.is_done():
        write_json(out / "native-final.json", {"kernel_checked": False,
            "accepted_steps": len(prefix.commands), "goals": list(prefix.goals),
            "elapsed_seconds": time.monotonic() - started})
        return 2
    certificate = checked_surface_final(prefix.state, target, classical=False, trace=None)
    nodes = proof_size(certificate)
    native_elapsed = time.monotonic() - started
    write_json(out / "native-final.json", {"kernel_checked": True, "theorem": theorem,
        "accepted_steps": len(prefix.commands), "goals": [], "proof_nodes": nodes,
        "elapsed_seconds": native_elapsed, "independent_replay_pending": True})
    print(json.dumps({"phase": "native_final_checked", "proof_nodes": nodes,
                      "elapsed_seconds": native_elapsed}), flush=True)
    del certificate, prefix, owner, following
    gc.collect()
    replay_started = time.monotonic()
    replay = run_proof(theorem, commands, request_id="polynomial-chunks-independent-replay",
        classical=False, on_error="stop", capabilities=capabilities,
        trace_byte_limit=2 * 1024**2).to_dict()
    replay_elapsed = time.monotonic() - replay_started
    write_json(out / "independent-replay.json", replay)
    assert replay["status"] == "proved" and replay["kernel_checked"] is True
    assert replay["goals"] == [] and replay["proof_nodes"] == nodes
    replay_target, _ = parse_formula_with_names(replay["theorem"])
    assert replay_target == target
    record = {"schema": "hydra-polynomial-chunks-native-probe-v1", "proved": True,
        "native_kernel_checked": True, "independent_replay_kernel_checked": True,
        "native_proof_nodes": nodes, "independent_replay_proof_nodes": replay["proof_nodes"],
        "native_elapsed_seconds": native_elapsed, "independent_replay_elapsed_seconds": replay_elapsed,
        "elapsed_seconds": time.monotonic() - started, "steps": len(commands),
        "case_id": request["case"]["case_id"], "model_calls": 0, "vampire_calls": 0,
        "timing_scope": "isolated native prototype, not a model benchmark"}
    write_json(out / "result.json", record)
    print(json.dumps(record), flush=True)
    return 0


def parent(args):
    assert args.attempt.isascii() and args.attempt.replace("-", "").isalnum()
    plans_path = Path(args.plans).resolve()
    assert plans_path.is_relative_to(HERE) and plans_path.stat().st_size <= 1024**2
    plans_data = plans_path.read_bytes()
    plans = json.loads(plans_data)
    case, = [case for case in plans["cases"] if case["case_id"] == args.case]
    assert case["plan_generated"] and 1 <= len(case["commands"]) <= 160
    assert all(isinstance(line, str) and len(line.encode("utf-8")) <= 512 for line in case["commands"])
    out = HERE / args.attempt
    out.mkdir(exist_ok=False)
    before = pins()
    request = {"schema": "hydra-polynomial-chunks-guarded-request-v1", "case": case,
        "plans_path": str(plans_path.relative_to(ROOT)), "plans_sha256": hashlib.sha256(plans_data).hexdigest(),
        "generator_source_pins": plans["source_pins"], "execution_source_pins_before": before,
        "limits": {"wall_seconds": WALL_SECONDS, "child_cpu_seconds": CPU_SECONDS,
                   "sampled_owned_child_rss_bytes": RSS_BYTES, "output_bytes": OUTPUT_BYTES,
                   "sample_interval_seconds": SAMPLE_SECONDS},
        "model_calls": 0, "vampire_calls": 0}
    write_json(out / "request.json", request)
    process = None
    peak = 0
    stop = None
    started = time.monotonic()
    try:
        sys.path.insert(0, str(APP))
        # Only the fixed, read-only owned-child RSS accounting helpers are used.
        # Importing this module does not inspect a solver package or start one.
        from vampire_process import _owned_child_rss, _resident_size
        _resident_size(os.getpid())  # fail closed before launching if unavailable
        with (out / "worker-output.txt").open("xb") as log:
            process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                "--worker", str(out)], cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"})
            while process.poll() is None:
                rss = _owned_child_rss(process)
                if rss is not None:
                    peak = max(peak, rss)
                    if rss > RSS_BYTES:
                        stop = "owned_child_rss"
                if time.monotonic() - started > WALL_SECONDS:
                    stop = stop or "wall_seconds"
                if sum(path.stat().st_size for path in out.iterdir() if path.is_file()) > OUTPUT_BYTES:
                    stop = stop or "output_bytes"
                if stop:
                    process.kill()
                    break
                time.sleep(SAMPLE_SECONDS)
            actual_exit = process.wait(timeout=5)
    except BaseException as error:
        stop = stop or ("guard_error: " + str(error)[:240])
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        raise
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        after = pins()
        record = {"schema": "hydra-owned-native-probe-completion-v1",
            "actual_child_exit_code": None if process is None else process.returncode,
            "child_pid": None if process is None else process.pid, "owned_child_reaped": process is not None and process.returncode is not None,
            "stop_reason": stop, "sampled_peak_owned_child_rss_bytes": peak,
            "elapsed_seconds": time.monotonic() - started,
            "execution_source_pins_after": after, "execution_sources_unchanged": before == after,
            "model_calls": 0, "vampire_calls": 0,
            "proof_record_present": (out / "result.json").exists()}
        write_json(out / "actual-completion.json", record)
        print(json.dumps(record), flush=True)
    return 0 if actual_exit == 0 and stop is None and before == after and (out / "result.json").exists() else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plans")
    parser.add_argument("--case")
    parser.add_argument("--attempt")
    parser.add_argument("--worker")
    args = parser.parse_args()
    if args.worker:
        destination = Path(args.worker).resolve()
        assert destination.parent == HERE and destination.is_dir()
        raise SystemExit(worker(destination))
    assert args.plans and args.case and args.attempt
    raise SystemExit(parent(args))
