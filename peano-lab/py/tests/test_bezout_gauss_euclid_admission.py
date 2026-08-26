"""Independent admission audit for the native Bezout-to-Euclid chain."""

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


# Statement and script hashes pin the exact human-authored contracts while
# keeping this already-large audit readable. Certificate hashes independently
# pin the deterministic proof objects produced from those contracts.
EXPECTED = {
    "add_permute_outer": {
        "dependencies": ("add_assoc", "add_comm"),
        "statement": "259774621ec64b47db54d52c4504abf8c9ecb2a423c0e0b08965f5a44f55ea5a",
        "script": (25, "f34f3ff889c16fcbb18066eb4915d3586e379f9ed03ca5b7abad8f655dee3929"),
        "certificate": ((149, 15), 4, "897b1a1c5b727b8ea340d39bcfcc9ebad1df3132cf15cb2e95a286c2b784671c"),
    },
    "balanced_bezout_euclid_step": {
        "dependencies": (
            "add_assoc",
            "add_comm",
            "mul_add",
            "mul_assoc",
            "add_mul",
            "add_permute_outer",
        ),
        "statement": "3b6f2fba9093863f374428df77f28fc81b787a2103e0fbfbfe9a8f19db83f98a",
        "script": (67, "839fbd61aa5883f2ee6fca8bee983e6ce535eab4ec999301a6a625251d0ba78f"),
        "certificate": ((880, 35), 24, "feae8ba0dfcb242f2442b7201e5d45c248b898844374ca77b38a15b05cd0026a"),
    },
    "gcd_balanced_bezout_exists_up_to": {
        "dependencies": (
            "zero_add",
            "le_zero",
            "le_eq_or_lt",
            "le_of_succ_le_succ",
            "division_remainder_exists",
            "is_gcd_zero_right",
            "is_gcd_euclid_forward",
            "balanced_bezout_euclid_step",
        ),
        "statement": "ee6ecd53ab81a278d0802f9d2297db20d14c702a45703340efe11f888f1eece7",
        "script": (80, "1bf3f99cc7707fe03f89506b377dd9bdf87e6972932dc5f39ffe18c0dfdf9738"),
        "certificate": ((2_233, 45), 63, "2e611f8aee45ae3a9d970163212fecf60aa3f5ea6c2e2cc4f9de81bc661703f5"),
    },
    "gcd_balanced_bezout_exists": {
        "dependencies": ("le_refl", "gcd_balanced_bezout_exists_up_to"),
        "statement": "a04ae60ae70da68a964c4440c8f521856fdfdcea733d6251294357eaaeab6af8",
        "script": (11, "41ecb09f72e3c75f0050925d4489341e9d8f8a956dd6a79fd9883b4d1c26fb9b"),
        "certificate": ((2_269, 47), 66, "0c34da8ea071e4db38ddf96626687c588d09b1a3639878f914c0d2c71f321e6c"),
    },
    "balanced_combination_scale_right": {
        "dependencies": ("mul_assoc", "mul_comm", "add_mul"),
        "statement": "59e7bcfea451e25ca739bc2bdbee87e497f83db25712dc3743e1fa10c36e075e",
        "script": (56, "fddfc4db29e5c4a4f34d100a419e15c77c7033ad3ac4f8a6e177ce036874093c"),
        "certificate": ((754, 28), 20, "dfb696fa22b514d253db7605418c48cdf678147d99df1a41a746298797f4ff89"),
    },
    "common_divisor_divides_balanced_result": {
        "dependencies": ("mul_assoc", "mul_add", "add_comm", "factor_difference"),
        "statement": "a1c724b5b09f2645426190ed9da60a61d5fcdd1f1c7f963e768a890d4df4a8de",
        "script": (48, "0268cb4d8b13b7a2439e6e013fd619105c70014211f38baad6297ab033314348"),
        "certificate": ((626, 39), 16, "b8a6860c94698f1c9f4f6156f304c3b28ea52a79afc77b2691026da2ad368d0b"),
    },
    "coprime_balanced_bezout": {
        "dependencies": ("gcd_balanced_bezout_exists",),
        "statement": "5a0429f7b8a6b245056b0fe0e9a1651c4eb4818dce780e85f75082d2c19e5cb8",
        "script": (24, "a46eee501b64113621714703f3c25a5740499006c2adedf78847bbf16df54d37"),
        "certificate": ((2_304, 48), 67, "342339e0e63d551124a62c6bbacd70559da6eff0492af8f6405a6c77a5fbcc27"),
    },
    "gauss_coprime_cancel": {
        "dependencies": (
            "multiple_refl",
            "one_mul",
            "coprime_balanced_bezout",
            "balanced_combination_scale_right",
            "common_divisor_divides_balanced_result",
        ),
        "statement": "1c3666be9deded79202818d9d6228aa230fefc0d123b60b73614b8a34483ff9c",
        "script": (30, "87abfe689bbac5c0982d653add4dab3d762255bd7b64bc320281872af9e2274f"),
        "certificate": ((3_800, 51), 110, "763e42141ac25ecef8fe28a3284c93af105ef2015bbfaa2067d90aeac22335db"),
    },
    "prime_divisor_eq_one_or_self": {
        "dependencies": ("mul_one",),
        "statement": "ebafa11a2163b9a35d431eea316b19c434ff1f6fd8d702b76530f1b8c1292bfb",
        "script": (19, "6ac1d216cd2fc0c20a8e0217a49ff8d003cb4042cd561e2f54c2a6cdefd275b8"),
        "certificate": ((57, 12), 2, "e7e3017fe0ec916869c91a094be8a21f81ddc39ca6cc73d6f163a71ccea57fd5"),
    },
    "euclid_prime_dvd_product": {
        "dependencies": (
            "prime_divisor_eq_one_or_self",
            "gcd_exists_relational",
            "is_gcd_one_to_coprime",
            "gauss_coprime_cancel",
        ),
        "statement": "8196d1e0311866b07fec69c0852169e95b52694b74d265845fa6c7a110cc71e0",
        "script": (36, "c0be5fbb2d11904318449e828477479083d2adfce86a1674af01ed6f5578d5b4"),
        "certificate": ((5_382, 55), 159, "8db2385c53a7f73f65e812822abeb564a8dff57bf9bcd1b65c9d707b0f7897b7"),
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
            changed_child, changed = _mutate_first(
                child, node_type, replacement
            )
            if changed:
                return replace(proof, **{item.name: changed_child}), True
    return proof, False


def _mutate_authored_body(proof: Proof, node_type: type[Proof], replacement):
    if type(proof) is Cut:
        body, changed = _mutate_authored_body(
            proof.body, node_type, replacement
        )
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


def test_public_live_use_closes_euclids_lemma() -> None:
    theorem = get("euclid_prime_dvd_product")
    assert theorem is not None
    session = driver.LabSession()
    commands = (
        f"pa prove {theorem.statement}",
        "use euclid_prime_dvd_product",
        "exact euclid_prime_dvd_product",
        "qed",
    )
    results = tuple(session.run_result(command) for command in commands)

    assert all(result["failed"] is False for result in results)
    assert "QED." in results[-1]["out"]
