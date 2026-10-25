"""One explicit 32-state teacher campaign on a root-owned Slurm allocation.

`prepare` performs metadata/parser admission only. `run` never submits a job,
downloads weights, resumes, retries, trains, or calls another solver/model.
The teacher is loaded once; native prefixes and continuations run serially in
owned resource-bounded children. Only complete independent replays are positive.
"""
from __future__ import annotations

import argparse
import gc
from hashlib import sha256
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time


from experimental_teacher import MODEL_KEY, TeacherLimits, load_teacher, TeacherPlannerBackend
from teacher_states import SCHEMA as SELECTION_SCHEMA, STATE_COUNT, MAX_SELECTION_BYTES, prepare_selection

PROFILE = "hydra-teacher-continuation-campaign-v1"
SMOKE_HELPER_SHA = "0c81000132949df3ab3314272fb39826c942332bc723ce4bec3ed76ad4b6d489"
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
MAX_PROPOSALS = 128
MAX_SCHEDULER_CALLS = 192
MAX_OUTPUT_BYTES = 256 * 1024**2
MAX_ONE_JSON = 2 * 1024**2


class CampaignCancelled(BaseException):
    pass


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "Duplicate JSON field.")
            value[key] = item
        return value
    def invalid(value):
        raise ValueError("Nonfinite JSON value: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def bounded_bytes(path, maximum):
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= maximum,
            "Expected a bounded regular input file.")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) == info.st_size and len(raw) <= maximum, "Input size changed while reading.")
    return raw


def save(path, record):
    raw = canonical(record) + b"\n"
    require(len(raw) <= MAX_ONE_JSON, "Campaign record exceeds its byte ceiling.")
    with Path(path).open("xb") as stream:
        stream.write(raw)
    return {"path": Path(path).name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def bootstrap(app):
    frozen = app.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
    sys.path[:0] = [str(app), str(app / "native-v7"), str(app / "training-v5"), str(frozen)]
    import peano_lab
    require(Path(peano_lab.__file__).resolve() == app / "native-v7/peano_lab/__init__.py",
            "Teacher controller selected the wrong native engine copy.")


def sources(app):
    root = app.parent
    own = Path(__file__).resolve().parent
    files = set(own.glob("*.py")) | set((own / "experimental-models").glob("*.json"))
    files.update(app.glob("*.py"))
    files.update((app / "native-v7/peano_lab").rglob("*.py"))
    files.update((app / "training-v5/hydra_training_v5").rglob("*.py"))
    files.update((root / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/training").rglob("*.py"))
    files.update((app / "training-v5").glob("BASELINE.json"))
    files.add(app / "experimental-models/qwen3-base-v1.json")
    files.add(root / "output/p6-prototype/remote_provider_smoke.py")
    require(600 <= len(files) <= 1200 and sum(p.stat().st_size for p in files) <= 48 * 1024**2,
            "Native/controller source bundle is missing or oversized.")
    require(all(p.is_file() and not p.is_symlink() for p in files), "Source links are forbidden.")
    return {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def smoke_helpers(root):
    path = root / "output/p6-prototype/remote_provider_smoke.py"
    require(path.is_file() and not path.is_symlink() and sha256(path.read_bytes()).hexdigest() == SMOKE_HELPER_SHA,
            "The pinned read-only scheduler helper changed.")
    spec = importlib.util.spec_from_file_location("hydra_p7_scheduler_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reservation_spec(record):
    required = {"schema", "job_id", "job_name", "nonce", "uid", "account", "partition",
                "model_key", "gpus", "nodes", "cpus", "memory_gib", "seconds"}
    require(type(record) is dict and set(record) == required
            and record["schema"] == "hydra-p7-teacher-reservation-v1", "Wrong exact teacher reservation schema.")
    require(record["account"] == ACCOUNT and record["partition"] == PARTITION
            and record["model_key"] == MODEL_KEY and type(record["uid"]) is int
            and record["uid"] == os.getuid(), "Wrong teacher allocation owner/model/account.")
    require(type(record["job_id"]) is str and re.fullmatch(r"\d{1,20}", record["job_id"])
            and type(record["job_name"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", record["job_name"])
            and type(record["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", record["nonce"]),
            "Malformed teacher allocation identity.")
    for key, number in (("gpus", 1), ("nodes", 1), ("cpus", 8), ("memory_gib", 64)):
        require(type(record[key]) is int and record[key] == number, "Teacher allocation differs from fixed resources.")
    require(type(record["seconds"]) is int and 600 <= record["seconds"] <= 7200,
            "Teacher allocation must be explicitly bounded by two GPU hours.")
    return record


class LiveReservation:
    """Use the already reviewed scheduler parser; a new teacher one-use contract."""
    def __init__(self, record, output, helper):
        self.record, self.output, self.helper = record, output, helper
        self.calls, self.last = 0, None

    def __call__(self):
        require(self.calls < MAX_SCHEDULER_CALLS and os.environ.get("SLURM_JOB_ID") == self.record["job_id"],
                "Teacher scheduler query bound/job identity changed.")
        raw, code = self.helper.read_scontrol(self.record["job_id"])
        # Parser shares the established comment binding `hydra-p6:<nonce>`.
        # The reservation schema and model admission remain teacher-specific.
        value = self.helper.parse_scontrol(raw, self.record)
        self.calls += 1
        self.last = value
        row = {"query": self.calls, "actual_exit_code": code, "allocation": value,
               "scheduler_output_sha256": sha256(raw.encode()).hexdigest()}
        raw_row = canonical(row) + b"\n"
        require(len(raw_row) <= 4096, "Scheduler receipt unexpectedly grew.")
        with (self.output / "scheduler.jsonl").open("ab") as stream:
            stream.write(raw_row)
        return value


def read_selection(args, app):
    raw = bounded_bytes(args.selection, MAX_SELECTION_BYTES)
    require(0 < len(raw) <= MAX_SELECTION_BYTES and sha256(raw).hexdigest() == args.selection_sha256,
            "Teacher selection differs from its explicit pin.")
    selection = strict_json(raw)
    require(selection.get("schema") == SELECTION_SCHEMA and selection.get("training_only") is True
            and len(selection.get("states", [])) == STATE_COUNT, "Expected exactly 32 selected training states.")
    # Regenerate from the new admitted dataset, including every reservation and
    # original source prefix. This does not execute a tactic or use teacher answers.
    with tempfile.TemporaryDirectory(prefix="hydra-p7-selection-") as folder:
        destination = Path(folder) / "selection.json"
        prepare_selection(selection["dataset_manifest"], dataset_sha256=selection["dataset_sha256"],
                          app_root=app, output=destination)
        require(destination.read_bytes() == raw, "Teacher state selection is not byte-exactly reproducible.")
    return selection


def _child_rss(pid):
    raw = Path(f"/proc/{pid}/status").read_text()
    match = re.search(r"^VmRSS:\s+(\d+) kB$", raw, flags=re.M)
    require(match is not None, "Owned native child RSS accounting is unavailable.")
    return int(match[1]) * 1024


def native_child(request, *, app, directory, stop):
    directory.mkdir(exist_ok=False)
    request_pin = save(directory / "request.json", request)
    output = directory / "result.json"
    log = directory / "child.log"
    process = None
    started = time.monotonic()
    ceiling = 20 if request["kind"] == "snapshot" else 40
    peak = 0
    stopped_for = None
    record = None
    failure = None
    code = None
    try:
        with log.open("xb") as stream:
            command = [sys.executable, "-B", "-P", str(Path(__file__).with_name("teacher_native.py")),
                "--app-root", str(app), "--request", str(directory / "request.json"),
                "--request-sha256", request_pin["sha256"], "--output", str(output)]
            require(not stop(), "Campaign stopped before native child launch.")
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
            while process.poll() is None:
                if stop():
                    stopped_for = "campaign_deadline"
                elif time.monotonic() - started > ceiling:
                    stopped_for = "owned_child_wall_limit"
                elif os.fstat(stream.fileno()).st_size > 1024**2:
                    stopped_for = "owned_child_log_limit"
                if stopped_for is None:
                    try:
                        peak = max(peak, _child_rss(process.pid))
                    except (OSError, ValueError):
                        if process.poll() is None:
                            stopped_for = "owned_child_rss_unavailable"
                    if peak > 2 * 1024**3:
                        stopped_for = "owned_child_rss_limit"
                if stopped_for:
                    process.kill()
                    break
                time.sleep(0.02)
            code = process.wait(timeout=5)
        if output.exists() and 0 < output.stat().st_size <= MAX_ONE_JSON:
            record = strict_json(output.read_bytes())
            require(type(record) is dict, "Native child returned a non-object result.")
    except BaseException as error:
        failure = error
        stopped_for = stopped_for or ("controller_" + type(error).__name__)
    finally:
        if process is not None:
            try:
                if process.poll() is None:
                    process.kill()
                code = process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired) as cleanup_error:
                failure = failure or cleanup_error
                stopped_for = stopped_for or "owned_child_cleanup_failed"
                code = process.returncode
        receipt = {"actual_exit_code": code, "pid": None if process is None else process.pid,
            "elapsed_seconds": time.monotonic() - started, "peak_rss_bytes": peak,
            "stopped_for": stopped_for, "quiescent": process is None or process.poll() is not None,
            "launched": process is not None,
            "request": request_pin, "child_result_sha256": None if record is None else sha256(output.read_bytes()).hexdigest(),
            "log_bytes": log.stat().st_size if log.exists() else 0, "automatic_retry": False}
        save(directory / "execution.json", receipt)
    if failure is not None:
        raise failure
    resource_exit = code in {-signal.SIGKILL, -signal.SIGXCPU, -signal.SIGALRM}
    if code != 0 or stopped_for is not None or record is None:
        return {"status": "resource_limit" if stopped_for or resource_exit else "native_child_failure",
                "kernel_checked": False, "positive_distillation_eligible": False,
                "execution": receipt, "partial_result": record}
    return {**record, "execution": receipt}


def planner_context(state, snapshot, *, failures, remaining):
    from peano_lab.engine.state import Goal
    from peano_lab.engine.trace import render_goals
    from peano_lab.kernel.formulas import parse_formula_with_names, parse_formula_in_context
    from proof_planner import CapabilitySnapshot, PlannerContext
    target, names = parse_formula_with_names(state["theorem"])
    require(not names and snapshot["prefix_checked"] and snapshot["status"] == "snapshot",
            "Only a freshly checked native prefix can be sent to the teacher.")
    goals = []
    require(type(snapshot["goals"]) is list and 0 < len(snapshot["goals"]) <= 16, "Missing complete native goal tuple.")
    for record in snapshot["goals"]:
        variables = record["variables"]
        require(type(variables) is list and len(variables) <= 64
                and type(record["context"]) is list and len(record["context"]) <= 128,
                "Native goal context exceeds its bound.")
        context = tuple((name, parse_formula_in_context(text, variables)) for name, text in record["context"])
        goals.append(Goal(context, parse_formula_in_context(record["target"], variables), tuple(variables)))
    require(tuple(render_goals(tuple(goals))) == tuple(state["all_goals_before"]) == tuple(snapshot["all_goals_before"]),
            "Typed planner reconstruction changed the exact checked full state.")
    cap = snapshot["capabilities"]
    return PlannerContext(target, (), tuple(goals), CapabilitySnapshot(cap["label"],
        tuple(cap["allowed_commands"]), tuple(cap["allowed_theorems"])), snapshot["kernel_identity"],
        failures=tuple(failures[-16:]), remaining=remaining, certificate_cost=snapshot["partial_proof_cost"])


def campaign(args):
    app = args.app_root.resolve(strict=True)
    root = app.parent
    bootstrap(app)
    before = sources(app)
    require(sha256(canonical(before)).hexdigest() == args.source_pins_sha256,
            "The exact prepared controller/native source bundle changed.")
    selection = read_selection(args, app)
    raw = bounded_bytes(args.reservation, 65536)
    require(not args.reservation.is_symlink() and 0 < len(raw) <= 65536
            and sha256(raw).hexdigest() == args.reservation_sha256, "Teacher reservation differs from its exact pin.")
    reservation = reservation_spec(strict_json(raw))
    require(sys.platform == "linux" and os.environ.get("SLURM_JOB_ID") == reservation["job_id"],
            "Run teacher only inside its exact active remote Slurm allocation.")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    checker = LiveReservation(reservation, output, smoke_helpers(root))
    first = checker()
    save(args.reservation.with_name(args.reservation.name + ".claimed"), {
        "schema": "hydra-p7-reservation-consumption-v1", "job_id": reservation["job_id"],
        "nonce": reservation["nonce"], "reservation_sha256": args.reservation_sha256,
        "selection_sha256": args.selection_sha256, "pid": os.getpid(), "output": str(output),
        "automatic_retry": False})
    began = time.monotonic()
    deadline = began + max(1, reservation["seconds"] - first["elapsed_seconds"] - 60)

    def stop():
        return time.monotonic() >= deadline

    def alarm(signum, frame):
        raise TimeoutError("Teacher campaign cleanup reserve reached.")

    def cancelled(signum, frame):
        raise CampaignCancelled("Teacher campaign received an owned-job cancellation signal.")

    signal.signal(signal.SIGALRM, alarm)
    signal.signal(signal.SIGTERM, cancelled)
    signal.signal(signal.SIGINT, cancelled)
    signal.alarm(max(1, math.ceil(deadline - began)))
    save(output / "request.json", {"schema": "hydra-teacher-campaign-request-v1", "profile": PROFILE,
        "selection_sha256": args.selection_sha256, "selected_ids": [s["id"] for s in selection["states"]],
        "source_pins_before": before, "source_pins_sha256": args.source_pins_sha256,
        "reservation": reservation, "reservation_sha256": args.reservation_sha256,
        "base_directory": str(args.base_directory), "states": STATE_COUNT,
        "max_calls": 64, "max_proposals": MAX_PROPOSALS, "max_output_tokens_per_call": 512,
        "max_input_tokens_including_template": 4096, "model_loads": 1,
        "student_model_calls": 0, "solver_calls": 0, "training_updates": 0, "automatic_retry": False})
    from planner_provider import PlannerProvider
    session = backend = provider = None
    torch = None
    summaries, positives = [], []
    total_proposals = 0
    error = None
    active_state = None
    started_state_ids = []
    try:
        started = time.monotonic()
        session = load_teacher(args.base_directory, app_root=app, reservation_check=checker,
                               should_stop=stop, limits=TeacherLimits())
        torch = session.torch
        torch.cuda.synchronize()
        save(output / "model-admission.json", {"identity": session.identity,
            "cold_load_seconds": time.monotonic() - started,
            "peak_allocated_gpu_bytes": torch.cuda.max_memory_allocated()})
        for index, state in enumerate(selection["states"]):
            require(not stop(), "Teacher campaign has no remaining time.")
            current_bytes = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
            # One prefix plus at most four continuations, each with a <=256KiB
            # request, <=2MiB result and <=1MiB log; proposal records are bounded
            # separately. Leave room for final source and completion receipts.
            require(current_bytes + 24 * 1024**2 <= MAX_OUTPUT_BYTES, "Teacher campaign output budget exhausted.")
            directory = output / (f"{index:03d}-" + state["id"][:16])
            directory.mkdir(exist_ok=False)
            active_state = {"state_id": state["id"], "index": index,
                "model_calls_before": session.calls, "generated_tokens_before": session.generated_tokens,
                "directory": str(directory.relative_to(output))}
            started_state_ids.append(state["id"])
            backend = provider = None
            request = {"schema": "hydra-teacher-native-request-v1", "kind": "snapshot",
                       "state": state, "holdout": selection["holdout"]}
            snapshot = native_child(request, app=app, directory=directory / "prefix", stop=stop)
            summary = {"state_id": state["id"], "index": index, "split": "train",
                "theorem": state["theorem"], "case_id": state["case_id"], "family": state["family"],
                "template_family": state["template_family"], "prefix_status": snapshot["status"],
                "teacher_calls": 0, "generated_tokens": 0, "proposals": 0, "outcome": "unknown",
                "positive_distillation_eligible": False}
            failures = list(state["recorded_failures"])
            if snapshot.get("status") == "snapshot" and snapshot.get("prefix_checked") is True:
                backend = TeacherPlannerBackend(session)
                provider = PlannerProvider(backend, max_calls=2, max_total_generated_tokens=1024)
                seen_commands = set()
                for attempt in range(2):
                    if stop() or total_proposals >= MAX_PROPOSALS:
                        break
                    context = planner_context(state, snapshot, failures=failures,
                        remaining={"depth": 96 - len(state["commands_before"]), "native_tactic_attempts": 384,
                            "model_calls": min(2 - attempt, 64 - session.calls), "imports": 0,
                            "solver_calls": 0, "campaign_proposals": MAX_PROPOSALS - total_proposals})
                    batch = provider.propose(context, model_calls_remaining=64 - session.calls,
                        generated_tokens_remaining=32768 - session.generated_tokens,
                        max_proposals=min(2, MAX_PROPOSALS-total_proposals), should_stop=stop)
                    torch.cuda.synchronize()
                    record = {"schema": "hydra-teacher-proposal-batch-v1", "state_id": state["id"],
                        "attempt": attempt, "status": batch.status, "detail": batch.detail,
                        "actual_model_calls": batch.actual_model_calls, "generated_tokens": batch.generated_tokens,
                        "input": backend.last_input, "output": backend.last_output,
                        "prompt_sha256": batch.prompt_sha256, "cache_identity": batch.cache_identity,
                        "provider": provider.report(), "kernel_checked": False,
                        "plans": [{"commands": p.commands, "reason": p.reason, "source": p.source,
                                  "plan_sha256": p.plan_sha256, "ast_nodes": p.ast_nodes} for p in batch.plans]}
                    proposal_path = directory / f"proposal-{attempt:02d}.json"
                    proposal_pin = save(proposal_path, record)
                    summary["teacher_calls"] += batch.actual_model_calls
                    summary["generated_tokens"] += batch.generated_tokens
                    total_proposals += len(batch.plans)
                    summary["proposals"] += len(batch.plans)
                    if not batch.plans:
                        failures.append((batch.status + ": " + batch.detail)[:1024])
                    for number, plan in enumerate(record["plans"]):
                        commands = tuple(plan["commands"])
                        if commands in seen_commands:
                            save(directory / f"duplicate-{attempt:02d}-{number:02d}.json",
                                 {"status": "repeated_plan_skipped", "plan_sha256": plan["plan_sha256"], "native_calls": 0})
                            continue
                        seen_commands.add(commands)
                        request = {"schema": "hydra-teacher-native-request-v1", "kind": "continuation",
                                   "state": state, "holdout": selection["holdout"], "plan": plan}
                        child_directory = directory / f"native-{attempt:02d}-{number:02d}"
                        result = native_child(request, app=app, directory=child_directory, stop=stop)
                        if (result.get("status") == "proved" and result.get("kernel_checked") is True
                                and result.get("independent_replay_checked") is True
                                and result.get("positive_distillation_eligible") is True):
                            summary.update(outcome="proved", positive_distillation_eligible=True,
                                successful_native_record=str((child_directory / "result.json").relative_to(output)),
                                successful_native_sha256=sha256((child_directory / "result.json").read_bytes()).hexdigest(),
                                native_execution_record=str((child_directory / "execution.json").relative_to(output)),
                                native_execution_sha256=sha256((child_directory / "execution.json").read_bytes()).hexdigest(),
                                teacher_proposal_record=str(proposal_path.relative_to(output)),
                                teacher_proposal_sha256=proposal_pin["sha256"],
                                teacher_plan_index=number, teacher_plan_sha256=plan["plan_sha256"],
                                complete_steps=len(result["commands"]), proof_cost=result["proof_cost"])
                            positives.append({**summary, "selection_sha256": args.selection_sha256,
                                "teacher_model_manifest_sha256": session.identity["model_manifest_sha256"],
                                "dataset_admission_required": "fresh_full_native_replay_and_reserved_state_exclusion"})
                            break
                        failures.append(("native " + result["status"] + ": " + str(result.get("error", result.get("reason", ""))))[:1024])
                    if summary["outcome"] == "proved" or batch.status in {"input_rejected", "limit"}:
                        break
            else:
                summary["outcome"] = "prefix_rejected_or_censored"
            save(directory / "summary.json", summary)
            summaries.append(summary)
            active_state = None
        checker()
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:1024]}
        if active_state is not None and session is not None:
            active_state = {**active_state, "error": error,
                "actual_model_calls": session.calls - active_state["model_calls_before"],
                "generated_tokens": session.generated_tokens - active_state["generated_tokens_before"],
                "last_teacher_input": None if backend is None else backend.last_input,
                "last_teacher_output": None if backend is None else backend.last_output,
                "positive_distillation_eligible": False}
            save(output / "interrupted-state.json", active_state)
        raise
    finally:
        session_report = None if session is None else session.report()
        peak = None if torch is None else {"allocated": torch.cuda.max_memory_allocated(),
                                          "reserved": torch.cuda.max_memory_reserved()}
        session = backend = provider = None
        gc.collect()
        if torch is not None:
            torch.cuda.empty_cache()
        after = sources(app)
        signal.alarm(0)
        save(output / "positive-continuations.json", {"schema": "hydra-teacher-positive-continuations-v1",
            "records": positives, "training_performed": False,
            "positive_count": len(positives), "fresh_p5_admission_required": True})
        save(output / "completion.json", {"schema": "hydra-teacher-campaign-completion-v1",
            "profile": PROFILE, "completed": error is None and len(summaries) == STATE_COUNT and after == before,
            "error": error, "elapsed_seconds": time.monotonic() - began,
            "selected_states": STATE_COUNT, "states_completed": len(summaries),
            "started_state_ids": started_state_ids,
            "unattempted_state_ids": [s["id"] for s in selection["states"] if s["id"] not in started_state_ids],
            "interrupted_state_id": None if active_state is None else active_state["state_id"],
            "summaries": summaries, "positive_continuations": len(positives),
            "proposals": total_proposals, "session": session_report, "peak_gpu_bytes": peak,
            "sources_unchanged": after == before, "source_pins_after": after,
            "scheduler_calls": checker.calls, "last_live_allocation": checker.last,
            "optimizer_updates": 0, "student_model_calls": 0, "solver_calls": 0,
            "automatic_retry": False, "model_disposal_attempted": True,
            "actual_outer_exit_required": True, "benchmark_claim": False})


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--app-root", type=Path, required=True)
    prepare.add_argument("--dataset-manifest", required=True)
    prepare.add_argument("--dataset-sha256", required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--sources-output", type=Path, required=True)
    run = sub.add_parser("run")
    for name in ("app-root", "selection", "reservation", "base-directory", "output"):
        run.add_argument("--" + name, type=Path, required=True)
    for name in ("selection-sha256", "reservation-sha256", "source-pins-sha256"):
        run.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        app = args.app_root.resolve(strict=True)
        bootstrap(app)
        result = prepare_selection(args.dataset_manifest, dataset_sha256=args.dataset_sha256,
                                   app_root=app, output=args.output)
        pins = sources(app)
        save(args.sources_output, {"schema": "hydra-teacher-source-pins-v1", "sources": pins,
                                  "source_pins_sha256": sha256(canonical(pins)).hexdigest()})
        print(json.dumps(result, sort_keys=True))
    else:
        campaign(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
