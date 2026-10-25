"""Hash only the new executed source scope; no native or reserved-case imports."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from paired_common import canonical, save, source_pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pins = source_pins(args.app_root)
    save(args.output, pins)
    print(json.dumps({"schema": "hydra-teacher-paired-source-map-v1", "files": len(pins),
        "bytes": sum(row["bytes"] for row in pins.values()), "source_pins_sha256": sha256(canonical(pins)).hexdigest(),
        "native_proof_runs": 0, "model_calls": 0, "reserved_cases_parsed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
