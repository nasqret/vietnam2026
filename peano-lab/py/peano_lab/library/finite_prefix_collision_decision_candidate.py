"""Constructive witnessed-collision decision for beta-coded finite prefixes.

Induction on prefix length splits off the final decoded value.  An earlier
occurrence gives an actual pair of distinct equal-value indices; absence of
that occurrence extends the old injectivity proof.  Composing this decision
with the already checked oversized-domain obstruction turns a negated
injection into a genuine existential collision without double-negation
elimination or any new kernel primitive.

These are isolated, dependency-curried proof candidates, not registered or
release-edition theorems.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation
from .fermat_two_squares_pigeonhole_candidate import _collision, _lt
from .finite_fold_surface import beta_at
from .finite_omission_candidate import bounded_into
from .finite_permutation_theorems import (
    contains_prefix,
    injective_prefix,
    injective_successor_prefix,
)


def make_finite_prefix_collision_decision_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build finite collision decisions and actual rectangular collisions."""

    old_collision = _collision("b", "c", "n", tag="fpcd_old")
    next_collision = _collision("b", "c", "S n", tag="fpcd_next")
    generic_collision = _collision("b", "c", "l", tag="fpcd_generic")
    old_injective = injective_prefix("b", "c", "n", tag="fpcd_old")
    next_injective = injective_successor_prefix(
        "b", "c", "n", tag="fpcd_next"
    )
    generic_injective = injective_prefix("b", "c", "l", tag="fpcd_generic")
    last_entry = beta_at("b", "c", "n", "v", tag="fpcd_last")
    old_contains = contains_prefix("b", "c", "n", "v", tag="fpcd_contains")
    full_bounded = bounded_into("b", "c", "l", "m", tag="fpcd_bounded")
    grid_bounded = bounded_into("b", "c", "l", "p", tag="fpcd_grid")
    floor = floor_sqrt_relation("p", "s", tag="fpcd_floor")

    return (
        spec(
            "finite_prefix_collision_succ",
            f"forall b c n. ({old_collision}) -> ({next_collision})",
            ("le_succ",),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro hcollision",
                "cases hcollision",
                "cases hcollision_witness",
                "cases hcollision_witness_witness",
                "cases hcollision_witness_witness_witness",
                "cases hcollision_witness_witness_witness_right",
                "cases hcollision_witness_witness_witness_right_right",
                "cases hcollision_witness_witness_witness_right_right_right",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "specialize le_succ (S x)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hcollision_witness_witness_witness_left",
                "split",
                "specialize le_succ (S x1)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hcollision_witness_witness_witness_right_left",
                "split",
                "intro hequal",
                "apply hcollision_witness_witness_witness_right_right_left",
                "exact hequal",
                "split",
                "exact hcollision_witness_witness_witness_right_right_right_left",
                "exact hcollision_witness_witness_witness_right_right_right_right",
            ),
            "A witnessed collision in a finite prefix remains a collision "
            "after adjoining one more decoded entry.",
        ),
        spec(
            "finite_prefix_last_occurrence_collision",
            f"forall b c n v. ({last_entry}) -> ({old_contains}) -> "
            f"({next_collision})",
            ("le_succ", "le_refl", "lt_irrefl_expanded"),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro v",
                "intro hlast",
                "intro hcontains",
                "cases hcontains",
                "cases hcontains_witness",
                "exists x",
                "exists n",
                "exists v",
                "split",
                "specialize le_succ (S x)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hcontains_witness_left",
                "split",
                "specialize le_refl (S n)",
                "exact le_refl",
                "split",
                "intro hequal",
                "rewrite hequal at hcontains_witness_left",
                "specialize lt_irrefl_expanded n",
                "apply lt_irrefl_expanded",
                "exact hcontains_witness_left",
                "split",
                "exact hcontains_witness_right",
                "exact hlast",
            ),
            "If the last decoded value already occurs, its earlier index "
            "and final index form an explicit witnessed collision.",
        ),
        spec(
            "finite_prefix_injective_extend_fresh",
            f"forall b c n v. ({old_injective}) -> ({last_entry}) -> "
            f"~({old_contains}) -> ({next_injective})",
            (
                "finite_lt_succ_eq_or_lt",
                "beta_at_unique",
            ),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro v",
                "intro holdinjective",
                "intro hlast",
                "intro hfresh",
                "intro i",
                "intro j",
                "intro y",
                "intro hibound",
                "intro hjbound",
                "intro hleft",
                "intro hright",
                "have hi : i = n \\/ exists gap. gap + S i = n",
                "specialize finite_lt_succ_eq_or_lt n",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hibound",
                "have hj : j = n \\/ exists gap. gap + S j = n",
                "specialize finite_lt_succ_eq_or_lt n",
                "specialize finite_lt_succ_eq_or_lt j",
                "apply finite_lt_succ_eq_or_lt",
                "exact hjbound",
                "cases hi",
                "cases hj",
                "trans n",
                "exact hi_left",
                "symm",
                "exact hj_left",
                "exfalso",
                "apply hfresh",
                "exists j",
                "split",
                "exact hj_right",
                "have hsame : y = v",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique n",
                "specialize beta_at_unique y",
                "specialize beta_at_unique v",
                "apply beta_at_unique",
                "rewrite hi_left at hleft",
                "rewrite hi_left at hleft",
                "exact hleft",
                "exact hlast",
                "rewrite hsame at hright",
                "rewrite hsame at hright",
                "exact hright",
                "cases hj",
                "exfalso",
                "apply hfresh",
                "exists i",
                "split",
                "exact hi_right",
                "have hsame : y = v",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique n",
                "specialize beta_at_unique y",
                "specialize beta_at_unique v",
                "apply beta_at_unique",
                "rewrite hj_left at hright",
                "rewrite hj_left at hright",
                "exact hright",
                "exact hlast",
                "rewrite hsame at hleft",
                "rewrite hsame at hleft",
                "exact hleft",
                "specialize holdinjective i",
                "specialize holdinjective j",
                "specialize holdinjective y",
                "apply holdinjective",
                "exact hi_right",
                "exact hj_right",
                "exact hleft",
                "exact hright",
            ),
            "An injective decoded prefix stays injective when its new final "
            "value has no earlier occurrence.",
        ),
        spec(
            "finite_prefix_collision_or_injective",
            f"forall b c l. (({generic_collision}) \\/ ({generic_injective}))",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "finite_prefix_collision_succ",
                "beta_at_exists",
                "finite_contains_decidable",
                "finite_prefix_last_occurrence_collision",
                "finite_prefix_injective_extend_fresh",
            ),
            (
                "intro b",
                "intro c",
                "induction l",
                "right",
                "intro i",
                "intro j",
                "intro v",
                "intro hibound",
                "intro hjbound",
                "intro hleft",
                "intro hright",
                "exfalso",
                "cases hibound",
                "have hzero : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hibound_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hzero",
                "cases IH",
                "left",
                "specialize finite_prefix_collision_succ b",
                "specialize finite_prefix_collision_succ c",
                "specialize finite_prefix_collision_succ l",
                "apply finite_prefix_collision_succ",
                "exact IH_left",
                f"have hlast : exists v. ({beta_at('b', 'c', 'l', 'v', tag='fpcd_induction_last')})",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hlast",
                "have hcontains : "
                f"(({contains_prefix('b', 'c', 'l', 'x', tag='fpcd_induction_contains')}) \\/ "
                f"~({contains_prefix('b', 'c', 'l', 'x', tag='fpcd_induction_contains')}))",
                "specialize finite_contains_decidable b",
                "specialize finite_contains_decidable c",
                "specialize finite_contains_decidable l",
                "specialize finite_contains_decidable x",
                "exact finite_contains_decidable",
                "cases hcontains",
                "left",
                "specialize finite_prefix_last_occurrence_collision b",
                "specialize finite_prefix_last_occurrence_collision c",
                "specialize finite_prefix_last_occurrence_collision l",
                "specialize finite_prefix_last_occurrence_collision x",
                "apply finite_prefix_last_occurrence_collision",
                "exact hlast_witness",
                "exact hcontains_left",
                "right",
                "specialize finite_prefix_injective_extend_fresh b",
                "specialize finite_prefix_injective_extend_fresh c",
                "specialize finite_prefix_injective_extend_fresh l",
                "specialize finite_prefix_injective_extend_fresh x",
                "apply finite_prefix_injective_extend_fresh",
                "exact IH_right",
                "exact hlast_witness",
                "intro hoccurs",
                "apply hcontains_right",
                "exact hoccurs",
            ),
            "Every finite beta-coded prefix constructively yields either "
            "explicit distinct equal-value indices or a proof of injectivity.",
        ),
        spec(
            "finite_bounded_into_oversized_collision",
            f"forall b c l m. ({full_bounded}) -> "
            f"({_lt('m', 'l', tag='fpcd_overflow')}) -> ({generic_collision})",
            (
                "finite_prefix_collision_or_injective",
                "finite_bounded_into_collision_from_constructive_decision",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro m",
                "intro hbounded",
                "intro hoverflow",
                "specialize finite_bounded_into_collision_from_constructive_decision b",
                "specialize finite_bounded_into_collision_from_constructive_decision c",
                "specialize finite_bounded_into_collision_from_constructive_decision l",
                "specialize finite_bounded_into_collision_from_constructive_decision m",
                "apply finite_bounded_into_collision_from_constructive_decision",
                "exact hbounded",
                "exact hoverflow",
                "specialize finite_prefix_collision_or_injective b",
                "specialize finite_prefix_collision_or_injective c",
                "specialize finite_prefix_collision_or_injective l",
                "exact finite_prefix_collision_or_injective",
            ),
            "An oversized beta-coded map into a bounded finite interval has "
            "an actual existentially witnessed collision.",
        ),
        spec(
            "floor_square_oversized_bounded_grid_collision",
            f"forall b c l p s. l = S s * S s -> ({floor}) -> "
            f"({grid_bounded}) -> ({generic_collision})",
            (
                "floor_square_successor_grid_strictly_exceeds_input",
                "finite_bounded_into_oversized_collision",
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
                "specialize finite_bounded_into_oversized_collision b",
                "specialize finite_bounded_into_oversized_collision c",
                "specialize finite_bounded_into_oversized_collision l",
                "specialize finite_bounded_into_oversized_collision p",
                "apply finite_bounded_into_oversized_collision",
                "exact hbounded",
                "rewrite hlength",
                "specialize floor_square_successor_grid_strictly_exceeds_input p",
                "specialize floor_square_successor_grid_strictly_exceeds_input s",
                "apply floor_square_successor_grid_strictly_exceeds_input",
                "exact hfloor",
            ),
            "Every residue-bounded beta map on the floor-square oversized "
            "grid contains explicit distinct colliding indices.",
        ),
    )


__all__ = ["make_finite_prefix_collision_decision_candidate_theorems"]
