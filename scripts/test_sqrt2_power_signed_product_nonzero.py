"""SI001 exact source, actual ancestor bodies and hostile-input regressions.

Proof execution belongs only in a root-owned bounded worker. Finite integer
models below calibrate statements; they are not universal proof certificates.
"""

from dataclasses import replace
from hashlib import sha256
from itertools import product
import sys

import pytest

import sqrt2_power_signed_product_nonzero as signed


@pytest.fixture(scope="module")
def certificate():
    return signed.prove_signed_product_nonzero()


def _curried(bundle, node):
    from peano_lab.kernel.formulas import Imp
    formula = node.target
    for dependency in reversed(node.dependencies):
        formula = Imp(bundle.nodes[dependency].target, formula)
    return formula


def _omit_premise(index):
    formula = signed.frozen_signed_product_nonzero_target()
    from peano_lab.kernel.formulas import Forall, Imp
    for _ in range(6):
        assert type(formula) is Forall
        formula = formula.body
    premises = []
    for _ in range(3):
        assert type(formula) is Imp
        premises.append(formula.left)
        formula = formula.right
    for i in reversed(range(3)):
        if i != index:
            formula = Imp(premises[i], formula)
    for _ in range(6):
        formula = Forall(formula)
    return formula


def test_exact_target_and_honest_public_source_contract():
    target = signed.frozen_signed_product_nonzero_target()
    from peano_lab.kernel.formulas import Bot, Forall, Imp
    from peano_lab.library.proof_bundle import encode_formula
    row = signed.source_contract()
    assert row["code"] == "SI001"
    assert row["parameters"] == ["p", "n", "q", "m", "r", "s"]
    assert row["premise_count"] == 3
    assert row["arbitrary_input_representatives"]
    assert row["arbitrary_output_representatives"]
    assert not row["original_HA_checked"]
    assert not row["quadratic_field_claim"]
    assert not row["finite_product_claim"]
    assert not row["closes_IR046"]
    assert not row["closes_IR072"]
    assert row["library_admissions"] == 0
    assert signed.json_hash(encode_formula(target)) == signed.SIGNED_PRODUCT_NONZERO_TARGET_SHA256
    formula = target
    for _ in range(6):
        assert type(formula) is Forall
        formula = formula.body
    for _ in range(3):
        assert type(formula) is Imp
        formula = formula.right
    assert type(formula) is Imp and type(formula.right) is Bot
    assert "peano_lab.library.theorems" not in sys.modules


def test_source_pins_are_small_and_archive_is_separately_bound():
    pins = signed.signed_product_nonzero_source_pins()
    assert str(signed.V28_ARTIFACT.relative_to(signed.ROOT)) not in pins
    assert "scripts/sqrt2_power_signed_product_nonzero.py" in pins
    for name, row in pins.items():
        raw = (signed.ROOT / name).read_bytes()
        assert row == dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
        assert len(raw) <= 16 * 1024**2


def test_complete_cone_keeps_every_actual_ordered_body_and_endpoint():
    ids, rows = signed.inert_selected_rows()
    cone = signed.load_signed_product_cone()
    from peano_lab.library.proof_bundle import encode_formula, encode_proof
    assert ids == cone.original_ids == signed.ANCESTOR_IDS
    assert len(cone.nodes) == 33
    assert cone.body_nodes == 2315
    assert cone.max_depth == 40
    assert sum(len(n.dependencies) for n in cone.nodes) == 70
    assert signed.json_hash(rows) == signed.SELECTED_ROWS_SHA256
    remap = {old: new for new, old in enumerate(ids)}
    for old, row, node in zip(ids, rows, cone.nodes):
        assert node.node_id == remap[old]
        assert node.fuel == row[0]
        assert encode_formula(node.target) == row[1]
        assert node.dependencies == tuple(remap[d] for d in row[2])
        assert encode_proof(node.body) == row[3]
    assert tuple(cone.endpoints[old] for old in signed.ROOT_DEPENDENCIES) == (26, 31, 32, 11, 12, 2)


def test_all_small_signed_models_allow_overlapping_output_representatives():
    checked = 0
    for first, second in product(range(-2, 3), repeat=2):
        p, n = max(first, 0) + 3, max(-first, 0) + 3
        q, m = max(second, 0) + 4, max(-second, 0) + 4
        positive, negative = p*q+n*m, p*m+n*q
        for offset in (0, 7):
            r, s = positive + offset, negative + offset
            assert r + negative == positive + s
            assert r > 0 and s > 0  # neither component need vanish
            assert (r == s) == (first == 0 or second == 0)
            if p != n and q != m:
                assert r != s
            checked += 1
    assert checked == 50


@pytest.mark.parametrize("omitted,values", (
    (0, (1, 0, 1, 0, 5, 5)),
    (1, (2, 2, 3, 1, 5, 5)),
    (2, (3, 1, 2, 2, 5, 5)),
))
def test_every_explicit_premise_is_needed(omitted, values):
    p, n, q, m, r, s = values
    premises = (r+(p*m+n*q) == (p*q+n*m)+s, p != n, q != m)
    assert all(value for i, value in enumerate(premises) if i != omitted)
    assert not premises[omitted]
    assert r == s
    assert _omit_premise(omitted) != signed.frozen_signed_product_nonzero_target()


def test_exact_source_and_corrupted_archive_fail_closed(monkeypatch, tmp_path):
    altered = signed.SIGNED_PRODUCT_NONZERO_SOURCE.replace("+n*m", "+n*q", 1)
    with monkeypatch.context() as patch:
        patch.setattr(signed, "SIGNED_PRODUCT_NONZERO_SOURCE", altered)
        with pytest.raises(signed.SignedProductNonzeroError, match="target AST"):
            signed.frozen_signed_product_nonzero_target()
    artifact = tmp_path / "wrong-v28.json"
    artifact.write_bytes(b"[]\n")
    with pytest.raises(signed.SignedProductNonzeroError, match="size/hash"):
        signed.inert_selected_rows(artifact)


def test_node_budget_stops_before_cone_or_proof_construction(monkeypatch):
    from sqrt2_power_binary_dag import BinaryDAGLimits
    def forbidden(*_args, **_kwargs):
        raise AssertionError("exhausted node cap reached proof construction")
    monkeypatch.setattr(signed, "load_signed_product_cone", forbidden)
    monkeypatch.setattr(signed, "_root_body", forbidden)
    with pytest.raises(signed.SignedProductNonzeroError, match="node budget"):
        signed.prove_signed_product_nonzero(limits=BinaryDAGLimits(max_nodes=33))


@pytest.mark.parametrize("kwargs", (
    {"max_total_body_nodes": 2300},
    {"max_depth": 20},
    {"max_payload_bytes": signed.SELECTED_ROWS_BYTES - 1},
))
def test_stricter_structural_caps_fail_closed(kwargs):
    from sqrt2_power_binary_dag import BinaryDAGLimits
    with pytest.raises(ValueError):
        signed.prove_signed_product_nonzero(limits=BinaryDAGLimits(**kwargs))


def test_native_original_ha_and_fresh_canonical_replay(certificate):
    from peano_lab.library.proof_bundle import check_encoded_proof_bundle
    result = certificate
    assert result.target == result.receipt.target == signed.frozen_signed_product_nonzero_target()
    assert result.target_ast_sha256 == signed.SIGNED_PRODUCT_NONZERO_TARGET_SHA256
    assert len(result.bundle.nodes) == result.receipt.kernel_calls == 34
    assert result.bundle.root == 33
    assert result.bundle.nodes[33].dependencies == (26, 31, 32, 11, 12, 2)
    assert result.receipt.total_body_nodes <= 200000
    assert result.max_proof_depth <= 256
    assert len(result.payload.encode()) <= 8 * 1024**2
    assert result.provenance["actual_ancestor_nodes"] == 33
    assert result.provenance["actual_ancestor_body_nodes"] == 2315
    assert result.provenance["external_certificate_references"] == []
    assert result.provenance["new_axioms"] == []
    assert result.provenance["IR_parents_closed"] == result.provenance["library_admissions"] == 0
    assert not result.provenance["quadratic_field_claim"]
    assert not result.provenance["finite_product_claim"]
    assert check_encoded_proof_bundle(result.payload).target == result.target


def test_native_rejects_all_missing_explicit_premises(certificate):
    from peano_lab.kernel.checker import check
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    for omitted in range(3):
        target = _omit_premise(omitted)
        changed = replace(root, target=target)
        assert not check((), root.body, _curried(bundle, changed))
        with pytest.raises(ProofBundleError, match="exact caller target"):
            check_proof_bundle(bundle, target)


def test_native_rejects_wrong_balance_and_missing_dependency(certificate):
    from sqrt2_power_native import closed_formula
    from peano_lab.kernel.checker import check
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    changed_target = closed_formula(signed.SIGNED_PRODUCT_NONZERO_SOURCE.replace("+n*m", "+n*q", 1))
    assert not check((), root.body, _curried(bundle, replace(root, target=changed_target)))
    for i in range(len(root.dependencies)):
        changed = replace(root, dependencies=root.dependencies[:i] + root.dependencies[i+1:])
        assert not check((), root.body, _curried(bundle, changed))


def test_native_rejects_forged_root_and_actual_ancestor(certificate):
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    bundle = certificate.bundle
    for index in (0, bundle.root):
        nodes = list(bundle.nodes)
        nodes[index] = replace(nodes[index], body=EqRefl(Zero()))
        with pytest.raises(ProofBundleError, match="kernel rejected"):
            check_proof_bundle(replace(bundle, nodes=tuple(nodes)), certificate.target)
