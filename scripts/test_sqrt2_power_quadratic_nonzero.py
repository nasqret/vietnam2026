"""QN001 exact target, lossless sharing, signed models and hostile-body tests.

The root owns all execution. Host integer models only calibrate statements;
ordinary universal proofs require complete canonical original-HA replay.
"""

import ast
from dataclasses import replace
from hashlib import sha256
from itertools import product
from pathlib import Path
import sys

import pytest

import sqrt2_power_quadratic_nonzero as quadratic


@pytest.fixture(scope="module")
def certificate():
    return quadratic.prove_quadratic_nonzero()


def _curried(bundle, node):
    from peano_lab.kernel.formulas import Imp
    target = node.target
    for dependency in reversed(node.dependencies):
        target = Imp(bundle.nodes[dependency].target, target)
    return target


def _omit_premise(index):
    target = quadratic.frozen_quadratic_nonzero_target()
    from peano_lab.kernel.formulas import Forall, Imp
    for _ in range(12):
        assert type(target) is Forall
        target = target.body
    premises = []
    for _ in range(4):
        assert type(target) is Imp
        premises.append(target.left)
        target = target.right
    for i in reversed(range(4)):
        if i != index:
            target = Imp(premises[i], target)
    for _ in range(12):
        target = Forall(target)
    return target


def _pair(value, shift):
    return max(value, 0) + shift, max(-value, 0) + shift


def _model(values, weight=2):
    ap, an, bp, bn, cp, cn, dp, dn, rp, rn, sp, sn = values
    real_negative = (ap*cn+an*cp)+weight*(bp*dn+bn*dp)
    real_positive = (ap*cp+an*cn)+weight*(bp*dp+bn*dn)
    radical_negative = (ap*dn+an*dp)+(bp*cn+bn*cp)
    radical_positive = (ap*dp+an*dn)+(bp*cp+bn*cn)
    return (rp+real_negative == real_positive+rn,
            sp+radical_negative == radical_positive+sn,
            not (ap == an and bp == bn),
            not (cp == cn and dp == dn)), not (rp == rn and sp == sn)


def test_exact_named_target_and_honest_binary_scope():
    target = quadratic.frozen_quadratic_nonzero_target()
    from peano_lab.kernel.formulas import And, Bot, Forall, Imp
    from peano_lab.library.proof_bundle import encode_formula
    assert quadratic.json_hash(encode_formula(target)) == quadratic.TARGET_SHA256
    row = quadratic.source_contract()
    assert row["code"] == "QN001" and row["premise_count"] == 4
    assert row["parameters"] == list(quadratic.PARAMETERS)
    assert row["binary_quadratic_integer_product"] and row["arbitrary_signed_representatives"]
    assert not row["finite_product_claim"] and not row["irrationality_claim"]
    assert not row["closes_IR046"] and not row["closes_IR072"]
    assert not row["original_HA_checked"]
    assert row["IR_parents_closed"] == row["library_admissions"] == 0
    formula = target
    for _ in range(12):
        assert type(formula) is Forall
        formula = formula.body
    for _ in range(4):
        assert type(formula) is Imp
        formula = formula.right
    assert type(formula) is Imp and type(formula.left) is And and type(formula.right) is Bot
    assert "peano_lab.library.theorems" not in sys.modules


def test_no_parent_generator_or_checker_is_used_for_target_binding():
    tree = ast.parse(Path(quadratic.__file__).read_text())
    forbidden_generators = {"prove_signed_norm_zero", "prove_quadratic_norm_product",
                            "prove_signed_product_nonzero", "Basis"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            assert name not in forbidden_generators
    frozen = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "frozen_quadratic_nonzero_target")
    for node in ast.walk(frozen):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            assert not name.startswith(("prove_", "check_", "read_archived", "merge_archived"))


def test_frozen_source_map_includes_actual_compressed_proof_inputs():
    pins = quadratic.quadratic_nonzero_source_pins()
    for name, pin in pins.items():
        raw = (quadratic.ROOT / name).read_bytes()
        assert pin == dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
        assert len(raw) <= 16 * 1024**2
    for pin in quadratic.ARCHIVES.values():
        assert pins[pin["path"]] == dict(bytes=pin["bytes"], sha256=pin["sha256"])


def test_all_parent_bodies_and_dependency_orders_are_preserved_when_shared():
    rows, metrics = quadratic.merge_archived_rows()
    assert len(rows) == 218 and metrics["duplicate_rows"] == 59
    assert metrics["body_nodes"] == 81031 and metrics["max_depth"] == 84
    assert metrics["row_bytes"] == 3206485
    assert sum(len(row[2]) for row in rows) == 590
    assert quadratic.json_hash(rows) == quadratic.MERGED_ROWS_SHA256
    assert metrics["endpoints"] == quadratic.MERGED_ENDPOINTS
    for code in quadratic.ARCHIVES:
        root, target, originals = quadratic.read_archived_rows(code)
        remap = metrics["parent_maps"][code]
        assert rows[remap[root]][1] == target
        for old, original in enumerate(originals):
            shared = rows[remap[old]]
            assert shared[0] == original[0]  # exact original fuel
            assert shared[1] == original[1]  # exact original conclusion
            assert shared[2] == [remap[d] for d in original[2]]
            assert shared[3] == original[3]  # the body, not a receipt


def test_all_small_signed_models_and_nonnormalized_outputs():
    checked = 0
    for A, B, C, D in product(range(-2, 3), repeat=4):
        R, T = A*C+2*B*D, A*D+B*C
        pairs = [_pair(value, i+1) for i, value in enumerate((A, B, C, D))]
        for output_shift in (5, 9):
            values = tuple(x for pair in (*pairs, _pair(R, output_shift), _pair(T, output_shift+1)) for x in pair)
            premises, conclusion = _model(values)
            assert premises[0] and premises[1]
            if all(premises):
                assert conclusion
            assert (R*R-2*T*T) == (A*A-2*B*B)*(C*C-2*D*D)
            checked += 1
    assert checked == 1250


@pytest.mark.parametrize("omitted,signed", (
    (0, (1, 0, 1, 0)),
    (1, (1, 0, 0, 1)),
    (2, (0, 0, 1, 0)),
    (3, (1, 0, 0, 0)),
))
def test_each_explicit_premise_has_an_actual_counterexample_if_removed(omitted, signed):
    pairs = [_pair(value, i+1) for i, value in enumerate(signed)]
    values = tuple(x for pair in (*pairs, (5, 5), (7, 7)) for x in pair)
    premises, conclusion = _model(values)
    assert all(value for i, value in enumerate(premises) if i != omitted)
    assert not premises[omitted] and not conclusion
    assert _omit_premise(omitted) != quadratic.frozen_quadratic_nonzero_target()


def test_the_quadratic_weight_two_cannot_be_replaced_by_one():
    # (1+sqrt(1))(1-sqrt(1)) is zero, unlike the intended sqrt(2) ring.
    pairs = [_pair(value, i+1) for i, value in enumerate((1, 1, 1, -1))]
    values = tuple(x for pair in (*pairs, (5, 5), (7, 7)) for x in pair)
    wrong_premises, conclusion = _model(values, weight=1)
    assert all(wrong_premises) and not conclusion
    assert not _model(values, weight=2)[0][0]


def test_changed_target_and_corrupt_archive_fail_closed(monkeypatch, tmp_path):
    with monkeypatch.context() as patch:
        patch.setattr(quadratic, "QUADRATIC_NONZERO_SOURCE", quadratic.QUADRATIC_NONZERO_SOURCE.replace("2*", "1*"))
        with pytest.raises(quadratic.QuadraticNonzeroError, match="target AST"):
            quadratic.frozen_quadratic_nonzero_target()
    wrong = tmp_path / "wrong-parent.json.gz"
    wrong.write_bytes(b"not an archived ordinary proof\n")
    paths = {code: quadratic.ROOT / pin["path"] for code, pin in quadratic.ARCHIVES.items()}
    paths["SN001"] = wrong
    with pytest.raises(quadratic.QuadraticNonzeroError, match="input size/hash"):
        quadratic.read_archived_rows("SN001", archive_paths=paths)


def test_forged_inert_parent_row_cannot_survive_the_exact_merged_pin(monkeypatch):
    original_reader = quadratic.read_archived_rows
    def altered(code, **kwargs):
        root, target, rows = original_reader(code, **kwargs)
        if code == "SN003":
            rows[root][3] = ["eq_refl", ["zero"]]
        return root, target, rows
    monkeypatch.setattr(quadratic, "read_archived_rows", altered)
    with pytest.raises(quadratic.QuadraticNonzeroError, match="merged cone changed"):
        quadratic.merge_archived_rows()


@pytest.mark.parametrize("kwargs", (
    {"max_nodes": 220}, {"max_total_body_nodes": 81030},
))
def test_early_caps_stop_before_any_archive_or_proof_construction(monkeypatch, kwargs):
    from sqrt2_power_binary_dag import BinaryDAGLimits
    def forbidden(*args, **kw):
        raise AssertionError("exhausted structural cap reached construction")
    monkeypatch.setattr(quadratic, "merge_archived_rows", forbidden)
    monkeypatch.setattr(quadratic, "_root_body", forbidden)
    with pytest.raises(quadratic.QuadraticNonzeroError, match="before construction"):
        quadratic.prove_quadratic_nonzero(limits=BinaryDAGLimits(**kwargs))


@pytest.mark.parametrize("kwargs", (
    {"max_payload_bytes": 3206484}, {"max_depth": 40},
))
def test_smaller_archive_byte_and_depth_limits_are_not_silently_widened(kwargs):
    from sqrt2_power_binary_dag import BinaryDAGLimits
    with pytest.raises(quadratic.QuadraticNonzeroError):
        quadratic.merge_archived_rows(limits=BinaryDAGLimits(**kwargs))


def test_native_full_ordinary_ha_and_fresh_canonical_replay(certificate):
    from peano_lab.library.proof_bundle import check_encoded_proof_bundle
    result = certificate
    assert result.target == result.receipt.target == quadratic.frozen_quadratic_nonzero_target()
    assert result.target_ast_sha256 == quadratic.TARGET_SHA256
    assert len(result.bundle.nodes) == result.receipt.kernel_calls == 221
    assert result.bundle.root == 220
    assert result.bundle.nodes[220].dependencies == (191, 214, 217, 215, 216, 218, 219)
    assert result.receipt.total_body_nodes <= 200000
    assert result.max_proof_depth <= 256
    assert len(result.payload.encode()) <= 8 * 1024**2
    assert result.provenance["actual_shared_ancestor_nodes"] == 218
    assert result.provenance["actual_shared_ancestor_body_nodes"] == 81031
    assert result.provenance["exact_duplicate_rows_shared"] == 59
    assert result.provenance["regenerated_parent_generators"] == 0
    assert not result.provenance["archive_status_is_proof_authority"]
    assert result.provenance["IR_parents_closed"] == result.provenance["library_admissions"] == 0
    assert result.provenance["new_axioms"] == result.provenance["new_definitions"] == []
    assert not result.provenance["finite_product_claim"] and not result.provenance["irrationality_claim"]
    assert check_encoded_proof_bundle(result.payload).target == result.target


def test_native_rejects_all_omitted_premises_and_wrong_quadratic_weight(certificate):
    from sqrt2_power_native import closed_formula
    from peano_lab.kernel.checker import check
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    for i in range(4):
        target = _omit_premise(i)
        assert not check((), root.body, _curried(bundle, replace(root, target=target)))
    wrong = closed_formula(quadratic.QUADRATIC_NONZERO_SOURCE.replace("2*", "1*"))
    assert not check((), root.body, _curried(bundle, replace(root, target=wrong)))


def test_native_rejects_missing_parent_or_helper_dependencies(certificate):
    from peano_lab.kernel.checker import check
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    for i in range(len(root.dependencies)):
        dependencies = root.dependencies[:i] + root.dependencies[i+1:]
        assert not check((), root.body, _curried(bundle, replace(root, dependencies=dependencies)))


def test_native_rejects_false_caller_and_forged_actual_ancestor(certificate):
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    bundle = certificate.bundle
    with pytest.raises(ProofBundleError, match="exact caller target"):
        check_proof_bundle(bundle, Bot())
    for identifier in (0, 191, 214, 217, bundle.root):
        nodes = list(bundle.nodes)
        nodes[identifier] = replace(nodes[identifier], body=EqRefl(Zero()))
        with pytest.raises(ProofBundleError, match="kernel rejected"):
            check_proof_bundle(replace(bundle, nodes=tuple(nodes)), certificate.target)
