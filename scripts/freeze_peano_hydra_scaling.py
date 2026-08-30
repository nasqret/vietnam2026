#!/usr/bin/env python3
"""Plan or create one fresh CPU-only synthetic Hydra source snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.dont_write_bytecode = True
sys.pycache_prefix = "/dev/null"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true", help="read-only inventory (default)")
    modes.add_argument("--freeze", action="store_true", help="copy into a fresh local Git repository")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--expected-plan-sha256")
    parser.add_argument("--protected-input", type=Path, action="append", default=[],
                        help="existing external origin directory never allowed to contain output; repeat as needed")
    args = parser.parse_args(argv)
    if args.freeze and args.output_dir is None:
        parser.error("--freeze requires one explicit fresh --output-dir")
    if not args.freeze and (args.output_dir is not None or args.expected_plan_sha256 is not None
                            or args.protected_input):
        parser.error("--output-dir, --expected-plan-sha256 and --protected-input belong only to --freeze")
    from training.peano_hydra import scaling_freeze as freeze
    try:
        if args.freeze:
            result = freeze.freeze_scaling_source(
                args.source_root, args.output_dir, expected_plan_sha256=args.expected_plan_sha256,
                protected_inputs=tuple(args.protected_input),
            )
        else:
            result = freeze.plan_scaling_freeze(args.source_root)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
        return 0
    except freeze.ScalingFreezeError as error:
        observation = error.observation or {
            "status": "incomplete", "partial_output_retained": False,
            "error": " ".join(str(error).split())[:1024],
        }
        print(json.dumps(observation, sort_keys=True, ensure_ascii=False, allow_nan=False))
        print("hydra-scaling-freeze: " + str(error), file=sys.stderr)
        return 2
    except (ValueError, OSError, TypeError) as error:
        print("hydra-scaling-freeze: " + " ".join(str(error).split())[:1024], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
