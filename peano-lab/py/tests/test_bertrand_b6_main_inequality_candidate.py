"""Focused strict-HA audit for the three Bertrand B6 inequality rows."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import re

import pytest

from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
)
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import bertrand_b6_main_inequality_candidate as module
from peano_lab.library.bertrand_b6_growth_candidate import (
    make_bertrand_b6_growth_candidate_theorems,
)
from peano_lab.library.bertrand_b6_main_inequality_candidate import (
    _divrem_three_relation,
    make_bertrand_b6_main_inequality_candidate_theorems,
)
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    floor_sqrt_relation,
    make_bertrand_ceil_sqrt_candidate_theorems,
)
from peano_lab.library.bertrand_hj_all_s_candidate import (
    make_bertrand_hj_all_s_candidate_theorems,
)
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_total_candidate import (
    make_bertrand_power_total_candidate_theorems,
    power_total_relation,
)
from peano_lab.library.bertrand_quotient_budget_candidate import (
    make_bertrand_quotient_budget_candidate_theorems,
    witness_le,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "bertrand_main_inequality_factorized_from_total",
    "bertrand_main_inequality_factorized",
    "bertrand_main_inequality_nat",
)

EXPECTED_DEPENDENCIES = {
    "bertrand_main_inequality_factorized_from_total": (
        "floor_sqrt_factorized_threshold_thirty_two",
        "ceil_div_six_total",
        "bertrand_hj_envelope_thirty_two",
        "floor_ceil_division_budget",
        "bertrand_floor_power_product_le_h_from_total",
        "bertrand_four_power_product_le_of_sum_from_total",
        "mul_le_mul_right",
        "le_trans",
    ),
    "bertrand_main_inequality_factorized": (
        "pow_exists",
        "bertrand_main_inequality_factorized_from_total",
    ),
    "bertrand_main_inequality_nat": (
        "two_mul_eq_add_self",
        "bertrand_main_inequality_factorized",
    ),
}

# Populated only after each candidate body has replayed in an authorized,
# isolated process.  These remain deliberately fail-closed candidate data;
# they are not empty-context closure or Stable-enrollment receipts.
EXPECTED_STATEMENTS: dict[str, tuple[int, str] | None] = {
    "bertrand_main_inequality_factorized_from_total": (
        14_319,
        "3dbc96f20375ed758b3c242486bdbc812cc84db1d893222d92d1cbd002bc005b",
    ),
    "bertrand_main_inequality_factorized": (
        8_857,
        "ab5dc2cb6163228be8ededfd38ed28afb328b83f1648449bf5d02ee12bb04c26",
    ),
    "bertrand_main_inequality_nat": (
        9_321,
        "fdc17cb51c8aa9e91beb76d8438707a565deddec59449695e34ec0d07c0adb5b",
    ),
}
EXPECTED_ARTIFACT_SHA256: dict[str, tuple[str, str] | None] = {
    "bertrand_main_inequality_factorized_from_total": (
        "2753621e73f7c92fe889885fa966c11f3703af4e26b9e0bc30097b6d9c09a89c",
        "d0a1e992bce8a34e698c5ab99afbdcf1f848e583cf6b14c4f621ceead1e2c54d",
    ),
    "bertrand_main_inequality_factorized": (
        "e07c853b7225b0c53cd7731111eceb107b9797264fc3b699deb6d2c73f8d7768",
        "239061549fc936235e11412aba4e0a81021d034525563632ab836455ab280269",
    ),
    "bertrand_main_inequality_nat": (
        "8e828d9fdaa6ec835ae1f8ae0b125cf44c6dcdb777e94bd4cfc72967baeb2fc9",
        "3c3dbee3189281f00051b332eac83b2fe40a8d7bc52980dcff27a3f1f877c288",
    ),
}
EXPECTED_BODIES: dict[str, tuple[int, int, int, int, int, int, int] | None] = {
    "bertrand_main_inequality_factorized_from_total": (
        8,
        115,
        130,
        46,
        130,
        129,
        0,
    ),
    "bertrand_main_inequality_factorized": (
        2,
        34,
        41,
        30,
        41,
        40,
        0,
    ),
    "bertrand_main_inequality_nat": (
        2,
        35,
        55,
        29,
        55,
        54,
        0,
    ),
}


def _expected_divrem_three_relation(
    dividend: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    gap = f"bmi_remainder_gap_{tag}"
    return (
        f"((({dividend}) = 3 * ({quotient}) + ({remainder})) /\\ "
        f"exists {gap}. {gap} + S ({remainder}) = 3)"
    )


def _expected_statements() -> dict[str, str]:
    factorized_total = power_total_relation(tag="b6_main_factorized")
    factorized_threshold = witness_le(
        "16 * 32", "n", tag="b6_main_factorized_threshold"
    )
    factorized_floor = floor_sqrt_relation(
        "2 * n", "s", tag="b6_main_factorized_floor"
    )
    factorized_division = _expected_divrem_three_relation(
        "2 * n",
        "q",
        "r",
        tag="b6_main_factorized_division",
    )
    factorized_a = _power_terms(
        "2 * n", "s", "A", tag="b6_main_factorized_a"
    )
    factorized_b = _power_terms(
        "4", "q", "B", tag="b6_main_factorized_b"
    )
    factorized_f = _power_terms(
        "4", "n", "F", tag="b6_main_factorized_f"
    )
    factorized_result = witness_le(
        "n * A * B", "F", tag="b6_main_factorized_result"
    )

    thin_threshold = witness_le(
        "16 * 32", "n", tag="b6_main_thin_threshold"
    )
    thin_floor = floor_sqrt_relation(
        "2 * n", "s", tag="b6_main_thin_floor"
    )
    thin_division = _expected_divrem_three_relation(
        "2 * n", "q", "r", tag="b6_main_thin_division"
    )
    thin_a = _power_terms("2 * n", "s", "A", tag="b6_main_thin_a")
    thin_b = _power_terms("4", "q", "B", tag="b6_main_thin_b")
    thin_f = _power_terms("4", "n", "F", tag="b6_main_thin_f")
    thin_result = witness_le(
        "n * A * B", "F", tag="b6_main_thin_result"
    )

    public_threshold = witness_le(
        "16 * 32", "n", tag="b6_main_public_threshold"
    )
    public_floor = floor_sqrt_relation(
        "n + n", "s", tag="b6_main_public_floor"
    )
    public_division = _expected_divrem_three_relation(
        "n + n", "q", "r", tag="b6_main_public_division"
    )
    public_a = _power_terms(
        "n + n", "s", "A", tag="b6_main_public_a"
    )
    public_b = _power_terms("4", "q", "B", tag="b6_main_public_b")
    public_f = _power_terms("4", "n", "F", tag="b6_main_public_f")
    public_result = witness_le(
        "n * A * B", "F", tag="b6_main_public_result"
    )

    return {
        "bertrand_main_inequality_factorized_from_total": (
            "forall n s q r A B F. "
            f"({factorized_total}) -> ({factorized_threshold}) -> "
            f"({factorized_floor}) -> ({factorized_division}) -> "
            f"({factorized_a}) -> ({factorized_b}) -> "
            f"({factorized_f}) -> ({factorized_result})"
        ),
        "bertrand_main_inequality_factorized": (
            "forall n s q r A B F. "
            f"({thin_threshold}) -> ({thin_floor}) -> "
            f"({thin_division}) -> ({thin_a}) -> ({thin_b}) -> "
            f"({thin_f}) -> ({thin_result})"
        ),
        "bertrand_main_inequality_nat": (
            "forall n s q r A B F. "
            f"({public_threshold}) -> ({public_floor}) -> "
            f"({public_division}) -> ({public_a}) -> ({public_b}) -> "
            f"({public_f}) -> ({public_result})"
        ),
    }


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_power_total_candidate_theorems(TheoremSpec),
        *make_bertrand_quotient_budget_candidate_theorems(TheoremSpec),
        *make_bertrand_hj_all_s_candidate_theorems(TheoremSpec),
        *make_bertrand_b6_growth_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_b6_main_inequality_candidate_theorems(TheoremSpec)


def _core() -> dict[str, TheoremSpec]:
    prior = _prior_specs()
    prior_by_name = {item.name: item for item in prior}
    assert len(prior_by_name) == len(prior)
    public = dict(_specs_by_name())
    collisions = set(public) & set(prior_by_name)
    assert all(public[name] == prior_by_name[name] for name in collisions)
    return public | {
        name: item
        for name, item in prior_by_name.items()
        if name not in public
    }


def _row_core(row_name: str) -> dict[str, TheoremSpec]:
    rows = _specs()
    index = EXPECTED_NAMES.index(row_name)
    return _core() | {item.name: item for item in rows[:index]}


def _replace_script_once(
    item: TheoremSpec,
    old: str,
    new: str | None,
) -> TheoremSpec:
    commands = list(item.script)
    index = commands.index(old)
    if new is None:
        commands.pop(index)
    else:
        commands[index] = new
    return replace(item, script=tuple(commands))


def _strict_threshold(tag: str) -> str:
    return f"exists bmi_strict_{tag}. bmi_strict_{tag} + S (16 * 32) = n"


BOUNDARY_MUTATION_CASES = (
    (
        "factorized__shift_right_factor",
        EXPECTED_NAMES[0],
        witness_le("16 * 32", "n", tag="b6_main_factorized_threshold"),
        witness_le("16 * 31", "n", tag="b6_main_factorized_threshold"),
    ),
    (
        "thin__shift_left_factor",
        EXPECTED_NAMES[1],
        witness_le("16 * 32", "n", tag="b6_main_thin_threshold"),
        witness_le("15 * 32", "n", tag="b6_main_thin_threshold"),
    ),
    (
        "public__reorder_carrier",
        EXPECTED_NAMES[2],
        witness_le("16 * 32", "n", tag="b6_main_public_threshold"),
        witness_le("32 * 16", "n", tag="b6_main_public_threshold"),
    ),
    (
        "factorized__strict_threshold",
        EXPECTED_NAMES[0],
        witness_le("16 * 32", "n", tag="b6_main_factorized_threshold"),
        _strict_threshold("factorized"),
    ),
    (
        "public__delete_threshold_factor",
        EXPECTED_NAMES[2],
        witness_le("16 * 32", "n", tag="b6_main_public_threshold"),
        witness_le("32", "n", tag="b6_main_public_threshold"),
    ),
    (
        "public__replace_floor_double",
        EXPECTED_NAMES[2],
        floor_sqrt_relation("n + n", "s", tag="b6_main_public_floor"),
        floor_sqrt_relation("2 * n", "s", tag="b6_main_public_floor"),
    ),
    (
        "public__replace_division_double",
        EXPECTED_NAMES[2],
        _expected_divrem_three_relation(
            "n + n", "q", "r", tag="b6_main_public_division"
        ),
        _expected_divrem_three_relation(
            "2 * n", "q", "r", tag="b6_main_public_division"
        ),
    ),
    (
        "public__replace_power_double",
        EXPECTED_NAMES[2],
        _power_terms("n + n", "s", "A", tag="b6_main_public_a"),
        _power_terms("2 * n", "s", "A", tag="b6_main_public_a"),
    ),
    (
        "public__right_associate_result",
        EXPECTED_NAMES[2],
        witness_le("n * A * B", "F", tag="b6_main_public_result"),
        witness_le("n * (A * B)", "F", tag="b6_main_public_result"),
    ),
    (
        "factorized__reverse_result",
        EXPECTED_NAMES[0],
        witness_le("n * A * B", "F", tag="b6_main_factorized_result"),
        witness_le("F", "n * A * B", tag="b6_main_factorized_result"),
    ),
)

TRANSPORT_SCRIPT_MUTATIONS = (
    (
        "floor__reverse_equality_direction",
        "rewrite <- hdouble at hfloor",
        "rewrite hdouble at hfloor",
    ),
    (
        "floor__delete_one_rewrite",
        "rewrite <- hdouble at hfloor",
        None,
    ),
    (
        "division__reverse_equality_direction",
        "rewrite <- hdouble at hdiv",
        "rewrite hdouble at hdiv",
    ),
    (
        "division__delete_rewrite",
        "rewrite <- hdouble at hdiv",
        None,
    ),
    (
        "power__reverse_equality_direction",
        "rewrite <- hdouble at hA",
        "rewrite hdouble at hA",
    ),
    (
        "power__delete_one_rewrite",
        "rewrite <- hdouble at hA",
        None,
    ),
)


def test_b6_main_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_b6_main_inequality_candidate_theorems(
        TheoremSpec
    ) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == (
        EXPECTED_DEPENDENCIES
    )
    assert {item.name: item.statement for item in specs} == (
        _expected_statements()
    )

    public = dict(_specs_by_name())
    prior = {item.name for item in _prior_specs()}
    assert not ({item.name for item in specs} & set(public))
    assert not ({item.name for item in specs} & prior)
    _core()
    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            marker not in item.statement
            for marker in (
                "PowTotal",
                "FloorSqrt(",
                "DivRem(",
                "Pow(",
                "Le(",
                "<=",
                "^",
                "DNE",
            )
        )


def test_b6_main_factorized_carrier_and_left_association_are_exact() -> None:
    specs = {item.name: item for item in _specs()}
    for item in specs.values():
        assert item.statement.count("16 * 32") == 1
        assert "16 * 31" not in item.statement
        assert "15 * 32" not in item.statement
        assert "32 * 16" not in item.statement
        assert "n * (A * B)" not in item.statement
        assert "n * A * B" in item.statement
        assert "512" not in item.statement
        assert all("512" not in command for command in item.script)

    source = Path(module.__file__).read_text(encoding="utf-8")
    assert re.search(r"(?<![A-Za-z0-9_])512(?![A-Za-z0-9_])", source) is None
    assert module.__all__ == [
        "make_bertrand_b6_main_inequality_candidate_theorems"
    ]


def test_b6_main_public_surface_has_exactly_five_checked_transports() -> None:
    specs = {item.name: item for item in _specs()}
    public = specs["bertrand_main_inequality_nat"]
    assert public.statement.count("n + n") == 5
    assert public.statement.count("2 * n") == 0
    assert public.script.count("rewrite <- hdouble at hfloor") == 2
    assert public.script.count("rewrite <- hdouble at hdiv") == 1
    assert public.script.count("rewrite <- hdouble at hA") == 2
    assert sum(
        command.startswith("rewrite") and "hdouble" in command
        for command in public.script
    ) == 5
    assert public.dependencies == (
        "two_mul_eq_add_self",
        "bertrand_main_inequality_factorized",
    )


def test_b6_main_private_divrem_three_expander_is_hygienic() -> None:
    relation = _divrem_three_relation(
        "n + n", "q", "r", tag="public_hygiene"
    )
    assert relation.count("n + n") == 1
    assert relation == _expected_divrem_three_relation(
        "n + n", "q", "r", tag="public_hygiene"
    )
    with pytest.raises(ValueError):
        _divrem_three_relation("n +", "q", "r", tag="bad_term")
    with pytest.raises(ValueError):
        _divrem_three_relation("n", "q", "r", tag="bad-tag")
    with pytest.raises(ValueError):
        _divrem_three_relation(
            "bmi_remainder_gap_capture",
            "q",
            "r",
            tag="capture",
        )


def test_b6_main_scripts_are_constructive_and_deterministic() -> None:
    first = _specs()
    second = make_bertrand_b6_main_inequality_candidate_theorems(TheoremSpec)
    assert tuple(item.script for item in first) == tuple(
        item.script for item in second
    )
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


def test_b6_main_static_manifests_are_fail_closed() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_STATEMENTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACT_SHA256) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert all(
        EXPECTED_BODIES[name] is None
        or len(EXPECTED_BODIES[name]) == 7
        for name in EXPECTED_NAMES
    )
    for case_id, row_name, old, new in BOUNDARY_MUTATION_CASES:
        assert case_id
        assert row_name in EXPECTED_NAMES
        assert old != new
        assert _expected_statements()[row_name].count(old) == 1


def test_b6_main_exact_hashes_are_frozen_after_authorized_replay() -> None:
    if any(EXPECTED_STATEMENTS[name] is None for name in EXPECTED_NAMES):
        pytest.skip("exact hashes await the authorized isolated body audit")
    if any(EXPECTED_ARTIFACT_SHA256[name] is None for name in EXPECTED_NAMES):
        pytest.skip("artifact hashes await the authorized isolated body audit")

    specs = _specs()
    assert {
        item.name: (
            len(item.statement),
            sha256(item.statement.encode()).hexdigest(),
        )
        for item in specs
    } == EXPECTED_STATEMENTS
    assert {
        item.name: (
            sha256("\0".join(item.script).encode()).hexdigest(),
            sha256(
                "\0".join((item.statement, *item.dependencies)).encode()
            ).hexdigest(),
        )
        for item in specs
    } == EXPECTED_ARTIFACT_SHA256


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_b6_main_candidate_only_body_receipts(
    row_name: str,
) -> None:
    expected = EXPECTED_BODIES[row_name]
    if expected is None:
        pytest.skip("candidate-only receipt awaits isolated replay")

    index = EXPECTED_NAMES.index(row_name)
    receipt = replay_candidate_bodies(
        _specs()[: index + 1], core=_core()
    )[-1]
    actual = (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    )
    assert receipt.name == row_name
    assert actual == expected
    assert receipt.proof_nodes <= MAX_LIVE_PROOF_NODES
    assert receipt.proof_depth <= MAX_LIVE_PROOF_DEPTH
    assert receipt.proof_objects <= MAX_LIVE_PROOF_OBJECTS


@pytest.mark.parametrize(
    ("row_name", "dependency"),
    tuple(
        (row_name, dependency)
        for row_name, dependencies in EXPECTED_DEPENDENCIES.items()
        for dependency in dependencies
    ),
)
def test_b6_main_every_direct_dependency_is_live(
    row_name: str,
    dependency: str,
) -> None:
    item = {spec.name: spec for spec in _specs()}[row_name]
    shortened = replace(
        item,
        dependencies=tuple(
            name for name in item.dependencies if name != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(row_name))


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_b6_main_false_conclusions_are_rejected(row_name: str) -> None:
    item = {spec.name: spec for spec in _specs()}[row_name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(row_name))


@pytest.mark.parametrize(
    ("case_id", "row_name", "old", "new"),
    BOUNDARY_MUTATION_CASES,
    ids=tuple(case[0] for case in BOUNDARY_MUTATION_CASES),
)
def test_b6_main_boundary_mutations_are_rejected(
    case_id: str,
    row_name: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = {spec.name: spec for spec in _specs()}[row_name]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(row_name))


@pytest.mark.parametrize(
    ("case_id", "old", "new"),
    TRANSPORT_SCRIPT_MUTATIONS,
    ids=tuple(case[0] for case in TRANSPORT_SCRIPT_MUTATIONS),
)
def test_b6_main_public_transport_corruptions_are_rejected(
    case_id: str,
    old: str,
    new: str | None,
) -> None:
    del case_id
    item = {spec.name: spec for spec in _specs()}[
        "bertrand_main_inequality_nat"
    ]
    mutated = _replace_script_once(item, old, new)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (mutated,), core=_row_core("bertrand_main_inequality_nat")
        )
