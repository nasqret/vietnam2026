#!/usr/bin/env python3
"""Plan/check TRAIN-only proposal search, run a tiny fixture, or harvest proofs.

Model generation is available to a reviewed owner through main(...,
reservation_check=...). Calling --generate without that one-use resource gate
fails before model loading. This CLI never creates an approval or submits jobs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]


def main(argv=None, *, reservation_check=None):
    from training.peano_hydra import self_training_proposals as proposal
    from training.peano_hydra import corrective_workflow as files, scaling_workflow as workflow
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments in (["--fixture-worker"], ["--replay-worker"]):
        try:
            request = workflow.decode(sys.stdin.buffer.read(4 * 1024**2 + 1))
            result = (proposal.fixture_worker(request) if arguments == ["--fixture-worker"]
                      else proposal.replay_worker(request))
            print(workflow.canonical(result).decode(), flush=True)
            return 0
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
            print("self-training-worker: " + " ".join(str(error).split())[:2000], file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--fixture", action="store_true")
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--harvest", action="store_true")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--expected-request-sha256", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--generation-directory", type=Path)
    parser.add_argument("--expected-generation-sha256")
    parser.add_argument("--execution-inputs", type=Path)
    parser.add_argument("--expected-execution-inputs-sha256")
    args = parser.parse_args(arguments)
    try:
        proposal.require((args.generation_directory is not None) == (args.expected_generation_sha256 is not None)
                         == args.harvest, "only harvest consumes an exact generation directory/raw SHA")
        proposal.require((args.execution_inputs is not None) == (args.expected_execution_inputs_sha256 is not None)
                         == (args.generate or args.harvest), "generation/harvest require external pilot acceptance evidence")
        proposal.require(args.check or args.output is not None, "a fresh explicit output is required")
        if args.generate:
            proposal.require(callable(reservation_check),
                "model generation requires a separately reviewed owner with a one-use resource reservation; this standalone CLI cannot allocate it")
        if args.fixture:
            from training.peano_hydra import review_runtime
            request = proposal._read({"path": str(args.request.absolute()), "sha256": args.expected_request_sha256})
            proposal.require(request.get("schema") == proposal.FIXTURE_SCHEMA, "fixture mode accepts only authored test material")
            files.guard_output(args.output, protected=(*workflow._protected(), args.request.absolute().parent))
            command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null", str(Path(__file__).absolute()), "--fixture-worker")
            limits = review_runtime.ProcessLimits(**proposal.FIXTURE_LIMITS)
            payload = proposal.canonical(request)
            before = proposal.execution_sources()
            process = review_runtime.run_bounded(command, cwd=ROOT, limits=limits, input_bytes=payload,
                                                runtime_library_paths=files.runtime_libraries())
            after = proposal.execution_sources()
            passed = process["returncode"] == 0 and process["reason"] == "exited" and before == after
            if passed:
                review_runtime.validate_process_record(process, command=command, limits=limits,
                                                      input_bytes=payload, success_codes=(0,))
            result = {"schema": proposal.FIXTURE_SCHEMA + "-process", "status": "passed" if passed else "failed",
                "request_file_sha256": args.expected_request_sha256, "source_files_before": before,
                "source_files_after": after, "process": process,
                "result": workflow.decode(process["stdout"].encode()) if passed else None,
                "model_generation_performed": False, "positive_training_rows": 0, **proposal.CLAIMS}
            files.publish_metadata(args.output, result, protected=(*workflow._protected(), args.request.absolute().parent))
            proposal.require(passed, "bounded authored fixture failed; its process receipt was retained")
        else:
            bound = proposal.check_request(args.request, args.expected_request_sha256)
            if args.generate:
                inputs = proposal._read({"path": str(args.execution_inputs.absolute()), "sha256": args.expected_execution_inputs_sha256})
                proposal.experiment.keys(inputs, {"pilot_request", "pilot_run", "pilot_verification", "review", "authorization"},
                                         "generation execution evidence")
                authorization = proposal._read(inputs["authorization"])
                result = proposal.generate(bound, output=args.output,
                    pilot_inputs={key: inputs[key] for key in ("pilot_request", "pilot_run", "pilot_verification", "review")},
                    authorization=authorization, authorization_sha256=inputs["authorization"]["sha256"],
                    reservation_check=reservation_check)
            elif args.harvest:
                files.guard_output(args.output, protected=(*workflow._protected(), *bound.protected_paths(), args.generation_directory))
                inputs = proposal._read({"path": str(args.execution_inputs.absolute()), "sha256": args.expected_execution_inputs_sha256})
                proposal.experiment.keys(inputs, {"pilot_request", "pilot_run", "pilot_verification", "review"},
                                         "independent harvest pilot acceptance")
                result = proposal.harvest_generation(bound, args.generation_directory, args.expected_generation_sha256,
                                                     pilot_inputs=inputs)
                files.publish_metadata(args.output, result,
                    protected=(*workflow._protected(), *bound.protected_paths(), args.generation_directory))
            else:
                result = bound.to_dict()
                if args.output is not None:
                    files.publish_metadata(args.output, result, protected=(*workflow._protected(), *bound.protected_paths()))
        print(json.dumps({key: result[key] for key in (
            "schema", "status", "plan_sha256", "generation_sha256", "harvest_sha256",
            "accepted_transition_count", "candidate_count", "training_authorized", "dataset_admitted") if key in result},
            sort_keys=True, ensure_ascii=False), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
        print("self-training-proposals: " + " ".join(str(error).split())[:3000], file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
