# Scheduler revision: one query may use 15 wall seconds, still no retries.
# All model/job/native limits and exact live-identity checks remain unchanged.
# Provider v2 binding of the frozen p6-prototype controller.
# Uses the v2 Transformers 4.53.3 beam-slot accounting; no controller behavior,
# reservation schema, resource ceiling, or retry policy changes.
"""One remote, owned-allocation smoke; never submit, resume, retry or train.

Invoke only inside a root-created held-then-released Slurm job, with the exact
one-use reservation SHA. Invalid model suggestions are preserved as invalid;
successful transport/inference is distinct from any native proof success.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import gc
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
REGISTRY_SHA = "3303c4727052557a04bc2e33ea624ff7093703c68ae8fa95b12fb05adbc781c1"
KERNEL_SHA = "ad88855528244707b1fe7bd142d8fea60883a23b429840e07dd1875f3499c45d"
THEOREM = "forall a b. a=b -> b=a"
PREFIX = ("intro a", "intro b", "intro h")
PRIMITIVE_BEAMS = 4
PLANNER_TOKENS = 256
MAX_OUTPUT_BYTES = 8 * 1024**2
MAX_SCONTROL_BYTES = 65536
SCONTROL_WALL_SECONDS = 15.0
MAX_SCONTROL_CALLS = 64
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate request field.")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("Nonfinite JSON number: " + value)
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    require(type(result) is dict, "Expected one JSON object.")
    return result


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= 2 * 1024**2, "One smoke record exceeds its byte ceiling.")
    with path.open("xb") as stream:
        stream.write(raw)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def seconds(text):
    match = re.fullmatch(r"(?:(\d+)-)?(\d+):(\d{2}):(\d{2})", text)
    require(match is not None, "Missing/unsupported finite Slurm duration.")
    days, hours, minutes, secs = (int(value or 0) for value in match.groups())
    require(minutes < 60 and secs < 60, "Malformed Slurm duration.")
    return days * 86400 + hours * 3600 + minutes * 60 + secs


def memory_gib(text):
    match = re.fullmatch(r"(\d+)([KMGT])", text)
    require(match is not None, "Missing/unsupported allocated memory unit.")
    number, unit = match.groups()
    value = int(number) * {"K": 1 / 1024**2, "M": 1 / 1024, "G": 1, "T": 1024}[unit]
    require(value.is_integer() if isinstance(value, float) else True, "Nonintegral GiB allocation.")
    return int(value)


def reservation_spec(record):
    required = {"schema", "job_id", "job_name", "nonce", "uid", "account", "partition",
                "model_key", "gpus", "nodes", "cpus", "memory_gib", "seconds"}
    require(set(record) == required and record["schema"] == "hydra-p6-smoke-reservation-v1",
            "Reservation must use the exact one-use smoke schema.")
    require(type(record["job_id"]) is str and re.fullmatch(r"\d{1,20}", record["job_id"])
            and type(record["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", record["nonce"])
            and type(record["job_name"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", record["job_name"]),
            "Invalid bounded reservation identity.")
    require(record["account"] == ACCOUNT and record["partition"] == PARTITION
            and record["model_key"] in {"qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base"},
            "Unsupported account, partition or model.")
    for key, expected in (("gpus", 1), ("nodes", 1), ("cpus", 8), ("memory_gib", 64), ("seconds", 600)):
        require(type(record[key]) is int and record[key] == expected, "Smoke allocation differs from its fixed ceiling.")
    require(type(record["uid"]) is int and record["uid"] == os.getuid(), "Reservation does not belong to this uid.")
    return record


def parse_scontrol(raw, record):
    require(type(raw) is str and len(raw.encode()) <= MAX_SCONTROL_BYTES and "\x00" not in raw,
            "Malformed scheduler response.")
    pairs = re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)", raw)
    fields = {}
    for key, value in pairs:
        require(key not in fields, "Duplicate scheduler field.")
        fields[key] = value
    require(fields.get("JobId") == record["job_id"] and fields.get("JobName") == record["job_name"]
            and fields.get("Comment") == "hydra-p6:" + record["nonce"]
            and fields.get("Account") == ACCOUNT and fields.get("Partition") == PARTITION
            and fields.get("JobState") == "RUNNING" and fields.get("Requeue") == "0"
            and fields.get("Restarts") == "0", "Live scheduler identity/state/nonce/retry policy differs.")
    owner = re.fullmatch(r"[^()\s]+\((\d+)\)", fields.get("UserId", ""))
    require(owner is not None and int(owner[1]) == record["uid"], "Live job belongs to another uid.")
    require(fields.get("NumNodes") == "1" and fields.get("NumCPUs") == str(record["cpus"])
            and re.fullmatch(r"[A-Za-z0-9_.-]+", fields.get("NodeList", ""))
            and fields.get("NodeList") not in {"None", "(null)"}, "Expected exactly one allocated compute node.")
    tres = {}
    for item in fields.get("AllocTRES", "").split(","):
        require(item.count("=") == 1, "Missing/malformed actual allocated TRES.")
        key, value = item.split("=", 1)
        require(key not in tres, "Duplicate allocated TRES.")
        tres[key] = value
    require(tres.get("cpu") == str(record["cpus"]) and tres.get("node") == "1"
            and tres.get("gres/gpu") == "1" and memory_gib(tres.get("mem", "")) == record["memory_gib"],
            "Actual allocated CPU/memory/GPU resources differ.")
    total = seconds(fields.get("TimeLimit", ""))
    elapsed = seconds(fields.get("RunTime", ""))
    require(total == record["seconds"] and 0 <= elapsed < total - 10, "No bounded live allocation remains.")
    return {"job_id": record["job_id"], "gpus": 1, "cpus": record["cpus"],
            "memory_gib": record["memory_gib"], "seconds": total, "elapsed_seconds": elapsed,
            "node": fields["NodeList"], "job_name": fields["JobName"], "nonce": record["nonce"]}


def read_scontrol(job):
    executable = shutil.which("scontrol")
    require(executable is not None, "Slurm scontrol is unavailable; no fallback reservation is accepted.")
    process = None
    with tempfile.TemporaryFile() as output:
        started = time.monotonic()
        try:
            process = subprocess.Popen([executable, "-o", "show", "job", job],
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
            while process.poll() is None:
                elapsed = time.monotonic() - started
                output_bytes = os.fstat(output.fileno()).st_size
                if elapsed > SCONTROL_WALL_SECONDS or output_bytes > MAX_SCONTROL_BYTES:
                    reason = "output" if output_bytes > MAX_SCONTROL_BYTES else "wall"
                    process.kill()
                    actual_exit = process.wait(timeout=3)
                    raise RuntimeError("Owned scontrol query exceeded its " + reason
                        + " ceiling; elapsed_seconds=" + str(round(elapsed, 6))
                        + "; output_bytes=" + str(output_bytes)
                        + "; actual_child_exit=" + str(actual_exit) + "; no retry.")
                time.sleep(0.01)
            code = process.wait(timeout=3)
            require(code == 0, "scontrol returned a nonzero actual exit.")
            output.seek(0)
            raw = output.read(MAX_SCONTROL_BYTES + 1)
            require(len(raw) <= MAX_SCONTROL_BYTES, "scontrol output exceeded its byte ceiling.")
            return raw.decode("utf-8"), code
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=3)


class LiveReservation:
    def __init__(self, record, output):
        self.record, self.output = record, output
        self.calls = 0
        self.last = None

    def __call__(self):
        require(self.calls < MAX_SCONTROL_CALLS, "Scheduler query count exceeded its finite bound.")
        require(os.environ.get("SLURM_JOB_ID") == self.record["job_id"], "The worker left its exact Slurm job.")
        raw, actual_exit = read_scontrol(self.record["job_id"])
        value = parse_scontrol(raw, self.record)
        self.calls += 1
        with (self.output / "scheduler.jsonl").open("ab") as stream:
            stream.write(canonical({"call": self.calls, "actual_exit_code": actual_exit,
                                   "raw": raw, "observed": value}) + b"\n")
        self.last = value
        return value


def source_pins(app):
    files = [Path(__file__).resolve(), app / "experimental_model.py",
             app / "experimental-models/qwen3-base-v1.json", app / "proof_planner.py",
             app / "planner_provider.py", app / "finite_difference.py", app / "arithmetic_search.py"]
    files.extend(sorted((app / "native-v7/peano_lab").rglob("*.py")))
    files.extend(sorted((app / "training-v5/hydra_training_v5").rglob("*.py")))
    files.append(app / "training-v5/BASELINE.json")
    require(100 <= len(files) <= 1024 and sum(p.stat().st_size for p in files) <= 32 * 1024**2,
            "Missing/oversized native/controller source bundle.")
    return {str(path.relative_to(app.parent)): digest(path) for path in files}


def kernel_identity(app):
    files = {p.name: digest(p) for p in sorted((app / "native-v7/peano_lab/kernel").glob("*.py"))}
    value = sha256(canonical({"logic": "intuitionistic", "files": files})).hexdigest()
    require(value == KERNEL_SHA, "Native kernel differs from the original unchanged checker family.")
    return value


class RecordingPlanner:
    """Transparent record of the real backend callbacks; never supplies answers."""
    def __init__(self, backend):
        self.backend = backend
        self.prompt = self.input_ids = self.output_ids = self.output_text = None

    @property
    def identity(self):
        return self.backend.identity

    @property
    def calls(self):
        return self.backend.calls

    @property
    def generated_tokens(self):
        return self.backend.generated_tokens

    def encode_prompt(self, prompt):
        self.prompt = prompt
        self.input_ids = self.backend.encode_prompt(prompt)
        return self.input_ids

    def generate(self, input_ids, *, max_new_tokens, should_stop=None):
        self.output_ids = self.backend.generate(input_ids, max_new_tokens=max_new_tokens, should_stop=should_stop)
        return self.output_ids

    def decode_output(self, output_ids):
        self.output_text = self.backend.decode_output(output_ids)
        return self.output_text


def native_setup():
    from peano_lab.batch import MODEL_V1_COMMANDS
    from peano_lab.kernel.formulas import parse_formula_with_names
    from peano_lab.engine.state import start
    from peano_lab.engine.trace import TraceLogger
    from peano_lab.ui.prove import ProofSession, SurfaceCapabilities, run_surface
    authority = SurfaceCapabilities(label="hydra-authority-no-imports-v1",
        allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
    target, names = parse_formula_with_names(THEOREM)
    def fresh():
        owner = ProofSession(start(target, names), target, names, THEOREM, False,
                             TraceLogger(session_id="p6-remote-smoke"))
        for command in PREFIX:
            owner = run_surface(owner, command, capabilities=authority)
        return owner
    return fresh, authority


def validate_native_candidates(candidates, fresh, authority, stop):
    from peano_lab.batch import run_proof
    from peano_lab.engine.tactics import TacticError
    from peano_lab.engine.state import proof_metrics
    from peano_lab.engine.trace import render_goals
    from peano_lab.ui.prove import checked_surface_final, run_surface
    records = []
    for candidate in candidates:
        require(not stop(), "Native smoke deadline reached.")
        owner = fresh()
        began = time.monotonic()
        row = {"candidate": candidate, "source": "model", "native_step_accepted": False,
               "kernel_checked": False, "independent_replay_checked": False}
        try:
            owner = run_surface(owner, candidate, capabilities=authority)
            row["native_step_accepted"] = True
            goals = render_goals(owner.state)
            if len(canonical(goals)) <= 16384:
                row["goals_after"] = goals
            else:
                row["goals_omitted_for_byte_limit"] = True
            if owner.state.is_done():
                certificate = checked_surface_final(owner.state, owner.original_target)
                replay = run_proof(THEOREM, PREFIX + (candidate,), capabilities=authority)
                require(replay.status == "proved" and replay.kernel_checked, "Independent native replay rejected the candidate proof.")
                row.update(kernel_checked=True, independent_replay_checked=True,
                           proof_nodes=proof_metrics(certificate)[0], complete_script=PREFIX + (candidate,),
                           script_sources=("manual_setup",) * len(PREFIX) + ("model",))
        except TacticError as error:
            row["native_error"] = str(error)[:1000]
        row["elapsed_seconds"] = time.monotonic() - began
        records.append(row)
    return records


def run(args):
    app = args.app_root.resolve(strict=True)
    require(digest(app / "experimental_model.py") == PROVIDER_SHA
            and digest(app / "experimental-models/qwen3-base-v1.json") == REGISTRY_SHA,
            "Experimental provider/registry differ from the reviewed implementation.")
    reservation_path = args.reservation.resolve(strict=True)
    require(not args.reservation.is_symlink() and reservation_path.stat().st_size <= 65536,
            "Expected a bounded ordinary one-use reservation file.")
    raw = reservation_path.read_bytes()
    require(sha256(raw).hexdigest() == args.reservation_sha256, "Reservation identity differs from the supplied pin.")
    reservation = reservation_spec(strict_json(raw))
    require(os.environ.get("SLURM_JOB_ID") == reservation["job_id"], "No exact active Slurm job is owned here.")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    checker = LiveReservation(reservation, output)
    first = checker()
    # Exclusive, adjacent one-use claim survives failure and is never reset.
    save(reservation_path.with_name(reservation_path.name + ".claimed"), {
        "schema": "hydra-p6-reservation-consumption-v1", "nonce": reservation["nonce"],
        "job_id": reservation["job_id"], "reservation_sha256": args.reservation_sha256,
        "output": str(output), "pid": os.getpid(), "automatic_retry": False})
    require(digest(reservation_path) == args.reservation_sha256, "Reservation changed while claimed.")
    os.chdir(app.parent)
    sys.path[:0] = [str(app), str(app / "native-v7"), str(app / "training-v5")]
    before = source_pins(app)
    kernel_sha = kernel_identity(app)
    began = time.monotonic()
    deadline = began + max(1, reservation["seconds"] - first["elapsed_seconds"] - 60)
    def stop():
        return time.monotonic() >= deadline
    def alarm(signum, frame):
        raise TimeoutError("Smoke cleanup reserve reached; no retry.")
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(max(1, math.ceil(deadline - time.monotonic())))
    save(output / "request.json", {"schema": "hydra-p6-remote-smoke-request-v1", "reservation": reservation,
        "reservation_sha256": args.reservation_sha256, "provider_sha256": PROVIDER_SHA,
        "source_pins_before": before, "kernel_identity": kernel_sha,
        "theorem": THEOREM, "authored_setup": PREFIX, "primitive_beams": PRIMITIVE_BEAMS,
        "primitive_new_tokens": 64, "planner_new_tokens": PLANNER_TOKENS,
        "input_token_cap": 4096, "model_call_cap": 2, "base_directory": str(args.base_directory),
        "adapter_directory": None if args.adapter_directory is None else str(args.adapter_directory),
        "adapter_manifest_sha256": args.adapter_manifest_sha256, "adapter_kind": args.adapter_kind,
        "optional_throughput_examples": args.throughput_examples, "automatic_retry": False,
        "training_pilot": False, "optimizer_updates": 0, "vampire_calls": 0})
    session = policy = backend = recording = provider = None
    torch = None
    completed = False
    error = None
    data = {}
    try:
        from experimental_model import load_torch_model, TorchPrimitivePolicy, TorchPlannerBackend, SessionLimits
        from proof_planner import CapabilitySnapshot, PlannerContext
        from planner_provider import PlannerProvider
        from peano_lab.engine.trace import render_goals
        from peano_lab.engine.state import proof_metrics, proof_identity_metrics
        from hydra_training_v5.peano_policy.contract import authority_prompt_environment
        from hydra_training_v5.peano_policy.prompt import CapabilityIdentity, render_prompt
        throughput_plan = None
        if args.throughput_examples:
            require(args.adapter_directory is None, "End-of-session throughput only accepts an unadapted base.")
            require(args.throughput_config is not None and args.dataset_manifest is not None
                    and args.dataset_sha256 is not None, "Throughput needs an exact admitted pilot config/dataset.")
            from hydra_training_v5.decision_pilot import prepare
            throughput_plan = prepare(args.throughput_config, dataset_manifest=str(args.dataset_manifest),
                                      dataset_sha256=args.dataset_sha256)
            require(throughput_plan.record["model"]["model_id"] == {
                "qwen3-1.7b-base": "Qwen/Qwen3-1.7B-Base", "qwen3-4b-base": "Qwen/Qwen3-4B-Base",
                "qwen3-8b-base": "Qwen/Qwen3-8B-Base"}[reservation["model_key"]], "Throughput model differs from reserved model.")
        fresh, authority = native_setup()
        owner = fresh()
        goals = tuple(render_goals(owner.state))
        environment = authority_prompt_environment(False, CapabilityIdentity(
            authority.label, tuple(sorted(authority.allowed_commands)), ()))
        primitive_prompt = render_prompt(goals=goals, focus=0, environment=environment)
        load_started = time.monotonic()
        session = load_torch_model(reservation["model_key"], base_directory=args.base_directory,
            adapter_directory=args.adapter_directory, adapter_manifest_sha256=args.adapter_manifest_sha256,
            adapter_kind=args.adapter_kind, reservation_check=checker, should_stop=stop,
            limits=SessionLimits(max_calls=2, max_token_slots=512), seed=0)
        torch = session.torch
        torch.cuda.synchronize()
        data["cold_load_seconds"] = time.monotonic() - load_started
        data["load_peak_allocated_gpu_bytes"] = torch.cuda.max_memory_allocated()
        save(output / "model-admission.json", session.identity)
        policy = TorchPrimitivePolicy(session, environment)
        primitive_input_ids = session.encode(primitive_prompt)
        started = time.monotonic()
        candidates = policy.propose(goals, max_candidates=PRIMITIVE_BEAMS)
        torch.cuda.synchronize()
        primitive_seconds = time.monotonic() - started
        native = validate_native_candidates(candidates, fresh, authority, stop)
        primitive = {"schema": "hydra-p6-primitive-smoke-v1", "theorem": THEOREM,
            "authored_setup": PREFIX, "exact_goals_before": goals, "prompt": primitive_prompt,
            "input_token_ids": primitive_input_ids, "input_tokens": len(primitive_input_ids),
            "candidates": candidates, "actual_model_calls": policy.calls,
            "generated_token_slots": policy.generated_tokens, "sequences_rejected_by_authority": policy.rejected,
            "raw_rejected_sequences_retained": False,
            "raw_omission_reason": "The frozen primitive provider exposes validated candidates and rejection count only.",
            "native_checks": native, "decode_seconds": primitive_seconds,
            "peak_allocated_gpu_bytes": torch.cuda.max_memory_allocated(),
            "provider_identity": policy.evaluation_identity}
        save(output / "primitive.json", primitive)
        nodes, depth = proof_metrics(owner.state.partial)
        objects, _, _ = proof_identity_metrics(owner.state.partial)
        context = PlannerContext(owner.original_target, owner.original_names, owner.state.goals,
            CapabilitySnapshot.from_native(authority), kernel_sha, remaining={"depth": 32,
            "tactic_attempts": 64, "imports": 0, "model_calls": 1, "vampire_calls": 0},
            certificate_cost={"partial_structural_occurrences": nodes, "partial_distinct_objects": objects,
                              "partial_proof_depth": depth})
        backend = TorchPlannerBackend(session, allow_primitive_adapter=args.adapter_directory is not None)
        recording = RecordingPlanner(backend)
        provider = PlannerProvider(recording, max_calls=1, max_total_generated_tokens=PLANNER_TOKENS)
        started = time.monotonic()
        batch = provider.propose(context, model_calls_remaining=1, generated_tokens_remaining=PLANNER_TOKENS,
                                 max_proposals=2, should_stop=stop)
        torch.cuda.synchronize()
        planner_seconds = time.monotonic() - started
        planner = {"schema": "hydra-p6-planner-smoke-v1", "status": batch.status, "detail": batch.detail,
            "prompt": recording.prompt, "input_token_ids": recording.input_ids,
            "raw_output_token_ids": recording.output_ids, "raw_output_text": recording.output_text,
            "input_tokens": batch.input_tokens, "actual_model_calls": batch.actual_model_calls,
            "generated_tokens": batch.generated_tokens, "decode_seconds": planner_seconds,
            "plans": [{"commands": plan.commands, "source": plan.source, "reason": plan.reason,
                       "plan_sha256": plan.plan_sha256, "ast_nodes": plan.ast_nodes,
                       "introduces_open_obligations": plan.introduces_open_obligations} for plan in batch.plans],
            "typed_compile_valid": batch.status == "proposals", "native_plan_executed": False,
            "kernel_checked": False, "planner_trained": False, "library_imports": 0,
            "peak_allocated_gpu_bytes": torch.cuda.max_memory_allocated(), "provider": provider.report()}
        save(output / "planner.json", planner)
        data["decoders"] = {"primitive": {"actual_model_calls": policy.calls,
            "native_accepted": sum(row["native_step_accepted"] for row in native),
            "kernel_proofs": sum(row["kernel_checked"] for row in native)},
            "planner": {"actual_model_calls": batch.actual_model_calls, "status": batch.status}}
        data["inference_peak_allocated_gpu_bytes"] = torch.cuda.max_memory_allocated()
        data["inference_peak_reserved_gpu_bytes"] = torch.cuda.max_memory_reserved()
        if args.throughput_examples:
            from hydra_training_v5 import decision_pilot
            helper = getattr(decision_pilot, "probe_completion_gradients", None)
            require(callable(helper), "The reviewed bounded completion-gradient helper is unavailable.")
            require(not stop(), "No throughput time remains.")
            try:
                throughput = helper(throughput_plan, model=session.model, tokenizer=session.tokenizer,
                    model_identity=session.identity,
                    max_examples=args.throughput_examples, max_seconds=min(120, max(1, int(deadline-time.monotonic())-10)),
                    disposable_model=True, should_stop=stop)
            except BaseException as failure:
                partial = getattr(failure, "probe_record", None)
                if type(partial) is dict:
                    save(output / "throughput.json", partial)
                raise
            torch.cuda.synchronize()
            save(output / "throughput.json", throughput)
            data["throughput"] = {"status": "executed", "record": "throughput.json", "optimizer_updates": 0}
        else:
            data["throughput"] = {"status": "not_requested", "examples": 0, "optimizer_updates": 0}
        data["session"] = session.report()
        data["peak_allocated_gpu_bytes"] = max(data["inference_peak_allocated_gpu_bytes"], torch.cuda.max_memory_allocated())
        data["peak_reserved_gpu_bytes"] = max(data["inference_peak_reserved_gpu_bytes"], torch.cuda.max_memory_reserved())
        require(session.calls == 2, "The smoke did not perform its two distinct actual decoder calls.")
        completed = True
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:1000]}
        if session is not None:
            data["session"] = session.report()
        raise
    finally:
        # No inference follows the optional disposable gradient probe.
        session = policy = backend = recording = provider = None
        gc.collect()
        if torch is not None:
            torch.cuda.empty_cache()
        after = source_pins(app)
        unchanged = before == after
        signal.alarm(0)
        result = {"schema": "hydra-p6-remote-smoke-completion-v1", "completed": completed and unchanged,
            "error": error, "source_pins_after": after, "sources_unchanged": unchanged,
            "elapsed_seconds": time.monotonic() - began, "last_live_allocation": checker.last,
            "scheduler_calls": checker.calls, "model_disposal_attempted": True,
            "native_kernel_identity": kernel_sha, "model_trained_by_probe": False,
            "optimizer_updates": 0, "automatic_retry": False, "vampire_calls": 0,
            "transport_and_inference_passed": completed and unchanged,
            "proof_success_is_separate": True, **data}
        save(output / "completion.json", result)
        require(sum(path.stat().st_size for path in output.iterdir() if path.is_file()) <= MAX_OUTPUT_BYTES,
                "Smoke evidence exceeded its fixed total output budget.")
        print(json.dumps({key: result[key] for key in ("completed", "elapsed_seconds", "sources_unchanged",
                         "transport_and_inference_passed", "optimizer_updates", "error")}), flush=True)
    require(completed and unchanged, "Smoke did not complete with unchanged source pins.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--reservation", type=Path, required=True)
    parser.add_argument("--reservation-sha256", required=True)
    parser.add_argument("--base-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--adapter-directory", type=Path)
    parser.add_argument("--adapter-manifest-sha256")
    parser.add_argument("--adapter-kind", choices=("fresh_decision_pilot", "historical_retention"), default="fresh_decision_pilot")
    parser.add_argument("--throughput-examples", type=int, choices=range(0, 9), default=0)
    parser.add_argument("--throughput-config", type=Path)
    parser.add_argument("--dataset-manifest", type=Path)
    parser.add_argument("--dataset-sha256")
    args = parser.parse_args()
    try:
        return run(args)
    except BaseException as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__,
                          "error": str(error)[:1000], "automatic_retry": False}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
