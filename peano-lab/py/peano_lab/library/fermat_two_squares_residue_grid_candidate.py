"""Constructive beta-coded affine residue grids for the two-square route.

A flat grid index is divided by its positive width to recover row and column;
the affine value ``root * row + column`` is divided by the nonzero modulus.
Induction and the already proved beta-prefix extension encode all remainders
as one bounded finite map, which can feed constructive finite collision.

Everything expands into unchanged first-order HA.  These isolated candidates
do not admit a theorem or claim the still-missing collision-to-norm descent.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation
from .fermat_residue_map_candidate import prime
from .fermat_two_squares_pigeonhole_candidate import _collision
from .finite_fold_surface import beta_at
from .finite_omission_candidate import bounded_into


AFFINE_GRID_POINT_REMAINDER_EXISTS = "affine_grid_point_remainder_exists"
BETA_AFFINE_RESIDUE_GRID_EXTEND = "beta_affine_residue_grid_extend"
BETA_AFFINE_RESIDUE_GRID_EXISTS = "beta_affine_residue_grid_exists"
BETA_AFFINE_RESIDUE_GRID_BOUNDED = "beta_affine_residue_grid_bounded"
PRIME_FLOOR_AFFINE_RESIDUE_GRID_EXISTS = "prime_floor_affine_residue_grid_exists"
PRIME_FLOOR_AFFINE_RESIDUE_GRID_COLLISION = "prime_floor_affine_residue_grid_collision"
EQUAL_AFFINE_REMAINDERS_BALANCED = "equal_affine_remainders_balanced"


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists ftrg_gap_{tag}. ftrg_gap_{tag} + S ({left}) = ({right})"


def _point(
    modulus: str,
    width: str,
    root: str,
    index: str,
    *,
    tag: str,
) -> str:
    row = f"ftrg_row_{tag}"
    column = f"ftrg_column_{tag}"
    quotient = f"ftrg_quotient_{tag}"
    remainder = f"ftrg_remainder_{tag}"
    column_bound = _lt(column, width, tag=f"{tag}_column")
    residue_bound = _lt(remainder, modulus, tag=f"{tag}_residue")
    return (
        f"exists {row} {column} {quotient} {remainder}. "
        f"(({index}) = ({width}) * {row} + {column} /\\ "
        f"(({column_bound}) /\\ (({root} * {row} + {column} = "
        f"({modulus}) * {quotient} + {remainder}) /\\ ({residue_bound}))))"
    )


def affine_residue_grid(
    modulus: str,
    width: str,
    root: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand the decoded row/column/quotient/remainder grid relation."""

    index = f"ftrg_index_{tag}"
    row = f"ftrg_row_{tag}"
    column = f"ftrg_column_{tag}"
    quotient = f"ftrg_quotient_{tag}"
    remainder = f"ftrg_remainder_{tag}"
    owned = (index, row, column, quotient, remainder)
    if len(set(owned)) != len(owned) or set(owned) & {
        modulus,
        width,
        root,
        code,
        scale,
        length,
    }:
        raise ValueError("generated affine-residue-grid binder captures an argument")
    index_bound = _lt(index, length, tag=f"{tag}_index")
    column_bound = _lt(column, width, tag=f"{tag}_column")
    residue_bound = _lt(remainder, modulus, tag=f"{tag}_residue")
    entry = beta_at(code, scale, index, remainder, tag=f"ftrg_{tag}_entry")
    return (
        f"forall {index}. ({index_bound}) -> exists {row} {column} "
        f"{quotient} {remainder}. (({index}) = ({width}) * {row} + "
        f"{column} /\\ (({column_bound}) /\\ "
        f"(({root} * {row} + {column} = ({modulus}) * {quotient} + "
        f"{remainder}) /\\ (({residue_bound}) /\\ ({entry})))))"
    )


def make_fermat_two_squares_residue_grid_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build constructive affine-grid coding and its witnessed collision."""

    point = _point("p", "w", "r", "k", tag="point")
    previous_grid = affine_residue_grid(
        "p", "w", "r", "b", "c", "l", tag="extend_previous"
    )
    next_grid = affine_residue_grid(
        "p", "w", "r", "z", "d", "S l", tag="extend_next"
    )
    last_point = _point("p", "w", "r", "l", tag="extend_last")
    existence_grid = affine_residue_grid(
        "p", "w", "r", "b", "c", "l", tag="existence"
    )
    induction_previous = affine_residue_grid(
        "p", "w", "r", "b", "c", "l", tag="induction_previous"
    )
    induction_next = affine_residue_grid(
        "p", "w", "r", "b", "c", "S l", tag="induction_next"
    )
    bounded_grid = affine_residue_grid(
        "p", "w", "r", "b", "c", "l", tag="bounded_source"
    )
    bounded_result = bounded_into("b", "c", "l", "p", tag="ftrg_bounded")
    prime_p = prime("p", tag="ftrg_prime")
    floor = floor_sqrt_relation("p", "s", tag="ftrg_floor")
    square_grid = affine_residue_grid(
        "p", "S s", "r", "b", "c", "l", tag="square_grid"
    )
    collision_grid = affine_residue_grid(
        "p", "S s", "r", "b", "c", "l", tag="collision_grid"
    )
    collision = _collision("b", "c", "l", tag="ftrg_actual")

    extend_last_entry = beta_at("z", "d", "l", "x3", tag="ftrg_extension_last")
    extend_old_source = beta_at("b", "c", "k", "value", tag="ftrg_extension_old")
    extend_old_target = beta_at("z", "d", "k", "value", tag="ftrg_extension_new")
    extension = (
        f"exists z d. (({extend_last_entry}) /\\ forall k value. "
        f"({_lt('k', 'l', tag='extension_old_bound')}) -> "
        f"({extend_old_source}) -> ({extend_old_target}))"
    )

    return (
        spec(
            AFFINE_GRID_POINT_REMAINDER_EXISTS,
            f"forall p w r k. ~(p = 0) -> ~(w = 0) -> ({point})",
            ("division_remainder_exists",),
            (
                "intro p",
                "intro w",
                "intro r",
                "intro k",
                "intro hp",
                "intro hw",
                "have hcoordinates : exists i j. "
                "k = w * i + j /\\ exists gap. gap + S j = w",
                "specialize division_remainder_exists w",
                "specialize division_remainder_exists k",
                "apply division_remainder_exists",
                "exact hw",
                "cases hcoordinates",
                "cases hcoordinates_witness",
                "cases hcoordinates_witness_witness",
                "have hresidue : exists q t. "
                "r * x + x1 = p * q + t /\\ exists gap. gap + S t = p",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists (r * x + x1)",
                "apply division_remainder_exists",
                "exact hp",
                "cases hresidue",
                "cases hresidue_witness",
                "cases hresidue_witness_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact hcoordinates_witness_witness_left",
                "split",
                "exact hcoordinates_witness_witness_right",
                "split",
                "exact hresidue_witness_witness_left",
                "exact hresidue_witness_witness_right",
            ),
            "Every flat grid index has canonical row, column, affine quotient, "
            "and strictly bounded residue witnesses.",
        ),
        spec(
            BETA_AFFINE_RESIDUE_GRID_EXTEND,
            f"forall p w r b c l. ({previous_grid}) -> ({last_point}) -> "
            f"exists z d. ({next_grid})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro p",
                "intro w",
                "intro r",
                "intro b",
                "intro c",
                "intro l",
                "intro hprevious",
                "intro hpoint",
                "cases hpoint",
                "cases hpoint_witness",
                "cases hpoint_witness_witness",
                "cases hpoint_witness_witness_witness",
                "cases hpoint_witness_witness_witness_witness",
                "cases hpoint_witness_witness_witness_witness_right",
                "cases hpoint_witness_witness_witness_witness_right_right",
                f"have hextension : {extension}",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend x3",
                "exact beta_prefix_extend",
                "cases hextension",
                "cases hextension_witness",
                "cases hextension_witness_witness",
                "exists x4",
                "exists x5",
                "intro k",
                "intro hk",
                "have hsplit : k = l \\/ exists gap. gap + S k = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt k",
                "apply finite_lt_succ_eq_or_lt",
                "exact hk",
                "cases hsplit",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "rewrite hsplit_left",
                "exact hpoint_witness_witness_witness_witness_left",
                "split",
                "exact hpoint_witness_witness_witness_witness_right_left",
                "split",
                "exact hpoint_witness_witness_witness_witness_right_right_left",
                "split",
                "exact hpoint_witness_witness_witness_witness_right_right_right",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hextension_witness_witness_left",
                "specialize hprevious k",
                "have hold : exists i j q t. "
                "(k = w * i + j /\\ ((exists gap. gap + S j = w) /\\ "
                "((r * i + j = p * q + t) /\\ "
                f"((exists gap. gap + S t = p) /\\ "
                f"({beta_at('b', 'c', 'k', 't', tag='ftrg_extend_old_entry')})))))",
                "apply hprevious",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_witness",
                "cases hold_witness_witness_witness_witness_right",
                "cases hold_witness_witness_witness_witness_right_right",
                "cases hold_witness_witness_witness_witness_right_right_right",
                "exists x6",
                "exists x7",
                "exists x8",
                "exists x9",
                "split",
                "exact hold_witness_witness_witness_witness_left",
                "split",
                "exact hold_witness_witness_witness_witness_right_left",
                "split",
                "exact hold_witness_witness_witness_witness_right_right_left",
                "split",
                "exact hold_witness_witness_witness_witness_right_right_right_left",
                "specialize hextension_witness_witness_right k",
                "specialize hextension_witness_witness_right x9",
                "apply hextension_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_witness_right_right_right_right",
            ),
            "Append the next canonical affine residue while preserving every "
            "decoded row, column, quotient, and earlier residue.",
        ),
        spec(
            BETA_AFFINE_RESIDUE_GRID_EXISTS,
            f"forall p w r l. ~(p = 0) -> ~(w = 0) -> "
            f"exists b c. ({existence_grid})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                AFFINE_GRID_POINT_REMAINDER_EXISTS,
                BETA_AFFINE_RESIDUE_GRID_EXTEND,
            ),
            (
                "intro p",
                "intro w",
                "intro r",
                "induction l",
                "intro hp",
                "intro hw",
                "exists 0",
                "exists 0",
                "intro k",
                "intro hk",
                "exfalso",
                "cases hk",
                "have hzero : S k = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S k)",
                "apply add_eq_zero_right",
                "exact hk_witness",
                "specialize succ_ne_zero k",
                "apply succ_ne_zero",
                "exact hzero",
                "intro hp",
                "intro hw",
                f"have hprevious : exists b c. ({induction_previous})",
                "apply IH",
                "exact hp",
                "exact hw",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hpoint : {_point('p', 'w', 'r', 'l', tag='induction_point')}",
                "specialize affine_grid_point_remainder_exists p",
                "specialize affine_grid_point_remainder_exists w",
                "specialize affine_grid_point_remainder_exists r",
                "specialize affine_grid_point_remainder_exists l",
                "apply affine_grid_point_remainder_exists",
                "exact hp",
                "exact hw",
                f"have hnext : exists b c. ({induction_next})",
                "specialize beta_affine_residue_grid_extend p",
                "specialize beta_affine_residue_grid_extend w",
                "specialize beta_affine_residue_grid_extend r",
                "specialize beta_affine_residue_grid_extend x",
                "specialize beta_affine_residue_grid_extend x1",
                "specialize beta_affine_residue_grid_extend l",
                "apply beta_affine_residue_grid_extend",
                "exact hprevious_witness_witness",
                "exact hpoint",
                "exact hnext",
            ),
            "Every nonzero modulus and positive grid width admit a full "
            "beta-coded prefix of bounded affine residues.",
        ),
        spec(
            BETA_AFFINE_RESIDUE_GRID_BOUNDED,
            f"forall p w r b c l. ({bounded_grid}) -> ({bounded_result})",
            (),
            (
                "intro p",
                "intro w",
                "intro r",
                "intro b",
                "intro c",
                "intro l",
                "intro hgrid",
                "intro k",
                "intro hk",
                "specialize hgrid k",
                "have hpoint : exists i j q t. "
                "(k = w * i + j /\\ ((exists gap. gap + S j = w) /\\ "
                "((r * i + j = p * q + t) /\\ "
                f"((exists gap. gap + S t = p) /\\ "
                f"({beta_at('b', 'c', 'k', 't', tag='ftrg_bounded_point')})))))",
                "apply hgrid",
                "exact hk",
                "cases hpoint",
                "cases hpoint_witness",
                "cases hpoint_witness_witness",
                "cases hpoint_witness_witness_witness",
                "cases hpoint_witness_witness_witness_witness",
                "cases hpoint_witness_witness_witness_witness_right",
                "cases hpoint_witness_witness_witness_witness_right_right",
                "cases hpoint_witness_witness_witness_witness_right_right_right",
                "exists x3",
                "split",
                "exact hpoint_witness_witness_witness_witness_right_right_right_right",
                "exact hpoint_witness_witness_witness_witness_right_right_right_left",
            ),
            "The encoded affine residue grid is an explicit BoundedInto map "
            "from its full domain into the modulus.",
        ),
        spec(
            PRIME_FLOOR_AFFINE_RESIDUE_GRID_EXISTS,
            f"forall p s r l. l = S s * S s -> ({prime_p}) -> "
            f"exists b c. ({square_grid})",
            ("prime_nonzero", "succ_ne_zero", BETA_AFFINE_RESIDUE_GRID_EXISTS),
            (
                "intro p",
                "intro s",
                "intro r",
                "intro l",
                "intro hlength",
                "intro hprime",
                "specialize beta_affine_residue_grid_exists p",
                "specialize beta_affine_residue_grid_exists (S s)",
                "specialize beta_affine_residue_grid_exists r",
                "specialize beta_affine_residue_grid_exists l",
                "apply beta_affine_residue_grid_exists",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact hpzero",
                "specialize succ_ne_zero s",
                "exact succ_ne_zero",
            ),
            "A prime floor-square grid admits a canonical beta-coded affine "
            "residue map on all successor-square points.",
        ),
        spec(
            PRIME_FLOOR_AFFINE_RESIDUE_GRID_COLLISION,
            f"forall p s r l. l = S s * S s -> ({prime_p}) -> ({floor}) -> "
            f"exists b c. (({collision_grid}) /\\ ({collision}))",
            (
                PRIME_FLOOR_AFFINE_RESIDUE_GRID_EXISTS,
                BETA_AFFINE_RESIDUE_GRID_BOUNDED,
                "floor_square_oversized_bounded_grid_collision",
            ),
            (
                "intro p",
                "intro s",
                "intro r",
                "intro l",
                "intro hlength",
                "intro hprime",
                "intro hfloor",
                f"have hgrid : exists b c. ({square_grid})",
                "specialize prime_floor_affine_residue_grid_exists p",
                "specialize prime_floor_affine_residue_grid_exists s",
                "specialize prime_floor_affine_residue_grid_exists r",
                "specialize prime_floor_affine_residue_grid_exists l",
                "apply prime_floor_affine_residue_grid_exists",
                "exact hlength",
                "exact hprime",
                "cases hgrid",
                "cases hgrid_witness",
                "exists x",
                "exists x1",
                "split",
                "exact hgrid_witness_witness",
                "specialize floor_square_oversized_bounded_grid_collision x",
                "specialize floor_square_oversized_bounded_grid_collision x1",
                "specialize floor_square_oversized_bounded_grid_collision l",
                "specialize floor_square_oversized_bounded_grid_collision p",
                "specialize floor_square_oversized_bounded_grid_collision s",
                "apply floor_square_oversized_bounded_grid_collision",
                "exact hlength",
                "exact hfloor",
                "specialize beta_affine_residue_grid_bounded p",
                "specialize beta_affine_residue_grid_bounded (S s)",
                "specialize beta_affine_residue_grid_bounded r",
                "specialize beta_affine_residue_grid_bounded x",
                "specialize beta_affine_residue_grid_bounded x1",
                "specialize beta_affine_residue_grid_bounded l",
                "apply beta_affine_residue_grid_bounded",
                "exact hgrid_witness_witness",
            ),
            "The actual affine prime-residue grid on all square-root points "
            "has explicit distinct flat indices with the same residue.",
        ),
        spec(
            EQUAL_AFFINE_REMAINDERS_BALANCED,
            "forall p r i j q i2 j2 q2 t. "
            "r * i + j = p * q + t -> r * i2 + j2 = p * q2 + t -> "
            "(r * i + j) + p * q2 = (r * i2 + j2) + p * q",
            ("add_permute_outer",),
            (
                "intro p",
                "intro r",
                "intro i",
                "intro j",
                "intro q",
                "intro i2",
                "intro j2",
                "intro q2",
                "intro t",
                "intro hfirst",
                "intro hsecond",
                "rewrite hfirst",
                "rewrite hsecond",
                "specialize add_permute_outer (p * q)",
                "specialize add_permute_outer t",
                "specialize add_permute_outer (p * q2)",
                "specialize add_permute_outer 0",
                "rewrite PA3 at add_permute_outer",
                "rewrite PA3 at add_permute_outer",
                "exact add_permute_outer",
            ),
            "Equal affine remainders yield an exact subtraction-free balanced "
            "congruence between their two grid values.",
        ),
    )


__all__ = [
    "AFFINE_GRID_POINT_REMAINDER_EXISTS",
    "BETA_AFFINE_RESIDUE_GRID_BOUNDED",
    "BETA_AFFINE_RESIDUE_GRID_EXISTS",
    "BETA_AFFINE_RESIDUE_GRID_EXTEND",
    "EQUAL_AFFINE_REMAINDERS_BALANCED",
    "PRIME_FLOOR_AFFINE_RESIDUE_GRID_COLLISION",
    "PRIME_FLOOR_AFFINE_RESIDUE_GRID_EXISTS",
    "affine_residue_grid",
    "make_fermat_two_squares_residue_grid_candidate_theorems",
]
