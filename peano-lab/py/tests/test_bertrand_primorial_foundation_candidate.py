"""Fail-closed audit for the dense-mask Bertrand primorial foundation.

The ten candidate statements are rebuilt independently from the stable
BetaAt/Product surface.  Stable and the earlier local prefix are the only
body authorities; receipts are evidence and never theorem authority.
"""

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
from peano_lab.kernel import terms as terms_module
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero, parse_term_in_context, pretty_term
from peano_lab.library import (
    alpha_enrollment_v8,
    bertrand_choose_foundation_candidate as choose_module,
    bertrand_primorial_foundation_candidate as module,
    editions_v8,
    finite_fold_surface as fold_surface,
    theorems as stable_module,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    make_bertrand_primorial_foundation_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
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


CHOICE_EXISTS = "primorial_factor_choice_exists"
CHOICE_FUNCTIONAL = "primorial_factor_choice_functional"
PREFIX_EXTEND = "primorial_factor_prefix_extend"
PREFIX_EXISTS = "primorial_factor_prefix_exists"
PREFIX_TRANSPORT = "primorial_factor_prefix_transport_entry"
PRIMORIAL_EXISTS = "primorial_exists"
PRIMORIAL_FUNCTIONAL = "primorial_functional"
PRIMORIAL_ZERO = "primorial_zero"
PRIMORIAL_SUCC = "primorial_succ_decompose"
PRIMORIAL_POSITIVE = "primorial_positive"

EXPECTED_NAMES = (
    CHOICE_EXISTS,
    CHOICE_FUNCTIONAL,
    PREFIX_EXTEND,
    PREFIX_EXISTS,
    PREFIX_TRANSPORT,
    PRIMORIAL_EXISTS,
    PRIMORIAL_FUNCTIONAL,
    PRIMORIAL_ZERO,
    PRIMORIAL_SUCC,
    PRIMORIAL_POSITIVE,
)
EXPECTED_DEPENDENCIES = {
    CHOICE_EXISTS: ("prime_decidable",),
    CHOICE_FUNCTIONAL: (),
    PREFIX_EXTEND: (
        CHOICE_EXISTS,
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    PREFIX_EXISTS: (
        "add_eq_zero_right",
        "succ_ne_zero",
        PREFIX_EXTEND,
    ),
    PREFIX_TRANSPORT: ("beta_at_unique", CHOICE_FUNCTIONAL),
    PRIMORIAL_EXISTS: ("beta_product_exists", PREFIX_EXISTS),
    PRIMORIAL_FUNCTIONAL: (
        "beta_product_transport_prefix",
        "beta_product_functional",
        PREFIX_TRANSPORT,
    ),
    PRIMORIAL_ZERO: ("beta_product_zero",),
    PRIMORIAL_SUCC: (
        "beta_product_succ_decompose",
        "beta_at_unique",
        "le_refl",
        "le_succ",
    ),
    PRIMORIAL_POSITIVE: (
        "mul_succ_left",
        PRIMORIAL_ZERO,
        PRIMORIAL_SUCC,
    ),
}
EXPECTED_DIRECT_CUTS = {
    name: count
    for name, count in zip(
        EXPECTED_NAMES,
        (1, 0, 3, 3, 2, 2, 3, 1, 4, 3),
        strict=True,
    )
}
assert sum(map(len, EXPECTED_DEPENDENCIES.values())) == 22

STABLE_SOURCE_SHA256 = (
    "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919"
)
FOLD_SOURCE_SHA256 = (
    "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30"
)
CHOOSE_HELPER_SOURCE_SHA256 = (
    "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
)
TERMS_SOURCE_SHA256 = (
    "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185"
)
ALPHA_ENROLLMENT_SOURCE_SHA256 = (
    "129f75d0d969665025e82df0427e66383902c9275e0e880a3d9495b11dc5b33f"
)
EDITIONS_SOURCE_SHA256 = (
    "47d5622d6c185d92d9acc10a9e65f3d823a0e6d86a79b5b7760b0295d9d63e5a"
)
PRIMORIAL_SOURCE_SHA256 = (
    "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98"
)
RFC_SHA256 = (
    "c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89"
)

# All execution receipts fail closed until isolated selectors reproduce them.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOICE_EXISTS: (
        487,
        "c02e015e6be53fa0fe884fd84f34a6d8b51371325ce15e6356e197d6dac03bfa",
        "cc66d79dd4f85c15bb942468fc2f96a936fb6107767e63cc6452a0a12e4177d7",
        "f887ecfb41cb351e39fed263dd72756b8a2e49b56b01480a5dae67c4ec5d392f",
    ),
    CHOICE_FUNCTIONAL: (
        949,
        "f816f55546f2895a64ac893159374aa5ab239b28c8bc375d4f8e382a21df243f",
        "2d44c33edc3bc95d26dea573e13db5b85d0b23824e4a4878c7c0403ee6ec7c1d",
        "f816f55546f2895a64ac893159374aa5ab239b28c8bc375d4f8e382a21df243f",
    ),
    PREFIX_EXTEND: (
        2348,
        "8ee43fa046353026725d72c8f0752fd25ec4773d53095a725b12ff698cde5e35",
        "9ef72fcf52e307817211df10dd1523d20933a8dd786f64155546c89606b68b94",
        "94f29f39d20d2bbb8d84262827295fe05b1ac7ea41e2bb2b82b6fb64f8c2f2c3",
    ),
    PREFIX_EXISTS: (
        1196,
        "c835841f1e3998ccaa92dafe2c09c4a4254c0ff37adc74e3f03e30678ead8322",
        "a770cf47339fcd71576962b8a45d224ecc9a1af866d42621cabd4f59b6ac1ca7",
        "e0ae16e9e954c75689702d8fe90366dd1a8040d99c547a597eb8c40b231853cd",
    ),
    PREFIX_TRANSPORT: (
        2715,
        "1d08f9d66ec6440cf95acf08843ce9f5e0b3371d79007b001a6d871c316e518f",
        "7ed56c733e24d6b3c84b10366ea076ca3be0d4f3bd55933742a01834f98aaccb",
        "797f391beca668a53daac2392fb55f71b83976b99da6e8cf4dc5255d5b41077a",
    ),
    PRIMORIAL_EXISTS: (
        3307,
        "0eab9db8f2c4006d3caae4427458f18b56964ab68b1b8c041b9d107141519963",
        "62191f10cf597c1df0e29bf20a93050decb589096eb87240563fb1669ef90963",
        "81c510eb059dce3ad1267eb927258fe1b5b062422eda1e80366dac22dc1ebc15",
    ),
    PRIMORIAL_FUNCTIONAL: (
        8425,
        "ab40ee85c439348063c8336817ef9d987d6ba5cb9ded5f1b0d1da22b88da8ea8",
        "03a6f9e24d9d928e08a2e355b22af845e5751b8848db269d80614b0b458cdcbd",
        "3c83270a6f3c7bdf50d8acada9a547d8c16b3521d1f9c8329393e223828b8c72",
    ),
    PRIMORIAL_ZERO: (
        3786,
        "afda0460d1652b883b6b4e4c57d9f42fd81f2a4bc9d35135f84b8635da236414",
        "2449b4b6b72fa6b2236ee1d5faccc545dd5d4fd6b98e99e431db833258bf27dd",
        "61fd343411a023a78bf81d4570a5c89ec0c374889c2032a7fca1642dad6fd6a5",
    ),
    PRIMORIAL_SUCC: (
        8574,
        "fbd87b2f990453d0b213b63128f0d50e40056e8bc025c934af393355a434ed86",
        "30c1ef40f09eacd6674628d5d8d8897076679078ae5ea0cc8b656455b01881ea",
        "ed2fec9f895a25a0a8e54a00103b30cc98fab200d323cb3c024be8d7203c48e7",
    ),
    PRIMORIAL_POSITIVE: (
        4184,
        "b011acbb280e8b3da4cf55e81f165b8dc3b78d101952a1ec410b94ab87096662",
        "098dccf3a65358a9346adc8aca2cf3c4037fb1e92a756dc2e8f2fce31db37def",
        "441a23a52c6c4c4fbd5ac91911a922cb43699509af7b0730a36dac474b20ca05",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CHOICE_EXISTS: (1, 13, 18, 9, 18, 17, 0),
    CHOICE_FUNCTIONAL: (0, 28, 75, 18, 75, 74, 0),
    PREFIX_EXTEND: (3, 42, 72, 26, 72, 71, 0),
    PREFIX_EXISTS: (3, 20, 31, 15, 31, 30, 0),
    PREFIX_TRANSPORT: (2, 36, 73, 27, 73, 72, 0),
    PRIMORIAL_EXISTS: (2, 14, 19, 11, 19, 18, 0),
    PRIMORIAL_FUNCTIONAL: (3, 31, 61, 28, 61, 60, 0),
    PRIMORIAL_ZERO: (1, 7, 21, 14, 21, 20, 0),
    PRIMORIAL_SUCC: (4, 40, 71, 27, 71, 70, 0),
    PRIMORIAL_POSITIVE: (3, 42, 73, 20, 73, 72, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOICE_EXISTS: (18, 18, 9, 10, 11),
    CHOICE_FUNCTIONAL: (75, 75, 18, 0, 18),
    PREFIX_EXTEND: (72, 72, 26, 651, 35),
    PREFIX_EXISTS: (31, 31, 15, 111, 21),
    PREFIX_TRANSPORT: (73, 73, 27, 66, 27),
    PRIMORIAL_EXISTS: (19, 19, 11, 7, 11),
    PRIMORIAL_FUNCTIONAL: (61, 61, 28, 20, 28),
    PRIMORIAL_ZERO: (21, 21, 14, 3, 14),
    PRIMORIAL_SUCC: (71, 71, 27, 30, 27),
    PRIMORIAL_POSITIVE: (73, 73, 20, 339, 31),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CHOICE_EXISTS: (
        2212,
        74,
        1489,
        1551,
        63,
        5739,
        74,
        "19a8aee9e143853aedf140fe44f3937232ed558ad6365beb62708b19ee7c9cde",
    ),
    CHOICE_FUNCTIONAL: (
        75,
        18,
        75,
        74,
        0,
        0,
        18,
        "50241282eb81b56fce304af27de6c43f28cf711dfd1d2ad1e512ee225d5ae537",
    ),
    PREFIX_EXTEND: (
        31469,
        82,
        5198,
        5448,
        251,
        101206,
        82,
        "94b38ae5afa80925e4f4ecef4a62fb5cb31affbb1ce360fd7591ca8dc2a7e154",
    ),
    PREFIX_EXISTS: (
        31520,
        85,
        5229,
        5481,
        253,
        101869,
        85,
        "b2088b8766ebc5dba48e4163e3a09dd4e38af2dd62e2906e9b03571e2b8f9273",
    ),
    PREFIX_TRANSPORT: (
        1269,
        60,
        840,
        876,
        37,
        3587,
        60,
        "247390da81417322540f7f3d76b8a28958db10d509edadcf3e61b7407b85e3ab",
    ),
    PRIMORIAL_EXISTS: (
        62026,
        87,
        5484,
        5748,
        265,
        201875,
        87,
        "07912ea10236674cbad847636cb7dae666af47aa8e1f96c299058f7eb69c376c",
    ),
    PRIMORIAL_FUNCTIONAL: (
        2771,
        63,
        1177,
        1216,
        40,
        10684,
        63,
        "f234fa34de0e6de4bff4a1a1e9bac2c65152dd4ccaa3368b9de7ae53e83664e7",
    ),
    PRIMORIAL_ZERO: (
        1192,
        61,
        763,
        799,
        37,
        3429,
        61,
        "f7bfb839d144393f535296513c44ec3d8d2044d3973abba82fde84472f5c58f6",
    ),
    PRIMORIAL_SUCC: (
        2514,
        63,
        855,
        896,
        42,
        9737,
        63,
        "a2a55ecfdaadc4a28ae9c11a1be2f26a1e208d2300cb0c56a2b53733305afdc9",
    ),
    PRIMORIAL_POSITIVE: (
        3951,
        66,
        999,
        1042,
        44,
        15578,
        66,
        "18e67c0bee49a28ce31a546442f012c02cc7cb07fd3a9c9c307d254fe0430bd3",
    ),
}


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(ch.isalnum() or ch in "_'" for ch in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _context(variables: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(variables, tuple):
        raise ValueError("variables must be a tuple")
    checked = tuple(_identifier(item, "context variable") for item in variables)
    if len(set(checked)) != len(checked):
        raise ValueError("context variables must be distinct")
    return checked


def _render(source: str, context: tuple[str, ...]) -> str:
    return pretty_term(
        parse_term_in_context(source, list(context)),
        list(context),
    ).replace("·", "*")


def _binders(
    tag: str,
    avoid: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"bpr_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated binder captures an argument")
    return names


def _lt(left: str, right: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    (gap,) = _binders(tag, avoid, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _at(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, avoid, ("height", "quotient"))
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value}))"
    )


def _prime(value: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    left, right = _binders(tag, avoid, ("left", "right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def _choice_rendered(
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    selected = f"S ({index})"
    prime = _prime(selected, tag=f"{tag}_prime", avoid=avoid)
    return (
        f"((({prime}) /\\ {value} = {selected}) \\/ "
        f"(~({prime}) /\\ {value} = 1))"
    )


def _choice(
    index: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    return _choice_rendered(
        _render(index, context),
        _render(value, context),
        tag=tag,
        avoid=context,
    )


def _prefix_rendered(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("index", "value"))
    local = avoid + (index, value)
    bound = _lt(index, length, tag=f"{tag}_bound", avoid=local)
    decoded = _at(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    choice = _choice_rendered(
        index,
        value,
        tag=f"{tag}_choice",
        avoid=local,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _prefix(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    return _prefix_rendered(
        _render(code, context),
        _render(scale, context),
        _render(length, context),
        tag=tag,
        avoid=context,
    )


def _primorial(
    index: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_index = _render(index, context)
    rendered_value = _render(value, context)
    code, scale = _binders(tag, context, ("code", "scale"))
    local = context + (code, scale)
    prefix = _prefix_rendered(
        code,
        scale,
        rendered_index,
        tag=f"{tag}_mask",
        avoid=local,
    )
    product = fold_surface._product_relation_term(
        code,
        scale,
        rendered_index,
        rendered_value,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def _surface_parts() -> dict[str, str]:
    transport_variables = ("b", "c", "d", "e", "m", "i", "a")
    predecessor_variables = ("m", "z", "p", "r")
    return {
        "choice_exists": _choice(
            "i", "a", tag="bpfc_exists", variables=("i", "a")
        ),
        "choice_functional_left": _choice(
            "i", "a", tag="bpfcf_left", variables=("i", "a", "z")
        ),
        "choice_functional_right": _choice(
            "i", "z", tag="bpfcf_right", variables=("i", "a", "z")
        ),
        "extend_before": _prefix(
            "b", "c", "m", tag="bpfpe_before", variables=("b", "c", "m")
        ),
        "extend_after": _prefix(
            "d",
            "e",
            "S m",
            tag="bpfpe_after",
            variables=("b", "c", "m", "d", "e"),
        ),
        "prefix_exists": _prefix(
            "b", "c", "m", tag="bpfpx_result", variables=("m", "b", "c")
        ),
        "transport_left": _prefix(
            "b", "c", "m", tag="bpfpt_left", variables=transport_variables
        ),
        "transport_right": _prefix(
            "d", "e", "m", tag="bpfpt_right", variables=transport_variables
        ),
        "transport_bound": _lt(
            "i", "m", tag="bpfpt_bound", avoid=transport_variables
        ),
        "transport_source": _at(
            "b",
            "c",
            "i",
            "a",
            tag="bpfpt_source",
            avoid=transport_variables,
        ),
        "transport_target": _at(
            "d",
            "e",
            "i",
            "a",
            tag="bpfpt_target",
            avoid=transport_variables,
        ),
        "exists": _primorial(
            "m", "z", tag="bp_exists", variables=("m", "z")
        ),
        "functional_left": _primorial(
            "m", "x", tag="bp_functional_left", variables=("m", "x", "y")
        ),
        "functional_right": _primorial(
            "m", "y", tag="bp_functional_right", variables=("m", "x", "y")
        ),
        "zero": _primorial("0", "z", tag="bp_zero_source", variables=("z",)),
        "successor": _primorial(
            "S m", "z", tag="bp_succ_source", variables=("m", "z")
        ),
        "predecessor": _primorial(
            "m", "r", tag="bp_succ_predecessor", variables=predecessor_variables
        ),
        "successor_choice": _choice(
            "m", "p", tag="bp_succ_factor", variables=predecessor_variables
        ),
        "positive": _primorial(
            "m", "z", tag="bp_positive_source", variables=("m", "z")
        ),
    }


def _expected_statements() -> dict[str, str]:
    part = _surface_parts()
    return {
        CHOICE_EXISTS: f"forall i. exists a. ({part['choice_exists']})",
        CHOICE_FUNCTIONAL: (
            "forall i a z. "
            f"({part['choice_functional_left']}) -> "
            f"({part['choice_functional_right']}) -> a = z"
        ),
        PREFIX_EXTEND: (
            "forall b c m. "
            f"({part['extend_before']}) -> "
            f"exists d e. ({part['extend_after']})"
        ),
        PREFIX_EXISTS: (
            f"forall m. exists b c. ({part['prefix_exists']})"
        ),
        PREFIX_TRANSPORT: (
            "forall b c d e m. "
            f"({part['transport_left']}) -> ({part['transport_right']}) -> "
            f"forall i a. ({part['transport_bound']}) -> "
            f"({part['transport_source']}) -> ({part['transport_target']})"
        ),
        PRIMORIAL_EXISTS: f"forall m. exists z. ({part['exists']})",
        PRIMORIAL_FUNCTIONAL: (
            "forall m x y. "
            f"({part['functional_left']}) -> "
            f"({part['functional_right']}) -> x = y"
        ),
        PRIMORIAL_ZERO: f"forall z. ({part['zero']}) -> z = 1",
        PRIMORIAL_SUCC: (
            f"forall m z. ({part['successor']}) -> (exists p r. "
            f"({part['successor_choice']}) /\\ "
            f"(({part['predecessor']}) /\\ z = r * p))"
        ),
        PRIMORIAL_POSITIVE: (
            f"forall m z. ({part['positive']}) -> exists r. z = S r"
        ),
    }


def _script_parts() -> dict[str, str]:
    extend_avoid = ("b", "c", "m", "x", "d", "e", "i", "a")
    extend_append = _at(
        "d", "e", "m", "x", tag="bpfpe_append", avoid=extend_avoid
    )
    extend_old_bound = _lt(
        "i", "m", tag="bpfpe_old_bound", avoid=extend_avoid
    )
    extend_old = _at(
        "b", "c", "i", "a", tag="bpfpe_old", avoid=extend_avoid
    )
    extend_new = _at(
        "d", "e", "i", "a", tag="bpfpe_new", avoid=extend_avoid
    )
    extend_relation = (
        f"exists d e. (({extend_append}) /\\ forall i a. "
        f"({extend_old_bound}) -> ({extend_old}) -> ({extend_new}))"
    )
    hold_variables = ("b", "c", "m", "x", "x1", "x2", "i", "a")
    hold_decoded = _at(
        "b",
        "c",
        "i",
        "a",
        tag="bpfpe_hold_decoded",
        avoid=hold_variables,
    )
    hold_choice = _choice(
        "i",
        "a",
        tag="bpfpe_hold_choice",
        variables=hold_variables,
    )

    transport_variables = ("b", "c", "d", "e", "m", "i", "a")
    left_entry_decoded = _at(
        "b",
        "c",
        "i",
        "p",
        tag="bpfpt_left_entry",
        avoid=transport_variables + ("p",),
    )
    left_entry_choice = _choice(
        "i",
        "p",
        tag="bpfpt_left_choice",
        variables=transport_variables + ("p",),
    )
    right_entry_decoded = _at(
        "d",
        "e",
        "i",
        "q",
        tag="bpfpt_right_entry",
        avoid=transport_variables + ("q",),
    )
    right_entry_choice = _choice(
        "i",
        "q",
        tag="bpfpt_right_choice",
        variables=transport_variables + ("q",),
    )

    functional_variables = (
        "m",
        "x",
        "y",
        "x1",
        "x2",
        "x3",
        "x4",
        "i",
        "a",
    )
    functional_bound = _lt(
        "i", "m", tag="bp_functional_bound", avoid=functional_variables
    )
    functional_source = _at(
        "x1",
        "x2",
        "i",
        "a",
        tag="bp_functional_source_entry",
        avoid=functional_variables,
    )
    functional_target = _at(
        "x3",
        "x4",
        "i",
        "a",
        tag="bp_functional_target_entry",
        avoid=functional_variables,
    )
    functional_transport = fold_surface._product_relation_term(
        "x3",
        "x4",
        "m",
        "x",
        tag="bp_functional_transport",
        avoid=("m", "x", "y", "x1", "x2", "x3", "x4"),
    )

    successor_last = _at(
        "x",
        "x1",
        "m",
        "p",
        tag="bp_succ_last_factor",
        avoid=("m", "z", "x", "x1", "p", "r"),
    )
    successor_prefix_product = fold_surface._product_relation_term(
        "x",
        "x1",
        "m",
        "r",
        tag="bp_succ_prefix_product",
        avoid=("m", "z", "x", "x1", "p", "r"),
    )
    terminal_variables = ("m", "z", "x", "x1", "x2", "x3", "a")
    successor_terminal = _at(
        "x",
        "x1",
        "m",
        "a",
        tag="bp_succ_mask_terminal",
        avoid=terminal_variables,
    )
    successor_terminal_choice = _choice(
        "m",
        "a",
        tag="bp_succ_mask_choice",
        variables=terminal_variables,
    )
    surface = _surface_parts()
    successor_result = (
        f"exists p r. ({surface['successor_choice']}) /\\ "
        f"(({surface['predecessor']}) /\\ z = r * p)"
    )
    return {
        "extend_choice": _choice(
            "m",
            "x",
            tag="bpfpe_last_choice",
            variables=("b", "c", "m", "x"),
        ),
        "extend_relation": extend_relation,
        "extend_hold": (
            f"exists a. (({hold_decoded}) /\\ ({hold_choice}))"
        ),
        "prefix_previous": _prefix(
            "b",
            "c",
            "m",
            tag="bpfpx_previous",
            variables=("m", "b", "c"),
        ),
        "prefix_successor": _prefix(
            "b",
            "c",
            "S m",
            tag="bpfpx_successor",
            variables=("m", "b", "c"),
        ),
        "left_entry": (
            f"exists p. (({left_entry_decoded}) /\\ "
            f"({left_entry_choice}))"
        ),
        "right_entry": (
            f"exists q. (({right_entry_decoded}) /\\ "
            f"({right_entry_choice}))"
        ),
        "exists_product": fold_surface._product_relation_term(
            "x",
            "x1",
            "m",
            "z",
            tag="bp_exists_product_witness",
            avoid=("m", "x", "x1", "z"),
        ),
        "functional_preservation": (
            f"forall i a. ({functional_bound}) -> "
            f"({functional_source}) -> ({functional_target})"
        ),
        "functional_transport": functional_transport,
        "successor_decomposition": (
            f"exists p r. ({successor_last}) /\\ "
            f"(({successor_prefix_product}) /\\ z = r * p)"
        ),
        "successor_terminal": (
            f"exists a. (({successor_terminal}) /\\ "
            f"({successor_terminal_choice}))"
        ),
        "successor_result": successor_result,
    }


def _expected_scripts() -> dict[str, tuple[str, ...]]:
    part = _surface_parts()
    local = _script_parts()
    return {
        CHOICE_EXISTS: (
            "intro i",
            "specialize prime_decidable (S i)",
            "cases prime_decidable",
            "exists S i",
            "left",
            "split",
            "exact prime_decidable_left",
            "refl",
            "exists 1",
            "right",
            "split",
            "exact prime_decidable_right",
            "refl",
        ),
        CHOICE_FUNCTIONAL: (
            "intro i",
            "intro a",
            "intro z",
            "intro hleft",
            "intro hright",
            "cases hleft",
            "cases hleft_left",
            "cases hright",
            "cases hright_left",
            "trans S i",
            "exact hleft_left_right",
            "symm",
            "exact hright_left_right",
            "cases hright_right",
            "exfalso",
            "apply hright_right_left",
            "exact hleft_left_left",
            "cases hleft_right",
            "cases hright",
            "cases hright_left",
            "exfalso",
            "apply hleft_right_left",
            "exact hright_left_left",
            "cases hright_right",
            "trans 1",
            "exact hleft_right_right",
            "symm",
            "exact hright_right_right",
        ),
        PREFIX_EXTEND: (
            "intro b",
            "intro c",
            "intro m",
            "intro hprefix",
            f"have hchoice : exists x. ({local['extend_choice']})",
            "apply primorial_factor_choice_exists",
            "cases hchoice",
            f"have hext : {local['extend_relation']}",
            "apply beta_prefix_extend",
            "cases hext",
            "cases hext_witness",
            "cases hext_witness_witness",
            "exists x1",
            "exists x2",
            "intro i",
            "intro hi",
            r"have hsplit : i = m \/ exists gap. gap + S i = m",
            "apply finite_lt_succ_eq_or_lt",
            "exact hi",
            "cases hsplit",
            *("rewrite hsplit_left",) * 7,
            "exists x",
            "split",
            "exact hext_witness_witness_left",
            "exact hchoice_witness",
            f"have hold : {local['extend_hold']}",
            "apply hprefix",
            "exact hsplit_right",
            "cases hold",
            "cases hold_witness",
            "exists x3",
            "split",
            "apply hext_witness_witness_right",
            "exact hsplit_right",
            "exact hold_witness_left",
            "exact hold_witness_right",
        ),
        PREFIX_EXISTS: (
            "induction m",
            "exists 0",
            "exists 0",
            "intro i",
            "intro hi",
            "exfalso",
            "cases hi",
            "have hsi : S i = 0",
            "apply add_eq_zero_right",
            "exact hi_witness",
            "apply succ_ne_zero",
            "exact hsi",
            f"have hprevious : exists b c. ({local['prefix_previous']})",
            "exact IH",
            "cases hprevious",
            "cases hprevious_witness",
            f"have hnext : exists b c. ({local['prefix_successor']})",
            "apply primorial_factor_prefix_extend",
            "exact hprevious_witness_witness",
            "exact hnext",
        ),
        PREFIX_TRANSPORT: (
            "intro b",
            "intro c",
            "intro d",
            "intro e",
            "intro m",
            "intro hleft",
            "intro hright",
            "intro i",
            "intro a",
            "intro hi",
            "intro ha",
            f"have hleft_entry : {local['left_entry']}",
            "apply hleft",
            "exact hi",
            "cases hleft_entry",
            "cases hleft_entry_witness",
            f"have hright_entry : {local['right_entry']}",
            "apply hright",
            "exact hi",
            "cases hright_entry",
            "cases hright_entry_witness",
            "have hap : a = x",
            "apply beta_at_unique",
            "exact ha",
            "exact hleft_entry_witness_left",
            "have hpq : x = x1",
            "apply primorial_factor_choice_functional",
            "exact hleft_entry_witness_right",
            "exact hright_entry_witness_right",
            "have haq : a = x1",
            "trans x",
            "exact hap",
            "exact hpq",
            "rewrite haq",
            "rewrite haq",
            "exact hright_entry_witness_left",
        ),
        PRIMORIAL_EXISTS: (
            "intro m",
            f"have hprefix : exists b c. ({part['prefix_exists']})",
            "apply primorial_factor_prefix_exists",
            "cases hprefix",
            "cases hprefix_witness",
            f"have hproduct : exists z. ({local['exists_product']})",
            "apply beta_product_exists",
            "cases hproduct",
            "exists x2",
            "exists x",
            "exists x1",
            "split",
            "exact hprefix_witness_witness",
            "exact hproduct_witness",
        ),
        PRIMORIAL_FUNCTIONAL: (
            "intro m",
            "intro x",
            "intro y",
            "intro hleft",
            "intro hright",
            "cases hleft",
            "cases hleft_witness",
            "cases hleft_witness_witness",
            "cases hright",
            "cases hright_witness",
            "cases hright_witness_witness",
            f"have hpres : {local['functional_preservation']}",
            "specialize primorial_factor_prefix_transport_entry x1",
            "specialize primorial_factor_prefix_transport_entry x2",
            "specialize primorial_factor_prefix_transport_entry x3",
            "specialize primorial_factor_prefix_transport_entry x4",
            "specialize primorial_factor_prefix_transport_entry m",
            "apply primorial_factor_prefix_transport_entry",
            "exact hleft_witness_witness_left",
            "exact hright_witness_witness_left",
            f"have htransport : {local['functional_transport']}",
            "apply beta_product_transport_prefix",
            "exact hleft_witness_witness_right",
            "exact hpres",
            "cases htransport",
            "cases htransport_witness",
            "cases hright_witness_witness_right",
            "cases hright_witness_witness_right_witness",
            "apply beta_product_functional",
            "exact htransport_witness_witness",
            "exact hright_witness_witness_right_witness_witness",
        ),
        PRIMORIAL_ZERO: (
            "intro z",
            "intro hprimorial",
            "cases hprimorial",
            "cases hprimorial_witness",
            "cases hprimorial_witness_witness",
            "apply beta_product_zero",
            "exact hprimorial_witness_witness_right",
        ),
        PRIMORIAL_SUCC: (
            "intro m",
            "intro z",
            "intro hprimorial",
            "cases hprimorial",
            "cases hprimorial_witness",
            "cases hprimorial_witness_witness",
            f"have hdecomposition : {local['successor_decomposition']}",
            "apply beta_product_succ_decompose",
            "exact hprimorial_witness_witness_right",
            "cases hdecomposition",
            "cases hdecomposition_witness",
            "cases hdecomposition_witness_witness",
            "cases hdecomposition_witness_witness_right",
            f"have hterminal : {local['successor_terminal']}",
            "apply hprimorial_witness_witness_left",
            "apply le_refl",
            "cases hterminal",
            "cases hterminal_witness",
            "have hfactor : x2 = x4",
            "apply beta_at_unique",
            "exact hdecomposition_witness_witness_left",
            "exact hterminal_witness_left",
            "exists x4",
            "exists x3",
            "split",
            "exact hterminal_witness_right",
            "split",
            "exists x",
            "exists x1",
            "split",
            "intro i",
            "intro hi",
            "apply hprimorial_witness_witness_left",
            "apply le_succ",
            "exact hi",
            "exact hdecomposition_witness_witness_right_left",
            "trans x3 * x2",
            "exact hdecomposition_witness_witness_right_right",
            "rewrite hfactor",
            "refl",
        ),
        PRIMORIAL_POSITIVE: (
            "induction m",
            "intro z",
            "intro hprimorial",
            "have hz : z = 1",
            "apply primorial_zero",
            "exact hprimorial",
            "exists 0",
            "trans 1",
            "exact hz",
            "refl",
            "intro z",
            "intro hprimorial",
            f"have hdecomposition : {local['successor_result']}",
            "apply primorial_succ_decompose",
            "exact hprimorial",
            "cases hdecomposition",
            "cases hdecomposition_witness",
            "cases hdecomposition_witness_witness",
            "cases hdecomposition_witness_witness_right",
            "have hprevious : exists t. x1 = S t",
            "apply IH",
            "exact hdecomposition_witness_witness_right_left",
            "cases hprevious",
            "cases hdecomposition_witness_witness_left",
            "cases hdecomposition_witness_witness_left_left",
            "exists x2 * S m + m",
            "trans x1 * x",
            "exact hdecomposition_witness_witness_right_right",
            "rewrite hprevious_witness",
            "rewrite hdecomposition_witness_witness_left_left_right",
            "trans x2 * S m + S m",
            "apply mul_succ_left",
            "apply PA4",
            "cases hdecomposition_witness_witness_left_right",
            "exists x2 * 1 + 0",
            "trans x1 * x",
            "exact hdecomposition_witness_witness_right_right",
            "rewrite hprevious_witness",
            "rewrite hdecomposition_witness_witness_left_right_right",
            "trans x2 * 1 + 1",
            "apply mul_succ_left",
            "apply PA4",
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_foundation_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    assert not (set(EXPECTED_NAMES) & set(public))
    return public


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _core() | _table(_specs()[:index])


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _available()
    formula = _closed_formula(item.statement)
    target = formula
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        if tactic == "use":
            raise AssertionError("primorial foundation delegated through use")
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    public = _specs_by_name()
    if name in public:
        checked = replay(name)
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


def test_bertrand_primorial_foundation_sources_are_pinned() -> None:
    expected = (
        (stable_module, STABLE_SOURCE_SHA256),
        (fold_surface, FOLD_SOURCE_SHA256),
        (choose_module, CHOOSE_HELPER_SOURCE_SHA256),
        (terms_module, TERMS_SOURCE_SHA256),
        (alpha_enrollment_v8, ALPHA_ENROLLMENT_SOURCE_SHA256),
        (editions_v8, EDITIONS_SOURCE_SHA256),
        (module, PRIMORIAL_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest
    rfc = (
        Path(__file__).resolve().parents[3]
        / "research/arithmetic-library/"
        "ha-bertrand-primorial-foundation-tranche-rfc-v1.md"
    )
    assert sha256(rfc.read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_primorial_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    expected_statements = _expected_statements()
    expected_scripts = _expected_scripts()
    assert make_bertrand_primorial_foundation_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected_statements[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert {item.name: item.script for item in rows} == expected_scripts
    assert module.__all__ == [
        "make_bertrand_primorial_foundation_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v8.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    for index, name in enumerate(EXPECTED_NAMES):
        assert set(_row_core(name)) == stable | set(EXPECTED_NAMES[:index])
    assert all(
        dependency in _row_core(item.name)
        for item in rows
        for dependency in item.dependencies
    )

    provider_token = "bertrand_primorial_foundation_candidate"
    for authority_module in (stable_module, alpha_enrollment_v8, editions_v8):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    for item in rows:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        for token in (
            "Primorial(",
            "FactorPrefix(",
            "Sel(",
            "Product(",
            "Prime(",
            "BetaAt(",
            "<=",
            "<",
            "^",
            "%",
            "|",
        ):
            assert token not in item.statement
        for command in item.script:
            assert all(
                token not in command
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


def test_bertrand_primorial_script_topology_is_exact() -> None:
    table = _table(_specs())
    scripts = _expected_scripts()
    for name in EXPECTED_NAMES:
        assert table[name].script == scripts[name]
    assert tuple(len(table[name].script) for name in EXPECTED_NAMES) == (
        13,
        28,
        42,
        20,
        36,
        14,
        31,
        7,
        40,
        42,
    )

    extend = table[PREFIX_EXTEND].script
    assert extend.count("rewrite hsplit_left") == 7
    assert extend.count("apply beta_prefix_extend") == 1
    transport = table[PREFIX_TRANSPORT].script
    assert transport.count("rewrite haq") == 2
    functional = table[PRIMORIAL_FUNCTIONAL].script
    assert functional.count(
        "apply primorial_factor_prefix_transport_entry"
    ) == 1
    assert functional.count("apply beta_product_transport_prefix") == 1
    successor = table[PRIMORIAL_SUCC].script
    assert successor.count("apply beta_product_succ_decompose") == 1
    assert successor.count("apply beta_at_unique") == 1
    assert successor.count("apply le_refl") == 1
    assert successor.count("apply le_succ") == 1
    assert not any(command.startswith("induction ") for command in successor)
    positive = table[PRIMORIAL_POSITIVE].script
    assert positive.count("cases hdecomposition_witness_witness_left") == 1
    assert positive.count(
        "cases hdecomposition_witness_witness_left_left"
    ) == 1
    assert not any(
        command.startswith("have hfactor : exists")
        for command in positive
    )
    assert positive.count("apply mul_succ_left") == 2
    assert positive.count("apply PA4") == 2


def test_bertrand_primorial_helpers_are_term_safe_and_hygienic() -> None:
    left = _primorial("S m", "z", tag="hygiene_left", variables=("m", "z"))
    right = _primorial(
        "S m", "z", tag="hygiene_right", variables=("m", "z")
    )
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"m", "z"}
    choice = _choice("S m", "z", tag="choice_term", variables=("m", "z"))
    assert module._primorial_factor_choice_term(
        "S m", "z", tag="choice_term", variables=("m", "z")
    ) == choice
    prefix = _prefix(
        "b",
        "c",
        "m + n",
        tag="prefix_term",
        variables=("b", "c", "m", "n"),
    )
    assert module._primorial_factor_prefix_term(
        "b",
        "c",
        "m + n",
        tag="prefix_term",
        variables=("b", "c", "m", "n"),
    ) == prefix
    assert module._primorial_relation_term(
        "S m", "z", tag="hygiene_left", variables=("m", "z")
    ) == left
    assert module._primorial_relation_term(
        "0", "1", tag="hygiene_closed", variables=()
    ) == _primorial("0", "1", tag="hygiene_closed", variables=())
    assert module._primorial_relation_term(
        "m + n",
        "z",
        tag="hygiene_compound",
        variables=("m", "n", "z"),
    ) == _primorial(
        "m + n",
        "z",
        tag="hygiene_compound",
        variables=("m", "n", "z"),
    )

    with pytest.raises(ValueError):
        module._primorial_relation_term(
            "m", "z", tag="bad tag", variables=("m", "z")
        )
    with pytest.raises(ValueError):
        module._primorial_relation_term(
            "m", "z", tag="valid", variables=["m", "z"]
        )
    with pytest.raises(ValueError):
        module._primorial_relation_term(
            "m", "z", tag="valid", variables=("m", "m", "z")
        )
    with pytest.raises(ValueError):
        module._primorial_relation_term(
            "m", "z", tag="valid", variables=("z",)
        )
    with pytest.raises(ValueError):
        module._primorial_relation_term(
            "bpr_code_valid",
            "z",
            tag="valid",
            variables=("bpr_code_valid", "z"),
        )
    with pytest.raises(ValueError):
        module._primorial_factor_prefix_term(
            "bpr_index_valid",
            "c",
            "m",
            tag="valid",
            variables=("bpr_index_valid", "c", "m"),
        )
    with pytest.raises(ValueError):
        module._primorial_factor_choice_term(
            "bpr_left_valid_prime",
            "z",
            tag="valid",
            variables=("bpr_left_valid_prime", "z"),
        )


def test_bertrand_primorial_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"PRIMORIAL {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_bodies_are_frozen(name: str) -> None:
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
        label=f"primorial foundation body {name}",
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
        f"PRIMORIAL {name} BODY actual={actual!r} "
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
    (item_name, dependency)
    for item_name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[item_name]
)
assert len(LIVE_EDGES) == 22


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_primorial_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(
            candidate
            for candidate in item.dependencies
            if candidate != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    part = _surface_parts()
    prime = _prime(
        "S (i)", tag="bpfc_exists_prime", avoid=("i", "a")
    )
    prime_branch = f"(({prime}) /\\ a = S (i))"
    nonprime_branch = f"(~({prime}) /\\ a = 1)"
    same_code_successor = _prefix(
        "b",
        "c",
        "S m",
        tag="bpfpe_mutated_same",
        variables=("b", "c", "m"),
    )
    prefix_zero = _at(
        "b",
        "c",
        "0",
        "0",
        tag="bpfpx_mutated_zero",
        avoid=("m", "b", "c"),
    )
    shifted_target = _at(
        "d",
        "e",
        "i",
        "S a",
        tag="bpfpt_target",
        avoid=("b", "c", "d", "e", "m", "i", "a"),
    )
    shifted_successor_choice = _choice(
        "S m",
        "p",
        tag="bp_succ_factor",
        variables=("m", "z", "p", "r"),
    )
    return (
        (
            CHOICE_EXISTS,
            "delete_nonprime_branch",
            part["choice_exists"],
            prime_branch,
        ),
        (
            CHOICE_EXISTS,
            "delete_prime_branch",
            part["choice_exists"],
            nonprime_branch,
        ),
        (
            CHOICE_FUNCTIONAL,
            "successor_result",
            "a = z",
            "a = S z",
        ),
        (
            PREFIX_EXTEND,
            "reuse_same_code",
            f"exists d e. ({part['extend_after']})",
            f"({same_code_successor})",
        ),
        (
            PREFIX_EXISTS,
            "force_zero_first_entry",
            f"exists b c. ({part['prefix_exists']})",
            (
                f"exists b c. (({part['prefix_exists']}) /\\ "
                f"({prefix_zero}))"
            ),
        ),
        (
            PREFIX_TRANSPORT,
            "shift_target_value",
            part["transport_target"],
            shifted_target,
        ),
        (
            PRIMORIAL_EXISTS,
            "force_zero_value",
            f"exists z. ({part['exists']})",
            f"exists z. (({part['exists']}) /\\ z = 0)",
        ),
        (
            PRIMORIAL_FUNCTIONAL,
            "successor_right_value",
            "x = y",
            "x = S y",
        ),
        (
            PRIMORIAL_ZERO,
            "zero_product_is_zero",
            "z = 1",
            "z = 0",
        ),
        (
            PRIMORIAL_SUCC,
            "shift_selector_index",
            part["successor_choice"],
            shifted_successor_choice,
        ),
        (
            PRIMORIAL_POSITIVE,
            "require_double_successor",
            "exists r. z = S r",
            "exists r. z = S (S r)",
        ),
    )


def test_bertrand_primorial_mutations_have_counterfixtures() -> None:
    assert 1 != 0  # Sel(0,1): candidate one is nonprime.
    assert 2 != 1  # Sel(1,2): candidate two is prime.
    assert 1 != 2  # Functionality at i=0 with a=z=1.
    assert 1 % 3 != 2  # Code one cannot decode factor two at index one.
    assert 1 != 0  # A nonempty prefix selects one at its first entry.
    assert 1 != 2  # Transport must preserve, not increment, the entry.
    assert 1 != 0  # Primorial(0)=1, so existence cannot force zero.
    assert 1 != 2  # Primorial functionality at index zero.
    assert 1 != 0  # The empty dense product is one.
    assert 1 != 2  # Primorial(1)=1 cannot use selector factor two.
    assert 1 < 2  # Primorial(0)=1 is positive but not a double successor.


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_bertrand_primorial_genuine_mutations_are_rejected(
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
def test_bertrand_primorial_independent_closures_are_frozen(
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
        label=f"primorial foundation closure {name}",
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
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    print(f"PRIMORIAL {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze independent closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
