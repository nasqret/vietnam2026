"""RN001 source calibration and separately selectable guarded native tests.

Source tests inspect exact statements/ancestors and finite models, never claim
that host arithmetic is a proof. Native functions are for the root-owned worker.
"""
from itertools import product
import unittest
from unittest.mock import patch

import pytest

import sqrt2_power_rational_norm_transport as norm


def pair(value, offset):
    return max(value, 0) + offset, max(-value, 0) + offset


def square(p, n, s):
    return p*p+n*n == s+(p*n+n*p)


def irat_eq(p, n, d, q, m, e):
    return d != 0 and e != 0 and p*e+m*d == n*e+q*d


class RationalNormTransportSourceTests(unittest.TestCase):
    def test_exact_named_and_expanded_statement_shape(self):
        from sqrt2_power_native import strip_target
        from sqrt2_power_definitions import parse_named
        from peano_lab.library.proof_bundle import encode_formula
        target = norm.frozen_rational_norm_transport_target()
        named = parse_named(norm.RATIONAL_NORM_TRANSPORT_NAMED_SOURCE,
                            registry=norm.rational_norm_definitions())
        binders, premises, _ = strip_target(target)
        self.assertEqual(target, named)
        self.assertEqual((binders, len(premises)), (14, 6))
        self.assertEqual(len(set(norm.PARAMETERS)), 14)
        self.assertEqual(norm.json_hash(encode_formula(target)), norm.RATIONAL_NORM_TRANSPORT_TARGET_SHA256)
        self.assertTrue(norm.RATIONAL_NORM_TRANSPORT_NAMED_SOURCE.endswith(
            "IRatEq(a,2*b,d*d,c,2*t,e*e)"))

    def test_existing_definitions_are_exact_and_no_new_alias_is_added(self):
        from sqrt2_power_definitions import DEFINITIONS
        definitions = norm.rational_norm_definitions()
        self.assertEqual(set(definitions), {"IRatValid", "IRatEq", "SignedDifferenceSquare"})
        self.assertIs(definitions["IRatValid"], DEFINITIONS["IRatValid"])
        self.assertIs(definitions["IRatEq"], DEFINITIONS["IRatEq"])
        self.assertEqual(definitions["SignedDifferenceSquare"].stable_id, "ND0157")
        self.assertEqual(definitions["IRatEq"].conceptual_dependencies, ("IRatValid",))
        self.assertEqual(definitions["SignedDifferenceSquare"].conceptual_dependencies, ())
        self.assertEqual(norm.rational_norm_transport_manifest()["new_definitions"], 0)

    def test_contract_is_not_a_proof_or_parent_closure_claim(self):
        row = norm.rational_norm_transport_manifest()
        self.assertEqual(row["code"], "RN001")
        self.assertEqual(row["premise_count"], 6)
        self.assertTrue(row["arbitrary_signed_representatives"])
        self.assertTrue(row["allows_negative_norm"])
        self.assertFalse(row["original_HA_checked"])
        self.assertFalse(row["independent_lean_checked"])
        self.assertFalse(row["closes_IR031"])
        self.assertFalse(row["closes_IR032"])
        self.assertFalse(row["real_interpretation"])
        self.assertEqual(row["IR_parents_closed"], 0)
        self.assertEqual(row["library_admissions"], 0)
        self.assertIsNone(row["resource_fit"])

    def test_hostile_sources_cannot_rebind_the_exact_target(self):
        mutations = (
            norm.RATIONAL_NORM_TRANSPORT_SOURCE.replace("(2*b)*(e*e)", "(3*b)*(e*e)"),
            norm.RATIONAL_NORM_TRANSPORT_SOURCE.replace(norm.SQUARE_SOURCES[2]+" -> ", ""),
            norm.RATIONAL_NORM_TRANSPORT_SOURCE.replace("a*(e*e)", "a*e"),
            norm.RATIONAL_NORM_TRANSPORT_SOURCE.replace("+c*(d*d)", "+unknown*(d*d)"),
        )
        for changed in mutations:
            self.assertNotEqual(changed, norm.RATIONAL_NORM_TRANSPORT_SOURCE)
            with patch.object(norm, "RATIONAL_NORM_TRANSPORT_SOURCE", changed):
                with self.assertRaises(ValueError):
                    norm.frozen_rational_norm_transport_target()
        changed = norm.RATIONAL_NORM_TRANSPORT_NAMED_SOURCE.replace("c,2*t,e*e)", "c,3*t,e*e)")
        with patch.object(norm, "RATIONAL_NORM_TRANSPORT_NAMED_SOURCE", changed):
            with self.assertRaises(ValueError):
                norm.frozen_rational_norm_transport_target()

    def test_actual_inert_cone_has_all_small_signed_transport_ancestors(self):
        ids, rows = norm.inert_selected_rows()
        self.assertEqual(ids, norm.ANCESTOR_IDS)
        self.assertEqual(len(ids), 28)
        self.assertEqual(sum(len(row[2]) for row in rows), 63)
        self.assertEqual(norm.json_hash(rows), norm.SELECTED_ROWS_SHA256)
        self.assertEqual(len(norm.canonical(rows)), 160288)
        self.assertEqual(norm.ROOT_DEPENDENCIES, (2, 6, 8, 64, 691, 693, 715))
        table = dict(zip(ids, rows))
        for old, pin in norm.ENDPOINTS.items():
            self.assertEqual(norm.json_hash(table[old]), pin["row_sha256"])
            self.assertEqual(norm.json_hash(table[old][1]), pin["target_sha256"])
            self.assertEqual(tuple(table[old][2]), pin["dependencies"])
        self.assertNotIn(710, ids)  # Not Gaussian norm multiplication.

    def test_all_small_noncanonical_signed_pairs_with_changed_denominators(self):
        count = 0
        for A, B, d, k in product(range(-2, 3), range(-2, 3), range(1, 4), range(1, 4)):
            ap, an = pair(A, 2)
            bp, bn = pair(B, 3)
            cp, cn = pair(k*A, 5)
            dp, dn = pair(k*B, 7)
            e = d*k
            a, b, c, t = A*A, B*B, (k*A)**2, (k*B)**2
            self.assertTrue(irat_eq(ap, an, d, cp, cn, e))
            self.assertTrue(irat_eq(bp, bn, d, dp, dn, e))
            for p, n, s in ((ap, an, a), (bp, bn, b), (cp, cn, c), (dp, dn, t)):
                self.assertTrue(square(p, n, s))
            self.assertTrue(irat_eq(a, 2*b, d*d, c, 2*t, e*e))
            count += 1
        self.assertEqual(count, 225)

    def test_negative_norm_and_zero_coefficients_are_allowed(self):
        # sqrt(2)/2 = (3 sqrt(2))/6; norm is -1/2 in both representatives.
        self.assertTrue(irat_eq(0, 0, 2, 0, 0, 6))
        self.assertTrue(irat_eq(1, 0, 2, 3, 0, 6))
        self.assertTrue(irat_eq(0, 2, 4, 0, 18, 36))
        self.assertLess(0-2*1, 0)
        # A zero represented coordinate does not require componentwise zeros.
        self.assertTrue(square(4, 4, 0))
        self.assertTrue(irat_eq(4, 4, 2, 7, 7, 3))

    def test_square_denominators_cannot_be_replaced_by_unsquared_denominators(self):
        self.assertTrue(irat_eq(2, 0, 2, 1, 0, 1))
        self.assertTrue(irat_eq(4, 0, 4, 1, 0, 1))
        self.assertFalse(irat_eq(4, 0, 2, 1, 0, 1))

    def test_omitting_each_square_has_a_small_counterexample(self):
        # Both coordinates are 1/1 in each representative. Change only one
        # unguarded square witness; all other square/equivalence premises hold.
        for omitted in range(4):
            values = [1, 1, 1, 1]
            values[omitted] = 2
            self.assertTrue(all(square(1, 0, s) for i, s in enumerate(values) if i != omitted))
            self.assertFalse(square(1, 0, values[omitted]))
            a, b, c, t = values
            self.assertFalse(irat_eq(a, 2*b, 1, c, 2*t, 1))

    def test_both_coordinate_equivalences_and_denominator_validity_matter(self):
        # Omit real-coordinate equality: 1 differs from 2, so norms differ.
        self.assertTrue(irat_eq(0, 0, 1, 0, 0, 1))
        self.assertFalse(irat_eq(1, 0, 1, 4, 0, 1))
        # Omit radical-coordinate equality: sqrt(2) differs from 2 sqrt(2).
        self.assertFalse(irat_eq(0, 2, 1, 0, 8, 1))
        # Mere cleared equality with zero denominators is not IRatEq.
        self.assertEqual(0*1+0*0, 0*1+0*0)
        self.assertFalse(irat_eq(0, 0, 0, 0, 0, 1))
        self.assertFalse(irat_eq(0, 0, 0*0, 0, 0, 1*1))

    def test_source_pins_include_ordinary_kernel_and_unchanged_definitions(self):
        pins = norm.rational_norm_transport_source_pins()
        self.assertIn("peano-lab/py/peano_lab/kernel/checker.py", pins)
        self.assertIn("scripts/sqrt2_power_definitions.py", pins)
        self.assertIn("scripts/sqrt2_power_rational_norm_transport.py", pins)
        self.assertTrue(all(set(row) == {"bytes", "sha256"} for row in pins.values()))


@pytest.fixture(scope="module")
def certificate():
    return norm.prove_rational_norm_transport()


def _curried(bundle, node):
    from peano_lab.kernel.formulas import Imp
    formula = node.target
    for dependency in reversed(node.dependencies):
        formula = Imp(bundle.nodes[dependency].target, formula)
    return formula


def _omit_premise(index):
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall, Imp
    binders, premises, result = strip_target(norm.frozen_rational_norm_transport_target())
    assert binders == 14 and len(premises) == 6 and 0 <= index < 6
    for i in reversed(range(6)):
        if i != index:
            result = Imp(premises[i], result)
    for _ in range(binders):
        result = Forall(result)
    return result


def test_native_exact_29_node_bundle_and_canonical_replay(certificate):
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import check_encoded_proof_bundle, encode_proof_bundle
    limits = BinaryDAGLimits()
    assert certificate.target == certificate.receipt.target == norm.frozen_rational_norm_transport_target()
    assert certificate.target_ast_sha256 == norm.RATIONAL_NORM_TRANSPORT_TARGET_SHA256
    assert len(certificate.bundle.nodes) == certificate.receipt.node_count == certificate.receipt.kernel_calls == 29
    assert certificate.bundle.root == 28
    assert certificate.receipt.dependency_edges == 70
    assert certificate.bundle.nodes[28].dependencies == (2, 6, 8, 14, 21, 22, 27)
    assert certificate.receipt.total_body_nodes <= limits.max_total_body_nodes == 200000
    assert certificate.max_proof_depth <= limits.max_depth == 256
    assert len(certificate.payload.encode()) <= limits.max_payload_bytes == 8 * 1024**2
    assert encode_proof_bundle(certificate.bundle, certificate.target, limits=limits.bundle_limits()) == certificate.payload
    assert check_encoded_proof_bundle(certificate.payload, limits=limits.bundle_limits()).target == certificate.target
    provenance = certificate.provenance
    assert provenance["original_HA_checked"] and provenance["canonical_bytes_replayed"]
    assert provenance["empty_context"] and provenance["arbitrary_signed_representatives"]
    assert provenance["actual_ancestor_nodes"] == 28
    assert provenance["actual_ancestor_body_nodes"] == 2438
    assert provenance["solver_calls"] == provenance["ring_normalizer_calls"] == 0
    assert provenance["new_axioms"] == provenance["external_certificate_references"] == []
    assert provenance["IR_parents_closed"] == provenance["library_admissions"] == 0
    assert not provenance["closes_IR031"] and not provenance["closes_IR032"]
    assert not provenance["real_interpretation"]


def test_native_all_actual_ancestor_bodies_and_ordered_dependencies(certificate):
    from peano_lab.library.proof_bundle import encode_formula, encode_proof
    ids, rows = norm.inert_selected_rows()
    remap = {old: new for new, old in enumerate(ids)}
    for old, row in zip(ids, rows):
        node = certificate.bundle.nodes[remap[old]]
        assert node.node_id == remap[old] and node.fuel == row[0]
        assert encode_formula(node.target) == row[1]
        assert encode_proof(node.body) == row[3]
        assert node.dependencies == tuple(remap[d] for d in row[2])


def test_native_original_HA_rejects_each_missing_premise(certificate):
    from dataclasses import replace
    from peano_lab.kernel.checker import check
    root = certificate.bundle.nodes[certificate.bundle.root]
    for omitted in range(6):
        changed = _omit_premise(omitted)
        assert changed != certificate.target
        assert not check((), root.body, _curried(certificate.bundle, replace(root, target=changed)))


def test_native_original_HA_rejects_wrong_weights_and_denominators(certificate):
    from dataclasses import replace
    from sqrt2_power_native import closed_formula
    from peano_lab.kernel.checker import check
    root = certificate.bundle.nodes[certificate.bundle.root]
    for wrong in (
        norm.CONCLUSION_SOURCE.replace("(2*b)*(e*e)", "(3*b)*(e*e)"),
        norm.CONCLUSION_SOURCE.replace("a*(e*e)", "a*e").replace("(2*b)*(e*e)", "(2*b)*e"),
        norm.CONCLUSION_SOURCE.replace("(d*d)", "d").replace("d*d=0", "d=0"),
    ):
        changed = closed_formula(norm.RATIONAL_NORM_TRANSPORT_SOURCE.replace(norm.CONCLUSION_SOURCE, wrong))
        assert changed != certificate.target
        assert not check((), root.body, _curried(certificate.bundle, replace(root, target=changed)))


def test_native_original_HA_rejects_removed_validity_and_forged_ancestor(certificate):
    from dataclasses import replace
    from sqrt2_power_native import closed_formula
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    changed_source = norm.RATIONAL_NORM_TRANSPORT_SOURCE.replace(
        norm.EQUIVALENCE_SOURCES[0], "(ap*e+cn*d=an*e+cp*d)").replace(
        norm.EQUIVALENCE_SOURCES[1], "(bp*e+dn*d=bn*e+dp*d)")
    changed = closed_formula(changed_source)
    assert not check((), root.body, _curried(bundle, replace(root, target=changed)))
    omitted = replace(root, dependencies=root.dependencies[:-1])
    assert not check((), root.body, _curried(bundle, omitted))
    assert not check((), EqRefl(Zero()), _curried(bundle, root))
    forged = replace(bundle.nodes[0], body=EqRefl(Zero()))
    with pytest.raises(ProofBundleError, match="kernel rejected"):
        check_proof_bundle(replace(bundle, nodes=(forged,)+bundle.nodes[1:]), certificate.target,
                           limits=BinaryDAGLimits().bundle_limits())


if __name__ == "__main__":
    unittest.main()
