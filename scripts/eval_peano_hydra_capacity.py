#!/usr/bin/env python3
"""Plan, execute, or independently replay the fixed 32-goal exposed DEV diagnostic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "peano-lab/py"):
    sys.path.insert(0, str(directory))

from training.peano_hydra.capacity import (  # noqa: E402
    CapacityError, MAX_REPORT_BYTES, MAX_REPLAY_REQUEST_BYTES, build_capacity_plan,
    execute_capacity, replay_worker, verify_capacity,
)
from training.peano_hydra.evaluation import _canonical, _json_object  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments == ["--replay-worker"]:
        try:
            raw = sys.stdin.buffer.read(MAX_REPLAY_REQUEST_BYTES + 1)
            if len(raw) > MAX_REPLAY_REQUEST_BYTES:
                raise CapacityError("native replay request exceeds its byte reservation")
            request = _json_object(raw, description="native replay request")
            sys.stdout.write(_canonical(replay_worker(request)).decode() + "\n")
            return 0
        except (ValueError, TypeError, OSError, RuntimeError, RecursionError) as error:
            print(f"capacity-replay-worker: {' '.join(str(error).split())}", file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="freeze/print the model-free 32-goal plan (default)")
    mode.add_argument("--execute-models", action="store_true", help="explicitly run base/new model lanes on one CUDA GPU")
    mode.add_argument("--verify", type=Path, metavar="FILE", help="authenticate a saved result and replay its proofs without CUDA")
    parser.add_argument("--preparation-dir", type=Path, default=ROOT / "_deploy/hydra-posttrain-next")
    parser.add_argument("--trained-adapter", type=Path, help="exact preparation-compatible adapter directory or manifest")
    parser.add_argument("--authority-aware", action="store_true",
                        help="explicit V4/primitive decoder profile; requires its separately prepared V2 corpus")
    parser.add_argument("--output", type=Path, help="write one new JSON file; never overwrite")
    args = parser.parse_args(arguments)
    if args.execute_models and args.trained_adapter is None:
        parser.error("--execute-models requires explicit --trained-adapter PATH")
    try:
        profile = {}
        if args.authority_aware:
            from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE

            profile["authority_profile"] = AUTHORITY_PRIMITIVE_PROFILE
        if args.output is not None and (args.output.exists() or args.output.is_symlink()):
            raise CapacityError("capacity output must be a fresh non-symlink file")
        if args.verify is not None:
            result = verify_capacity(args.verify, preparation_directory=args.preparation_dir,
                                     trained_adapter=args.trained_adapter, **profile)
        else:
            plan = build_capacity_plan(args.preparation_dir, trained_adapter=args.trained_adapter, **profile)
            result = execute_capacity(plan) if args.execute_models else plan.to_dict()
        rendered = json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n"
        if len(rendered.encode()) > MAX_REPORT_BYTES:
            raise CapacityError("rendered capacity artifact exceeds its byte reservation")
        if args.output is not None:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(rendered)
            print(args.output)
        else:
            print(rendered, end="")
    except (ValueError, TypeError, OSError, RuntimeError) as error:
        print(f"eval-peano-hydra-capacity: {' '.join(str(error).split())}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
