#!/usr/bin/env python3
"""Plan or run bounded authored CPU fixtures for opt-in renamed-state deduplication.

Default --check only hashes source and prints the fixed plan. --run requires a
fresh output path and executes isolated native workers, including a separate
fresh replay for each proof. No models, training, network, old preparations,
or saved model-proposal transcripts are used.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.pycache_prefix = "/dev/null"
ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))

from training.peano_hydra import search_dedup as demo  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only fixed fixture/source plan (default)")
    mode.add_argument("--run", action="store_true", help="run bounded CPU fixtures and fresh proof replay")
    mode.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, help="fresh JSON artifact; its parent directory must already exist")
    args = parser.parse_args(argv)
    try:
        if args.worker:
            demo.require(argv == ["--worker"], "internal worker accepts only bounded stdin")
            request = demo.decode(sys.stdin.buffer.read(demo.MAX_REQUEST_BYTES + 1))
            result = demo.worker(request)
        else:
            demo.require(not args.run or args.output is not None, "--run requires a fresh --output")
            if args.output is not None:
                demo.fresh_output(args.output)
            plan = demo.build_demo_plan(ROOT)
            def progress(event):
                print(demo.canonical(event).decode(), file=sys.stderr, flush=True)
            result = demo.execute_demo(plan, root=ROOT, progress=progress) if args.run else plan
            if args.output is not None:
                demo.fresh_output(args.output, result)
        sys.stdout.buffer.write(demo.canonical(result) + b"\n")
        sys.stdout.buffer.flush()
        return 3 if args.run and result["status"] != "complete" else 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print("search-dedup-fixtures: " + " ".join(str(error).split())[:2000], file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
