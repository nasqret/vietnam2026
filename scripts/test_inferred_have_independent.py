"""The installed, hash-pinned Lean checker independently checks inferred facts.

This tests native certificates with the compiled Lean checker. It deliberately
does not describe that as compilation of newly emitted textual Lean source.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py/tests"))

from test_inferred_have import EXAMPLES, run
from peano_lab.engine.tactics import checked_final
from peano_lab.kernel.formulas import And, parse_formula
from peano_lab.kernel.proofs import AndIntro, Hyp, ImpIntro
from peano_lab.library.proof_bundle import BundleNode, ProofBundle, check_proof_bundle, encode_proof_bundle
import constructive_bottom_layer_checkpoints as independent


def test_new_inferred_have_certificates_pass_the_existing_independent_lean_checker():
    if not independent.LEAN_BINARY.is_file():
        pytest.skip("installed independent Lean checker is unavailable")
    nodes = []
    for index, (statement, script) in enumerate(EXAMPLES):
        target = parse_formula(statement)
        proof = checked_final(run(statement, script), target)
        nodes.append(BundleNode(index, target, (), proof))
    target = nodes[-1].target
    body = Hyp(0)
    for index in reversed(range(len(nodes) - 1)):
        target = And(nodes[index].target, target)
        body = AndIntro(Hyp(len(nodes) - 1 - index), body)
    for _ in nodes:
        body = ImpIntro(body)
    root = len(nodes)
    nodes.append(BundleNode(root, target, tuple(range(root)), body))
    bundle = ProofBundle(tuple(nodes), root)
    native = check_proof_bundle(bundle, target)
    assert native.kernel_calls == len(EXAMPLES) + 1
    payload = encode_proof_bundle(bundle, target).encode()
    checkpoint = independent.Checkpoint("inferred-have-reading-policy", (), "test-only.json",
        len(payload), sha256(payload).hexdigest(), len(nodes), (), "", "")
    independent._lean_check(checkpoint, len(nodes), bundle.root, payload)
