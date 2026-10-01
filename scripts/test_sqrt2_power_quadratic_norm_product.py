"""SN003 source calibration and separately selectable native proof tests.

The unittest class is proof-free. The pytest module fixture below is used only
by test_native_* functions, which belong in the root-owned guarded worker.
Finite integer models are never substituted for original-HA certificates.
"""

from itertools import product
import unittest
from unittest.mock import patch

import pytest

import sqrt2_power_quadratic_norm_product as norm


def pair(z, offset=0):
    return max(z, 0) + offset, max(-z, 0) + offset


def times(A, B):
    return A[0] * B[0] + A[1] * B[1], A[0] * B[1] + A[1] * B[0]


def square(A, value):
    p, n = A
    return p*p+n*n == value+(p*n+n*p)


def balanced(A, B):
    return A[0] + B[1] == B[0] + A[1]


class QuadraticNormProductSourceTests(unittest.TestCase):
    def test_exact_public_shape_and_existing_square_definition(self):
        row = norm.source_contract()
        self.assertEqual(row["code"], "SN003")
        self.assertEqual(len(row["parameters"]), 18)
        self.assertEqual(len(set(row["parameters"])), 18)
        self.assertEqual(row["premise_count"], 8)
        self.assertEqual(row["source"].count(" -> "), 8)
        self.assertEqual(row["signed_square_definition"]["id"], "ND0157")
        self.assertEqual(row["signed_square_definition"]["arity"], 3)
        self.assertFalse(row["original_HA_checked"])
        self.assertFalse(row["closes_IR031"])
        self.assertFalse(row["closes_IR046"])
        self.assertFalse(row["Gaussian_GNorm_claim"])
        self.assertIsNone(row["resource_fit"])

    def test_both_product_balances_follow_all_six_square_premises(self):
        parts = norm.QUADRATIC_NORM_PRODUCT_SOURCE.split(". ", 1)[1].split(" -> ")
        self.assertEqual(tuple(parts[:6]), norm.SQUARE_SOURCES)
        self.assertEqual(parts[6], norm.REAL_PRODUCT_BALANCE_SOURCE)
        self.assertEqual(parts[7], norm.RADICAL_PRODUCT_BALANCE_SOURCE)
        self.assertEqual(parts[8], norm.CONCLUSION_SOURCE)
        self.assertIn("rp+", parts[6])
        self.assertTrue(parts[6].endswith("+rn"))
        self.assertIn("sp+", parts[7])
        self.assertTrue(parts[7].endswith("+sn"))

    def test_small_helpers_are_not_eighteen_variable_ring_targets(self):
        self.assertEqual([row["binders"] for row in norm.HELPERS], [1, 4, 2])
        for row in norm.HELPERS:
            self.assertNotIn(" -> ", row["source"])
            self.assertEqual(len(row["target_sha256"]), 64)
        self.assertEqual(len(norm.QUADRATIC_NORM_PRODUCT_TARGET_SHA256), 64)

    def test_original_target_ast_and_hostile_source_binding(self):
        from sqrt2_power_native import closed_formula, strip_target
        from peano_lab.library.proof_bundle import encode_formula
        target = norm.frozen_quadratic_norm_product_target()
        self.assertEqual(norm.json_hash(encode_formula(target)), norm.QUADRATIC_NORM_PRODUCT_TARGET_SHA256)
        binders, premises, _ = strip_target(target)
        self.assertEqual((binders, len(premises)), (18, 8))
        for row in norm.HELPERS:
            self.assertEqual(norm.json_hash(encode_formula(closed_formula(row["source"]))), row["target_sha256"])
        mutations = (
            norm.QUADRATIC_NORM_PRODUCT_SOURCE.replace("+2*(bp*dn+bn*dp)", "+3*(bp*dn+bn*dp)", 1),
            norm.QUADRATIC_NORM_PRODUCT_SOURCE.replace(norm.SQUARE_SOURCES[4]+" -> ", "", 1),
            norm.QUADRATIC_NORM_PRODUCT_SOURCE.replace("r+2*(a*d+b*c)", "r+2*(a*d+b*undeclared)", 1),
        )
        for source in mutations:
            self.assertNotEqual(source, norm.QUADRATIC_NORM_PRODUCT_SOURCE)
            with patch.object(norm, "QUADRATIC_NORM_PRODUCT_SOURCE", source):
                with self.assertRaises(ValueError):
                    norm.frozen_quadratic_norm_product_target()

    def test_two_local_ten_argument_aliases_roundtrip_without_changing_implication_shape(self):
        from sqrt2_power_definitions import parse_named
        from sqrt2_power_quadratic_definitions import QUADRATIC_DEFINITIONS
        from peano_lab.library.defined_syntax import _definition
        square_definition = _definition(stable_id="ND0157", name="SignedDifferenceSquare",
            parameters=("p", "n", "s"), template_source=norm.DEFINITION_TEMPLATE,
            summary="Existing signed square, instantiated locally for exact expansion testing.",
            category="existing_signed_integer_arithmetic", conceptual_dependencies=())
        registry = {square_definition.name: square_definition, **QUADRATIC_DEFINITIONS}
        self.assertEqual(set(QUADRATIC_DEFINITIONS), {"IQuadProductReal", "IQuadProductRadical"})
        for definition in QUADRATIC_DEFINITIONS.values():
            self.assertEqual(definition.arity, 10)
        source = "forall "+" ".join(norm.PARAMETERS)+". " + " -> ".join((
            "SignedDifferenceSquare(ap,an,a)", "SignedDifferenceSquare(bp,bn,b)",
            "SignedDifferenceSquare(cp,cn,c)", "SignedDifferenceSquare(dp,dn,d)",
            "SignedDifferenceSquare(rp,rn,r)", "SignedDifferenceSquare(sp,sn,t)",
            "IQuadProductReal(ap,an,bp,bn,cp,cn,dp,dn,rp,rn)",
            "IQuadProductRadical(ap,an,bp,bn,cp,cn,dp,dn,sp,sn)", norm.CONCLUSION_SOURCE))
        self.assertEqual(parse_named(source, registry=registry), norm.frozen_quadratic_norm_product_target())
        with self.assertRaises(ValueError):
            parse_named(source.replace("dp,dn,rp,rn)", "dp,dn,rp)"), registry=registry)

    def test_all_small_signed_inputs_with_nonnormalized_representatives(self):
        count = 0
        for signed in product((-1, 0, 1), repeat=4):
            A, B, C, D = [pair(z, i + 1) for i, z in enumerate(signed)]
            U, V, W, X = times(A, C), times(B, D), times(A, D), times(B, C)
            canonical_R = tuple(U[i] + 2*V[i] for i in range(2))
            canonical_I = tuple(W[i] + X[i] for i in range(2))
            R, I = tuple(z + 5 for z in canonical_R), tuple(z + 6 for z in canonical_I)
            a, b, c, d = (z*z for z in signed)
            r, t = (R[0] - R[1])**2, (I[0] - I[1])**2
            for args in ((A, a), (B, b), (C, c), (D, d), (R, r), (I, t)):
                self.assertTrue(square(*args))
            self.assertTrue(balanced(R, canonical_R))
            self.assertTrue(balanced(I, canonical_I))
            self.assertEqual(r + 2*(a*d+b*c), (a*c+(2*2)*(b*d))+2*t)
            count += 1
        self.assertEqual(count, 81)

    def test_negative_quadratic_norm_is_allowed_and_is_not_Gaussian_GNorm(self):
        A, B, C, D = 0, 1, 0, 1
        real, radical = A*C+2*B*D, A*D+B*C
        self.assertEqual((A*A-2*B*B), -2)
        self.assertEqual(real*real-2*radical*radical, (A*A-2*B*B)*(C*C-2*D*D))
        self.assertNotEqual(real*real+radical*radical, (A*A+B*B)*(C*C+D*D))

    def test_wrong_real_weight_and_missing_output_balance_are_detectable(self):
        # A=B=C=D=1: real3/radical2. Mutated real weight3 gives real4.
        a = b = c = d = 1
        wrong_r, t = 4*4, 2*2
        self.assertNotEqual(wrong_r+2*(a*d+b*c), (a*c+(2*2)*(b*d))+2*t)
        canonical_R = (3, 0)
        wrong_R = (4, 0)
        self.assertTrue(square(wrong_R, wrong_r))
        self.assertFalse(balanced(wrong_R, canonical_R))

    def test_omitting_each_square_premise_has_a_small_counterexample(self):
        # A=B=C=D=1, R=3, I=2; change only the omitted square witness.
        pairs = ((1, 0),)*4 + ((3, 0), (2, 0))
        for omitted in range(6):
            values = [1, 1, 1, 1, 9, 4]
            values[omitted] += 1
            self.assertTrue(all(square(pair_, value) for i, (pair_, value)
                                in enumerate(zip(pairs, values)) if i != omitted))
            self.assertFalse(square(pairs[omitted], values[omitted]))
            a, b, c, d, r, t = values
            self.assertNotEqual(r+2*(a*d+b*c), (a*c+(2*2)*(b*d))+2*t)

    def test_radical_output_balance_cannot_be_dropped(self):
        # True R=3/I=2 is replaced by I=3 with its own correct square witness.
        self.assertTrue(square((3, 0), 9))
        self.assertFalse(balanced((3, 0), (2, 0)))
        self.assertNotEqual(9+2*(1*1+1*1), (1*1+(2*2)*(1*1))+2*9)

    def test_small_helper_arithmetic_calibration(self):
        for x, y in product(range(4), repeat=2):
            self.assertEqual(x+x, 2*x)
            self.assertEqual(2*(x+2*y), (2*2)*y+2*x)
        for p, n, q, m in product(range(3), repeat=4):
            cross = p*(2*q)+n*(2*m)
            self.assertEqual(cross+cross, (2*2)*(p*q+n*m))

    def test_actual_inert_cone_contains_transport_and_all_required_bodies(self):
        ids, rows = norm.inert_selected_rows()
        self.assertEqual(ids, norm.ANCESTOR_IDS)
        self.assertEqual(len(ids), 33)
        self.assertEqual(sum(len(row[2]) for row in rows), 106)
        self.assertEqual(norm.json_hash(rows), norm.SELECTED_ROWS_SHA256)
        self.assertEqual(len(norm.canonical(rows)), 353005)
        self.assertIn(693, norm.ROOT_DEPENDENCIES)
        self.assertIn(272, norm.ROOT_DEPENDENCIES)
        table = dict(zip(ids, rows))
        for i, pin in norm.ENDPOINTS.items():
            self.assertEqual(norm.json_hash(table[i]), pin["row_sha256"])
            self.assertEqual(norm.json_hash(table[i][1]), pin["target_sha256"])
        self.assertNotIn(710, ids)  # Gaussian norm multiplication is NOT reused.

    def test_pins_and_lazy_source_layer_do_not_claim_native_acceptance(self):
        self.assertIn("scripts/sqrt2_power_quadratic_norm_product.py", norm.norm_product_source_pins())
        self.assertNotIn("peano_lab", norm.__dict__)
        self.assertNotIn("sqrt2_power_native", norm.__dict__)
        self.assertFalse(norm.source_contract()["original_HA_checked"])


@pytest.fixture(scope="module")
def certificate():
    """Root-owned native worker only; each output contains every actual body."""
    return norm.prove_quadratic_norm_product()


def _curried(bundle, node):
    from peano_lab.kernel.formulas import Imp
    target = node.target
    for dependency in reversed(node.dependencies):
        target = Imp(bundle.nodes[dependency].target, target)
    return target


def _omit_premise(index):
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall, Imp
    binders, premises, conclusion = strip_target(norm.frozen_quadratic_norm_product_target())
    assert binders == 18 and len(premises) == 8 and 0 <= index < 8
    for i in reversed(range(8)):
        if i != index:
            conclusion = Imp(premises[i], conclusion)
    for _ in range(binders):
        conclusion = Forall(conclusion)
    return conclusion


def test_native_exact_37_node_bundle_and_same_canonical_bytes_replay(certificate):
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import check_encoded_proof_bundle, encode_proof_bundle
    limits = BinaryDAGLimits()
    result = certificate
    assert result.target == result.receipt.target == norm.frozen_quadratic_norm_product_target()
    assert result.target_ast_sha256 == norm.QUADRATIC_NORM_PRODUCT_TARGET_SHA256
    assert len(result.bundle.nodes) == result.receipt.node_count == result.receipt.kernel_calls == 37
    assert result.bundle.root == 36
    assert result.receipt.dependency_edges == 115
    assert result.bundle.nodes[36].dependencies == (19, 23, 26, 31, 32, 13, 33, 34, 35)
    assert result.receipt.total_body_nodes <= limits.max_total_body_nodes == 200000
    assert result.max_proof_depth <= limits.max_depth == 256
    assert len(result.payload.encode()) <= limits.max_payload_bytes == 8 * 1024**2
    assert encode_proof_bundle(result.bundle, result.target, limits=limits.bundle_limits()) == result.payload
    replay = check_encoded_proof_bundle(result.payload, limits=limits.bundle_limits())
    assert replay.target == result.target
    assert replay.node_count == 37 and replay.dependency_edges == 115
    provenance = result.provenance
    assert provenance["original_HA_checked"] and provenance["canonical_bytes_replayed"]
    assert provenance["empty_context"] and provenance["arbitrary_output_representatives"]
    assert provenance["output_square_transport_node"] == 693
    assert provenance["actual_ancestor_nodes"] == 33
    assert provenance["actual_ancestor_body_nodes"] == 4468
    assert provenance["new_axioms"] == provenance["external_certificate_references"] == []
    assert provenance["IR_parents_closed"] == provenance["library_admissions"] == 0
    assert not provenance["closes_IR031"] and not provenance["closes_IR046"]
    assert not provenance["rational_or_real_claim"] and not provenance["Gaussian_GNorm_claim"]


def test_native_actual_ancestor_bodies_and_ordered_dependencies(certificate):
    from peano_lab.library.proof_bundle import encode_formula, encode_proof
    ids, rows = norm.inert_selected_rows()
    remap = {old: new for new, old in enumerate(ids)}
    assert tuple(ids) == norm.ANCESTOR_IDS
    for old, row in zip(ids, rows):
        node = certificate.bundle.nodes[remap[old]]
        assert node.node_id == remap[old]
        assert node.fuel == row[0]
        assert encode_formula(node.target) == row[1]
        assert node.dependencies == tuple(remap[dependency] for dependency in row[2])
        assert encode_proof(node.body) == row[3]
    for index, helper in enumerate(norm.HELPERS, start=33):
        node = certificate.bundle.nodes[index]
        assert node.dependencies == ()
        assert norm.json_hash(encode_formula(node.target)) == helper["target_sha256"]
    assert norm.json_hash(rows) == certificate.provenance["selected_rows_sha256"] == norm.SELECTED_ROWS_SHA256
    assert 710 not in ids  # Gaussian GNorm product is neither assumed nor relabeled.


def test_native_original_HA_rejects_each_of_eight_omitted_premises(certificate):
    from dataclasses import replace
    from peano_lab.kernel.checker import check
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    for omitted in range(8):
        changed = _omit_premise(omitted)
        assert changed != certificate.target
        # This is a real original-HA rejection, not merely a codec error.
        assert not check((), root.body, _curried(bundle, replace(root, target=changed)))
        with pytest.raises(ProofBundleError, match="exact caller target"):
            check_proof_bundle(bundle, changed, limits=BinaryDAGLimits().bundle_limits())


def test_native_original_HA_rejects_false_conclusion_weights(certificate):
    from dataclasses import replace
    from sqrt2_power_native import closed_formula
    from peano_lab.kernel.checker import check
    root = certificate.bundle.nodes[certificate.bundle.root]
    for wrong_conclusion in (
        "r+3*(a*d+b*c)=(a*c+(2*2)*(b*d))+2*t",
        "r+2*(a*d+b*c)=(a*c+(2*2)*(b*d))+3*t",
    ):
        changed = closed_formula(norm.QUADRATIC_NORM_PRODUCT_SOURCE.replace(norm.CONCLUSION_SOURCE, wrong_conclusion))
        assert changed != certificate.target
        assert not check((), root.body, _curried(certificate.bundle, replace(root, target=changed)))
    # Both mutations are actually false at A=B=C=D=1, not just different ASTs.
    assert 9+3*(1+1) != (1+4)+2*4
    assert 9+2*(1+1) != (1+4)+3*4


def test_native_original_HA_rejects_missing_dependency_and_forged_body(certificate):
    from dataclasses import replace
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    # Remove the actual output-square transport dependency, retaining its body.
    omitted = replace(root, dependencies=root.dependencies[1:])
    assert not check((), omitted.body, _curried(bundle, omitted))
    assert not check((), EqRefl(Zero()), _curried(bundle, root))
    # A genuine checker rejection at the first ancestor is fast and ensures an
    # apparently valid root cannot authenticate a replaced source proof body.
    forged = replace(bundle.nodes[0], body=EqRefl(Zero()))
    with pytest.raises(ProofBundleError, match="kernel rejected"):
        check_proof_bundle(replace(bundle, nodes=(forged,) + bundle.nodes[1:]), certificate.target,
                           limits=BinaryDAGLimits().bundle_limits())


if __name__ == "__main__":
    unittest.main()
