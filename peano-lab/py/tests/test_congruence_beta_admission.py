"""Independent admission audit for congruence and Gödel-beta values."""

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
    "mod_eq_trans": {
        "dependencies": ("add_assoc", "add_comm", "mul_add"),
        "statement": "07009140b6d6d7f4e1e34d6c33bf1b007ea29c26a14eeafa9b2fa3d377abe7a9",
        "script": (42, "5c6a6bf4b3f23de8a7e5eb7bf40cd16d426d00c345fb5e9f834ecba808da2e9f"),
        "certificate": ((252, 29), 6, "052be6f7213b8697002669ec4b938db550329a8573d520d03cb51af28630bd61"),
    },
    "mod_eq_add": {
        "dependencies": ("mul_add", "add_comm", "add_permute_outer"),
        "statement": "6e8c1e97ea5c4221a993e587d4475550418981e5fbef1b4c65e149dee0713ddd",
        "script": (42, "7789df1fd37be5a3be0d6d6cbf4e6c0867bf135e3508ca852e99ec0386c5394f"),
        "certificate": ((370, 30), 10, "49e4d310fb281152161969987650ed529899ec2db8d310000cbe9c0aebb8b986"),
    },
    "beta_modulus_nonzero": {
        "dependencies": ("succ_ne_zero",),
        "statement": "6701007cb46c44334c05d9bd894078b9b002f9624b4057b9203dd83087294526",
        "script": (4, "a257b75ac056a1cb2f3caa2c4e5839e1e6bd054244563bcb6993fcb8f7a4c20b"),
        "certificate": ((9, 6), 1, "e8ce620074f6ed37285a3dc034e72bc8f267c4442673ed7dc77c9db067d2f314"),
    },
    "beta_at_self_of_bound": {
        "dependencies": ("mul_zero_left", "zero_add"),
        "statement": "2d7d05bc900916fb1c5e23a402436d7e460ee6ad7ac1de57ba9cc1db76a9c095",
        "script": (12, "b7d6bf2e801f275c7bd097dc7903391161a1b43d9c78d6aa7ec0cf67ad0955b9"),
        "certificate": ((62, 16), 2, "b563c1208a1c868c1c93ba1f03ddef49f5acdcf564dc44edfd0d3ea4e3f5aef4"),
    },
    "beta_at_exists": {
        "dependencies": (
            "beta_modulus_nonzero",
            "mul_comm",
            "division_remainder_exists",
        ),
        "statement": "acd7a937d6ec7c3c4d6214357bdfcdf3a975ccd71f7e14a540a1690d5e9b1773",
        "script": (24, "26c9e7b0a2a682552cbf79df3d6826b613851a3900507ef7298223cade742bf8"),
        "certificate": ((479, 31), 15, "967de23f5a2e16ad6917ba20073cb2b63a1ab562945069360c57b040c48078d4"),
    },
    "beta_at_unique": {
        "dependencies": ("mul_comm", "division_remainder_unique"),
        "statement": "eac0700b7c24aa059073c61ffdf1541dc02d23400571b003fe964b9df65f5afd",
        "script": (37, "4283a8c482f83a0cbea6bdcb718123ac1f20c922b12ea1862d672ca4752ba4af"),
        "certificate": ((1_121, 59), 30, "891320ec08736c26f18d9ac34c38da3df2b764b63794d0a33c8820ce51caf2ae"),
    },
    "beta_at_exists_unique": {
        "dependencies": ("beta_at_exists", "beta_at_unique"),
        "statement": "e113675254fcdd4275f8c427c704dc1eb9816fb5cc2e251d0995ece07f983228",
        "script": (22, "2bc0efab1270e45491a7d3e22ee0a4002c200f646c78152645b925c48d45fd62"),
        "certificate": ((1_625, 61), 47, "37ae2a410d200b75cd68831454765e500dc8dafcc77b8a51ed60f9a79f971d8c"),
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
        nodes = tuple(_walk(certificate))

        assert free_names == ()
        assert hashlib.sha256(spec.statement.encode()).hexdigest() == expected["statement"]
        assert spec.dependencies == expected["dependencies"]
        assert len(spec.script) == script_length
        assert _digest(spec.script) == script_digest
        assert replay(name).formula == formula
        assert certificate_digest == expected_certificate_digest
        assert proof_metrics(certificate) == metrics
        assert sum(type(node) is Cut for node in nodes) == cut_count
        assert not any(type(node) is DNE for node in nodes)
        assert {
            node.name for node in nodes if type(node) is Axiom
        } <= {"PA1", "PA2", "PA3", "PA4", "PA5", "PA6"}
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


def test_public_live_use_closes_congruence_and_beta_endpoints() -> None:
    for name in ("mod_eq_trans", "mod_eq_add", "beta_at_exists_unique"):
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
