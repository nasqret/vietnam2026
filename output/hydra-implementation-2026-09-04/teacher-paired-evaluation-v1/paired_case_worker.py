"""One reserved case, one cold model construction, no training or retry.

All project/model/native imports are inside run(), after exact source, one-use
parent authority, Slurm identity, resource and input checks. CLI is not a search
service: only a parent-produced, hash-bound case request can enter it.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import resource
import signal
import sys
import time

from paired_common import (FEATURES, MODEL_LIMITS, ORIGINAL, PROVIDER_SHA, RESOURCE_LIMITS,
    WALL_PROFILES, canonical, case_payload, native_identity, ordinary, pin,
    proof_acceptance, require, save, source_pins, strict_json, study_spec,
    training_exposure, validate_counts, valid_sha)
from paired_controller import (HERE, SLICE_SHA, reservation_spec, scheduler_helpers,
                               selected_cases)


def append_event(path, record, *, maximum=4 * 1024**2):
    raw = canonical(record) + b"\n"
    size = path.stat().st_size if path.exists() else 0
    require(len(raw) <= 160 * 1024 and size + len(raw) <= maximum, "Bounded event evidence is full.")
    with path.open("ab") as stream:
        stream.write(raw)


def check_gpu_memory(session):
    if (session.torch.cuda.max_memory_allocated() > RESOURCE_LIMITS["gpu_observed_bytes"]
            or session.torch.cuda.max_memory_reserved() > RESOURCE_LIMITS["gpu_observed_bytes"]):
        raise MemoryError("Observed GPU allocator peak exceeded its fixed post-load/call ceiling.")


def check_deadline(should_stop, message):
    if should_stop():
        raise TimeoutError(message)


class RecordingPolicy:
    """Transparent actual-provider accounting; never adds a tactic or retries."""
    def __init__(self, policy, environment, output, should_stop):
        self.policy, self.environment, self.output, self.should_stop = policy, environment, output, should_stop
        self.requests = 0
        self.decode_seconds = 0.0

    @property
    def calls(self):
        return self.policy.calls

    def propose(self, goals_before, *, max_candidates):
        require(max_candidates == MODEL_LIMITS["candidate_width"] and self.requests < MODEL_LIMITS["calls"],
                "Search changed its shared proposal-width/request allowance.")
        check_deadline(self.should_stop, "Case search deadline reached before model input.")
        from hydra_training_v5.peano_policy.prompt import render_prompt
        prompt = render_prompt(goals=goals_before, focus=0, environment=self.environment)
        session = self.policy.session
        before = session.report()
        started = time.monotonic()
        self.requests += 1
        candidates = None
        error = None
        try:
            candidates = self.policy.propose(goals_before, max_candidates=max_candidates)
            session.torch.cuda.synchronize()
            check_gpu_memory(session)
            return candidates
        except BaseException as failure:
            error = {"type": type(failure).__name__, "detail": str(failure)[:1000]}
            raise
        finally:
            elapsed = time.monotonic() - started
            self.decode_seconds += elapsed
            after = session.report()
            append_event(self.output / "model-calls.jsonl", {
                "request": self.requests, "ordered_goals_sha256": sha256(canonical(goals_before)).hexdigest(),
                "ordered_goal_count": len(goals_before), "prompt": prompt,
                "prompt_sha256": sha256(prompt.encode()).hexdigest(),
                "candidate_width": max_candidates, "accepted_candidates": candidates,
                "error": error, "provider_wall_seconds": elapsed,
                "actual_generation_calls_before": before["actual_model_calls"],
                "actual_generation_calls_after": after["actual_model_calls"],
                "actual_token_slots_after": after["generated_token_slots"],
                "actual_forward_passes_after": after["forward_passes"],
                "rejected_sequences_total": self.policy.rejected,
                "invalid_raw_sequences": "not exposed by the frozen primitive provider; count retained"})


def run(args):
    began = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (RESOURCE_LIMITS["cpu_seconds"], RESOURCE_LIMITS["cpu_seconds"] + 1))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (RESOURCE_LIMITS["case_file_bytes"], RESOURCE_LIMITS["case_file_bytes"]))
    require(platform.system() == "Linux" and platform.machine() == "aarch64"
            and sys.version_info[:3] == (3, 13, 5) and not sys.flags.ignore_environment
            and os.environ.get("PYTHONHASHSEED") == "0", "Wrong fixed remote runtime or process hash seed.")
    raw = ordinary(args.request, 65536)
    require(valid_sha(args.request_sha256) and sha256(raw).hexdigest() == args.request_sha256,
            "Case request bytes changed.")
    request = strict_json(raw)
    fields = {"schema", "app_root", "study_path", "study_sha256", "reservation_path",
              "reservation_sha256", "controller_pid", "case_index", "input"}
    require(set(request) == fields and request["schema"] == "hydra-paired-case-request-v1"
            and type(request["controller_pid"]) is int and request["controller_pid"] == os.getppid(),
            "Case worker is not under its exact controller parent.")
    app = Path(request["app_root"]).resolve(strict=True)
    output = args.request.absolute().parent
    require(output.resolve() == output and not output.is_symlink(), "Case output escapes through a link.")
    study_raw = ordinary(request["study_path"])
    require(sha256(study_raw).hexdigest() == request["study_sha256"], "Study changed in transit.")
    study = study_spec(strict_json(study_raw), SLICE_SHA)
    reservation_path = Path(request["reservation_path"])
    reservation_raw = ordinary(reservation_path, 65536)
    require(sha256(reservation_raw).hexdigest() == request["reservation_sha256"], "Reservation changed in transit.")
    reservation = reservation_spec(strict_json(reservation_raw), study, request["study_sha256"])
    claim = strict_json(ordinary(reservation_path.with_name(reservation_path.name + ".claimed"), 65536))
    require(claim.get("schema") == "hydra-paired-reservation-consumption-v1"
            and claim.get("pid") == os.getppid() and claim.get("reservation_sha256") == request["reservation_sha256"]
            and claim.get("study_sha256") == request["study_sha256"] and claim.get("arm") == reservation["arm"]
            and output.parent == Path(claim.get("output", "")), "Missing exact consumed parent allocation.")
    cases = selected_cases(app, study)
    index = request["case_index"]
    require(type(index) is int and 0 <= index < len(cases) and output.name == f"case-{index:02d}"
            and canonical(request["input"]) == canonical(case_payload(cases[index], study["wall_profile"])),
            "Case worker received extra information or a different theorem/settings.")
    before = source_pins(app)
    source_sha = sha256(canonical(before)).hexdigest()
    require(source_sha == study["source_pins_sha256"], "Full frozen executed source scope differs.")
    require(pin(__file__)["sha256"] == reservation["case_worker_sha256"], "Worker escaped its reserved source pin.")
    save(output / "case-started.json", {"schema": "hydra-paired-case-consumption-v1",
        "request_sha256": args.request_sha256, "pid": os.getpid(), "controller_pid": os.getppid(),
        "case_index": index, "automatic_retry": False, "resume": False})
    helpers = scheduler_helpers()
    class CaseReservation(helpers.LiveReservation):
        def __call__(self):
            require(self.calls < RESOURCE_LIMITS["child_scheduler_calls"], "Case scheduler query cap reached.")
            return super().__call__()
    checker = CaseReservation(reservation, output)
    first = checker()
    profile = WALL_PROFILES[study["wall_profile"]]
    deadline = [began + profile["load_seconds"]]
    phase = ["load"]
    def stop():
        return time.monotonic() >= deadline[0]
    def interrupted(signum, frame):
        raise TimeoutError("Bounded case " + phase[0] + " phase stopped; no retry.")
    signal.signal(signal.SIGALRM, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    def set_phase(name, seconds):
        phase[0] = name
        deadline[0] = min(began + profile["case_seconds"] - 1, time.monotonic() + seconds)
        signal.setitimer(signal.ITIMER_REAL, max(0.001, deadline[0] - time.monotonic()))
        append_event(output / "progress.jsonl", {"phase": name, "elapsed_seconds": time.monotonic() - began})
    # Startup/source admission is charged to load, rather than receiving another allowance.
    set_phase("load", max(0.001, began + profile["load_seconds"] - time.monotonic()))
    session = policy = wrapped = None
    search_result = replay = None
    identity = None
    original = None
    actual_counters = None
    error = None
    status = "infrastructure_failure"
    source_after_sha = None
    cold_seconds = replay_seconds = None
    exposure = None
    exposure_admission = None
    teacher_admission_seconds = None
    kernel = None
    progress_events = 0
    try:
        kernel = native_identity(app)
        os.chdir(app.parent)
        sys.path[:0] = [str(app), str(app / "native-v7"), str(app.parent / ORIGINAL), str(app / "training-v5")]
        from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
        from peano_lab.ui.prove import SurfaceCapabilities
        from training.peano_hydra.protocol import validate_statement
        from hybrid_search import HybridLimits, search
        original = validate_statement(request["input"]["theorem"])
        capabilities = SurfaceCapabilities(label="hydra-authority-no-imports-v1",
            allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
        arm = reservation["arm"]
        descriptor = study["arms"][arm]
        if descriptor is not None:
            from experimental_model import load_torch_model, TorchPrimitivePolicy, SessionLimits
            from hydra_training_v5.peano_policy.contract import authority_prompt_environment
            from hydra_training_v5.peano_policy.prompt import CapabilityIdentity
            adapter_raw = ordinary(Path(descriptor["adapter_directory"]) / "manifest.json")
            require(sha256(adapter_raw).hexdigest() == descriptor["adapter_manifest_sha256"], "Selected adapter manifest changed.")
            if descriptor["adapter_kind"] == "fresh_decision_pilot":
                exposure = training_exposure(strict_json(adapter_raw))
                expected = study["fresh_training_exposure"]
                require(exposure == expected, "Fresh size arm has different data/steps/objective or holdout admission.")
            elif descriptor["adapter_kind"] == "teacher_augmented_pilot":
                from teacher_exposure import verify_admission
                require(arm == "distilled_1_7b", "Teacher exposure was assigned to an ordinary arm.")
                admission_started = time.monotonic()
                try:
                    exposure_admission = verify_admission(app.parent, study["teacher_admission"], strict_json(adapter_raw),
                        study["distilled_training_exposure"], should_stop=stop)
                finally:
                    teacher_admission_seconds = time.monotonic() - admission_started
                exposure = exposure_admission["teacher_exposure"]
                save(output / "teacher-admission.json", exposure_admission)
            model_started = time.monotonic()
            session = load_torch_model(descriptor["model_key"], base_directory=descriptor["base_directory"],
                adapter_directory=descriptor["adapter_directory"], adapter_manifest_sha256=descriptor["adapter_manifest_sha256"],
                adapter_kind="fresh_decision_pilot" if exposure_admission is not None else descriptor["adapter_kind"],
                reservation_check=checker, should_stop=stop,
                limits=SessionLimits(max_calls=MODEL_LIMITS["calls"], max_token_slots=MODEL_LIMITS["generated_token_slots"]),
                seed=MODEL_LIMITS["seed"])
            session.torch.cuda.synchronize()
            cold_seconds = time.monotonic() - model_started
            check_gpu_memory(session)
            identity = session.identity
            require(identity["source_sha256"] == PROVIDER_SHA and identity["adapter"]["saved_adapter_reload_checked"] is True,
                    "Real provider did not admit the exact saved adapter.")
            save(output / "model-admission.json", identity)
            environment = authority_prompt_environment(False, CapabilityIdentity(
                capabilities.label, tuple(sorted(capabilities.allowed_commands)), ()))
            policy = TorchPrimitivePolicy(session, environment)
            wrapped = RecordingPolicy(policy, environment, output, stop)
        check_deadline(stop, "Load/admission phase exhausted its allowance.")
        def progress(value):
            nonlocal progress_events
            require(progress_events < 2048, "Native progress event bound exceeded.")
            progress_events += 1
            append_event(output / "progress.jsonl", {"phase": "search", "event": progress_events,
                "elapsed_seconds": time.monotonic() - began, "native": value}, maximum=1024**2)
            check_deadline(stop, "Native search phase reached its finite deadline.")
        # The frozen search gets its exact cooperative work/wall cap. Two of
        # the fifteen completion seconds permit bounded return/serialization;
        # they do not increase HybridLimits or add new search iterations.
        set_phase("search", profile["search_seconds"] + profile["search_return_grace_seconds"])
        search_result = search(original, capabilities=capabilities, model_policy=wrapped,
            vampire_advisor=None, external_advisors=(), planner_enabled=False, planner_provider=None,
            branch_ranker=None, limits=HybridLimits(**request["input"]["settings"]["native_work"]),
            emit_progress=progress)
        set_phase("independent_replay", profile["replay_seconds"])
        session_report = None if session is None else session.report()
        policy_report = None if policy is None else {"calls": policy.calls, "generated_tokens": policy.generated_tokens}
        actual_counters = validate_counts(search_result, session_report, policy_report)
        if search_result["status"] == "proof":
            replay_started = time.monotonic()
            checked = run_proof(original, tuple(search_result["commands"]), request_id="paired-independent-original",
                                classical=False, on_error="stop", capabilities=capabilities)
            replay = checked.to_dict(include_trace=False)
            replay_seconds = time.monotonic() - replay_started
        proved = proof_acceptance(search_result, replay, original)
        status = "proved" if proved else "unknown"
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:1000], "phase": phase[0]}
        status = "resource_stop" if isinstance(failure, (TimeoutError, MemoryError)) else "infrastructure_failure"
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            source_after_sha = sha256(canonical(source_pins(app))).hexdigest()
            require(source_after_sha == source_sha, "Source changed while this case ran.")
        except BaseException as failure:
            status = "infrastructure_failure"
            error = {"type": type(failure).__name__, "detail": str(failure)[:1000], "phase": "source_verification"}
        # Exact generation counters are still available on ordinary failures;
        # native counters are incomplete if search did not return. A killed
        # process produces no such record and the parent keeps counters unknown.
        session_report = None if session is None else session.report()
        if actual_counters is None:
            actual_counters = {"actual_model_calls": 0 if session is None else session.calls,
                "generated_token_slots": 0 if session is None else session.generated_tokens,
                "forward_passes": 0 if session is None else session.forward_passes,
                "planner_calls": 0, "complete": False, "native_counters_complete": search_result is not None}
        gpu = None if session is None else {
            "peak_allocated_bytes": session.torch.cuda.max_memory_allocated(),
            "peak_reserved_bytes": session.torch.cuda.max_memory_reserved(),
            "scope": "Per-process observed allocator peaks; checked after load/decode, not a hard GPU memory sandbox"}
        value = {"schema": "hydra-paired-case-result-v1", "status": status,
            "request_sha256": args.request_sha256, "input_sha256": sha256(canonical(request["input"])).hexdigest(),
            "source_pins_sha256": source_sha, "source_pins_after_sha256": source_after_sha,
            "original_input_theorem": request["input"]["theorem"], "canonical_theorem": original,
            "kernel_identity": kernel, "features": FEATURES, "actual_counters": actual_counters,
            "search": search_result, "independent_original_replay": replay,
            "native_checked": status == "proved", "error": error,
            "model": session_report, "training_exposure": exposure, "teacher_exposure_admission": exposure_admission,
            "teacher_admission_seconds": teacher_admission_seconds,
            "model_policy": None if policy is None else {"identity": policy.evaluation_identity,
                "calls": policy.calls, "generated_tokens": policy.generated_tokens, "rejected_sequences": policy.rejected},
            "model_construction_seconds": cold_seconds,
            "model_construction_scope": "New process and loaded model each case; OS/HF disk cache may be warm",
            "post_load_provider_seconds": None if wrapped is None else wrapped.decode_seconds,
            "additional_replay_seconds": replay_seconds, "gpu_memory": gpu,
            "host_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "cpu_user_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "cpu_system_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            "elapsed_seconds": time.monotonic() - began, "last_live_allocation": checker.last,
            "scheduler_calls": checker.calls, "optimizer_updates": 0, "planner_calls": 0,
            "external_solver_calls": 0, "automatic_retry": False, "resume": False,
            "training_allowed": False, "retrieval_allowed": False,
            "model_memory_released_by": "Owned process exit and parent-confirmed group quiescence"}
        save(output / "case-result.json", value)
    return 0 if status in {"proved", "unknown"} else (3 if status == "resource_stop" else 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    try:
        return run(parser.parse_args())
    except BaseException as failure:
        print(canonical({"status": "failed", "type": type(failure).__name__,
                         "detail": str(failure)[:1000], "automatic_retry": False}).decode(), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
