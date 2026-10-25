#!/usr/bin/env python3
"""Candidate Peano-v2 closed-numeral-addition certificate producer.

Source-derived, NOT locally executed or validated. Run generation and verification
only in an authorized SLURM job. The producer is untrusted; only acceptance by the
pinned standalone Peano Lean verifier establishes the requested derivation.

Checker source: nasqret/peano-lab-lean
Commit: bd89f7b83dc3a3291ac1553a296691f576578e31
Contract: PeanoLab/{Syntax,Codec,Checker,Verify}.lean, Lean v4.31.0.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


CHECKER_REPOSITORY = "https://github.com/nasqret/peano-lab-lean"
CHECKER_COMMIT = "bd89f7b83dc3a3291ac1553a296691f576578e31"
ARTIFACT_FORMAT = "peano-lab-v2"
# Deliberately small: nested unary terms and certificates are a canary task.
MAX_SUM = 64


def _natural(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer (not bool)")
    return value


def numeral(value: int) -> list[Any]:
    """Return the closed unary term S^value(0)."""
    value = _natural(value, "numeral")
    if value > MAX_SUM:
        raise ValueError(f"canary numeral exceeds {MAX_SUM}")
    term: list[Any] = ["zero"]
    for _ in range(value):
        term = ["succ", term]
    return term


def addition_artifact(left: int, right: int) -> list[Any]:
    """Encode a proof of numeral(left)+numeral(right)=numeral(left+right).

    Base: forall_elim(PA3, a) proves a+0=a.
    Step: forall_elim(forall_elim(PA4,a),b) proves a+S(b)=S(a+b),
    then cong_s(previous) and eq_trans close a+S(b)=S(result).

    Proof.size counts constructors, not embedded term nodes. There are exactly
    2+5*right proof constructors. Fuel is the checker's default 8*size+16.
    No checker result is fabricated or inferred by this producer.
    """
    left = _natural(left, "left")
    right = _natural(right, "right")
    if left + right > MAX_SUM:
        raise ValueError(f"canary sum exceeds {MAX_SUM}")
    a = numeral(left)
    proof: list[Any] = ["forall_elim", ["axiom", "PA3"], a]
    for predecessor in range(right):
        step = [
            "forall_elim",
            ["forall_elim", ["axiom", "PA4"], a],
            numeral(predecessor),
        ]
        proof = ["eq_trans", step, ["cong_s", proof]]
    target = ["eq", ["add", a, numeral(right)], numeral(left + right)]
    proof_size = 2 + 5 * right
    fuel = 8 * proof_size + 16
    return [ARTIFACT_FORMAT, fuel, target, proof]


def canonical_bytes(artifact: list[Any]) -> bytes:
    """Serialize generated inert arrays in the exact Peano-v2 byte format.

    This is an encoder, not a decoder or acceptance gate. It does not certify an
    arbitrary supplied list. The final Lean process performs exact-arity decoding,
    canonical round-trip, closed-target checking, and intuitionistic derivation.
    """
    return (
        json.dumps(artifact, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=int)
    parser.add_argument("right", type=int)
    parser.add_argument("--output", type=Path, help="new artifact file; defaults to stdout")
    args = parser.parse_args()
    try:
        payload = canonical_bytes(addition_artifact(args.left, args.right))
    except ValueError as exc:
        parser.error(str(exc))
    if args.output is None:
        sys.stdout.buffer.write(payload)
    else:
        # Refuse silent replacement of an existing candidate or accepted artifact.
        with args.output.open("xb") as stream:
            stream.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
