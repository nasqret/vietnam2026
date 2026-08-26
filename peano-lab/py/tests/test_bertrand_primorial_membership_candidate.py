"""Fail-closed audit for Primorial membership and monotonicity.

The eleven candidate statements are rebuilt independently from the pinned
dense Primorial surface.  Replay authority is exactly Stable, the recursively
rebuilt ten-row Primorial foundation, and the earlier local row prefix.
Receipts are evidence only and never theorem authority.
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
    bertrand_primorial_foundation_candidate as foundation_module,
    bertrand_primorial_membership_candidate as module,
    editions_v8,
    finite_fold_surface as fold_surface,
    theorems as stable_module,
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


INDEX_TRANSPORT = "primorial_index_eq_transport"
CHOICE_PRIME_DIVISOR_EQ = "primorial_factor_choice_prime_divisor_eq"
PRIME_DIVIDES_OF_LE = "primorial_prime_divides_of_le"
PRIME_LE_OF_DIVIDES = "primorial_prime_le_of_divides"
PRIME_DIVIDES_IFF_LE = "primorial_prime_divides_iff_le"
SUCC_FACTOR = "primorial_succ_factor"
SUCC_DIVIDES = "primorial_succ_divides"
ADD_LENGTH_DIVIDES = "primorial_add_length_divides"
LE_DIVIDES = "primorial_le_divides"
LE_POSITIVE_QUOTIENT = "primorial_le_positive_quotient"
LE_MONOTONE = "primorial_le_monotone"

EXPECTED_NAMES = (
    INDEX_TRANSPORT,
    CHOICE_PRIME_DIVISOR_EQ,
    PRIME_DIVIDES_OF_LE,
    PRIME_LE_OF_DIVIDES,
    PRIME_DIVIDES_IFF_LE,
    SUCC_FACTOR,
    SUCC_DIVIDES,
    ADD_LENGTH_DIVIDES,
    LE_DIVIDES,
    LE_POSITIVE_QUOTIENT,
    LE_MONOTONE,
)
EXPECTED_DEPENDENCIES = {
    INDEX_TRANSPORT: (),
    CHOICE_PRIME_DIVISOR_EQ: (
        "divisor_one",
        "prime_divisor_eq_one_or_self",
    ),
    PRIME_DIVIDES_OF_LE: (
        "prime_is_succ_succ",
        "beta_factor_divides_product",
    ),
    PRIME_LE_OF_DIVIDES: (
        "divisor_one",
        "le_refl",
        "le_succ",
        "euclid_prime_dvd_product",
        "primorial_zero",
        "primorial_succ_decompose",
        CHOICE_PRIME_DIVISOR_EQ,
    ),
    PRIME_DIVIDES_IFF_LE: (PRIME_LE_OF_DIVIDES, PRIME_DIVIDES_OF_LE),
    SUCC_FACTOR: ("primorial_succ_decompose", "primorial_functional"),
    SUCC_DIVIDES: (SUCC_FACTOR,),
    ADD_LENGTH_DIVIDES: (
        "zero_add",
        "add_succ_left",
        INDEX_TRANSPORT,
        "primorial_functional",
        "multiple_refl",
        "primorial_exists",
        SUCC_DIVIDES,
        "multiple_trans",
    ),
    LE_DIVIDES: (INDEX_TRANSPORT, ADD_LENGTH_DIVIDES),
    LE_POSITIVE_QUOTIENT: (
        "zero_or_succ",
        "primorial_positive",
        LE_DIVIDES,
    ),
    LE_MONOTONE: (LE_POSITIVE_QUOTIENT,),
}
EXPECTED_DIRECT_CUTS = dict(
    zip(
        EXPECTED_NAMES,
        (0, 2, 2, 7, 2, 2, 1, 8, 2, 3, 1),
        strict=True,
    )
)
assert sum(map(len, EXPECTED_DEPENDENCIES.values())) == 30

FOUNDATION_NAMES = (
    "primorial_factor_choice_exists",
    "primorial_factor_choice_functional",
    "primorial_factor_prefix_extend",
    "primorial_factor_prefix_exists",
    "primorial_factor_prefix_transport_entry",
    "primorial_exists",
    "primorial_functional",
    "primorial_zero",
    "primorial_succ_decompose",
    "primorial_positive",
)
FOUNDATION_DEPENDENCIES = {
    FOUNDATION_NAMES[0]: ("prime_decidable",),
    FOUNDATION_NAMES[1]: (),
    FOUNDATION_NAMES[2]: (
        FOUNDATION_NAMES[0],
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    FOUNDATION_NAMES[3]: (
        "add_eq_zero_right",
        "succ_ne_zero",
        FOUNDATION_NAMES[2],
    ),
    FOUNDATION_NAMES[4]: ("beta_at_unique", FOUNDATION_NAMES[1]),
    FOUNDATION_NAMES[5]: ("beta_product_exists", FOUNDATION_NAMES[3]),
    FOUNDATION_NAMES[6]: (
        "beta_product_transport_prefix",
        "beta_product_functional",
        FOUNDATION_NAMES[4],
    ),
    FOUNDATION_NAMES[7]: ("beta_product_zero",),
    FOUNDATION_NAMES[8]: (
        "beta_product_succ_decompose",
        "beta_at_unique",
        "le_refl",
        "le_succ",
    ),
    FOUNDATION_NAMES[9]: (
        "mul_succ_left",
        FOUNDATION_NAMES[7],
        FOUNDATION_NAMES[8],
    ),
}

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
FOUNDATION_SOURCE_SHA256 = (
    "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98"
)
FOUNDATION_TEST_SHA256 = (
    "a4b270e209f7f68652c54926e5cd3e38a44baa42b2a969d4dc602c6b08fac0e1"
)
FOUNDATION_RFC_SHA256 = (
    "c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89"
)
MEMBERSHIP_SOURCE_SHA256 = (
    "edf14adde5edbbc6b7836003a174ee9a4b84f708fdcd0f3c3af45fc5013ac817"
)
MEMBERSHIP_RFC_SHA256 = (
    "4f569e76c68aa486fd1f1415491a5a3d678a75c239aa72ebd707d67fedde0df5"
)

# Execution receipts deliberately fail closed until reproduced serially.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    INDEX_TRANSPORT: (
        7177,
        "7a274234ee3bb9cf7a21348ac0f93afef7ddfa64b541dccdd1a16e2f04450626",
        "eab66c0bc5ac8d98592e20c979f26885b5f11782000f3c8dd895c92f3abc74f0",
        "7a274234ee3bb9cf7a21348ac0f93afef7ddfa64b541dccdd1a16e2f04450626",
    ),
    CHOICE_PRIME_DIVISOR_EQ: (
        797,
        "e43f1c2e9e884762dbeb877f2ab9be3260f70709c7d28d6874262f662124ca7a",
        "5bede1ede2364a288370626928cbddede165bed4d7a4fe2cf7b73ad173b18d2b",
        "cac5af9d30890038a349cba502c798fc6bc4e1938402e6634e7f9fe87e843a55",
    ),
    PRIME_DIVIDES_OF_LE: (
        4017,
        "cb207135eb99f9ab146abe290bdfd5c6a4fb07c305e2fd95d9c44a725e4ad773",
        "43065c4cb32d9a13fb97a536da7aaf07b4f991278deb9aa05b283a735af63e01",
        "3b3c640c07efad1c8c3301066a551b51e016c210f2b06be1f7bfcb3729af5029",
    ),
    PRIME_LE_OF_DIVIDES: (
        4021,
        "7826d458cfd5bc96e101fc9a25868e52c8f68f81b21c23d20e1258fda9443b1e",
        "3cf19ce958f9f2b3944ecf747c35b6bdbdb3e6238a5b956a7fced9c42e7e67ef",
        "2ff3c245b70536fd1406d94e7900c1a9b6e320ad1b6a9238e0fe0ebfa6045d25",
    ),
    PRIME_DIVIDES_IFF_LE: (
        4221,
        "a39ac81283f3c19c471ef758622f277d6ddabd69502b0e359c5751ed1db1880f",
        "4af94f76757521e29b05f42c44d81e6bf5fde427f1a945d58bb1e225e326ca3b",
        "3b84e288dfb9bcddebfc9af9a97ceecb43552ff929cc21463cd9d2fce8ca8cb8",
    ),
    SUCC_FACTOR: (
        7384,
        "67aab59f1e7a633c66a244581a506ccdb54f9ddd0404c897eab725d66e0ca44f",
        "8dc429df09a997b1fd12a195aaa9b5e642d27f0331f93d6a96b603f5f13a9be3",
        "09f111f102a2394d012ccc6066615653e7d06589f84db08d302726a47126f50c",
    ),
    SUCC_DIVIDES: (
        6961,
        "2535feb1c4bc129b04cf22ae6a2ce8cd87a9ffc4f2d95f9db8f47c202cb07ac1",
        "87d81df364143e900e795b26b6e59e2cba2c6b7bece6ddd3fbf2d598f226de28",
        "8dc53313615f120616626ed69c5c8ab57532bb243182e2403beaa8281ff6c946",
    ),
    ADD_LENGTH_DIVIDES: (
        7165,
        "81a25f1df093baccbeb3a0de527836a1e9e05710a10961438392cb7e89273ede",
        "de95574cdf2c32d1d9cc596edf947b223d99470ae0d188156929194d46f8afb0",
        "71998a71de9a407ae085249c160678878f9735c9d0404d3906d347d2fcb6fc01",
    ),
    LE_DIVIDES: (
        7036,
        "9ae7bf7dcfd2b9e9925ac90dcbd4283c67de46d5f2a95e147419a4f0356ec996",
        "a3cac6bf8442ae38ef8db76a9662c9c1eb16914688ac02f9859f37f0ae7d0f7a",
        "9628aab0204d77f497a0c37ef1e8e88a01deb34327fdfbb8bfbd5ee4c81a6b68",
    ),
    LE_POSITIVE_QUOTIENT: (
        7182,
        "92e1323cb6dc923be53ac30c10f366c600a629f95e97f3282b226a3d15c1509c",
        "f5a3ede33d8e207038853c6e193e31ae87235c8598c131bb8a22584f8262e9cb",
        "6d2b374b80bf09d797e92ff6ea373005b304905766737d9247bff52060c95232",
    ),
    LE_MONOTONE: (
        7034,
        "5581871c59ef8995565cb646c09a7cf41f3f8f134a84e622016fb070b06537a6",
        "b43efb21eeff1ed55d40ce831929991a4ad5cba09ce5cc621455a356a1ec830e",
        "35846c44e3074e4a911b09748f29d618660e13006f695b2f498a30fa64cb5de8",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    INDEX_TRANSPORT: (0, 10, 26, 14, 26, 25, 0),
    CHOICE_PRIME_DIVISOR_EQ: (2, 31, 40, 15, 40, 39, 0),
    PRIME_DIVIDES_OF_LE: (2, 45, 66, 23, 66, 65, 0),
    PRIME_LE_OF_DIVIDES: (7, 70, 96, 29, 96, 95, 0),
    PRIME_DIVIDES_IFF_LE: (2, 22, 48, 19, 48, 47, 0),
    SUCC_FACTOR: (2, 26, 34, 19, 34, 33, 0),
    SUCC_DIVIDES: (1, 16, 18, 13, 18, 17, 0),
    ADD_LENGTH_DIVIDES: (8, 66, 74, 26, 74, 73, 0),
    LE_DIVIDES: (2, 25, 28, 17, 28, 27, 0),
    LE_POSITIVE_QUOTIENT: (3, 35, 49, 19, 49, 48, 0),
    LE_MONOTONE: (1, 23, 28, 17, 28, 27, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    INDEX_TRANSPORT: (26, 26, 14, 1004, 38),
    CHOICE_PRIME_DIVISOR_EQ: (40, 40, 15, 16, 17),
    PRIME_DIVIDES_OF_LE: (66, 66, 23, 124, 27),
    PRIME_LE_OF_DIVIDES: (96, 96, 29, 326, 39),
    PRIME_DIVIDES_IFF_LE: (48, 48, 19, 6, 19),
    SUCC_FACTOR: (34, 34, 19, 11, 19),
    SUCC_DIVIDES: (18, 18, 13, 4, 13),
    ADD_LENGTH_DIVIDES: (74, 74, 26, 562, 39),
    LE_DIVIDES: (28, 28, 17, 9, 17),
    LE_POSITIVE_QUOTIENT: (49, 49, 19, 26, 21),
    LE_MONOTONE: (28, 28, 17, 9, 17),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    INDEX_TRANSPORT: (
        26,
        14,
        26,
        25,
        0,
        1004,
        38,
        "10ecbee2fbd57aeaf20ba54d12c9d8487dce9842cc9ab1399714b775e2826962",
    ),
    CHOICE_PRIME_DIVISOR_EQ: (
        285,
        29,
        269,
        284,
        16,
        772,
        30,
        "87bc3952700d9962c8517f07c7e7b27e62e38c2b48715ef8fce1b6146089ab8f",
    ),
    PRIME_DIVIDES_OF_LE: (
        3134,
        67,
        1162,
        1213,
        52,
        11520,
        67,
        "8a079aa6992bae556906f2444b47bb13063fd68ca7737882335b3e2a8dc0e3b5",
    ),
    PRIME_LE_OF_DIVIDES: (
        9722,
        69,
        2573,
        2708,
        136,
        34279,
        69,
        "868467f783b69044a3cc7ad0ce333be4c9dfd386a27e7947358d9b3ac46c6696",
    ),
    PRIME_DIVIDES_IFF_LE: (
        12904,
        70,
        2884,
        3028,
        145,
        47005,
        70,
        "2382a37dd765da4840c458e276574f2360dfe60953630d7f9b4e3a3929275e7a",
    ),
    SUCC_FACTOR: (
        5319,
        65,
        1353,
        1398,
        46,
        22691,
        65,
        "ee2462f404b10fef2779a8ebfee230fc2295db2885c08607e24b6c802bf832c5",
    ),
    SUCC_DIVIDES: (
        5337,
        66,
        1371,
        1416,
        46,
        23795,
        66,
        "a0cfb4736744c1a9a8028970d91e2cd74ba55a6c959d6a75421604506ec91917",
    ),
    ADD_LENGTH_DIVIDES: (
        70454,
        93,
        6242,
        6521,
        280,
        244511,
        93,
        "865a4e07db070730b66a793de04fd3f0d5f5a6263d1830cc548ce15276957076",
    ),
    LE_DIVIDES: (
        70508,
        95,
        6270,
        6550,
        281,
        247598,
        95,
        "d024eb6d4bf826d5db41763eca4cc9c076745c3010bb521448f7e785e4785098",
    ),
    LE_POSITIVE_QUOTIENT: (
        74516,
        98,
        6463,
        6747,
        285,
        265571,
        98,
        "d7ab6b53d16d4ad2c949ab034f3269203e8f7e3a4622c99236bc8b21e5739da7",
    ),
    LE_MONOTONE: (
        74544,
        99,
        6491,
        6775,
        285,
        266623,
        99,
        "e3385b67e4fca523cfafab51f5726e8f45c7e651c3f2d78de7112e11045acb08",
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


def _prime_rendered(value: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    left, right = _binders(tag, avoid, ("left", "right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def _prime(value: str, *, tag: str, variables: tuple[str, ...]) -> str:
    context = _context(variables)
    return _prime_rendered(_render(value, context), tag=tag, avoid=context)


def _choice_rendered(
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    selected = f"S ({index})"
    prime = _prime_rendered(selected, tag=f"{tag}_prime", avoid=avoid)
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


def _lt(left: str, right: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    (gap,) = _binders(tag, avoid, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _le(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_left = _render(left, context)
    rendered_right = _render(right, context)
    (gap,) = _binders(tag, context, ("le_gap",))
    return f"exists {gap}. {gap} + ({rendered_left}) = ({rendered_right})"


def _divides(
    divisor: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_divisor = _render(divisor, context)
    rendered_value = _render(value, context)
    (quotient,) = _binders(tag, context, ("quotient",))
    return (
        f"exists {quotient}. {rendered_value} = "
        f"({rendered_divisor}) * {quotient}"
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
    transport = ("n", "m", "z")
    choice = ("i", "a", "p")
    forward = ("p", "m", "z")
    step = ("m", "x", "y")
    add = ("g", "m", "x", "y")
    ordered = ("m", "n", "x", "y")
    return {
        "transport_source": _primorial(
            "n", "z", tag="bpmit_source", variables=transport
        ),
        "transport_target": _primorial(
            "m", "z", tag="bpmit_target", variables=transport
        ),
        "choice_prime": _prime(
            "p", tag="bpfcpde_prime", variables=choice
        ),
        "choice_relation": _choice(
            "i", "a", tag="bpfcpde_choice", variables=choice
        ),
        "choice_divides": _divides(
            "p", "a", tag="bpfcpde_divides", variables=choice
        ),
        "forward_prime": _prime(
            "p", tag="bppdol_prime", variables=forward
        ),
        "forward_bound": _le(
            "p", "m", tag="bppdol_bound", variables=forward
        ),
        "forward_source": _primorial(
            "m", "z", tag="bppdol_source", variables=forward
        ),
        "forward_result": _divides(
            "p", "z", tag="bppdol_result", variables=forward
        ),
        "reverse_prime": _prime(
            "p", tag="bpplod_prime", variables=forward
        ),
        "reverse_source": _primorial(
            "m", "z", tag="bpplod_source", variables=forward
        ),
        "reverse_divides": _divides(
            "p", "z", tag="bpplod_divides", variables=forward
        ),
        "reverse_result": _le(
            "p", "m", tag="bpplod_result", variables=forward
        ),
        "iff_prime": _prime(
            "p", tag="bppdil_prime", variables=forward
        ),
        "iff_source": _primorial(
            "m", "z", tag="bppdil_source", variables=forward
        ),
        "iff_divides_left": _divides(
            "p", "z", tag="bppdil_divides_left", variables=forward
        ),
        "iff_bound_left": _le(
            "p", "m", tag="bppdil_bound_left", variables=forward
        ),
        "iff_bound_right": _le(
            "p", "m", tag="bppdil_bound_right", variables=forward
        ),
        "iff_divides_right": _divides(
            "p", "z", tag="bppdil_divides_right", variables=forward
        ),
        "factor_before": _primorial(
            "m", "x", tag="bpsf_before", variables=step
        ),
        "factor_after": _primorial(
            "S m", "y", tag="bpsf_after", variables=step
        ),
        "factor_choice": _choice(
            "m", "p", tag="bpsf_factor", variables=step + ("p",)
        ),
        "divides_before": _primorial(
            "m", "x", tag="bpsd_before", variables=step
        ),
        "divides_after": _primorial(
            "S m", "y", tag="bpsd_after", variables=step
        ),
        "divides_result": _divides(
            "x", "y", tag="bpsd_result", variables=step
        ),
        "add_before": _primorial(
            "m", "x", tag="bpald_before", variables=add
        ),
        "add_after": _primorial(
            "g + m", "y", tag="bpald_after", variables=add
        ),
        "add_result": _divides(
            "x", "y", tag="bpald_result", variables=add
        ),
        "le_index_bound": _le(
            "m", "n", tag="bpld_index_bound", variables=ordered
        ),
        "le_before": _primorial(
            "m", "x", tag="bpld_before", variables=ordered
        ),
        "le_after": _primorial(
            "n", "y", tag="bpld_after", variables=ordered
        ),
        "le_result": _divides(
            "x", "y", tag="bpld_result", variables=ordered
        ),
        "positive_index_bound": _le(
            "m", "n", tag="bplpq_index_bound", variables=ordered
        ),
        "positive_before": _primorial(
            "m", "x", tag="bplpq_before", variables=ordered
        ),
        "positive_after": _primorial(
            "n", "y", tag="bplpq_after", variables=ordered
        ),
        "monotone_index_bound": _le(
            "m", "n", tag="bplm_index_bound", variables=ordered
        ),
        "monotone_before": _primorial(
            "m", "x", tag="bplm_before", variables=ordered
        ),
        "monotone_after": _primorial(
            "n", "y", tag="bplm_after", variables=ordered
        ),
        "monotone_result": _le(
            "x", "y", tag="bplm_result", variables=ordered
        ),
    }


def _script_surface_parts() -> dict[str, str]:
    forward_variables = ("p", "m", "z", "x", "x1", "x2", "a")
    forward_decoded = _at(
        "x1",
        "x2",
        "S x",
        "a",
        tag="bppdol_local_entry",
        avoid=forward_variables,
    )
    forward_choice = _choice(
        "S x",
        "a",
        tag="bppdol_local_choice",
        variables=forward_variables,
    )

    reverse_variables = ("p", "m", "z", "a", "r")
    reverse_choice = _choice(
        "m",
        "a",
        tag="bpplod_local_factor",
        variables=reverse_variables,
    )
    reverse_previous = _primorial(
        "m",
        "r",
        tag="bpplod_local_previous",
        variables=reverse_variables,
    )
    reverse_local_variables = ("p", "m", "z", "x", "x1")
    reverse_left = _divides(
        "p",
        "x1",
        tag="bpplod_local_left_divides",
        variables=reverse_local_variables,
    )
    reverse_right = _divides(
        "p",
        "x",
        tag="bpplod_local_right_divides",
        variables=reverse_local_variables,
    )

    step_variables = ("m", "x", "y")
    factor_choice = _choice(
        "m", "p", tag="bpsf_factor", variables=step_variables + ("p",)
    )
    factor_previous = _primorial(
        "m",
        "r",
        tag="bpsf_local_previous",
        variables=step_variables + ("p", "r"),
    )
    divides_choice = _choice(
        "m",
        "p",
        tag="bpsd_local_factor",
        variables=step_variables + ("p",),
    )

    add_variables = ("g", "m", "x", "y")
    add_middle = _primorial(
        "g + m",
        "r",
        tag="bpald_local_middle",
        variables=add_variables + ("r",),
    )
    ordered_variables = ("m", "n", "x", "y")
    return {
        "forward_entry": (
            f"exists a. (({forward_decoded}) /\\ ({forward_choice}))"
        ),
        "reverse_decomposition": (
            "exists a r. "
            f"({reverse_choice}) /\\ (({reverse_previous}) /\\ z = r * a)"
        ),
        "reverse_split": f"({reverse_left}) \\/ ({reverse_right})",
        "reverse_previous_bound": _le(
            "p",
            "m",
            tag="bpplod_local_previous_bound",
            variables=reverse_local_variables,
        ),
        "factor_decomposition": (
            "exists p r. "
            f"({factor_choice}) /\\ (({factor_previous}) /\\ y = r * p)"
        ),
        "divides_local_factor": (
            f"exists p. ({divides_choice}) /\\ y = x * p"
        ),
        "add_zero_target": _primorial(
            "m",
            "y",
            tag="bpald_local_zero_target",
            variables=add_variables,
        ),
        "add_step_target": _primorial(
            "S (g + m)",
            "y",
            tag="bpald_local_step_target",
            variables=add_variables,
        ),
        "add_middle_exists": f"exists r. ({add_middle})",
        "add_left_divides": _divides(
            "x",
            "x1",
            tag="bpald_local_left_divides",
            variables=add_variables + ("x1",),
        ),
        "add_right_divides": _divides(
            "x1",
            "y",
            tag="bpald_local_right_divides",
            variables=add_variables + ("x1",),
        ),
        "le_shifted_after": _primorial(
            "x1 + m",
            "y",
            tag="bpld_local_shifted_after",
            variables=ordered_variables + ("x1",),
        ),
        "positive_divides": _divides(
            "x",
            "y",
            tag="bplpq_local_divides",
            variables=ordered_variables,
        ),
    }


def _expected_statements() -> dict[str, str]:
    part = _surface_parts()
    return {
        INDEX_TRANSPORT: (
            "forall n m z. n = m -> "
            f"({part['transport_source']}) -> ({part['transport_target']})"
        ),
        CHOICE_PRIME_DIVISOR_EQ: (
            "forall i a p. "
            f"({part['choice_prime']}) -> ({part['choice_relation']}) -> "
            f"({part['choice_divides']}) -> p = S i"
        ),
        PRIME_DIVIDES_OF_LE: (
            "forall p m z. "
            f"({part['forward_prime']}) -> ({part['forward_bound']}) -> "
            f"({part['forward_source']}) -> ({part['forward_result']})"
        ),
        PRIME_LE_OF_DIVIDES: (
            "forall p m z. "
            f"({part['reverse_prime']}) -> ({part['reverse_source']}) -> "
            f"({part['reverse_divides']}) -> ({part['reverse_result']})"
        ),
        PRIME_DIVIDES_IFF_LE: (
            "forall p m z. "
            f"({part['iff_prime']}) -> ({part['iff_source']}) -> "
            f"((({part['iff_divides_left']}) -> "
            f"({part['iff_bound_left']})) /\\ "
            f"(({part['iff_bound_right']}) -> "
            f"({part['iff_divides_right']})))"
        ),
        SUCC_FACTOR: (
            "forall m x y. "
            f"({part['factor_before']}) -> ({part['factor_after']}) -> "
            f"(exists p. ({part['factor_choice']}) /\\ y = x * p)"
        ),
        SUCC_DIVIDES: (
            "forall m x y. "
            f"({part['divides_before']}) -> ({part['divides_after']}) -> "
            f"({part['divides_result']})"
        ),
        ADD_LENGTH_DIVIDES: (
            "forall g m x y. "
            f"({part['add_before']}) -> ({part['add_after']}) -> "
            f"({part['add_result']})"
        ),
        LE_DIVIDES: (
            "forall m n x y. "
            f"({part['le_index_bound']}) -> ({part['le_before']}) -> "
            f"({part['le_after']}) -> ({part['le_result']})"
        ),
        LE_POSITIVE_QUOTIENT: (
            "forall m n x y. "
            f"({part['positive_index_bound']}) -> "
            f"({part['positive_before']}) -> ({part['positive_after']}) -> "
            "exists q. y = x * S q"
        ),
        LE_MONOTONE: (
            "forall m n x y. "
            f"({part['monotone_index_bound']}) -> "
            f"({part['monotone_before']}) -> "
            f"({part['monotone_after']}) -> "
            f"({part['monotone_result']})"
        ),
    }


def _expected_scripts() -> dict[str, tuple[str, ...]]:
    return {
        INDEX_TRANSPORT: (
            "intro n",
            "intro m",
            "intro z",
            "intro hindex",
            "intro hsource",
            "rewrite hindex at hsource",
            "rewrite hindex at hsource",
            "rewrite hindex at hsource",
            "rewrite hindex at hsource",
            "exact hsource",
        ),
        CHOICE_PRIME_DIVISOR_EQ: (
            "intro i",
            "intro a",
            "intro p",
            "intro hp",
            "cases hp",
            "intro hchoice",
            "intro hdivides",
            "cases hchoice",
            "cases hchoice_left",
            "rewrite hchoice_left_right at hdivides",
            "have hsplit : p = 1 \\/ S i = p",
            "specialize prime_divisor_eq_one_or_self (S i)",
            "specialize prime_divisor_eq_one_or_self p",
            "apply prime_divisor_eq_one_or_self",
            "exact hchoice_left_left",
            "exact hdivides",
            "cases hsplit",
            "exfalso",
            "apply hp_left",
            "exact hsplit_left",
            "symm",
            "exact hsplit_right",
            "cases hchoice_right",
            "rewrite hchoice_right_right at hdivides",
            "have hpone : p = 1",
            "specialize divisor_one p",
            "apply divisor_one",
            "exact hdivides",
            "exfalso",
            "apply hp_left",
            "exact hpone",
        ),
        PRIME_DIVIDES_OF_LE: (
            "intro p",
            "intro m",
            "intro z",
            "intro hp",
            "intro hle",
            "intro hprimorial",
            "have hshape : exists k. p = S (S k)",
            "specialize prime_is_succ_succ p",
            "apply prime_is_succ_succ",
            "exact hp",
            "cases hshape",
            "rewrite hshape_witness at hp",
            "rewrite hshape_witness at hp",
            "rewrite hshape_witness at hle",
            "cases hprimorial",
            "cases hprimorial_witness",
            "cases hprimorial_witness_witness",
            "have hentry : " + _script_surface_parts()["forward_entry"],
            "apply hprimorial_witness_witness_left",
            "exact hle",
            "cases hentry",
            "cases hentry_witness",
            "cases hentry_witness_right",
            "cases hentry_witness_right_left",
            "have hfactor_value : x3 = p",
            "trans S (S x)",
            "exact hentry_witness_right_left_right",
            "symm",
            "exact hshape_witness",
            "rewrite hfactor_value at hentry_witness_left",
            "rewrite hfactor_value at hentry_witness_left",
            "specialize beta_factor_divides_product x1",
            "specialize beta_factor_divides_product x2",
            "specialize beta_factor_divides_product m",
            "specialize beta_factor_divides_product z",
            "specialize beta_factor_divides_product (S x)",
            "specialize beta_factor_divides_product p",
            "apply beta_factor_divides_product",
            "exact hle",
            "exact hentry_witness_left",
            "exact hprimorial_witness_witness_right",
            "cases hentry_witness_right_right",
            "exfalso",
            "apply hentry_witness_right_right_left",
            "exact hp",
        ),
        PRIME_LE_OF_DIVIDES: (
            "intro p",
            "intro m",
            "induction m",
            "intro z",
            "intro hp",
            "cases hp",
            "intro hprimorial",
            "intro hdivides",
            "have hz : z = 1",
            "specialize primorial_zero z",
            "apply primorial_zero",
            "exact hprimorial",
            "rewrite hz at hdivides",
            "have hpone : p = 1",
            "specialize divisor_one p",
            "apply divisor_one",
            "exact hdivides",
            "exfalso",
            "apply hp_left",
            "exact hpone",
            "intro z",
            "intro hp",
            "cases hp",
            "intro hprimorial",
            "intro hdivides",
            "have hdecomposition : "
            + _script_surface_parts()["reverse_decomposition"],
            "specialize primorial_succ_decompose m",
            "specialize primorial_succ_decompose z",
            "apply primorial_succ_decompose",
            "exact hprimorial",
            "cases hdecomposition",
            "cases hdecomposition_witness",
            "cases hdecomposition_witness_witness",
            "cases hdecomposition_witness_witness_right",
            "rewrite hdecomposition_witness_witness_right_right at hdivides",
            "have hsplit : " + _script_surface_parts()["reverse_split"],
            "specialize euclid_prime_dvd_product p",
            "specialize euclid_prime_dvd_product x1",
            "specialize euclid_prime_dvd_product x",
            "apply euclid_prime_dvd_product",
            "split",
            "exact hp_left",
            "exact hp_right",
            "exact hdivides",
            "cases hsplit",
            "have hprevious : "
            + _script_surface_parts()["reverse_previous_bound"],
            "specialize IH x1",
            "apply IH",
            "split",
            "exact hp_left",
            "exact hp_right",
            "exact hdecomposition_witness_witness_right_left",
            "exact hsplit_left",
            "specialize le_succ p",
            "specialize le_succ m",
            "apply le_succ",
            "exact hprevious",
            "have hterminal : p = S m",
            "specialize primorial_factor_choice_prime_divisor_eq m",
            "specialize primorial_factor_choice_prime_divisor_eq x",
            "specialize primorial_factor_choice_prime_divisor_eq p",
            "apply primorial_factor_choice_prime_divisor_eq",
            "split",
            "exact hp_left",
            "exact hp_right",
            "exact hdecomposition_witness_witness_left",
            "exact hsplit_right",
            "rewrite hterminal",
            "specialize le_refl (S m)",
            "exact le_refl",
        ),
        PRIME_DIVIDES_IFF_LE: (
            "intro p",
            "intro m",
            "intro z",
            "intro hp",
            "intro hprimorial",
            "split",
            "intro hdivides",
            "specialize primorial_prime_le_of_divides p",
            "specialize primorial_prime_le_of_divides m",
            "specialize primorial_prime_le_of_divides z",
            "apply primorial_prime_le_of_divides",
            "exact hp",
            "exact hprimorial",
            "exact hdivides",
            "intro hle",
            "specialize primorial_prime_divides_of_le p",
            "specialize primorial_prime_divides_of_le m",
            "specialize primorial_prime_divides_of_le z",
            "apply primorial_prime_divides_of_le",
            "exact hp",
            "exact hle",
            "exact hprimorial",
        ),
        SUCC_FACTOR: (
            "intro m",
            "intro x",
            "intro y",
            "intro hbefore",
            "intro hafter",
            "have hdecomposition : "
            + _script_surface_parts()["factor_decomposition"],
            "specialize primorial_succ_decompose m",
            "specialize primorial_succ_decompose y",
            "apply primorial_succ_decompose",
            "exact hafter",
            "cases hdecomposition",
            "cases hdecomposition_witness",
            "cases hdecomposition_witness_witness",
            "cases hdecomposition_witness_witness_right",
            "have hprevious : x = x2",
            "specialize primorial_functional m",
            "specialize primorial_functional x",
            "specialize primorial_functional x2",
            "apply primorial_functional",
            "exact hbefore",
            "exact hdecomposition_witness_witness_right_left",
            "exists x1",
            "split",
            "exact hdecomposition_witness_witness_left",
            "rewrite hprevious",
            "exact hdecomposition_witness_witness_right_right",
        ),
        SUCC_DIVIDES: (
            "intro m",
            "intro x",
            "intro y",
            "intro hbefore",
            "intro hafter",
            "have hfactor : " + _script_surface_parts()["divides_local_factor"],
            "specialize primorial_succ_factor m",
            "specialize primorial_succ_factor x",
            "specialize primorial_succ_factor y",
            "apply primorial_succ_factor",
            "exact hbefore",
            "exact hafter",
            "cases hfactor",
            "cases hfactor_witness",
            "exists x1",
            "exact hfactor_witness_right",
        ),
        ADD_LENGTH_DIVIDES: (
            "induction g",
            "intro m",
            "intro x",
            "intro y",
            "intro hbefore",
            "intro hafter",
            "have hzero : 0 + m = m",
            "specialize zero_add m",
            "exact zero_add",
            "have htarget : " + _script_surface_parts()["add_zero_target"],
            "specialize primorial_index_eq_transport (0 + m)",
            "specialize primorial_index_eq_transport m",
            "specialize primorial_index_eq_transport y",
            "apply primorial_index_eq_transport",
            "exact hzero",
            "exact hafter",
            "have hequal : x = y",
            "specialize primorial_functional m",
            "specialize primorial_functional x",
            "specialize primorial_functional y",
            "apply primorial_functional",
            "exact hbefore",
            "exact htarget",
            "rewrite <- hequal",
            "specialize multiple_refl x",
            "exact multiple_refl",
            "intro m",
            "intro x",
            "intro y",
            "intro hbefore",
            "intro hafter",
            "have hstep : S g + m = S (g + m)",
            "specialize add_succ_left g",
            "specialize add_succ_left m",
            "exact add_succ_left",
            "have htarget : " + _script_surface_parts()["add_step_target"],
            "specialize primorial_index_eq_transport (S g + m)",
            "specialize primorial_index_eq_transport (S (g + m))",
            "specialize primorial_index_eq_transport y",
            "apply primorial_index_eq_transport",
            "exact hstep",
            "exact hafter",
            "have hmiddle : " + _script_surface_parts()["add_middle_exists"],
            "specialize primorial_exists (g + m)",
            "exact primorial_exists",
            "cases hmiddle",
            "have hleft : " + _script_surface_parts()["add_left_divides"],
            "specialize IH m",
            "specialize IH x",
            "specialize IH x1",
            "apply IH",
            "exact hbefore",
            "exact hmiddle_witness",
            "have hright : " + _script_surface_parts()["add_right_divides"],
            "specialize primorial_succ_divides (g + m)",
            "specialize primorial_succ_divides x1",
            "specialize primorial_succ_divides y",
            "apply primorial_succ_divides",
            "exact hmiddle_witness",
            "exact htarget",
            "specialize multiple_trans x1",
            "specialize multiple_trans x",
            "specialize multiple_trans y",
            "apply multiple_trans",
            "exact hright",
            "exact hleft",
        ),
        LE_DIVIDES: (
            "intro m",
            "intro n",
            "intro x",
            "intro y",
            "intro hle",
            "intro hbefore",
            "intro hafter",
            "cases hle",
            "have hindex : n = x1 + m",
            "symm",
            "exact hle_witness",
            "have hshifted : " + _script_surface_parts()["le_shifted_after"],
            "specialize primorial_index_eq_transport n",
            "specialize primorial_index_eq_transport (x1 + m)",
            "specialize primorial_index_eq_transport y",
            "apply primorial_index_eq_transport",
            "exact hindex",
            "exact hafter",
            "specialize primorial_add_length_divides x1",
            "specialize primorial_add_length_divides m",
            "specialize primorial_add_length_divides x",
            "specialize primorial_add_length_divides y",
            "apply primorial_add_length_divides",
            "exact hbefore",
            "exact hshifted",
        ),
        LE_POSITIVE_QUOTIENT: (
            "intro m",
            "intro n",
            "intro x",
            "intro y",
            "intro hle",
            "intro hbefore",
            "intro hafter",
            "have hdivides : " + _script_surface_parts()["positive_divides"],
            "specialize primorial_le_divides m",
            "specialize primorial_le_divides n",
            "specialize primorial_le_divides x",
            "specialize primorial_le_divides y",
            "apply primorial_le_divides",
            "exact hle",
            "exact hbefore",
            "exact hafter",
            "cases hdivides",
            "have hpositive : exists r. y = S r",
            "specialize primorial_positive n",
            "specialize primorial_positive y",
            "apply primorial_positive",
            "exact hafter",
            "cases hpositive",
            "specialize zero_or_succ x1",
            "cases zero_or_succ",
            "rewrite zero_or_succ_left at hdivides_witness",
            "rewrite PA5 at hdivides_witness",
            "rewrite hpositive_witness at hdivides_witness",
            "exfalso",
            "apply PA1",
            "exact hdivides_witness",
            "cases zero_or_succ_right",
            "exists x3",
            "rewrite zero_or_succ_right_witness at hdivides_witness",
            "exact hdivides_witness",
        ),
        LE_MONOTONE: (
            "intro m",
            "intro n",
            "intro x",
            "intro y",
            "intro hle",
            "intro hbefore",
            "intro hafter",
            "have hquotient : exists q. y = x * S q",
            "specialize primorial_le_positive_quotient m",
            "specialize primorial_le_positive_quotient n",
            "specialize primorial_le_positive_quotient x",
            "specialize primorial_le_positive_quotient y",
            "apply primorial_le_positive_quotient",
            "exact hle",
            "exact hbefore",
            "exact hafter",
            "cases hquotient",
            "exists x * x1",
            "trans x * S x1",
            "symm",
            "apply PA6",
            "symm",
            "exact hquotient_witness",
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_membership_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _foundation_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_foundation_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    foundation = _table(_foundation_specs())
    assert not (set(stable) & set(foundation))
    assert not (set(EXPECTED_NAMES) & set(stable))
    assert not (set(EXPECTED_NAMES) & set(foundation))
    return stable | foundation


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
            raise AssertionError("Primorial membership delegated through use")
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _close(
    name: str,
    cache: dict[str, tuple[Formula, Proof]] | None = None,
) -> tuple[Formula, Proof]:
    """Close one row with a per-selector cache, never retained globally."""

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
    dependencies = tuple(_close(dependency, cache) for dependency in item.dependencies)
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


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_bertrand_primorial_membership_sources_are_pinned() -> None:
    expected = (
        (stable_module, STABLE_SOURCE_SHA256),
        (fold_surface, FOLD_SOURCE_SHA256),
        (choose_module, CHOOSE_HELPER_SOURCE_SHA256),
        (terms_module, TERMS_SOURCE_SHA256),
        (alpha_enrollment_v8, ALPHA_ENROLLMENT_SOURCE_SHA256),
        (editions_v8, EDITIONS_SOURCE_SHA256),
        (foundation_module, FOUNDATION_SOURCE_SHA256),
        (module, MEMBERSHIP_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest

    root = _repository_root()
    fixed_files = (
        (
            root
            / "peano-lab/py/tests/"
            "test_bertrand_primorial_foundation_candidate.py",
            FOUNDATION_TEST_SHA256,
        ),
        (
            root
            / "research/arithmetic-library/"
            "ha-bertrand-primorial-foundation-tranche-rfc-v1.md",
            FOUNDATION_RFC_SHA256,
        ),
        (
            root
            / "research/arithmetic-library/"
            "ha-bertrand-primorial-membership-tranche-rfc-v1.md",
            MEMBERSHIP_RFC_SHA256,
        ),
    )
    for path, digest in fixed_files:
        assert sha256(path.read_bytes()).hexdigest() == digest


def test_bertrand_primorial_membership_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    expected_scripts = _expected_scripts()
    assert make_bertrand_primorial_membership_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert {item.name: item.statement for item in rows} == _expected_statements()
    assert {item.name: item.dependencies for item in rows} == EXPECTED_DEPENDENCIES
    assert {item.name: item.script for item in rows} == expected_scripts
    assert module.__all__ == [
        "make_bertrand_primorial_membership_candidate_theorems"
    ]

    foundation = _foundation_specs()
    assert tuple(item.name for item in foundation) == FOUNDATION_NAMES
    assert {item.name: item.dependencies for item in foundation} == (
        FOUNDATION_DEPENDENCIES
    )
    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v8.ALPHA_ENTRIES}
    assert not (set(FOUNDATION_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    for index, name in enumerate(FOUNDATION_NAMES):
        allowed = stable | set(FOUNDATION_NAMES[:index])
        assert set(foundation[index].dependencies) <= allowed
    for index, name in enumerate(EXPECTED_NAMES):
        assert set(_row_core(name)) == (
            stable | set(FOUNDATION_NAMES) | set(EXPECTED_NAMES[:index])
        )
        assert set(rows[index].dependencies) <= set(_row_core(name))

    provider_token = "bertrand_primorial_membership_candidate"
    for authority_module in (
        stable_module,
        alpha_enrollment_v8,
        editions_v8,
        foundation_module,
    ):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    forbidden_surface = (
        "Primorial(",
        "FactorPrefix(",
        "Sel(",
        "Product(",
        "Prime(",
        "BetaAt(",
        "Dvd(",
        "<=",
        "<",
        "^",
        "%",
        "|",
    )
    forbidden_script = (
        "DNE",
        "classical",
        "by_contra",
        "sorry",
        "auto",
        "compact_arith",
        "ring",
        "use ",
    )
    for item in rows:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface)
        assert all(
            token not in command
            for command in item.script
            for token in forbidden_script
        )


def test_bertrand_primorial_membership_script_topology_is_exact() -> None:
    scripts = _expected_scripts()
    table = _table(_specs())
    assert {name: table[name].script for name in EXPECTED_NAMES} == scripts

    assert scripts[INDEX_TRANSPORT].count("rewrite hindex at hsource") == 4
    assert scripts[CHOICE_PRIME_DIVISOR_EQ].count("apply divisor_one") == 1
    assert scripts[CHOICE_PRIME_DIVISOR_EQ].count(
        "apply prime_divisor_eq_one_or_self"
    ) == 1
    assert scripts[PRIME_DIVIDES_OF_LE].count(
        "apply beta_factor_divides_product"
    ) == 1
    assert scripts[PRIME_DIVIDES_OF_LE].count(
        "apply prime_is_succ_succ"
    ) == 1
    reverse = scripts[PRIME_LE_OF_DIVIDES]
    assert reverse.count("induction m") == 1
    assert reverse.count("apply euclid_prime_dvd_product") == 1
    assert reverse.count("apply primorial_succ_decompose") == 1
    assert reverse.count(
        "apply primorial_factor_choice_prime_divisor_eq"
    ) == 1
    iff = scripts[PRIME_DIVIDES_IFF_LE]
    assert iff.count("apply primorial_prime_le_of_divides") == 1
    assert iff.count("apply primorial_prime_divides_of_le") == 1
    factor = scripts[SUCC_FACTOR]
    assert factor.count("apply primorial_succ_decompose") == 1
    assert factor.count("apply primorial_functional") == 1
    assert scripts[SUCC_DIVIDES].count("apply primorial_succ_factor") == 1
    additive = scripts[ADD_LENGTH_DIVIDES]
    assert additive.count("induction g") == 1
    assert additive.count("apply primorial_index_eq_transport") == 2
    assert additive.count("apply primorial_functional") == 1
    assert additive.count("apply primorial_exists") <= 1
    assert additive.count("apply primorial_succ_divides") == 1
    assert additive.count("apply multiple_trans") == 1
    ordered = scripts[LE_DIVIDES]
    assert ordered.count("apply primorial_index_eq_transport") == 1
    assert ordered.count("apply primorial_add_length_divides") == 1
    positive = scripts[LE_POSITIVE_QUOTIENT]
    assert positive.count("apply primorial_le_divides") == 1
    assert positive.count("apply primorial_positive") == 1
    assert positive.count("cases zero_or_succ") == 1
    monotone = scripts[LE_MONOTONE]
    assert monotone.count("apply primorial_le_positive_quotient") == 1
    assert monotone.count("apply PA6") == 1


def test_bertrand_primorial_membership_helpers_are_hygienic() -> None:
    variables = ("m", "n", "x", "y")
    assert module._le_term(
        "S m", "n + x", tag="helper_le", variables=variables
    ) == _le("S m", "n + x", tag="helper_le", variables=variables)
    assert module._divides_term(
        "S x", "y", tag="helper_divides", variables=variables
    ) == _divides(
        "S x", "y", tag="helper_divides", variables=variables
    )
    assert module._prime_relation_term(
        "S m", tag="helper_prime", variables=variables
    ) == _prime("S m", tag="helper_prime", variables=variables)
    left = foundation_module._primorial_relation_term(
        "m + n", "y", tag="helper_primorial_left", variables=variables
    )
    right = _primorial(
        "m + n", "y", tag="helper_primorial_left", variables=variables
    )
    assert left == right
    parsed, free = parse_formula_with_names(left)
    assert isinstance(parsed, Formula)
    assert set(free) == {"m", "n", "y"}

    failing_calls = (
        lambda: module._le_term(
            "missing", "n", tag="valid", variables=("m", "n")
        ),
        lambda: module._divides_term(
            "m", "missing", tag="valid", variables=("m", "n")
        ),
        lambda: module._prime_relation_term(
            "missing", tag="valid", variables=("m",)
        ),
        lambda: module._le_term(
            "m", "n", tag="bad tag", variables=("m", "n")
        ),
        lambda: module._le_term(
            "m", "n", tag="forall", variables=("m", "n")
        ),
        lambda: module._le_term(
            "m", "n", tag="valid", variables=["m", "n"]
        ),
        lambda: module._le_term(
            "m", "n", tag="valid", variables=("m", "m", "n")
        ),
        lambda: module._le_term(
            "m", "n", tag="valid", variables=("m",)
        ),
        lambda: module._le_term(
            "m",
            "n",
            tag="valid",
            variables=("m", "n", "bpr_le_gap_valid"),
        ),
        lambda: module._divides_term(
            "m",
            "n",
            tag="valid",
            variables=("m", "n", "bpr_quotient_valid"),
        ),
        lambda: module._prime_relation_term(
            "m",
            tag="valid",
            variables=("m", "bpr_left_valid"),
        ),
    )
    for call in failing_calls:
        with pytest.raises(ValueError):
            call()


def test_bertrand_primorial_membership_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS.values()) == (
        0,
        2,
        2,
        7,
        2,
        2,
        1,
        8,
        2,
        3,
        1,
    )
    assert sum(EXPECTED_DIRECT_CUTS.values()) == 30


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_membership_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"PRIMORIAL MEMBERSHIP {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_membership_bodies_are_frozen(name: str) -> None:
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
        label=f"primorial membership body {name}",
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
        f"PRIMORIAL MEMBERSHIP {name} BODY actual={actual!r} "
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
assert len(LIVE_EDGES) == len(set(LIVE_EDGES)) == 30


@pytest.mark.parametrize(
    ("name", "dependency"),
    LIVE_EDGES,
    ids=tuple(f"{name}--{dependency}" for name, dependency in LIVE_EDGES),
)
def test_bertrand_primorial_membership_every_dependency_is_live(
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
def test_bertrand_primorial_membership_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _double_successor_divides(
    divisor: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_divisor = _render(divisor, context)
    rendered_value = _render(value, context)
    (quotient,) = _binders(tag, context, ("quotient",))
    return (
        f"exists {quotient}. {rendered_value} = "
        f"({rendered_divisor}) * S (S {quotient})"
    )


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    part = _surface_parts()
    transport_variables = ("n", "m", "z")
    forward_variables = ("p", "m", "z")
    step_variables = ("m", "x", "y")
    add_variables = ("g", "m", "x", "y")
    ordered_variables = ("m", "n", "x", "y")
    return (
        (
            INDEX_TRANSPORT,
            "shift_target_index",
            part["transport_target"],
            _primorial(
                "S m",
                "z",
                tag="bpmit_target",
                variables=transport_variables,
            ),
        ),
        (
            CHOICE_PRIME_DIVISOR_EQ,
            "double_successor_candidate",
            "p = S i",
            "p = S (S i)",
        ),
        (
            PRIME_DIVIDES_OF_LE,
            "successor_divisor",
            part["forward_result"],
            _divides(
                "S p",
                "z",
                tag="bppdol_result",
                variables=forward_variables,
            ),
        ),
        (
            PRIME_LE_OF_DIVIDES,
            "successor_lower_bound",
            part["reverse_result"],
            _le(
                "S p",
                "m",
                tag="bpplod_result",
                variables=forward_variables,
            ),
        ),
        (
            PRIME_DIVIDES_IFF_LE,
            "strengthen_left_conjunct",
            part["iff_bound_left"],
            _le(
                "S p",
                "m",
                tag="bppdil_bound_left",
                variables=forward_variables,
            ),
        ),
        (
            SUCC_FACTOR,
            "shift_selected_factor",
            part["factor_choice"],
            _choice(
                "S m",
                "p",
                tag="bpsf_factor",
                variables=step_variables + ("p",),
            ),
        ),
        (
            SUCC_DIVIDES,
            "double_successor_quotient",
            part["divides_result"],
            _double_successor_divides(
                "x",
                "y",
                tag="bpsd_result",
                variables=step_variables,
            ),
        ),
        (
            ADD_LENGTH_DIVIDES,
            "successor_divisor",
            part["add_result"],
            _divides(
                "S x",
                "y",
                tag="bpald_result",
                variables=add_variables,
            ),
        ),
        (
            LE_DIVIDES,
            "reverse_index_bound",
            part["le_index_bound"],
            _le(
                "n",
                "m",
                tag="bpld_index_bound",
                variables=ordered_variables,
            ),
        ),
        (
            LE_POSITIVE_QUOTIENT,
            "double_successor_positive_quotient",
            "exists q. y = x * S q",
            "exists q. y = x * S (S q)",
        ),
        (
            LE_MONOTONE,
            "strict_value_growth",
            part["monotone_result"],
            _le(
                "S x",
                "y",
                tag="bplm_result",
                variables=ordered_variables,
            ),
        ),
    )


def test_bertrand_primorial_membership_mutations_have_counterfixtures() -> None:
    assert 1 != 2  # Primorial(1)=1, while Primorial(2)=2.
    assert 2 != 3  # At selector index one, the candidate is exactly two.
    assert 2 % 3 != 0  # S p does not divide Primorial(2) when p=2.
    assert not 3 <= 2  # Le(S p,m) fails at the boundary prime p=m=2.
    assert not 3 <= 2  # The left Dvd-to-Le conjunct cannot be strengthened.
    assert 2 != 3  # The 1-to-2 step selects index one, not index two.
    assert 1 < 2  # The neutral 0-to-1 step has quotient one, not at least two.
    assert 1 % 2 != 0  # S x cannot divide y at equal zero length.
    assert 1 <= 2 and 2 % 1 == 0 and 1 % 2 != 0
    assert 1 < 2  # Equal zero bounds have quotient one, not a double successor.
    assert not 2 <= 1  # Equal Primorial values do not grow strictly.


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_bertrand_primorial_membership_genuine_mutations_are_rejected(
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
def test_bertrand_primorial_membership_independent_closures_are_frozen(
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
        label=f"primorial membership closure {name}",
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

    print(
        f"PRIMORIAL MEMBERSHIP {name} CLOSURE actual={actual!r}",
        flush=True,
    )
    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze independent closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
