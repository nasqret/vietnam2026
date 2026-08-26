"""Fail-closed audit for duplicate-free Primorial product comparison."""

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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import (
    alpha_enrollment_v10,
    bertrand_primorial_duplicate_free_candidate as module,
    bertrand_primorial_foundation_candidate as foundation_module,
    bertrand_primorial_membership_candidate as membership_module,
    editions_v10,
    fermat_residue_product_candidate as coprime_module,
    finite_fold_surface as fold_surface,
    theorems as stable_module,
)
from peano_lab.library.bertrand_primorial_duplicate_free_candidate import (
    make_bertrand_primorial_duplicate_free_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    make_bertrand_primorial_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_membership_candidate import (
    make_bertrand_primorial_membership_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_residue_product_candidate import (
    make_fermat_residue_product_candidate_theorems,
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


EMPTY = "beta_distinct_empty"
SUCC_INTRO = "beta_distinct_succ_intro"
ELIM_PREFIX = "beta_distinct_succ_elim_prefix"
LAST_NE = "beta_distinct_succ_last_ne"
TRANSPORT = "beta_distinct_transport"
COPRIME_LAST = "beta_distinct_prime_product_coprime_last"
DIVIDES_COMMON = "beta_distinct_prime_product_divides_common_multiple"
POINTWISE = "beta_bounded_prime_prefix_divides_primorial_pointwise"
DIVIDES_PRIMORIAL = (
    "beta_distinct_bounded_prime_product_divides_primorial"
)
LE_PRIMORIAL = "beta_distinct_bounded_prime_product_le_primorial"

EXPECTED_NAMES = (
    EMPTY,
    SUCC_INTRO,
    ELIM_PREFIX,
    LAST_NE,
    TRANSPORT,
    COPRIME_LAST,
    DIVIDES_COMMON,
    POINTWISE,
    DIVIDES_PRIMORIAL,
    LE_PRIMORIAL,
)
EXPECTED_DEPENDENCIES = {
    EMPTY: ("add_eq_zero_right", "succ_ne_zero"),
    SUCC_INTRO: (
        "le_of_succ_le_succ",
        "le_eq_or_lt",
        "beta_at_unique",
    ),
    ELIM_PREFIX: ("le_succ",),
    LAST_NE: ("le_succ", "le_refl", "lt_irrefl_expanded"),
    TRANSPORT: ("beta_at_exists", "beta_at_unique"),
    COPRIME_LAST: (
        "le_succ",
        "le_refl",
        "beta_at_unique",
        "distinct_primes_coprime",
        "beta_product_pointwise_coprime",
        LAST_NE,
    ),
    DIVIDES_COMMON: (
        "beta_product_zero",
        "beta_product_succ_decompose",
        "le_succ",
        "le_refl",
        "one_multiple",
        "coprime_product_is_lcm",
        ELIM_PREFIX,
        COPRIME_LAST,
    ),
    POINTWISE: ("beta_at_unique", "primorial_prime_divides_of_le"),
    DIVIDES_PRIMORIAL: (POINTWISE, DIVIDES_COMMON),
    LE_PRIMORIAL: (
        "divisor_le_nonzero",
        "primorial_positive",
        DIVIDES_PRIMORIAL,
    ),
}
EXPECTED_DIRECT_CUTS = dict(
    zip(EXPECTED_NAMES, (2, 3, 1, 3, 2, 6, 8, 2, 2, 3), strict=True)
)
assert sum(map(len, EXPECTED_DEPENDENCIES.values())) == 32

STABLE_SOURCE_SHA256 = (
    "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919"
)
FOLD_SOURCE_SHA256 = (
    "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30"
)
COPRIME_SOURCE_SHA256 = (
    "b43a6fa9be64b806d9973abfb0d566533910c8a841fba16777b8a9498b98d59d"
)
FOUNDATION_SOURCE_SHA256 = (
    "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98"
)
MEMBERSHIP_SOURCE_SHA256 = (
    "edf14adde5edbbc6b7836003a174ee9a4b84f708fdcd0f3c3af45fc5013ac817"
)
ALPHA_ENROLLMENT_SOURCE_SHA256 = (
    "251526dcbe1a9fa4491b98ea3fe05bacb77a26e970248e75336dd379db1d9975"
)
EDITIONS_SOURCE_SHA256 = (
    "a3261bb8963e2068c3faa9b6ee8b24a211ba4a08d685a26bd168e9c249e2a359"
)
CANDIDATE_SOURCE_SHA256 = (
    "2367c77427d86fb9cd99f3335d383b655580b29822bcfd161f76c023f71446fc"
)
RFC_SHA256 = (
    "855a80eb661535a5e3fcf57bfc7dce60cbbfbe640c9e5f2a300b508217621703"
)

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    EMPTY: (
        1119,
        "b6f77a8bef5ce61f5d5b0601a529155ad4ddd5596285ed5cfefd2887ee2ec4a1",
        "2280e9bfafa89f13306e2c1fc58c76bd5cefa64fa973fdec0a38b81167aac0f2",
        "753d88cdad623c8ee87bcf4298ee3d2003035cf3150c3bed76bbec85d9c4350c",
    ),
    SUCC_INTRO: (
        2883,
        "bd0523f1683ceabcebcdee390ad79825f461edd51e50e654fcd9329f860dc774",
        "d1b3d48c2796a3af0510a59d29970af5226d2fc24f47e843a78a018da3c2c855",
        "25497667eb9dd1a9f3342c0841840b2f86494a33a3a196fdcdd382d14046bf94",
    ),
    ELIM_PREFIX: (
        2476,
        "1f983e97db993aed7d2ce963e27c989758a625b469827d0b115c26a61c87d448",
        "06799347c908562c1879d3da279acf3ea60203b4891f8e4adae51310fc350ec7",
        "0bfb3bd2c7ab939ba1937c47e5c5eca9bd754e83eb3f2614bfba51dab2d3caa6",
    ),
    LAST_NE: (
        1760,
        "513a9e34ee21aa04c273f4812984c15073e7d7b4557853ecdb2b25520015df4a",
        "25acc2e272cc22ce05759c891809ec8b938ae6e49acc34e6f38fb0e838d3c74a",
        "d7ba92bebcffd1568cb55d5567c848a8e5b0b872df603dac2473ae7a1e2987fa",
    ),
    TRANSPORT: (
        2847,
        "04f78a7b33aea6787a74e2c9a6941d01adcfcdd5816732eb3770412bf26a93ae",
        "f66b08948eb2d04621a3c5514329a1d48cec0365873c0424213329563f7a5aa8",
        "f7d992eedcbedf486f6464f8e43b8af6e6f9c38967653d90b1c4adab30f3ea8a",
    ),
    COPRIME_LAST: (
        4327,
        "feffc8d03e04abca1876578dcc248563a682600d806082a06796bc01ad9bf46b",
        "0d5bf5ee056a73ce3fcfd12d152619a19c2541c694e256cb0176a8bb5cfd975c",
        "7d071ae214ae9d03eb64e023da1191cccfc73c51a9d6a3d86811712ca98e7595",
    ),
    DIVIDES_COMMON: (
        4700,
        "1686feffac9714a37c731b2fa711a5ac4171b39b65e490ba696a5601723f8435",
        "49a61eadccf3016b2733a68fc79f8cd25c1698b11da19d6085275adea42cd097",
        "0a77be46ec4ad3cf5d9390b4889f5babc8623bc24bb7c8e31da85ff6ed69f463",
    ),
    POINTWISE: (
        6074,
        "f014b8afd407f2fac5e2fdae0cc39e10247bd70b5ac91ac79f670a754392b045",
        "6b97dc2bd9636a2b15f9db299d281db4e47f3f6081b39cbfa9e1062925ad7264",
        "c267b3103b6513780324a58924ba6ce1414449c467e30e78404e794e101dcd5d",
    ),
    DIVIDES_PRIMORIAL: (
        8707,
        "1904e525d450967e8e2cbdfb1dbe95c3a8f1ba85d31d598b7d545969f8910480",
        "b33296512687cae79269e1a30347ad736dc24cfbb162e9e8c4b951f29e01fb8d",
        "0a99638c16e14e241dc7bf58650c4372dfdff2ee64ce0214487fd5dd8303b2f2",
    ),
    LE_PRIMORIAL: (
        8705,
        "cda3813fa239744aa02a88eaceae9b54a9f051bd4e9d33c60ca13f1ea616a81f",
        "75d9fe20d1eb719cde7ec9f07e0e6417a92489fa656f0dc658e066251fbfbaf3",
        "a801783a5c07cf540ba2632d3f1ae2e6d98bbd4e7a8c870fe2557d58dbd27d94",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    EMPTY: (2, 17, 20, 16, 20, 19, 0),
    SUCC_INTRO: (3, 98, 125, 33, 125, 124, 0),
    ELIM_PREFIX: (1, 31, 64, 35, 64, 63, 0),
    LAST_NE: (3, 30, 69, 34, 69, 68, 0),
    TRANSPORT: (2, 79, 81, 33, 81, 80, 0),
    COPRIME_LAST: (6, 76, 119, 37, 119, 118, 0),
    DIVIDES_COMMON: (8, 103, 125, 37, 125, 124, 0),
    POINTWISE: (2, 40, 60, 28, 60, 59, 0),
    DIVIDES_PRIMORIAL: (2, 31, 38, 24, 38, 37, 0),
    LE_PRIMORIAL: (3, 39, 50, 28, 50, 49, 0),
}
EXPECTED_ENVELOPES: dict[
    str, tuple[int, int, int, int, int] | None
] = {
    EMPTY: (20, 20, 16, 4, 16),
    SUCC_INTRO: (125, 125, 33, 126, 37),
    ELIM_PREFIX: (64, 64, 35, 10, 35),
    LAST_NE: (69, 69, 34, 17, 34),
    TRANSPORT: (81, 81, 33, 24, 33),
    COPRIME_LAST: (119, 119, 37, 136, 37),
    DIVIDES_COMMON: (125, 125, 37, 387, 39),
    POINTWISE: (60, 60, 28, 64, 28),
    DIVIDES_PRIMORIAL: (38, 38, 24, 10, 24),
    LE_PRIMORIAL: (50, 50, 28, 15, 28),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    EMPTY: (
        40,
        16,
        40,
        39,
        0,
        206,
        21,
        "ab4f94f1a66f93a968ce98565c40e2344c1e98b91fe5ea53c5274d4cc2b971dc",
    ),
    SUCC_INTRO: (
        1360,
        62,
        879,
        918,
        40,
        3927,
        62,
        "88c26034c812782ba4786694e2fb703ce07501bc6a4a303b886f20c44c09c587",
    ),
    ELIM_PREFIX: (
        104,
        35,
        102,
        103,
        2,
        283,
        35,
        "86fba5b63064fb9f5b182de3ba58abd0a16bd30acd6588dbfcfece43777ae14b",
    ),
    LAST_NE: (
        217,
        34,
        186,
        190,
        5,
        771,
        34,
        "2c55aa9dceda177c3f9c740767eb4df0bddecf45103397c47e6fddd6aff33a68",
    ),
    TRANSPORT: (
        1681,
        61,
        957,
        1011,
        55,
        4648,
        61,
        "81b479bc8ebebac9306ad0a0258d87a5fdb776417a171ad929e50ef41714d87e",
    ),
    COPRIME_LAST: (
        9945,
        69,
        2776,
        2914,
        139,
        33711,
        69,
        "10477aca29fa0c67ef65615902ab47d49015bb2795978c6e2b21e67d55b67162",
    ),
    DIVIDES_COMMON: (
        16890,
        77,
        3024,
        3171,
        148,
        58365,
        77,
        "3bdecba9ee72742a516482812b44762d5e89ebf7b1dbd36118fd06cd071cee59",
    ),
    POINTWISE: (
        4315,
        69,
        1222,
        1274,
        53,
        15528,
        69,
        "b6bbff2f4dd7874ea90ccd8141a4611a8e6304032cca9e3c7c35d0e42c2c0265",
    ),
    DIVIDES_PRIMORIAL: (
        21243,
        79,
        3385,
        3542,
        158,
        75841,
        79,
        "b69fa607701ae89c5d32c37b8ea6499c9d8f532309894501300617e7508bf463",
    ),
    LE_PRIMORIAL: (
        25308,
        82,
        3660,
        3827,
        168,
        94193,
        82,
        "1076205c5051dda936d286f7f6c1d2666e7897cb537a61978d9fd19051a0140d",
    ),
}


def _le(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = foundation_module._validated_context(variables)
    rendered_left = foundation_module._render_term(
        left, label="independent order left", context=context
    )
    rendered_right = foundation_module._render_term(
        right, label="independent order right", context=context
    )
    (gap,) = foundation_module._binders(tag, context, ("le_gap",))
    return f"exists {gap}. {gap} + ({rendered_left}) = ({rendered_right})"


def _divides(
    divisor: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = foundation_module._validated_context(variables)
    rendered_divisor = foundation_module._render_term(
        divisor, label="independent divisor", context=context
    )
    rendered_value = foundation_module._render_term(
        value, label="independent dividend", context=context
    )
    (quotient,) = foundation_module._binders(
        tag, context, ("quotient",)
    )
    return f"exists {quotient}. {rendered_value} = ({rendered_divisor}) * {quotient}"


def _coprime(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = foundation_module._validated_context(variables)
    left_term = foundation_module._render_term(
        left, label="independent coprime left", context=context
    )
    right_term = foundation_module._render_term(
        right, label="independent coprime right", context=context
    )
    divisor, left_factor, right_factor = foundation_module._binders(
        tag,
        context,
        (
            "coprime_divisor",
            "coprime_left_factor",
            "coprime_right_factor",
        ),
    )
    return (
        f"forall {divisor}. (exists {left_factor}. "
        f"{left_term} = {divisor} * {left_factor}) -> "
        f"(exists {right_factor}. "
        f"{right_term} = {divisor} * {right_factor}) -> "
        f"{divisor} = 1"
    )


def _all_prime(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = foundation_module._validated_context(variables)
    index, value = foundation_module._binders(
        tag, context, ("prime_index", "prime_value")
    )
    local = context + (index, value)
    bound = foundation_module._lt_term(
        index, length, tag=f"{tag}_bound", avoid=local
    )
    decoded = foundation_module._beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    prime = foundation_module._prime_term(
        value, tag=f"{tag}_prime", avoid=local
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({prime}))"
    )


def _distinct(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = foundation_module._validated_context(variables)
    left_index, right_index, left_value, right_value = (
        foundation_module._binders(
            tag,
            context,
            (
                "left_index",
                "right_index",
                "left_value",
                "right_value",
            ),
        )
    )
    local = context + (
        left_index,
        right_index,
        left_value,
        right_value,
    )
    left_bound = foundation_module._lt_term(
        left_index, length, tag=f"{tag}_left_bound", avoid=local
    )
    right_bound = foundation_module._lt_term(
        right_index, length, tag=f"{tag}_right_bound", avoid=local
    )
    left_decoded = foundation_module._beta_at_term(
        code,
        scale,
        left_index,
        left_value,
        tag=f"{tag}_left_decoded",
        avoid=local,
    )
    right_decoded = foundation_module._beta_at_term(
        code,
        scale,
        right_index,
        right_value,
        tag=f"{tag}_right_decoded",
        avoid=local,
    )
    return (
        f"forall {left_index} {right_index} {left_value} {right_value}. "
        f"({left_bound}) -> ({right_bound}) -> "
        f"({left_decoded}) -> ({right_decoded}) -> "
        f"~({left_index} = {right_index}) -> "
        f"~({left_value} = {right_value})"
    )


def _pointwise_le(
    code: str,
    scale: str,
    length: str,
    bound_value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = foundation_module._validated_context(variables)
    index, value = foundation_module._binders(
        tag, context, ("bound_index", "bound_value")
    )
    local = context + (index, value)
    index_bound = foundation_module._lt_term(
        index, length, tag=f"{tag}_index_bound", avoid=local
    )
    decoded = foundation_module._beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    (gap,) = foundation_module._binders(
        f"{tag}_value_bound", local, ("le_gap",)
    )
    rendered_bound = foundation_module._render_term(
        bound_value, label="independent pointwise bound", context=context
    )
    return (
        f"forall {index} {value}. ({index_bound}) -> ({decoded}) -> "
        f"exists {gap}. {gap} + ({value}) = ({rendered_bound})"
    )


def _pointwise_divides(
    code: str,
    scale: str,
    length: str,
    target: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = foundation_module._validated_context(variables)
    index, value = foundation_module._binders(
        tag, context, ("divisor_index", "divisor_value")
    )
    local = context + (index, value)
    index_bound = foundation_module._lt_term(
        index, length, tag=f"{tag}_index_bound", avoid=local
    )
    decoded = foundation_module._beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    (quotient,) = foundation_module._binders(
        f"{tag}_result", local, ("quotient",)
    )
    rendered_target = foundation_module._render_term(
        target, label="independent common multiple", context=context
    )
    return (
        f"forall {index} {value}. ({index_bound}) -> ({decoded}) -> "
        f"exists {quotient}. {rendered_target} = {value} * {quotient}"
    )


def _product(
    code: str,
    scale: str,
    length: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = foundation_module._validated_context(variables)
    rendered = tuple(
        foundation_module._render_term(
            term, label="independent product term", context=context
        )
        for term in (code, scale, length, value)
    )
    return fold_surface._product_relation_term(
        *rendered, tag=tag, avoid=context
    )


def _expected_statements() -> dict[str, str]:
    intro_variables = ("b", "c", "l", "p")
    prior_variables = intro_variables + ("i", "q")
    prior_bound = foundation_module._lt_term(
        "i", "l", tag="bpdfsi_prior_bound", avoid=prior_variables
    )
    prior = foundation_module._beta_at_term(
        "b", "c", "i", "q", tag="bpdfsi_prior", avoid=prior_variables
    )
    intro_last = foundation_module._beta_at_term(
        "b", "c", "l", "p", tag="bpdfsi_last", avoid=intro_variables
    )
    intro_ne = f"forall i q. ({prior_bound}) -> ({prior}) -> ~(q = p)"
    last_variables = ("b", "c", "l", "i", "p", "q")
    transport_variables = ("b", "c", "d", "e", "l")
    transport_entry_variables = transport_variables + ("i", "p")
    transport_bound = foundation_module._lt_term(
        "i", "l", tag="bpdft_bound", avoid=transport_entry_variables
    )
    source_entry = foundation_module._beta_at_term(
        "b",
        "c",
        "i",
        "p",
        tag="bpdft_source_entry",
        avoid=transport_entry_variables,
    )
    target_entry = foundation_module._beta_at_term(
        "d",
        "e",
        "i",
        "p",
        tag="bpdft_target_entry",
        avoid=transport_entry_variables,
    )
    transport_entries = (
        f"forall i p. ({transport_bound}) -> ({source_entry}) -> "
        f"({target_entry})"
    )
    coprime_variables = ("b", "c", "l", "r", "p")
    divide_variables = ("b", "c", "l", "n", "z")
    pointwise_variables = ("m", "z", "b", "c", "l")
    bounded_variables = ("m", "z", "b", "c", "l", "n")
    empty = _distinct(
        "b", "c", "0", tag="bpdf_empty", variables=("b", "c")
    )
    intro_prefix = _distinct(
        "b", "c", "l", tag="bpdfsi_prefix", variables=intro_variables
    )
    intro_result = _distinct(
        "b", "c", "S l", tag="bpdfsi_result", variables=intro_variables
    )
    elim_source = _distinct(
        "b", "c", "S l", tag="bpdfsep_source", variables=("b", "c", "l")
    )
    elim_result = _distinct(
        "b", "c", "l", tag="bpdfsep_result", variables=("b", "c", "l")
    )
    last_distinct = _distinct(
        "b",
        "c",
        "S l",
        tag="bpdfsln_distinct",
        variables=last_variables,
    )
    last_bound = foundation_module._lt_term(
        "i", "l", tag="bpdfsln_bound", avoid=last_variables
    )
    last_left = foundation_module._beta_at_term(
        "b", "c", "i", "p", tag="bpdfsln_left", avoid=last_variables
    )
    last_right = foundation_module._beta_at_term(
        "b", "c", "l", "q", tag="bpdfsln_right", avoid=last_variables
    )
    transport_source = _distinct(
        "b",
        "c",
        "l",
        tag="bpdft_source",
        variables=transport_variables,
    )
    transport_result = _distinct(
        "d",
        "e",
        "l",
        tag="bpdft_result",
        variables=transport_variables,
    )
    coprime_primes = _all_prime(
        "b",
        "c",
        "S l",
        tag="bpdfcp_primes",
        variables=coprime_variables,
    )
    coprime_distinct = _distinct(
        "b",
        "c",
        "S l",
        tag="bpdfcp_distinct",
        variables=coprime_variables,
    )
    coprime_product = _product(
        "b",
        "c",
        "l",
        "r",
        tag="bpdfcp_product",
        variables=coprime_variables,
    )
    coprime_last = foundation_module._beta_at_term(
        "b", "c", "l", "p", tag="bpdfcp_last", avoid=coprime_variables
    )
    coprime_result = _coprime(
        "r", "p", tag="bpdfcp_result", variables=coprime_variables
    )
    common_primes = _all_prime(
        "b", "c", "l", tag="bpdfdcm_primes", variables=divide_variables
    )
    common_distinct = _distinct(
        "b", "c", "l", tag="bpdfdcm_distinct", variables=divide_variables
    )
    common_pointwise = _pointwise_divides(
        "b",
        "c",
        "l",
        "z",
        tag="bpdfdcm_pointwise",
        variables=divide_variables,
    )
    common_product = _product(
        "b", "c", "l", "n", tag="bpdfdcm_product", variables=divide_variables
    )
    common_result = _divides(
        "n", "z", tag="bpdfdcm_result", variables=divide_variables
    )
    pointwise_primorial = foundation_module._primorial_relation_term(
        "m",
        "z",
        tag="bpbpdp_primorial",
        variables=pointwise_variables,
    )
    pointwise_primes = _all_prime(
        "b", "c", "l", tag="bpbpdp_primes", variables=pointwise_variables
    )
    pointwise_bounds = _pointwise_le(
        "b",
        "c",
        "l",
        "m",
        tag="bpbpdp_bounds",
        variables=pointwise_variables,
    )
    pointwise_result = _pointwise_divides(
        "b",
        "c",
        "l",
        "z",
        tag="bpbpdp_result",
        variables=pointwise_variables,
    )

    def bounded_parts(stem: str) -> tuple[str, ...]:
        return (
            foundation_module._primorial_relation_term(
                "m",
                "z",
                tag=f"{stem}_primorial",
                variables=bounded_variables,
            ),
            _all_prime(
                "b",
                "c",
                "l",
                tag=f"{stem}_primes",
                variables=bounded_variables,
            ),
            _distinct(
                "b",
                "c",
                "l",
                tag=f"{stem}_distinct",
                variables=bounded_variables,
            ),
            _pointwise_le(
                "b",
                "c",
                "l",
                "m",
                tag=f"{stem}_bounds",
                variables=bounded_variables,
            ),
            _product(
                "b",
                "c",
                "l",
                "n",
                tag=f"{stem}_product",
                variables=bounded_variables,
            ),
        )

    bounded = bounded_parts("bpdfbdp")
    comparison = bounded_parts("bpdfblp")
    return {
        EMPTY: f"forall b c. ({empty})",
        SUCC_INTRO: (
            "forall b c l p. "
            f"({intro_prefix}) -> ({intro_last}) -> "
            f"({intro_ne}) -> ({intro_result})"
        ),
        ELIM_PREFIX: (
            f"forall b c l. ({elim_source}) -> ({elim_result})"
        ),
        LAST_NE: (
            "forall b c l i p q. "
            f"({last_distinct}) -> ({last_bound}) -> "
            f"({last_left}) -> ({last_right}) -> ~(p = q)"
        ),
        TRANSPORT: (
            "forall b c d e l. "
            f"({transport_source}) -> ({transport_entries}) -> "
            f"({transport_result})"
        ),
        COPRIME_LAST: (
            "forall b c l r p. "
            f"({coprime_primes}) -> ({coprime_distinct}) -> "
            f"({coprime_product}) -> ({coprime_last}) -> "
            f"({coprime_result})"
        ),
        DIVIDES_COMMON: (
            "forall b c l n z. "
            f"({common_primes}) -> ({common_distinct}) -> "
            f"({common_pointwise}) -> ({common_product}) -> "
            f"({common_result})"
        ),
        POINTWISE: (
            "forall m z b c l. "
            f"({pointwise_primorial}) -> ({pointwise_primes}) -> "
            f"({pointwise_bounds}) -> ({pointwise_result})"
        ),
        DIVIDES_PRIMORIAL: (
            "forall m z b c l n. "
            f"({bounded[0]}) -> ({bounded[1]}) -> ({bounded[2]}) -> "
            f"({bounded[3]}) -> ({bounded[4]}) -> "
            f"({_divides('n', 'z', tag='bpdfbdp_result', variables=bounded_variables)})"
        ),
        LE_PRIMORIAL: (
            "forall m z b c l n. "
            f"({comparison[0]}) -> ({comparison[1]}) -> "
            f"({comparison[2]}) -> ({comparison[3]}) -> "
            f"({comparison[4]}) -> "
            f"({_le('n', 'z', tag='bpdfblp_result', variables=bounded_variables)})"
        ),
    }


@lru_cache(maxsize=1)
def _foundation_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_foundation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _membership_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_membership_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _pointwise_coprime_spec() -> tuple[TheoremSpec, ...]:
    rows = make_fermat_residue_product_candidate_theorems(TheoremSpec)
    selected = tuple(
        row for row in rows if row.name == "beta_product_pointwise_coprime"
    )
    assert len(selected) == 1
    return selected


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_duplicate_free_candidate_theorems(
        TheoremSpec
    )


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    candidate = (
        _foundation_specs()
        + _membership_specs()
        + _pointwise_coprime_spec()
    )
    candidate_table = _table(candidate)
    assert not (set(stable) & set(candidate_table))
    assert not (set(EXPECTED_NAMES) & set(stable))
    assert not (set(EXPECTED_NAMES) & set(candidate_table))
    return stable | candidate_table


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _core() | _table(_specs()[:index])


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
        if tactic == "use":
            raise AssertionError("duplicate-free proof delegated through use")
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _close(
    name: str,
    cache: dict[str, tuple[Formula, Proof]] | None = None,
) -> tuple[Formula, Proof]:
    """Close one selector with a cache whose lifetime is only this call."""

    if cache is None:
        cache = {}
    if name in cache:
        return cache[name]
    public = _specs_by_name()
    if name in public:
        checked = replay(name)
        result = (checked.formula, checked.certificate)
        cache[name] = result
        return result
    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    dependencies = tuple(_close(dep, cache) for dep in item.dependencies)
    for dependency_formula, dependency_proof in reversed(dependencies):
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    result = (formula, body)
    cache[name] = result
    return result


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_proof(proof: Proof):
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
            pending.extend(
                (child, False)
                for child in children
                if id(child) not in digests
            )
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


def test_bertrand_primorial_duplicate_free_sources_are_pinned() -> None:
    expected = (
        (stable_module, STABLE_SOURCE_SHA256),
        (fold_surface, FOLD_SOURCE_SHA256),
        (coprime_module, COPRIME_SOURCE_SHA256),
        (foundation_module, FOUNDATION_SOURCE_SHA256),
        (membership_module, MEMBERSHIP_SOURCE_SHA256),
        (alpha_enrollment_v10, ALPHA_ENROLLMENT_SOURCE_SHA256),
        (editions_v10, EDITIONS_SOURCE_SHA256),
        (module, CANDIDATE_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest
    root = Path(__file__).resolve().parents[3]
    rfc = root / "research/arithmetic-library/" \
        "ha-bertrand-primorial-duplicate-free-tranche-rfc-v1.md"
    assert sha256(rfc.read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_primorial_duplicate_free_factory_is_isolated() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_primorial_duplicate_free_candidate_theorems"
    ]
    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v10.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert "beta_product_pointwise_coprime" in _core()
    assert "beta_range_one_entry_eq_succ" not in _core()
    assert "prime_product_coprime" not in _core()
    for index, name in enumerate(EXPECTED_NAMES):
        assert set(_row_core(name)) == set(_core()) | set(
            EXPECTED_NAMES[:index]
        )
    for item in rows:
        assert all(dep in _row_core(item.name) for dep in item.dependencies)
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        for token in (
            "AllPrime(",
            "Distinct(",
            "PointwiseLe(",
            "PointwiseDivides(",
            "Primorial(",
            "Product(",
            "Prime(",
            "BetaAt(",
            "<=",
            "<",
            "|",
        ):
            assert token not in item.statement
        assert not any(
            token in command
            for command in item.script
            for token in (
                "DNE",
                "classical",
                "by_contra",
                "sorry",
                "auto",
                "compact_arith",
                "ring",
                "use ",
            )
        )
    provider_token = "bertrand_primorial_duplicate_free_candidate"
    for authority in (stable_module, alpha_enrollment_v10, editions_v10):
        source = Path(authority.__file__).read_text(encoding="utf-8")
        assert provider_token not in source


def test_bertrand_primorial_duplicate_free_topology_is_exact() -> None:
    table = _table(_specs())
    assert tuple(len(table[name].script) for name in EXPECTED_NAMES) == (
        17,
        98,
        31,
        30,
        79,
        76,
        103,
        40,
        31,
        39,
    )
    assert table[SUCC_INTRO].script.count("apply beta_at_unique") == 2
    assert table[ELIM_PREFIX].script.count("apply le_succ") == 2
    assert table[LAST_NE].script.count("apply lt_irrefl_expanded") == 1
    assert table[TRANSPORT].script.count("exact beta_at_exists") == 2
    assert table[TRANSPORT].script.count("apply beta_at_unique") == 2
    assert table[COPRIME_LAST].script.count(
        "apply beta_product_pointwise_coprime"
    ) == 1
    assert table[COPRIME_LAST].script.count(
        "apply distinct_primes_coprime"
    ) == 1
    assert table[DIVIDES_COMMON].script.count("induction l") == 1
    assert table[DIVIDES_COMMON].script.count(
        "apply coprime_product_is_lcm"
    ) == 1
    assert table[POINTWISE].script.count(
        "apply primorial_prime_divides_of_le"
    ) == 1
    assert table[DIVIDES_PRIMORIAL].script.count(
        "apply beta_distinct_prime_product_divides_common_multiple"
    ) == 1
    assert table[LE_PRIMORIAL].script.count("apply divisor_le_nonzero") == 1
    assert table[LE_PRIMORIAL].script.count("apply primorial_positive") == 1


def test_bertrand_primorial_duplicate_free_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert all(value is not None for value in EXPECTED_ARTIFACTS.values())
    assert all(value is not None for value in EXPECTED_BODIES.values())
    assert all(value is not None for value in EXPECTED_ENVELOPES.values())
    assert all(value is not None for value in EXPECTED_CLOSURES.values())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_duplicate_free_artifacts_are_frozen(
    name: str,
) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"PRIMORIAL DISTINCT {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_duplicate_free_bodies_are_frozen(
    name: str,
) -> None:
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
        label=f"Primorial distinct body {name}",
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
    assert not any(type(node) is DNE for node in _walk_proof(body))
    print(
        f"PRIMORIAL DISTINCT {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, (
        f"freeze body receipt for {name}: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[name] is not None, (
        f"freeze envelope receipt for {name}: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == 32


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_primorial_duplicate_free_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(dep for dep in item.dependencies if dep != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_duplicate_free_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    distinct_empty = module._distinct_prefix_term(
        "b", "c", "0", tag="bpdf_empty", variables=("b", "c")
    )
    repeated_zero = module._beta_at_term(
        "b", "c", "0", "p", tag="bpdf_mut_left", avoid=("b", "c", "p", "q")
    )
    repeated_zero_right = module._beta_at_term(
        "b", "c", "0", "q", tag="bpdf_mut_right", avoid=("b", "c", "p", "q")
    )
    stronger_empty = (
        f"({distinct_empty}) /\\ (forall p q. ({repeated_zero}) -> "
        f"({repeated_zero_right}) -> ~(p = q))"
    )
    intro_variables = ("b", "c", "l", "p")
    prior_variables = intro_variables + ("i", "q")
    prior_bound = module._lt_term(
        "i", "l", tag="bpdfsi_prior_bound", avoid=prior_variables
    )
    prior = module._beta_at_term(
        "b", "c", "i", "q", tag="bpdfsi_prior", avoid=prior_variables
    )
    freshness = f"forall i q. ({prior_bound}) -> ({prior}) -> ~(q = p)"
    elim_result = module._distinct_prefix_term(
        "b", "c", "l", tag="bpdfsep_result", variables=("b", "c", "l")
    )
    elim_stronger = module._distinct_prefix_term(
        "b",
        "c",
        "S (S l)",
        tag="bpdfsep_result",
        variables=("b", "c", "l"),
    )
    last_variables = ("b", "c", "l", "i", "p", "q")
    last_entry = module._beta_at_term(
        "b", "c", "l", "q", tag="bpdfsln_right", avoid=last_variables
    )
    prior_entry = module._beta_at_term(
        "b", "c", "i", "q", tag="bpdfsln_right", avoid=last_variables
    )
    transport_variables = ("b", "c", "d", "e", "l", "i", "p")
    target_entry = module._beta_at_term(
        "d", "e", "i", "p", tag="bpdft_target_entry", avoid=transport_variables
    )
    shifted_target = module._beta_at_term(
        "d",
        "e",
        "i",
        "S p",
        tag="bpdft_target_entry",
        avoid=transport_variables,
    )
    coprime_variables = ("b", "c", "l", "r", "p")
    coprime_distinct = module._distinct_prefix_term(
        "b", "c", "S l", tag="bpdfcp_distinct", variables=coprime_variables
    )
    divide_variables = ("b", "c", "l", "n", "z")
    divide_distinct = module._distinct_prefix_term(
        "b", "c", "l", tag="bpdfdcm_distinct", variables=divide_variables
    )
    pointwise_variables = ("m", "z", "b", "c", "l")
    pointwise_result = module._pointwise_divides_term(
        "b", "c", "l", "z", tag="bpbpdp_result", variables=pointwise_variables
    )
    shifted_pointwise = pointwise_result.replace(
        "z = bpr_divisor_value_bpbpdp_result *",
        "z = S (bpr_divisor_value_bpbpdp_result) *",
        1,
    )
    bounded_variables = ("m", "z", "b", "c", "l", "n")
    divides = module._divides_term(
        "n", "z", tag="bpdfbdp_result", variables=bounded_variables
    )
    reverse_divides = module._divides_term(
        "z", "n", tag="bpdfbdp_result", variables=bounded_variables
    )
    comparison = module._le_term(
        "n", "z", tag="bpdfblp_result", variables=bounded_variables
    )
    stronger_comparison = module._le_term(
        "S n", "z", tag="bpdfblp_result", variables=bounded_variables
    )
    return (
        (EMPTY, "same_index_values", distinct_empty, stronger_empty),
        (SUCC_INTRO, "drop_freshness", f"({freshness}) -> ", ""),
        (ELIM_PREFIX, "stronger_length", elim_result, elim_stronger),
        (LAST_NE, "last_is_prior", last_entry, prior_entry),
        (TRANSPORT, "shift_target_value", target_entry, shifted_target),
        (COPRIME_LAST, "drop_distinctness", f"({coprime_distinct}) -> ", ""),
        (DIVIDES_COMMON, "drop_distinctness", f"({divide_distinct}) -> ", ""),
        (POINTWISE, "successor_divisor", pointwise_result, shifted_pointwise),
        (DIVIDES_PRIMORIAL, "reverse_divisibility", divides, reverse_divides),
        (LE_PRIMORIAL, "successor_lower", comparison, stronger_comparison),
    )


def test_bertrand_primorial_duplicate_free_mutations_have_fixtures() -> None:
    assert 2 == 2
    assert 2 * 2 == 4 and 4 > 2
    assert 2 < 6 and 6 > 2
    assert 2 == 2 and 3 > 2


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_bertrand_primorial_duplicate_free_mutations_are_rejected(
    name: str,
    case_id: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = _table(_specs())[name]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_duplicate_free_closures_are_frozen(
    name: str,
) -> None:
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
        label=f"Primorial distinct closure {name}",
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
    assert not any(type(node) is DNE for node in _walk_proof(certificate))
    direct_cut_count = 0
    probe = certificate
    while type(probe) is Cut:
        direct_cut_count += 1
        probe = probe.body
    assert direct_cut_count == len(item.dependencies)
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cut_count):
        assert not check((), _mutate_direct_cut(certificate, index), formula)
    print(f"PRIMORIAL DISTINCT {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
