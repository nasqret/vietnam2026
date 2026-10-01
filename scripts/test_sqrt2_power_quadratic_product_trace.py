"""QF001 source/finite-model calibration and separately selectable HA checks.

Only root-owned guarded native tests execute the proof producer. Host CRT and
integer computations calibrate the concrete trace definition, not HA evidence.
"""
from itertools import product
import gc
from math import lcm
import unittest
from unittest.mock import patch

import pytest

import sqrt2_power_quadratic_product_trace as trace


def signed_pair(value, offset=0):
    return max(value, 0)+offset, max(-value, 0)+offset


def represented(A):
    return A[0]-A[1], A[2]-A[3]


def nonzero(A):
    return not (A[0] == A[1] and A[2] == A[3])


def balances(A, B, C):
    ap, an, bp, bn = A
    cp, cn, dp, dn = B
    rp, rn, sp, sn = C
    real = rp+((ap*cn+an*cp)+2*(bp*dn+bn*dp)) == ((ap*cp+an*cn)+2*(bp*dp+bn*dn))+rn
    radical = sp+((ap*dn+an*dp)+(bp*cn+bn*cp)) == ((ap*dp+an*dn)+(bp*cp+bn*cn))+sn
    return real, radical


def pack_beta(values):
    """Host-only constructive CRT calibration of an actual finite beta code."""
    scale = lcm(*range(1, len(values)+1))*(max(values, default=0)+1)
    code, modulus_product = 0, 1
    for i, value in enumerate(values):
        modulus = 1+(i+1)*scale
        adjustment = ((value-code)*pow(modulus_product, -1, modulus)) % modulus
        code += modulus_product*adjustment
        modulus_product *= modulus
    return code, scale


def beta_at(code, scale, index, value):
    modulus = 1+(index+1)*scale
    return value < modulus and code % modulus == value


def streams(values):
    return tuple(pack_beta([row[i] for row in values]) for i in range(4))


def quad_at(table, index, values):
    return all(beta_at(*stream, index, value) for stream, value in zip(table, values))


class QuadraticProductTraceSourceTests(unittest.TestCase):
    def test_exact_expansion_target_and_negative_conclusion_shape(self):
        from sqrt2_power_native import strip_target
        from peano_lab.kernel.formulas import And, Bot
        from peano_lab.library.proof_bundle import encode_formula
        target = trace.frozen_quadratic_product_trace_target()
        binders, opened, conclusion = strip_target(target)
        self.assertEqual(binders, 21)
        self.assertEqual(len(opened), 4)  # Three premises, then the final negation.
        self.assertIs(type(opened[-1]), And)
        self.assertIs(type(conclusion), Bot)
        self.assertEqual(trace.json_hash(encode_formula(target)), trace.TARGET_SHA256)
        self.assertEqual(len(trace.canonical(encode_formula(target))), 7075)
        self.assertEqual(trace.source_contract()["premise_count"], 3)

    def test_four_new_definitions_and_exact_eight_node_dependency_closure(self):
        registry = trace.definition_registry()
        definitions = trace.trace_definitions()
        self.assertEqual(set(registry), {"Lt", "BetaAt", "IQuadProductReal", "IQuadProductRadical",
            "IQuadAt", "IQuadProductStep", "IQuadProductTrace", "IQuadNonzeroFactors"})
        self.assertEqual([d.stable_id for d in definitions.values()], ["ND0390", "ND0391", "ND0392", "ND0393"])
        self.assertEqual([d.arity for d in definitions.values()], [13, 17, 17, 9])
        self.assertEqual(registry["Lt"].conceptual_dependencies, ())
        self.assertEqual(registry["BetaAt"].conceptual_dependencies, ())
        for name, definition in definitions.items():
            self.assertTrue(set(definition.conceptual_dependencies) <= registry.keys())
            self.assertNotIn(name, definition.conceptual_dependencies)
        self.assertEqual(sum(len(d.conceptual_dependencies) for d in definitions.values()), 9)

    def test_trace_definition_has_no_hidden_nonzero_hypothesis(self):
        names = {row[1]: row for row in trace.DEFINITION_ROWS}
        step = names["IQuadProductStep"][3]
        product_trace = names["IQuadProductTrace"][3]
        self.assertIn("exists ap an bp bn cp cn dp dn rp rn sp sn.", step)
        self.assertEqual(step.count("IQuadAt("), 3)
        self.assertIn("IQuadProductReal(", step)
        self.assertIn("IQuadProductRadical(", step)
        self.assertIn(",S i,rp,rn,sp,sn)", step)
        self.assertIn(",0,1,0,0,0)", product_trace)
        self.assertNotIn("~", step)
        self.assertNotIn("~", product_trace)
        self.assertNotIn("IQuadNonzeroFactors", product_trace)

    def test_source_only_scope_does_not_claim_existence_or_irrationality(self):
        row = trace.source_contract()
        self.assertTrue(row["conditional_on_actual_trace"])
        self.assertTrue(row["nonzero_factors_separate_premise"])
        self.assertFalse(row["trace_existence_proved"])
        self.assertFalse(row["real_interpretation"])
        self.assertFalse(row["rational_denominator_claim"])
        self.assertFalse(row["closes_IR046"])
        self.assertFalse(row["closes_IR072"])
        self.assertFalse(row["original_HA_checked"])
        self.assertEqual(row["library_admissions"], 0)

    def test_frozen_source_and_definition_mutations_fail_closed(self):
        changed = trace.NAMED_SOURCE.replace(
            "IQuadNonzeroFactors(ab,ac,bb,bc,cb,cc,db,dc,L) -> ", "")
        with patch.object(trace, "NAMED_SOURCE", changed):
            with self.assertRaises(ValueError):
                trace.frozen_quadratic_product_trace_target()
        for index, old, new in ((1, ",S i,rp,rn,sp,sn)", ",i,rp,rn,sp,sn)"),
                                (2, ",0,1,0,0,0)", ",0,0,0,0,0)")):
            rows = list(trace.DEFINITION_ROWS)
            row = list(rows[index])
            self.assertIn(old, row[3])
            row[3] = row[3].replace(old, new)
            rows[index] = tuple(row)
            with patch.object(trace, "DEFINITION_ROWS", tuple(rows)):
                with self.assertRaises(ValueError):
                    trace.definition_registry()

    def test_definition_capture_arity_and_collision_guards(self):
        from sqrt2_power_definitions import parse_named
        registry = trace.definition_registry()
        names = trace.FACTOR_PARAMETERS + ("i", "ap", "an", "bp", "bn")
        actual = parse_named("IQuadAt(ab,ac,bb,bc,cb,cc,db,dc,S i,ap+an,an,bp,bn)", names, registry)
        expected = parse_named(
            "BetaAt(ab,ac,S i,ap+an) /\\ (BetaAt(bb,bc,S i,an) /\\ "
            "(BetaAt(cb,cc,S i,bp) /\\ BetaAt(db,dc,S i,bn)))", names, registry)
        self.assertEqual(actual, expected)
        with self.assertRaises(ValueError):
            parse_named("IQuadAt(ab,ac,bb,bc,cb,cc,db,dc,i,ap,an,bp)", names, registry)
        rows = list(trace.DEFINITION_ROWS)
        row = list(rows[0])
        row[0] = 388
        rows[0] = tuple(row)
        with patch.object(trace, "DEFINITION_ROWS", tuple(rows)):
            with self.assertRaises(ValueError):
                trace.definition_registry()

    def test_actual_beta_order_archive_cone_and_endpoint_sources(self):
        from sqrt2_power_native import closed_formula
        from peano_lab.library.proof_bundle import encode_formula
        ids, rows = trace.inert_beta_rows()
        self.assertEqual(ids, trace.ANCESTOR_IDS)
        self.assertEqual(len(ids), 19)
        self.assertEqual(sum(len(row[2]) for row in rows), 24)
        self.assertEqual(len(trace.canonical(rows)), 22720)
        self.assertEqual(trace.json_hash(rows), trace.ANCESTOR_ROWS_SHA256)
        table = dict(zip(ids, rows))
        for old, pin in trace.ENDPOINTS.items():
            self.assertEqual(table[old][1], encode_formula(closed_formula(pin["source"])))
            self.assertEqual(trace.json_hash(table[old]), pin["row_sha256"])

    def test_full_qn_archive_and_lossless_merged_rows_not_receipt_lookup(self):
        root, target, original = trace.read_qn_rows()
        self.assertEqual(root, 220)
        self.assertEqual(len(original), 221)
        self.assertEqual(trace.json_hash(target), trace.QN_TARGET_SHA256)
        original_bytes = trace.canonical(original)
        del original
        gc.collect()
        rows, endpoints, total, depth = trace.merge_actual_rows()
        self.assertEqual(trace.canonical(rows[:221]), original_bytes)
        self.assertEqual(len(rows), 223)
        self.assertEqual(total, 81331)
        self.assertEqual(depth, 84)
        self.assertEqual(endpoints, {12: 12, 14: 13, 40: 221, 122: 222, "QN001": 220})
        self.assertEqual(trace.json_hash(rows), "0124d3c7f0e178abec2d8084e3aea3424befecef7c964b9e96f5d887729ecf18")
        self.assertEqual(len(trace.canonical(rows)), 3214692)

    def test_changed_archive_pin_and_missing_archive_fail_closed(self):
        pin = dict(trace.QN_ARCHIVE)
        pin["sha256"] = "0"*64
        with patch.object(trace, "QN_ARCHIVE", pin):
            with self.assertRaises(ValueError):
                trace.read_qn_rows()
        with patch.object(trace, "QN_ARCHIVE", None):
            with self.assertRaises(ValueError):
                trace.read_qn_rows()

    def test_actual_small_beta_encoded_product_traces_including_empty_prefix(self):
        choices = [(a, b) for a, b in product((-1, 0, 1), repeat=2) if (a, b) != (0, 0)]
        tested = 0
        for length in range(3):
            for values in product(choices, repeat=length):
                factors = [signed_pair(a, i+1)+signed_pair(b, i+2) for i, (a, b) in enumerate(values)]
                accumulators = [(1, 0, 0, 0)]
                for i, B in enumerate(factors):
                    a, b = represented(accumulators[-1])
                    c, d = represented(B)
                    C = signed_pair(a*c+2*b*d, i+3)+signed_pair(a*d+b*c, i+4)
                    self.assertEqual(balances(accumulators[-1], B, C), (True, True))
                    self.assertTrue(nonzero(C))
                    accumulators.append(C)
                factor_streams, accumulator_streams = streams(factors), streams(accumulators)
                self.assertTrue(quad_at(accumulator_streams, 0, (1, 0, 0, 0)))
                for i, B in enumerate(factors):
                    self.assertTrue(quad_at(factor_streams, i, B))
                    self.assertTrue(quad_at(accumulator_streams, i, accumulators[i]))
                    self.assertTrue(quad_at(accumulator_streams, i+1, accumulators[i+1]))
                    self.assertTrue(nonzero(B))
                self.assertTrue(quad_at(accumulator_streams, length, accumulators[-1]))
                self.assertTrue(nonzero(accumulators[-1]))
                tested += 1
        self.assertEqual(tested, 73)

    def test_missing_initial_unit_factor_condition_or_either_balance_has_counterexample(self):
        zero, one, radical = (0, 0, 0, 0), (1, 0, 0, 0), (0, 0, 1, 0)
        self.assertEqual(balances(zero, one, zero), (True, True))  # Missing start.
        self.assertEqual(balances(one, zero, zero), (True, True))  # Zero factor.
        self.assertEqual(balances(radical, one, zero), (True, False))  # Missing radical balance.
        self.assertEqual(balances(one, one, zero), (False, True))  # Missing real balance.
        self.assertFalse(nonzero((5, 5, 7, 7)))  # Nonzero components are not enough.

    def test_beta_uniqueness_requires_bounded_residue_and_final_index(self):
        code, scale = pack_beta([1, 0])
        self.assertTrue(beta_at(code, scale, 0, 1))
        self.assertTrue(beta_at(code, scale, 1, 0))
        self.assertFalse(beta_at(code, scale, 1, 1))
        modulus = 1+scale
        self.assertEqual(code % modulus, (1+modulus) % modulus)
        self.assertFalse(beta_at(code, scale, 0, 1+modulus))

    def test_small_source_pins_exclude_giant_v28_archive(self):
        pins = trace.quadratic_product_trace_source_pins()
        self.assertIn(trace.QN_ARCHIVE["path"], pins)
        self.assertNotIn(str(trace.V28_ARTIFACT.relative_to(trace.ROOT)), pins)
        self.assertTrue(all(row["bytes"] < 16*1024**2 for row in pins.values()))


@pytest.fixture(scope="module")
def certificate():
    return trace.prove_quadratic_product_trace()


def _curried(bundle, node):
    from peano_lab.kernel.formulas import Imp
    result = node.target
    for dependency in reversed(node.dependencies):
        result = Imp(bundle.nodes[dependency].target, result)
    return result


def test_native_exact_224_node_canonical_bundle_and_one_induction(certificate):
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import encode_proof, encode_proof_bundle, check_encoded_proof_bundle
    limits = BinaryDAGLimits()
    assert certificate.target == certificate.receipt.target == trace.frozen_quadratic_product_trace_target()
    assert certificate.target_ast_sha256 == trace.TARGET_SHA256
    assert len(certificate.bundle.nodes) == certificate.receipt.node_count == 224
    assert certificate.bundle.root == 223
    assert certificate.bundle.nodes[223].dependencies == (12, 13, 221, 222, 220)
    assert certificate.receipt.total_body_nodes <= limits.max_total_body_nodes == 200000
    assert certificate.max_proof_depth <= limits.max_depth == 256
    assert len(certificate.payload.encode()) <= limits.max_payload_bytes == 8*1024**2
    assert certificate.payload.endswith("\n")
    assert encode_proof_bundle(certificate.bundle, certificate.target, limits=limits.bundle_limits()) == certificate.payload
    assert check_encoded_proof_bundle(certificate.payload, limits=limits.bundle_limits()).target == certificate.target
    root = encode_proof(certificate.bundle.nodes[223].body)
    pending, induction = [root], 0
    while pending:
        node = pending.pop()
        induction += node[0] == "ind"
        assert node[0] != "dne"
        pending.extend(node[i] for i in trace._PROOF_CHILDREN[node[0]])
    assert induction == 1
    provenance = certificate.provenance
    assert provenance["original_HA_checked"] and provenance["canonical_bytes_replayed"]
    assert provenance["actual_ancestor_nodes"] == 223
    assert provenance["actual_ancestor_body_nodes"] == 81331
    assert provenance["conditional_on_actual_trace"] and provenance["actual_beta_transitions"]
    assert not provenance["trace_existence_proved"] and not provenance["real_interpretation"]
    assert provenance["IR_parents_closed"] == provenance["library_admissions"] == 0


def test_native_complete_qn_and_beta_bodies_preserved():
    from peano_lab.library.proof_bundle import encode_formula, encode_proof
    # Read the large historical archive before retaining a decoded proof.
    # Keep exact row bytes, not a second expanded object graph or a receipt.
    rows, endpoints, _, _ = trace.merge_actual_rows()
    expected = tuple(trace.canonical(row) for row in rows)
    del rows
    gc.collect()
    certificate = trace.prove_quadratic_product_trace()
    for index, raw in enumerate(expected):
        node = certificate.bundle.nodes[index]
        actual = [node.fuel, encode_formula(node.target), list(node.dependencies), encode_proof(node.body)]
        assert trace.canonical(actual) == raw
    assert endpoints["QN001"] == 220
    assert trace.json_hash(encode_formula(certificate.bundle.nodes[220].target)) == trace.QN_TARGET_SHA256


def test_native_original_HA_rejects_each_missing_public_premise(certificate):
    from dataclasses import replace
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall, Imp
    from peano_lab.kernel.checker import check
    binders, opened, conclusion = strip_target(certificate.target)
    assert binders == 21 and len(opened) == 4
    root = certificate.bundle.nodes[223]
    for omitted in range(3):
        changed = conclusion
        for i in reversed(range(4)):
            if i != omitted:
                changed = Imp(opened[i], changed)
        for _ in range(21):
            changed = Forall(changed)
        assert changed != certificate.target
        assert not check((), root.body, _curried(certificate.bundle, replace(root, target=changed)))


def test_native_original_HA_rejects_wrong_terminal_and_componentwise_claim(certificate):
    from dataclasses import replace
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.checker import check
    root = certificate.bundle.nodes[223]
    for wrong in (
        trace.NAMED_SOURCE.replace(",L,rp,rn,sp,sn) ->", ",S L,rp,rn,sp,sn) ->"),
        trace.NAMED_SOURCE.replace("~(rp=rn /\\ sp=sn)", "~(rp=0 /\\ sp=0)"),
    ):
        changed = parse_named(wrong, registry=trace.definition_registry())
        assert changed != certificate.target
        assert not check((), root.body, _curried(certificate.bundle, replace(root, target=changed)))


def test_native_original_HA_rejects_missing_qn_dependency_and_forged_parent(certificate):
    from dataclasses import replace
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    bundle, root = certificate.bundle, certificate.bundle.nodes[223]
    changed = replace(root, dependencies=root.dependencies[:-1])
    assert not check((), root.body, _curried(bundle, changed))
    assert not check((), EqRefl(Zero()), _curried(bundle, root))
    # Early original-HA rejection demonstrates that no trusted status record
    # can rescue a forged ancestor body, without rechecking a large suffix.
    forged = replace(bundle.nodes[0], body=EqRefl(Zero()))
    with pytest.raises(ProofBundleError, match="kernel rejected"):
        check_proof_bundle(replace(bundle, nodes=(forged,)+bundle.nodes[1:]), certificate.target,
                           limits=BinaryDAGLimits().bundle_limits())


if __name__ == "__main__":
    unittest.main()
