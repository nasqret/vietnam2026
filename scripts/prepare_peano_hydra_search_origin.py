#!/usr/bin/env python3
"""Prepare or recheck one fixed corrective-model origin; never train or infer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))
from training.peano_hydra import search_origin as origin


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--adapter-manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--reference-manifest", type=Path)
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args(argv)
    try:
        if args.prepare:
            origin._require(args.source_root is not None and args.adapter_manifest is not None
                            and args.output_dir is not None and args.python is not None,
                            "--prepare requires --source-root, --adapter-manifest, --output-dir and --python")
            origin._require(args.reference_manifest is None and args.expected_manifest_sha256 is None,
                            "reference/hash options belong only to --check")
            reference = origin.prepare_origin(args.source_root, args.adapter_manifest, args.output_dir, args.python)
            path = reference.receipt_path.parent / origin.REFERENCE_FILENAME
            raw = origin.bridge._read(path, origin.bridge.MAX_BUNDLE_MANIFEST_BYTES)
            result = {"status": "validated-original-origin", "reference": reference.to_dict(),
                      "manifest_path": str(path), "manifest_file_sha256": origin._sha(raw),
                      "claims": dict(origin.CLAIMS)}
        else:
            origin._require(args.reference_manifest is not None and args.expected_manifest_sha256 is not None,
                            "--check requires --reference-manifest and --expected-manifest-sha256")
            origin._require(args.output_dir is None and args.python is None,
                            "--check cannot write an output directory or select an execution interpreter")
            reference = origin.load_reference(args.reference_manifest, args.expected_manifest_sha256,
                                               source_root=args.source_root, adapter_manifest=args.adapter_manifest)
            result = {"status": "externally-anchored-byte-recheck-no-replay",
                      "reference": reference.to_dict(), "native_replay_performed": False,
                      "claims": dict(origin.CLAIMS)}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (ValueError, TypeError, OSError, RuntimeError) as error:
        observation = getattr(error, "observation", None)
        if observation is not None:
            print(json.dumps({"status": "incomplete", **observation}, sort_keys=True))
        print("search-origin: " + " ".join(str(error).split())[:3000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
