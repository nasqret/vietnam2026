"""Transparent certificate-completion canary, not a theorem-proving benchmark.

Prompt ^a+b=; completion c|r...rz;. Each r selects one successor step,
z the addition-zero axiom. Completion is untrusted and must pass Lean.
The compiler uses the GENERATED r count and c, never repairs them to the target.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .peano import addition_artifact, numeral

ALPHABET = "_ ^0123456789+=|rz;"  # index zero is right padding, never a target
TOKEN_TO_ID = {ch: i for i, ch in enumerate(ALPHABET)}
PAD_ID = 0
EOS_ID = TOKEN_TO_ID[";"]


@dataclass(frozen=True)
class Example:
    a: int
    b: int
    split: str

    @property
    def prompt(self):
        return f"^{self.a}+{self.b}="

    @property
    def completion(self):
        return f"{self.a + self.b}|{'r' * self.b}z;"

    @property
    def theorem_id(self):
        return f"closed-add-{self.a}-{self.b}"


def examples() -> dict[str, list[Example]]:
    """Exact identities are split before serialization; OOD b exceeds training b.

    IID rows still share a single derivation schema, so this is deliberately
    weaker than a theorem-family or derivation-template held-out experiment.
    """
    out = {k: [] for k in ("train", "iid", "ood_depth", "ood_operand")}
    for a in range(16):
        for b in range(8):
            bucket = int(hashlib.sha256(f"add:{a}:{b}".encode()).hexdigest()[:8], 16) % 5
            split = "iid" if bucket == 0 else "train"
            out[split].append(Example(a, b, split))
    out["ood_depth"] = [Example(a, b, "ood_depth") for a in range(16) for b in range(8, 12)]
    out["ood_operand"] = [Example(a, b, "ood_operand") for a in range(16, 20) for b in range(8)]
    return out


def encode(text: str) -> list[int]:
    return [TOKEN_TO_ID[ch] for ch in text]


def compile_prediction(example: Example, completion: str):
    """Elaborate model choices into an artifact; only the checker accepts it.

    Well-formed but wrong c or wrong recurrence count yields a target/proof
    mismatch in Lean. Malformed or excessive outputs are rejected by the parser.
    """
    match = re.fullmatch(r"(0|[1-9][0-9]?)\|(r*)z;", completion)
    if match is None:
        raise ValueError("not in compact certificate language")
    c, steps = int(match.group(1)), len(match.group(2))
    artifact = addition_artifact(example.a, steps)
    artifact[2] = ["eq", ["add", numeral(example.a), numeral(example.b)], numeral(c)]
    return artifact


def reference_valid(example: Example, completion: str) -> bool:
    """Elementary arithmetic diagnostic, not the authoritative proof gate."""
    m = re.fullmatch(r"(0|[1-9][0-9]?)\|(r*)z;", completion)
    return bool(m and int(m.group(1)) == example.a + example.b and len(m.group(2)) == example.b)
