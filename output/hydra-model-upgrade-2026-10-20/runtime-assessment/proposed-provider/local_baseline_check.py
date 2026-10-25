"""Sequential local comparison of the unchanged historical MLX Hydra provider.

Run only as an explicit local evaluation with the existing runtime Python -I -B.
One old model is loaded; each selected frozen panel case gets fresh counters.
No training, downloads, retries, fallback, live routing or model replacement.
The old beam4 / 64-decision / 1536-prompt decoder is deliberately unchanged.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import signal
import sys
import time
import traceback


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent.parent


def fresh_historical_policy(loaded, wrapper_type, trained, capabilities):
    """New existing wrapper/provider objects, sharing only immutable weights."""
    wrapper = wrapper_type(capabilities, lambda _event: None)
    shared = loaded.policy
    wrapper.identity = copy.deepcopy(loaded.identity)
    wrapper.load_attempted = True
    wrapper.policy = trained._MLXCandidatePolicy(
        shared.model, shared.tokenizer, shared.mx, shared.environment,
        copy.deepcopy(shared.evaluation_identity["model"]), wrapper._policy_progress)
    # This fresh wrapper has no independent load snapshot. The original loaded
    # wrapper owns the single mandatory final custody check for the entire run.
    return wrapper


def provider_report(wrapper):
    stats = wrapper.finalize()  # Fresh wrapper has no snapshot: counters only.
    return {**stats, "identity": copy.deepcopy(wrapper.identity),
            "actual_model_calls": stats["model_calls"],
            "generated_token_slots": None,
            "token_slot_accounting": "not exposed by unchanged historical beam decoder; no estimate",
            "kernel_checked": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("study", "study-sha256", "inputs", "inputs-sha256", "helper-sha256", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--case", "--case-id", action="append", required=True, dest="case_ids")
    args = parser.parse_args()
    if not (sys.flags.isolated and sys.dont_write_bytecode and sys.platform == "darwin"):
        raise ValueError("use the existing local runtime Python with -I -B")
    for key, value in vars(args).items():
        if key.endswith("sha256") and not re.fullmatch("[0-9a-f]{64}", value):
            raise ValueError("invalid SHA-256: " + key)
    helper_path = HERE / "local_candidate_check.py"
    if helper_path.is_symlink() or not helper_path.is_file() or helper_path.stat().st_size > 128 * 1024:
        raise ValueError("missing, linked or oversized shared local-check helper")
    if hashlib.sha256(helper_path.read_bytes()).hexdigest() != args.helper_sha256:
        raise ValueError("shared local-check helper hash differs")
    sys.path.insert(0, str(HERE))
    from local_candidate_check import (
        SEARCH_LIMITS, LOAD_SECONDS, HARD_CASE_SECONDS, FINALIZE_SECONDS,
        HardDeadline, alarm, fingerprint, read_json, save, require, offline_guard, validate_replay,
        local_app_source_pins, assert_unused_source_modules,
    )
    require(1 <= len(args.case_ids) <= 32 and len(set(args.case_ids)) == len(args.case_ids),
            "select 1..32 distinct panel cases explicitly")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {"schema": "hydra-local-upgrade-arm-v1", "arm": "historical_local_mlx",
               "status": "starting", "training": False, "automatic_retry": False,
               "promotion_performed": False, "parallel_models": False,
               "started_utc": datetime.now(timezone.utc).isoformat(), "arguments": vars(args),
               "search_limits": SEARCH_LIMITS,
               "provider_limits": {"decoder_beam_width": 4, "max_new_tokens": 64,
                                   "max_prompt_tokens": 1536, "max_model_calls": 16},
               "load_seconds_ceiling": LOAD_SECONDS, "hard_case_seconds": HARD_CASE_SECONDS,
               "finalization_seconds_ceiling": FINALIZE_SECONDS,
               "scope": "unchanged deployed historical MLX provider on frozen local integration panel",
               "proof_admission_requires_completed_run_receipt": True,
               "cases": [], "runner": fingerprint(__file__),
               "helper": fingerprint(helper_path, args.helper_sha256)}
    loaded, source_pins, fatal = None, {}, None
    actual_calls = 0
    signal.signal(signal.SIGALRM, alarm)
    try:
        signal.setitimer(signal.ITIMER_REAL, LOAD_SECONDS)
        study = read_json(args.study, args.study_sha256)
        inputs = read_json(args.inputs, args.inputs_sha256)
        require(study["schema"] == "hydra-model-upgrade-comparison-v1"
                and study["search_limits"] == SEARCH_LIMITS
                and study["payload_files"]["inputs.json"] == args.inputs_sha256,
                "search budgets or panel differ from the pinned comparison")
        cases = inputs["cases"]
        require(inputs["schema"] == "hydra-model-upgrade-panel-search-inputs-v1" and len(cases) == 32
                and all(type(case) is dict and set(case) == {"id", "theorem"}
                        and type(case["id"]) is str and re.fullmatch("[a-zA-Z0-9_-]+", case["id"])
                        and type(case["theorem"]) is str and 0 < len(case["theorem"].encode()) <= 8192
                        for case in cases), "unexpected frozen panel")
        by_id = {case["id"]: case for case in cases}
        require(len(by_id) == 32 and set(args.case_ids) <= set(by_id), "unknown or duplicate panel IDs")
        source_pins, source_exclusions = local_app_source_pins(study, REPO)
        require(all(str(REPO / "hydra-playground" / name) in source_pins for name in
                    ("worker.py", "model_runtime.py", "hybrid_runtime.py", "hybrid_search.py")),
                "study omitted a required local runtime source pin")
        source_pins[str(helper_path)] = receipt["helper"]
        receipt["source_files"] = source_pins
        receipt["unused_app_source_exclusions"] = source_exclusions
        sys.path.insert(0, str(REPO / "hydra-playground"))
        sys.addaudithook(offline_guard)
        assert_unused_source_modules()
        import worker
        import model_runtime as trained
        from hybrid_runtime import LazyModelPolicy
        worker.load_kernel()
        from hybrid_search import search, HybridLimits
        from peano_lab.batch import MODEL_V1_COMMANDS
        from peano_lab.ui.prove import SurfaceCapabilities
        capabilities = SurfaceCapabilities(label="hydra-authority-no-imports-v1",
            allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
        require(trained.MODEL_MANIFEST_SHA == study["baseline_manifest_sha256"],
                "local historical model differs from the comparison's baseline artifact")
        loaded = LazyModelPolicy(capabilities, lambda _event: None)
        loaded._prepare()
        require(trained.MAX_NEW_TOKENS == 64 and trained.MAX_PROMPT_TOKENS == 1536,
                "historical decoding limits changed")
        receipt["model_identity"] = copy.deepcopy(loaded.identity)
        receipt["model_load_and_admission_seconds"] = time.monotonic() - started
        signal.setitimer(signal.ITIMER_REAL, 0)
        for case_id in args.case_ids:
            case = by_id[case_id]
            policy = fresh_historical_policy(loaded, LazyModelPolicy, trained, capabilities)
            case_started = time.monotonic()
            deadline = case_started + SEARCH_LIMITS["wall_seconds"]
            record = {"case_id": case_id, "theorem": case["theorem"], "status": "started", "proved": False}
            case_fatal = None
            signal.setitimer(signal.ITIMER_REAL, HARD_CASE_SECONDS)
            try:
                result = search(case["theorem"], capabilities=capabilities, model_policy=policy,
                                limits=HybridLimits(**SEARCH_LIMITS))
                record.update(search=result, status=result["status"])
                errors = [row for row in result.get("diagnostics", []) if row.get("kind") == "model_error"]
                prompt_limit = "This interactive proof state exceeds the 1,536-token prompt bound; it was not truncated."
                record["expected_prompt_limit_declines"] = [row for row in errors if row.get("message") == prompt_limit]
                require(all(row.get("message") == prompt_limit for row in errors),
                        "historical provider infrastructure failure; not a model-quality result")
                require(result["model_calls"] == policy.calls, "historical search/provider call accounting differs")
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
                case_fatal = error
                record.update(status="timeout", proved=False, error_type=type(error).__name__, error=str(error),
                              remaining_batch_aborted=True)
            except BaseException as error:
                case_fatal = error
                record.update(status="infrastructure_error", proved=False,
                              error_type=type(error).__name__, error=str(error))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                record["wall_seconds"] = time.monotonic() - case_started
                record["search_and_replay_seconds"] = record["wall_seconds"]
                record["provider"] = provider_report(policy)
                actual_calls += record["provider"]["actual_model_calls"]
                save(out / (case_id + ".json"), record)
                receipt["cases"].append({key: record[key] for key in ("case_id", "status", "proved", "wall_seconds")})
                print(json.dumps({"arm": receipt["arm"], **receipt["cases"][-1]}), flush=True)
            if case_fatal is not None:
                raise case_fatal
        receipt.update(status="cases_finished_pending_custody", cases_completed=len(receipt["cases"]),
                       actual_model_calls=actual_calls)
    except BaseException as error:
        fatal = error
        receipt.update(status="failed", error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if loaded is not None:
            custody_started = time.monotonic()
            try:
                signal.setitimer(signal.ITIMER_REAL, FINALIZE_SECONDS)
                receipt["loaded_policy_finalization"] = loaded.finalize()
                for path, pin in source_pins.items():
                    require(fingerprint(path) == pin, "local runtime source changed: " + path)
                assert_unused_source_modules()
                receipt["input_custody_finalized"] = True
                if fatal is None:
                    receipt["status"] = "completed"
            except BaseException as error:
                fatal = fatal or error
                receipt.update(status="failed", input_custody_finalized=False,
                               finalize_error_type=type(error).__name__, finalize_error=str(error))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                receipt["custody_finalization_seconds"] = time.monotonic() - custody_started
        receipt["actual_model_calls"] = actual_calls
        receipt["wall_seconds"] = time.monotonic() - started
        receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(out / "receipt.json", receipt)
    if fatal is not None:
        raise fatal


if __name__ == "__main__":
    main()
