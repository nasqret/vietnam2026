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
    "mod_eq_mul_right": {
        "dependencies": ("add_mul", "mul_assoc"),
        "statement": "8733e14f0e281c8da5e450d12fe21b7d5929d4b5e9953d867333be510677d636",
        "script": (26, "cf7e391dc56ca71ba86f22be7ecc663e8af5872ccb0a7e21f88fb32496540a2e"),
        "certificate": ((484, 26), 13, "4994212781f9a86bb60622ca1fe8ad409d0bb500791af6a24b5a825098729e27"),
    },
    "mod_eq_mul_left": {
        "dependencies": ("mod_eq_mul_right", "mul_comm"),
        "statement": "dbadf46b1b0bf5a186fbdd59491a88885e0649b62e28e8465f6dee8bdb9e21fe",
        "script": (25, "950e4ebdc52eae84f677b237f20983484305d5af68f3da71457c99287a889dcf"),
        "certificate": ((738, 27), 21, "84e29f574f4ebbcb3993c2746183e370648a84346c8cf4e46f50a28581bf9dc6"),
    },
    "mod_eq_mul": {
        "dependencies": ("mod_eq_mul_right", "mod_eq_mul_left", "mod_eq_trans"),
        "statement": "a3983a74ea581e76450a400c1ed5b4e06e6feac6ff9a6ebb90d8f82f3c316d2b",
        "script": (28, "7e6cb0f149bca7982d666e9b5365ca4dda9449c28943be656d98ff4a94fdc87e"),
        "certificate": ((1_505, 32), 43, "660f19930d52443997b878d9fbc824d96e6070e8e7304d08159dcb591af5cc56"),
    },
    "remainder_decomposition_to_mod_eq": {
        "dependencies": ("add_comm", "mul_comm"),
        "statement": "5329024af13cfcbc0e4662ef24110fcbe2ece3d384ffca5c07cf3f6b7a49b55b",
        "script": (16, "2992d90f135d6b779fc3d926e9fce7e53496c3301dedcc2a55b10eef23b55ad2"),
        "certificate": ((323, 26), 10, "acea3f60f7fa7dfcd1745c5cb1dd1d20436c173affa5518ebcb4f981b6893b19"),
    },
    "mod_eq_bounded_unique": {
        "dependencies": ("add_comm", "division_remainder_unique"),
        "statement": "8e73abc172b556b5fb557c527977e6f07c1e366080b207163dd58b7931643c0d",
        "script": (28, "5a41e200eef2c09137f70c22f1e0bfb69ac5559741c198834c63d8495fa2917c"),
        "certificate": ((961, 59), 26, "9bdbf756db7d40a03088e05e9f311290d4ce31c6304913bcc5a3a12d5a0c2f89"),
    },
    "mod_eq_to_remainder_decomposition": {
        "dependencies": (
            "division_remainder_exists",
            "add_comm",
            "mul_comm",
            "mod_eq_trans",
            "mod_eq_bounded_unique",
        ),
        "statement": "03d36e6993b3691311ccb9e9e75006895f186ff659f1042d9b69fe4811db2360",
        "script": (51, "142583f023f91df0300654d0b53de0ff14549d484ad3e927a1e548758ba20862"),
        "certificate": ((1_793, 64), 50, "a92fbaccbecc0472384e7c424f6b72dda864ce0922174b87828afea85ba5320a"),
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
    "beta_at_to_mod_eq": {
        "dependencies": ("remainder_decomposition_to_mod_eq",),
        "statement": "c748a4a17fd48703d134abcd46e96aa5ef082fc1f9aa69ce089d1421446d565d",
        "script": (13, "ab6a199f73fef6b1309d2690f5f9546a534bbc7b37f6e007b271d5fbab2d7b12"),
        "certificate": ((358, 27), 11, "dd174002d4701711239c5958acc580ca4ff11c1788aff4936b9a8d9ad65562e6"),
    },
    "beta_at_of_mod_eq_bound": {
        "dependencies": ("beta_modulus_nonzero", "mod_eq_to_remainder_decomposition"),
        "statement": "9934b7b533260bf9c2c53f4a06d653873048b3ccb1b78fba0bd897fe6a604536",
        "script": (17, "9793a6989e45a6b331c687f4a0f7e057fcc20a966e269f5dc646a9770da8ac14"),
        "certificate": ((1_839, 66), 53, "e4a2ead06ca651304be645d679f5e7e81da4ede0afd9997f2f59864f7b01074f"),
    },
    "bezout_mod_left": {
        "dependencies": ("add_assoc", "add_comm"),
        "statement": "7c933e89b5e783e0fe57654937ee8202b8b0a917184b23463fccbda85de308b0",
        "script": (19, "f3828f2a187f21e71e99b16eac7dd26300a29c468da8cc40071fad3fb12a97dd"),
        "certificate": ((134, 19), 4, "0ba24c738b192b0a35c82006181468cc99f2d1cea106cfdaf43d38e80d5b20e2"),
    },
    "bezout_mod_right": {
        "dependencies": ("add_assoc",),
        "statement": "2b9829ff7d6d6582927a7b85c058b531717e3d91259f9bcc574a76f687eec068",
        "script": (13, "b536b76554c8b03ff31194d28bc162a51636713784307c2d659b3ee5552cb2c0"),
        "certificate": ((50, 16), 1, "2b31fb490cc73a830a30434cc534a5a880ed1d52921a4ec97c3e6cdbd932beb2"),
    },
    "mod_eq_predecessor_cancel": {
        "dependencies": ("add_assoc", "add_comm", "mul_succ_left"),
        "statement": "ff9e6397219fcf402e7a0e46e5d1ce0cee284f43b12ebdd124e21082c0170db4",
        "script": (15, "bb918309a373e8829e44b53205816842834e936c6e644241c3c8f9b4c2339244"),
        "certificate": ((315, 25), 9, "35e5bcc4216481e35319981c1f0536cda87b5ec2a6c2215b49d5b686cea7686f"),
    },
    "binary_crt": {
        "dependencies": (
            "nonzero_is_succ",
            "coprime_balanced_bezout",
            "bezout_mod_left",
            "bezout_mod_right",
            "mod_eq_mul_left",
            "mul_add",
            "mul_one",
            "dvd_to_mod_zero",
            "mul_assoc",
            "mul_comm",
            "mod_eq_add",
            "mod_eq_refl",
            "mod_eq_trans",
            "mod_eq_predecessor_cancel",
            "zero_add",
        ),
        "statement": "25e1f5213a9a5b04f3a20077b936ba8814f6ae8951f4f72e5f5e2135d7c9148f",
        "script": (276, "16a1f89d08a1f88ddffa41e9f5b0c81e2bcf8d8b056cd239ae82d01e80de673e"),
        "certificate": ((5_044, 51), 144, "fd5384ba933f194fe0229c01f97f3261d12dfe8586196f1fdd390349aefad2df"),
    },
    "binary_crt_remainders": {
        "dependencies": ("binary_crt", "mod_eq_to_remainder_decomposition"),
        "statement": "ddcf02df0ca3aa652ebe043c1fd2cf099ff83c77a550d263fb143dcff3147a56",
        "script": (44, "af70451e2aa8c622fb07d64f2990919364781717c493adebb465164a946363af"),
        "certificate": ((6_890, 66), 196, "f3432e4bdae49a7b4c832eb34d5c1550436a146e36a4321130d2045f4637bd2f"),
    },
    "binary_crt_beta_pair": {
        "dependencies": ("beta_modulus_nonzero", "binary_crt", "beta_at_of_mod_eq_bound"),
        "statement": "38fc1d7a370130b0342285a0d06f441aea33cfe4881d6215a86f86fdbb3ecb7e",
        "script": (47, "c922363bdbcc3cc43560fbbb358d5f408fcdd77e17092fa73a70e1549e612d71"),
        "certificate": ((6_941, 69), 201, "d0c6658e1cbb304cd57f39f2a60f1695aeac5bd52587d87d8d22ecdf29067776"),
    },
    "beta_modulus_coprime_base": {
        "dependencies": ("divides_remainder", "divisor_one", "mul_comm"),
        "statement": "e3888d0932249958689f3ec9e8d191cf866212c101dabfe5b62c198c39c4d373",
        "script": (20, "5a184438ec47cbcaefa77c2cfec764f5fab1c64509eb9ec832609392037fa545"),
        "certificate": ((874, 30), 24, "f7e3c800ecbe062e709ee0d115860418d316389e361f5b26c5e460340ed6ce42"),
    },
    "common_divisor_beta_moduli_divides_gap_times_c": {
        "dependencies": (
            "divides_remainder",
            "add_succ_left",
            "add_mul",
            "zero_add",
        ),
        "statement": "5e42d3c08bd8cc965eac53bfd7e6abfdf30d1a27ee43f0d38ab3febc24389b0f",
        "script": (27, "bf289ffe19464b806b973dc2271b0ea7218eaa5724d8f42bd0e0fea69b70ed29"),
        "certificate": ((855, 30), 24, "42a60bc7d8feda4822b114ce9a25a29d27d03a2ab6b9cb2e8a078f4942a8862a"),
    },
    "beta_moduli_coprime_of_gap_dvd": {
        "dependencies": (
            "beta_modulus_coprime_base",
            "common_divisor_beta_moduli_divides_gap_times_c",
            "multiple_trans",
            "multiple_refl",
            "gauss_coprime_cancel",
            "mul_comm",
        ),
        "statement": "df6c3daf567bc06a5ca361d2b1cfc976d2ec1bca03f3b8dd5e24dba8b0070602",
        "script": (59, "bee06c03429b6c7f54a1d21e3676efe6002f870c848181331d89c38c90945f97"),
        "certificate": ((6_007, 56), 175, "e31f87a1af34325c3566489d1e3ffe0220e721312a89d0f9a62ea1ea88cf3fe8"),
    },
    "binary_crt_beta_pair_of_gap_dvd": {
        "dependencies": ("beta_moduli_coprime_of_gap_dvd", "binary_crt_beta_pair"),
        "statement": "ca85aea2052028f5d185d8c782cf933f0d06c2c7c40d86f3657aad907f3131e5",
        "script": (27, "beef18023d324c09cc87fa9619a743277d018baa55dea765bc220d51e40aa054"),
        "certificate": ((12_980, 71), 378, "79ec20e402f2b19088c6fb04d4e63229715dbf4e5565e648b4b0f38842fa2a47"),
    },
    "bounded_common_multiple_step": {
        "dependencies": (
            "mul_eq_zero",
            "succ_ne_zero",
            "zero_or_succ",
            "multiple_mul_right",
            "mul_comm",
        ),
        "statement": "7a8fdf6f5a7e1d28efecf7a58005eb7f45d21dccd7aee4cb2cd8acbe7ca792ec",
        "script": (52, "144ec3170f18ec447363382768190823f628a9c5871656c202525ef7d650cc39"),
        "certificate": ((483, 29), 15, "aa455c44508fbe46578348227387b413695af701093b7b5daf55c1a284c9ccd0"),
    },
    "bounded_common_multiple_exists": {
        "dependencies": ("bounded_common_multiple_step", "succ_ne_zero", "add_eq_zero_left"),
        "statement": "ad3921906117ef267f82ff3e9be6d228c7872b98fccb582228c9d4a86866019f",
        "script": (29, "b8222e577fbfc91069929b6a67c9805960a397085ce99fe75c0bfedda4843953"),
        "certificate": ((640, 30), 22, "ccb71e803625625f870e7768b2428a556b41ee1700e549c7f2ddb728865729bd"),
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
    for name in (
        "mod_eq_trans",
        "mod_eq_add",
        "mod_eq_mul",
        "remainder_decomposition_to_mod_eq",
        "mod_eq_bounded_unique",
        "mod_eq_to_remainder_decomposition",
        "beta_at_exists_unique",
        "beta_at_to_mod_eq",
        "beta_at_of_mod_eq_bound",
        "binary_crt",
        "binary_crt_remainders",
        "binary_crt_beta_pair",
        "beta_modulus_coprime_base",
        "common_divisor_beta_moduli_divides_gap_times_c",
        "beta_moduli_coprime_of_gap_dvd",
        "binary_crt_beta_pair_of_gap_dvd",
        "bounded_common_multiple_step",
        "bounded_common_multiple_exists",
    ):
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
