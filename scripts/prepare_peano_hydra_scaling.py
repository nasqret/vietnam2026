#!/usr/bin/env python3
"""Prepare/reverify the five-stage Hydra candidate pipeline, without a GPU."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    from training.peano_hydra import scaling_workflow as workflow
    if arguments in (["--native-worker"], ["--harvest-worker"], ["--admission-worker"]):
        try:
            request = workflow.decode(sys.stdin.buffer.read(workflow.MAX_METADATA_BYTES + 1))
            if arguments == ["--native-worker"]:
                result = workflow.native_worker(request)
            elif arguments == ["--admission-worker"]:
                result = workflow.admission_worker(request)
            else:
                from training.peano_hydra.self_training import native_replay_worker
                result = native_replay_worker(request)
            print(workflow.canonical(result).decode())
            return 0
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
            print("frontier-worker: " + " ".join(str(error).split()), file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--build", action="store_true")
    modes.add_argument("--verify", action="store_true")
    modes.add_argument("--harvest", action="store_true")
    modes.add_argument("--prepare-pilot", action="store_true")
    parser.add_argument("--profile", choices=("smoke", "pilot"), default="smoke")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--expected-readiness-sha256")
    parser.add_argument("--baseline-source", type=Path)
    parser.add_argument("--expected-baseline-source-sha256")
    parser.add_argument("--round-plan", type=Path)
    parser.add_argument("--expected-round-file-sha256")
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--expected-candidates-file-sha256")
    parser.add_argument("--review-file", type=Path)
    parser.add_argument("--expected-review-sha256", help="external CANONICAL review SHA, not raw-file SHA")
    parser.add_argument("--run-id")
    args = parser.parse_args(arguments)
    try:
        if not args.prepare_pilot and args.run_id is not None:
            parser.error("--run-id belongs only to --prepare-pilot")
        if args.plan:
            if any((args.bundle, args.baseline_source, args.round_plan, args.candidates,
                    args.expected_readiness_sha256, args.expected_round_file_sha256,
                    args.expected_candidates_file_sha256, args.expected_baseline_source_sha256,
                    args.review_file, args.expected_review_sha256)):
                parser.error("--plan does not consume model/data/review inputs")
            result = workflow.specification()
            if args.output is not None:
                workflow.write_json(args.output, result)
        elif args.build:
            if args.output is None or any((args.bundle, args.round_plan, args.candidates,
                args.expected_readiness_sha256, args.expected_round_file_sha256,
                args.expected_candidates_file_sha256, args.review_file, args.expected_review_sha256)):
                parser.error("--build needs one fresh --output and no bundle/harvest inputs")
            result = workflow.build_bundle(args.output, profile=args.profile,
                baseline_source=args.baseline_source,
                baseline_source_sha256=args.expected_baseline_source_sha256)
            result = {"status": result["readiness"]["status"], "output": result["output"],
                      "readiness_raw_sha256": result["readiness_raw_sha256"],
                      "native_verified_routes": result["readiness"]["native_verified_routes"],
                      "native_verified_transitions": result["readiness"]["native_verified_transitions"],
                      "training_authorized": False, "gpu_jobs_started": 0}
        elif args.verify:
            if args.bundle is None or args.expected_readiness_sha256 is None:
                parser.error("--verify requires --bundle and its external raw readiness SHA")
            if any((args.baseline_source, args.expected_baseline_source_sha256, args.round_plan,
                    args.expected_round_file_sha256, args.candidates, args.expected_candidates_file_sha256,
                    args.review_file, args.expected_review_sha256)):
                parser.error("--verify does not accept build/harvest inputs")
            if args.output is not None:
                workflow.fileio.guard_output(args.output, protected=(*workflow._protected(), args.bundle.absolute()))
            result = workflow.verify_bundle(args.bundle, expected_readiness_sha256=args.expected_readiness_sha256)
            if args.output is not None:
                workflow.write_json(args.output, result)
        elif args.prepare_pilot:
            if any(value is None for value in (args.bundle, args.expected_readiness_sha256,
                    args.review_file, args.expected_review_sha256, args.output, args.run_id)):
                parser.error("--prepare-pilot requires pinned bundle, external review, run ID and fresh output")
            if any((args.baseline_source, args.expected_baseline_source_sha256, args.round_plan,
                    args.expected_round_file_sha256, args.candidates, args.expected_candidates_file_sha256)):
                parser.error("--prepare-pilot does not accept build/harvest inputs")
            result = workflow.prepare_pilot(args.bundle,
                expected_readiness_sha256=args.expected_readiness_sha256,
                review_file=args.review_file, expected_review_sha256=args.expected_review_sha256,
                output_directory=args.output, run_id=args.run_id)
        else:
            if any((args.baseline_source, args.expected_baseline_source_sha256)):
                parser.error("--harvest does not accept build inputs")
            if any(v is None for v in (args.round_plan, args.expected_round_file_sha256,
                                        args.candidates, args.expected_candidates_file_sha256, args.output,
                                        args.bundle, args.expected_readiness_sha256,
                                        args.review_file, args.expected_review_sha256)):
                parser.error("--harvest requires pinned parent/round/candidate files, external review and a fresh --output")
            from training.peano_hydra.self_training import harvest_candidates
            workflow.fileio.guard_output(args.output, protected=(*workflow._protected(), args.bundle.absolute()))
            plan, plan_sha = workflow.read_json(args.round_plan, args.expected_round_file_sha256)
            candidates, candidates_sha = workflow.read_json(args.candidates, args.expected_candidates_file_sha256)
            review, review_raw_sha = workflow.read_json(args.review_file)
            workflow.experiment.keys(candidates, {"candidates"}, "candidate file")
            result = harvest_candidates(plan, candidates["candidates"], parent_bundle=args.bundle,
                parent_readiness_sha256=args.expected_readiness_sha256,
                review=review, review_sha256=args.expected_review_sha256)
            if (workflow.read_json(args.round_plan)[1] != plan_sha
                    or workflow.read_json(args.candidates)[1] != candidates_sha
                    or workflow.read_json(args.review_file)[1] != review_raw_sha):
                raise ValueError("harvest inputs changed during native replay")
            workflow.write_json(args.output, result)
            result = {k: v for k, v in result.items() if k not in {"accepted_transitions", "outcomes"}}
        print(workflow.canonical(result).decode())
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
        print("hydra-scaling: " + " ".join(str(error).split()), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
