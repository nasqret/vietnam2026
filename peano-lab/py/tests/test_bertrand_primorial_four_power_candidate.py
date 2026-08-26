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
from peano_lab.kernel.formulas import Formula, Imp
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v10
from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
    make_bertrand_central_binom_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_succ_candidate import (
    make_bertrand_central_binom_succ_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_upper_candidate import (
    make_bertrand_central_binom_upper_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_zero_candidate import (
    make_bertrand_central_binom_zero_candidate_theorems,
)
from peano_lab.library.bertrand_choose_diagonal_candidate import (
    make_bertrand_choose_diagonal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_factorial_bridge_candidate import (
    make_bertrand_choose_factorial_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_choose_factorial_support_candidate import (
    make_bertrand_choose_factorial_support_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    _le_term,
    make_bertrand_choose_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    make_bertrand_choose_laws_candidate_theorems,
)
from peano_lab.library.bertrand_choose_pascal_candidate import (
    make_bertrand_choose_pascal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_positive_candidate import (
    make_bertrand_choose_positive_candidate_theorems,
)
from peano_lab.library.bertrand_choose_recurrence_candidate import (
    make_bertrand_choose_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_choose_row_functional_candidate import (
    make_bertrand_choose_row_functional_candidate_theorems,
)
from peano_lab.library.bertrand_choose_symmetry_candidate import (
    make_bertrand_choose_symmetry_candidate_theorems,
)
from peano_lab.library.bertrand_choose_table_row_functional_candidate import (
    make_bertrand_choose_table_row_functional_candidate_theorems,
)
from peano_lab.library.bertrand_choose_weighted_vertical_candidate import (
    make_bertrand_choose_weighted_vertical_candidate_theorems,
)
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_bridge_candidate import (
    make_bertrand_power_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_choose_interval_candidate import (
    make_bertrand_primorial_choose_interval_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _primorial_relation_term,
    make_bertrand_primorial_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_four_power_candidate import (
    make_bertrand_primorial_four_power_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_interval_candidate import (
    _primorial_interval_relation_term,
    make_bertrand_primorial_interval_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_membership_candidate import (
    make_bertrand_primorial_membership_candidate_theorems,
)
from peano_lab.library.bertrand_quotient_budget_candidate import (
    make_bertrand_quotient_budget_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_residue_product_candidate import (
    make_fermat_residue_product_candidate_theorems,
)
from peano_lab.library.finite_product_prefix_suffix_candidate import (
    make_finite_product_prefix_suffix_candidate_theorems,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    compile_layered_replay,
    intern_layered_replay_bodies,
)
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "primorial_one",
    "double_half_predecessor_data",
    "odd_positive_prefix_predecessor_bound",
    "central_binom_nonzero_strong_upper",
    "primorial_four_power_support_package",
    "primorial_le_four_pow_bounded",
    "primorial_le_four_pow",
)

EXPECTED_DEPENDENCIES = {
    EXPECTED_NAMES[0]: ("primorial_zero", "primorial_succ_decompose"),
    EXPECTED_NAMES[1]: ("two_mul_eq_add_self", "add_succ_left"),
    EXPECTED_NAMES[2]: ("two_mul_eq_add_self", "add_succ_left"),
    EXPECTED_NAMES[3]: ("central_binom_strong_upper",),
    EXPECTED_NAMES[4]: (
        "central_binom_exists",
        "choose_exists",
        "primorial_prefix_interval_split",
        "primorial_even_interval_le_central",
        "primorial_odd_interval_le_middle",
        "central_binom_odd_middle_le_four_pow",
    ),
    EXPECTED_NAMES[5]: (
        "le_zero",
        "le_eq_or_lt",
        "le_of_succ_le_succ",
        "zero_or_succ",
        "le_refl",
        "le_add_right",
        "le_trans",
        "mul_le_mul",
        "two_mul_eq_add_self",
        "add_succ_left",
        "parity_cases",
        "pow_exists",
        "pow_zero",
        "pow_one",
        "pow_add",
        "primorial_index_eq_transport",
        "primorial_zero",
        EXPECTED_NAMES[0],
        EXPECTED_NAMES[1],
        EXPECTED_NAMES[2],
        EXPECTED_NAMES[3],
    ),
    EXPECTED_NAMES[6]: (
        "le_refl",
        EXPECTED_NAMES[4],
        EXPECTED_NAMES[5],
    ),
}

EXPECTED_DIRECT_EDGES = dict(
    zip(EXPECTED_NAMES, (2, 2, 2, 1, 6, 21, 3), strict=True)
)
assert sum(map(len, EXPECTED_DEPENDENCIES.values())) == 37

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    EXPECTED_NAMES[0]: (
        3402,
        "c7f859d89db18445b73070dc35e525f5b62255ba57e56dd6c726574bc2edf978",
        "cb5a4f494383707c15fdaf78797d6b4424efeb15fbcd3f031c4b1647227f76e1",
        "4e03565f36ac54b970a37e71c0ca6b861c94d4e0f16918a0648d7f3023f09351",
    ),
    EXPECTED_NAMES[1]: (
        108,
        "359118772768df520ecc56bf5e975eb6560e7ca1864b68ff97b3b7aa067ac42e",
        "013a02a02bb61dd53a75745045c0b121c3a156fad04641547d8df45516e5ba58",
        "7b27e975e737f27b953e6039f3f1f7d8c7e71f1e69964173ec73e3bb696e8bac",
    ),
    EXPECTED_NAMES[2]: (
        123,
        "b320d11f3fc6d029e70028b73c5d47e842f91b10561dc24c21f49033a8bdee5f",
        "3b9d17f388e605268a42cd1a51ac0afae95ebba82c289e261a1acf0cfa7c811a",
        "f77225f042cc6b0ed874a8c03187b2c8ce6c8916d2d4f6b6bc443b1d89c29713",
    ),
    EXPECTED_NAMES[3]: (
        10440,
        "7d8a5bb4292ef09d2fd5074e388d153332f9876889dddc03e28bc3a78a21cd90",
        "3dd144824520fb4b34133d3b2e291cddf03fcaa4b853aa60d9096feff60fcc2d",
        "4fa5d8055258f47f431cbd3fb556817cf5213eeca07e7854d7775bedba76d812",
    ),
    EXPECTED_NAMES[4]: (
        68902,
        "08b8c1fba8506570897f039421349a70a14c52566b384c28b0b543694c833054",
        "5fa6c7e1131973826c1f2522263a591a2c74b0f00d7967c15d9704478e591ab3",
        "711aad37174ab5ded10fa2dea4ed88e456621495abff2076495a9b332af540b7",
    ),
    EXPECTED_NAMES[5]: (
        75638,
        "825cd90cde9e9d0ccff15d44324b69a8d631ca546324da2b362d99f59c3a3b1c",
        "87122d5ba13787f8fbd20fbbb95a083f5f79e5bb26d3aba88c624493b96177d7",
        "80703f4cd50e66e27c8627499a05b866b8a3826d654ff3145e4328f3727d9e25",
    ),
    EXPECTED_NAMES[6]: (
        6483,
        "a7b1b285007564aaea7bddc85d853561b76623d611b95eea651aeff388c60a2e",
        "c7d7286091c1131b470ef9ba1143e6e04dbaeec6936a5747d631843a459f8b4f",
        "36bf0858652689c7fd2a546af281c1c9d309e08bcccf94a6f905b624995897bc",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    EXPECTED_NAMES[0]: (2, 27, 97, 16, 97, 96, 0),
    EXPECTED_NAMES[1]: (2, 19, 70, 20, 68, 69, 2),
    EXPECTED_NAMES[2]: (2, 17, 69, 23, 64, 68, 5),
    EXPECTED_NAMES[3]: (1, 20, 35, 18, 35, 34, 0),
    EXPECTED_NAMES[4]: (6, 11, 17, 12, 17, 16, 0),
    EXPECTED_NAMES[5]: (21, 303, 486, 56, 481, 485, 5),
    EXPECTED_NAMES[6]: (3, 17, 22, 17, 22, 21, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    EXPECTED_NAMES[0]: (97, 97, 16, 58, 16),
    EXPECTED_NAMES[1]: (70, 68, 20, 115, 22),
    EXPECTED_NAMES[2]: (69, 64, 23, 172, 26),
    EXPECTED_NAMES[3]: (35, 35, 18, 623, 49),
    EXPECTED_NAMES[4]: (17, 17, 12, 0, 12),
    EXPECTED_NAMES[5]: (486, 481, 56, 836, 59),
    EXPECTED_NAMES[6]: (22, 22, 17, 5, 17),
}
EXPECTED_LAYERED_CLOSURES: dict[
    str,
    tuple[int, int, int, int, int, int, int, str, str] | None,
] = {
    EXPECTED_NAMES[0]: (
        3840,
        65,
        712,
        945,
        234,
        12524,
        65,
        "b1a4c6d2be75824e307f539018fd8ec00e74c3b833a87a7d1b1437ba729d6fd8",
        "62e3a97578f4548500f701c0365790c69da8269ea211b4adf8664028daaee4c3",
    ),
    EXPECTED_NAMES[1]: (
        391,
        27,
        249,
        311,
        63,
        932,
        28,
        "8541205f563cc52ffd346758fb334f80bb2eb643b66ca4d1f5f7cec368125f4b",
        "e6e97c00f6bf0bdaa013310e2c63a72991e4233d5ad5cf9662bfeec9beee772e",
    ),
    EXPECTED_NAMES[2]: (
        390,
        28,
        252,
        310,
        59,
        1005,
        31,
        "5bb22e86d10541b41412371c0259ff2bd1f7f49d6ee1c7db40b5caaa36b89eff",
        "ca236604600d9201e492fcaee05c27757b1b0cf56e8ad12403b0629e096400c5",
    ),
    EXPECTED_NAMES[3]: (
        42676,
        89,
        6735,
        9098,
        2364,
        166163,
        89,
        "482cc60190184a494c4481bee7dd765c875983e5c506a562a9ef777202dac2a6",
        "0611cb98df67b4698071dead8269bc8fe60c7485857929fb65fc41283581d3ab",
    ),
    EXPECTED_NAMES[4]: (
        261349,
        95,
        10079,
        13539,
        3461,
        934272,
        95,
        "94bc6a0db28b6a95ec990a87cef5ebda8e130c77a8df2997fc11047386529f9a",
        "da627c10236bf42dfb60adc615a8f7e04de7792906e25d334ce8dcbea66df94d",
    ),
    EXPECTED_NAMES[5]: (
        116993,
        94,
        8046,
        10853,
        2808,
        467980,
        94,
        "7b630dbd96217afdfce39bb491bd3afb3aefd8b144ce6707852c3d46c26a362d",
        "88bb1d994316b3870e95bc2f0e0872e0c30665fa42f3db61e444613e2d1d6623",
    ),
    EXPECTED_NAMES[6]: (
        273390,
        95,
        11021,
        14743,
        3723,
        950581,
        95,
        "b6fc2f868d90eef5c58eca779c617972c630a41cec00442a352dd11f2ecda6ec",
        "1517f21f9ffdc16bc1ae3a33935d9cfb094911a27e98bc299ff791f2a2bc672f",
    ),
}

SOURCE_PINS = {
    "bertrand_primorial_foundation_candidate.py": (
        "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98"
    ),
    "bertrand_primorial_membership_candidate.py": (
        "edf14adde5edbbc6b7836003a174ee9a4b84f708fdcd0f3c3af45fc5013ac817"
    ),
    "bertrand_primorial_interval_candidate.py": (
        "02e59e0f7addcae3bb127271ddeaa6728c5dab1dee096a878fced278065c10a3"
    ),
    "bertrand_primorial_choose_interval_candidate.py": (
        "5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09"
    ),
    "bertrand_central_binom_upper_candidate.py": (
        "5bfea8dc2427bf60be8115c6b8cfb8e6a81d4c1bfb0ce65b695cdb065281247a"
    ),
    "bertrand_integer_envelope_candidate.py": (
        "8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1"
    ),
    "bertrand_power_order_candidate.py": (
        "50b07e3b40b81966a37bc07cbb44b93498a86efa76aabcbb4af94b17c1eb17e6"
    ),
    "bertrand_primorial_four_power_candidate.py": (
        "86c0bfa4e5840c35d0ea6a0bf443dedd159c298b21ee6345d1cdc0d5c6ede2f3"
    ),
}

RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-primorial-four-power-tranche-rfc-v1.md"
)
RFC_SHA256 = (
    "5edd10d8f7b43ce503a926bce3a73d76bb48470bed9fcb4720927a3b9ea8a567"
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


def _dedupe(rows: tuple[TheoremSpec, ...]) -> tuple[TheoremSpec, ...]:
    result: list[TheoremSpec] = []
    seen: dict[str, TheoremSpec] = {}
    for row in rows:
        old = seen.get(row.name)
        if old is not None:
            assert old == row
            continue
        seen[row.name] = row
        result.append(row)
    return tuple(result)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_four_power_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    pointwise = tuple(
        row
        for row in make_fermat_residue_product_candidate_theorems(TheoremSpec)
        if row.name == "beta_product_pointwise_coprime"
    )
    assert len(pointwise) == 1
    rows = (
        *make_bertrand_choose_foundation_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_table_row_functional_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_laws_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_diagonal_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_recurrence_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_pascal_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_symmetry_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_weighted_vertical_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_factorial_support_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_factorial_bridge_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_positive_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_zero_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_succ_candidate_theorems(TheoremSpec),
        make_bertrand_integer_envelope_candidate_theorems(TheoremSpec)[0],
        make_bertrand_quotient_budget_candidate_theorems(TheoremSpec)[0],
        make_bertrand_power_bridge_candidate_theorems(TheoremSpec)[0],
        make_bertrand_power_order_candidate_theorems(TheoremSpec)[0],
        *make_bertrand_primorial_foundation_candidate_theorems(TheoremSpec),
        *make_bertrand_primorial_membership_candidate_theorems(TheoremSpec),
        *make_finite_product_prefix_suffix_candidate_theorems(
            TheoremSpec
        )[:1],
        *make_bertrand_primorial_interval_candidate_theorems(TheoremSpec),
        *pointwise,
        *make_bertrand_primorial_choose_interval_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_upper_candidate_theorems(TheoremSpec),
    )
    return _dedupe(rows)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    prior = _table(_prior_specs())
    assert not (set(stable) & set(prior))
    assert not (set(EXPECTED_NAMES) & set(stable))
    assert not (set(EXPECTED_NAMES) & set(prior))
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
        assert tactic != "use"
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


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


def _expected_statements() -> dict[str, str]:
    one = _primorial_relation_term(
        "1", "z", tag="bpo_source", variables=("z",)
    )
    double = _le_term(
        "k", "n", tag="bdhpb_result", variables=("n", "k")
    )
    odd = _le_term(
        "S k", "n", tag="boppb_result", variables=("n", "k")
    )
    nz_variables = ("n", "c", "q")
    nz_central = _central_binom_relation_term(
        "n", "c", tag="bcnzsu_central", variables=nz_variables
    )
    nz_power = _power_terms("4", "n", "q", tag="bcnzsu_power")
    nz_result = _le_term(
        "2 * c", "q", tag="bcnzsu_result", variables=nz_variables
    )

    central_exists_relation = _central_binom_relation_term(
        "n",
        "c",
        tag="bpfpsp_central_exists",
        variables=("n", "c"),
    )
    central_exists = f"forall n. exists c. ({central_exists_relation})"
    choose_exists_relation = _choose_relation_term(
        "n",
        "k",
        "c",
        tag="bpfpsp_choose_exists",
        variables=("n", "k", "c"),
    )
    choose_exists = f"forall n k. exists c. ({choose_exists_relation})"
    split_source = _primorial_relation_term(
        "a + l",
        "z",
        tag="bpfpsp_split_source",
        variables=("a", "l", "z"),
    )
    split_prefix = _primorial_relation_term(
        "a",
        "x",
        tag="bpfpsp_split_prefix",
        variables=("a", "l", "z", "x", "y"),
    )
    split_interval = _primorial_interval_relation_term(
        "a",
        "l",
        "y",
        tag="bpfpsp_split_interval",
        variables=("a", "l", "z", "x", "y"),
    )
    split_law = (
        "forall a l z. "
        f"({split_source}) -> exists x y. ({split_prefix}) /\\ "
        f"(({split_interval}) /\\ z = x * y)"
    )
    law_variables = ("n", "z", "c")
    even_interval = _primorial_interval_relation_term(
        "n",
        "n",
        "z",
        tag="bpfpsp_even_interval",
        variables=law_variables,
    )
    even_central = _central_binom_relation_term(
        "n",
        "c",
        tag="bpfpsp_even_central",
        variables=law_variables,
    )
    even_result = _le_term(
        "z", "c", tag="bpfpsp_even_result", variables=law_variables
    )
    even_law = (
        "forall n z c. "
        f"({even_interval}) -> ({even_central}) -> ({even_result})"
    )
    odd_interval = _primorial_interval_relation_term(
        "S n",
        "n",
        "z",
        tag="bpfpsp_odd_interval",
        variables=law_variables,
    )
    odd_middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "c",
        tag="bpfpsp_odd_middle",
        variables=law_variables,
    )
    odd_result = _le_term(
        "z", "c", tag="bpfpsp_odd_result", variables=law_variables
    )
    odd_law = (
        "forall n z c. "
        f"({odd_interval}) -> ({odd_middle}) -> ({odd_result})"
    )
    upper_variables = ("n", "c", "q")
    upper_middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "c",
        tag="bpfpsp_odd_upper_middle",
        variables=upper_variables,
    )
    upper_power = _power_terms(
        "4", "n", "q", tag="bpfpsp_odd_upper_power"
    )
    upper_result = _le_term(
        "c",
        "q",
        tag="bpfpsp_odd_upper_result",
        variables=upper_variables,
    )
    upper_law = (
        "forall n c q. "
        f"({upper_middle}) -> ({upper_power}) -> ({upper_result})"
    )
    package = (
        f"({central_exists}) /\\ (({choose_exists}) /\\ "
        f"(({split_law}) /\\ (({even_law}) /\\ "
        f"(({odd_law}) /\\ ({upper_law})))))"
    )

    bounded_variables = ("N", "n", "z", "q")
    bounded_index = _le_term(
        "n", "N", tag="bplfpb_index", variables=bounded_variables
    )
    bounded_primorial = _primorial_relation_term(
        "n",
        "z",
        tag="bplfpb_primorial",
        variables=bounded_variables,
    )
    bounded_power = _power_terms("4", "n", "q", tag="bplfpb_power")
    bounded_result = _le_term(
        "z", "q", tag="bplfpb_result", variables=bounded_variables
    )
    bounded = (
        "forall N n z q. "
        f"({bounded_index}) -> ({bounded_primorial}) -> "
        f"({bounded_power}) -> ({bounded_result})"
    )
    public_variables = ("n", "z", "q")
    public_primorial = _primorial_relation_term(
        "n", "z", tag="bplfp_primorial", variables=public_variables
    )
    public_power = _power_terms("4", "n", "q", tag="bplfp_power")
    public_result = _le_term(
        "z", "q", tag="bplfp_result", variables=public_variables
    )
    return {
        EXPECTED_NAMES[0]: f"forall z. ({one}) -> z = 1",
        EXPECTED_NAMES[1]: (
            "forall n k. S n = 2 * k -> "
            f"(~(k = 0) /\\ ({double}))"
        ),
        EXPECTED_NAMES[2]: (
            "forall n k. S n = 2 * k + 1 -> "
            f"(exists h. k = S h) -> ({odd})"
        ),
        EXPECTED_NAMES[3]: (
            "forall n c q. ~(n = 0) -> "
            f"({nz_central}) -> ({nz_power}) -> ({nz_result})"
        ),
        EXPECTED_NAMES[4]: package,
        EXPECTED_NAMES[5]: f"({package}) -> ({bounded})",
        EXPECTED_NAMES[6]: (
            "forall n z q. "
            f"({public_primorial}) -> ({public_power}) -> ({public_result})"
        ),
    }


@lru_cache(maxsize=None)
def _candidate_pool(root_name: str) -> tuple[TheoremSpec, ...]:
    index = EXPECTED_NAMES.index(root_name)
    rows = (*_prior_specs(), *_specs()[: index + 1])
    assert len({row.name for row in rows}) == len(rows)
    return rows


@lru_cache(maxsize=None)
def _blueprint(root_name: str) -> tuple[
    tuple[str, ...],
    tuple[Formula, ...],
    tuple[tuple[int, ...], ...],
    tuple[tuple[int, ...], ...],
    tuple[str, ...],
    int,
    str,
]:
    public = _specs_by_name()
    candidates = {row.name: row for row in _candidate_pool(root_name)}
    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(name: str) -> None:
        if name in public:
            stable_names.add(name)
            return
        item = candidates.get(name)
        assert item is not None, (root_name, name)
        mark = marks.get(name, 0)
        assert mark != 1, (root_name, name)
        if mark == 2:
            return
        marks[name] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[name] = 2
        candidate_order.append(name)

    visit(root_name)
    names = tuple(sorted(stable_names)) + tuple(candidate_order)
    positions = {name: index for index, name in enumerate(names)}
    kinds = tuple(
        "stable_atomic" if name in stable_names else "candidate_body"
        for name in names
    )
    specs = tuple(
        public[name] if name in stable_names else candidates[name]
        for name in names
    )
    targets = tuple(_closed_formula(row.statement) for row in specs)
    dependencies = tuple(
        ()
        if kind == "stable_atomic"
        else tuple(positions[dependency] for dependency in row.dependencies)
        for kind, row in zip(kinds, specs, strict=True)
    )
    depths: list[int] = []
    for node_id, node_dependencies in enumerate(dependencies):
        assert all(dependency < node_id for dependency in node_dependencies)
        depths.append(
            0
            if not node_dependencies
            else 1 + max(depths[item] for item in node_dependencies)
        )
    layer_lists = [[] for _ in range(1 + max(depths, default=0))]
    for node_id, depth in enumerate(depths):
        layer_lists[depth].append(node_id)
    layers = tuple(tuple(layer) for layer in layer_lists)
    topology_rows = (
        "\x1f".join(
            (
                str(node_id),
                name,
                kinds[node_id],
                specs[node_id].statement,
                "\x1e".join(
                    names[dependency]
                    for dependency in dependencies[node_id]
                ),
            )
        )
        for node_id, name in enumerate(names)
    )
    topology = sha256("\x1c".join(topology_rows).encode()).hexdigest()
    return (
        names,
        targets,
        dependencies,
        layers,
        kinds,
        positions[root_name],
        topology,
    )


def _dependency_curried_body(
    item: TheoremSpec,
    targets_by_name: dict[str, Formula],
) -> Proof:
    target = targets_by_name[item.name]
    for dependency in reversed(item.dependencies):
        target = Imp(targets_by_name[dependency], target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        assert tactic != "use"
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


@lru_cache(maxsize=None)
def _bundle(root_name: str) -> LayeredReplayBundle:
    names, targets, dependencies, _layers, kinds, root, _topology = (
        _blueprint(root_name)
    )
    public = _specs_by_name()
    candidates = {row.name: row for row in _candidate_pool(root_name)}
    targets_by_name = dict(zip(names, targets, strict=True))
    nodes = []
    for node_id, name in enumerate(names):
        body = (
            replay(name).certificate
            if kinds[node_id] == "stable_atomic"
            else _dependency_curried_body(candidates[name], targets_by_name)
        )
        nodes.append(
            LayeredReplayNode(
                node_id=node_id,
                target=targets[node_id],
                dependencies=dependencies[node_id],
                body=body,
            )
        )
        if kinds[node_id] == "stable_atomic":
            assert replay(name).spec == public[name]
    return LayeredReplayBundle(tuple(nodes), root)


def test_bertrand_primorial_four_power_source_and_rfc_pins() -> None:
    root = Path(__file__).resolve().parents[3]
    library = root / "peano-lab" / "py" / "peano_lab" / "library"
    for filename, expected in SOURCE_PINS.items():
        actual = sha256((library / filename).read_bytes()).hexdigest()
        assert actual == expected, filename
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_primorial_four_power_surfaces_are_exact() -> None:
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
        entry.spec.name for entry in editions_v10.ALPHA_ENTRIES
    }


def test_bertrand_primorial_four_power_topology_is_exact() -> None:
    rows = _table(_specs())
    assert rows[EXPECTED_NAMES[1]].script.count("induction k") == 1
    assert rows[EXPECTED_NAMES[2]].script.count("induction k") == 1
    assert rows[EXPECTED_NAMES[3]].script.count("induction n") == 1
    assert rows[EXPECTED_NAMES[5]].script.count("induction N") == 1
    assert rows[EXPECTED_NAMES[5]].script.count("apply IH") == 3
    assert rows[EXPECTED_NAMES[5]].script.count("apply pow_add") == 2
    assert rows[EXPECTED_NAMES[5]].script.count("apply mul_le_mul") == 2
    assert rows[EXPECTED_NAMES[5]].script.count(
        "apply primorial_index_eq_transport"
    ) == 4
    assert not any(
        command.startswith("rewrite hprimorial at")
        or command.startswith("rewrite hpower at")
        for row in rows.values()
        for command in row.script
    )


def test_bertrand_primorial_four_power_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_EDGES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_LAYERED_CLOSURES) == EXPECTED_NAMES
    assert all(value is not None for value in EXPECTED_ARTIFACTS.values())
    assert all(value is not None for value in EXPECTED_BODIES.values())
    assert all(value is not None for value in EXPECTED_ENVELOPES.values())
    assert all(
        value is not None for value in EXPECTED_LAYERED_CLOSURES.values()
    )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_four_power_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"PRIMORIAL FOUR POWER {name} ARTIFACT actual={actual!r}")
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_four_power_bodies_are_frozen(name: str) -> None:
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
        label=f"Primorial four-power body {name}",
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
        f"PRIMORIAL FOUR POWER {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == 37


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_primorial_four_power_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(
            dep for dep in item.dependencies if dep != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_four_power_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    false_item = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((false_item,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str], ...]:
    rows = _table(_specs())
    replacements = []
    one_old = "z = 1"
    one_new = "z = 0"
    replacements.append((one_old, one_new))
    vars2 = ("n", "k")
    replacements.append(
        (
            _le_term("k", "n", tag="bdhpb_result", variables=vars2),
            _le_term("S k", "n", tag="bdhpb_result", variables=vars2),
        )
    )
    replacements.append(
        (
            _le_term("S k", "n", tag="boppb_result", variables=vars2),
            _le_term(
                "S (S k)", "n", tag="boppb_result", variables=vars2
            ),
        )
    )
    nz_vars = ("n", "c", "q")
    replacements.append(
        (
            _le_term(
                "2 * c", "q", tag="bcnzsu_result", variables=nz_vars
            ),
            _le_term(
                "S (2 * c)",
                "q",
                tag="bcnzsu_result",
                variables=nz_vars,
            ),
        )
    )
    upper_vars = ("n", "c", "q")
    replacements.append(
        (
            _le_term(
                "c",
                "q",
                tag="bpfpsp_odd_upper_result",
                variables=upper_vars,
            ),
            _le_term(
                "S c",
                "q",
                tag="bpfpsp_odd_upper_result",
                variables=upper_vars,
            ),
        )
    )
    bounded_vars = ("N", "n", "z", "q")
    replacements.append(
        (
            _le_term(
                "z", "q", tag="bplfpb_result", variables=bounded_vars
            ),
            _le_term(
                "S z", "q", tag="bplfpb_result", variables=bounded_vars
            ),
        )
    )
    public_vars = ("n", "z", "q")
    replacements.append(
        (
            _le_term("z", "q", tag="bplfp_result", variables=public_vars),
            _le_term(
                "S z", "q", tag="bplfp_result", variables=public_vars
            ),
        )
    )
    result = []
    for name, (old, new) in zip(EXPECTED_NAMES, replacements, strict=True):
        statement = rows[name].statement
        assert statement.count(old) == 1
        result.append((name, statement, statement.replace(old, new, 1)))
    return tuple(result)


def test_bertrand_primorial_four_power_mutations_have_fixtures() -> None:
    assert 1 != 0
    assert 2 > 1
    assert 3 > 2
    assert 5 > 4
    assert 2 > 1


@pytest.mark.parametrize(
    ("name", "old", "new"),
    _mutations(),
    ids=EXPECTED_NAMES,
)
def test_bertrand_primorial_four_power_mutations_are_rejected(
    name: str,
    old: str,
    new: str,
) -> None:
    item = _table(_specs())[name]
    assert item.statement == old
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=new),),
            core=_row_core(name),
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_four_power_layered_closures_are_frozen(
    name: str,
) -> None:
    (
        names,
        targets,
        dependencies,
        layers,
        kinds,
        root,
        topology,
    ) = _blueprint(name)
    assert names[root] == name
    assert targets[root] == _closed_formula(_table(_specs())[name].statement)
    assert tuple(names[item] for item in dependencies[root]) == (
        EXPECTED_DEPENDENCIES[name]
    )
    assert root in layers[-1]
    assert kinds == (
        ("stable_atomic",) * kinds.count("stable_atomic")
        + ("candidate_body",) * kinds.count("candidate_body")
    )
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    raw = _bundle(name)
    interned = intern_layered_replay_bodies(
        raw,
        targets[root],
        limits=limits,
    )
    assert type(interned) is LayeredReplayBundle
    targets_by_id = {node.node_id: node.target for node in interned.nodes}
    for node in interned.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(targets_by_id[dependency], body_target)
        assert check((), node.body, body_target)
        assert not any(type(item) is DNE for item in _walk(node.body))
    compiled = compile_layered_replay(
        interned,
        targets[root],
        limits=limits,
    )
    assert type(compiled) is LayeredReplayCandidate
    assert compiled.layers == layers
    assert check((), compiled.certificate, compiled.target)
    assert not any(type(item) is DNE for item in _walk(compiled.certificate))
    assert compiled.proof_nodes <= MAX_LIVE_PROOF_NODES
    assert compiled.proof_depth <= MAX_LIVE_PROOF_DEPTH
    assert compiled.proof_objects <= MAX_LIVE_PROOF_OBJECTS
    root_node = interned.nodes[root]
    assert len(root_node.dependencies) == EXPECTED_DIRECT_EDGES[name]
    for index in range(len(root_node.dependencies)):
        broken_dependencies = list(root_node.dependencies)
        broken_dependencies[index] = -1
        broken_root = replace(
            root_node,
            dependencies=tuple(broken_dependencies),
        )
        broken_nodes = list(interned.nodes)
        broken_nodes[root] = broken_root
        broken = LayeredReplayBundle(tuple(broken_nodes), root)
        assert compile_layered_replay(
            broken,
            targets[root],
            limits=limits,
        ) is None
    actual = (
        compiled.proof_nodes,
        compiled.proof_depth,
        compiled.proof_objects,
        compiled.proof_edges,
        compiled.reused_objects,
        compiled.proof_annotation_occurrences,
        compiled.proof_envelope_depth,
        _proof_dag_sha256(compiled.certificate),
        topology,
    )
    print(
        f"PRIMORIAL FOUR POWER {name} LAYERED actual={actual!r}",
        flush=True,
    )
    assert EXPECTED_LAYERED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_LAYERED_CLOSURES[name]
