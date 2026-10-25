"""Explicit, sequential local MLX candidate gate; never imported by the website.

Run with hydra-playground/.runtime/venv/bin/python3 -I -B only after the parent
authorizes the local runtime check. CLI pins must come from the actual completed
GPU comparison/export. No downloads, training, retries, fallback, or promotion.
One model is loaded (120 s separate loading ceiling); each case retains the
comparison's 30 s budget, with a 45 s SIGALRM cap including native proof replay.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
WORK = HERE.parent.parent
REPO = WORK.parent.parent
FROZEN = WORK / "comparison-01/latent-source"
SEARCH_LIMITS = {"max_depth": 96, "max_states": 2048, "max_tactic_attempts": 6000,
                 "max_expansions": 384, "max_frontier": 128, "candidates_per_state": 48,
                 "max_macro_steps": 8, "closure_steps": 16, "heuristic_burst": 8,
                 "max_model_calls": 16, "max_vampire_calls": 0, "wall_seconds": 30}
PROVIDER_LIMITS = {"max_calls": 16, "max_new_tokens": 128, "max_total_decision_tokens": 4096,
                   "max_context_tokens": 6144, "provider_seconds": 30}
LOAD_SECONDS, HARD_CASE_SECONDS, FINALIZE_SECONDS = 120, 45, 60
# These two files are outside the ordinary local search/replay dependency path.
# Their actual bytes remain recorded and immutable; importing either is forbidden.
UNUSED_APP_EXCLUSIONS = {
    "hydra-playground/publish_showcase.py": "Unused website publisher; this check never publishes or changes the website.",
    "hydra-playground/experimental_model.py": "Unused experimental Torch backend; this check uses only the ordinary MLX runtime.",
}


class HardDeadline(BaseException):
    """Cannot be swallowed as an ordinary adviser exception by hybrid search."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fingerprint(path, expected=None, maximum=4 * 1024 * 1024):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= maximum,
            "missing, linked, or oversized input: " + str(path))
    raw = path.read_bytes()
    pin = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    require(expected is None or pin["sha256"] == expected, "input hash differs: " + str(path))
    return pin


def read_json(path, expected):
    pin = fingerprint(path, expected)
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate metadata key")
            result[key] = value
        return result
    def invalid(_):
        raise ValueError("non-finite metadata")
    value = json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=invalid)
    require(fingerprint(path) == pin and type(value) is dict, "metadata changed or is not an object")
    return value


def local_app_source_pins(study, repo):
    app_pins = {name: pin for name, pin in study["hydra_source_files"].items()
                if Path(name).parent == Path("hydra-playground") and Path(name).suffix == ".py"}
    require({"hydra-playground/worker.py", "hydra-playground/model_runtime.py",
             "hydra-playground/hybrid_search.py", *UNUSED_APP_EXCLUSIONS} <= set(app_pins),
            "missing frozen native host entrypoints or explicit unused modules")
    source_pins, exclusions = {}, {}
    for name, expected in app_pins.items():
        path = Path(repo) / name
        actual = fingerprint(path, None if name in UNUSED_APP_EXCLUSIONS else expected)
        source_pins[str(path)] = actual
        if name in UNUSED_APP_EXCLUSIONS:
            exclusions[name] = {"expected_source07_sha256": expected, "actual": actual,
                                "reason": UNUSED_APP_EXCLUSIONS[name], "must_remain_unimported": True}
    return source_pins, exclusions


def assert_unused_source_modules():
    filenames = {Path(name).name for name in UNUSED_APP_EXCLUSIONS}
    stems = {Path(name).stem for name in UNUSED_APP_EXCLUSIONS}
    for name, module in tuple(sys.modules.items()):
        location = getattr(module, "__file__", None)
        require(not (set(name.split(".")) & stems)
                and not (type(location) is str and Path(location).name in filenames),
                "excluded unused publisher/experimental module was imported: " + name)


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def alarm(*_):
    raise HardDeadline("signal wall-time ceiling reached")


def offline_guard(event, _args):
    if event == "import" and set(str(_args[0]).split(".")) & {Path(name).stem for name in UNUSED_APP_EXCLUSIONS}:
        raise RuntimeError("unused publisher/experimental modules are forbidden in ordinary local checks")
    if event.startswith("socket."):
        raise OSError("local candidate check is offline")
    if event.startswith("subprocess.") or event in {
        "os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"}:
        raise RuntimeError("candidate check may not start another process/model")


def fresh_policy(loaded, policy_type, deadline):
    policy = policy_type(backend=loaded.backend, tokenizer=loaded.tokenizer,
        kind=loaded.kind, environment=loaded.environment, provenance=loaded.provenance,
        render_prompt=loaded.render_prompt, strict_generation=loaded.strict_generation,
        check_prompt_binding=loaded.check_prompt_binding, validate_tactic=loaded.validate_tactic,
        limits=loaded.limits, deadline_monotonic=deadline)
    policy.evaluation_identity = copy.deepcopy(loaded.evaluation_identity)
    return policy


def validate_replay(result, replay, theorem, worker):
    require(result["kernel_checked"] is True and replay["status"] == "proved"
            and replay["kernel_checked"] is True and not replay["goals"], "native replay failed")
    require(replay["theorem"] == replay["original_theorem"] == theorem
            and replay["commands"] == result["commands"] and replay["classical"] is False
            and "experimental" not in replay and replay["kernel_source_commit"] == worker.SOURCE_COMMIT,
            "replay target, authority, or source differs")
    steps = [row for row in replay["trace"] if "v" in row]
    require(replay["trace"][-1].get("qed") is True
            and replay["trace"][-1].get("theorem") == theorem
            and replay["tactics_applied"] == replay["tactics_requested"] == len(result["commands"]) == len(steps)
            and replay["failed_tactics"] == 0 and replay["failed_step"] is None and replay["error"] is None
            and all(step.get("status") == "ok" and step.get("error") is None for step in steps),
            "replay did not close with complete successful tactic accounting")


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("study", "study-sha256", "inputs", "inputs-sha256", "export", "export-sha256",
                 "checkpoint-sha256", "training-receipt", "training-receipt-sha256", "arm-receipt",
                 "arm-receipt-sha256", "run-id", "loader-sha256", "provider-sha256", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--export-bytes", type=int, required=True)
    parser.add_argument("--selected-step", type=int, required=True)
    parser.add_argument("--case", "--case-id", action="append", required=True, dest="case_ids")
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode, "invoke the existing runtime Python with -I -B")
    require(sys.platform == "darwin", "this gate is for the explicit local Apple Silicon runtime")
    for key, value in vars(args).items():
        if key.endswith("sha256"):
            require(re.fullmatch("[0-9a-f]{64}", value) is not None, "invalid SHA-256: " + key)
    require(1 <= len(args.case_ids) <= 32 and len(set(args.case_ids)) == len(args.case_ids),
            "select 1..32 distinct panel cases explicitly")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {"schema": "hydra-local-upgrade-arm-v1", "arm": args.run_id + "_local_mlx",
               "status": "starting", "training": False,
               "automatic_retry": False, "promotion_performed": False, "parallel_models": False,
               "started_utc": datetime.now(timezone.utc).isoformat(), "arguments": vars(args),
               "search_limits": SEARCH_LIMITS, "provider_limits": PROVIDER_LIMITS,
               "load_seconds_ceiling": LOAD_SECONDS, "hard_case_seconds": HARD_CASE_SECONDS,
               "finalization_seconds_ceiling": FINALIZE_SECONDS,
               "proof_admission_requires_completed_run_receipt": True,
               "scope": "quantized MLX local integration gate; not held-out quality or BF16 equivalence",
               "cases": [], "runner": fingerprint(__file__)}
    loaded, fatal_run = None, None
    signal.signal(signal.SIGALRM, alarm)
    try:
        signal.setitimer(signal.ITIMER_REAL, LOAD_SECONDS)
        study = read_json(args.study, args.study_sha256)
        inputs = read_json(args.inputs, args.inputs_sha256)
        training = read_json(args.training_receipt, args.training_receipt_sha256)
        arm_receipt = read_json(args.arm_receipt, args.arm_receipt_sha256)
        require(study["schema"] == "hydra-model-upgrade-comparison-v1"
                and study["search_limits"] == SEARCH_LIMITS and study["provider_limits"] == PROVIDER_LIMITS,
                "comparison search/provider budgets differ; no implicit budget changes")
        arm = study["arms"][args.run_id]
        require(arm["kind"] == "latent_compact_v3" and arm["selected_step"] == args.selected_step
                and arm["checkpoint_sha256"] == args.checkpoint_sha256
                and study["payload_files"][arm["receipt"]] == args.training_receipt_sha256
                and study["payload_files"]["inputs.json"] == args.inputs_sha256,
                "candidate or panel differs from the pinned GPU study")
        cases = inputs["cases"]
        require(inputs["schema"] == "hydra-model-upgrade-panel-search-inputs-v1" and len(cases) == 32
                and all(type(case) is dict and set(case) == {"id", "theorem"}
                        and type(case["id"]) is str and re.fullmatch("[a-zA-Z0-9_-]+", case["id"])
                        and type(case["theorem"]) is str and 0 < len(case["theorem"].encode()) <= 8192
                        for case in cases), "unexpected frozen comparison panel")
        by_id = {case["id"]: case for case in cases}
        require(len(by_id) == 32 and set(args.case_ids) <= set(by_id), "unknown or duplicate panel IDs")
        require(arm_receipt["schema"] == "hydra-upgrade-arm-v1" and arm_receipt["status"] == "completed"
                and arm_receipt["arm"] == args.run_id and arm_receipt["training"] is False
                and arm_receipt["automatic_retry"] is False and arm_receipt["study_sha256"] == args.study_sha256
                and arm_receipt["checkpoint_sha256"] == args.checkpoint_sha256
                and arm_receipt["exported_lora_sha256"] == args.export_sha256
                and arm_receipt["cases_completed"] == 32
                and [row["case_id"] for row in arm_receipt["cases"]] == list(by_id),
                "requires the actual completed, matching 32-case GPU arm/export receipt")
        frozen_pins = training["identity"]["sources_sha256"]
        modules = {p.relative_to(FROZEN).as_posix(): p for p in (FROZEN / "src/latentproof").glob("*.py")}
        require(len(frozen_pins) == 20 and set(modules) == set(frozen_pins), "frozen module inventory differs")
        source_pins = {str(path): fingerprint(path, frozen_pins[name]) for name, path in modules.items()}
        source_pins[str(HERE / "hydra_mlx_vanilla.py")] = fingerprint(HERE / "hydra_mlx_vanilla.py", args.loader_sha256)
        source_pins[str(HERE / "hydra_torch_candidate.py")] = fingerprint(HERE / "hydra_torch_candidate.py", args.provider_sha256)
        app_pins, exclusions = local_app_source_pins(study, REPO)
        source_pins.update(app_pins)
        receipt["unused_module_exclusions"] = exclusions
        receipt["source_files"] = source_pins
        sys.path[:0] = [str(HERE), str(REPO / "hydra-playground"), str(FROZEN / "src")]
        assert_unused_source_modules()
        sys.addaudithook(offline_guard)
        import worker
        import model_runtime as trained
        from hydra_mlx_vanilla import LocalCandidateSpec, load_local_policy
        from hydra_torch_candidate import CandidatePolicy, Limits
        from latentproof import qwen_data, qwen_eval
        require(all(Path(sys.modules[name].__file__).resolve().is_relative_to(FROZEN)
                    for name in ("latentproof", "latentproof.qwen_data", "latentproof.qwen_eval")),
                "imported a different latent source")
        worker.load_kernel()
        from hybrid_search import search, HybridLimits
        from peano_lab.ui.prove import SurfaceCapabilities
        spec = LocalCandidateSpec(export_path=Path(args.export), export_bytes=args.export_bytes,
            export_sha256=args.export_sha256, checkpoint_sha256=args.checkpoint_sha256,
            training_receipt_path=Path(args.training_receipt), training_receipt_sha256=args.training_receipt_sha256,
            arm_receipt_path=Path(args.arm_receipt), arm_receipt_sha256=args.arm_receipt_sha256,
            selected_step=args.selected_step, run_id=args.run_id)
        loaded = load_local_policy(trained=trained, spec=spec, frozen_data=qwen_data, frozen_eval=qwen_eval,
                                   limits=Limits(**PROVIDER_LIMITS))
        receipt["model_load_and_admission_seconds"] = time.monotonic() - started
        receipt["model_identity"] = copy.deepcopy(loaded.evaluation_identity)
        cap = loaded.environment.capabilities
        capabilities = SurfaceCapabilities(label=cap.label, allowed_commands=frozenset(cap.allowed_commands),
                                           allowed_theorems=frozenset())
        signal.setitimer(signal.ITIMER_REAL, 0)
        for case_id in args.case_ids:
            case = by_id[case_id]
            case_started = time.monotonic()
            deadline = case_started + SEARCH_LIMITS["wall_seconds"]
            policy = fresh_policy(loaded, CandidatePolicy, deadline)
            record = {"case_id": case_id, "theorem": case["theorem"], "status": "started", "proved": False,
                      "candidate_finalization_scope": "completed run receipt required"}
            signal.setitimer(signal.ITIMER_REAL, HARD_CASE_SECONDS)
            fatal = None
            try:
                result = search(case["theorem"], capabilities=capabilities, model_policy=policy,
                                limits=HybridLimits(**SEARCH_LIMITS))
                record.update(search=result, status=result["status"])
                failures = [row for row in policy.report()["attempts"]
                            if row["status"] == "failed" and row.get("error_type") != "TimeoutError"]
                require(not failures and not any(row.get("kind") == "model_error" for row in result.get("diagnostics", [])),
                        "provider infrastructure error; not a model-quality result")
                if result["status"] == "proof":
                    if time.monotonic() >= deadline:
                        raise TimeoutError("30 s case budget expired before replay")
                    replay = worker.replay({"theorem": case["theorem"], "tactics": result["commands"]})
                    record["independent_replay"] = replay
                    validate_replay(result, replay, case["theorem"], worker)
                    if time.monotonic() >= deadline:
                        raise TimeoutError("native proof replay exceeded the 30 s case budget")
                    record["proved"] = True
            except TimeoutError as error:
                record.update(status="timeout", proved=False, error_type=type(error).__name__, error=str(error))
            except HardDeadline as error:
                fatal = error
                record.update(status="timeout", proved=False, error_type=type(error).__name__, error=str(error))
            except BaseException as error:
                fatal = error
                record.update(status="infrastructure_error", proved=False, error_type=type(error).__name__, error=str(error))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                record["provider"] = policy.report()
                record["wall_seconds"] = time.monotonic() - case_started
                save(out / (case_id + ".json"), record)
                receipt["cases"].append({key: record[key] for key in ("case_id", "status", "proved", "wall_seconds")})
                print(json.dumps(receipt["cases"][-1]), flush=True)
            if fatal is not None:
                raise fatal
        receipt.update(status="cases_finished_pending_finalization", cases_completed=len(receipt["cases"]),
                       actual_model_calls=sum(read_json(out / (row["case_id"] + ".json"), None)["provider"]["actual_model_calls"]
                                              for row in receipt["cases"]))
    except BaseException as error:
        fatal_run = error
        receipt.update(status="failed", error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if loaded is not None:
            finalize_started = time.monotonic()
            try:
                # Rehash custody once, outside proof timers; do no additional model/native work.
                signal.setitimer(signal.ITIMER_REAL, FINALIZE_SECONDS)
                receipt["loaded_policy_finalization"] = loaded.finalize()
                assert_unused_source_modules()
                for path, pin in source_pins.items():
                    require(fingerprint(path) == pin, "source changed during candidate check: " + path)
                for path, pin in ((args.study, args.study_sha256), (args.inputs, args.inputs_sha256)):
                    fingerprint(path, pin)
                receipt["candidate_finalized"] = True
                if fatal_run is None:
                    receipt["status"] = "completed"
            except BaseException as error:
                fatal_run = error
                receipt.update(status="failed", candidate_finalized=False,
                               finalize_error_type=type(error).__name__, finalize_error=str(error))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                receipt["finalization_seconds"] = time.monotonic() - finalize_started
        receipt["wall_seconds"] = time.monotonic() - started
        receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(out / "receipt.json", receipt)
    if fatal_run is not None:
        raise fatal_run


if __name__ == "__main__":
    main()
