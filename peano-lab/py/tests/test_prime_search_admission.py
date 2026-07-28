"""Independent admission audit for constructive primality and prime search."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib

import driver

from peano_lab.engine.state import proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, parse_formula_with_names
from peano_lab.kernel.proofs import Axiom, Cut, DNE, EqRefl, Hyp, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.theorems import _specs_by_name, get, replay


EXPECTED = {
    "eq_decidable": {
        "dependencies": (),
        "statement": "c13a817645afe596d7f55f88eb9400073ae742c17213dfbf907f4c497aa1aca1",
        "script": (27, "5761f0f66c4e76177a693206a607c6f72022bb30edd68b32a1e9f9c36596616a"),
        "certificate": ((48, 20), 0, "d89ef3447e28a28ab792d7fa21faea761036166dcb1ca11b60321e1edde00df3"),
    },
    "multiple_decidable_nonzero": {
        "dependencies": (
            "eq_decidable",
            "division_remainder_exists",
            "multiple_has_zero_remainder",
            "division_remainder_unique",
        ),
        "statement": "08cd13450e5d21cb8318d95c115340c0ad6bfe7b90d4bba6ef8905d3d90c4684",
        "script": (40, "f7b7e4b023eb3834b4e92469ffddf1fe33902ad53c23f2de2d039adb31f7a529"),
        "certificate": ((1_242, 61), 32, "e472d09fa3657d1d6bd8e2976a074c32a9957cd876a8864a9e6a74dbb76793cf"),
    },
    "multiple_decidable": {
        "dependencies": (
            "mul_zero_left",
            "eq_decidable",
            "multiple_decidable_nonzero",
        ),
        "statement": "4908912a030aa9c2d38c5b250e5ec24574df08b3f129bd2d2360dbd315345fa7",
        "script": (29, "0639fe97ea2541b752a5d4a57aeed5a6e46b83966a909d884f3bd2e87286d68f"),
        "certificate": ((1_352, 64), 35, "27aa9616c05f0c33fb1fc32b6eb12769a4a3b02fc6e0fa504c99364b7d727513"),
    },
    "factor_property_succ": {
        "dependencies": ("le_eq_or_lt", "le_of_succ_le_succ"),
        "statement": "2156cefbc7f853dd128083b2ae4388e87432fc24cc43386b689f38b5c6261ab4",
        "script": (27, "cccf111f3fe2079e7829a29635541569c153f893fd207a6751b8a2c879fb47ca"),
        "certificate": ((150, 20), 5, "0d6bbb6b64800fb92e960101070f82d89f533ece9862ccc8bc6003b4efa666a9"),
    },
    "factor_search_up_to": {
        "dependencies": (
            "mul_zero_left",
            "succ_ne_zero",
            "le_zero",
            "le_refl",
            "le_succ",
            "mul_left_cancel_nonzero",
            "eq_decidable",
            "multiple_decidable_nonzero",
            "factor_property_succ",
        ),
        "statement": "256db49f74c5eeed8ff97f44d35f26d3e4dc74fb2fadfd502a66f0a343981706",
        "script": (101, "ae4b4020410e6127052ec6c8879829c003e19856c220ba8bbedb560966ba74bd"),
        "certificate": ((1_925, 69), 56, "b678af35c4dbb9a63bcbdbf03ddca2f03714b1b37f1d0de364c7025c98b232f1"),
    },
    "prime_or_composite": {
        "dependencies": ("divisor_le_nonzero", "factor_search_up_to"),
        "statement": "321b86c4b31d69e89d4be9b7bb89e9cfab9abb236aa6139b4ca90ed836cf72c9",
        "script": (38, "7eb204f046bfd08d9fed8f7227e6121b65ef899c234d111478dde5b6b9d0547b"),
        "certificate": ((2_038, 71), 59, "4f3834b266fc7ff365a0464d94b2fadcff92e87bea40e99d703517f25ecb4111"),
    },
    "prime_nonzero": {
        "dependencies": ("mul_zero_left", "succ_ne_zero"),
        "statement": "f74d3a446b0634b8019db1906e37846c34e3d71f60d5261139ed9ed69b465ed7",
        "script": (20, "b1a5be33a610c956d6f57f344fb2e23454e2ffda085fc702e193f61a144f5d1a"),
        "certificate": ((49, 11), 2, "28430940e08dfab2565eae42005fa5f7e1b95a3cbf5c389ecbcf09c3d4246a05"),
    },
    "prime_decidable": {
        "dependencies": ("eq_decidable", "prime_or_composite", "prime_nonzero"),
        "statement": "c29ffffd1aa72d334c0c66dd17ad201519fd9cb8e7bf920ab7a4f56605f370da",
        "script": (47, "5f2d66c668714fe8992dbd80ea7c0ed6ea04e474ac896fe5ae69fc4dfd482596"),
        "certificate": ((2_194, 73), 64, "80a5f7837c8ead5260cb192a038b0773d02a46335b670416d8624dad88c53074"),
    },
    "factor_nonzero_left": {
        "dependencies": ("mul_zero_left",),
        "statement": "733059a7f0a7b0efc0a06d04eefd2cf3e9cad880ef29754fcd2d6dfacf76cf28",
        "script": (11, "2b5cdb6580ac24b6cf406d4f43fed4006fed91acc7623f4951e51fd2ceae9afd"),
        "certificate": ((37, 12), 1, "623e666aaba60f46434bf5df0ec25bb00f53a075f872297f8f49636eba104912"),
    },
    "proper_factor_lt": {
        "dependencies": (
            "divisor_le_nonzero",
            "le_eq_or_lt",
            "mul_left_cancel_nonzero",
            "mul_one",
        ),
        "statement": "abc3d35ebe727ae0827f34d66cf9b6943d0dfddf02830e422c78417342ced085",
        "script": (43, "fdb0e91f9f6a0836fd78ebad38954072fff8af280f9c8dd0a60a6ed516204e00"),
        "certificate": ((468, 26), 16, "22b2140fa2bd79acd5378a7ce775317150348f9d9c6de5372d3a9d5d63643f2b"),
    },
    "prime_divisor_exists_up_to": {
        "dependencies": (
            "mul_zero_left",
            "le_zero",
            "lt_of_lt_of_le",
            "le_of_succ_le_succ",
            "multiple_refl",
            "multiple_trans",
            "prime_or_composite",
            "proper_factor_lt",
        ),
        "statement": "c695e9b0c2e8b21c98c58d24c8d34a9446679fc2f7ec0c03a3c3fb1f9ba9c3d9",
        "script": (71, "5190c0b1a75b41a4eac9878471df9171694204f76f0eb65e902d9e21336c56b4"),
        "certificate": ((2_931, 78), 91, "1258bfd21a67c530ec72c8e8d546eb8fbbdae2a09f563712794671cb02684add"),
    },
    "prime_divisor_exists": {
        "dependencies": ("le_refl", "prime_divisor_exists_up_to"),
        "statement": "937e67f7de2efd5bec917e9d60536b0e155b0d27025d4f2a14985c147fbea4d2",
        "script": (9, "c9e06b7c61598190b6ed4fb98e4c34f18bab7a71693eb0c9a9a50015f37e7881"),
        "certificate": ((2_977, 80), 94, "fab66d90500951594d41609b1994e723ac5fb049a3041c6618b3799b68d36d4b"),
    },
}

ZERO = Zero()
TRUE = Eq(ZERO, ZERO)


def _digest(value: object) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _cut_spine(proof: Proof) -> tuple[Cut, ...]:
    result: list[Cut] = []
    while type(proof) is Cut:
        result.append(proof)
        proof = proof.body
    return tuple(result)


def _replace_dependency_by_true(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        return replace(proof, proposition=TRUE, lemma=EqRefl(ZERO))
    return replace(
        proof,
        body=_replace_dependency_by_true(proof.body, index - 1),
    )


def _mutate_first(proof: Proof, node_type: type[Proof], replacement):
    if type(proof) is node_type:
        return replacement(proof), True
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            changed_child, changed = _mutate_first(child, node_type, replacement)
            if changed:
                return replace(proof, **{item.name: changed_child}), True
    return proof, False


def _mutate_authored_body(proof: Proof, node_type: type[Proof], replacement):
    if type(proof) is Cut:
        body, changed = _mutate_authored_body(proof.body, node_type, replacement)
        return replace(proof, body=body), changed
    return _mutate_first(proof, node_type, replacement)


def _cold_rows():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    rows = []
    for name in EXPECTED:
        theorem = replay(name)
        assert check((), theorem.certificate, theorem.formula)
        rows.append((name, theorem.certificate, _digest(theorem.certificate)))
    return tuple(rows)


def test_exact_contracts_and_deterministic_constructive_replay() -> None:
    first = _cold_rows()
    second = _cold_rows()
    assert second == first

    for name, certificate, certificate_digest in first:
        expected = EXPECTED[name]
        spec = get(name)
        assert spec is not None
        formula, free_names = parse_formula_with_names(spec.statement)
        script_length, script_digest = expected["script"]
        metrics, cut_count, expected_certificate_digest = expected["certificate"]

        assert free_names == ()
        assert hashlib.sha256(spec.statement.encode()).hexdigest() == expected["statement"]
        assert spec.dependencies == expected["dependencies"]
        assert len(spec.script) == script_length
        assert _digest(spec.script) == script_digest
        assert replay(name).formula == formula
        assert certificate_digest == expected_certificate_digest
        assert proof_metrics(certificate) == metrics
        assert sum(type(node) is Cut for node in _walk(certificate)) == cut_count
        assert not any(type(node) is DNE for node in _walk(certificate))
        assert check((), certificate, formula)


def test_every_declared_dependency_slot_is_semantically_necessary() -> None:
    for name, expected in EXPECTED.items():
        theorem = replay(name)
        dependencies = expected["dependencies"]
        spine = _cut_spine(theorem.certificate)
        assert len(spine) == len(dependencies)

        for index, (cut, dependency_name) in enumerate(
            zip(spine, dependencies, strict=True)
        ):
            dependency = replay(dependency_name)
            assert cut.proposition == dependency.formula
            assert cut.lemma == dependency.certificate
            assert cut.conclusion == theorem.formula
            assert not check(
                (),
                _replace_dependency_by_true(theorem.certificate, index),
                theorem.formula,
            )


def test_every_certificate_rejects_pa_and_authored_hypothesis_mutations() -> None:
    for name in EXPECTED:
        theorem = replay(name)
        bad_axiom, changed = _mutate_first(
            theorem.certificate,
            Axiom,
            lambda node: Axiom("PA6" if node.name != "PA6" else "PA5"),
        )
        assert changed and not check((), bad_axiom, theorem.formula)

        bad_hypothesis, changed = _mutate_authored_body(
            theorem.certificate,
            Hyp,
            lambda node: Hyp(node.index + 1),
        )
        assert changed and not check((), bad_hypothesis, theorem.formula)


def test_public_live_use_closes_decisions_and_prime_divisor_existence() -> None:
    for name in ("multiple_decidable", "prime_decidable", "prime_divisor_exists"):
        theorem = get(name)
        assert theorem is not None
        session = driver.LabSession()
        commands = (
            f"pa prove {theorem.statement}",
            f"use {name}",
            f"exact {name}",
            "qed",
        )
        results = tuple(session.run_result(command) for command in commands)

        assert all(result["failed"] is False for result in results)
        assert "QED." in results[-1]["out"]
