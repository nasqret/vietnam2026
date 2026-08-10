"""Focused strict-HA scaffold for the all-root Bertrand H/J package.

The six theorem surfaces and their dependency order are frozen here before
any expensive replay is attempted.  ``16*32`` is intentionally the native
threshold carrier; its value 512 is checked below only by host arithmetic and
is never proof authority.  Statement, artifact, and body receipts are frozen
only from successful isolated gates; recursive closure remains pending.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    floor_sqrt_relation,
    make_bertrand_ceil_sqrt_candidate_theorems,
)
from peano_lab.library.bertrand_floor_sqrt_total_candidate import (
    make_bertrand_floor_sqrt_total_candidate_theorems,
)
from peano_lab.library.bertrand_hj_all_s_candidate import (
    make_bertrand_hj_all_s_candidate_theorems,
)
from peano_lab.library.bertrand_hj_base_thirty_two_candidate import (
    make_bertrand_hj_base_thirty_two_candidate_theorems,
)
from peano_lab.library.bertrand_hj_transport_candidate import (
    make_bertrand_hj_transport_candidate_theorems,
)
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.bertrand_power_total_candidate import (
    make_bertrand_power_total_candidate_theorems,
    power_total_relation,
)
from peano_lab.library.bertrand_quotient_budget_candidate import (
    make_bertrand_quotient_budget_candidate_theorems,
    witness_le,
)
from peano_lab.library.bertrand_threshold_base_candidate import (
    make_bertrand_threshold_base_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "scaled_factor_square_identity",
    "thirty_two_square_eq_twice_sixteen_times_thirty_two",
    "floor_sqrt_factorized_threshold_thirty_two",
    "six_block_window_decomposition_above_thirty_two",
    "bertrand_hj_six_block_iterate_from_total",
    "bertrand_hj_envelope_thirty_two",
)

EXPECTED_DEPENDENCIES = {
    "scaled_factor_square_identity": ("mul_assoc",),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        "scaled_factor_square_identity",
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        "thirty_two_square_eq_twice_sixteen_times_thirty_two",
        "zero_add",
        "square_lt_successor_square",
        "mul_le_mul_left",
        "floor_sqrt_monotone",
    ),
    "six_block_window_decomposition_above_thirty_two": (
        "division_remainder_exists",
        "succ_ne_zero",
        "le_of_succ_le_succ",
        "le_add_right",
        "add_le_add_left",
        "add_assoc",
        "add_comm",
    ),
    "bertrand_hj_six_block_iterate_from_total": (
        "bertrand_hj_base_window_thirty_two_from_total",
        "bertrand_hj_six_step_from_total",
        "ceil_div_six_total",
        "le_add_right",
        "le_trans",
        "mul_add",
        "add_assoc",
    ),
    "bertrand_hj_envelope_thirty_two": (
        "pow_exists",
        "six_block_window_decomposition_above_thirty_two",
        "bertrand_hj_six_block_iterate_from_total",
    ),
}


def _threshold_statement() -> str:
    return (
        "forall n s. "
        f"({witness_le('16 * 32', 'n', tag='hjas_threshold_input')}) -> "
        f"({floor_sqrt_relation('2 * n', 's', tag='hjas_threshold_floor')}) -> "
        f"({witness_le('32', 's', tag='hjas_threshold_result')})"
    )


def _decomposition_statement() -> str:
    lower = witness_le("32", "b", tag="hjas_decomposition_base_lower")
    upper = witness_le("b", "37", tag="hjas_decomposition_base_upper")
    return (
        "forall s. "
        f"({witness_le('32', 's', tag='hjas_decomposition_source')}) -> "
        f"exists b k. ((({lower}) /\\ ({upper})) /\\ s = b + 6 * k)"
    )


def _iterator_statement() -> str:
    root = "b + 6 * k"
    ceiling = ceil_div_six_relation(
        f"({root}) * ({root})", "e", tag="hjas_iterator_ceiling"
    )
    h_power = _power_terms(
        f"({root}) + 1",
        f"2 * ({root}) + 2",
        "h",
        tag="hjas_iterator_h",
    )
    h_bound = _power_terms("4", "e", "u", tag="hjas_iterator_h_bound")
    j_power = _power_terms(
        f"({root}) + 7", "12", "j", tag="hjas_iterator_j"
    )
    j_bound = _power_terms(
        "4", f"({root}) + 5", "g", tag="hjas_iterator_j_bound"
    )
    h_result = witness_le("h", "u", tag="hjas_iterator_h_result")
    j_result = witness_le("j", "g", tag="hjas_iterator_j_result")
    return (
        "forall b. "
        f"({power_total_relation(tag='hjas_iterator')}) -> "
        f"({witness_le('32', 'b', tag='hjas_iterator_base_lower')}) -> "
        f"({witness_le('b', '37', tag='hjas_iterator_base_upper')}) -> "
        "forall k e h u j g. "
        f"({ceiling}) -> ({h_power}) -> ({h_bound}) -> "
        f"({j_power}) -> ({j_bound}) -> "
        f"((({h_result}) /\\ ({j_result})))"
    )


def _envelope_statement() -> str:
    ceiling = ceil_div_six_relation("s * s", "e", tag="hjas_envelope_ceiling")
    h_power = _power_terms(
        "s + 1", "2 * s + 2", "h", tag="hjas_envelope_h"
    )
    h_bound = _power_terms("4", "e", "u", tag="hjas_envelope_h_bound")
    j_power = _power_terms("s + 7", "12", "j", tag="hjas_envelope_j")
    j_bound = _power_terms("4", "s + 5", "g", tag="hjas_envelope_j_bound")
    h_result = witness_le("h", "u", tag="hjas_envelope_h_result")
    j_result = witness_le("j", "g", tag="hjas_envelope_j_result")
    return (
        "forall s e h u j g. "
        f"({witness_le('32', 's', tag='hjas_envelope_lower')}) -> "
        f"({ceiling}) -> ({h_power}) -> ({h_bound}) -> "
        f"({j_power}) -> ({j_bound}) -> "
        f"((({h_result}) /\\ ({j_result})))"
    )


EXPECTED_SURFACES = {
    "scaled_factor_square_identity": (
        "forall c d a. a = c * d -> a * a = c * (d * a)"
    ),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        "32 * 32 = 2 * (16 * 32)"
    ),
    "floor_sqrt_factorized_threshold_thirty_two": _threshold_statement(),
    "six_block_window_decomposition_above_thirty_two": (
        _decomposition_statement()
    ),
    "bertrand_hj_six_block_iterate_from_total": _iterator_statement(),
    "bertrand_hj_envelope_thirty_two": _envelope_statement(),
}

# Every receipt class requires isolated execution.  The unskipped readiness
# test below fails for each pending class, so the still-pending closure gate
# cannot be mistaken for a completed candidate audit.
PENDING_CANDIDATE_ONLY = "PENDING_CANDIDATE_ONLY_ISOLATED_AUDIT"
EXPECTED_STATEMENTS: dict[str, tuple[int, str]] | str = {
    "scaled_factor_square_identity": (
        46,
        "62d09740def9373ccc36fa4952c3bf1712c8e627fc215e841b329f9b291a3b8b",
    ),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        23,
        "1956cceff6dca8891691473c37f03d16b21ddba5e96f453c927387edd3045492",
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        433,
        "8ffc7797e2501d7a6202f6f0212ebd96b42b406b0045ab2eb353627adf8a452e",
    ),
    "six_block_window_decomposition_above_thirty_two": (
        355,
        "bccb76e88db4f479d9d7bc946efeaee34e2b34ad16d091db3b593fe1d45a5b9a",
    ),
    "bertrand_hj_six_block_iterate_from_total": (
        16_717,
        "ddf4cf517f3f775e0d2063ba6385a9a388943d708f90d27cfe3c082df6f02095",
    ),
    "bertrand_hj_envelope_thirty_two": (
        12_794,
        "6eb3d0386aad3792f827c0c93ccc7581400634cfa2d264dee5aae562bc146a6f",
    ),
}

# Successful isolated observations are retained here in theorem order.  The
# full table is promoted below only because all six body gates are now green.
CHECKPOINT_BODY_RECEIPTS: dict[
    str, tuple[int, int, int, int, int, int, int]
] = {
    "scaled_factor_square_identity": (1, 6, 12, 10, 12, 11, 0),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        1,
        7,
        339,
        59,
        339,
        338,
        0,
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        5,
        27,
        34,
        17,
        34,
        33,
        0,
    ),
    "six_block_window_decomposition_above_thirty_two": (
        7,
        57,
        137,
        53,
        137,
        136,
        0,
    ),
    "bertrand_hj_six_block_iterate_from_total": (
        7,
        177,
        2_388,
        96,
        1_986,
        2_387,
        402,
    ),
    "bertrand_hj_envelope_thirty_two": (
        3,
        68,
        102,
        36,
        102,
        101,
        0,
    ),
}
EXPECTED_BODIES: (
    dict[str, tuple[int, int, int, int, int, int, int]] | str
) = dict(CHECKPOINT_BODY_RECEIPTS)
EXPECTED_ARTIFACT_SHA256: dict[str, tuple[str, str]] | str = {
    "scaled_factor_square_identity": (
        "9b1b24c8a7483be234aed26af7e4722b6a1d518e20f058f908b5d17d6bcb1a40",
        "c83bbf482315783db9f0c28042228428e3951c70820474f0af673f13f9e63b86",
    ),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        "19ad9b11be26805e4f3430c099c32a0da2ab11cfc6e8f1307e2afad7198881ec",
        "6f199664eacb96193a0291d2629fc895f641fdb038949ad887e2e8b08d10fb4b",
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        "f088ea48bfe2a3ad62791729743ffd804d2cf4fb54a54ca63d1e6a461108e0c0",
        "ea4b7cfeba6afa11591683bbd8f972259df59b4fc2e76070b86e3a4ab0d07c65",
    ),
    "six_block_window_decomposition_above_thirty_two": (
        "23441fc82fee1af689013ffc9f0457f6f0ebb821f33bc89038b93edc983db558",
        "070fdbbc018d091582a71769967c90712bf8090a81e7d2025a427ae8b15c11d3",
    ),
    "bertrand_hj_six_block_iterate_from_total": (
        "2e6f41166070f330f912d5c01923c97562f6b8239182391ff525facc520c2768",
        "647620ce8053ea7381a3575a345d295b2e6d26b16d93ea358d820ab9a2b9c32d",
    ),
    "bertrand_hj_envelope_thirty_two": (
        "cccc5ad9c8e22fbb6e9a5ee7cdfea4268f21f339eabf0d7a47344724d177fbea",
        "6d83e785bc4f0965be8aa658f4fede1a0d15c0a507836527c30883e91680bf15",
    ),
}
EXPECTED_CLOSURES: dict[str, tuple[int, int, int, int, int]] | str = (
    PENDING_CANDIDATE_ONLY
)

STATEMENT_RECEIPTS_READY = isinstance(EXPECTED_STATEMENTS, dict)
BODY_RECEIPTS_READY = isinstance(EXPECTED_BODIES, dict)
ARTIFACT_RECEIPTS_READY = isinstance(EXPECTED_ARTIFACT_SHA256, dict)
REPLAY_AUDIT_READY = (
    STATEMENT_RECEIPTS_READY
    and BODY_RECEIPTS_READY
    and ARTIFACT_RECEIPTS_READY
)

LIVENESS_CASES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
FALSE_TARGET_CASES = EXPECTED_NAMES

BOUNDARY_MUTATION_CASES = (
    (
        "scaled_identity__boundary__successor_square",
        "scaled_factor_square_identity",
        "a * a = c * (d * a)",
        "S (a * a) = c * (d * a)",
    ),
    (
        "factorized_bridge__boundary__factor_three",
        "thirty_two_square_eq_twice_sixteen_times_thirty_two",
        "32 * 32 = 2 * (16 * 32)",
        "32 * 32 = 3 * (16 * 32)",
    ),
    (
        "threshold__boundary__root_thirty_three",
        "floor_sqrt_factorized_threshold_thirty_two",
        witness_le("32", "s", tag="hjas_threshold_result"),
        witness_le("33", "s", tag="hjas_threshold_result"),
    ),
    (
        "decomposition__boundary__upper_thirty_six",
        "six_block_window_decomposition_above_thirty_two",
        witness_le("b", "37", tag="hjas_decomposition_base_upper"),
        witness_le("b", "36", tag="hjas_decomposition_base_upper"),
    ),
    (
        "iterator__boundary__reverse_h_result",
        "bertrand_hj_six_block_iterate_from_total",
        witness_le("h", "u", tag="hjas_iterator_h_result"),
        witness_le("u", "h", tag="hjas_iterator_h_result"),
    ),
    (
        "envelope__boundary__reverse_j_result",
        "bertrand_hj_envelope_thirty_two",
        witness_le("j", "g", tag="hjas_envelope_j_result"),
        witness_le("g", "j", tag="hjas_envelope_j_result"),
    ),
)

EXPECTED_MANIFEST_COUNTS = {
    "theorems": 6,
    "declared_dependencies": 24,
    "liveness_cases": 24,
    "false_target_cases": 6,
    "boundary_mutation_cases": 6,
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec),
        *make_bertrand_quotient_budget_candidate_theorems(TheoremSpec),
        *make_bertrand_threshold_base_candidate_theorems(TheoremSpec),
        *make_bertrand_power_total_candidate_theorems(TheoremSpec),
        *make_bertrand_hj_transport_candidate_theorems(TheoremSpec),
        *make_bertrand_hj_base_thirty_two_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_hj_all_s_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = (*_prior_specs(), *_specs())
    assert len({row.name for row in rows}) == len(rows)
    return {row.name: row for row in rows}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


def test_hj_all_s_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_hj_all_s_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: item.statement for item in specs} == EXPECTED_SURFACES

    public = _specs_by_name()
    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert item.name not in public
        assert all(
            token not in item.statement
            for token in (
                "Pow(",
                "PowTotal",
                "CeilDivSix(",
                "FloorSqrt(",
                "^",
                "**",
                "<=",
            )
        )


def test_hj_all_s_threshold_retains_the_factorized_native_carrier() -> None:
    specs = {item.name: item for item in _specs()}
    identity = specs["scaled_factor_square_identity"]
    bridge = specs["thirty_two_square_eq_twice_sixteen_times_thirty_two"]
    threshold = specs["floor_sqrt_factorized_threshold_thirty_two"]
    assert identity.statement == (
        "forall c d a. a = c * d -> a * a = c * (d * a)"
    )
    assert bridge.statement == "32 * 32 = 2 * (16 * 32)"
    assert threshold.statement == _threshold_statement()
    for item in specs.values():
        assert "512" not in item.statement
        assert all("512" not in command for command in item.script)


def test_hj_all_s_threshold_value_is_host_regression_only() -> None:
    # This standard-natural calculation documents the RFC representation; it
    # is neither imported into a native proof nor accepted as kernel authority.
    assert 16 * 32 == 512
    assert 32 * 32 == 2 * (16 * 32)


def test_hj_all_s_block_surfaces_preserve_one_total_then_discharge_it() -> None:
    specs = {item.name: item for item in _specs()}
    decomposition = specs["six_block_window_decomposition_above_thirty_two"]
    iterator = specs["bertrand_hj_six_block_iterate_from_total"]
    envelope = specs["bertrand_hj_envelope_thirty_two"]

    assert decomposition.statement == _decomposition_statement()
    total = power_total_relation(tag="hjas_iterator")
    assert iterator.statement == _iterator_statement()
    assert iterator.statement.count(total) == 1
    assert envelope.statement == _envelope_statement()
    assert "bpt_a_" not in envelope.statement
    assert envelope.dependencies[0] == "pow_exists"
    assert sum(command.startswith("have htotal :") for command in envelope.script) == 1


def test_hj_all_s_scripts_are_constructive_and_deterministic() -> None:
    first = _specs()
    second = make_bertrand_hj_all_s_candidate_theorems(TheoremSpec)
    assert tuple(item.script for item in first) == tuple(item.script for item in second)
    for item in first:
        assert all(
            forbidden not in command
            for command in item.script
            for forbidden in (
                "DNE",
                "classical",
                "by_contra",
                "sorry",
                "auto",
                "compact_arith",
                "ring",
            )
        )


def test_hj_all_s_static_audit_manifests_are_frozen() -> None:
    assert len(EXPECTED_NAMES) == EXPECTED_MANIFEST_COUNTS["theorems"]
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(CHECKPOINT_BODY_RECEIPTS) == EXPECTED_NAMES
    assert all(len(receipt) == 7 for receipt in CHECKPOINT_BODY_RECEIPTS.values())
    assert sum(len(row) for row in EXPECTED_DEPENDENCIES.values()) == (
        EXPECTED_MANIFEST_COUNTS["declared_dependencies"]
    )
    assert len(LIVENESS_CASES) == EXPECTED_MANIFEST_COUNTS["liveness_cases"]
    assert len(FALSE_TARGET_CASES) == (
        EXPECTED_MANIFEST_COUNTS["false_target_cases"]
    )
    assert len(BOUNDARY_MUTATION_CASES) == (
        EXPECTED_MANIFEST_COUNTS["boundary_mutation_cases"]
    )

    liveness_ids = tuple(
        f"{name}__without__{dependency}"
        for name, dependency in LIVENESS_CASES
    )
    false_ids = tuple(f"{name}__false_target" for name in FALSE_TARGET_CASES)
    boundary_ids = tuple(case_id for case_id, *_rest in BOUNDARY_MUTATION_CASES)
    for ids in (liveness_ids, false_ids, boundary_ids):
        assert len(ids) == len(set(ids))
    all_ids = (*liveness_ids, *false_ids, *boundary_ids)
    assert len(all_ids) == len(set(all_ids))

    surfaces = {item.name: item.statement for item in _specs()}
    for _case_id, name, old, new in BOUNDARY_MUTATION_CASES:
        assert old != new
        assert old in surfaces[name]
        assert surfaces[name].replace(old, new, 1) != surfaces[name]


@pytest.mark.parametrize(
    ("receipt_class", "receipts"),
    (
        ("statement fingerprints", EXPECTED_STATEMENTS),
        ("body receipts", EXPECTED_BODIES),
        ("script/logical-spec fingerprints", EXPECTED_ARTIFACT_SHA256),
        ("closure receipts", EXPECTED_CLOSURES),
    ),
    ids=("statements", "bodies", "artifacts", "closures"),
)
def test_hj_all_s_candidate_only_receipt_gate_is_fail_closed(
    receipt_class: str,
    receipts: object,
) -> None:
    assert receipts != PENDING_CANDIDATE_ONLY, (
        f"{receipt_class} remain candidate-only pending; run their isolated "
        "audit before admission"
    )
    assert isinstance(receipts, dict)
    assert tuple(receipts) == EXPECTED_NAMES


@pytest.mark.skipif(
    not STATEMENT_RECEIPTS_READY,
    reason="statement fingerprints await the first successful isolated replay",
)
def test_hj_all_s_statement_fingerprints_are_frozen() -> None:
    assert isinstance(EXPECTED_STATEMENTS, dict)
    assert {
        item.name: (len(item.statement), sha256(item.statement.encode()).hexdigest())
        for item in _specs()
    } == EXPECTED_STATEMENTS


@pytest.mark.skipif(
    not ARTIFACT_RECEIPTS_READY,
    reason="script/logical-spec fingerprints await isolated factory inspection",
)
def test_hj_all_s_script_and_logical_spec_fingerprints_are_frozen() -> None:
    assert isinstance(EXPECTED_ARTIFACT_SHA256, dict)
    assert {
        item.name: (
            sha256("\0".join(item.script).encode()).hexdigest(),
            sha256(
                "\0".join((item.statement, *item.dependencies)).encode()
            ).hexdigest(),
        )
        for item in _specs()
    } == EXPECTED_ARTIFACT_SHA256


@pytest.mark.skipif(
    not isinstance(EXPECTED_CLOSURES, dict),
    reason="closure receipts remain a later candidate-only isolated gate",
)
def test_hj_all_s_closure_receipts_require_the_isolated_closure_gate() -> None:
    assert isinstance(EXPECTED_CLOSURES, dict)
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    pytest.fail(
        "candidate-only closure receipts are not admissible until the isolated "
        "closure validator is wired"
    )


@pytest.mark.skipif(
    not REPLAY_AUDIT_READY,
    reason="body receipts await the first successful isolated replay",
)
@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_hj_all_s_bodies_are_constructive(name: str) -> None:
    assert isinstance(EXPECTED_BODIES, dict)
    item = next(item for item in _specs() if item.name == name)
    receipt = replay_candidate_bodies((item,), core=_available())[0]
    assert (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    ) == EXPECTED_BODIES[name]


@pytest.mark.skipif(
    not REPLAY_AUDIT_READY,
    reason="dependency liveness awaits the first successful isolated replay",
)
@pytest.mark.parametrize(
    ("name", "dependency"),
    LIVENESS_CASES,
    ids=[f"{name}__without__{dependency}" for name, dependency in LIVENESS_CASES],
)
def test_hj_all_s_every_declared_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = next(item for item in _specs() if item.name == name)
    shortened = replace(
        item,
        dependencies=tuple(
            candidate for candidate in item.dependencies if candidate != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_available())


@pytest.mark.skipif(
    not REPLAY_AUDIT_READY,
    reason="negative replay awaits the first successful isolated replay",
)
@pytest.mark.parametrize(
    "name",
    FALSE_TARGET_CASES,
    ids=[f"{name}__false_target" for name in FALSE_TARGET_CASES],
)
def test_hj_all_s_false_target_is_rejected(name: str) -> None:
    item = next(item for item in _specs() if item.name == name)
    false_contract = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((false_contract,), core=_available())


@pytest.mark.skipif(
    not REPLAY_AUDIT_READY,
    reason="boundary mutations await the first successful isolated replay",
)
@pytest.mark.parametrize(
    ("case_id", "name", "old", "new"),
    BOUNDARY_MUTATION_CASES,
    ids=[case_id for case_id, *_rest in BOUNDARY_MUTATION_CASES],
)
def test_hj_all_s_boundary_mutation_is_rejected(
    case_id: str,
    name: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = next(item for item in _specs() if item.name == name)
    assert old in item.statement
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    assert mutated.statement != item.statement
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_available())
