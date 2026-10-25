"""Data-only codec tests: a guard forbids every actual kernel judgment."""
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
SOURCE = APP / "native-v7"
if not SOURCE.is_dir():
    SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py"
sys.path[:0] = [str(APP), str(SOURCE)]
from peano_lab.kernel import formulas as f, proofs as p, terms as t
with patch("peano_lab.kernel.checker.check", side_effect=AssertionError("Codec must not check proofs")):
    import certificate_codec as codec


def raw(document):
    return json.dumps(document, separators=(",", ":")).encode()


class PureCertificateCodecTests(unittest.TestCase):
    def setUp(self):
        for name in ("check", "check_classical"):
            guard = patch("peano_lab.kernel.checker." + name,
                          side_effect=AssertionError("Pure codec tests cannot check proofs"))
            guard.start(); self.addCleanup(guard.stop)
        self.zero = t.Zero()
        self.formula = f.Eq(self.zero, self.zero)
        self.proof = p.EqRefl(self.zero)

    def document(self):
        return json.loads(codec.encode_certificate(self.formula, self.proof))

    def test_preserves_shared_proof_and_annotation_identity(self):
        variable = t.Var(0)
        equation = f.Eq(variable, variable)
        leaf = p.EqRefl(variable)
        formula = f.Forall(f.And(equation, equation))
        proof = p.ForallIntro(p.AndIntro(leaf, leaf))
        encoded = codec.encode_certificate(formula, proof)
        decoded = codec.decode_certificate(encoded, expected_sha256=hashlib.sha256(encoded).hexdigest())
        self.assertIs(decoded.certificate.body.left, decoded.certificate.body.right)
        self.assertIs(decoded.formula.body.left, decoded.formula.body.right)
        self.assertIs(decoded.formula.body.left.left, decoded.certificate.body.left.t)
        self.assertEqual(decoded.metrics["proof_cost"]["distinct_objects"], 3)
        self.assertEqual(decoded.metrics["proof_cost"]["structural_occurrences"], 4)
        self.assertFalse(decoded.metrics["kernel_check_performed"])
        self.assertIn(codec.formula_identity(formula), decoded.formula_identities)

    def test_every_native_proof_constructor_is_inert_and_roundtrips(self):
        v, q, h = t.Var(0), f.Eq(t.Var(0), t.Var(0)), p.Hyp(0)
        examples = [h, p.ImpIntro(h), p.ImpElim(h, h), p.Cut(q, q, h, h),
            p.AndIntro(h, h), p.AndElimL(h), p.AndElimR(h), p.OrIntroL(h), p.OrIntroR(h),
            p.OrElim(h, h, h), p.BotElim(h), p.ForallIntro(h), p.ForallElim(h, v),
            p.ExistsIntro(v, h), p.ExistsElim(h, h), p.EqRefl(v), p.EqSym(h),
            p.EqTrans(h, h), p.CongS(h), p.CongAdd(h, h), p.CongMul(h, h),
            p.EqSubst(q, h, h), p.DNE(q), p.Axiom("PA1"), p.Ind(q, h, h)]
        for proof in examples:
            with self.subTest(constructor=type(proof).__name__):
                decoded = codec.decode_certificate(codec.encode_certificate(f.Forall(q), proof))
                self.assertIs(type(decoded.certificate), type(proof))
                self.assertEqual(decoded.certificate, proof)
        # Many examples are deliberately invalid proofs of the envelope formula.
        # The codec must not silently turn data decoding into proof validation.

    def test_term_and_formula_constructors_and_distinct_sharing(self):
        term = t.Mul(t.Add(t.Var(0), t.Succ(t.Zero())), t.Var(0))
        equation = f.Eq(term, term)
        formulas = [equation, f.Bot(), f.Imp(equation, f.Bot()),
                    f.And(equation, equation), f.Or(equation, equation),
                    f.Forall(equation), f.Exists(equation)]
        for formula in formulas:
            self.assertEqual(codec.decode_certificate(codec.encode_certificate(formula, self.proof)).formula, formula)
        shared = f.Eq(self.zero, self.zero)
        unshared = f.Eq(t.Zero(), t.Zero())
        self.assertEqual(codec.formula_identity(shared), codec.formula_identity(unshared))
        self.assertNotEqual(codec.formula_identity(shared), codec.formula_identity(f.Eq(t.Succ(t.Zero()), t.Zero())))

    def test_rejects_unknown_classes_partial_proofs_and_misplaced_fields(self):
        class ForeignProof(p.Proof):
            pass
        from peano_lab.engine.state import Hole
        for proof in (ForeignProof(), Hole(0), p.EqRefl(f.Bot()), p.Hyp(True),
                      p.Axiom("PA7"), p.Hyp(-1), p.Hyp(50_001)):
            with self.subTest(proof=type(proof).__name__):
                with self.assertRaises(codec.CodecError):
                    codec.encode_certificate(self.formula, proof)
        missing = object.__new__(p.EqRefl)
        with self.assertRaises(codec.CodecError):
            codec.encode_certificate(self.formula, missing)

    def test_rejects_cycles_in_actual_objects(self):
        cyclic = p.EqSym(self.proof)
        object.__setattr__(cyclic, "proof", cyclic)
        with self.assertRaisesRegex(codec.CodecError, "Cyclic"):
            codec.encode_certificate(self.formula, cyclic)
        cyclic_term = t.Succ(self.zero)
        object.__setattr__(cyclic_term, "term", cyclic_term)
        with self.assertRaises(codec.CodecError):
            codec.formula_identity(f.Eq(cyclic_term, self.zero))

    def test_rejects_forward_self_negative_boolean_and_wrong_category_refs(self):
        for value in (-1, True, 999, 2):
            document = self.document()
            proof_index = document["roots"]["certificate"]
            document["nodes"][proof_index]["fields"]["t"] = value
            with self.subTest(value=value), self.assertRaises(codec.CodecError):
                codec.decode_certificate(raw(document))
        document = self.document()
        document["nodes"][document["roots"]["certificate"]]["fields"]["t"] = document["roots"]["formula"]
        with self.assertRaises(codec.CodecError):
            codec.decode_certificate(raw(document))

    def test_rejects_unknown_extra_missing_and_unreachable_nodes(self):
        mutations = [lambda d: d.update(script="refl"),
                     lambda d: d["nodes"][0].update(module="os"),
                     lambda d: d["nodes"][0].update(tag="__import__"),
                     lambda d: d["nodes"][0]["fields"].update(payload="print(1)"),
                     lambda d: d["nodes"].append({"tag": "Zero", "fields": {}}),
                     lambda d: d["roots"].update(proof=0),
                     lambda d: d.update(version=True)]
        for mutate in mutations:
            document = self.document(); mutate(document)
            with self.assertRaises(codec.CodecError):
                codec.decode_certificate(raw(document))
        document = self.document()
        del document["nodes"][document["roots"]["certificate"]]["fields"]["t"]
        with self.assertRaises(codec.CodecError):
            codec.decode_certificate(raw(document))

    def test_rejects_duplicate_keys_non_integer_numbers_and_invalid_utf8(self):
        for value in (b'{"schema":1,"schema":2}', b'{"value":NaN}', b'{"value":1.0}',
                      b'{"value":123456789}', b'\xff', b'[[[[', b''):
            with self.subTest(raw=value), self.assertRaises(codec.CodecError):
                codec.decode_certificate(value)

    def test_authenticates_actual_bytes_and_caps_payload_size(self):
        encoded = codec.encode_certificate(self.formula, self.proof)
        with self.assertRaisesRegex(codec.CodecError, "hash mismatch"):
            codec.decode_certificate(encoded, expected_sha256="0" * 64)
        with self.assertRaises(codec.CodecError):
            codec.decode_certificate(encoded, expected_sha256=True)
        with self.assertRaises(codec.CodecError):
            codec.decode_certificate(encoded, limits=codec.CodecLimits(max_bytes=100))
        with self.assertRaises(codec.CodecError):
            codec.encode_certificate(self.formula, self.proof, limits=codec.CodecLimits(max_bytes=100))

    def test_shared_graph_cannot_hide_exponential_proof_occurrences(self):
        proof = self.proof
        for _ in range(15):
            proof = p.AndIntro(proof, proof)
        # Only sixteen proof objects, but 65,535 expanded proof occurrences.
        with self.assertRaisesRegex(codec.CodecError, "Proof structure rejected"):
            codec.encode_certificate(self.formula, proof)

    def test_separate_graph_payload_and_proof_depth_object_limits(self):
        proof = p.EqSym(p.EqSym(self.proof))
        for limits in (codec.CodecLimits(max_proof_objects=2), codec.CodecLimits(max_proof_depth=2),
                       codec.CodecLimits(max_graph_depth=2), codec.CodecLimits(max_graph_objects=2),
                       codec.CodecLimits(max_graph_occurrences=4)):
            with self.subTest(limits=limits), self.assertRaises(codec.CodecError):
                codec.encode_certificate(self.formula, proof, limits=limits)
        with self.assertRaises(codec.CodecError):
            codec.CodecLimits(max_proof_objects=10_001)
        with self.assertRaises(codec.CodecError):
            codec.CodecLimits(max_proof_depth=True)

    def test_cancellation_and_immutable_result(self):
        for operation in (lambda: codec.encode_certificate(self.formula, self.proof, should_stop=lambda: True),
                          lambda: codec.decode_certificate(b'{}', should_stop=lambda: True),
                          lambda: codec.formula_identity(self.formula, should_stop=lambda: True)):
            with self.assertRaisesRegex(codec.CodecError, "cancelled"):
                operation()
        decoded = codec.decode_certificate(codec.encode_certificate(self.formula, self.proof))
        with self.assertRaises(FrozenInstanceError):
            decoded.formula = f.Bot()


if __name__ == "__main__":
    unittest.main()
