#!/usr/bin/env python3
"""Build six offline, evidence-honest constructive frontier proof explorers.

The generator reads exact dependency-curried candidate factories, the sealed
Alpha-v15 release, and existing conservative definition templates.  It marks
actual Alpha enrollment separately from checked-use authority and never confers
Alpha/Stable theorem authority; every generated page says so prominently.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import html
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.library import bertrand_defined_edition as defined_adapter  # noqa: E402
from peano_lab.library import editions_v13 as v13  # noqa: E402
from peano_lab.library import editions_v14 as v14  # noqa: E402
from peano_lab.library import editions_v15 as v15  # noqa: E402
from peano_lab.library import four_square_frontier_promotion as four_square_closure  # noqa: E402
from peano_lab.library import lucas_mixed_promotion as lucas_closure  # noqa: E402
from peano_lab.library.bertrand_defined_edition import BERTRAND_DEFINITIONS  # noqa: E402
from peano_lab.library.defined_edition import DefinedEditionError  # noqa: E402
from peano_lab.library.defined_syntax import DEFINITIONS  # noqa: E402
from peano_lab.library.frontier_promotion import (  # noqa: E402
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
)
from peano_lab.library.ha_signed_balance_candidate import signed_balance  # noqa: E402
from peano_lab.library.pythagorean_fermat_four_candidate import (  # noqa: E402
    fermat_four_counterexample,
    fermat_four_strict_descent,
    primitive_pythagorean,
    pythagorean_triple,
)
from peano_lab.library.pythagorean_primitive_candidate import (  # noqa: E402
    opposite_parity,
)
from peano_lab.library.theorems import TheoremSpec, _specs_by_name  # noqa: E402


OUTPUT = REPO / "book" / "_static" / "constructive-frontier-explorer"
DEFINED_EXPLORER_STYLESHEET = (
    REPO / "book" / "_static" / "pa-proof-explorer" / "defined"
    / "assets" / "explorer.css"
)
CANDIDATE_STATUS = (
    "dependency-curried kernel-checked candidate body; "
    "Alpha enrollment varies; not admitted for checked use or Stable"
)
UNENROLLED_CANDIDATE_STATUS = (
    "dependency-curried kernel-checked candidate body; "
    "not enrolled in Alpha or Stable"
)
ALPHA_BODY_STATUS = (
    "Alpha v15 enrolled · body_checked; "
    "not admitted for checked use or Stable"
)
EXPERIMENTAL_CLOSURE_STATUS = (
    "independently replay-verified empty-context experiment; "
    "no persisted certificate, Alpha evidence change, checked-use authority, "
    "or Stable promotion"
)
ALPHA_EDITION_VERSION = "v15"
MANIFEST_SCHEMA = "peano-lab-constructive-frontier-explorer-v1"
MAX_DEFINED_STATEMENT_CHARACTERS = 12_000
MAX_DEFINED_ROOT_STATEMENT_CHARACTERS = 42_000
MAX_DEFINED_TACTIC_PROPOSITION_CHARACTERS = 2_400
MAX_DEFINED_TACTIC_PROPOSITIONS_PER_NODE = 2
MAX_DEFINED_TACTIC_PROPOSITIONS_PER_ROOT = 4


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    title: str
    kicker: str
    formula: str
    description: str
    scope: str
    roots: tuple[str, ...]
    factories: tuple[tuple[str, str], ...]
    definition_names: tuple[str, ...]
    example: str
    optional_module_prefix: str | None = None
    factory_name_filters: tuple[tuple[str, tuple[str, ...]], ...] = ()


FAMILIES = (
    Family(
        slug="supplementary-laws",
        title="Quadratic Supplementary Laws",
        kicker="Residues of −1 and 2",
        formula="(−1|p) = (−1)^((p−1)/2) · (2|p) = (−1)^((p²−1)/8)",
        description="Follow the complete constructive modulo-four and modulo-eight residue classifications.",
        scope="Both supplementary-law endpoint bodies and their authentic bounded Euler-criterion and Gauss-lemma prerequisites are enrolled in Alpha v15 as body_checked, without checked-use authority or Stable admission.",
        roots=("quadratic_supplement_minus_one_complete", "quadratic_supplement_two_complete"),
        factories=(
            ("euler_criterion_bounded_candidate", "make_euler_criterion_bounded_candidate_theorems"),
            ("quadratic_supplement_minus_one_candidate", "make_quadratic_supplement_minus_one_candidate_theorems"),
            ("gauss_lemma_bounded_candidate", "make_gauss_lemma_bounded_candidate_theorems"),
            ("quadratic_supplement_two_candidate", "make_quadratic_supplement_two_candidate_theorems"),
        ),
        definition_names=("Prime", "Odd", "Even", "Mod4One", "Mod4Three", "ModEq", "QRes", "BoundedQRes", "BetaAt", "BitCount", "Mod8One", "Mod8Three", "Mod8Five", "Mod8Seven"),
        example="supplementary",
        factory_name_filters=(
            ("euler_criterion_bounded_candidate", ("bounded_euler_criterion_complete",)),
            ("gauss_lemma_bounded_candidate", ("bounded_gauss_lemma_complete",)),
        ),
    ),
    Family(
        slug="kummer",
        title="Kummer’s Carry Theorem",
        kicker="Binomial valuations",
        formula="vₚ (a+b choose a) = number of base-p carries in a+b",
        description="Inspect the constructive bridge from Legendre valuations to explicitly counted addition carries.",
        scope="The exact binomial-carry endpoint, its carry-free corollary, and their minimal prerequisite closure were first enrolled in Alpha v14 as body_checked and remain in Alpha v15 without checked-use authority or Stable admission.",
        roots=("kummer_binomial_carry_bit_count", "kummer_carry_free_iff_not_divides"),
        factories=(
            ("kummer_valuation_candidate", "make_kummer_valuation_candidate_theorems"),
            ("kummer_carry_candidate", "make_kummer_carry_candidate_theorems"),
            ("kummer_carry_candidate", "make_kummer_carry_corollary_candidate_theorems"),
        ),
        definition_names=("Prime", "Choose", "Factorial", "PowerValuation", "PowerDivides", "LegendreSum", "BetaAt", "BitCount", "AllBits", "Sum", "Carry"),
        example="kummer",
    ),
    Family(
        slug="two-squares",
        title="Fermat and Sums of Two Squares",
        kicker="Prime representations and constructive classification",
        formula="n = x²+y² ⇔ n = 0 or every p ≡ 3 (mod 4) has even vₚ(n)",
        description="Explore the complete constructive all-natural two-square classification: prime representations, multiplication, valuation necessity, strictly decreasing sufficiency, and the explicit zero boundary.",
        scope="The complete all-natural iff, its nonzero specialization, prime classification, Brahmagupta–Fibonacci multiplication, and explicit constructive witnesses are kernel-checked dependency-curried candidate bodies; the complete classification and its exact prerequisite closure are enrolled in Alpha v15 as body_checked, without checked-use authority or Stable admission.",
        roots=(
            "prime_mod_four_one_is_sum_of_two_squares",
            "brahmagupta_fibonacci_two_square_identity",
            "two_square_representation_multiplicatively_closed",
            "three_mod_four_prime_divides_two_square_norm_divides_both",
            "prime_power_valuation_square_even",
            "three_mod_four_prime_nonzero_norm_positive_valuation_extracts",
            "three_mod_four_prime_represented_nonzero_valuation_even",
            "beta_two_square_represented_factor_product",
            "beta_grouped_prime_square_factor_product_is_two_square",
            "positive_number_with_admissible_prime_divisors_is_two_square",
            "even_valuation_sorted_terminal_prime_has_equal_predecessor",
            "two_square_product_is_two_square",
            "two_square_representations_closed_under_multiplication",
            "prime_is_two_squares_iff_two_or_one_mod_four",
            "all_bad_prime_even_two_square_sufficiency_bounded",
            "positive_number_with_even_bad_prime_valuations_is_two_square",
            "nonzero_two_square_iff_even_three_mod_four_prime_valuations",
            "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
        ),
        factories=(
            ("fermat_two_squares_candidate", "make_fermat_two_squares_candidate_theorems"),
            ("fermat_two_squares_pigeonhole_candidate", "make_fermat_two_squares_pigeonhole_candidate_theorems"),
            ("finite_prefix_collision_decision_candidate", "make_finite_prefix_collision_decision_candidate_theorems"),
            ("fermat_two_squares_residue_grid_candidate", "make_fermat_two_squares_residue_grid_candidate_theorems"),
            ("fermat_two_squares_collision_norm_candidate", "make_fermat_two_squares_collision_norm_candidate_theorems"),
            ("fermat_two_squares_prime_candidate", "make_fermat_two_squares_prime_candidate_theorems"),
            ("fermat_two_squares_classification_candidate", "make_fermat_two_squares_classification_candidate_theorems"),
        ),
        definition_names=("Prime", "Mod4One", "Mod4Three", "QRes", "BoundedQRes", "FloorSqrt", "ModEq", "Dvd", "BetaAt", "InjectivePrefix", "AllPrime", "Sorted", "PowerValuation", "SumTwoSquares", "AbsoluteDifference"),
        example="two-squares",
        optional_module_prefix="fermat_two_squares_",
    ),
    Family(
        slug="four-squares",
        title="Lagrange’s Four-Square Theorem",
        kicker="Complete constructive universal representation",
        formula="∀ n ∈ ℕ. ∃ a,b,c,d. n = a² + b² + c² + d²",
        description="Explore the complete constructive proof that every natural number is a sum of four squares: both Euler quaternion identities, actual bounded prime seeds, all sixteen signed orientations, strict multiplier descent, and explicit prime-factor witnesses.",
        scope="The complete universal Lagrange four-square theorem, representation of every prime, complete eight-variable Euler identity and signed-conjugate identity, explicit multiplicative closure, constructive modular seeds for every prime, all sixteen signed centered orientations, and bounded strict prime-multiple descent are kernel-checked dependency-curried bodies; the universal endpoint and its exact prerequisite closure are enrolled in Alpha v13 as body_checked, without checked-use authority or Stable admission.",
        roots=(
            "quaternion_coordinate_square_balance_total",
            "quaternion_coordinate_absolute_total",
            "four_square_norm_distributes",
            "four_square_two_square_factor_identity",
            "four_square_two_square_factor_total",
            "four_square_euler_all_mixed_cancel",
            "four_square_euler_quaternion_conditional",
            "four_square_euler_three_square_expansion",
            "four_square_euler_add_permute_sixteen",
            "four_square_euler_coordinate_triple_decompose",
            "four_square_euler_global_compensation",
            "four_square_euler_quaternion",
            "four_square_euler_four_square_product_total",
            "four_square_euler_representations_closed_under_multiplication",
            "four_square_prime_two_or_one_mod_four",
            "four_square_lagrange_bounded_from_primes",
            "four_square_lagrange_from_all_primes",
            "four_square_lagrange_from_three_mod_four_primes",
            "four_square_lagrange_iff_three_mod_four_primes",
            "four_square_cross_interleaved_prefix_exists",
            "four_square_cross_intersection",
            "four_square_prime_half_square_residues_injective",
            "four_square_square_residue_prefix_exists",
            "four_square_half_square_residue_prefix_injective",
            "four_square_bounded_complement_prefix_exists",
            "four_square_odd_prime_modular_seed",
            "four_square_non_two_prime_modular_seed",
            "four_square_prime_modular_seed",
            "four_square_odd_prime_half_coordinate_seed",
            "four_square_odd_prime_half_seed_norm_strict",
            "four_square_odd_prime_bounded_modular_seed",
            "four_square_non_two_prime_bounded_modular_seed",
            "four_square_prime_bounded_modular_seed",
            "four_square_descent_quaternion_quotient",
            "four_square_descent_centered_signed_remainder_exists",
            "four_square_descent_centered_four_remainders_exist",
            "four_square_descent_even_multiplier_matching_parity_halving",
            "four_square_parity_even_norm_pair_selection",
            "four_square_parity_even_multiplier_halving",
            "four_square_parity_represented_double_halving",
            "four_square_parity_represented_additive_double_halving",
            "four_square_descent_odd_centered_norm_strict",
            "four_square_descent_bounded_centered_quotient_nonzero",
            "four_square_descent_odd_centered_strict_step",
            "four_square_branch_even_represented_strict_step",
            "four_square_bounded_strict_descent_from_odd_signed_quaternion",
            "four_square_signed_centered_square_congruent",
            "four_square_signed_centered_norm_congruent",
            "four_square_signed_centered_norm_quotient_exists",
            "four_square_signed_absolute_congruence_divisible",
            "four_square_signed_conjugate_positive_blocks",
            "four_square_signed_conjugate_negative_blocks",
            "four_square_signed_conjugate_mixed_blocks",
            "four_square_signed_natural_negative_first_blocks",
            "four_square_signed_natural_positive_first_blocks",
            "four_square_signed_divisible_norm_product_representation",
            "four_square_signed_absolute_block_representation",
            "four_square_signed_orientation_mask_00",
            "four_square_signed_orientation_mask_03",
            "four_square_signed_orientation_mask_07",
            "four_square_signed_orientation_mask_15",
            "four_square_signed_centered_representation",
            "four_square_conjugate_global_compensation",
            "four_square_signed_conjugate_quaternion",
            "four_square_conjugate_absolute_coordinates_total",
            "four_square_descent_strict_step_from_centered_quaternion",
            "four_square_lagrange_from_modular_seeds_and_strict_descent",
            "four_square_prime_from_strict_descent",
            "four_square_lagrange_from_strict_descent",
            "four_square_descent_below_prime_multiplier_bounded",
            "four_square_prime_from_bounded_strict_descent_and_seed",
            "four_square_prime_from_bounded_strict_descent",
            "four_square_lagrange_from_bounded_strict_descent",
            "four_square_prime_from_odd_signed_quaternion",
            "four_square_lagrange_from_odd_signed_quaternion",
            "four_square_prime_representation",
            "four_square_lagrange",
        ),
        factories=(("four_square_identity_candidate", "make_four_square_identity_candidate_theorems"),),
        definition_names=("Prime", "Le", "Lt", "Dvd", "ModEq", "Product", "SignedBalance", "AbsoluteDifference", "SumTwoSquares", "FourSquareNorm"),
        example="four-squares",
        optional_module_prefix="four_square_",
    ),
    Family(
        slug="lucas",
        title="Lucas’s Multidigit Binomial Theorem",
        kicker="Complete constructive base-p digitwise congruence",
        formula="n = Σ nᵢpⁱ · k = Σ kᵢpⁱ · (n choose k) ≡ ∏ (nᵢ choose kᵢ) (mod p)",
        description="Explore the complete unconditional constructive multidigit Lucas congruence, genuinely terminating beta-coded digit chains, exact prime-block Pascal identities, coefficient streams, and witnessed digitwise products.",
        scope="The complete arbitrary-length multidigit Lucas congruence, terminating beta-coded quotient/digit chains, actual coefficient/product witnesses, and unrestricted prime-block one-step identity are kernel-checked dependency-curried bodies; the multidigit endpoint and its exact prerequisite closure are enrolled in Alpha v13 as body_checked, without checked-use authority or Stable admission.",
        roots=(
            "lucas_digit_carry_iff_prime_divides",
            "lucas_digit_no_carry_iff_not_divides",
            "lucas_base_p_digit_functional",
            "lucas_prime_base_digit_prefix_exists",
            "lucas_base_p_digit_prefix_point",
            "lucas_base_p_two_digit_reconstruction",
            "lucas_base_p_two_digit_total",
            "lucas_prime_row_sparse_complete",
            "lucas_prime_row_interior_zero_mod",
            "lucas_pascal_congruence_step",
            "lucas_prime_shift_below_base",
            "lucas_prime_shift_high_column",
            "lucas_repeated_prime_shift_below_base",
            "lucas_low_digit_product_congruence",
            "lucas_zero_upper_quotient_high_column_vanishes",
            "lucas_prime_block_digit_congruence",
            "lucas_one_step_division_congruence",
            "lucas_digit_chain_exists",
            "lucas_prime_digit_chain_exists",
            "lucas_digit_chain_step_exists",
            "lucas_choose_prefix_exists",
            "lucas_choose_prefix_point",
            "lucas_modular_backward_product_fold",
            "lucas_multidigit_congruence_from_one_step",
            "lucas_terminating_multidigit_theorem_from_one_step",
            "lucas_prime_digit_chain_terminal_zero",
            "lucas_terminating_prime_digit_chain_exists",
            "lucas_multidigit_congruence",
            "lucas_terminating_multidigit_theorem",
            "lucas_theorem_for_length",
            "lucas_theorem",
        ),
        factories=(("lucas_digit_candidate", "make_lucas_digit_candidate_theorems"),),
        definition_names=("Prime", "Lt", "Le", "Choose", "Factorial", "Dvd", "ModEq", "Product", "Sum", "PowerValuation", "Carry", "Digit", "BetaAt"),
        example="lucas",
        optional_module_prefix="lucas_",
    ),
    Family(
        slug="pythagorean-fermat-four",
        title="Pythagorean Triples and Fermat’s Fourth-Power Descent",
        kicker="Complete forward primitive parametrization and an explicit open descent obligation",
        formula="x²+y²=z² · gcd(x,y)=1 · conditional descent: x⁴+y⁴≠z²",
        description="Construct exact primitive Euclidean Pythagorean triples, inspect the opposite-parity, odd-hypotenuse, pairwise-coprime normal form of every primitive triple, and isolate the one still-unproved strict-descent premise behind Fermat’s exponent-four theorem.",
        scope="Euclid’s complete forward primitive Pythagorean constructor from ordered coprime opposite-parity parameters, witnessed square differences, the opposite-parity/odd-hypotenuse/pairwise-coprime normal form of every primitive triple, and conditional bounded-descent bridges are dependency-curried kernel-checked candidate bodies. The primitive inverse classification and the Fermat strict-descent premise remain unproved; no candidate in this family is enrolled in Alpha or Stable.",
        roots=(
            "pythagorean_euclidean_identity",
            "pythagorean_euclidean_from_order",
            "pythagorean_primitive_leg_swap",
            "pythagorean_opposite_parity_hypotenuse_odd",
            "pythagorean_primitive_euclidean_legs",
            "pythagorean_primitive_euclidean_constructor",
            "pythagorean_primitive_euclidean_from_order",
            "pythagorean_primitive_euclidean_swapped_constructor",
            "pythagorean_primitive_pairwise_coprime",
            "pythagorean_primitive_legs_not_both_even",
            "pythagorean_triple_legs_not_both_odd",
            "pythagorean_primitive_legs_opposite_parity",
            "pythagorean_primitive_hypotenuse_odd",
            "pythagorean_primitive_normal_form",
            "fermat_four_bounded_descent",
            "fermat_four_no_square_from_descent",
            "fermat_four_no_fourth_from_descent",
        ),
        factories=(
            (
                "pythagorean_fermat_four_candidate",
                "make_pythagorean_fermat_four_candidate_theorems",
            ),
        ),
        definition_names=(
            "Pythagorean",
            "Coprime",
            "OppositeParity",
            "PrimitivePythagorean",
            "FermatFourCounterexample",
            "FermatFourStrictDescent",
            "Le",
            "Lt",
            "Dvd",
            "Odd",
            "Even",
        ),
        example="pythagorean",
        optional_module_prefix="pythagorean_",
    ),
)


def _digest(value: str | bytes) -> str:
    return sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _custom_definitions() -> dict[str, dict[str, Any]]:
    records = (
        ("CF0001", "AbsoluteDifference", ("a", "b", "d"), "a = b + d \\/ b = a + d", "d is an explicitly witnessed natural absolute difference."),
        ("CF0002", "SumTwoSquares", ("n",), "exists x y. n = x * x + y * y", "n has explicitly witnessed natural two-square coordinates."),
        ("CF0003", "FourSquareNorm", ("n", "a", "b", "c", "d"), "n = a * a + b * b + c * c + d * d", "n is the natural norm of four displayed coordinates."),
        ("CF0004", "SignedBalance", ("code", "left", "right"), signed_balance("code", "left", "right", tag="frontier"), "A conservative signed-natural code balances the formal difference left−right."),
        ("CF0005", "Carry", ("p", "a", "b"), "exists q. q + p = a + b", "The sum of two natural digits is at least the base p."),
        ("CF0006", "Mod8One", ("p",), "exists q. p = 8 * q + 1", "p is one modulo eight with a witnessed quotient."),
        ("CF0007", "Mod8Three", ("p",), "exists q. p = 8 * q + 3", "p is three modulo eight with a witnessed quotient."),
        ("CF0008", "Mod8Five", ("p",), "exists q. p = 8 * q + 5", "p is five modulo eight with a witnessed quotient."),
        ("CF0009", "Mod8Seven", ("p",), "exists q. p = 8 * q + 7", "p is seven modulo eight with a witnessed quotient."),
        ("CF0010", "Digit", ("p", "n", "q", "d"), "(n = p * q + d) /\\ exists h. h + S d = p", "A base-p digit d and quotient q satisfy n = p·q+d with the witnessed strict bound d<p."),
        ("CF0011", "Pythagorean", ("x", "y", "z"), pythagorean_triple("x", "y", "z"), "The three natural coordinates satisfy the exact Pythagorean equation x²+y²=z²."),
        ("CF0013", "PrimitivePythagorean", ("x", "y", "z"), primitive_pythagorean("x", "y", "z", tag="frontier"), "The displayed Pythagorean triple has explicitly coprime natural legs."),
        ("CF0014", "FermatFourCounterexample", ("x", "y", "z"), fermat_four_counterexample("x", "y", "z", tag="frontier"), "Nonzero natural coordinates witness the stronger counterexample x⁴+y⁴=z²."),
        ("CF0015", "FermatFourStrictDescent", (), fermat_four_strict_descent(tag="frontier"), "Every positive fourth-power counterexample produces another with a strictly smaller natural hypotenuse; this premise remains unproved."),
        ("CF0016", "OppositeParity", ("m", "n"), opposite_parity("m", "n", tag="frontier"), "The Euclidean parameters have explicitly witnessed opposite natural parity."),
    )
    result: dict[str, dict[str, Any]] = {}
    for identifier, name, parameters, template, summary in records:
        parse_formula_in_context(template, list(parameters))
        result[name] = {
            "id": identifier,
            "name": name,
            "parameters": list(parameters),
            "summary": summary,
            "expanded_template": template,
            "template_sha256": _digest(template),
            "origin": "frontier-conservative-display-alias",
        }
    return result


def _definition_table() -> dict[str, dict[str, Any]]:
    table: dict[str, dict[str, Any]] = {}
    for definition in (*DEFINITIONS, *BERTRAND_DEFINITIONS):
        table[definition.name] = {
            "id": definition.stable_id,
            "name": definition.name,
            "parameters": list(definition.parameters),
            "summary": definition.summary,
            "expanded_template": definition.template_source,
            "template_sha256": _digest(definition.template_source),
            "origin": "existing-conservative-definition",
        }
    for name, custom in _custom_definitions().items():
        existing = table.get(name)
        if existing is None:
            table[name] = custom
            continue
        existing_formula = parse_formula_in_context(
            existing["expanded_template"], existing["parameters"]
        )
        custom_formula = parse_formula_in_context(
            custom["expanded_template"], custom["parameters"]
        )
        if existing_formula != custom_formula:
            raise ValueError(
                f"constructive definition {name!r} shadows an incompatible "
                "existing conservative definition"
            )
    return table


def _verified_compaction(
    compacted: Any,
    *,
    source: str,
    known_definitions: Mapping[str, Mapping[str, Any]],
    context: str,
) -> tuple[dict[str, Any], list[dict[str, str]], Counter[str]]:
    """Reject every source, definition, or AST-equivalence receipt mismatch."""

    receipt = compacted.receipt
    source_sha256 = _digest(source)
    if compacted.expanded_source != source:
        raise ValueError(f"{context}: compaction changed the exact source")
    if not receipt.exact_ast_equivalence:
        raise ValueError(f"{context}: compaction lacks exact AST equivalence")
    if receipt.expanded_source_sha256 != source_sha256:
        raise ValueError(f"{context}: expanded source SHA-256 mismatch")
    if receipt.defined_source_sha256 != _digest(compacted.defined_source):
        raise ValueError(f"{context}: defined source SHA-256 mismatch")
    if receipt.expanded_characters != len(source):
        raise ValueError(f"{context}: expanded source character count mismatch")
    if receipt.defined_characters != len(compacted.defined_source):
        raise ValueError(f"{context}: defined source character count mismatch")

    parts = [part.as_json() for part in compacted.parts]
    if "".join(part["text"] for part in parts) != compacted.defined_source:
        raise ValueError(f"{context}: defined parts do not reconstruct their source")
    uses = Counter(
        part["definition"] for part in parts if part["kind"] == "definition"
    )
    expected_uses = Counter(
        {use.definition_id: use.occurrences for use in receipt.definition_uses}
    )
    if uses != expected_uses:
        raise ValueError(f"{context}: linked-definition use count mismatch")
    for use in receipt.definition_uses:
        definition = known_definitions.get(use.definition_id)
        if definition is None or definition["name"] != use.name:
            raise ValueError(f"{context}: unreviewed or inconsistent definition {use.name}")

    return (
        {
            "expanded_source_sha256": receipt.expanded_source_sha256,
            "defined_source_sha256": receipt.defined_source_sha256,
            "canonical_expansion_sha256": receipt.canonical_expansion_sha256,
            "free_names": list(receipt.free_names),
            "expanded_characters": receipt.expanded_characters,
            "defined_characters": receipt.defined_characters,
            "exact_ast_equivalence": True,
            "definition_uses": [
                {
                    "id": use.definition_id,
                    "name": use.name,
                    "occurrences": use.occurrences,
                }
                for use in receipt.definition_uses
            ],
        },
        parts,
        uses,
    )


def _defined_node(
    node: Mapping[str, Any],
    known_definitions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a bounded, fail-closed conservative reading surface for one row."""

    source = str(node["statement"])
    exact_sha256 = _digest(source)
    if exact_sha256 != node["statement_sha256"]:
        raise ValueError(f"theorem {node['name']}: immutable statement SHA-256 mismatch")

    limit = (
        MAX_DEFINED_ROOT_STATEMENT_CHARACTERS
        if node["root"]
        else MAX_DEFINED_STATEMENT_CHARACTERS
    )
    defined_statement = source
    statement_parts: list[dict[str, str]] = [{"kind": "text", "text": source}]
    statement_receipt: dict[str, Any] | None = None
    statement_uses: Counter[str] = Counter()
    if len(source) > limit:
        statement_status = "exact-only-size-budget"
    else:
        try:
            compacted = defined_adapter.compact_formula_source(source)
        except DefinedEditionError:
            statement_status = "exact-only-compaction-unavailable"
        else:
            statement_receipt, statement_parts, statement_uses = _verified_compaction(
                compacted,
                source=source,
                known_definitions=known_definitions,
                context=f"theorem {node['name']}",
            )
            defined_statement = compacted.defined_source
            statement_status = "exact-ast-equivalent"

    tactic_budget = (
        MAX_DEFINED_TACTIC_PROPOSITIONS_PER_ROOT
        if node["root"]
        else MAX_DEFINED_TACTIC_PROPOSITIONS_PER_NODE
    )
    considered = 0
    compact_lines: list[dict[str, Any]] = []
    script_uses: Counter[str] = Counter()
    skipped_lines = 0
    for number, command in enumerate(node["script"], start=1):
        stripped = command.strip()
        if not stripped.startswith(("have ", "suffices ")):
            continue
        _prefix, separator, proposition_source = stripped.partition(":")
        if not separator or len(proposition_source.strip()) > MAX_DEFINED_TACTIC_PROPOSITION_CHARACTERS:
            skipped_lines += 1
            continue
        if considered >= tactic_budget:
            skipped_lines += 1
            continue
        considered += 1
        try:
            tactic = defined_adapter.compact_tactic_command(command, number)
        except DefinedEditionError:
            skipped_lines += 1
            continue
        if tactic.line_number != number or tactic.expanded_command != command:
            raise ValueError(f"theorem {node['name']} line {number}: exact source changed")
        if tactic.proposition is None:
            raise ValueError(f"theorem {node['name']} line {number}: proposition receipt missing")
        proposition_receipt, _parts, proposition_uses = _verified_compaction(
            tactic.proposition,
            source=proposition_source.strip(),
            known_definitions=known_definitions,
            context=f"theorem {node['name']} line {number}",
        )
        command_parts = [part.as_json() for part in tactic.parts]
        if "".join(part["text"] for part in command_parts) != tactic.defined_command:
            raise ValueError(f"theorem {node['name']} line {number}: command parts mismatch")
        command_uses = Counter(
            part["definition"] for part in command_parts if part["kind"] == "definition"
        )
        if command_uses != proposition_uses:
            raise ValueError(f"theorem {node['name']} line {number}: command definition mismatch")
        if tactic.defined_command == command:
            continue
        compact_lines.append(
            {
                "number": number,
                "defined_command": tactic.defined_command,
                "expanded_command_sha256": _digest(command),
                "command_parts": command_parts,
                "proposition_receipt": proposition_receipt,
            }
        )
        script_uses.update(command_uses)

    total_uses = statement_uses + script_uses
    return {
        "defined_statement": defined_statement,
        "expanded_statement_sha256": exact_sha256,
        "statement_status": statement_status,
        "statement_receipt": statement_receipt,
        "statement_parts": statement_parts,
        "statement_definition_uses": dict(sorted(statement_uses.items())),
        "defined_script_lines": compact_lines,
        "skipped_tactic_propositions": skipped_lines,
        "script_definition_uses": dict(sorted(script_uses.items())),
        "definition_uses": dict(sorted(total_uses.items())),
    }


def _factory_sources(family: Family) -> tuple[tuple[str, str], ...]:
    sources = list(family.factories)
    known = {module for module, _factory in sources}
    if family.optional_module_prefix is not None:
        library = PY_ROOT / "peano_lab" / "library"
        for path in sorted(library.glob(f"{family.optional_module_prefix}*candidate.py")):
            module_name = path.stem
            if module_name in known:
                continue
            module = importlib.import_module(f"peano_lab.library.{module_name}")
            factory_name = f"make_{module_name.removesuffix('_candidate')}_candidate_theorems"
            factory = getattr(module, factory_name, None)
            if callable(factory):
                sources.append((module_name, factory_name))
                known.add(module_name)
    return tuple(sources)


def _alpha_frontier_campaigns() -> dict[str, Any]:
    """Retain exact historical campaign provenance across additive releases."""

    return {
        **v13.alpha_v13_enrollment().campaign_by_name,
        **v14.alpha_v14_enrollment().campaign_by_name,
        **v15.alpha_v15_enrollment().campaign_by_name,
    }


def _alpha_admission_versions() -> dict[str, str]:
    """Identify original enrollment separately from the active edition."""

    return {
        **{name: "v13" for name in v13.FRONTIER_V13_EXPECTED_NAMES},
        **{name: "v14" for name in v14.FRONTIER_V14_EXPECTED_NAMES},
        **{name: "v15" for name in v15.FRONTIER_V15_EXPECTED_NAMES},
    }


def _verified_experimental_names(
    names: object,
    *,
    allowed: set[str],
    source: str,
    batch_limit: bool = True,
) -> tuple[str, ...]:
    """Validate named checked experiments without manufacturing a proof receipt."""

    if type(names) is not tuple or not names:
        raise ValueError(f"{source} must contain an exact nonempty named tuple")
    if any(type(name) is not str for name in names):
        raise ValueError(f"{source} contains a non-string experimental theorem")
    if len(set(names)) != len(names):
        raise ValueError(f"{source} repeats an experimental theorem")
    if batch_limit and len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise ValueError(f"{source} exceeds the unchanged experimental microbatch limit")
    unexpected = set(names).difference(allowed)
    if unexpected:
        raise ValueError(
            f"{source} contains noncampaign experimental rows: {sorted(unexpected)!r}"
        )
    for name in names:
        old = v13.ALPHA_EDITION.by_name.get(name)
        current = v15.ALPHA_EDITION.by_name.get(name)
        if (
            old is None
            or current is None
            or old.spec != current.spec
            or old.evidence is not v13.EvidenceStatus.BODY_CHECKED
            or current.evidence is not v15.EvidenceStatus.BODY_CHECKED
            or old.checked_use
            or current.checked_use
        ):
            raise ValueError(
                f"{source} does not match the sealed body-only Alpha entry {name!r}"
            )
    return names


def _checked_experimental_diagnostics(
    diagnostics: object,
    *,
    expected_names: tuple[str, ...],
    source: str,
) -> tuple[tuple[str, int, int], ...]:
    """Bind actual prior replay diagnostics to exactly their named proof batch."""

    if type(diagnostics) is not tuple or len(diagnostics) != len(expected_names):
        raise ValueError(f"{source} has incomplete checked experimental diagnostics")
    if any(
        type(item) is not tuple
        or len(item) != 3
        or type(item[0]) is not str
        or type(item[1]) is not int
        or type(item[2]) is not int
        or item[1] <= 0
        or item[2] <= 0
        or item[1] > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
        or item[2] > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        for item in diagnostics
    ):
        raise ValueError(f"{source} exceeds immutable experimental proof limits")
    if tuple(item[0] for item in diagnostics) != expected_names:
        raise ValueError(f"{source} checked experimental names differ from their batch")
    return diagnostics


@lru_cache(maxsize=1)
def _experimental_closure_campaigns() -> dict[str, dict[str, Any]]:
    """Expose only named, previously checked experiments; never replay proofs."""

    lucas_plan = lucas_closure.lucas_campaign_closure_plan()
    lucas_allowed = {row.name for row in lucas_plan.rows}
    if len(lucas_allowed) != lucas_closure.LUCAS_CAMPAIGN_EXPECTED_COUNT:
        raise ValueError("Lucas experimental campaign differs from its sealed slice")
    if lucas_plan.parent_alpha_identity_sha256 != v13.ALPHA_V13_IDENTITY_SHA256:
        raise ValueError("Lucas experimental campaign has an unsealed Alpha parent")

    lucas_batches: list[tuple[str, tuple[str, ...]]] = []
    for label, names in (
        ("lucas-initial", lucas_closure.LUCAS_CAMPAIGN_INITIAL_MICROBATCH),
        ("lucas-second", lucas_closure.LUCAS_CAMPAIGN_SECOND_MICROBATCH),
        ("lucas-third", lucas_closure.LUCAS_CAMPAIGN_THIRD_MICROBATCH),
        ("lucas-fourth", lucas_closure.LUCAS_CAMPAIGN_FOURTH_MICROBATCH),
    ):
        lucas_batches.append(
            (
                label,
                _verified_experimental_names(
                    names, allowed=lucas_allowed, source=f"{label} microbatch"
                ),
            )
        )
    shared_checked = getattr(lucas_closure, "LUCAS_CAMPAIGN_SHARED_CHECKED_NAMES", ())
    if shared_checked:
        checked_diagnostics = getattr(
            lucas_closure, "LUCAS_CAMPAIGN_SHARED_CHECKED_DIAGNOSTICS", ()
        )
        if (
            type(checked_diagnostics) is not tuple
            or len(checked_diagnostics) != len(shared_checked)
            or any(
                type(item) is not tuple
                or len(item) != 4
                or type(item[0]) is not str
                or any(type(value) is not int or value <= 0 for value in item[1:])
                or item[1] > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
                or item[2] > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
                or item[3] > MAX_FRONTIER_CLOSURE_MICROBATCH
                for item in checked_diagnostics
            )
            or tuple(item[0] for item in checked_diagnostics) != shared_checked
        ):
            raise ValueError(
                "Lucas shared checked experimental names lack matching bounded replay diagnostics"
            )
        lucas_batches.append(
            (
                "lucas-shared-checked",
                _verified_experimental_names(
                    shared_checked,
                    allowed=lucas_allowed,
                    source="Lucas independently checked shared roots",
                ),
            )
        )

    four_plan = four_square_closure.four_square_frontier_plan()
    four_allowed = {row.name for row in four_plan.campaign_obligations}
    four_parents = {row.name for row in four_plan.parent_obligations}
    if (
        len(four_allowed) != four_square_closure.FOUR_SQUARE_FRONTIER_CAMPAIGN_COUNT
        or len(four_parents)
        != four_square_closure.FOUR_SQUARE_FRONTIER_PARENT_COUNT
        or four_plan.source.parent_alpha_identity_sha256
        != v13.ALPHA_V13_IDENTITY_SHA256
    ):
        raise ValueError("four-square experimental campaign differs from its sealed slice")

    four_batches: list[tuple[str, tuple[str, ...]]] = []
    initial_batches = four_square_closure.four_square_initial_campaign_batches()
    initial_checked = (
        four_square_closure.FOUR_SQUARE_INITIAL_CAMPAIGN_CHECKED_BATCH_DIAGNOSTICS
    )
    if len(initial_batches) != len(initial_checked):
        raise ValueError("four-square initial checked microbatch diagnostics are incomplete")
    for batch, checked in zip(initial_batches, initial_checked, strict=True):
        if (
            type(checked) is not tuple
            or len(checked) != 3
            or checked[0] != len(batch.names)
            or any(type(value) is not int or value <= 0 for value in checked)
            or checked[1] > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
            or checked[2] > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
        ):
            raise ValueError("four-square initial checked microbatch exceeds immutable limits")
        label = f"four-square-initial-{batch.index + 1}"
        four_batches.append(
            (
                label,
                _verified_experimental_names(
                    batch.names, allowed=four_allowed, source=f"{label} microbatch"
                ),
            )
        )

    second_names = _verified_experimental_names(
        four_square_closure.FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES,
        allowed=four_allowed,
        source="four-square independently checked second layer",
    )
    _checked_experimental_diagnostics(
        four_square_closure.FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_CHECKED_DIAGNOSTICS,
        expected_names=second_names,
        source="four-square second layer",
    )
    four_batches.append(("four-square-second-layer", second_names))

    continuation_checked = getattr(
        four_square_closure,
        "FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_DIAGNOSTICS",
        (),
    )
    if continuation_checked:
        continuation_names = _verified_experimental_names(
            four_square_closure.FOUR_SQUARE_CAMPAIGN_CONTINUATION_NAMES,
            allowed=four_allowed,
            source="four-square independently checked continuation",
        )
        _checked_experimental_diagnostics(
            continuation_checked,
            expected_names=continuation_names,
            source="four-square continuation",
        )
        four_batches.append(("four-square-continuation", continuation_names))

    non_beta = _verified_experimental_names(
        four_square_closure.FOUR_SQUARE_NON_BETA_PARENT_NAMES,
        allowed=four_parents,
        source="four-square checked non-beta parents",
        batch_limit=False,
    )
    non_beta_checked = (
        four_square_closure.FOUR_SQUARE_NON_BETA_MICROBATCH_DIAGNOSTICS
    )
    _checked_experimental_diagnostics(
        non_beta_checked,
        expected_names=non_beta[:MAX_FRONTIER_CLOSURE_MICROBATCH],
        source="four-square checked non-beta parent microbatch",
    )
    established = {
        name
        for name, _nodes in four_square_closure.FOUR_SQUARE_ESTABLISHED_PARENT_DIAGNOSTICS
    }
    if not set(non_beta[MAX_FRONTIER_CLOSURE_MICROBATCH:]) <= established:
        raise ValueError("four-square remaining non-beta parents lack checked diagnostics")

    beta = _verified_experimental_names(
        four_square_closure.FOUR_SQUARE_BETA_PARENT_NAMES,
        allowed=four_parents,
        source="four-square checked beta parent singletons",
    )
    _checked_experimental_diagnostics(
        four_square_closure.FOUR_SQUARE_BETA_PARENT_CHECKED_DIAGNOSTICS,
        expected_names=beta,
        source="four-square beta parent singleton replays",
    )
    parent_names = non_beta + beta
    if set(parent_names) != four_parents:
        raise ValueError("four-square checked parent experiments omit sealed rows")

    policies = {
        "max_microbatch_rows": MAX_FRONTIER_CLOSURE_MICROBATCH,
        "max_proof_nodes": MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        "max_proof_objects": MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    }
    result: dict[str, dict[str, Any]] = {}
    for slug, campaign, root, total, batches, checked_parents, parent_total in (
        (
            "lucas",
            "lucas",
            "lucas_theorem",
            lucas_closure.LUCAS_CAMPAIGN_EXPECTED_COUNT,
            lucas_batches,
            (),
            len(lucas_plan.parent_names),
        ),
        (
            "four-squares",
            "four_square",
            four_square_closure.FOUR_SQUARE_FRONTIER_ROOT,
            four_square_closure.FOUR_SQUARE_FRONTIER_CAMPAIGN_COUNT,
            four_batches,
            parent_names,
            four_square_closure.FOUR_SQUARE_FRONTIER_PARENT_COUNT,
        ),
    ):
        names = tuple(name for _label, batch in batches for name in batch)
        if len(names) != len(set(names)):
            raise ValueError(f"{slug} repeats a checked experimental campaign row")
        if len(names) > total:
            raise ValueError(f"{slug} overstates its sealed experimental campaign")
        result[slug] = {
            "campaign": campaign,
            "root": root,
            "status": EXPERIMENTAL_CLOSURE_STATUS,
            "source_alpha_edition_version": "v13",
            "source_alpha_edition_identity_sha256": v13.ALPHA_V13_IDENTITY_SHA256,
            "verified_campaign_names": list(names),
            "verified_campaign_row_count": len(names),
            "campaign_row_count": total,
            "verified_parent_names": list(checked_parents),
            "verified_parent_row_count": len(checked_parents),
            "parent_row_count": parent_total,
            "parent_progress_recorded": bool(checked_parents),
            "verified_obligation_row_count": len(names) + len(checked_parents),
            "obligation_row_count": total + parent_total,
            "verified_microbatches": [
                {"label": label, "names": list(batch), "row_count": len(batch)}
                for label, batch in batches
            ],
            "immutable_limits": dict(policies),
            "flagship_experimentally_verified": root in names,
            "has_persisted_certificates": False,
            "replayed_during_generation": False,
            "changes_alpha_evidence": False,
            "grants_checked_use": False,
            "grants_stable_membership": False,
        }
    return result


def _experimental_closure_by_name(
    campaigns: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, str]]:
    """Index only validated named historical experiments, never observations."""

    result: dict[str, dict[str, str]] = {}
    for progress in campaigns.values():
        for batch in progress["verified_microbatches"]:
            for name in batch["names"]:
                if name in result:
                    raise ValueError(f"experimental theorem {name!r} occurs in two campaigns")
                result[name] = {
                    "campaign": str(progress["campaign"]),
                    "role": "campaign",
                    "microbatch": str(batch["label"]),
                }
        for name in progress["verified_parent_names"]:
            previous = result.get(name)
            if previous is not None and previous["campaign"] != progress["campaign"]:
                raise ValueError(f"experimental parent {name!r} crosses campaigns")
            result[name] = {
                "campaign": str(progress["campaign"]),
                "role": "parent",
                "microbatch": "four-square-checked-parent",
            }
    return result


def _family_nodes(
    family: Family,
    *,
    experimental_by_name: Mapping[str, Mapping[str, str]] | None = None,
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    selected: dict[str, dict[str, Any]] = {}
    alpha_entries = v15.ALPHA_EDITION.by_name
    alpha_campaigns = _alpha_frontier_campaigns()
    alpha_admission_versions = _alpha_admission_versions()
    experiments = (
        _experimental_closure_by_name(_experimental_closure_campaigns())
        if experimental_by_name is None
        else experimental_by_name
    )
    factory_name_filters = {
        module: frozenset(names)
        for module, names in family.factory_name_filters
    }
    for module_index, (module_name, factory_name) in enumerate(_factory_sources(family)):
        module = importlib.import_module(f"peano_lab.library.{module_name}")
        factory = getattr(module, factory_name, None)
        if not callable(factory):
            raise ValueError(f"missing constructive candidate factory {module_name}.{factory_name}")
        for module_order, item in enumerate(factory(TheoremSpec)):
            accepted_names = factory_name_filters.get(module_name)
            if accepted_names is not None and item.name not in accepted_names:
                continue
            source = {
                "source_module": f"peano_lab.library.{module_name}",
                "factory": factory_name,
                "statement_sha256": _digest(item.statement),
                "script_sha256": _digest("\n".join(item.script)),
                "selected": item.name not in selected,
            }
            if item.name in selected:
                source["matches_selected_statement"] = (
                    source["statement_sha256"] == selected[item.name]["statement_sha256"]
                )
                selected[item.name]["sources"].append(source)
                continue
            alpha_entry = alpha_entries.get(item.name)
            alpha_campaign = alpha_campaigns.get(item.name)
            experimental_closure = experiments.get(item.name)
            if alpha_entry is not None:
                if (
                    alpha_entry.spec.statement != item.statement
                    or tuple(alpha_entry.spec.dependencies) != tuple(item.dependencies)
                    or tuple(alpha_entry.spec.script) != tuple(item.script)
                ):
                    raise ValueError(
                        f"candidate {item.name!r} differs from its sealed Alpha-v15 entry"
                    )
                if (
                    alpha_entry.evidence is not v15.EvidenceStatus.BODY_CHECKED
                    or alpha_entry.checked_use
                    or alpha_campaign is None
                    or item.name not in alpha_admission_versions
                ):
                    raise ValueError(
                        f"candidate {item.name!r} has unexpected Alpha-v15 evidence"
                    )
            if experimental_closure is not None and (
                alpha_entry is None
                or alpha_admission_versions.get(item.name) != "v13"
                or experimental_closure["role"] != "campaign"
            ):
                raise ValueError(
                    f"candidate {item.name!r} has unsealed experimental closure metadata"
                )
            row = {
                "name": item.name,
                "summary": item.summary,
                "statement": item.statement,
                "statement_sha256": _digest(item.statement),
                "dependencies": list(item.dependencies),
                "script": list(item.script),
                "source_module": f"peano_lab.library.{module_name}",
                "factory": factory_name,
                "sources": [source],
                "module_index": module_index,
                "module_order": module_order,
                "status": (
                    ALPHA_BODY_STATUS
                    if alpha_entry is not None
                    else UNENROLLED_CANDIDATE_STATUS
                ),
                "enrolled_in_alpha": alpha_entry is not None,
                "alpha_evidence": (
                    alpha_entry.evidence.value if alpha_entry is not None else None
                ),
                "alpha_checked_use": (
                    alpha_entry.checked_use if alpha_entry is not None else False
                ),
                "alpha_edition_version": (
                    ALPHA_EDITION_VERSION if alpha_entry is not None else None
                ),
                "alpha_admission_version": (
                    alpha_admission_versions[item.name]
                    if alpha_entry is not None
                    else None
                ),
                "alpha_edition_identity_sha256": (
                    v15.ALPHA_V15_IDENTITY_SHA256 if alpha_entry is not None else None
                ),
                "alpha_campaign": (
                    alpha_campaign.value if alpha_campaign is not None else None
                ),
                "admitted_to_alpha": False,
                "admitted_to_stable": False,
                "experimental_closure_verified": experimental_closure is not None,
                "experimental_closure_campaign": (
                    experimental_closure["campaign"]
                    if experimental_closure is not None
                    else None
                ),
                "experimental_closure_microbatch": (
                    experimental_closure["microbatch"]
                    if experimental_closure is not None
                    else None
                ),
                "experimental_closure_status": (
                    EXPERIMENTAL_CLOSURE_STATUS
                    if experimental_closure is not None
                    else None
                ),
                "experimental_closure_has_persisted_certificate": False,
                "root": item.name in family.roots,
            }
            selected[item.name] = row
            rows.append(row)
    if not rows:
        raise ValueError(f"constructive family {family.slug} has no candidate bodies")
    return tuple(rows)


def build_corpora() -> dict[str, dict[str, Any]]:
    experimental_campaigns = _experimental_closure_campaigns()
    experimental_by_name = _experimental_closure_by_name(experimental_campaigns)
    definitions = _definition_table()
    definitions_by_id = {
        definition["id"]: definition for definition in definitions.values()
    }
    if len(definitions_by_id) != len(definitions):
        raise ValueError("constructive frontier definitions repeat a stable identifier")
    candidates: dict[str, tuple[dict[str, Any], ...]] = {}
    for family in FAMILIES:
        rows = _family_nodes(family, experimental_by_name=experimental_by_name)
        for row in rows:
            row["defined"] = _defined_node(row, definitions_by_id)
        candidates[family.slug] = rows
    family_of = {
        node["name"]: slug for slug, nodes in candidates.items() for node in nodes
    }
    public = _specs_by_name()
    alpha_entries = v15.ALPHA_EDITION.by_name
    alpha_admission_versions = _alpha_admission_versions()
    corpora: dict[str, dict[str, Any]] = {}
    for family in FAMILIES:
        nodes = candidates[family.slug]
        local = {node["name"] for node in nodes}
        edges: list[dict[str, Any]] = []
        external: dict[str, dict[str, Any]] = {}
        for node in nodes:
            for dependency in node["dependencies"]:
                alpha_entry = alpha_entries.get(dependency)
                experiment = experimental_by_name.get(dependency)
                enrolled_alpha = alpha_entry is not None
                alpha_evidence = (
                    alpha_entry.evidence.value if alpha_entry is not None else None
                )
                checked_use = (
                    alpha_entry.checked_use if alpha_entry is not None else False
                )
                if dependency in local:
                    kind = "internal-candidate"
                    origin = family.slug
                    evidence = "dependency-curried-candidate-body"
                    admitted_alpha = False
                    admitted_stable = False
                elif dependency in family_of:
                    kind = "cross-family-candidate"
                    origin = family_of[dependency]
                    evidence = "dependency-curried-candidate-body"
                    admitted_alpha = False
                    admitted_stable = False
                elif alpha_entry is not None:
                    evidence = alpha_entry.evidence.value
                    if alpha_entry.evidence is v15.EvidenceStatus.STABLE_CLOSED:
                        kind = "stable-admitted-theorem"
                        origin = "sealed-stable-edition"
                        admitted_alpha = True
                        admitted_stable = True
                    elif alpha_entry.evidence is v15.EvidenceStatus.ALPHA_CLOSED:
                        kind = "alpha-admitted-theorem"
                        origin = "sealed-alpha-edition"
                        admitted_alpha = True
                        admitted_stable = False
                    elif alpha_entry.evidence is v15.EvidenceStatus.BODY_CHECKED:
                        kind = "alpha-enrolled-candidate-not-admitted"
                        origin = "sealed-alpha-body-only"
                        admitted_alpha = False
                        admitted_stable = False
                    else:
                        kind = "alpha-pending-candidate-not-admitted"
                        origin = "sealed-alpha-pending-layered"
                        admitted_alpha = False
                        admitted_stable = False
                elif dependency in public:
                    kind = "public-registry-release-unverified"
                    origin = "public-registry-without-sealed-release-attestation"
                    evidence = "release-status-unattested"
                    admitted_alpha = False
                    admitted_stable = False
                else:
                    kind = "external-unenrolled-candidate"
                    origin = "external-candidate-library"
                    evidence = "release-status-unattested"
                    admitted_alpha = False
                    admitted_stable = False
                edges.append(
                    {
                        "source": dependency,
                        "target": node["name"],
                        "kind": kind,
                        "evidence": evidence,
                        "enrolled_in_alpha": enrolled_alpha,
                        "alpha_evidence": alpha_evidence,
                        "alpha_checked_use": checked_use,
                        "alpha_edition_version": (
                            ALPHA_EDITION_VERSION if enrolled_alpha else None
                        ),
                        "alpha_admission_version": alpha_admission_versions.get(
                            dependency
                        ),
                        "admitted_to_alpha": admitted_alpha,
                        "admitted_to_stable": admitted_stable,
                        "experimental_closure_verified": experiment is not None,
                        "experimental_closure_campaign": (
                            experiment["campaign"] if experiment is not None else None
                        ),
                        "experimental_closure_role": (
                            experiment["role"] if experiment is not None else None
                        ),
                    }
                )
                if kind != "internal-candidate":
                    external[dependency] = {
                        "name": dependency,
                        "kind": kind,
                        "origin": origin,
                        "evidence": evidence,
                        "enrolled_in_alpha": enrolled_alpha,
                        "alpha_evidence": alpha_evidence,
                        "alpha_checked_use": checked_use,
                        "alpha_edition_version": (
                            ALPHA_EDITION_VERSION if enrolled_alpha else None
                        ),
                        "alpha_admission_version": alpha_admission_versions.get(
                            dependency
                        ),
                        "admitted_to_alpha": admitted_alpha,
                        "admitted_to_stable": admitted_stable,
                        "experimental_closure_verified": experiment is not None,
                        "experimental_closure_campaign": (
                            experiment["campaign"] if experiment is not None else None
                        ),
                        "experimental_closure_role": (
                            experiment["role"] if experiment is not None else None
                        ),
                    }
        family_definitions = []
        for name in family.definition_names:
            if name not in definitions:
                raise ValueError(f"family {family.slug} requests an unknown definition {name}")
            family_definitions.append(definitions[name])
        included_ids = {definition["id"] for definition in family_definitions}
        used_definition_ids = {
            definition_id
            for node in nodes
            for definition_id in node["defined"]["definition_uses"]
        }
        for definition_id in sorted(used_definition_ids.difference(included_ids)):
            family_definitions.append(definitions_by_id[definition_id])
        experimental_visible = [
            node for node in nodes if node["experimental_closure_verified"]
        ]
        relevant_experiments = []
        for campaign_slug, progress in experimental_campaigns.items():
            visible_names = [
                node["name"]
                for node in experimental_visible
                if node["experimental_closure_campaign"] == progress["campaign"]
            ]
            if not visible_names and campaign_slug != family.slug:
                continue
            relevant_experiments.append(
                {
                    **progress,
                    "visible_node_names": visible_names,
                    "visible_node_count": len(visible_names),
                }
            )
        corpora[family.slug] = {
            "schema": "peano-lab-constructive-frontier-family-v1",
            "slug": family.slug,
            "title": family.title,
            "formula": family.formula,
            "description": family.description,
            "scope": family.scope,
            "candidate_status": CANDIDATE_STATUS,
            "alpha_edition_version": ALPHA_EDITION_VERSION,
            "alpha_edition_identity_sha256": v15.ALPHA_V15_IDENTITY_SHA256,
            "alpha_enrolled_node_count": sum(
                node["enrolled_in_alpha"] for node in nodes
            ),
            "alpha_checked_use_node_count": sum(
                node["alpha_checked_use"] for node in nodes
            ),
            "experimental_closure_status": EXPERIMENTAL_CLOSURE_STATUS,
            "experimental_closed_visible_node_count": len(experimental_visible),
            "experimental_closure_campaigns": relevant_experiments,
            "experimental_closure_has_persisted_certificates": False,
            "experimental_closure_replayed_during_generation": False,
            "experimental_closure_grants_checked_use": False,
            "experimental_closure_grants_stable_membership": False,
            "alpha_enrolled_root_names": [
                node["name"]
                for node in nodes
                if node["root"] and node["enrolled_in_alpha"]
            ],
            "admitted_to_alpha": False,
            "admitted_to_stable": False,
            "root_names": [name for name in family.roots if name in local],
            "definition_count": len(family_definitions),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "internal_edge_count": sum(edge["kind"] == "internal-candidate" for edge in edges),
            "external_dependency_count": len(external),
            "formal_line_count": sum(len(node["script"]) for node in nodes),
            "defined_statement_count": sum(
                node["defined"]["statement_status"] == "exact-ast-equivalent"
                for node in nodes
            ),
            "compacted_statement_count": sum(
                node["defined"]["defined_statement"] != node["statement"]
                for node in nodes
            ),
            "defined_tactic_proposition_count": sum(
                len(node["defined"]["defined_script_lines"]) for node in nodes
            ),
            "definitions": family_definitions,
            "external_dependencies": sorted(external.values(), key=lambda item: item["name"]),
            "nodes": list(nodes),
            "edges": edges,
            "example": family.example,
        }
    displayed_alpha_names = {
        node["name"]
        for corpus in corpora.values()
        for node in corpus["nodes"]
        if node["enrolled_in_alpha"]
    }
    expected_alpha_names = (
        set(v13.FRONTIER_V13_EXPECTED_NAMES)
        | set(v14.FRONTIER_V14_EXPECTED_NAMES)
        | set(v15.FRONTIER_V15_EXPECTED_NAMES)
    )
    if displayed_alpha_names != expected_alpha_names:
        raise ValueError(
            "constructive explorers do not cover the exact Alpha-v13/v14/v15 appends"
        )
    return corpora


def _svg(corpus: Mapping[str, Any]) -> str:
    nodes = corpus["nodes"]
    columns = max(int(node["module_index"]) for node in nodes) + 1
    rows = max(int(node["module_order"]) for node in nodes) + 1
    width = max(720, 325 * columns + 85)
    height = max(330, 58 * rows + 115)
    locations = {
        str(node["name"]): (
            45 + 325 * int(node["module_index"]),
            76 + 58 * int(node["module_order"]),
        )
        for node in nodes
    }
    internal_edges = []
    for edge in corpus["edges"]:
        if edge["kind"] != "internal-candidate":
            continue
        sx, sy = locations[str(edge["source"])]
        tx, ty = locations[str(edge["target"])]
        x1, y1, x2, y2 = sx + 274, sy + 20, tx, ty + 20
        bend = max(35, abs(x2 - x1) // 2)
        internal_edges.append(
            f'<path class="frontier-edge" d="M {x1} {y1} '
            f'C {x1 + bend} {y1}, {x2 - bend} {y2}, {x2} {y2}" '
            f'data-source="{html.escape(str(edge["source"]), quote=True)}" '
            f'data-target="{html.escape(str(edge["target"]), quote=True)}"/>'
        )
    headings = []
    modules: dict[int, str] = {}
    for node in nodes:
        modules.setdefault(int(node["module_index"]), str(node["source_module"]).split(".")[-1])
    for index, name in sorted(modules.items()):
        short = name.removesuffix("_candidate").replace("fermat_two_squares_", "two squares · ")
        headings.append(
            f'<text class="frontier-column-label" x="{45 + 325 * index}" y="43">'
            f'{html.escape(short)}</text>'
        )
    drawn = []
    for node in nodes:
        name = str(node["name"])
        x, y = locations[name]
        local = {row["name"] for row in nodes}
        external_count = sum(dependency not in local for dependency in node["dependencies"])
        label = name if len(name) <= 35 else name[:32] + "…"
        classes = ["frontier-node"]
        if node["root"]:
            classes.append("frontier-root")
        if node["experimental_closure_verified"]:
            classes.append("frontier-experiment-verified")
        experimental_note = (
            " · replay experiment ✓" if node["experimental_closure_verified"] else ""
        )
        drawn.append(
            f'<g class="{" ".join(classes)}" data-node="{html.escape(name, quote=True)}" '
            f'tabindex="0" role="button" aria-label="{html.escape(name, quote=True)}" '
            f'transform="translate({x},{y})">'
            '<rect width="274" height="41" rx="10"/>'
            f'<text x="12" y="18">{html.escape(label)}</text>'
            f'<text class="frontier-node-meta" x="12" y="33">'
            f'{len(node["script"])} proof lines · {external_count} external'
            f'{experimental_note}</text></g>'
        )
    return (
        f'<svg class="frontier-svg" id="frontier-graph" role="img" '
        f'aria-label="Interactive candidate proof dependency graph" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
        + "".join(internal_edges)
        + "".join(headings)
        + "".join(drawn)
        + "</svg>"
    )


def _example_markup(family: Family) -> str:
    if family.example == "supplementary":
        controls = '<label>Prime or integer <input data-input="n" type="number" min="2" max="499" value="41"></label>'
    elif family.example == "two-squares":
        controls = '<label>Nonnegative integer <input data-input="n" type="number" min="0" max="499" value="65"></label>'
    elif family.example == "kummer":
        controls = (
            '<label>Prime p <input data-input="p" type="number" min="2" max="29" value="5"></label>'
            '<label>a <input data-input="a" type="number" min="0" max="120" value="8"></label>'
            '<label>b <input data-input="b" type="number" min="0" max="120" value="7"></label>'
        )
    elif family.example == "lucas":
        controls = (
            '<label>Prime p <input data-input="p" type="number" min="2" max="29" value="5"></label>'
            '<label>n <input data-input="n" type="number" min="0" max="120" value="37"></label>'
            '<label>k <input data-input="k" type="number" min="0" max="120" value="7"></label>'
        )
    elif family.example == "pythagorean":
        controls = (
            '<label>First parameter m <input data-input="m" type="number" min="2" max="120" value="2"></label>'
            '<label>Second parameter n <input data-input="n" type="number" min="1" max="119" value="1"></label>'
        )
    else:
        controls = '<label>Example integer <input data-input="n" type="number" min="0" max="180" value="37"></label>'
    return (
        f'<section class="frontier-example" data-example="{family.example}">'
        '<h2>Constructive numerical example</h2><p>Finite browser arithmetic illustrates the displayed formulas; it is not a theorem certificate.</p>'
        f'<form data-example-form>{controls}<button type="submit">Compute witness</button></form>'
        '<output data-example-result aria-live="polite"></output></section>'
    )


def _experimental_progress_markup(corpus: Mapping[str, Any]) -> str:
    """Render historical proof experiments apart from sealed release evidence."""

    campaigns = corpus["experimental_closure_campaigns"]
    if not campaigns:
        return ""
    cards = []
    for campaign in campaigns:
        verified = int(campaign["verified_campaign_row_count"])
        total = int(campaign["campaign_row_count"])
        visible = int(campaign["visible_node_count"])
        label = "Lucas" if campaign["campaign"] == "lucas" else "Lagrange four-square"
        parents = (
            f'<p>Older parent rows: <strong>{campaign["verified_parent_row_count"]}'
            f' / {campaign["parent_row_count"]}</strong> independently '
            "replay-verified outside this candidate map. Total sealed-slice "
            f'obligations experimentally verified: <strong>'
            f'{campaign["verified_obligation_row_count"]} / '
            f'{campaign["obligation_row_count"]}</strong>.</p>'
            if campaign["parent_progress_recorded"]
            else ""
        )
        cards.append(
            f'<article class="frontier-experimental-card" '
            f'data-experimental-campaign="{html.escape(campaign["campaign"], quote=True)}">'
            f'<h3>{label} campaign · {verified} / {total}</h3>'
            f'<progress max="{total}" value="{verified}" '
            f'aria-label="{label} independently replay-verified experimental rows">'
            f'{verified}/{total}</progress>'
            f'<p><strong>{visible}</strong> verified campaign '
            f'{"node" if visible == 1 else "nodes"} visible in this proof family; '
            "the campaign denominator includes rows shared with other maps.</p>"
            f"{parents}</article>"
        )
    return (
        '<section class="frontier-experimental" '
        'aria-labelledby="frontier-experimental-heading">'
        '<h2 id="frontier-experimental-heading">Independent closure experiments</h2>'
        '<p class="frontier-experimental-disclaimer">Previously independently '
        "replay-verified empty-context experiments. Certificates are not persisted; "
        "this browser does not replay proofs. Alpha release evidence, checked-use "
        "authority, and Stable membership remain unchanged.</p>"
        + "".join(cards)
        + "</section>"
    )


def _family_landing_html(family: Family, corpus: Mapping[str, Any]) -> bytes:
    """Keep public family entrances identical to the original proof families."""

    target = html.escape(str(corpus["root_names"][-1]), quote=True)
    title = html.escape(family.title)
    description = html.escape(family.description)
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Proof Explorer</title>
  <meta name="description" content="{html.escape(family.description, quote=True)}">
  <link rel="stylesheet" href="../assets/proofs.css">
</head>
<body class="family-page {html.escape(family.slug, quote=True)}-page">
  <header class="family-hero">
    <div class="shell">
      <nav class="crumbs"><a href="../">Proof explorers</a><span>/</span><span>{title}</span></nav>
      <p class="eyebrow">{html.escape(family.kicker)} · Constructive arithmetic</p>
      <h1>{title}</h1>
      <p class="formula">{html.escape(family.formula)}</p>
      <p class="lede">{description}</p>
      <div class="hero-actions">
        <a class="primary-action" href="explorer/defined/graph.html?target={target}&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus">Open the definition-aware map</a>
        <a class="secondary-action" href="explorer/defined/graph.html?target={target}">Read the final theorem</a>
      </div>
    </div>
  </header>
  <main class="shell family-main">
    <section class="view-grid">
      <article class="view-card featured">
        <p class="card-kicker">Recommended</p>
        <h2>Defined mathematical notation</h2>
        <p>Browse {corpus['definition_count']} linked conservative definitions and {corpus['node_count']} theorem bodies without losing their exact first-order expansions.</p>
        <a href="explorer/defined/">Browse definitions and theorems →</a>
      </article>
      <article class="view-card">
        <p class="card-kicker">Focused route</p>
        <h2>Complete dependency graph</h2>
        <p>Follow the selected theorem through its constructive prerequisites, linked definitions, and original proof scripts.</p>
        <a href="explorer/defined/graph.html?target={target}&amp;view=prerequisites&amp;definitions=selected&amp;edges=focus">Trace prerequisites →</a>
      </article>
      <article class="view-card">
        <p class="card-kicker">Exact certificate</p>
        <h2>Fully expanded arithmetic</h2>
        <p>Inspect {corpus['formal_line_count']} original tactic lines and {corpus['edge_count']} dependency edges with every definition fully expanded.</p>
        <a href="explorer/">Open the exact edition →</a>
      </article>
    </section>
    <section class="release-note"><strong>Candidate artifact:</strong> {corpus['node_count']} theorem bodies · {corpus['definition_count']} linked definitions · {corpus['edge_count']} proof edges · {corpus['formal_line_count']} tactic lines. {html.escape(CANDIDATE_STATUS)}.</section>
  </main>
</body>
</html>
"""
    return page.encode("utf-8")


def _defined_library_html(family: Family, corpus: Mapping[str, Any]) -> bytes:
    """Mirror the original definition-aware searchable theorem-library UI."""

    target = html.escape(str(corpus["root_names"][-1]), quote=True)
    definition_cards = "".join(
        f'<article class="pd-result pd-result-definition" data-entry '
        f'data-kind="definition" data-search="{html.escape(" ".join((definition["id"], definition["name"], definition["summary"])).lower(), quote=True)}">'
        f'<a href="graph.html#frontier-definition-{html.escape(definition["id"], quote=True)}">'
        f'<code>{html.escape(definition["id"])}</code> · '
        f'<strong>{html.escape(definition["name"])}</strong></a>'
        f'<p>{html.escape(definition["summary"])}</p>'
        '<small>conservative definition · not a theorem</small></article>'
        for definition in corpus["definitions"]
    )
    theorem_cards = "".join(
        f'<article class="pd-result" data-entry data-kind="theorem" '
        f'data-search="{html.escape(" ".join((node["name"], node["summary"], node["defined"]["defined_statement"][:240])).lower(), quote=True)}">'
        f'<a href="graph.html?target={html.escape(node["name"], quote=True)}">'
        f'<strong>{html.escape(node["name"])}</strong></a>'
        f'<p>{html.escape(node["summary"])}</p>'
        f'<small>theorem body · {len(node["defined"]["definition_uses"])} '
        f'linked definitions · {"Alpha body_checked" if node["enrolled_in_alpha"] else "unenrolled candidate"} · no checked-use authority</small></article>'
        for node in corpus["nodes"]
    )
    count = int(corpus["definition_count"]) + int(corpus["node_count"])
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(family.title)} with defined notation</title>
  <link rel="stylesheet" href="../../../assets/frontier.css">
</head>
<body class="pa-defined-proof-site" data-page="index" data-family="{family.slug}">
  <header class="pd-header pd-hero">
    <nav><a href="../../">{html.escape(family.title)}</a><a href="../">Exact explicit edition</a><a href="graph.html?target={target}">Mixed dependency graph</a></nav>
    <p class="pd-kicker">Parallel reading edition</p>
    <h1>{html.escape(family.title)} with defined notation</h1>
    <p>Readable conservative notation is linked to exact expansions while the complete explicit tactic corpus remains visible.</p>
    <div class="pd-stats"><b>{corpus['node_count']}</b> theorem bodies · <b>{corpus['definition_count']}</b> definitions</div>
  </header>
  <main data-defined-dashboard>
    <section class="pd-controls"><label>Search <input data-search type="search"></label><label>Kind <select data-kind><option value="all">Theorems and definitions</option><option value="theorem">Theorems</option><option value="definition">Definitions</option></select></label><button data-clear type="button">Clear</button><output data-count>{count} entries</output></section>
    <p class="pd-callout">{html.escape(CANDIDATE_STATUS)}.</p>
    <section class="pd-results">{definition_cards}{theorem_cards}</section>
  </main>
  <script src="../../../assets/frontier.js" defer></script>
</body>
</html>
"""
    return page.encode("utf-8")


def _family_html(
    family: Family,
    corpus: Mapping[str, Any],
    *,
    notation: str = "defined",
) -> bytes:
    if notation not in {"defined", "exact"}:
        raise ValueError("frontier proof graph notation must be defined or exact")
    safe_json = json.dumps(corpus, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    assets = "../../../assets" if notation == "defined" else "../../assets"
    family_home = "../../" if notation == "defined" else "../"
    defined_home = "index.html" if notation == "defined" else "defined/"
    alternate = "../" if notation == "defined" else "defined/graph.html"
    alternate_title = "Exact explicit edition" if notation == "defined" else "Defined notation map"
    exact_selected = notation == "exact"
    definition_cards = "".join(
        f'<details class="frontier-definition" '
        f'id="frontier-definition-{html.escape(definition["id"], quote=True)}" '
        f'data-definition-id="{html.escape(definition["id"], quote=True)}">'
        f'<summary><code>{html.escape(definition["name"])}'
        f'({html.escape(", ".join(definition["parameters"]))})</code></summary>'
        f'<p>{html.escape(definition["summary"])}</p>'
        f'<pre>{html.escape(definition["expanded_template"])}</pre>'
        f'<small>{html.escape(definition["id"])} · exact expansion SHA-256 '
        f'{html.escape(definition["template_sha256"])}</small></details>'
        for definition in corpus["definitions"]
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(family.title)} — {'Exact proof explorer' if exact_selected else 'Theorems and definitions'}</title>
  <meta name="description" content="{html.escape(family.description, quote=True)}">
  <link rel="stylesheet" href="{assets}/frontier.css">
</head>
<body class="pa-defined-proof-site" data-page="graph" data-family="{family.slug}" data-frontier-notation="{notation}">
  <header class="pd-header">
    <nav><a href="{family_home}">{html.escape(family.title)}</a><a href="{defined_home}">Defined edition</a><a href="{alternate}">{alternate_title}</a></nav>
    <p class="pd-kicker">{'Exact first-order proof graph' if exact_selected else 'Typed theorem and definition graph'}</p>
    <h1>{html.escape(family.title)}</h1>
    <p>{html.escape(family.description)}</p>
    <div class="pd-stats"><b>{corpus['node_count']}</b> theorem bodies · <b>{corpus['definition_count']}</b> definitions · <b>{corpus['edge_count']}</b> proof edges</div>
  </header>
  <main class="frontier-main">
    <section class="frontier-graph-section"><div class="frontier-toolbar"><h2>Interactive proof map</h2><label>Search theorems <input id="frontier-search" type="search" placeholder="Name, summary, exact or defined statement"></label><div class="frontier-view-controls" role="group" aria-label="Statement notation"><button data-frontier-view="defined" type="button" aria-pressed="{'false' if exact_selected else 'true'}">Readable definitions</button><button data-frontier-view="exact" type="button" aria-pressed="{'true' if exact_selected else 'false'}">Exact HA</button></div><span>Gold nodes are endpoints; teal outlines mark replay-verified experiments, not release evidence.</span></div><div class="frontier-map-controls" role="group" aria-label="Proof graph controls"><button id="frontier-zoom-out" type="button" aria-label="Zoom out">−</button><output id="frontier-zoom-level">100%</output><button id="frontier-zoom-in" type="button" aria-label="Zoom in">+</button><button id="frontier-zoom-fit" type="button">Fit map</button><button id="frontier-focus" type="button" aria-pressed="false">Focus dependencies</button><button id="frontier-print" type="button">Print proof map</button></div><div class="frontier-graph-scroll">{_svg(corpus)}</div></section>
    <section class="frontier-detail" id="frontier-detail" aria-live="polite"><h2>Choose a theorem</h2><p>Select a graph node to inspect its readable defined notation, exact first-order statement, linked definitions, declaration, dependencies, proof script, and source receipts.</p></section>
    {_example_markup(family)}
    <section class="frontier-definitions"><h2>Conservative definitions</h2><p>Each notation below expands immediately into the unchanged first-order language; it introduces no trusted kernel predicate.</p>{definition_cards}</section>
    <section class="frontier-boundary"><h2>Evidence and release boundary</h2><p><strong>{html.escape(CANDIDATE_STATUS)}</strong></p><p>{html.escape(family.scope)}</p><p>Alpha v15 enrolls exactly {corpus['alpha_enrolled_node_count']} of these {corpus['node_count']} displayed bodies as body_checked. Each original Alpha-v13, v14, or v15 enrollment version remains recorded separately. Enrollment records an exact dependency-curried proof body; it does not grant checked theorem use, empty-context closure, or Stable membership. Separately displayed historical replay experiments have no persisted certificate and do not change release evidence, checked-use authority, or Stable admission. This browser surface does not replay a proof, authorize theorem use, alter an edition, or assert completion beyond the exact listed endpoints.</p></section>
{f'<details class="frontier-evidence-record"><summary>Historical experimental replay records</summary>{_experimental_progress_markup(corpus)}</details>' if corpus['experimental_closure_campaigns'] else ''}
  </main>
  <script id="frontier-corpus" type="application/json">{safe_json}</script>
  <script src="{assets}/frontier.js" defer></script>
</body>
</html>
"""
    return page.encode("utf-8")


FRONTIER_CSS = r""":root{color-scheme:light dark;--ink:#162137;--muted:#617089;--paper:#f5f7fc;--surface:#ffffff;--line:#dce2ef;--violet:#6249ca;--teal:#087f78;--gold:#d18a12;--status:#845400;--status-bg:#fff3d5}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.frontier-hero{padding:2.8rem max(calc((100vw - 1250px)/2),5vw) 3rem;color:#fff;background:radial-gradient(circle at 85% 20%,#35337f,transparent 38%),linear-gradient(135deg,#101a31,#202345)}.frontier-back{color:#cbd9f0;text-decoration:none}.frontier-kicker{margin:2rem 0 .4rem;color:#91e6d8;font-size:.75rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase}.frontier-hero h1{margin:.1rem 0 .55rem;font:600 clamp(2rem,5vw,4.2rem)/1.05 Georgia,serif;letter-spacing:-.04em}.frontier-formula{font:600 clamp(1rem,2vw,1.4rem)/1.4 ui-monospace,SFMono-Regular,monospace;color:#a1ebde}.frontier-description,.frontier-scope{max-width:920px;color:#ccd6e8}.frontier-status{display:inline-block;max-width:920px;margin:.45rem 0;padding:.7rem 1rem;border:1px solid #f3d187;border-radius:12px;background:var(--status-bg);color:var(--status);font-size:.87rem;font-weight:750}.frontier-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.75rem;max-width:900px;margin:1.7rem 0 0}.frontier-stats div{padding:.7rem .9rem;border:1px solid #ffffff25;border-radius:12px;background:#ffffff0a}.frontier-stats dt{font-size:1.18rem;font-weight:800}.frontier-stats dd{margin:0;color:#cad3e5;font-size:.74rem}.frontier-main{width:min(1350px,calc(100% - 2rem));margin:1.5rem auto 4rem}.frontier-graph-section,.frontier-detail,.frontier-example,.frontier-definitions,.frontier-boundary{margin-bottom:1.25rem;padding:1.2rem;border:1px solid var(--line);border-radius:16px;background:var(--surface);box-shadow:0 8px 30px #1720330b}.frontier-toolbar{display:flex;align-items:center;flex-wrap:wrap;gap:1rem}.frontier-toolbar h2,.frontier-detail h2,.frontier-example h2,.frontier-definitions h2,.frontier-boundary h2{margin:.15rem 0;font:600 1.35rem Georgia,serif}.frontier-toolbar label,.frontier-example label{display:grid;gap:.2rem;color:var(--muted);font-size:.75rem}.frontier-toolbar span{color:var(--muted);font-size:.76rem}.frontier-toolbar input,.frontier-example input{min-height:36px;padding:.4rem .6rem;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)}.frontier-graph-scroll{overflow:auto;max-height:840px;margin-top:.8rem;border:1px solid var(--line);border-radius:12px;background:linear-gradient(90deg,#f7f9ff 1px,transparent 1px),linear-gradient(#f7f9ff 1px,transparent 1px);background-size:30px 30px}.frontier-svg{display:block;overflow:visible}.frontier-edge{fill:none;stroke:#b3bfd5;stroke-opacity:.62;stroke-width:1.2}.frontier-column-label{fill:var(--muted);font:600 11px ui-sans-serif,system-ui}.frontier-node{cursor:pointer}.frontier-node rect{fill:#f8faff;stroke:#cbd6e8;stroke-width:1}.frontier-node text{fill:#28354d;font:600 10px ui-monospace,monospace}.frontier-node .frontier-node-meta{fill:#697991;font:400 9px ui-sans-serif,system-ui}.frontier-root rect{fill:#fff4d8;stroke:#d18a12;stroke-width:1.3}.frontier-node.selected rect,.frontier-node:focus rect{stroke:var(--violet);stroke-width:2}.frontier-node.dimmed,.frontier-edge.dimmed{opacity:.12}.frontier-detail pre,.frontier-definition pre{max-height:280px;overflow:auto;padding:.8rem;border:1px solid var(--line);border-radius:8px;background:#f7f9ff;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 ui-monospace,monospace}.frontier-dependency-list{display:flex;flex-wrap:wrap;gap:.45rem}.frontier-chip{padding:.25rem .55rem;border:1px solid var(--line);border-radius:999px;font:11px ui-monospace,monospace}.frontier-chip.internal{color:var(--teal);cursor:pointer}.frontier-chip.external{color:var(--muted)}.frontier-example form{display:flex;flex-wrap:wrap;gap:.8rem;align-items:end}.frontier-example input{width:130px}.frontier-example button{min-height:38px;padding:.5rem .9rem;border:0;border-radius:9px;background:var(--violet);color:#fff;font-weight:700}.frontier-example output{display:block;min-height:35px;margin-top:1rem;color:var(--teal);font:600 14px ui-monospace,monospace;white-space:pre-wrap}.frontier-definition{margin:.65rem 0;padding:.7rem .8rem;border:1px solid var(--line);border-radius:10px}.frontier-definition summary{cursor:pointer}.frontier-definition code,.frontier-detail code{font:12px ui-monospace,monospace;color:var(--violet)}.frontier-definition small,.frontier-detail small{color:var(--muted);overflow-wrap:anywhere}.frontier-boundary strong{color:var(--status)}@media(prefers-color-scheme:dark){:root{--ink:#e5eaf4;--muted:#aab6ca;--paper:#0b1020;--surface:#141b2e;--line:#303c54;--violet:#aa99fb;--teal:#75d4c6;--status:#ffe0a0;--status-bg:#493616}.frontier-graph-scroll{background:#11182a}.frontier-node rect{fill:#202b42;stroke:#394864}.frontier-node text{fill:#e1e8f6}.frontier-root rect{fill:#4b391a;stroke:#e7ba56}.frontier-detail pre,.frontier-definition pre{background:#0e1525}.frontier-example button{color:#17142b}.frontier-status{border-color:#8a6627}}@media(max-width:700px){.frontier-stats{grid-template-columns:repeat(2,minmax(0,1fr))}.frontier-toolbar{align-items:stretch}.frontier-main{width:calc(100% - 1rem)}.frontier-hero{padding-inline:1rem}.frontier-example input{width:98px}}
"""

FRONTIER_CSS += r""".frontier-reading-note{max-width:950px;margin:1rem 0 0;color:#b9e7dc;font-size:.78rem}.frontier-view-controls,.frontier-map-controls{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem}.frontier-view-controls button,.frontier-map-controls button{min-height:34px;padding:.38rem .7rem;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink);cursor:pointer;font-size:.76rem}.frontier-view-controls button[aria-pressed="true"],.frontier-map-controls button[aria-pressed="true"]{border-color:var(--violet);background:#6249ca18;color:var(--violet);font-weight:700}.frontier-map-controls{margin-top:.85rem}.frontier-map-controls output{min-width:42px;text-align:center;color:var(--muted);font-size:.74rem}.frontier-definition-link{padding:0;border:0;background:none;color:var(--violet);font:inherit;text-decoration:underline;text-decoration-style:dotted;cursor:pointer}.frontier-definition-link:hover,.frontier-definition-link:focus{text-decoration-style:solid}.frontier-receipt{display:flex;flex-wrap:wrap;gap:.4rem;margin:.55rem 0;color:var(--teal);font-size:.74rem}.frontier-mode-note{color:var(--muted);font-size:.8rem}.frontier-definition:target{border-color:var(--violet)}@media print{body{background:#fff;color:#111}.frontier-hero{padding:1rem;color:#111;background:#fff}.frontier-back,.frontier-toolbar label,.frontier-view-controls,.frontier-map-controls,.frontier-example{display:none!important}.frontier-main{width:100%;margin:0}.frontier-graph-section,.frontier-detail,.frontier-definitions,.frontier-boundary{break-inside:avoid-page;border-color:#ddd;box-shadow:none}.frontier-graph-scroll{overflow:visible;max-height:none;border:0}.frontier-svg{width:100%!important;height:auto!important}.frontier-detail pre{max-height:none}.frontier-status{color:#111;background:#fff;border-color:#777}.frontier-definition-link{color:#222}}"""

FRONTIER_CSS += r""".frontier-experimental{margin-bottom:1.25rem;padding:1.2rem;border:1px solid #0a887a52;border-radius:16px;background:var(--surface);box-shadow:0 8px 30px #1720330b}.frontier-experimental h2{margin:.15rem 0;font:600 1.35rem Georgia,serif}.frontier-experimental-disclaimer{max-width:960px;color:var(--muted);font-size:.85rem}.frontier-experimental-card{margin-top:.8rem;padding:.85rem 1rem;border:1px solid #0a887a45;border-radius:12px}.frontier-experimental-card h3{margin:0 0 .55rem;color:var(--teal);font-size:.96rem}.frontier-experimental-card progress{width:min(420px,100%);height:11px;accent-color:var(--teal)}.frontier-experimental-card p{margin:.5rem 0 0;color:var(--muted);font-size:.8rem}.frontier-experiment-verified rect{stroke:#087f78!important;stroke-width:1.8!important}.frontier-experimental-note{margin:.75rem 0;padding:.7rem .85rem;border:1px solid #0a887a52;border-radius:10px;color:var(--teal);font-size:.78rem}@media(prefers-color-scheme:dark){.frontier-experiment-verified rect{stroke:#75d4c6!important}}@media print{.frontier-experimental{break-inside:avoid-page;border-color:#777;box-shadow:none}.frontier-experiment-verified rect{stroke:#333!important;stroke-dasharray:4 2}}"""


FRONTIER_JS = r"""(() => {
  "use strict";
  const dashboard = document.querySelector("[data-defined-dashboard]");
  if (dashboard) {
    const input = dashboard.querySelector("[data-search]");
    const kind = dashboard.querySelector("[data-kind]");
    const clear = dashboard.querySelector("[data-clear]");
    const count = dashboard.querySelector("[data-count]");
    const entries = Array.from(dashboard.querySelectorAll("[data-entry]"));
    const refreshLibrary = () => {
      const query = input.value.toLowerCase().trim();
      let visible = 0;
      entries.forEach(entry => {
        const matched = (!query || entry.dataset.search.includes(query))
          && (kind.value === "all" || entry.dataset.kind === kind.value);
        entry.hidden = !matched;
        if (matched) visible += 1;
      });
      count.textContent = `${visible} ${visible === 1 ? "entry" : "entries"}`;
    };
    input.addEventListener("input", refreshLibrary);
    kind.addEventListener("change", refreshLibrary);
    clear.addEventListener("click", () => {
      input.value = "";
      kind.value = "all";
      refreshLibrary();
      input.focus();
    });
  }
  const source = document.getElementById("frontier-corpus");
  if (!source) return;
  const corpus = JSON.parse(source.textContent);
  const nodes = new Map(corpus.nodes.map(node => [node.name, node]));
  const external = new Map(corpus.external_dependencies.map(row => [row.name, row]));
  const definitions = new Map(corpus.definitions.map(row => [row.id, row]));
  const escape = value => String(value).replace(/[&<>"']/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[character]));
  const detail = document.getElementById("frontier-detail");
  const graph = document.getElementById("frontier-graph");
  const graphScroll = document.querySelector(".frontier-graph-scroll");
  const search = document.getElementById("frontier-search");
  const parameters = new URLSearchParams(window.location?.search || "");
  let selectedName = null;
  let displayMode = document.body?.dataset.frontierNotation === "exact"
    || parameters.get("notation") === "exact" ? "exact" : "defined";
  let dependencyFocus = parameters.get("view") === "prerequisites";
  let zoom = 1;

  function linkedParts(parts) {
    return parts.map(part => part.kind === "definition"
      ? `<button class="frontier-definition-link" data-definition="${escape(part.definition)}" type="button" title="Open exact conservative expansion">${escape(part.text)}</button>`
      : escape(part.text)).join("");
  }

  function openDefinition(identifier) {
    const card = document.getElementById(`frontier-definition-${identifier}`);
    if (!card) return;
    card.open = true;
    card.scrollIntoView({behavior:"smooth",block:"center"});
    card.querySelector("summary")?.focus();
  }

  function refreshVisibility() {
    const query = search?.value.toLowerCase().trim() || "";
    const matched = new Set(corpus.nodes.filter(node => !query || `${node.name} ${node.summary} ${node.statement} ${node.defined.defined_statement}`.toLowerCase().includes(query)).map(node => node.name));
    let neighborhood = null;
    if (dependencyFocus && selectedName) {
      neighborhood = new Set([selectedName, ...(nodes.get(selectedName)?.dependencies || [])]);
      corpus.edges.filter(edge => edge.source === selectedName).forEach(edge => neighborhood.add(edge.target));
    }
    const visible = name => matched.has(name) && (!neighborhood || neighborhood.has(name));
    document.querySelectorAll(".frontier-node").forEach(item => item.classList.toggle("dimmed", !visible(item.dataset.node)));
    document.querySelectorAll(".frontier-edge").forEach(item => item.classList.toggle("dimmed", !visible(item.dataset.source) || !visible(item.dataset.target)));
  }

  function setZoom(next) {
    if (!graph) return;
    zoom = Math.max(.18, Math.min(2.5, next));
    const viewBox = graph.viewBox.baseVal;
    graph.style.width = `${Math.round(viewBox.width * zoom)}px`;
    graph.style.height = `${Math.round(viewBox.height * zoom)}px`;
    const label = document.getElementById("frontier-zoom-level");
    if (label) label.textContent = `${Math.round(zoom * 100)}%`;
  }

  function openNode(name, center = false) {
    const node = nodes.get(name);
    if (!node) return;
    selectedName = name;
    document.querySelectorAll(".frontier-node.selected").forEach(item => item.classList.remove("selected"));
    document.querySelectorAll(".frontier-node").forEach(item => {
      if (item.dataset.node !== name) return;
      item.classList.add("selected");
      if (center) item.scrollIntoView({behavior:"smooth",block:"nearest",inline:"center"});
    });
    const dependencies = node.dependencies.map(dependency => {
      if (nodes.has(dependency)) {
        const target = nodes.get(dependency);
        const channel = target.enrolled_in_alpha ? `Alpha ${target.alpha_edition_version} · body checked; first enrolled ${target.alpha_admission_version}` : "candidate · unenrolled";
        const experiment = target.experimental_closure_verified ? " · independent replay experiment; not admitted" : "";
        return `<button class="frontier-chip internal" data-dependency="${escape(dependency)}" type="button">${escape(dependency)} · ${escape(channel)}${escape(experiment)}</button>`;
      }
      const evidence = external.get(dependency);
      const channel = evidence?.admitted_to_stable
        ? "Stable closed"
        : evidence?.admitted_to_alpha
          ? "Alpha closed"
          : evidence?.enrolled_in_alpha
            ? `Alpha ${evidence.alpha_edition_version} · ${evidence.alpha_evidence} · not admitted`
            : "candidate · unenrolled";
      const experiment = evidence?.experimental_closure_verified ? " · independent replay experiment; not admitted" : "";
      return `<button class="frontier-chip external" data-dependency="${escape(dependency)}" type="button" title="${escape(evidence?.evidence || "release-status-unattested")}">${escape(dependency)} · ${escape(channel)}${escape(experiment)}</button>`;
    }).join("");
    const provenance = node.sources.map(source => `<span class="frontier-chip ${source.selected ? "internal" : "external"}">${escape(source.source_module)} · ${source.selected ? "selected canonical source" : source.matches_selected_statement ? "matching alternate source" : "non-selected alternate statement"}</span>`).join("");
    const defined = node.defined;
    const readable = displayMode === "defined";
    const statement = readable ? linkedParts(defined.statement_parts) : escape(node.statement);
    const lineOverrides = new Map(defined.defined_script_lines.map(line => [line.number, line]));
    const proof = node.script.map((line, index) => {
      const number = index + 1;
      const compact = readable ? lineOverrides.get(number) : null;
      return `${String(number).padStart(3, "0")}  ${compact ? linkedParts(compact.command_parts) : escape(line)}`;
    }).join("\n");
    const uses = Object.entries(defined.definition_uses).map(([identifier, count]) => {
      const definition = definitions.get(identifier);
      return `<button class="frontier-chip internal" data-definition="${escape(identifier)}" type="button">${escape(definition?.name || identifier)} · ${count}</button>`;
    }).join("");
    const receipt = defined.statement_receipt;
    const attestation = receipt
      ? `<p class="frontier-receipt">Exact AST equivalence verified · ${receipt.expanded_characters} → ${receipt.defined_characters} characters · defined SHA-256 ${escape(receipt.defined_source_sha256)}</p><p><small>Canonical expanded AST SHA-256 ${escape(receipt.canonical_expansion_sha256)}</small></p>`
      : `<p class="frontier-mode-note">This statement remains exact only: ${escape(defined.statement_status)}. No unverified equivalence is claimed.</p>`;
    const experiment = node.experimental_closure_verified
      ? `<p class="frontier-experimental-note"><strong>Independent replay-verified experiment, not release evidence.</strong> Named microbatch ${escape(node.experimental_closure_microbatch)} previously checked an empty-context proof. No certificate is persisted; Alpha evidence remains body_checked, with no checked-use authority or Stable promotion.</p>`
      : "";
    const heading = readable ? "Readable conservative defined notation" : "Exact expanded first-order HA statement";
    const proofHeading = readable ? "Proof script with verified readable local propositions" : "Exact stored proof script";
    detail.innerHTML = `<h2>${escape(name)}</h2><p>${escape(node.summary)}</p><p class="frontier-status">${escape(node.status)}</p>${experiment}<p><small>${escape(node.source_module)} · exact statement SHA-256 ${escape(node.statement_sha256)}</small></p><h3>${heading}</h3><pre>${statement}</pre>${attestation}<h3>Linked definitions in this proof</h3><div class="frontier-dependency-list">${uses || "No reviewed notation aliases are needed for this formula."}</div><h3>Declared dependencies</h3><div class="frontier-dependency-list">${dependencies || "No declared dependencies."}</div><h3>Source provenance</h3><div class="frontier-dependency-list">${provenance}</div><h3>${proofHeading}</h3><pre>${proof || "No tactic commands."}</pre>`;
    detail.querySelectorAll("[data-dependency]").forEach(item => {
      if (nodes.has(item.dataset.dependency)) item.addEventListener("click", () => openNode(item.dataset.dependency,true));
    });
    detail.querySelectorAll("[data-definition]").forEach(item => item.addEventListener("click", () => openDefinition(item.dataset.definition)));
    refreshVisibility();
  }
  document.querySelectorAll(".frontier-node").forEach(item => {
    item.addEventListener("click", () => openNode(item.dataset.node));
    item.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openNode(item.dataset.node); } });
  });
  search?.addEventListener("input",refreshVisibility);
  document.querySelectorAll("[data-frontier-view]").forEach(button => {
    button.addEventListener("click", () => {
      displayMode = button.dataset.frontierView === "exact" ? "exact" : "defined";
      document.querySelectorAll("[data-frontier-view]").forEach(item => item.setAttribute("aria-pressed",String(item.dataset.frontierView === displayMode)));
      if (selectedName) openNode(selectedName);
    });
  });
  document.getElementById("frontier-zoom-out")?.addEventListener("click",()=>setZoom(zoom/1.2));
  document.getElementById("frontier-zoom-in")?.addEventListener("click",()=>setZoom(zoom*1.2));
  document.getElementById("frontier-zoom-fit")?.addEventListener("click",()=>{
    if (graph && graphScroll) setZoom((graphScroll.clientWidth-24)/graph.viewBox.baseVal.width);
  });
  document.getElementById("frontier-focus")?.addEventListener("click",event=>{
    dependencyFocus=!dependencyFocus;
    event.currentTarget.setAttribute("aria-pressed",String(dependencyFocus));
    refreshVisibility();
  });
  document.getElementById("frontier-print")?.addEventListener("click",()=>window.print());
  const prime = n => Number.isInteger(n) && n > 1 && Array.from({length: Math.max(0, Math.floor(Math.sqrt(n)) - 1)}, (_, i) => i + 2).every(d => n % d !== 0);
  function choose(n, k) { let result = 1n; for (let i = 1; i <= k; i++) result = result * BigInt(n - k + i) / BigInt(i); return result; }
  function valuation(n, p) { let count = 0; const base = BigInt(p); while (n > 0n && n % base === 0n) { n /= base; count++; } return count; }
  function carries(a, b, p) { let count = 0, carry = 0, first = a, second = b; const digits = []; while (first || second || carry) { const x = first % p, y = second % p, next = x + y + carry >= p ? 1 : 0; digits.push(`${x}+${y}+${carry}→${next}`); count += next; first = Math.floor(first / p); second = Math.floor(second / p); carry = next; if (digits.length > 64) break; } return {count, digits}; }
  function lucasDigitProduct(n, k, p) { let upper = n, lower = k, product = 1n; const digits = []; do { const nd = upper % p, kd = lower % p; const coefficient = kd <= nd ? choose(nd, kd) : 0n; product *= coefficient; digits.push(`C(${nd},${kd})=${coefficient}`); upper = Math.floor(upper / p); lower = Math.floor(lower / p); } while (upper || lower); return {product, digits}; }
  function twoSquare(n) { for (let x = 0; x * x <= n; x++) { const y = Math.floor(Math.sqrt(n - x * x)); if (x * x + y * y === n) return [x, y]; } return null; }
  function fourSquare(n) { for (let a = 0; a * a <= n; a++) for (let b = 0; a * a + b * b <= n; b++) for (let c = 0; a * a + b * b + c * c <= n; c++) { const d = Math.floor(Math.sqrt(n - a * a - b * b - c * c)); if (a * a + b * b + c * c + d * d === n) return [a, b, c, d]; } return null; }
  function greatestCommonDivisor(a, b) { let first = Math.abs(a), second = Math.abs(b); while (second) [first, second] = [second, first % second]; return first; }
  function factor(n) { if (n === 0) return {text:"0 (prime valuations undefined)",bad:[]}; let rest = n, text = [], bad = []; for (let p = 2; p * p <= rest; p++) if (rest % p === 0) { let e = 0; while (rest % p === 0) { rest /= p; e++; } text.push(`${p}^${e}`); if (p % 4 === 3 && e % 2) bad.push(`${p}^${e}`); } if (rest > 1) { text.push(`${rest}^1`); if (rest % 4 === 3) bad.push(`${rest}^1`); } return {text:text.join(" · ") || "1",bad}; }
  const example = document.querySelector("[data-example]");
  const form = example?.querySelector("[data-example-form]");
  const output = example?.querySelector("[data-example-result]");
  function calculate(event) {
    event?.preventDefault();
    try {
      const value = key => Number(example.querySelector(`[data-input="${key}"]`).value);
      if (corpus.example === "supplementary") { const p = value("n"); if (!prime(p) || p === 2) throw Error("Choose an odd prime ≤ 499."); const squares = new Set(Array.from({length:p},(_,x)=>(x*x)%p)); output.textContent = `p=${p}, p mod 4=${p%4}, p mod 8=${p%8}\n−1 is ${squares.has(p-1)?"a quadratic residue":"a nonresidue"}; 2 is ${squares.has(2)?"a quadratic residue":"a nonresidue"}.`; }
      else if (corpus.example === "kummer") { const p=value("p"),a=value("a"),b=value("b"); if (!prime(p)) throw Error("Choose a prime base."); const binomial=choose(a+b,a), count=carries(a,b,p), v=valuation(binomial,p); output.textContent=`C(${a+b},${a})=${binomial}; v_${p}=${v}; carry count=${count.count}\n${count.digits.join(" | ") || "no nonzero digits"}`; }
      else if (corpus.example === "lucas") { const p=value("p"),n=value("n"),k=value("k"); if (!prime(p)) throw Error("Choose a prime base."); if (![n,k].every(Number.isSafeInteger) || n < 0 || k < 0 || k > n) throw Error("Choose natural inputs with 0 ≤ k ≤ n."); const binomial=choose(n,k), expansion=lucasDigitProduct(n,k,p), modulus=BigInt(p); output.textContent=`C(${n},${k})=${binomial} ≡ ${binomial % modulus} (mod ${p})\n${expansion.digits.join(" · ")}\nDigit product=${expansion.product} ≡ ${expansion.product % modulus} (mod ${p})\nFinite numerical illustration; consult the proof map for the checked theorem boundary.`; }
      else if (corpus.example === "two-squares") { const n=value("n"); if (!Number.isInteger(n) || n < 0) throw Error("Choose a nonnegative integer."); const witness=twoSquare(n), factors=factor(n); output.textContent=`${n} = ${factors.text}\n${witness ? `${n} = ${witness[0]}² + ${witness[1]}²` : "No natural two-square witness."}${factors.bad.length ? `\nOdd 3-mod-4 factor: ${factors.bad.join(", ")}` : ""}`; }
      else if (corpus.example === "pythagorean") { const m=value("m"),n=value("n"); if (![m,n].every(Number.isSafeInteger) || n < 1 || m <= n) throw Error("Choose natural parameters with 0 < n < m."); const difference=m*m-n*n,doubled=2*m*n,hypotenuse=m*m+n*n,primitive=greatestCommonDivisor(m,n)===1 && (m-n)%2===1; output.textContent=`m=${m}, n=${n}\n(${difference}, ${doubled}, ${hypotenuse})\n${difference}² + ${doubled}² = ${hypotenuse}²\n${primitive ? "Coprime, opposite-parity parameters." : "Parameters do not satisfy the classical primitive criterion."}\nForward constructor only; primitive inverse classification and Fermat strict descent remain open.`; }
      else { const n=value("n"), witness=fourSquare(n); output.textContent=witness ? `${n} = ${witness[0]}² + ${witness[1]}² + ${witness[2]}² + ${witness[3]}²\nConstructive four-square witness; the kernel-checked universal theorem is available in the proof map.` : "No witness found inside the finite example search."; }
    } catch (error) { output.textContent=error.message; }
  }
  form?.addEventListener("submit",calculate);
  if (example && output) calculate();
  if (dependencyFocus) {
    document.getElementById("frontier-focus")?.setAttribute("aria-pressed", "true");
  }
  if (corpus.root_names.length) {
    const requested = parameters.get("target");
    openNode(nodes.has(requested) ? requested : corpus.root_names[corpus.root_names.length-1]);
  }
  const definitionHash = window.location?.hash || "";
  if (definitionHash.startsWith("#frontier-definition-")) {
    openDefinition(definitionHash.slice("#frontier-definition-".length));
  }
})();
"""


def _landing_html(corpora: Mapping[str, Mapping[str, Any]]) -> bytes:
    cards = "".join(
        f'<article class="pd-result"><h2><a href="{family.slug}/">'
        f'{html.escape(family.title)}</a></h2>'
        f'<p>{html.escape(family.description)}</p>'
        f'<small>{corpora[family.slug]["node_count"]} theorem bodies · '
        f'{corpora[family.slug]["definition_count"]} conservative definitions '
        "· no checked-use authority</small></article>"
        for family in FAMILIES
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Constructive Arithmetic Proof Explorers</title>'
        '<link rel="stylesheet" href="assets/frontier.css"></head>'
        '<body class="pa-defined-proof-site" data-page="index">'
        '<header class="pd-header pd-hero"><p class="pd-kicker">Constructive arithmetic</p>'
        '<h1>Proof explorers</h1>'
        '<p>Read theorem bodies, linked conservative definitions, and exact constructive proofs.</p></header>'
        f'<main><p class="pd-callout">{html.escape(CANDIDATE_STATUS)}</p>'
        f'<section class="pd-results">{cards}</section></main></body></html>\n'
    ).encode("utf-8")


def build_files() -> tuple[dict[str, bytes], dict[str, Any]]:
    corpora = build_corpora()
    experimental_campaigns = _experimental_closure_campaigns()
    files: dict[str, bytes] = {
        "index.html": _landing_html(corpora),
        "assets/frontier.css": (
            FRONTIER_CSS + "\n" + DEFINED_EXPLORER_STYLESHEET.read_text(encoding="utf-8")
        ).encode("utf-8"),
        "assets/frontier.js": FRONTIER_JS.encode("utf-8"),
    }
    families = []
    for family in FAMILIES:
        corpus = corpora[family.slug]
        corpus_bytes = _json(corpus)
        files[f"{family.slug}/index.html"] = _family_landing_html(family, corpus)
        files[f"{family.slug}/explorer/defined/index.html"] = (
            _defined_library_html(family, corpus)
        )
        files[f"{family.slug}/explorer/defined/graph.html"] = (
            _family_html(family, corpus, notation="defined")
        )
        files[f"{family.slug}/explorer/index.html"] = (
            _family_html(family, corpus, notation="exact")
        )
        files[f"{family.slug}/api/corpus.json"] = corpus_bytes
        families.append(
            {
                "slug": family.slug,
                "title": family.title,
                "candidate_status": CANDIDATE_STATUS,
                "alpha_edition_version": ALPHA_EDITION_VERSION,
                "alpha_enrolled_node_count": corpus["alpha_enrolled_node_count"],
                "alpha_checked_use_node_count": corpus[
                    "alpha_checked_use_node_count"
                ],
                "experimental_closed_visible_node_count": corpus[
                    "experimental_closed_visible_node_count"
                ],
                "experimental_closure_campaigns": corpus[
                    "experimental_closure_campaigns"
                ],
                "alpha_enrolled_root_names": corpus["alpha_enrolled_root_names"],
                "node_count": corpus["node_count"],
                "edge_count": corpus["edge_count"],
                "definition_count": corpus["definition_count"],
                "formal_line_count": corpus["formal_line_count"],
                "defined_statement_count": corpus["defined_statement_count"],
                "compacted_statement_count": corpus["compacted_statement_count"],
                "defined_tactic_proposition_count": corpus["defined_tactic_proposition_count"],
                "root_names": corpus["root_names"],
                "corpus_sha256": _digest(corpus_bytes),
            }
        )
    inventory = [
        {"path": name, "sha256": _digest(payload), "bytes": len(payload)}
        for name, payload in sorted(files.items())
    ]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "candidate_status": CANDIDATE_STATUS,
        "alpha_edition_version": ALPHA_EDITION_VERSION,
        "alpha_edition_identity_sha256": v15.ALPHA_V15_IDENTITY_SHA256,
        "alpha_enrolled_node_count": sum(
            corpus["alpha_enrolled_node_count"] for corpus in corpora.values()
        ),
        "alpha_checked_use_node_count": sum(
            corpus["alpha_checked_use_node_count"] for corpus in corpora.values()
        ),
        "experimental_closure_status": EXPERIMENTAL_CLOSURE_STATUS,
        "experimental_closed_visible_node_count": sum(
            corpus["experimental_closed_visible_node_count"]
            for corpus in corpora.values()
        ),
        "experimental_closure_campaigns": list(experimental_campaigns.values()),
        "experimental_closure_has_persisted_certificates": False,
        "experimental_closure_replayed_during_generation": False,
        "experimental_closure_grants_checked_use": False,
        "experimental_closure_grants_stable_membership": False,
        "admitted_to_alpha": False,
        "admitted_to_stable": False,
        "family_count": len(FAMILIES),
        "families": families,
        "file_count": len(files) + 1,
        "files": inventory,
        "aggregate_sha256": _digest(_json(inventory)),
    }
    files["manifest.json"] = _json(manifest)
    return files, manifest


def _safe_output(path: Path) -> Path:
    resolved = path.resolve(strict=False)
    if resolved in {REPO.resolve(), REPO.parent.resolve(), PY_ROOT.resolve(), Path("/")}:
        raise ValueError("refusing a broad constructive-frontier output directory")
    return resolved


def _write(files: Mapping[str, bytes], output: Path) -> None:
    output = _safe_output(output)
    for relative, payload in files.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)


def _check(files: Mapping[str, bytes], output: Path) -> bool:
    output = _safe_output(output)
    changed = [
        relative
        for relative, payload in files.items()
        if not (output / relative).is_file() or (output / relative).read_bytes() != payload
    ]
    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    } if output.is_dir() else set()
    changed.extend(sorted(actual.difference(files)))
    if changed:
        print(
            "constructive frontier explorer drift: " + ", ".join(sorted(set(changed))[:15]),
            file=sys.stderr,
        )
        return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true", help="reject generated-output drift")
    args = parser.parse_args(argv)
    try:
        files, manifest = build_files()
        if args.check:
            if not _check(files, args.output):
                return 1
            verb = "verified"
        else:
            _write(files, args.output)
            verb = "wrote"
    except (ImportError, OSError, TypeError, ValueError) as error:
        print(f"constructive frontier explorer: {error}", file=sys.stderr)
        return 2
    print(
        f"{verb} constructive frontier explorer: {manifest['family_count']} families, "
        f"{manifest['file_count']} files, {manifest['aggregate_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
