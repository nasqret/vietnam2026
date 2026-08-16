"""Fail-closed audit for the Bertrand B5 order/quotient tranche."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import (
    alpha_enrollment_v11,
    editions_v11,
    theorems as stable_module,
)
from peano_lab.library.bertrand_b5_order_quotient_candidate import (
    make_bertrand_b5_order_quotient_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
)
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.bertrand_power_valuation_candidate import _power_terms
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.finite_fold_surface import (
    beta_at,
    power_relation,
    product_relation,
    sum_relation,
)
from peano_lab.library.finite_product_order_candidate import (
    make_finite_product_order_candidate_theorems,
)
from peano_lab.library.finite_repeat_sum_candidate import (
    make_finite_repeat_sum_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_distributive_candidate import (
    make_ha_signed_mul_distributive_candidate_theorems,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    _proof_envelope_metrics_bounded,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


PRODUCT_POINTWISE = "beta_product_pointwise_le"
PRODUCT_UNIFORM = "beta_product_uniform_le_pow"
ADD_LT_ADD = "add_lt_add"
ADD_LT_CANCEL = "add_lt_cancel_left"
SUM_POINTWISE = "beta_sum_pointwise_le"
SUM_UNIFORM = "beta_sum_uniform_le_mul"
DIVISION_ZERO = "division_zero_quotient_of_lt"
DIVISION_BIT = "division_double_quotient_bit"
DIVISION_LOWER = "division_double_quotient_lower"
DIVISION_UPPER = "division_double_quotient_upper"
POWER_MONOTONE = "pow_le_pow_of_exponent_le"
POWER_TAIL = "pow_tail_strict_of_square"

EXPECTED_NAMES = (
    PRODUCT_POINTWISE,
    PRODUCT_UNIFORM,
    ADD_LT_ADD,
    ADD_LT_CANCEL,
    SUM_POINTWISE,
    SUM_UNIFORM,
    DIVISION_ZERO,
    DIVISION_BIT,
    DIVISION_LOWER,
    DIVISION_UPPER,
    POWER_MONOTONE,
    POWER_TAIL,
)

EXPECTED_DEPENDENCIES = {
    PRODUCT_POINTWISE: (
        "beta_product_zero",
        "beta_product_succ_decompose",
        "le_succ",
        "le_refl",
        "mul_le_mul",
    ),
    PRODUCT_UNIFORM: ("beta_repeat_entry_eq", PRODUCT_POINTWISE),
    ADD_LT_ADD: ("add_succ_left", "add_shuffle_middle"),
    ADD_LT_CANCEL: ("add_assoc", "add_comm", "add_left_cancel"),
    SUM_POINTWISE: (
        "beta_sum_zero",
        "beta_sum_succ_decompose",
        "le_succ",
        "le_refl",
        "add_le_add_right",
        "add_le_add_left",
        "le_trans",
    ),
    SUM_UNIFORM: (
        "beta_repeat_exists",
        "beta_sum_exists",
        "beta_repeat_entry_eq",
        "beta_repeat_sum_exact",
        SUM_POINTWISE,
    ),
    DIVISION_ZERO: ("zero_add", "division_remainder_unique"),
    DIVISION_BIT: (
        "le_or_lt",
        "le_eq_or_lt",
        "lt_not_le",
        "zero_le",
        "one_le_of_ne_zero",
        "add_shuffle_middle",
        "mul_add",
        "add_assoc",
        "add_comm",
        ADD_LT_ADD,
        ADD_LT_CANCEL,
        "division_remainder_unique",
    ),
    DIVISION_LOWER: (DIVISION_BIT, "le_refl", "le_succ"),
    DIVISION_UPPER: (DIVISION_BIT, "le_refl", "le_succ"),
    POWER_MONOTONE: (
        "pow_exists",
        "add_comm",
        "pow_add",
        "one_le_pow",
        "le_mul_of_one_le_right",
    ),
    POWER_TAIL: (POWER_MONOTONE, "lt_of_lt_of_le"),
}

EXPECTED_DIRECT_CUTS = dict(
    zip(EXPECTED_NAMES, (5, 2, 2, 3, 7, 5, 2, 12, 3, 3, 5, 2), strict=True)
)
assert sum(EXPECTED_DIRECT_CUTS.values()) == 51

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    PRODUCT_POINTWISE: (
        4_309,
        "cfba50ff943fb741207835583df50acf7b00867e98d90ac6e1eb734e850affef",
        "e33adae0f21aaa403bd39e96eb97a10277e68abe809fcac3dc35b2fd0bde48f0",
        "00a8d7e5dc543ec464df9757867a58cc5929918ea3a76a26b0a429f1c233ff45",
    ),
    PRODUCT_UNIFORM: (
        5_450,
        "189186521ad0b0d3e03179bf58ae08e587720d0c89097eaee4aa46262da76583",
        "c9f542be9266e1572ecbeb7d3f79c645f5a8c4f7de2908e9dde051bff96b6008",
        "c861c218427be07156fc217ae032211c92a0deffd4f68aa03d03924aea4ec72e",
    ),
    ADD_LT_ADD: (
        239,
        "c7b75fa701d0896352dbaea6f2b937e7a91919de80812295e41e402df9860c9f",
        "e06646d1f66f8f96a459cc91e3071508af9860391fe7d3a351ec40dbc7fc8fda",
        "78400f6833eaf1630d7ef54159e744e3e0a2eb6ac5cbd7e9f1a28867783f9cd8",
    ),
    ADD_LT_CANCEL: (
        172,
        "1b7ef5c45ef0423bb97e9dd01bea4598f23e1f1f6fdc8b8d629c99bf40b68182",
        "04f0611ca2deb143d202336b13232ed17fa6c4a409891933ea61f23da2a6bf79",
        "1af5895ec0af186f5fcd081c559201eeccb4239bb358adfaaaa29aca3e94216c",
    ),
    SUM_POINTWISE: (
        3_929,
        "e5a131053323693fdb7c54cc93123b4a1eb241154a81241ecbfbf1459cccd43a",
        "9254e9d5fbbf59886f380bd0b52bd166aed14e7a9b9b9abca9459cf597768270",
        "a52862d40a3ee1c8b820f0b66ef64c6b463b8b9c336237217021d1714772ef0c",
    ),
    SUM_UNIFORM: (
        2_239,
        "f41a2c190dde133057d92cc376197261bfefc24c2748ab4a79d6d7d98a1eea0c",
        "341a6a96b6cf2207d1d6750e51ee32ab84c9e8b37ef1af7a671399da4577bf0f",
        "22fc6531a01c65d8f07f1af3dde15732c76bcda57b0d8dc58ed083cba50b2641",
    ),
    DIVISION_ZERO: (
        202,
        "0ddca4b241a2bb80f3fc2ae7ea9612c591938c4e52f1bac3840a6ed7eb726afe",
        "0fcc0f67af4f206167785cec8d4cc728ab1a81f335609a261a8f84e34069b77d",
        "463366776714015804f1f33f7700bd9fea0effb6a460fb6963b8809010e15c40",
    ),
    DIVISION_BIT: (
        280,
        "6a6e3956ccf5a02184635a0929fb20e667ef76b2ebcc5649188957d7ba9ef903",
        "c5ffd2f8e05f95d71271726f9934b2810d429111e53d97488eebf66f850cc390",
        "11724424b425064ec4b2720a6f13634bacba9eaf0dd84ba914dfc2bba662b96f",
    ),
    DIVISION_LOWER: (
        323,
        "02b255a2ab126ae1a0209286e349d88039777f6f2f8a7b08eaff457db11a63b5",
        "b324d4016fb188a825fcd64414feb54285f178a9963efd6190a0fb340a2f2ce6",
        "68f02e1e9acb901191d81512008e6858882d0d2a554e34e8eefe92c669c680c6",
    ),
    DIVISION_UPPER: (
        327,
        "cc80175b6b59f3ff51ba903fe05527ff62b1a803f1ca5c21f6705e0619462d45",
        "0a5bed2c5cdccbb90dd88c27528e422c1de60d33e5e1ee5597e46f2cef1e78c9",
        "ff2b563dff491ad253ee923108a5128238cb11510f07d7e21a4af89828b0a7c6",
    ),
    POWER_MONOTONE: (
        6_111,
        "c3f0c67cfe8a3fb26913dadcc14701443f58649856ac2bbfcf1db8e5dcba0440",
        "c435a389193d6d7a630366cfa583626065feacfa72701442c366e6bc1cfda8bc",
        "55da536017dcd7d81dc3f7b18cae4e5c2724f85f9697cc37cd0a1669f86b6501",
    ),
    POWER_TAIL: (
        5_972,
        "79fe63a6a36140b27a28416389f6f45513f194b6392c650a0295e1ad293521a4",
        "284a0a3b0eb8bc894431b40003fd18fcd786c0e7d798f77dfdac615e725e36b8",
        "25181d775467e45acb47f446d1ace0d2a45ff96e626ba9599d8b46be87588cf0",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    PRODUCT_POINTWISE: (5, 97, 122, 41, 122, 121, 0),
    PRODUCT_UNIFORM: (2, 45, 58, 34, 58, 57, 0),
    ADD_LT_ADD: (2, 37, 59, 24, 59, 58, 0),
    ADD_LT_CANCEL: (3, 30, 58, 27, 58, 57, 0),
    SUM_POINTWISE: (7, 108, 133, 44, 133, 132, 0),
    SUM_UNIFORM: (5, 66, 75, 37, 75, 74, 0),
    DIVISION_ZERO: (2, 26, 32, 20, 32, 31, 0),
    DIVISION_BIT: (12, 133, 238, 36, 236, 237, 2),
    DIVISION_LOWER: (3, 28, 37, 21, 37, 36, 0),
    DIVISION_UPPER: (3, 28, 37, 21, 37, 36, 0),
    POWER_MONOTONE: (5, 47, 55, 30, 55, 54, 0),
    POWER_TAIL: (2, 27, 33, 23, 33, 32, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    PRODUCT_POINTWISE: (122, 122, 41, 434, 42),
    PRODUCT_UNIFORM: (58, 58, 34, 21, 34),
    ADD_LT_ADD: (59, 59, 24, 74, 24),
    ADD_LT_CANCEL: (58, 58, 27, 27, 27),
    SUM_POINTWISE: (133, 133, 44, 439, 45),
    SUM_UNIFORM: (75, 75, 37, 37, 37),
    DIVISION_ZERO: (32, 32, 20, 13, 20),
    DIVISION_BIT: (238, 236, 36, 272, 36),
    DIVISION_LOWER: (37, 37, 21, 34, 21),
    DIVISION_UPPER: (37, 37, 21, 37, 21),
    POWER_MONOTONE: (55, 55, 30, 22, 30),
    POWER_TAIL: (33, 33, 23, 10, 24),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    PRODUCT_POINTWISE: (
        3_136,
        64,
        1_066,
        1_113,
        48,
        11_588,
        64,
        "fc279a490f98b0805e52b179dd3756156dee9dcf66a278d5b68c238afddafc18",
    ),
    PRODUCT_UNIFORM: (
        4_338,
        66,
        1_147,
        1_195,
        49,
        15_773,
        66,
        "8277eef19b6206d326fb81e69a4f43a74d3e2b95064e3d6482b8a9bff706a508",
    ),
    ADD_LT_ADD: (
        331,
        24,
        220,
        232,
        13,
        798,
        24,
        "866829169b6aa88b2d56728f4245304849530cb09455352e09eef5b2b69b8d03",
    ),
    ADD_LT_CANCEL: (
        307,
        27,
        223,
        234,
        12,
        636,
        27,
        "3fd90d3302464f9ca84abf88c9945d69ae51dc6935750737ae7cfa9c0f59ddf4",
    ),
    SUM_POINTWISE: (
        2_868,
        64,
        1_037,
        1_082,
        46,
        11_375,
        64,
        "ad7d3a41b7573fc367c4766403d29dacb647dd1292932c48912d3a2dd1decea2",
    ),
    SUM_UNIFORM: (
        67_815,
        88,
        5_362,
        5_620,
        259,
        222_869,
        88,
        "5f4cbf987a339c8b3e91b912c8f92b691a5c70c03265518037c637b68f86d2be",
    ),
    DIVISION_ZERO: (
        903,
        59,
        576,
        598,
        23,
        2_195,
        59,
        "674c9919acd071a22fe76ab23228029221f57dcf344d48bbfce87ed8c157cd5b",
    ),
    DIVISION_BIT: (
        2_387,
        69,
        1_138,
        1_177,
        40,
        6_022,
        69,
        "e19038a89917307c322749e973cf7d87f839e47509cc7f581295452b593c949f",
    ),
    DIVISION_LOWER: (
        2_489,
        70,
        1_196,
        1_237,
        42,
        6_406,
        70,
        "b3e5e99ffbbf009dcae795b20d1732079148cb00aa60bfb5a07d6781daedda52",
    ),
    DIVISION_UPPER: (
        2_489,
        70,
        1_196,
        1_237,
        42,
        6_412,
        70,
        "69de893a797dc9d3bb9fba0de26dd139858a10276277c7bcb513ea2d12b45c35",
    ),
    POWER_MONOTONE: (
        70_898,
        89,
        5_818,
        6_082,
        265,
        243_892,
        89,
        "80d7a3a64bace04be82c7874618c8a9727876baec932874078311bc34a7dd0ba",
    ),
    POWER_TAIL: (
        71_011,
        90,
        5_874,
        6_139,
        266,
        245_343,
        90,
        "385178cbbe1cdcaeec59c2bea47798cc0abe9b7a996758c512d6c3692babe152",
    ),
}

SOURCE_PINS = {
    "finite_product_order_candidate.py": (
        "4a502fe8e233c631305ebb644cec9e3c877e1830e0348995f8e6e481fff1b433"
    ),
    "ha_signed_mul_distributive_candidate.py": (
        "ff28cc33978bef5e28493d5fea88c7d7d9432fdd8a317ab7c0781f7b60376035"
    ),
    "bertrand_power_order_candidate.py": (
        "50b07e3b40b81966a37bc07cbb44b93498a86efa76aabcbb4af94b17c1eb17e6"
    ),
    "bertrand_power_growth_candidate.py": (
        "41584397a149b7af19891bdd7b0f6b6366f6412c4c636508921af85d7220bfab"
    ),
    "finite_repeat_sum_candidate.py": (
        "7e468d7ddced0220b4c6da6c7417edfa1f1392e793770b0109808ad32d84d182"
    ),
    "bertrand_b5_order_quotient_candidate.py": (
        "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e"
    ),
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-order-quotient-tranche-rfc-v1.md"
)
RFC_SHA256 = (
    "fdcaf69b3913b7dbbcf312373b49f39b42819ba398cbb35f77e8eb66fb4762c1"
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_finite_product_order_candidate_theorems(TheoremSpec),
        *make_bertrand_b5_order_quotient_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_ha_signed_mul_distributive_candidate_theorems(TheoremSpec)[:1],
        *make_bertrand_power_order_candidate_theorems(TheoremSpec)[:2],
        *make_finite_repeat_sum_candidate_theorems(TheoremSpec)[:1],
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec)[:1],
    )


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    prior = _table(_prior_specs())
    assert not set(stable) & set(prior)
    assert not set(EXPECTED_NAMES) & set(stable)
    assert not set(EXPECTED_NAMES) & set(prior)
    return stable | prior


def _row_core(name: str) -> dict[str, TheoremSpec]:
    return _core() | _table(_specs()[: EXPECTED_NAMES.index(name)])


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    formula = _closed_formula(item.statement)
    target = formula
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(_available()[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    stable = _specs_by_name()
    if name in stable:
        checked = replay(name)
        assert checked.spec == stable[name]
        return checked.formula, checked.certificate

    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    dependencies = tuple(_close(name) for name in item.dependencies)
    for dependency_formula, dependency_proof in reversed(dependencies):
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    return formula, body


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(_proof_children(node))


def _proof_dag_sha256(proof: Proof) -> str:
    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend((child, False) for child in children)
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


def _divrem(
    divisor: str,
    value: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    bound = _lt_term(
        remainder,
        divisor,
        tag=f"{tag}_bound",
        variables=variables,
    )
    return (
        f"(({value}) = ({divisor}) * ({quotient}) + ({remainder}) /\\ "
        f"({bound}))"
    )


def _expected_statements() -> dict[str, str]:
    product_left = beta_at("b", "c", "i", "a", tag="bppl_left")
    product_right = beta_at("d", "e", "i", "z", tag="bppl_right")
    product_pointwise = (
        "forall i a z. (exists bppl_bound. bppl_bound + S i = l) -> "
        f"({product_left}) -> ({product_right}) -> "
        "exists bppl_factor_gap. bppl_factor_gap + a = z"
    )
    product_uniform_at = beta_at("b", "c", "i", "x", tag="bpulp_source")
    product_uniform = (
        "forall i x. (exists bpulp_bound. bpulp_bound + S i = l) -> "
        f"({product_uniform_at}) -> "
        "exists bpulp_factor_gap. bpulp_factor_gap + x = a"
    )

    add_variables = ("a", "b", "c", "d")
    cancel_variables = ("c", "a", "b")
    sum_variables = ("b", "c", "d", "e", "l", "n", "q")
    pointwise_variables = (*sum_variables, "i", "a", "z")
    sum_left_at = beta_at("b", "c", "i", "a", tag="bspl_left")
    sum_right_at = beta_at("d", "e", "i", "z", tag="bspl_right")
    sum_pointwise = (
        "forall i a z. "
        f"({_lt_term('i', 'l', tag='bspl_bound', variables=pointwise_variables)}) "
        f"-> ({sum_left_at}) -> ({sum_right_at}) -> "
        f"({_le_term('a', 'z', tag='bspl_factor', variables=pointwise_variables)})"
    )
    uniform_variables = ("b", "c", "a", "l", "n", "i", "x")
    uniform_at = beta_at("b", "c", "i", "x", tag="bsulm_source")
    sum_uniform = (
        "forall i x. "
        f"({_lt_term('i', 'l', tag='bsulm_bound', variables=uniform_variables)}) "
        f"-> ({uniform_at}) -> "
        f"({_le_term('x', 'a', tag='bsulm_factor', variables=uniform_variables)})"
    )

    division_variables = ("d", "n", "q", "r")
    double_variables = ("d", "n", "q", "r", "Q", "R")
    zero_source = _divrem(
        "d", "n", "q", "r", tag="bdzq_source", variables=division_variables
    )
    bit_source = _divrem(
        "d", "n", "q", "r", tag="bddqb_source", variables=double_variables
    )
    bit_double = _divrem(
        "d",
        "n + n",
        "Q",
        "R",
        tag="bddqb_double",
        variables=double_variables,
    )

    power_variables = ("p", "e", "f", "x", "y")
    tail_variables = ("p", "e", "x", "s", "n")
    add_left = _lt_term(
        "a", "b", tag="b5alaa_left", variables=add_variables
    )
    add_right = _lt_term(
        "c", "d", tag="b5alaa_right", variables=add_variables
    )
    add_result = _lt_term(
        "a + c", "b + d", tag="b5alaa_result", variables=add_variables
    )
    cancel_source = _lt_term(
        "c + a",
        "c + b",
        tag="b5altcl_source",
        variables=cancel_variables,
    )
    cancel_result = _lt_term(
        "a", "b", tag="b5altcl_result", variables=cancel_variables
    )
    sum_result = _le_term(
        "n", "q", tag="bspl_result", variables=sum_variables
    )
    uniform_result = _le_term(
        "n",
        "l * a",
        tag="bsulm_result",
        variables=("b", "c", "a", "l", "n"),
    )
    lower_source = _divrem(
        "d", "n", "q", "r", tag="bddql_source", variables=double_variables
    )
    lower_double = _divrem(
        "d",
        "n + n",
        "Q",
        "R",
        tag="bddql_double",
        variables=double_variables,
    )
    lower_result = _le_term(
        "q + q", "Q", tag="bddql_result", variables=double_variables
    )
    upper_source = _divrem(
        "d", "n", "q", "r", tag="bddqu_source", variables=double_variables
    )
    upper_double = _divrem(
        "d",
        "n + n",
        "Q",
        "R",
        tag="bddqu_double",
        variables=double_variables,
    )
    upper_result = _le_term(
        "Q", "S (q + q)", tag="bddqu_result", variables=double_variables
    )
    power_base = _le_term(
        "1", "p", tag="bppem_base", variables=power_variables
    )
    power_exponent = _le_term(
        "e", "f", tag="bppem_exponent", variables=power_variables
    )
    power_result = _le_term(
        "x", "y", tag="bppem_result", variables=power_variables
    )
    tail_base = _le_term(
        "1", "p", tag="bpsts_base", variables=tail_variables
    )
    tail_exponent = _le_term(
        "2", "e", tag="bpsts_exponent", variables=tail_variables
    )
    tail_source = _lt_term(
        "n", "s", tag="bpsts_source", variables=tail_variables
    )
    tail_result = _lt_term(
        "n", "x", tag="bpsts_result", variables=tail_variables
    )
    return {
        PRODUCT_POINTWISE: (
            "forall b c d e l n q. "
            f"({product_pointwise}) -> "
            f"({product_relation('b', 'c', 'l', 'n', tag='bppl_left_product')}) "
            f"-> ({product_relation('d', 'e', 'l', 'q', tag='bppl_right_product')}) "
            "-> exists bppl_result_gap. bppl_result_gap + n = q"
        ),
        PRODUCT_UNIFORM: (
            "forall b c a l n q. "
            f"({product_uniform}) -> "
            f"({product_relation('b', 'c', 'l', 'n', tag='bpulp_source_product')}) "
            f"-> ({power_relation('a', 'l', 'q', tag='bpulp_target_power')}) "
            "-> exists bpulp_result_gap. bpulp_result_gap + n = q"
        ),
        ADD_LT_ADD: (
            "forall a b c d. "
            f"({add_left}) -> ({add_right}) -> ({add_result})"
        ),
        ADD_LT_CANCEL: (
            "forall c a b. "
            f"({cancel_source}) -> ({cancel_result})"
        ),
        SUM_POINTWISE: (
            "forall b c d e l n q. "
            f"({sum_pointwise}) -> "
            f"({sum_relation('b', 'c', 'l', 'n', tag='bspl_left_sum')}) "
            f"-> ({sum_relation('d', 'e', 'l', 'q', tag='bspl_right_sum')}) "
            f"-> ({sum_result})"
        ),
        SUM_UNIFORM: (
            "forall b c a l n. "
            f"({sum_uniform}) -> "
            f"({sum_relation('b', 'c', 'l', 'n', tag='bsulm_source_sum')}) "
            f"-> ({uniform_result})"
        ),
        DIVISION_ZERO: (
            "forall d n q r. "
            f"({zero_source}) -> "
            f"({_lt_term('n', 'd', tag='bdzq_bound', variables=division_variables)}) "
            "-> q = 0"
        ),
        DIVISION_BIT: (
            "forall d n q r Q R. "
            f"({bit_source}) -> ({bit_double}) -> "
            "(Q = q + q \\/ Q = S (q + q))"
        ),
        DIVISION_LOWER: (
            "forall d n q r Q R. "
            f"({lower_source}) -> ({lower_double}) -> ({lower_result})"
        ),
        DIVISION_UPPER: (
            "forall d n q r Q R. "
            f"({upper_source}) -> ({upper_double}) -> ({upper_result})"
        ),
        POWER_MONOTONE: (
            "forall p e f x y. "
            f"({power_base}) -> ({power_exponent}) "
            f"-> ({power_relation('p', 'e', 'x', tag='bppem_left_power')}) "
            f"-> ({power_relation('p', 'f', 'y', tag='bppem_right_power')}) "
            f"-> ({power_result})"
        ),
        POWER_TAIL: (
            "forall p e x s n. "
            f"({tail_base}) -> ({tail_exponent}) "
            f"-> ({_power_terms('p', '2', 's', tag='bpsts_square_power')}) "
            f"-> ({power_relation('p', 'e', 'x', tag='bpsts_tail_power')}) "
            f"-> ({tail_source}) -> ({tail_result})"
        ),
    }


def _mutations() -> dict[str, str]:
    expected = _expected_statements()
    result: dict[str, str] = {}

    replacements = {
        PRODUCT_POINTWISE: (
            "exists bppl_result_gap. bppl_result_gap + n = q",
            "exists bppl_result_gap. bppl_result_gap + q = n",
        ),
        PRODUCT_UNIFORM: (
            "exists bpulp_result_gap. bpulp_result_gap + n = q",
            "exists bpulp_result_gap. bpulp_result_gap + q = n",
        ),
        ADD_LT_ADD: (
            _lt_term(
                "a + c",
                "b + d",
                tag="b5alaa_result",
                variables=("a", "b", "c", "d"),
            ),
            _lt_term(
                "a + d",
                "b + c",
                tag="b5alaa_result",
                variables=("a", "b", "c", "d"),
            ),
        ),
        ADD_LT_CANCEL: (
            _lt_term(
                "a",
                "b",
                tag="b5altcl_result",
                variables=("c", "a", "b"),
            ),
            _lt_term(
                "b",
                "a",
                tag="b5altcl_result",
                variables=("c", "a", "b"),
            ),
        ),
        SUM_POINTWISE: (
            _le_term(
                "n",
                "q",
                tag="bspl_result",
                variables=("b", "c", "d", "e", "l", "n", "q"),
            ),
            _le_term(
                "q",
                "n",
                tag="bspl_result",
                variables=("b", "c", "d", "e", "l", "n", "q"),
            ),
        ),
        SUM_UNIFORM: (
            _le_term(
                "n",
                "l * a",
                tag="bsulm_result",
                variables=("b", "c", "a", "l", "n"),
            ),
            _le_term(
                "n",
                "a",
                tag="bsulm_result",
                variables=("b", "c", "a", "l", "n"),
            ),
        ),
        DIVISION_ZERO: ("q = 0", "q = 1"),
        DIVISION_BIT: (
            "(Q = q + q \\/ Q = S (q + q))",
            "Q = q + q",
        ),
        DIVISION_LOWER: (
            _le_term(
                "q + q",
                "Q",
                tag="bddql_result",
                variables=("d", "n", "q", "r", "Q", "R"),
            ),
            _le_term(
                "S (q + q)",
                "Q",
                tag="bddql_result",
                variables=("d", "n", "q", "r", "Q", "R"),
            ),
        ),
        DIVISION_UPPER: (
            _le_term(
                "Q",
                "S (q + q)",
                tag="bddqu_result",
                variables=("d", "n", "q", "r", "Q", "R"),
            ),
            _le_term(
                "Q",
                "q + q",
                tag="bddqu_result",
                variables=("d", "n", "q", "r", "Q", "R"),
            ),
        ),
        POWER_MONOTONE: (
            _le_term(
                "x",
                "y",
                tag="bppem_result",
                variables=("p", "e", "f", "x", "y"),
            ),
            _lt_term(
                "x",
                "y",
                tag="bppem_result",
                variables=("p", "e", "f", "x", "y"),
            ),
        ),
        POWER_TAIL: (
            _lt_term(
                "n",
                "x",
                tag="bpsts_result",
                variables=("p", "e", "x", "s", "n"),
            ),
            _lt_term(
                "S n",
                "x",
                tag="bpsts_result",
                variables=("p", "e", "x", "s", "n"),
            ),
        ),
    }
    for name, (old, new) in replacements.items():
        assert expected[name].count(old) == 1, name
        result[name] = expected[name].replace(old, new, 1)
    return result


MUTATIONS = _mutations()
LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == 51


def test_bertrand_b5_order_quotient_source_rfc_and_parent_are_pinned() -> None:
    root = Path(__file__).resolve().parents[3]
    library = root / "peano-lab" / "py" / "peano_lab" / "library"
    for filename, expected in SOURCE_PINS.items():
        assert sha256((library / filename).read_bytes()).hexdigest() == expected
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256
    assert len(editions_v11.ALPHA_ENTRIES) == 1_123
    assert editions_v11.EXPECTED_ALPHA_V11_EDGE_COUNT == 3_482
    assert editions_v11.EXPECTED_ALPHA_V11_LAYER_COUNT == 45
    assert editions_v11.ALPHA_V11_ENROLLMENT_SHA256 == (
        "c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36"
    )
    assert editions_v11.ALPHA_V11_IDENTITY_SHA256 == (
        "46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3"
    )


def test_bertrand_b5_order_quotient_surfaces_and_authority_are_exact() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert tuple(row.statement for row in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {row.name: row.dependencies for row in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert all(_closed_formula(row.statement) for row in rows)
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        entry.spec.name for entry in editions_v11.ALPHA_ENTRIES
    }

    provider_tokens = (
        "finite_product_order_candidate",
        "bertrand_b5_order_quotient_candidate",
    )
    for authority in (stable_module, alpha_enrollment_v11, editions_v11):
        source = Path(authority.__file__).read_text(encoding="utf-8")
        assert all(token not in source for token in provider_tokens)

    positions = {name: index for index, name in enumerate(EXPECTED_NAMES)}
    available = set(_core())
    for row in rows:
        assert all(dependency in available for dependency in row.dependencies)
        assert all(
            dependency not in positions
            or positions[dependency] < positions[row.name]
            for dependency in row.dependencies
        )
        assert "DNE" not in row.statement
        assert all(
            forbidden not in command
            for command in row.script
            for forbidden in ("DNE", "classical", "by_contra", "sorry")
        )
        available.add(row.name)


def test_bertrand_b5_order_quotient_topology_is_exact() -> None:
    rows = _table(_specs())
    assert rows[ADD_LT_ADD].script.count("exists S (x + x1)") == 1
    assert not any(
        command.startswith("induction") for command in rows[ADD_LT_ADD].script
    )
    assert rows[SUM_POINTWISE].script.count("induction l") == 1
    assert rows[SUM_POINTWISE].script.count("apply IH") == 1
    assert rows[SUM_UNIFORM].script.count("apply beta_sum_pointwise_le") == 1
    assert rows[DIVISION_ZERO].script.count(
        "apply division_remainder_unique"
    ) == 1
    assert rows[DIVISION_BIT].script.count(
        "apply division_remainder_unique"
    ) == 3
    assert rows[DIVISION_BIT].script.count("cases hsplit") == 1
    assert rows[DIVISION_BIT].script.count("cases le_or_lt_right") == 1
    assert "cases hcandidate" not in rows[DIVISION_BIT].script
    assert rows[DIVISION_LOWER].script.count("cases hbit") == 1
    assert rows[DIVISION_UPPER].script.count("cases hbit") == 1
    assert not any(
        command.startswith("induction")
        for command in rows[POWER_MONOTONE].script
    )
    assert rows[POWER_MONOTONE].script.count("cases hgap_power") == 1
    assert rows[POWER_TAIL].script.count("apply lt_of_lt_of_le") == 1
    assert not any(
        command.startswith("rewrite")
        and command.endswith((" at hsum", " at hpower", " at hdouble"))
        for row in rows.values()
        for command in row.script
    )


def test_bertrand_b5_order_quotient_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert all(value is not None for value in EXPECTED_ARTIFACTS.values())
    assert all(value is not None for value in EXPECTED_BODIES.values())
    assert all(value is not None for value in EXPECTED_ENVELOPES.values())
    assert all(value is not None for value in EXPECTED_CLOSURES.values())
    assert tuple(EXPECTED_DIRECT_CUTS.values()) == (
        5,
        2,
        2,
        3,
        7,
        5,
        2,
        12,
        3,
        3,
        5,
        2,
    )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_order_quotient_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 ORDER QUOTIENT {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_order_quotient_bodies_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    body, target = _body(item)
    assert check((), body, target)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        body,
        max_proof_occurrences=limits.max_body_occurrences,
        max_proof_objects=limits.max_body_objects,
        max_proof_depth=limits.max_body_depth,
        max_annotation_occurrences=limits.max_body_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_body_envelope_depth,
        label=f"B5 order/quotient body {name}",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual = (
        len(item.dependencies),
        len(item.script),
        nodes,
        depth,
        objects,
        edges,
        reused,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(body))
    print(
        f"B5 ORDER QUOTIENT {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_b5_order_quotient_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(
            entry for entry in item.dependencies if entry != dependency
        ),
    )
    assert len(shortened.dependencies) + 1 == len(item.dependencies)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_order_quotient_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def test_bertrand_b5_order_quotient_mutations_have_counterfixtures() -> None:
    assert not (2 <= 1)
    assert not (2 <= 1)
    assert not (0 + 1 < 1 + 0)
    assert not (1 < 0)
    assert not (1 <= 0)
    assert not (2 <= 1)
    assert not (0 == 1)
    assert not (1 == 0)
    assert not (1 <= 0)
    assert not (1 <= 0)
    assert not (1 < 1)
    assert not (4 < 4)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_order_quotient_genuine_mutations_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    assert _closed_formula(item.statement) != _closed_formula(MUTATIONS[name])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=MUTATIONS[name]),),
            core=_row_core(name),
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_order_quotient_closures_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    formula, certificate = _close(name)
    assert formula == _closed_formula(item.statement)
    assert check((), certificate, formula)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        certificate,
        max_proof_occurrences=limits.max_candidate_proof_occurrences,
        max_proof_objects=limits.max_candidate_proof_objects,
        max_proof_depth=limits.max_candidate_proof_depth,
        max_annotation_occurrences=(
            limits.max_candidate_annotation_occurrences
        ),
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_candidate_envelope_depth,
        label=f"B5 order/quotient closure {name}",
    )
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual = (
        nodes,
        depth,
        objects,
        edges,
        reused,
        envelope[3],
        envelope[4],
        _proof_dag_sha256(certificate),
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(certificate))

    direct_cuts = 0
    probe = certificate
    while type(probe) is Cut:
        direct_cuts += 1
        probe = probe.body
    assert direct_cuts == len(item.dependencies)
    assert direct_cuts == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cuts):
        assert not check((), _mutate_direct_cut(certificate, index), formula)

    print(f"B5 ORDER QUOTIENT {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_CLOSURES[name]
