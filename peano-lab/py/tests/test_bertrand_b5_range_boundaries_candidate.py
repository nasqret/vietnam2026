"""Fail-closed audit for the Bertrand B5 range-boundary tranche."""

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
from peano_lab.library.bertrand_b5_range_boundaries_candidate import (
    DIVISION_QUOTIENT_LE_DIVIDEND,
    DIVISION_QUOTIENT_LOWER_OF_SCALED_LE,
    FLOOR_SQRT_LE_THIRD_QUOTIENT,
    FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS,
    FLOOR_SQRT_THREE_MUL_LE_DOUBLE,
    FLOOR_SQRT_TWO_LE_OF_TWO_LT,
    FLOOR_THIRD_DOUBLE_GAP_PACKAGE,
    THIRD_QUOTIENT_DOUBLE_GAP_EXISTS,
    THREE_MUL_LE_SQUARE_OF_THREE_LE,
    TWO_LT_DOUBLE_LOWER_SIX,
    make_bertrand_b5_range_boundaries_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
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


EXPECTED_NAMES = (
    TWO_LT_DOUBLE_LOWER_SIX,
    FLOOR_SQRT_TWO_LE_OF_TWO_LT,
    THREE_MUL_LE_SQUARE_OF_THREE_LE,
    FLOOR_SQRT_THREE_MUL_LE_DOUBLE,
    DIVISION_QUOTIENT_LOWER_OF_SCALED_LE,
    FLOOR_SQRT_LE_THIRD_QUOTIENT,
    FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS,
    DIVISION_QUOTIENT_LE_DIVIDEND,
    THIRD_QUOTIENT_DOUBLE_GAP_EXISTS,
    FLOOR_THIRD_DOUBLE_GAP_PACKAGE,
)

EXPECTED_DEPENDENCIES = {
    TWO_LT_DOUBLE_LOWER_SIX: (
        "add_le_add_right",
        "add_le_add_left",
        "le_trans",
    ),
    FLOOR_SQRT_TWO_LE_OF_TWO_LT: (
        "le_or_lt",
        "le_refl",
        "le_succ",
        "lt_of_lt_of_le",
        "lt_three_cases",
        "floor_sqrt_strict_upper_bound",
        TWO_LT_DOUBLE_LOWER_SIX,
        "le_trans",
        "lt_not_le",
        "lt_irrefl_expanded",
    ),
    THREE_MUL_LE_SQUARE_OF_THREE_LE: ("mul_le_mul_right",),
    FLOOR_SQRT_THREE_MUL_LE_DOUBLE: (
        TWO_LT_DOUBLE_LOWER_SIX,
        FLOOR_SQRT_TWO_LE_OF_TWO_LT,
        THREE_MUL_LE_SQUARE_OF_THREE_LE,
        "le_eq_or_lt",
        "floor_sqrt_lower_bound",
        "le_trans",
    ),
    DIVISION_QUOTIENT_LOWER_OF_SCALED_LE: (
        "division_block_upper",
        "le_or_lt",
        "mul_le_mul_left",
        "lt_of_lt_of_le",
        "lt_not_le",
    ),
    FLOOR_SQRT_LE_THIRD_QUOTIENT: (
        FLOOR_SQRT_THREE_MUL_LE_DOUBLE,
        DIVISION_QUOTIENT_LOWER_OF_SCALED_LE,
    ),
    FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS: (
        "add_comm",
        FLOOR_SQRT_LE_THIRD_QUOTIENT,
    ),
    DIVISION_QUOTIENT_LE_DIVIDEND: (
        "le_mul_of_one_le_left",
        "le_add_right",
        "le_trans",
    ),
    THIRD_QUOTIENT_DOUBLE_GAP_EXISTS: (
        "add_comm",
        DIVISION_QUOTIENT_LE_DIVIDEND,
    ),
    FLOOR_THIRD_DOUBLE_GAP_PACKAGE: (
        FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS,
        THIRD_QUOTIENT_DOUBLE_GAP_EXISTS,
    ),
}

EXPECTED_DIRECT_CUTS = dict(
    zip(EXPECTED_NAMES, (3, 10, 1, 6, 5, 2, 2, 3, 2, 2), strict=True)
)
assert sum(EXPECTED_DIRECT_CUTS.values()) == 36

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    TWO_LT_DOUBLE_LOWER_SIX: (
        174,
        "36cfeccb44fa65f9ea0b7a2e8bab565b1d0cd4e5cc9878f2794b7a70770ca6df",
        "fb779b81d5cbd1711668fcb036cbe0c9393372c64c0db6a013f7436cb7008690",
        "b1e43578458283a0720a4773f5902b750fb832f94136af8dbabb037b6c98463c",
    ),
    FLOOR_SQRT_TWO_LE_OF_TWO_LT: (
        382,
        "01eba4040374f11c94b463da39c632f3d647f8fb3c8ddfd89e5e5f361dbaf52c",
        "812353c890b1fba30b90f3bdb30f551f0afb19bf3636a0d36afb936e26eeb925",
        "4d1807c5594b5e6e0f7ae70ee89c8ebcd025209cd1acce32a1ad6907598a2169",
    ),
    THREE_MUL_LE_SQUARE_OF_THREE_LE: (
        172,
        "4d8b946fad30ba076486944c0e3ec5c7b6a52c1bbe589722be39a09ced27d07b",
        "5b9913f0bab4aada1553c76e9cf04058672d8402026f433b73d978602b392f3e",
        "3705a5edb799d4d458ae7014fd762532cca4755b5b07f8d47dea9703cab29b05",
    ),
    FLOOR_SQRT_THREE_MUL_LE_DOUBLE: (
        398,
        "0a2ae60546cedef2112f54b7540a34f57580f14643086142d2069747b8feacb4",
        "44eed44d1c03a102b8db1225323aa5cb0dedd62645c1eb35c0e22dce1d9e1e6b",
        "07b16136930026bc1e046b18c7776f49c4ee88c38bd1ca62dc797520e6fb2270",
    ),
    DIVISION_QUOTIENT_LOWER_OF_SCALED_LE: (
        308,
        "4dd82198f3527746d1c20df59127daf26582175efa06275579888354ff71f0e8",
        "595ce4d4ad61d7c75752e0b0e9593281891f777e1d1ba9ee723d24e72852cd02",
        "a8ad02a9fd47d3edf3f8883d0baf6f8c033531941fdd4a0b4d0f92a556d30ebb",
    ),
    FLOOR_SQRT_LE_THIRD_QUOTIENT: (
        524,
        "969dbea400f3487cf92af4b4371dc17355770fce60cb47cb07edf88c3c94bddf",
        "37e227f8be69721c7d94d9098aab21db3acb63d8a430ba932c2f35271e69a5a3",
        "ae5d031782e02fd76eabb5b7a990eb348a498a441364b4762d0cf0cc4f3f745b",
    ),
    FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS: (
        468,
        "1cafd44295618ab82c90915fefa56d5f070e85e082b527ddabfe49aacbdfeafd",
        "eef28399003fcbae267de724e19063247aed15d6840e21d6e5d93b3b623a2676",
        "7df3d5fa82d5e566f903e18a65b8935945e31abb300818ea2b8f0d6f3b26b751",
    ),
    DIVISION_QUOTIENT_LE_DIVIDEND: (
        219,
        "5a8712e417178d1798fe61b631401e0fd166c949b8e94cd226c64ed1c1f54e2b",
        "b2aa339fe2c85c989cd08dd72c8dd2e95a35d607b77b9329d74f276905b52f8c",
        "a8bd7cd7c21584bf5e1528c36fc0eb0241aa9009e86da6c040801b4fed34c2c3",
    ),
    THIRD_QUOTIENT_DOUBLE_GAP_EXISTS: (
        165,
        "a88bdf6d12ec77cb7261f5aade309220bc65674a950a998874ec862253846b56",
        "b1d22c4b03473fdee598507e205802d557cf24d0b357e5c5c6505025e3d876bf",
        "c661d74f3cb5f4c2105929a641802f1a91bac22b08a07eb28db0157e921c8a22",
    ),
    FLOOR_THIRD_DOUBLE_GAP_PACKAGE: (
        487,
        "a5a1d1d411635360c9b7c64fe2582a50b0955fbc814abb0b9646cfdbb1c8775b",
        "065361094c5d1915df029687c2c243c80ecfd091323baaad8d50a26a48d5e67a",
        "6c6e18584108a1d9868263109c5f9deb6b4f43b75638845b8667fea350e1d865",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    TWO_LT_DOUBLE_LOWER_SIX: (3, 20, 23, 12, 23, 22, 0),
    FLOOR_SQRT_TWO_LE_OF_TWO_LT: (10, 79, 271, 37, 271, 270, 0),
    THREE_MUL_LE_SQUARE_OF_THREE_LE: (1, 7, 18, 11, 18, 17, 0),
    FLOOR_SQRT_THREE_MUL_LE_DOUBLE: (6, 42, 135, 29, 135, 134, 0),
    DIVISION_QUOTIENT_LOWER_OF_SCALED_LE: (5, 42, 47, 24, 47, 46, 0),
    FLOOR_SQRT_LE_THIRD_QUOTIENT: (2, 21, 25, 17, 25, 24, 0),
    FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS: (2, 22, 28, 18, 28, 27, 0),
    DIVISION_QUOTIENT_LE_DIVIDEND: (3, 26, 44, 18, 44, 43, 0),
    THIRD_QUOTIENT_DOUBLE_GAP_EXISTS: (2, 16, 20, 13, 20, 19, 0),
    FLOOR_THIRD_DOUBLE_GAP_PACKAGE: (2, 29, 33, 18, 33, 32, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    TWO_LT_DOUBLE_LOWER_SIX: (23, 23, 12, 33, 15),
    FLOOR_SQRT_TWO_LE_OF_TWO_LT: (271, 271, 37, 312, 37),
    THREE_MUL_LE_SQUARE_OF_THREE_LE: (18, 18, 11, 6, 11),
    FLOOR_SQRT_THREE_MUL_LE_DOUBLE: (135, 135, 29, 133, 29),
    DIVISION_QUOTIENT_LOWER_OF_SCALED_LE: (47, 47, 24, 31, 24),
    FLOOR_SQRT_LE_THIRD_QUOTIENT: (25, 25, 17, 12, 20),
    FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS: (28, 28, 18, 10, 18),
    DIVISION_QUOTIENT_LE_DIVIDEND: (44, 44, 18, 53, 20),
    THIRD_QUOTIENT_DOUBLE_GAP_EXISTS: (20, 20, 13, 11, 13),
    FLOOR_THIRD_DOUBLE_GAP_PACKAGE: (33, 33, 18, 9, 18),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    TWO_LT_DOUBLE_LOWER_SIX: (
        265,
        18,
        188,
        200,
        13,
        755,
        18,
        "2e7492c8acc699339d0b0e1de0a8b052ea094af037665ce8eda5556373262675",
    ),
    FLOOR_SQRT_TWO_LE_OF_TWO_LT: (
        1_119,
        37,
        813,
        832,
        20,
        2_821,
        37,
        "9cc67c18846ccb3a61d47b9eb4987765b471972fdd3f164a55d5ae99a610c302",
    ),
    THREE_MUL_LE_SQUARE_OF_THREE_LE: (
        361,
        27,
        298,
        328,
        31,
        1_003,
        28,
        "6b1d770a647590523ef5a3643317ed2b688468d539fd0017d4bdff76c49765d2",
    ),
    FLOOR_SQRT_THREE_MUL_LE_DOUBLE: (
        2_047,
        39,
        1_163,
        1_207,
        45,
        5_521,
        39,
        "a3e441d94a69cfc1db9c24e32a3bdd685f16ff553e025578e9595126f0080da8",
    ),
    DIVISION_QUOTIENT_LOWER_OF_SCALED_LE: (
        484,
        28,
        403,
        419,
        17,
        1_264,
        28,
        "f6ed60013b0975ed3a08802b08857fa7d1fbfcf264438d1a412d005743f584d0",
    ),
    FLOOR_SQRT_LE_THIRD_QUOTIENT: (
        2_556,
        40,
        1_305,
        1_355,
        51,
        7_021,
        40,
        "354c48a01086b0ab70f16c9cf80cabfe5f204ab10acc584418d00a34194ee6b7",
    ),
    FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS: (
        2_657,
        42,
        1_333,
        1_384,
        52,
        7_408,
        42,
        "660e6a48fc302f8dc54f1286e8f78718fb2a1663f29ed19124dfe153974e3b82",
    ),
    DIVISION_QUOTIENT_LE_DIVIDEND: (
        564,
        28,
        391,
        427,
        37,
        1_603,
        29,
        "38ac90be96fcb0002b495b14f0038576306431d5757220bbcd2773bdcfce4649",
    ),
    THIRD_QUOTIENT_DOUBLE_GAP_EXISTS: (
        657,
        30,
        411,
        448,
        38,
        1_889,
        31,
        "d240e5aff550d26326d7afd4a220c611bc1133785fda656f3b64aa8da05de17a",
    ),
    FLOOR_THIRD_DOUBLE_GAP_PACKAGE: (
        3_347,
        43,
        1_473,
        1_532,
        60,
        9_566,
        43,
        "0bd0dcfdecb299e20597b84c76a19796763893cc25235e53402977844605255b",
    ),
}

SOURCE_PINS = {
    "theorems.py": (
        "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919"
    ),
    "alpha_enrollment_v11.py": (
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093"
    ),
    "editions_v11.py": (
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf"
    ),
    "bertrand_choose_foundation_candidate.py": (
        "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
    ),
    "bertrand_ceil_sqrt_candidate.py": (
        "745db5174c6f9348ec97fc6076a909f1dd98e04e899e5a26ebd38b61b842b237"
    ),
    "bertrand_b5_order_quotient_candidate.py": (
        "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e"
    ),
    "bertrand_b5_range_boundaries_candidate.py": (
        "767e574d2e93639e967b9cd497de83a80a266a051a7315990d0d9bd27613e95e"
    ),
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-range-boundaries-tranche-rfc-v1.md"
)
RFC_SHA256 = (
    "635a83faa0db7f4aae0f9c8632655789da91ad79ebb0a905bcf864d7bf646dbb"
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_b5_range_boundaries_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    alpha = {entry.spec.name: entry.spec for entry in editions_v11.ALPHA_ENTRIES}
    assert len(alpha) == len(editions_v11.ALPHA_ENTRIES)
    for name, item in stable.items():
        assert alpha[name] == item
    assert not set(EXPECTED_NAMES) & set(alpha)
    return alpha


def _row_core(name: str) -> dict[str, TheoremSpec]:
    return _core() | _table(_specs()[: EXPECTED_NAMES.index(name)])


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    target = _closed_formula(item.statement)
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
    dependencies = tuple(_close(dependency) for dependency in item.dependencies)
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


def _floor_sqrt(value: str, root: str, *, tag: str) -> str:
    lower = f"bcs_sqrt_lower_gap_{tag}"
    upper = f"bcs_sqrt_upper_gap_{tag}"
    return (
        f"((exists {lower}. {lower} + ({root}) * ({root}) = ({value})) /\\ "
        f"exists {upper}. {upper} + S ({value}) = S ({root}) * S ({root}))"
    )


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
    base_variables = ("n",)
    root_variables = ("n", "s")
    square_variables = ("s",)
    quotient_variables = ("d", "N", "q", "r", "s")
    boundary_variables = ("n", "s", "q", "r")
    dividend_variables = ("n", "q", "r")

    base_positive = _lt_term(
        "2", "n", tag="b5rbtdls_positive", variables=base_variables
    )
    base_result = _le_term(
        "3 + 3", "n + n", tag="b5rbtdls_result", variables=base_variables
    )
    root_positive = _lt_term(
        "2", "n", tag="b5rbfstl_positive", variables=root_variables
    )
    root_floor = _floor_sqrt("n + n", "s", tag="b5rbfstl_floor")
    root_result = _le_term(
        "2", "s", tag="b5rbfstl_result", variables=root_variables
    )
    square_source = _le_term(
        "3", "s", tag="b5rbtmsts_source", variables=square_variables
    )
    square_result = _le_term(
        "3 * s", "s * s", tag="b5rbtmsts_result", variables=square_variables
    )
    scaled_positive = _lt_term(
        "2", "n", tag="b5rbfstmd_positive", variables=root_variables
    )
    scaled_floor = _floor_sqrt("n + n", "s", tag="b5rbfstmd_floor")
    scaled_result = _le_term(
        "3 * s", "n + n", tag="b5rbfstmd_result", variables=root_variables
    )
    quotient_division = _divrem(
        "d",
        "N",
        "q",
        "r",
        tag="b5rbdqlosl_division",
        variables=quotient_variables,
    )
    quotient_scaled = _le_term(
        "d * s",
        "N",
        tag="b5rbdqlosl_scaled",
        variables=quotient_variables,
    )
    quotient_result = _le_term(
        "s", "q", tag="b5rbdqlosl_result", variables=quotient_variables
    )
    boundary_positive = _lt_term(
        "2", "n", tag="b5rbfsltq_positive", variables=boundary_variables
    )
    boundary_floor = _floor_sqrt("n + n", "s", tag="b5rbfsltq_floor")
    boundary_division = _divrem(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5rbfsltq_division",
        variables=boundary_variables,
    )
    boundary_result = _le_term(
        "s", "q", tag="b5rbfsltq_result", variables=boundary_variables
    )
    dividend_division = _divrem(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5rbdqld_division",
        variables=dividend_variables,
    )
    dividend_result = _le_term(
        "q", "n + n", tag="b5rbdqld_result", variables=dividend_variables
    )
    return {
        TWO_LT_DOUBLE_LOWER_SIX: (
            f"forall n. ({base_positive}) -> ({base_result})"
        ),
        FLOOR_SQRT_TWO_LE_OF_TWO_LT: (
            "forall n s. "
            f"({root_positive}) -> ({root_floor}) -> ({root_result})"
        ),
        THREE_MUL_LE_SQUARE_OF_THREE_LE: (
            f"forall s. ({square_source}) -> ({square_result})"
        ),
        FLOOR_SQRT_THREE_MUL_LE_DOUBLE: (
            "forall n s. "
            f"({scaled_positive}) -> ({scaled_floor}) -> ({scaled_result})"
        ),
        DIVISION_QUOTIENT_LOWER_OF_SCALED_LE: (
            "forall d N q r s. "
            f"({quotient_division}) -> ({quotient_scaled}) -> "
            f"({quotient_result})"
        ),
        FLOOR_SQRT_LE_THIRD_QUOTIENT: (
            "forall n s q r. "
            f"({boundary_positive}) -> ({boundary_floor}) -> "
            f"({boundary_division}) -> ({boundary_result})"
        ),
        FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS: (
            "forall n s q r. "
            f"({boundary_positive}) -> ({boundary_floor}) -> "
            f"({boundary_division}) -> exists g. s + g = q"
        ),
        DIVISION_QUOTIENT_LE_DIVIDEND: (
            "forall n q r. "
            f"({dividend_division}) -> ({dividend_result})"
        ),
        THIRD_QUOTIENT_DOUBLE_GAP_EXISTS: (
            "forall n q r. "
            f"({dividend_division}) -> exists h. q + h = n + n"
        ),
        FLOOR_THIRD_DOUBLE_GAP_PACKAGE: (
            "forall n s q r. "
            f"({boundary_positive}) -> ({boundary_floor}) -> "
            f"({boundary_division}) -> "
            "exists g h. s + g = q /\\ q + h = n + n"
        ),
    }


def _mutations() -> dict[str, str]:
    expected = _expected_statements()
    replacements = {
        TWO_LT_DOUBLE_LOWER_SIX: (
            _le_term("3 + 3", "n + n", tag="b5rbtdls_result", variables=("n",)),
            _le_term("7", "n + n", tag="b5rbtdls_result", variables=("n",)),
        ),
        FLOOR_SQRT_TWO_LE_OF_TWO_LT: (
            _le_term("2", "s", tag="b5rbfstl_result", variables=("n", "s")),
            _le_term("3", "s", tag="b5rbfstl_result", variables=("n", "s")),
        ),
        THREE_MUL_LE_SQUARE_OF_THREE_LE: (
            _le_term(
                "3 * s", "s * s", tag="b5rbtmsts_result", variables=("s",)
            ),
            _le_term(
                "4 * s", "s * s", tag="b5rbtmsts_result", variables=("s",)
            ),
        ),
        FLOOR_SQRT_THREE_MUL_LE_DOUBLE: (
            _le_term(
                "3 * s",
                "n + n",
                tag="b5rbfstmd_result",
                variables=("n", "s"),
            ),
            _le_term(
                "4 * s",
                "n + n",
                tag="b5rbfstmd_result",
                variables=("n", "s"),
            ),
        ),
        DIVISION_QUOTIENT_LOWER_OF_SCALED_LE: (
            _le_term(
                "s",
                "q",
                tag="b5rbdqlosl_result",
                variables=("d", "N", "q", "r", "s"),
            ),
            _le_term(
                "S s",
                "q",
                tag="b5rbdqlosl_result",
                variables=("d", "N", "q", "r", "s"),
            ),
        ),
        FLOOR_SQRT_LE_THIRD_QUOTIENT: (
            _le_term(
                "s",
                "q",
                tag="b5rbfsltq_result",
                variables=("n", "s", "q", "r"),
            ),
            _le_term(
                "S s",
                "q",
                tag="b5rbfsltq_result",
                variables=("n", "s", "q", "r"),
            ),
        ),
        FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS: (
            "exists g. s + g = q",
            "exists g. S s + g = q",
        ),
        DIVISION_QUOTIENT_LE_DIVIDEND: (
            _le_term(
                "q",
                "n + n",
                tag="b5rbdqld_result",
                variables=("n", "q", "r"),
            ),
            _le_term(
                "S q",
                "n + n",
                tag="b5rbdqld_result",
                variables=("n", "q", "r"),
            ),
        ),
        THIRD_QUOTIENT_DOUBLE_GAP_EXISTS: (
            "exists h. q + h = n + n",
            "exists h. S q + h = n + n",
        ),
        FLOOR_THIRD_DOUBLE_GAP_PACKAGE: (
            "s + g = q /\\ q + h = n + n",
            "S s + g = q /\\ q + h = n + n",
        ),
    }
    result: dict[str, str] = {}
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
assert len(LIVE_EDGES) == 36


def test_bertrand_b5_range_boundaries_sources_and_rfc_are_pinned() -> None:
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


def test_bertrand_b5_range_boundaries_surfaces_and_authority() -> None:
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

    provider_token = "bertrand_b5_range_boundaries_candidate"
    for authority in (stable_module, alpha_enrollment_v11, editions_v11):
        source = Path(authority.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

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


def test_bertrand_b5_range_boundaries_topology_is_exact() -> None:
    rows = _table(_specs())
    assert rows[TWO_LT_DOUBLE_LOWER_SIX].script.count("apply le_trans") == 1
    root = rows[FLOOR_SQRT_TWO_LE_OF_TWO_LT].script
    assert root.count("cases hsmall_cases") == 1
    assert root.count("cases hsmall_cases_left") == 1
    assert root.count("apply floor_sqrt_strict_upper_bound") == 1
    assert rows[THREE_MUL_LE_SQUARE_OF_THREE_LE].script.count(
        "apply mul_le_mul_right"
    ) == 1
    scaled = rows[FLOOR_SQRT_THREE_MUL_LE_DOUBLE].script
    assert scaled.count("cases hsplit") == 1
    assert scaled.count("apply floor_sqrt_lower_bound") == 1
    quotient = rows[DIVISION_QUOTIENT_LOWER_OF_SCALED_LE].script
    assert quotient.count("cases hdivision") == 1
    assert quotient.count("cases hcases") == 1
    assert quotient.count("apply division_block_upper") == 1
    assert rows[FLOOR_SQRT_LE_THIRD_QUOTIENT].script.count(
        "apply division_quotient_lower_of_scaled_le"
    ) == 1
    assert rows[FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS].script.count(
        "cases hbound"
    ) == 1
    assert rows[DIVISION_QUOTIENT_LE_DIVIDEND].script.count(
        "apply le_trans"
    ) == 1
    assert rows[THIRD_QUOTIENT_DOUBLE_GAP_EXISTS].script.count(
        "cases hbound"
    ) == 1
    package = rows[FLOOR_THIRD_DOUBLE_GAP_PACKAGE].script
    assert package.count("cases hfirst") == 1
    assert package.count("cases hsecond") == 1
    assert not any(
        command.startswith("induction")
        for row in rows.values()
        for command in row.script
    )
    assert not any(
        command.startswith("rewrite")
        and command.endswith((" at hfloor", " at hdivision"))
        for row in rows.values()
        for command in row.script
    )


def test_bertrand_b5_range_boundaries_receipts_are_shaped() -> None:
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
        3,
        10,
        1,
        6,
        5,
        2,
        2,
        3,
        2,
        2,
    )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_range_boundaries_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 RANGE {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_range_boundaries_bodies_are_frozen(name: str) -> None:
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
        label=f"B5 range body {name}",
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
        f"B5 RANGE {name} BODY actual={actual!r} envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_b5_range_boundaries_every_dependency_is_live(
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
def test_bertrand_b5_range_boundaries_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def test_bertrand_b5_range_boundaries_mutation_counterfixtures() -> None:
    assert 2 < 3 and not (7 <= 3 + 3)
    assert 2 * 2 <= 3 + 3 < 3 * 3 and not (3 <= 2)
    assert 3 <= 3 and not (4 * 3 <= 3 * 3)
    assert not (4 * 2 <= 3 + 3)
    assert 3 + 3 == 3 * 2 + 0 and not (3 <= 2)
    assert not (3 <= 2)
    assert not any(3 + gap == 2 for gap in range(4))
    assert 0 == 3 * 0 + 0 and not (1 <= 0)
    assert not any(1 + gap == 0 for gap in range(2))
    assert not any(3 + gap == 2 for gap in range(4))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_range_boundaries_genuine_mutations_are_rejected(
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
def test_bertrand_b5_range_boundaries_closures_are_frozen(name: str) -> None:
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
        label=f"B5 range closure {name}",
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
    expected_cuts = EXPECTED_DIRECT_CUTS[name]
    current = certificate
    for _index in range(expected_cuts):
        assert type(current) is Cut
        current = current.body
    assert type(current) is not Cut
    for index in range(expected_cuts):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)
    print(
        f"B5 RANGE {name} CLOSURE actual={actual!r}",
        flush=True,
    )
    assert EXPECTED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_CLOSURES[name]
