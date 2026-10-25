"""Additive balanced-v1 successors for the Bertrand H/J closure graph.

Alpha v7 and every original candidate provider remain immutable.  This
factory gives the balanced power seed a unique name, clones the three
Alpha-v7 transport rows under unique balanced-v1 names, and replaces only
six post-v7 candidate surfaces: five base-window leaves and the six-block
iterator.  Those six names are safe to retain because they were never
enrolled in Alpha v7.

Statements and summaries are inherited byte-for-byte.  Dependency and
script rewrites are exact theorem-token substitutions; the factory fails if
an expected source token disappears.  This module adds no theorem authority:
all returned rows remain ordinary dependency-curried candidates until their
bodies and recursive closures are checked independently.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

from .bertrand_hj_all_s_candidate import (
    make_bertrand_hj_all_s_candidate_theorems,
)
from .bertrand_hj_base_thirty_two_candidate import (
    make_bertrand_hj_base_thirty_two_candidate_theorems,
)
from .bertrand_hj_transport_candidate import (
    make_bertrand_hj_transport_candidate_theorems,
)
from .bertrand_power_seed_balanced_candidate import (
    make_bertrand_power_seed_balanced_candidate_theorems,
)


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
    "eight_times_eight_eq_sixty_four",
    "eight_times_sixteen_eq_one_twenty_eight",
    BALANCED_V1_SEED_NAME,
    BALANCED_V1_H_TRANSPORT_NAME,
    BALANCED_V1_J_TRANSPORT_NAME,
    BALANCED_V1_COMBINED_TRANSPORT_NAME,
    *BASE_THIRTY_TWO_REPLACEMENT_NAMES,
    ITERATOR_REPLACEMENT_NAME,
)


def _by_name(rows: Iterable[Any], *, provider: str) -> dict[str, Any]:
    ordered = tuple(rows)
    table = {row.name: row for row in ordered}
    if len(table) != len(ordered):
        raise ValueError(f"{provider} returned duplicate theorem names")
    return table


def _rewrite_dependencies(
    dependencies: tuple[str, ...],
    replacements: Mapping[str, str],
    *,
    row_name: str,
) -> tuple[str, ...]:
    for old_name in replacements:
        if dependencies.count(old_name) != 1:
            raise ValueError(
                f"{row_name} no longer has exactly one dependency "
                f"token {old_name!r}"
            )
    rewritten = tuple(replacements.get(name, name) for name in dependencies)
    if any(old_name in rewritten for old_name in replacements):
        raise ValueError(f"{row_name} retained an obsolete dependency token")
    return rewritten


def _rewrite_script(
    script: tuple[str, ...],
    replacements: Mapping[str, str],
    *,
    row_name: str,
) -> tuple[str, ...]:
    counts = {old_name: 0 for old_name in replacements}
    rewritten: list[str] = []
    for command in script:
        result = command
        for old_name, new_name in replacements.items():
            occurrences = result.count(old_name)
            counts[old_name] += occurrences
            result = result.replace(old_name, new_name)
        rewritten.append(result)
    missing = tuple(name for name, count in counts.items() if count == 0)
    if missing:
        raise ValueError(
            f"{row_name} no longer uses expected script tokens {missing!r}"
        )
    result = tuple(rewritten)
    if any(old_name in command for old_name in replacements for command in result):
        raise ValueError(f"{row_name} retained an obsolete script token")
    return result


def _clone(
    spec: Callable[..., Any],
    row: Any,
    *,
    name: str | None = None,
    replacements: Mapping[str, str] | None = None,
) -> Any:
    token_map = {} if replacements is None else replacements
    dependencies = (
        row.dependencies
        if not token_map
        else _rewrite_dependencies(
            row.dependencies,
            token_map,
            row_name=row.name,
        )
    )
    script = (
        row.script
        if not token_map
        else _rewrite_script(row.script, token_map, row_name=row.name)
    )
    return spec(
        row.name if name is None else name,
        row.statement,
        dependencies,
        script,
        row.summary,
    )


def make_bertrand_balanced_v1_successor_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return the exact twelve-row additive balanced-v1 manifest."""

    balanced_seed_rows = make_bertrand_power_seed_balanced_candidate_theorems(
        spec
    )
    if tuple(row.name for row in balanced_seed_rows) != (
        "eight_times_eight_eq_sixty_four",
        "eight_times_sixteen_eq_one_twenty_eight",
        OLD_SEED_NAME,
    ):
        raise ValueError("balanced seed provider manifest changed")
    square_helper, product_helper, old_balanced_seed = balanced_seed_rows
    balanced_seed = _clone(
        spec,
        old_balanced_seed,
        name=BALANCED_V1_SEED_NAME,
    )

    transport = _by_name(
        make_bertrand_hj_transport_candidate_theorems(spec),
        provider="H/J transport provider",
    )
    h_transport = _clone(
        spec,
        transport[OLD_H_TRANSPORT_NAME],
        name=BALANCED_V1_H_TRANSPORT_NAME,
        replacements={OLD_SEED_NAME: BALANCED_V1_SEED_NAME},
    )
    j_transport = _clone(
        spec,
        transport[OLD_J_TRANSPORT_NAME],
        name=BALANCED_V1_J_TRANSPORT_NAME,
        replacements={OLD_SEED_NAME: BALANCED_V1_SEED_NAME},
    )
    combined_transport = _clone(
        spec,
        transport[OLD_COMBINED_TRANSPORT_NAME],
        name=BALANCED_V1_COMBINED_TRANSPORT_NAME,
        replacements={
            OLD_H_TRANSPORT_NAME: BALANCED_V1_H_TRANSPORT_NAME,
            OLD_J_TRANSPORT_NAME: BALANCED_V1_J_TRANSPORT_NAME,
        },
    )

    base_thirty_two = _by_name(
        make_bertrand_hj_base_thirty_two_candidate_theorems(spec),
        provider="base-thirty-two provider",
    )
    base_replacements = tuple(
        _clone(
            spec,
            base_thirty_two[name],
            replacements={OLD_SEED_NAME: BALANCED_V1_SEED_NAME},
        )
        for name in BASE_THIRTY_TWO_REPLACEMENT_NAMES
    )

    all_s = _by_name(
        make_bertrand_hj_all_s_candidate_theorems(spec),
        provider="all-s provider",
    )
    iterator = _clone(
        spec,
        all_s[ITERATOR_REPLACEMENT_NAME],
        replacements={
            OLD_COMBINED_TRANSPORT_NAME: (
                BALANCED_V1_COMBINED_TRANSPORT_NAME
            )
        },
    )

    result = (
        square_helper,
        product_helper,
        balanced_seed,
        h_transport,
        j_transport,
        combined_transport,
        *base_replacements,
        iterator,
    )
    if tuple(row.name for row in result) != EXPECTED_NAMES:
        raise ValueError("balanced-v1 successor manifest changed")
    if len({row.name for row in result}) != len(result):
        raise ValueError("balanced-v1 successor manifest contains duplicates")
    return result


__all__ = [
    "BALANCED_V1_COMBINED_TRANSPORT_NAME",
    "BALANCED_V1_H_TRANSPORT_NAME",
    "BALANCED_V1_J_TRANSPORT_NAME",
    "BALANCED_V1_SEED_NAME",
    "BASE_THIRTY_TWO_REPLACEMENT_NAMES",
    "EXPECTED_NAMES",
    "ITERATOR_REPLACEMENT_NAME",
    "make_bertrand_balanced_v1_successor_candidate_theorems",
]
