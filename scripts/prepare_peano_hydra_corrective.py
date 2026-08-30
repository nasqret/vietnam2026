#!/usr/bin/env python3
"""Plan/admit/reverify one corrective experiment; never launch a GPU job."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "peano-lab/py"))
from training.peano_hydra import corrective_workflow as workflow


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--worker"]:
        try:
            request = workflow.decode(sys.stdin.buffer.read(64 * 1024 + 1))
            workflow.require(len(workflow.canonical(request)) <= 64 * 1024, "worker request exceeds its bound")
            result = workflow.worker(request)
            workflow.require(not {"torch", "transformers", "peft"} & set(sys.modules), "admission imported a model framework")
            print(workflow.canonical(result).decode())
            return 0
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
            print("corrective-worker: " + " ".join(str(error).split())[:3000], file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--verify", action="store_true")
    modes.add_argument("--check-approval", action="store_true")
    modes.add_argument("--propose-approval", action="store_true")
    modes.add_argument("--freeze-origin-sources", type=Path, metavar="CHECKOUT")
    parser.add_argument("--output-dir", type=Path, default=Path(workflow.BUNDLE))
    parser.add_argument("--run-id", default=workflow.RUN_ID)
    parser.add_argument("--origin-request", type=Path, default=Path(workflow.INPUT))
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--stage", choices=tuple(workflow.JOBS))
    parser.add_argument("--expected-readiness-sha256")
    parser.add_argument("--source-commit")
    parser.add_argument("--output", type=Path, help="fresh metadata file; existing files are never replaced")
    args = parser.parse_args(arguments)
    try:
        output = args.output_dir.absolute()
        origin_request = args.origin_request.absolute()
        workflow.require(args.run_id == workflow.RUN_ID, "this corrective experiment has one fixed run-id")
        workflow.require(args.stage is None or args.check_approval, "--stage is only an approval-check option")
        workflow.require(args.approval is None or args.check_approval or args.verify,
                         "--approval only checks an existing admitted bundle")
        workflow.require(args.expected_readiness_sha256 is None or args.verify,
                         "--expected-readiness-sha256 is only a verification option")
        workflow.require(args.source_commit is None or args.freeze_origin_sources is not None or args.propose_approval,
                         "--source-commit is only a freeze/proposal option")
        workflow.require(not (args.approval is not None and args.expected_readiness_sha256 is not None),
                         "approval and offline-readiness anchors cannot be mixed")
        extras = () if args.freeze_origin_sources is None else (args.freeze_origin_sources.absolute(),)
        protected = workflow.protected_roots(origin_request=origin_request, bundle=output, extra=extras)
        if args.output is not None:
            workflow.guard_output(args.output.absolute(), protected=protected)
        approval = None
        if args.check_approval or ((args.prepare or args.verify) and (args.approval is not None or os.environ.get("SLURM_JOB_ID"))):
            workflow.require(args.approval is not None, "cluster verification requires fresh explicit approval")
            actual_stage = next((name for name, script in workflow.JOBS.items() if os.environ.get("PEANO_JOB_SCRIPT") == script), None)
            chosen = args.stage if args.check_approval else actual_stage
            workflow.require(chosen in workflow.JOBS, "select the exact approval stage")
            approval = workflow.check_approval(args.approval.absolute(), origin_request=origin_request,
                                               output=output, stage_name=chosen, run_id=args.run_id,
                                               require_job=os.environ.get("SLURM_JOB_ID") is not None)
        if args.check_approval:
            result = {"schema": workflow.APPROVAL_SCHEMA, "status": "approved-scope-checked",
                      "stage": args.stage, "ready_bundle_sha256": approval["ready_bundle_sha256"],
                      "no_job_submitted": True}
        elif args.freeze_origin_sources is not None:
            workflow.require(args.output is not None and args.source_commit == workflow.SOURCE_COMMIT,
                             "source freezing requires a fresh output and the preserved original commit")
            from training.peano_hydra.origin_bridge import freeze_origin_sources
            raw = freeze_origin_sources(args.freeze_origin_sources.absolute(), expected_commit=args.source_commit)
            workflow.publish_metadata(args.output.absolute(), raw, raw=True, protected=protected)
            print(json.dumps({"status": "frozen-source-manifest-published", "output": str(args.output.absolute()),
                              "sha256": workflow.file_record(args.output.absolute())["sha256"],
                              "source_files_copied": False, "native_proofs_executed": False}))
            return 0
        elif args.prepare:
            workflow.require(os.environ.get("SLURM_JOB_ID") is None,
                             "cluster stage only verifies the externally approved pre-admitted bundle")
            result = workflow.prepare_bundle(output, origin_request=origin_request, run_id=args.run_id)
        elif args.verify:
            expected = args.expected_readiness_sha256 if approval is None else approval["ready_bundle_sha256"]
            workflow.require(expected is not None, "local verification needs --expected-readiness-sha256")
            result = workflow.verify_bundle(output, origin_request=origin_request, expected_readiness_sha256=expected)
        elif args.propose_approval:
            workflow.require(args.output is not None and args.source_commit is not None,
                             "approval proposal requires a fresh output and frozen source commit")
            result = workflow.approval_proposal(output, origin_request=origin_request, source_commit=args.source_commit)
        else:
            result = workflow.specification()
        if args.output is not None:
            workflow.publish_metadata(args.output.absolute(), result, protected=protected)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
        print("corrective: " + " ".join(str(error).split())[:3000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
