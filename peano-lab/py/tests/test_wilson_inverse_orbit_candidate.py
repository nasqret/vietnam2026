"""WMI-only recursive discovery audit for the 19-node Wilson orbit stack."""

from __future__ import annotations

import gc
import resource
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Eq,
    Formula,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)
from peano_lab.library.wilson_inverse_endpoints_candidate import (
    _beta_at_term as endpoint_beta_at_term,
    _inverse_index_term as endpoint_inverse_index_term,
    _mod_eq as endpoint_mod_eq,
    _strictly_below_term as endpoint_strictly_below_term,
    make_wilson_inverse_endpoints_candidate_theorems,
)
from peano_lab.library.wilson_inverse_involution_candidate import (
    make_wilson_inverse_involution_candidate_theorems,
    successor_positive,
    successor_strictly_below as involution_successor_strictly_below,
)
from peano_lab.library.wilson_inverse_orbit_candidate import (
    beta_at_zero_index as orbit_beta_at_zero_index,
    make_wilson_inverse_orbit_candidate_theorems,
    nonendpoint,
)
from peano_lab.library.wilson_inverse_point_candidate import (
    balanced_inverse,
    inverse_index as point_inverse_index,
    make_wilson_inverse_point_candidate_theorems,
    prime as point_prime,
    strictly_below as point_strictly_below,
    successor_strictly_below as point_successor_strictly_below,
)
from peano_lab.library.wilson_inverse_prefix_candidate import (
    beta_at,
    inverse_index as prefix_inverse_index,
    inverse_prefix,
    inverse_prefix_successor,
    make_wilson_inverse_prefix_candidate_theorems,
    prime as prefix_prime,
    strictly_below as prefix_strictly_below,
)
from peano_lab.library.wilson_square_one_candidate import (
    make_wilson_square_one_candidate_theorems,
    positive as square_positive,
    prime as square_prime,
    square_one_mod,
    strictly_below as square_strictly_below,
)


SQUARE_NAME = "prime_bounded_square_one_cases"
POINT_NAMES = (
    "prime_inverse_index_exists",
    "bounded_mod_inverse_unique",
    "bounded_inverse_index_unique",
    "inverse_index_symmetric",
)
PREFIX_NAMES = (
    "prime_inverse_prefix_extend",
    "prime_inverse_prefix_exists_bounded",
    "prime_inverse_prefix_exists",
)
INVOLUTION_NAMES = (
    "inverse_prefix_entry_sound",
    "inverse_prefix_extensional",
    "inverse_prefix_involutive",
    "inverse_prefix_injective",
    "inverse_prefix_surjective",
    "prime_inverse_prefix_fixed_cases",
)
ENDPOINT_NAMES = (
    "inverse_prefix_zero_fixed",
    "inverse_prefix_last_fixed",
    "prime_inverse_prefix_exact_endpoints",
)
ORBIT_NAMES = (
    "prime_inverse_prefix_nonendpoint_not_fixed",
    "prime_inverse_prefix_nonendpoint_mate",
)
PRIME_FREE_INVOLUTION_NAMES = INVOLUTION_NAMES[:5]
EXPECTED_NAMES = (
    (SQUARE_NAME,)
    + POINT_NAMES
    + PREFIX_NAMES
    + INVOLUTION_NAMES
    + ENDPOINT_NAMES
    + ORBIT_NAMES
)

EXPECTED_DEPENDENCIES = {
    SQUARE_NAME: (
        "ne_zero_of_one_le",
        "nonzero_is_succ",
        "mul_succ_left",
        "add_assoc",
        "add_comm",
        "add_left_cancel",
        "factor_difference",
        "euclid_prime_dvd_product",
        "le_succ_self",
        "lt_of_le_of_lt",
        "zero_or_succ",
        "divisor_le_nonzero",
        "lt_not_le",
        "succ_ne_zero",
        "le_antisymm",
        "succ_injective",
    ),
    "prime_inverse_index_exists": (
        "succ_ne_zero",
        "succ_le_succ",
        "prime_bounded_nonzero_mod_inverse",
        "nonzero_is_succ",
        "le_of_succ_le_succ",
    ),
    "bounded_mod_inverse_unique": (
        "mod_eq_symm",
        "mod_eq_mul_left",
        "mod_eq_mul_right",
        "mul_assoc",
        "mul_comm",
        "mul_one",
        "one_mul",
        "mod_eq_trans",
        "mod_eq_bounded_unique",
    ),
    "bounded_inverse_index_unique": (
        "succ_le_succ",
        "bounded_mod_inverse_unique",
        "succ_injective",
    ),
    "inverse_index_symmetric": ("mul_comm",),
    "prime_inverse_prefix_extend": (
        "prime_inverse_index_exists",
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "prime_inverse_prefix_exists_bounded": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "lt_to_le",
        "prime_inverse_prefix_extend",
    ),
    "prime_inverse_prefix_exists": (
        "le_refl",
        "prime_inverse_prefix_exists_bounded",
    ),
    "inverse_prefix_entry_sound": ("beta_at_unique",),
    "inverse_prefix_extensional": ("bounded_inverse_index_unique",),
    "inverse_prefix_involutive": (
        "inverse_prefix_entry_sound",
        "inverse_index_symmetric",
        "inverse_prefix_extensional",
    ),
    "inverse_prefix_injective": (
        "inverse_prefix_involutive",
        "beta_at_unique",
    ),
    "inverse_prefix_surjective": ("inverse_prefix_involutive",),
    "prime_inverse_prefix_fixed_cases": (
        "inverse_prefix_entry_sound",
        "succ_le_succ",
        SQUARE_NAME,
        "succ_injective",
    ),
    "inverse_prefix_zero_fixed": (
        "mod_eq_refl",
        "one_mul",
        "inverse_prefix_extensional",
    ),
    "inverse_prefix_last_fixed": (
        "zero_add",
        "predecessor_square_mod_one",
        "inverse_prefix_extensional",
    ),
    "prime_inverse_prefix_exact_endpoints": (
        "prime_is_succ_succ",
        "succ_injective",
        "inverse_prefix_zero_fixed",
        "inverse_prefix_last_fixed",
        "prime_inverse_prefix_fixed_cases",
    ),
    "prime_inverse_prefix_nonendpoint_not_fixed": (
        "prime_inverse_prefix_fixed_cases",
    ),
    "prime_inverse_prefix_nonendpoint_mate": (
        "prime_inverse_prefix_nonendpoint_not_fixed",
        "inverse_prefix_involutive",
        "prime_is_succ_succ",
        "succ_injective",
        "inverse_prefix_zero_fixed",
        "inverse_prefix_last_fixed",
        "beta_at_unique",
    ),
}

EXPECTED_CORE_BOUNDARY = (
    "ne_zero_of_one_le",
    "nonzero_is_succ",
    "mul_succ_left",
    "add_assoc",
    "add_comm",
    "add_left_cancel",
    "factor_difference",
    "euclid_prime_dvd_product",
    "le_succ_self",
    "lt_of_le_of_lt",
    "zero_or_succ",
    "divisor_le_nonzero",
    "lt_not_le",
    "succ_ne_zero",
    "le_antisymm",
    "succ_injective",
    "succ_le_succ",
    "prime_bounded_nonzero_mod_inverse",
    "le_of_succ_le_succ",
    "mod_eq_symm",
    "mod_eq_mul_left",
    "mod_eq_mul_right",
    "mul_assoc",
    "mul_comm",
    "mul_one",
    "one_mul",
    "mod_eq_trans",
    "mod_eq_bounded_unique",
    "beta_prefix_extend",
    "finite_lt_succ_eq_or_lt",
    "add_eq_zero_right",
    "lt_to_le",
    "le_refl",
    "beta_at_unique",
    "mod_eq_refl",
    "zero_add",
    "predecessor_square_mod_one",
    "prime_is_succ_succ",
)

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_CANDIDATE_SOURCES = (
    ("square_one", _SOURCE_ROOT / "wilson_square_one_candidate.py"),
    ("point", _SOURCE_ROOT / "wilson_inverse_point_candidate.py"),
    ("prefix", _SOURCE_ROOT / "wilson_inverse_prefix_candidate.py"),
    ("involution", _SOURCE_ROOT / "wilson_inverse_involution_candidate.py"),
    ("endpoints", _SOURCE_ROOT / "wilson_inverse_endpoints_candidate.py"),
    ("orbit", _SOURCE_ROOT / "wilson_inverse_orbit_candidate.py"),
)

_FALSE_CONTRACT_REWRITES = {
    SQUARE_NAME: ("x = 1 \\/ x = n", "x = 1 \\/ x = S n"),
    "prime_inverse_index_exists": (
        "= 1 + p * wip_mod_right_exists_result_inverse",
        "= S 1 + p * wip_mod_right_exists_result_inverse",
    ),
    "bounded_mod_inverse_unique": ("-> y = z", "-> y = S z"),
    "bounded_inverse_index_unique": ("-> j = k", "-> j = S k"),
    "inverse_index_symmetric": (
        "= 1 + p * wip_mod_right_symmetric_target_inverse",
        "= S 1 + p * wip_mod_right_symmetric_target_inverse",
    ),
    "prime_inverse_prefix_extend": (
        "= 1 + p * wip_mod_right_extend_after_inverse_mod",
        "= S 1 + p * wip_mod_right_extend_after_inverse_mod",
    ),
    "prime_inverse_prefix_exists_bounded": (
        "= 1 + p * wip_mod_right_bounded_result_inverse_mod",
        "= S 1 + p * wip_mod_right_bounded_result_inverse_mod",
    ),
    "prime_inverse_prefix_exists": (
        "= 1 + p * wip_mod_right_full_result_inverse_mod",
        "= S 1 + p * wip_mod_right_full_result_inverse_mod",
    ),
    "inverse_prefix_entry_sound": (
        "= 1 + p * wip_mod_right_entry_result_mod",
        "= S 1 + p * wip_mod_right_entry_result_mod",
    ),
    "inverse_prefix_extensional": (
        "b = wip_beta_quotient_extensional_result * "
        "S ((S (i)) * c) + (j)",
        "b = wip_beta_quotient_extensional_result * "
        "S ((S (i)) * c) + (S j)",
    ),
    "inverse_prefix_involutive": (
        "b = wip_beta_quotient_involutive_back * S ((S (j)) * c) + (i)",
        "b = wip_beta_quotient_involutive_back * S ((S (j)) * c) + (S i)",
    ),
    "inverse_prefix_injective": ("-> i = j", "-> i = S j"),
    "inverse_prefix_surjective": (
        "b = wip_beta_quotient_surjective_result_at * "
        "S ((S (i)) * c) + (j)",
        "b = wip_beta_quotient_surjective_result_at * "
        "S ((S (i)) * c) + (S j)",
    ),
    "prime_inverse_prefix_fixed_cases": (
        "i = 0 \\/ S i = n",
        "i = 0 \\/ S i = S n",
    ),
    "inverse_prefix_zero_fixed": (
        "b = wie_beta_quotient_zero_result * S ((S (0)) * c) + (0)",
        "b = wie_beta_quotient_zero_result * S ((S (0)) * c) + (S 0)",
    ),
    "inverse_prefix_last_fixed": (
        "b = wip_beta_quotient_last_result * S ((S (k)) * c) + (k)",
        "b = wip_beta_quotient_last_result * S ((S (k)) * c) + (S k)",
    ),
    "prime_inverse_prefix_exact_endpoints": (
        "i = 0 \\/ i = k",
        "i = 0 \\/ i = S k",
    ),
    "prime_inverse_prefix_nonendpoint_not_fixed": (
        "-> ~(i = j)",
        "-> ~(i = S j)",
    ),
    "prime_inverse_prefix_nonendpoint_mate": (
        "~((S j) = n)",
        "~((S j) = S n)",
    ),
}


@dataclass(frozen=True)
class _Checked:
    formula: Formula
    certificate: Proof


@dataclass(frozen=True)
class _PassReceipt:
    duration_seconds: float
    peak_rss_kib: int
    peak_rss_growth_kib: int


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return (
        make_wilson_square_one_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_point_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_prefix_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_involution_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_endpoints_candidate_theorems(TheoremSpec)
        + make_wilson_inverse_orbit_candidate_theorems(TheoremSpec)
    )


def _expected_statements() -> dict[str, str]:
    square_prime_p = square_prime("p", tag="prime")
    square_positive_x = square_positive("x", tag="positive")
    square_bounded_x = square_strictly_below("x", "p", tag="bounded")
    square_mod_one = square_one_mod("p", "x", tag="square_one")

    point_prime_p = point_prime("p", tag="exists_prime")
    point_i_below_n = point_strictly_below("i", "n", tag="exists_index_bound")
    point_exists_result = point_inverse_index(
        "p", "n", "i", "j", tag="exists_result"
    )
    point_y_below_p = point_strictly_below("y", "p", tag="unique_y_bound")
    point_z_below_p = point_strictly_below("z", "p", tag="unique_z_bound")
    point_inverse_xy = balanced_inverse("p", "x", "y", tag="unique_xy")
    point_inverse_xz = balanced_inverse("p", "x", "z", tag="unique_xz")
    point_left_relation = point_inverse_index(
        "p", "n", "i", "j", tag="index_unique_left"
    )
    point_right_relation = point_inverse_index(
        "p", "n", "i", "k", tag="index_unique_right"
    )
    point_symmetric_source = point_inverse_index(
        "p", "n", "i", "j", tag="symmetric_source"
    )
    point_symmetric_target = point_inverse_index(
        "p", "n", "j", "i", tag="symmetric_target"
    )

    prefix_extend_prime = prefix_prime("p", tag="extend_prime")
    prefix_extend_bound = prefix_strictly_below("l", "n", tag="extend_length")
    prefix_extend_before = inverse_prefix(
        "p", "n", "b", "c", "l", tag="extend_before"
    )
    prefix_extend_after = inverse_prefix_successor(
        "p", "n", "z", "d", "l", tag="extend_after"
    )
    prefix_bounded_prime = prefix_prime("p", tag="bounded_prime")
    prefix_bounded_length = (
        "exists wip_weak_gap_bounded_length. "
        "wip_weak_gap_bounded_length + l = n"
    )
    prefix_bounded_result = inverse_prefix(
        "p", "n", "b", "c", "l", tag="bounded_result"
    )
    prefix_full_prime = prefix_prime("p", tag="full_prime")
    prefix_full_result = inverse_prefix(
        "p", "n", "b", "c", "n", tag="full_result"
    )

    entry_prefix = inverse_prefix("p", "n", "b", "c", "l", tag="entry_prefix")
    entry_bound = prefix_strictly_below("i", "l", tag="entry_index_bound")
    entry_at = beta_at("b", "c", "i", "j", tag="entry_source")
    entry_result = prefix_inverse_index("p", "n", "i", "j", tag="entry_result")
    extensional_prefix = inverse_prefix(
        "p", "n", "b", "c", "l", tag="extensional_prefix"
    )
    extensional_bound = prefix_strictly_below(
        "i", "l", tag="extensional_index_bound"
    )
    extensional_source = prefix_inverse_index(
        "p", "n", "i", "j", tag="extensional_source"
    )
    extensional_result = beta_at(
        "b", "c", "i", "j", tag="extensional_result"
    )
    involutive_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="involutive_prefix"
    )
    involutive_i_bound = prefix_strictly_below(
        "i", "n", tag="involutive_index_bound"
    )
    involutive_j_bound = prefix_strictly_below(
        "j", "n", tag="involutive_mate_bound"
    )
    involutive_at = beta_at("b", "c", "i", "j", tag="involutive_source")
    involutive_back = beta_at("b", "c", "j", "i", tag="involutive_back")
    injective_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="injective_prefix"
    )
    injective_i_bound = prefix_strictly_below(
        "i", "n", tag="injective_left_bound"
    )
    injective_j_bound = prefix_strictly_below(
        "j", "n", tag="injective_right_bound"
    )
    injective_left = beta_at("b", "c", "i", "k", tag="injective_left_entry")
    injective_right = beta_at(
        "b", "c", "j", "k", tag="injective_right_entry"
    )
    surjective_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="surjective_prefix"
    )
    surjective_j_bound = prefix_strictly_below(
        "j", "n", tag="surjective_value_bound"
    )
    surjective_i_bound = prefix_strictly_below(
        "i", "n", tag="surjective_index_bound"
    )
    surjective_at = beta_at("b", "c", "i", "j", tag="surjective_result_at")
    fixed_prime = prefix_prime("p", tag="fixed_prime")
    fixed_prefix = inverse_prefix("p", "n", "b", "c", "n", tag="fixed_prefix")
    fixed_bound = prefix_strictly_below("i", "n", tag="fixed_index_bound")
    fixed_at = beta_at("b", "c", "i", "i", tag="fixed_entry")

    endpoint_zero_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="zero_prefix"
    )
    endpoint_zero = endpoint_beta_at_term(
        "b",
        "c",
        "0",
        "0",
        tag="zero_result",
        avoid=("p", "n", "k", "b", "c"),
    )
    endpoint_last_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="last_prefix"
    )
    endpoint_last = beta_at("b", "c", "k", "k", tag="last_result")
    endpoint_exact_prime = prefix_prime("p", tag="exact_prime")
    endpoint_exact_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="exact_prefix"
    )
    endpoint_exact_zero = endpoint_beta_at_term(
        "b",
        "c",
        "0",
        "0",
        tag="exact_zero",
        avoid=("p", "n", "b", "c", "k"),
    )
    endpoint_exact_last = beta_at("b", "c", "k", "k", tag="exact_last")
    endpoint_exact_fixed_bound = prefix_strictly_below(
        "i", "n", tag="exact_fixed_bound"
    )
    endpoint_exact_fixed_at = beta_at(
        "b", "c", "i", "i", tag="exact_fixed_entry"
    )
    endpoint_exact_fixed_cases = (
        f"forall i. ({endpoint_exact_fixed_bound}) -> "
        f"({endpoint_exact_fixed_at}) -> i = 0 \\/ i = k"
    )

    orbit_prime = prefix_prime("p", tag="orbit_prime")
    orbit_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="orbit_prefix"
    )
    orbit_source_bound = prefix_strictly_below(
        "i", "n", tag="orbit_source_bound"
    )
    orbit_source_at = beta_at(
        "b", "c", "i", "j", tag="orbit_source_entry"
    )
    orbit_source_nonendpoint = nonendpoint("i", "n")
    orbit_mate_nonendpoint = nonendpoint("j", "n")

    return {
        SQUARE_NAME: (
            f"forall p n x. p = S n -> ({square_prime_p}) -> "
            f"({square_positive_x}) -> ({square_bounded_x}) -> "
            f"({square_mod_one}) -> x = 1 \\/ x = n"
        ),
        "prime_inverse_index_exists": (
            f"forall p n i. p = S n -> ({point_prime_p}) -> "
            f"({point_i_below_n}) -> exists j. ({point_exists_result})"
        ),
        "bounded_mod_inverse_unique": (
            f"forall p x y z. ({point_y_below_p}) -> ({point_z_below_p}) -> "
            f"({point_inverse_xy}) -> ({point_inverse_xz}) -> y = z"
        ),
        "bounded_inverse_index_unique": (
            f"forall p n i j k. p = S n -> ({point_left_relation}) -> "
            f"({point_right_relation}) -> j = k"
        ),
        "inverse_index_symmetric": (
            f"forall p n i j. ({point_symmetric_source}) -> "
            f"({point_symmetric_target})"
        ),
        "prime_inverse_prefix_extend": (
            f"forall p n b c l. p = S n -> ({prefix_extend_prime}) -> "
            f"({prefix_extend_bound}) -> ({prefix_extend_before}) -> "
            f"exists z d. ({prefix_extend_after})"
        ),
        "prime_inverse_prefix_exists_bounded": (
            f"forall p n l. p = S n -> ({prefix_bounded_prime}) -> "
            f"({prefix_bounded_length}) -> exists b c. ({prefix_bounded_result})"
        ),
        "prime_inverse_prefix_exists": (
            f"forall p n. p = S n -> ({prefix_full_prime}) -> "
            f"exists b c. ({prefix_full_result})"
        ),
        "inverse_prefix_entry_sound": (
            f"forall p n b c l i j. ({entry_prefix}) -> ({entry_bound}) -> "
            f"({entry_at}) -> ({entry_result})"
        ),
        "inverse_prefix_extensional": (
            f"forall p n b c l i j. p = S n -> ({extensional_prefix}) -> "
            f"({extensional_bound}) -> ({extensional_source}) -> "
            f"({extensional_result})"
        ),
        "inverse_prefix_involutive": (
            f"forall p n b c i j. p = S n -> ({involutive_prefix}) -> "
            f"({involutive_i_bound}) -> ({involutive_at}) -> "
            f"(({involutive_j_bound}) /\\ ({involutive_back}))"
        ),
        "inverse_prefix_injective": (
            f"forall p n b c i j k. p = S n -> ({injective_prefix}) -> "
            f"({injective_i_bound}) -> ({injective_j_bound}) -> "
            f"({injective_left}) -> ({injective_right}) -> i = j"
        ),
        "inverse_prefix_surjective": (
            f"forall p n b c j. p = S n -> ({surjective_prefix}) -> "
            f"({surjective_j_bound}) -> exists i. "
            f"(({surjective_i_bound}) /\\ ({surjective_at}))"
        ),
        "prime_inverse_prefix_fixed_cases": (
            f"forall p n b c i. p = S n -> ({fixed_prime}) -> "
            f"({fixed_prefix}) -> ({fixed_bound}) -> ({fixed_at}) -> "
            "i = 0 \\/ S i = n"
        ),
        "inverse_prefix_zero_fixed": (
            f"forall p n k b c. p = S n -> n = S k -> "
            f"({endpoint_zero_prefix}) -> ({endpoint_zero})"
        ),
        "inverse_prefix_last_fixed": (
            f"forall p n k b c. p = S n -> n = S k -> "
            f"({endpoint_last_prefix}) -> ({endpoint_last})"
        ),
        "prime_inverse_prefix_exact_endpoints": (
            f"forall p n b c. p = S n -> ({endpoint_exact_prime}) -> "
            f"({endpoint_exact_prefix}) -> exists k. ((n = S k) /\\ "
            f"(({endpoint_exact_zero}) /\\ (({endpoint_exact_last}) /\\ "
            f"({endpoint_exact_fixed_cases}))))"
        ),
        "prime_inverse_prefix_nonendpoint_not_fixed": (
            f"forall p n b c i j. p = S n -> ({orbit_prime}) -> "
            f"({orbit_prefix}) -> ({orbit_source_bound}) -> "
            f"({orbit_source_at}) -> ({orbit_source_nonendpoint}) -> "
            "~(i = j)"
        ),
        "prime_inverse_prefix_nonendpoint_mate": (
            f"forall p n b c i j. p = S n -> ({orbit_prime}) -> "
            f"({orbit_prefix}) -> ({orbit_source_bound}) -> "
            f"({orbit_source_at}) -> ({orbit_source_nonendpoint}) -> "
            f"({orbit_mate_nonendpoint})"
        ),
    }


def _spec_digest(spec: TheoremSpec) -> str:
    payload = "\x1f".join(
        (
            spec.name,
            spec.statement,
            "\x1e".join(spec.script),
            "\x1e".join(spec.dependencies),
        )
    )
    return sha256(payload.encode()).hexdigest()


def _graph_digest(specs: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(_spec_digest(spec) for spec in specs)
    return sha256(payload.encode()).hexdigest()


def _source_digests() -> tuple[tuple[str, str], ...]:
    return tuple(
        (name, sha256(path.read_bytes()).hexdigest())
        for name, path in _CANDIDATE_SOURCES
    )


def _fresh_replayer():
    specs = _candidate_specs()
    core = _specs_by_name()
    local: dict[str, TheoremSpec] = {}
    for spec in specs:
        assert spec.name not in core
        assert spec.name not in local
        local[spec.name] = spec

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        if name in core:
            checked = replay(name)
            return _Checked(checked.formula, checked.certificate)

        spec = local[name]
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            dependency_spec = local.get(dependency) or core[dependency]
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, args = _primitive(command)
            state = apply_tactic(state, tactic, args)
        certificate = checked_final(state, target)

        body = certificate
        for _ in spec.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(spec.dependencies):
            checked_dependency = run(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )
        assert check((), body, formula)
        return _Checked(formula, body)

    return specs, local, run


def _cold_rows():
    started = perf_counter()
    starting_peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, local, run = _fresh_replayer()
    checked: dict[str, _Checked] = {}
    rows = []
    for spec in specs:
        theorem = run(spec.name)
        checked[spec.name] = theorem
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
        rows.append(
            (
                spec.name,
                nodes,
                depth,
                objects,
                edges,
                reused,
                cuts,
                len(spec.statement),
                _spec_digest(spec),
                sha256(spec.statement.encode()).hexdigest(),
                sha256("\n".join(spec.script).encode()).hexdigest(),
                sha256("\0".join(spec.dependencies).encode()).hexdigest(),
            )
        )
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS

    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = _PassReceipt(
        duration_seconds=perf_counter() - started,
        peak_rss_kib=peak_rss,
        peak_rss_growth_kib=max(0, peak_rss - starting_peak_rss),
    )
    return (
        specs,
        checked,
        tuple(rows),
        local,
        _source_digests(),
        _graph_digest(specs),
        receipt,
    )


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_rows()
    first_rows = first[2]
    first_sources = first[4]
    first_graph = first[5]
    first_receipt = first[6]
    del first
    gc.collect()
    second = _cold_rows()
    assert second[2] == first_rows
    assert second[4] == first_sources
    assert second[5] == first_graph
    return second[:4] + ((first_receipt, second[6]), second[4], second[5])


def _assert_cut_spine(
    certificate: Proof,
    spec: TheoremSpec,
    local: dict[str, TheoremSpec],
) -> None:
    body = certificate
    core = _specs_by_name()
    for dependency in spec.dependencies:
        assert type(body) is Cut
        dependency_spec = local.get(dependency) or core[dependency]
        expected = _closed_formula(dependency_spec.statement)
        assert body.proposition == expected
        assert check((), body.lemma, expected)
        assert not any(type(node) is DNE for node in _walk(body.lemma))
        body = body.body


def _mutate_cut_at(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(
            certificate,
            proposition=Eq(zero, zero),
            lemma=EqRefl(zero),
        )
    return replace(certificate, body=_mutate_cut_at(certificate.body, index - 1))


def _row_metadata(row: tuple[object, ...]) -> dict[str, object]:
    (
        name,
        nodes,
        depth,
        objects,
        edges,
        reused,
        cuts,
        length,
        spec_digest,
        statement_digest,
        script_digest,
        dependencies_digest,
    ) = row
    return {
        "name": name,
        "nodes": nodes,
        "depth": depth,
        "objects": objects,
        "edges": edges,
        "reused": reused,
        "cuts": cuts,
        "statement_length": length,
        "spec_sha256": spec_digest,
        "statement_sha256": statement_digest,
        "script_sha256": script_digest,
        "dependencies_sha256": dependencies_digest,
    }


def wmi_receipt_metadata() -> dict[str, object]:
    """Expose deterministic recursive Wilson-orbit evidence to WMI."""

    _, _, rows, _, passes, source_digests, graph_digest = _discovery_runs()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    return {
        "candidate_source_sha256": dict(source_digests),
        "graph_sha256": graph_digest,
        "recursive_graph_names": list(EXPECTED_NAMES),
        "discovery_passes": [
            {
                "pass_index": index,
                "duration_seconds": receipt.duration_seconds,
                "peak_rss_kib": receipt.peak_rss_kib,
                "peak_rss_growth_kib": receipt.peak_rss_growth_kib,
                "candidate_source_sha256": dict(source_digests),
            }
            for index, receipt in enumerate(passes, start=1)
        ],
        "candidates": [_row_metadata(row) for row in rows],
    }


def test_wilson_orbit_contracts_are_exact_deterministic_closed_expanded_pa() -> None:
    group_factories = (
        make_wilson_square_one_candidate_theorems,
        make_wilson_inverse_point_candidate_theorems,
        make_wilson_inverse_prefix_candidate_theorems,
        make_wilson_inverse_involution_candidate_theorems,
        make_wilson_inverse_endpoints_candidate_theorems,
        make_wilson_inverse_orbit_candidate_theorems,
    )
    first_groups = tuple(factory(TheoremSpec) for factory in group_factories)
    second_groups = tuple(factory(TheoremSpec) for factory in group_factories)
    assert tuple(map(len, first_groups)) == (1, 4, 3, 6, 3, 2)
    assert second_groups == first_groups
    first = tuple(spec for group in first_groups for spec in group)
    assert len(first) == 19
    assert tuple(spec.name for spec in first) == EXPECTED_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES
    assert {spec.name: spec.statement for spec in first} == _expected_statements()

    for spec in first:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert _closed_formula(spec.statement) == formula
        assert formula == parse_formula(spec.statement)
        assert len(spec.statement) < 8_192
        assert all("DNE" not in command for command in spec.script)
        assert all(
            token not in spec.statement
            for token in (
                "BetaAt(",
                "InvIdx(",
                "InvPrefix(",
                "Lt(",
                "ModEq(",
                "Positive(",
                "Prime(",
                "SquareOne(",
                "%",
                "^",
                "<",
                "∣",
            )
        )

    by_name = {spec.name: spec for spec in first}
    for name in PRIME_FREE_INVOLUTION_NAMES + ENDPOINT_NAMES[:2]:
        assert "~(p = 1)" not in by_name[name].statement
        assert "wip_prime_left_" not in by_name[name].statement
    fixed = by_name["prime_inverse_prefix_fixed_cases"]
    assert fixed.statement.endswith("i = 0 \\/ S i = n")

    zero = by_name["inverse_prefix_zero_fixed"]
    last = by_name["inverse_prefix_last_fixed"]
    exact = by_name["prime_inverse_prefix_exact_endpoints"]
    assert "p = S n -> n = S k" in zero.statement
    assert "p = S n -> n = S k" in last.statement
    assert "n = S (S k)" not in zero.statement
    assert "n = S (S k)" not in last.statement
    assert "~(k = 0)" not in exact.statement
    assert "i = 0 \\/ i = k" in exact.statement
    assert exact.statement.count("~(p = 1)") == 1
    assert "coincidence at p=2" in exact.summary
    assert "p = 2" not in exact.statement
    assert "p = 3" not in exact.statement

    not_fixed = by_name["prime_inverse_prefix_nonendpoint_not_fixed"]
    mate = by_name["prime_inverse_prefix_nonendpoint_mate"]
    for orbit_spec in (not_fixed, mate):
        assert orbit_spec.statement.count("~(p = 1)") == 1
        assert orbit_spec.statement.count("~(i = 0)") == 1
        assert orbit_spec.statement.count("~((S i) = n)") == 1
        assert "n = S (S k)" not in orbit_spec.statement
        assert "~(0 = k)" not in orbit_spec.statement
        assert "p = 2" not in orbit_spec.statement
        assert "p = 3" not in orbit_spec.statement
    assert "~(j = 0)" not in not_fixed.statement
    assert "~((S j) = n)" not in not_fixed.statement
    assert mate.statement.count("~(j = 0)") == 1
    assert mate.statement.count("~((S j) = n)") == 1

    # At p=2 the exact endpoints may coincide (k=0).  The orbit contracts do
    # not silently strengthen that fact: they apply only after explicitly
    # excluding both endpoint equations for the source, and make no claim that
    # the two endpoint indices are distinct.
    assert "coincidence at p=2" in exact.summary
    assert "nonendpoint" in not_fixed.summary
    assert "nonendpoint" in mate.summary


def test_wilson_orbit_helpers_are_exact_hygienic_and_alpha_equal() -> None:
    zero_bound = endpoint_strictly_below_term(
        "0", "n", tag="exact", avoid=("n",)
    )
    assert zero_bound == (
        "exists wie_strict_gap_exact. wie_strict_gap_exact + S 0 = n"
    )
    zero_at = endpoint_beta_at_term(
        "b", "c", "0", "0", tag="exact", avoid=("b", "c")
    )
    assert zero_at == (
        "((exists wie_beta_height_exact. wie_beta_height_exact + S (0) = "
        "S ((S (0)) * c)) /\\ exists wie_beta_quotient_exact. "
        "b = wie_beta_quotient_exact * S ((S (0)) * c) + (0))"
    )
    orbit_scope = nonendpoint("i", "n")
    assert orbit_scope == "(~(i = 0) /\\ ~((S i) = n))"
    orbit_zero_at = orbit_beta_at_zero_index(
        "b", "c", "0", tag="exact"
    )
    assert orbit_zero_at == (
        "((exists wio_beta_height_exact. wio_beta_height_exact + S (0) = "
        "S ((S (0)) * c)) /\\ exists wio_beta_quotient_exact. "
        "b = wio_beta_quotient_exact * S ((S (0)) * c) + (0))"
    )
    assert orbit_zero_at != zero_at
    assert parse_formula(orbit_zero_at) == parse_formula(zero_at)
    predecessor_mod = endpoint_mod_eq(
        "p", "n * n", "1", tag="exact", avoid=("p", "n")
    )
    assert predecessor_mod == (
        "exists wie_mod_left_exact wie_mod_right_exact. "
        "(n * n) + p * wie_mod_left_exact = (1) + p * wie_mod_right_exact"
    )
    zero_index = endpoint_inverse_index_term(
        "p", "n", "0", "0", tag="exact", avoid=("p", "n")
    )
    parsed_zero_index, zero_index_free = parse_formula_with_names(zero_index)
    assert set(zero_index_free) == {"p", "n"}
    assert parsed_zero_index == parse_formula(zero_index)

    local_at = endpoint_beta_at_term(
        "b",
        "c",
        "i",
        "j",
        tag="shared_local",
        avoid=("b", "c", "i", "j"),
    )
    public_at = beta_at("b", "c", "i", "j", tag="shared_public")
    assert local_at != public_at
    assert parse_formula(local_at) == parse_formula(public_at)

    local_index = endpoint_inverse_index_term(
        "p",
        "n",
        "i",
        "j",
        tag="shared_local_index",
        avoid=("p", "n", "i", "j"),
    )
    public_index = prefix_inverse_index(
        "p", "n", "i", "j", tag="shared_public_index"
    )
    assert local_index != public_index
    assert parse_formula(local_index) == parse_formula(public_index)

    surfaces = {
        zero_bound: {"n"},
        zero_at: {"b", "c"},
        orbit_scope: {"i", "n"},
        orbit_zero_at: {"b", "c"},
        predecessor_mod: {"p", "n"},
        successor_positive("i", tag="free_positive"): {"i"},
        involution_successor_strictly_below(
            "i", "p", tag="free_successor_bound"
        ): {"i", "p"},
        inverse_prefix("p", "n", "b", "c", "l", tag="free_prefix"): {
            "p",
            "n",
            "b",
            "c",
            "l",
        },
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    alpha_pairs = (
        (
            endpoint_beta_at_term(
                "b", "c", "0", "0", tag="alpha_left", avoid=("b", "c")
            ),
            endpoint_beta_at_term(
                "b", "c", "0", "0", tag="alpha_right", avoid=("b", "c")
            ),
        ),
        (
            endpoint_mod_eq(
                "p", "n * n", "1", tag="alpha_left_mod", avoid=("p", "n")
            ),
            endpoint_mod_eq(
                "p", "n * n", "1", tag="alpha_right_mod", avoid=("p", "n")
            ),
        ),
        (
            orbit_beta_at_zero_index("b", "c", "i", tag="alpha_left_orbit"),
            orbit_beta_at_zero_index("b", "c", "i", tag="alpha_right_orbit"),
        ),
    )
    for left, right in alpha_pairs:
        assert left != right
        assert parse_formula(left) == parse_formula(right)

    invalid_calls = (
        lambda: endpoint_mod_eq(
            "S p", "n", "1", tag="bad_modulus", avoid=("p", "n")
        ),
        lambda: endpoint_beta_at_term(
            "b + c", "c", "0", "0", tag="bad_code", avoid=("b", "c")
        ),
        lambda: endpoint_strictly_below_term(
            "0", "n", tag="bad tag", avoid=("n",)
        ),
        lambda: nonendpoint("S i", "n"),
        lambda: orbit_beta_at_zero_index(
            "b + c", "c", "0", tag="bad_orbit_code"
        ),
        lambda: orbit_beta_at_zero_index("b", "c", "0", tag="bad tag"),
    )
    for call in invalid_calls:
        with pytest.raises(ValueError, match="Peano identifier|binder tag"):
            call()

    with pytest.raises(ValueError, match="captures an argument"):
        endpoint_mod_eq(
            "p",
            "n",
            "1",
            tag="capture",
            avoid=("p", "n", "wie_mod_left_capture"),
        )

    with pytest.raises(ValueError, match="captures an argument"):
        orbit_beta_at_zero_index(
            "b", "c", "wio_beta_height_capture", tag="capture"
        )


def test_wilson_orbit_graph_is_exact_core_bounded_and_source_isolated() -> None:
    specs = _candidate_specs()
    core = _specs_by_name()
    assert len(specs) == 19
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert len({spec.name for spec in specs}) == 19
    assert all(spec.name not in core for spec in specs)

    local_names = set(EXPECTED_NAMES)
    available = set(core) | local_names
    positions = {spec.name: index for index, spec in enumerate(specs)}
    assert all(
        dependency in available
        for spec in specs
        for dependency in spec.dependencies
    )
    assert all(
        dependency not in positions or positions[dependency] < positions[spec.name]
        for spec in specs
        for dependency in spec.dependencies
    )
    boundary = []
    for spec in specs:
        for dependency in spec.dependencies:
            if dependency not in local_names and dependency not in boundary:
                boundary.append(dependency)
    assert tuple(boundary) == EXPECTED_CORE_BOUNDARY
    assert all(name in core for name in EXPECTED_CORE_BOUNDARY)
    assert tuple(name for name, _ in _CANDIDATE_SOURCES) == (
        "square_one",
        "point",
        "prefix",
        "involution",
        "endpoints",
        "orbit",
    )
    assert all(path.is_file() for _, path in _CANDIDATE_SOURCES)

    by_name = {spec.name: spec for spec in specs}
    assert {
        dependency
        for dependency in by_name["prime_inverse_prefix_exact_endpoints"].dependencies
        if dependency in local_names
    } == {
        "inverse_prefix_zero_fixed",
        "inverse_prefix_last_fixed",
        "prime_inverse_prefix_fixed_cases",
    }
    assert all(
        all("prime" not in dependency for dependency in by_name[name].dependencies)
        for name in PRIME_FREE_INVOLUTION_NAMES
    )

    assert {
        dependency
        for dependency in by_name[
            "prime_inverse_prefix_nonendpoint_not_fixed"
        ].dependencies
        if dependency in local_names
    } == {"prime_inverse_prefix_fixed_cases"}
    assert {
        dependency
        for dependency in by_name[
            "prime_inverse_prefix_nonendpoint_mate"
        ].dependencies
        if dependency in local_names
    } == {
        "prime_inverse_prefix_nonendpoint_not_fixed",
        "inverse_prefix_involutive",
        "inverse_prefix_zero_fixed",
        "inverse_prefix_last_fixed",
    }


def test_wilson_orbit_stack_replays_twice_profiles_full_cut_closure() -> None:
    specs, checked, rows, local, passes, source_digests, graph_digest = (
        _discovery_runs()
    )
    source_map = dict(source_digests)
    print(
        "WMI WILSON ORBIT GRAPH RECEIPT "
        f"nodes={len(EXPECTED_NAMES)} graph_sha256={graph_digest} "
        f"square_source_sha256={source_map['square_one']} "
        f"point_source_sha256={source_map['point']} "
        f"prefix_source_sha256={source_map['prefix']} "
        f"involution_source_sha256={source_map['involution']} "
        f"endpoint_source_sha256={source_map['endpoints']} "
        f"orbit_source_sha256={source_map['orbit']}",
        flush=True,
    )
    for index, receipt in enumerate(passes, start=1):
        print(
            "WMI WILSON ORBIT PASS RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib}",
            flush=True,
        )
    for spec, row in zip(specs, rows, strict=True):
        metadata = _row_metadata(row)
        print(
            "WMI WILSON ORBIT RECEIPT "
            f"name={metadata['name']} nodes={metadata['nodes']} "
            f"depth={metadata['depth']} objects={metadata['objects']} "
            f"edges={metadata['edges']} reused={metadata['reused']} "
            f"cuts={metadata['cuts']} statement_length={metadata['statement_length']} "
            f"spec_sha256={metadata['spec_sha256']} "
            f"statement_sha256={metadata['statement_sha256']} "
            f"script_sha256={metadata['script_sha256']} "
            f"dependencies_sha256={metadata['dependencies_sha256']}",
            flush=True,
        )
        assert metadata["nodes"] <= MAX_USE_CERTIFICATE_NODES
        assert metadata["depth"] <= MAX_USE_PROOF_DEPTH
        assert metadata["objects"] <= MAX_USE_CERTIFICATE_OBJECTS
        theorem = checked[spec.name]
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        _assert_cut_spine(theorem.certificate, spec, local)


def test_wilson_orbit_rejects_false_contracts_and_every_direct_cut_mutation() -> None:
    specs, checked, _, _, _, _, _ = _discovery_runs()
    assert set(_FALSE_CONTRACT_REWRITES) == set(EXPECTED_NAMES)
    for spec in specs:
        theorem = checked[spec.name]
        marker, replacement = _FALSE_CONTRACT_REWRITES[spec.name]
        assert marker != replacement
        assert spec.statement.count(marker) == 1
        false_contract = parse_formula(spec.statement.replace(marker, replacement))
        assert false_contract != theorem.formula
        assert not check((), theorem.certificate, false_contract)

        for index, dependency in enumerate(spec.dependencies):
            mutated = _mutate_cut_at(theorem.certificate, index)
            assert not check((), mutated, theorem.formula), (
                "kernel accepted replaced live dependency edge: "
                f"{spec.name}->{dependency}"
            )
