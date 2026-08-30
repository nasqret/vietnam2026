"""Constructive square-root and finite-collision bridges for two squares.

All displayed order, primality, square-root, and beta-prefix relations are
expanded into the unchanged first-order language ``{0,S,+,*,=}``.  These are
isolated dependency-curried candidates, not public or release-edition claims.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import beta_at
from .finite_omission_candidate import bounded_into
from .finite_permutation_theorems import (
    bounded_prefix,
    contains_prefix,
    injective_prefix,
    surjective_prefix,
)


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists ftsp_gap_{tag}. ftsp_gap_{tag} + S ({left}) = {right}"


def _le(left: str, right: str, *, tag: str) -> str:
    return f"exists ftsp_weak_{tag}. ftsp_weak_{tag} + ({left}) = {right}"


def _collision(code: str, scale: str, length: str, *, tag: str) -> str:
    first = f"ftsp_first_{tag}"
    second = f"ftsp_second_{tag}"
    value = f"ftsp_value_{tag}"
    left_entry = beta_at(code, scale, first, value, tag=f"ftsp_{tag}_left")
    right_entry = beta_at(code, scale, second, value, tag=f"ftsp_{tag}_right")
    return (
        f"exists {first} {second} {value}. "
        f"(({_lt(first, length, tag=f'{tag}_first')}) /\\ "
        f"(({_lt(second, length, tag=f'{tag}_second')}) /\\ "
        f"(~({first} = {second}) /\\ (({left_entry}) /\\ ({right_entry})))))"
    )


def make_fermat_two_squares_pigeonhole_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build independently checkable constructive pigeonhole prerequisites."""

    prime_p = prime("p", tag="ftsp_prime")
    floor_p = floor_sqrt_relation("p", "s", tag="ftsp_prime_floor")
    full_bounded = bounded_into("b", "c", "l", "n", tag="ftsp_full_bounded")
    full_injective = injective_prefix("b", "c", "l", tag="ftsp_full_injective")
    grid_bounded = bounded_into("b", "c", "l", "p", tag="ftsp_grid_bounded")
    grid_injective = injective_prefix("b", "c", "l", tag="ftsp_grid_injective")
    square_bounded = bounded_prefix("b", "c", "n", tag="ftsp_square_bounded")
    square_injective = injective_prefix(
        "b", "c", "n", tag="ftsp_square_injective"
    )
    square_surjective = surjective_prefix(
        "b", "c", "n", tag="ftsp_square_surjective"
    )
    last_entry = beta_at("b", "c", "n", "v", tag="ftsp_last_entry")
    earlier_entry = beta_at("b", "c", "i", "v", tag="ftsp_earlier_entry")
    collision_l = _collision("b", "c", "l", tag="general")
    collision_n = _collision("b", "c", "n", tag="decision_previous")
    collision_sn = _collision("b", "c", "S n", tag="decision_successor")
    decision_injective_n = injective_prefix(
        "b", "c", "n", tag="ftsp_decision_previous"
    )
    decision_injective_sn = injective_prefix(
        "b", "c", "sn", tag="ftsp_decision_successor"
    ).replace("sn", "S n")
    decision_last = beta_at("b", "c", "n", "v", tag="ftsp_decision_last")
    decision_contains = contains_prefix(
        "b", "c", "n", "v", tag="ftsp_decision_contains"
    )

    return (
        spec(
            "prime_is_not_natural_square",
            f"forall p s. ({prime_p}) -> ~(p = s * s)",
            (),
            (
                "intro p",
                "intro s",
                "intro hprime",
                "intro hsquare",
                "cases hprime",
                "have hfactor : s = 1 \\/ s = 1",
                "specialize hprime_right s",
                "specialize hprime_right s",
                "apply hprime_right",
                "exact hsquare",
                "cases hfactor",
                "apply hprime_left",
                "rewrite hsquare",
                "rewrite hfactor_left",
                "rewrite hfactor_left",
                "norm_num",
                "apply hprime_left",
                "rewrite hsquare",
                "rewrite hfactor_right",
                "rewrite hfactor_right",
                "norm_num",
            ),
            "No natural square satisfies the nonunit factor-pair definition of primality.",
        ),
        spec(
            "natural_square_monotone_expanded",
            "forall a s. "
            f"({_le('a', 's', tag='square_source')}) -> "
            f"({_le('a * a', 's * s', tag='square_result')})",
            ("mul_le_mul_right", "mul_le_mul_left", "le_trans"),
            (
                "intro a",
                "intro s",
                "intro hle",
                "have hfirst : exists k. k + a * a = s * a",
                "specialize mul_le_mul_right a",
                "specialize mul_le_mul_right s",
                "specialize mul_le_mul_right a",
                "apply mul_le_mul_right",
                "exact hle",
                "have hsecond : exists k. k + s * a = s * s",
                "specialize mul_le_mul_left a",
                "specialize mul_le_mul_left s",
                "specialize mul_le_mul_left s",
                "apply mul_le_mul_left",
                "exact hle",
                "specialize le_trans (a * a)",
                "specialize le_trans (s * a)",
                "specialize le_trans (s * s)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
            ),
            "Witnessed weak order on natural coordinates transports to their squares.",
        ),
        spec(
            "prime_floor_square_strictly_below_prime",
            f"forall p s. ({prime_p}) -> ({floor_p}) -> "
            f"({_lt('s * s', 'p', tag='prime_floor_strict')})",
            ("prime_is_not_natural_square", "le_eq_or_lt"),
            (
                "intro p",
                "intro s",
                "intro hprime",
                "intro hfloor",
                "cases hfloor",
                "have hsplit : s * s = p \\/ exists k. k + S (s * s) = p",
                "specialize le_eq_or_lt (s * s)",
                "specialize le_eq_or_lt p",
                "apply le_eq_or_lt",
                "exact hfloor_left",
                "cases hsplit",
                "exfalso",
                "specialize prime_is_not_natural_square p",
                "specialize prime_is_not_natural_square s",
                "apply prime_is_not_natural_square",
                "exact hprime",
                "symm",
                "exact hsplit_left",
                "exact hsplit_right",
            ),
            "For a prime, its floor-square lower endpoint is strictly smaller than the prime.",
        ),
        spec(
            "prime_floor_bounded_coordinate_square_strict",
            f"forall p s a. ({prime_p}) -> ({floor_p}) -> "
            f"({_le('a', 's', tag='coordinate_bound')}) -> "
            f"({_lt('a * a', 'p', tag='coordinate_square_bound')})",
            (
                "natural_square_monotone_expanded",
                "prime_floor_square_strictly_below_prime",
                "lt_of_le_of_lt",
            ),
            (
                "intro p",
                "intro s",
                "intro a",
                "intro hprime",
                "intro hfloor",
                "intro hbound",
                "have hsquare : exists k. k + a * a = s * s",
                "specialize natural_square_monotone_expanded a",
                "specialize natural_square_monotone_expanded s",
                "apply natural_square_monotone_expanded",
                "exact hbound",
                "have hprimebound : exists k. k + S (s * s) = p",
                "specialize prime_floor_square_strictly_below_prime p",
                "specialize prime_floor_square_strictly_below_prime s",
                "apply prime_floor_square_strictly_below_prime",
                "exact hprime",
                "exact hfloor",
                "specialize lt_of_le_of_lt (a * a)",
                "specialize lt_of_le_of_lt (s * s)",
                "specialize lt_of_le_of_lt p",
                "apply lt_of_le_of_lt",
                "exact hsquare",
                "exact hprimebound",
            ),
            "Every coordinate at most the floor square root of a prime has square below that prime.",
        ),
        spec(
            "two_strict_values_sum_below_double",
            "forall a b p. "
            f"({_lt('a', 'p', tag='sum_first')}) -> "
            f"({_lt('b', 'p', tag='sum_second')}) -> "
            f"({_lt('a + b', 'p + p', tag='sum_result')})",
            ("add_assoc", "add_comm", "add_succ_left"),
            (
                "intro a",
                "intro b",
                "intro p",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hsecond",
                "exists x + x1 + 1",
                "rewrite <- hfirst_witness",
                "rewrite <- hsecond_witness",
                "simp [add_assoc, add_comm, add_succ_left]",
                "congr",
                "congr",
                "congr",
                "refl",
                "trans (x + b) + a",
                "symm",
                "apply add_assoc",
                "trans (b + x) + a",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
            ),
            "Two natural values each strictly below p have sum strictly below 2p.",
        ),
        spec(
            "prime_floor_bounded_two_square_norm_below_double",
            f"forall p s a b. ({prime_p}) -> ({floor_p}) -> "
            f"({_le('a', 's', tag='norm_first_bound')}) -> "
            f"({_le('b', 's', tag='norm_second_bound')}) -> "
            f"({_lt('a * a + b * b', 'p + p', tag='norm_upper')})",
            (
                "prime_floor_bounded_coordinate_square_strict",
                "two_strict_values_sum_below_double",
            ),
            (
                "intro p",
                "intro s",
                "intro a",
                "intro b",
                "intro hprime",
                "intro hfloor",
                "intro hfirst",
                "intro hsecond",
                "have hfirstsquare : exists k. k + S (a * a) = p",
                "specialize prime_floor_bounded_coordinate_square_strict p",
                "specialize prime_floor_bounded_coordinate_square_strict s",
                "specialize prime_floor_bounded_coordinate_square_strict a",
                "apply prime_floor_bounded_coordinate_square_strict",
                "exact hprime",
                "exact hfloor",
                "exact hfirst",
                "have hsecondsquare : exists k. k + S (b * b) = p",
                "specialize prime_floor_bounded_coordinate_square_strict p",
                "specialize prime_floor_bounded_coordinate_square_strict s",
                "specialize prime_floor_bounded_coordinate_square_strict b",
                "apply prime_floor_bounded_coordinate_square_strict",
                "exact hprime",
                "exact hfloor",
                "exact hsecond",
                "specialize two_strict_values_sum_below_double (a * a)",
                "specialize two_strict_values_sum_below_double (b * b)",
                "specialize two_strict_values_sum_below_double p",
                "apply two_strict_values_sum_below_double",
                "exact hfirstsquare",
                "exact hsecondsquare",
            ),
            "Any two coordinates bounded by the prime floor square root have norm strictly below twice the prime.",
        ),
        spec(
            "floor_square_successor_grid_strictly_exceeds_input",
            f"forall p s. ({floor_p}) -> "
            f"({_lt('p', 'S s * S s', tag='grid_overflow')})",
            (),
            (
                "intro p",
                "intro s",
                "intro hfloor",
                "cases hfloor",
                "exact hfloor_right",
            ),
            "The successor-floor-square grid has strictly more points than the input modulus.",
        ),
        spec(
            "floor_square_oversized_grid_exists",
            f"forall p. exists s. (({floor_p}) /\\ "
            f"({_lt('p', 'S s * S s', tag='existing_grid_overflow')}))",
            ("floor_sqrt_total", "floor_square_successor_grid_strictly_exceeds_input"),
            (
                "intro p",
                f"have hfloor : exists s. ({floor_p})",
                "specialize floor_sqrt_total p",
                "exact floor_sqrt_total",
                "cases hfloor",
                "exists x",
                "split",
                "exact hfloor_witness",
                "specialize floor_square_successor_grid_strictly_exceeds_input p",
                "specialize floor_square_successor_grid_strictly_exceeds_input x",
                "apply floor_square_successor_grid_strictly_exceeds_input",
                "exact hfloor_witness",
            ),
            "Every natural admits an explicitly witnessed floor-square grid with more cells than that natural.",
        ),
        spec(
            "prime_floor_bounded_divisible_norm_represents_prime",
            f"forall p s a b. ({prime_p}) -> ({floor_p}) -> "
            f"({_le('a', 's', tag='representation_first')}) -> "
            f"({_le('b', 's', tag='representation_second')}) -> "
            f"({_lt('0', 'a * a + b * b', tag='representation_positive')}) -> "
            "(exists k. a * a + b * b = p * k) -> p = a * a + b * b",
            (
                "prime_floor_bounded_two_square_norm_below_double",
                "bounded_divisible_two_square_norm_equals_prime",
            ),
            (
                "intro p",
                "intro s",
                "intro a",
                "intro b",
                "intro hprime",
                "intro hfloor",
                "intro hfirst",
                "intro hsecond",
                "intro hpositive",
                "intro hdivisible",
                "have hupper : exists k. k + S (a * a + b * b) = p + p",
                "specialize prime_floor_bounded_two_square_norm_below_double p",
                "specialize prime_floor_bounded_two_square_norm_below_double s",
                "specialize prime_floor_bounded_two_square_norm_below_double a",
                "specialize prime_floor_bounded_two_square_norm_below_double b",
                "apply prime_floor_bounded_two_square_norm_below_double",
                "exact hprime",
                "exact hfloor",
                "exact hfirst",
                "exact hsecond",
                "specialize bounded_divisible_two_square_norm_equals_prime p",
                "specialize bounded_divisible_two_square_norm_equals_prime a",
                "specialize bounded_divisible_two_square_norm_equals_prime b",
                "apply bounded_divisible_two_square_norm_equals_prime",
                "exact hpositive",
                "exact hdivisible",
                "exact hupper",
            ),
            "A positive divisible norm with floor-square-bounded coordinates is already an exact prime representation.",
        ),
        spec(
            "finite_bounded_into_oversized_not_injective",
            f"forall b c l n. ({full_bounded}) -> "
            f"({_lt('n', 'l', tag='domain_overflow')}) -> ~({full_injective})",
            (
                "lt_to_le",
                "lt_of_lt_of_le",
                "finite_bounded_injective_surjective",
                "lt_irrefl_expanded",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hbounded",
                "intro hoverflow",
                "intro hinjective",
                "have hweak : exists k. k + n = l",
                "specialize lt_to_le n",
                "specialize lt_to_le l",
                "apply lt_to_le",
                "exact hoverflow",
                f"have hsquarebounded : {square_bounded}",
                "intro i",
                "intro hi",
                "have hlarge : exists k. k + S i = l",
                "specialize lt_of_lt_of_le i",
                "specialize lt_of_lt_of_le n",
                "specialize lt_of_lt_of_le l",
                "apply lt_of_lt_of_le",
                "exact hi",
                "exact hweak",
                "specialize hbounded i",
                "apply hbounded",
                "exact hlarge",
                f"have hsquareinjective : {square_injective}",
                "intro i",
                "intro j",
                "intro v",
                "intro hi",
                "intro hj",
                "intro hleft",
                "intro hright",
                "specialize hinjective i",
                "specialize hinjective j",
                "specialize hinjective v",
                "apply hinjective",
                "specialize lt_of_lt_of_le i",
                "specialize lt_of_lt_of_le n",
                "specialize lt_of_lt_of_le l",
                "apply lt_of_lt_of_le",
                "exact hi",
                "exact hweak",
                "specialize lt_of_lt_of_le j",
                "specialize lt_of_lt_of_le n",
                "specialize lt_of_lt_of_le l",
                "apply lt_of_lt_of_le",
                "exact hj",
                "exact hweak",
                "exact hleft",
                "exact hright",
                f"have hsurjective : {square_surjective}",
                "specialize finite_bounded_injective_surjective n",
                "specialize finite_bounded_injective_surjective b",
                "specialize finite_bounded_injective_surjective c",
                "apply finite_bounded_injective_surjective",
                "exact hsquarebounded",
                "exact hsquareinjective",
                f"have hlast : exists v. (({last_entry}) /\\ "
                f"({_lt('v', 'n', tag='last_value')}))",
                "specialize hbounded n",
                "apply hbounded",
                "exact hoverflow",
                "cases hlast",
                "cases hlast_witness",
                f"have hearlier : exists i. "
                f"(({_lt('i', 'n', tag='earlier_index')}) /\\ "
                f"({earlier_entry.replace('v', 'x')}))",
                "specialize hsurjective x",
                "apply hsurjective",
                "exact hlast_witness_right",
                "cases hearlier",
                "cases hearlier_witness",
                "have hequal : x1 = n",
                "specialize hinjective x1",
                "specialize hinjective n",
                "specialize hinjective x",
                "apply hinjective",
                "specialize lt_of_lt_of_le x1",
                "specialize lt_of_lt_of_le n",
                "specialize lt_of_lt_of_le l",
                "apply lt_of_lt_of_le",
                "exact hearlier_witness_left",
                "exact hweak",
                "exact hoverflow",
                "exact hearlier_witness_right",
                "exact hlast_witness_left",
                "rewrite hequal at hearlier_witness_left",
                "specialize lt_irrefl_expanded n",
                "apply lt_irrefl_expanded",
                "exact hearlier_witness_left",
            ),
            "An explicitly bounded beta-coded map from a larger finite domain cannot be injective.",
        ),
        spec(
            "floor_square_oversized_bounded_grid_not_injective",
            f"forall b c l p s. l = S s * S s -> ({floor_p}) -> "
            f"({grid_bounded}) -> ~({grid_injective})",
            (
                "floor_square_successor_grid_strictly_exceeds_input",
                "finite_bounded_into_oversized_not_injective",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro p",
                "intro s",
                "intro hlength",
                "intro hfloor",
                "intro hbounded",
                "intro hinjective",
                "have hoverflow : exists k. k + S p = l",
                "rewrite hlength",
                "specialize floor_square_successor_grid_strictly_exceeds_input p",
                "specialize floor_square_successor_grid_strictly_exceeds_input s",
                "apply floor_square_successor_grid_strictly_exceeds_input",
                "exact hfloor",
                "specialize finite_bounded_into_oversized_not_injective b",
                "specialize finite_bounded_into_oversized_not_injective c",
                "specialize finite_bounded_into_oversized_not_injective l",
                "specialize finite_bounded_into_oversized_not_injective p",
                "apply finite_bounded_into_oversized_not_injective",
                "exact hbounded",
                "exact hoverflow",
                "exact hinjective",
            ),
            "Every beta-coded prime-residue-bounded map on the oversized floor-square grid has a collision obstruction.",
        ),
        spec(
            "finite_bounded_into_collision_from_constructive_decision",
            f"forall b c l n. ({full_bounded}) -> "
            f"({_lt('n', 'l', tag='collision_overflow')}) -> "
            f"(({collision_l}) \\/ ({full_injective})) -> ({collision_l})",
            ("finite_bounded_into_oversized_not_injective",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hbounded",
                "intro hoverflow",
                "intro hdecision",
                "cases hdecision",
                "exact hdecision_left",
                "exfalso",
                "specialize finite_bounded_into_oversized_not_injective b",
                "specialize finite_bounded_into_oversized_not_injective c",
                "specialize finite_bounded_into_oversized_not_injective l",
                "specialize finite_bounded_into_oversized_not_injective n",
                "apply finite_bounded_into_oversized_not_injective",
                "exact hbounded",
                "exact hoverflow",
                "exact hdecision_right",
            ),
            "Once collision-versus-injectivity is constructively decided, oversized bounded maps yield an actual collision witness.",
        ),
    )


__all__ = ["make_fermat_two_squares_pigeonhole_candidate_theorems"]
