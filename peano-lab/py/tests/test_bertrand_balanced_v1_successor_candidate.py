"""Focused fail-closed audit for the additive balanced-v1 successor package.

The audit pins every source from which a successor is derived, proves that
Alpha-v7 rows remain byte-identical, and permits only the declared theorem
name/dependency/script-token deltas.  Manifest hashes and body receipts start
as explicit pending gates; neither a factory observation nor a body receipt
is theorem authority.
"""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.library import (
    alpha_enrollment_v7,
    bertrand_balanced_v1_successor_candidate as successor_provider,
    bertrand_hj_all_s_candidate as all_s_provider,
    bertrand_hj_base_thirty_two_candidate as base_thirty_two_provider,
    bertrand_hj_transport_candidate as transport_provider,
    bertrand_power_seed_balanced_candidate as balanced_seed_provider,
    bertrand_power_total_candidate as power_total_provider,
    editions_v7,
)
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    make_bertrand_ceil_sqrt_candidate_theorems,
)
from peano_lab.library.bertrand_floor_sqrt_total_candidate import (
    make_bertrand_floor_sqrt_total_candidate_theorems,
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
from peano_lab.library.bertrand_quotient_budget_candidate import (
    make_bertrand_quotient_budget_candidate_theorems,
)
from peano_lab.library.bertrand_threshold_base_candidate import (
    make_bertrand_threshold_base_candidate_theorems,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _specs_by_name,
)


SQUARE_HELPER_NAME = "eight_times_eight_eq_sixty_four"
PRODUCT_HELPER_NAME = "eight_times_sixteen_eq_one_twenty_eight"
OLD_SEED_NAME = "pow_two_seed_bundle_from_total"
BALANCED_V1_SEED_NAME = "pow_two_seed_bundle_balanced_v1_from_total"

OLD_H_TRANSPORT_NAME = "bertrand_h_six_step_transport_from_total"
OLD_J_TRANSPORT_NAME = "bertrand_j_six_step_transport_from_total"
OLD_COMBINED_TRANSPORT_NAME = "bertrand_hj_six_step_from_total"
BALANCED_V1_H_TRANSPORT_NAME = (
    "bertrand_h_six_step_transport_balanced_v1_from_total"
)
BALANCED_V1_J_TRANSPORT_NAME = (
    "bertrand_j_six_step_transport_balanced_v1_from_total"
)
BALANCED_V1_COMBINED_TRANSPORT_NAME = (
    "bertrand_hj_six_step_balanced_v1_from_total"
)

BASE_THIRTY_TWO_REPLACEMENT_NAMES = (
    "pow_eleven_two_le_pow_two_seven_from_total",
    "pow_six_ten_le_pow_four_thirteen_from_total",
    "pow_six_six_le_pow_four_eight_from_total",
    "pow_six_four_le_pow_four_six_from_total",
    "pow_two_double_eq_pow_four_from_total",
)
ITERATOR_REPLACEMENT_NAME = "bertrand_hj_six_block_iterate_from_total"

EXPECTED_NAMES = (
    SQUARE_HELPER_NAME,
    PRODUCT_HELPER_NAME,
    BALANCED_V1_SEED_NAME,
    BALANCED_V1_H_TRANSPORT_NAME,
    BALANCED_V1_J_TRANSPORT_NAME,
    BALANCED_V1_COMBINED_TRANSPORT_NAME,
    *BASE_THIRTY_TWO_REPLACEMENT_NAMES,
    ITERATOR_REPLACEMENT_NAME,
)

EXPECTED_SOURCE_SHA256 = {
    balanced_seed_provider: (
        "76f290ee51d70fe62b14d81777488f5823050597249a9aa1beafcfdaad894eab"
    ),
    power_total_provider: (
        "6fbccade6d6d347ca11a6f8ace061dad56202bf733959ed40990e1dd21630410"
    ),
    transport_provider: (
        "6635abd33044e290ef9eb1224cde26bc0154d5e58f609aa259e6fe16d757afe3"
    ),
    base_thirty_two_provider: (
        "2ca24de2693a8bb32bfb999fdb9602460bdce16dd5ce94f64c59d2a06f4a2386"
    ),
    all_s_provider: (
        "1dd96d72ff5d548dc6d8eb71cdcec58d151dd6632c45301e528a1cb2c9a6f31a"
    ),
    editions_v7: (
        "c9db901c52b92380cb077730b2827cfc7de393160e1301db5f4df18a26f0383c"
    ),
    alpha_enrollment_v7: (
        "38d61bfd64598044ad344f3139d266f0f40f9d38b9a54b4967abe2df46bca9fe"
    ),
    successor_provider: (
        "852f3dc63a0bd6e80dccee70046c628e1929ae3e08bb200a016d25e1429d5b7b"
    ),
}

PENDING_MANIFEST_HASHES = "PENDING_BALANCED_V1_MANIFEST_HASHES"
EXPECTED_MANIFEST_HASHES: dict[str, str] | str = {
    "script_sha256": (
        "0cdb8d835b263537843d09014eb6eacf141a6fe9a9d3cbac9e873951ffeb74c7"
    ),
    "logical_sha256": (
        "26ef14eee1a037dcfd4a22377ec6654b85320c4f78c12ab97dd596381b11d661"
    ),
}

PENDING_BODY_RECEIPT = "PENDING_BALANCED_V1_BODY_RECEIPT"
EXPECTED_BODY_RECEIPTS: dict[
    str, tuple[int, int, int, int, int, int, int] | str
] = {
    SQUARE_HELPER_NAME: (0, 82, 397, 84, 397, 396, 0),
    PRODUCT_HELPER_NAME: (2, 77, 408, 74, 408, 407, 0),
    BALANCED_V1_SEED_NAME: (4, 61, 770, 41, 705, 769, 65),
    BALANCED_V1_H_TRANSPORT_NAME: (13, 201, 800, 116, 692, 799, 108),
    BALANCED_V1_J_TRANSPORT_NAME: (11, 113, 637, 101, 576, 636, 61),
    BALANCED_V1_COMBINED_TRANSPORT_NAME: (2, 64, 82, 49, 82, 81, 0),
    "pow_eleven_two_le_pow_two_seven_from_total": (
        9,
        121,
        1383,
        97,
        1383,
        1382,
        0,
    ),
    "pow_six_ten_le_pow_four_thirteen_from_total": (
        8,
        136,
        1116,
        50,
        1019,
        1115,
        97,
    ),
    "pow_six_six_le_pow_four_eight_from_total": (
        8,
        164,
        510,
        49,
        497,
        509,
        13,
    ),
    "pow_six_four_le_pow_four_six_from_total": (
        7,
        101,
        373,
        41,
        360,
        372,
        13,
    ),
    "pow_two_double_eq_pow_four_from_total": (2, 26, 30, 22, 30, 29, 0),
    ITERATOR_REPLACEMENT_NAME: (7, 177, 2388, 96, 1986, 2387, 402),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return successor_provider.make_bertrand_balanced_v1_successor_candidate_theorems(
        TheoremSpec
    )


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _old_balanced_seed_rows() -> tuple[TheoremSpec, ...]:
    return balanced_seed_provider.make_bertrand_power_seed_balanced_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _old_power_total_rows() -> tuple[TheoremSpec, ...]:
    return power_total_provider.make_bertrand_power_total_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _old_transport() -> dict[str, TheoremSpec]:
    rows = transport_provider.make_bertrand_hj_transport_candidate_theorems(
        TheoremSpec
    )
    return _table(rows)


@lru_cache(maxsize=1)
def _old_base_thirty_two() -> dict[str, TheoremSpec]:
    rows = base_thirty_two_provider.make_bertrand_hj_base_thirty_two_candidate_theorems(
        TheoremSpec
    )
    return _table(rows)


@lru_cache(maxsize=1)
def _old_all_s() -> dict[str, TheoremSpec]:
    rows = all_s_provider.make_bertrand_hj_all_s_candidate_theorems(
        TheoremSpec
    )
    return _table(rows)


def _rewritten_dependencies(
    original: TheoremSpec, replacements: dict[str, str]
) -> tuple[str, ...]:
    assert all(original.dependencies.count(name) == 1 for name in replacements)
    return tuple(replacements.get(name, name) for name in original.dependencies)


def _rewritten_script(
    original: TheoremSpec, replacements: dict[str, str]
) -> tuple[str, ...]:
    assert all(
        any(name in command for command in original.script)
        for name in replacements
    )
    return tuple(
        _replace_tokens(command, replacements) for command in original.script
    )


def _replace_tokens(command: str, replacements: dict[str, str]) -> str:
    result = command
    for old_name, new_name in replacements.items():
        result = result.replace(old_name, new_name)
    return result


def _assert_exact_clone(
    successor: TheoremSpec,
    original: TheoremSpec,
    *,
    expected_name: str,
    replacements: dict[str, str],
) -> None:
    assert successor.name == expected_name
    assert successor.statement == original.statement
    assert successor.summary == original.summary
    assert successor.dependencies == _rewritten_dependencies(
        original, replacements
    )
    assert successor.script == _rewritten_script(original, replacements)
    assert all(
        old_name not in successor.dependencies
        for old_name in replacements
    )
    assert all(
        old_name not in command
        for old_name in replacements
        for command in successor.script
    )


def _changed_commands(
    successor: TheoremSpec, original: TheoremSpec
) -> tuple[tuple[str, str], ...]:
    assert len(successor.script) == len(original.script)
    return tuple(
        (old, new)
        for old, new in zip(original.script, successor.script, strict=True)
        if old != new
    )


def _manifest_script_sha256(rows: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join((row.name, *row.script)) for row in rows
    )
    return sha256(payload.encode()).hexdigest()


def _manifest_logical_sha256(rows: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join((row.name, row.statement, *row.dependencies))
        for row in rows
    )
    return sha256(payload.encode()).hexdigest()


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    package = _table(_rows())
    public = dict(_specs_by_name())
    support = (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec),
        *make_bertrand_quotient_budget_candidate_theorems(TheoremSpec),
        *make_bertrand_threshold_base_candidate_theorems(TheoremSpec),
        *_old_power_total_rows(),
        *_old_base_thirty_two().values(),
    )
    for row in support:
        if row.name in package:
            assert row.name in {
                *BASE_THIRTY_TWO_REPLACEMENT_NAMES,
                ITERATOR_REPLACEMENT_NAME,
            }
            continue
        if row.name in public:
            assert public[row.name] == row
        else:
            public[row.name] = row
    assert not (set(public) & set(package))
    return public | package


def test_balanced_v1_successor_static_contract_is_fail_closed() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert successor_provider.EXPECTED_NAMES == EXPECTED_NAMES
    assert len(rows) == len(EXPECTED_NAMES) == 12
    assert len(set(EXPECTED_NAMES)) == len(EXPECTED_NAMES)
    assert all(
        expected == PENDING_BODY_RECEIPT or isinstance(expected, tuple)
        for expected in EXPECTED_BODY_RECEIPTS.values()
    )
    assert (
        EXPECTED_MANIFEST_HASHES == PENDING_MANIFEST_HASHES
        or isinstance(EXPECTED_MANIFEST_HASHES, dict)
    )

    for module, expected_sha256 in EXPECTED_SOURCE_SHA256.items():
        assert sha256(Path(module.__file__).read_bytes()).hexdigest() == (
            expected_sha256
        )


def test_balanced_v1_successor_exact_allowed_delta_and_topology() -> None:
    rows = _rows()
    table = _table(rows)
    old_balanced = _table(_old_balanced_seed_rows())
    old_power = _table(_old_power_total_rows())
    old_transport = _old_transport()
    old_base = _old_base_thirty_two()
    old_all_s = _old_all_s()

    assert table[SQUARE_HELPER_NAME] == old_balanced[SQUARE_HELPER_NAME]
    assert table[PRODUCT_HELPER_NAME] == old_balanced[PRODUCT_HELPER_NAME]
    _assert_exact_clone(
        table[BALANCED_V1_SEED_NAME],
        old_balanced[OLD_SEED_NAME],
        expected_name=BALANCED_V1_SEED_NAME,
        replacements={},
    )
    assert (
        table[BALANCED_V1_SEED_NAME].statement
        == old_power[OLD_SEED_NAME].statement
    )
    assert (
        table[BALANCED_V1_SEED_NAME].dependencies
        != old_power[OLD_SEED_NAME].dependencies
    )
    assert table[BALANCED_V1_SEED_NAME].script != old_power[OLD_SEED_NAME].script

    _assert_exact_clone(
        table[BALANCED_V1_H_TRANSPORT_NAME],
        old_transport[OLD_H_TRANSPORT_NAME],
        expected_name=BALANCED_V1_H_TRANSPORT_NAME,
        replacements={OLD_SEED_NAME: BALANCED_V1_SEED_NAME},
    )
    _assert_exact_clone(
        table[BALANCED_V1_J_TRANSPORT_NAME],
        old_transport[OLD_J_TRANSPORT_NAME],
        expected_name=BALANCED_V1_J_TRANSPORT_NAME,
        replacements={OLD_SEED_NAME: BALANCED_V1_SEED_NAME},
    )
    _assert_exact_clone(
        table[BALANCED_V1_COMBINED_TRANSPORT_NAME],
        old_transport[OLD_COMBINED_TRANSPORT_NAME],
        expected_name=BALANCED_V1_COMBINED_TRANSPORT_NAME,
        replacements={
            OLD_H_TRANSPORT_NAME: BALANCED_V1_H_TRANSPORT_NAME,
            OLD_J_TRANSPORT_NAME: BALANCED_V1_J_TRANSPORT_NAME,
        },
    )

    for name in BASE_THIRTY_TWO_REPLACEMENT_NAMES:
        successor = table[name]
        original = old_base[name]
        _assert_exact_clone(
            successor,
            original,
            expected_name=name,
            replacements={OLD_SEED_NAME: BALANCED_V1_SEED_NAME},
        )
        assert _changed_commands(successor, original) == (
            (
                f"apply {OLD_SEED_NAME}",
                f"apply {BALANCED_V1_SEED_NAME}",
            ),
        )

    iterator = table[ITERATOR_REPLACEMENT_NAME]
    old_iterator = old_all_s[ITERATOR_REPLACEMENT_NAME]
    _assert_exact_clone(
        iterator,
        old_iterator,
        expected_name=ITERATOR_REPLACEMENT_NAME,
        replacements={
            OLD_COMBINED_TRANSPORT_NAME: (
                BALANCED_V1_COMBINED_TRANSPORT_NAME
            )
        },
    )
    iterator_changes = _changed_commands(iterator, old_iterator)
    assert len(iterator_changes) == 12
    assert all(
        old.startswith(("specialize ", "apply "))
        and new.startswith(("specialize ", "apply "))
        for old, new in iterator_changes
    )

    h_changes = _changed_commands(
        table[BALANCED_V1_H_TRANSPORT_NAME],
        old_transport[OLD_H_TRANSPORT_NAME],
    )
    j_changes = _changed_commands(
        table[BALANCED_V1_J_TRANSPORT_NAME],
        old_transport[OLD_J_TRANSPORT_NAME],
    )
    assert h_changes == (
        (f"apply {OLD_SEED_NAME}", f"apply {BALANCED_V1_SEED_NAME}"),
    )
    assert j_changes == h_changes
    combined_changes = _changed_commands(
        table[BALANCED_V1_COMBINED_TRANSPORT_NAME],
        old_transport[OLD_COMBINED_TRANSPORT_NAME],
    )
    assert len(combined_changes) == 16
    assert all(
        old.startswith(("specialize ", "apply "))
        and new.startswith(("specialize ", "apply "))
        for old, new in combined_changes
    )

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert set(EXPECTED_NAMES) & set(old_balanced) == {
        SQUARE_HELPER_NAME,
        PRODUCT_HELPER_NAME,
    }
    assert set(EXPECTED_NAMES) & set(old_transport) == set()
    assert set(EXPECTED_NAMES) & set(old_base) == set(
        BASE_THIRTY_TWO_REPLACEMENT_NAMES
    )
    assert set(EXPECTED_NAMES) & set(old_all_s) == {
        ITERATOR_REPLACEMENT_NAME
    }

    for old_name in (
        OLD_SEED_NAME,
        OLD_H_TRANSPORT_NAME,
        OLD_J_TRANSPORT_NAME,
        OLD_COMBINED_TRANSPORT_NAME,
    ):
        alpha_entry = editions_v7.entry(
            old_name, edition=editions_v7.EditionName.ALPHA
        )
        assert alpha_entry is not None
        original = (
            old_power[old_name]
            if old_name == OLD_SEED_NAME
            else old_transport[old_name]
        )
        assert alpha_entry.spec == original
        assert alpha_entry.membership is editions_v7.Membership.ALPHA_ONLY
        assert alpha_entry.evidence is editions_v7.EvidenceStatus.BODY_CHECKED

    available = _available()
    positions = {name: index for index, name in enumerate(EXPECTED_NAMES)}
    for row in rows:
        assert _closed_formula(row.statement)
        assert all(dependency in available for dependency in row.dependencies)
        assert all(
            dependency not in positions
            or positions[dependency] < positions[row.name]
            for dependency in row.dependencies
        )
        assert all(
            forbidden not in command
            for command in row.script
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


def test_balanced_v1_successor_manifest_hashes_are_frozen() -> None:
    rows = _rows()
    actual = {
        "script_sha256": _manifest_script_sha256(rows),
        "logical_sha256": _manifest_logical_sha256(rows),
    }
    print(f"BALANCED V1 SUCCESSOR MANIFEST HASHES actual={actual!r}", flush=True)
    assert isinstance(EXPECTED_MANIFEST_HASHES, dict), (
        f"freeze deterministic lightweight factory hashes: {actual!r}"
    )
    assert actual == EXPECTED_MANIFEST_HASHES


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_balanced_v1_successor_body_receipt_is_frozen(row_name: str) -> None:
    item = _table(_rows())[row_name]
    receipts = replay_candidate_bodies((item,), core=_available())
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt.name == row_name
    actual = (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    )
    print(
        "BALANCED V1 SUCCESSOR BODY RECEIPT "
        f"row={row_name!r} actual={actual!r}",
        flush=True,
    )
    expected = EXPECTED_BODY_RECEIPTS[row_name]
    assert isinstance(expected, tuple), (
        f"freeze body receipt only after the kernel accepts {row_name!r}: "
        f"{actual!r}"
    )
    assert actual == expected
