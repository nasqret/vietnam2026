"""Checked arithmetic and interval support for the finite Bertrand cover.

The first three rows isolate the only generic reasoning used by the final
finite chain.  The remaining rows certify every consecutive covering
inequality from the base interval at one through the prime 521.  The large
carriers stay in their compact additive-multiplicative representations, so
no tactic normalizes a forbidden large unary numeral.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_primorial_choose_interval_candidate import (
    _prime_relation_term,
)
from .bertrand_primorial_foundation_candidate import _lt_term
from .bertrand_primorial_membership_candidate import _le_term


BERTRAND_ADD_SWAP_NESTED = "bertrand_add_swap_nested"
BERTRAND_ADD_SIX_PERMUTE = "bertrand_add_six_permute"
BERTRAND_COVERING_INTERVAL = "bertrand_covering_interval"
BERTRAND_COVER_ONE_TWO = "bertrand_cover_one_two"
BERTRAND_COVER_TWO_THREE = "bertrand_cover_two_three"
BERTRAND_COVER_THREE_FIVE = "bertrand_cover_three_five"
BERTRAND_COVER_FIVE_SEVEN = "bertrand_cover_five_seven"
BERTRAND_COVER_SEVEN_THIRTEEN = "bertrand_cover_seven_thirteen"
BERTRAND_COVER_THIRTEEN_TWENTY_THREE = (
    "bertrand_cover_thirteen_twenty_three"
)
BERTRAND_COVER_TWENTY_THREE_FORTY_THREE = (
    "bertrand_cover_twenty_three_forty_three"
)
BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE = (
    "bertrand_cover_forty_three_eighty_three"
)
BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE = (
    "bertrand_cover_eighty_three_one_hundred_sixty_three"
)
BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN = (
    "bertrand_cover_one_hundred_sixty_three_three_hundred_seventeen"
)
BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE = (
    "bertrand_cover_three_hundred_seventeen_five_hundred_twenty_one"
)


_SMALL_COVERS = (
    (BERTRAND_COVER_ONE_TWO, "1", "2", 0, "bb8c_one_two"),
    (BERTRAND_COVER_TWO_THREE, "2", "3", 1, "bb8c_two_three"),
    (BERTRAND_COVER_THREE_FIVE, "3", "5", 1, "bb8c_three_five"),
    (BERTRAND_COVER_FIVE_SEVEN, "5", "7", 3, "bb8c_five_seven"),
    (
        BERTRAND_COVER_SEVEN_THIRTEEN,
        "7",
        "13",
        1,
        "bb8c_seven_thirteen",
    ),
    (
        BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
        "13",
        "23",
        3,
        "bb8c_thirteen_twenty_three",
    ),
    (
        BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
        "23",
        "43",
        3,
        "bb8c_twenty_three_forty_three",
    ),
    (
        BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
        "43",
        "9 * 9 + 2",
        3,
        "bb8c_forty_three_eighty_three",
    ),
)


def _cover_statement(left: str, right: str, *, tag: str) -> str:
    return _le_term(
        right,
        f"({left}) + ({left})",
        tag=tag,
        variables=(),
    )


def _small_cover_script(gap: int) -> tuple[str, ...]:
    return (f"exists {gap}", "norm_num")


def _cover_eighty_three_to_one_sixty_three_script() -> tuple[str, ...]:
    left = "9 * 9 + 2"
    right = "13 * 12 + 7"
    remainder = "8 * 10"
    return (
        "have h13 : 13 = 9 + 4",
        "norm_num",
        "have h9twelve : 9 * 12 = 9 * 9 + 27",
        "norm_num",
        "have h4twelve : 4 * 12 = 48",
        "norm_num",
        f"have hcarrier : {right} = ({left}) + ({remainder})",
        "rewrite h13",
        "specialize add_mul 9",
        "specialize add_mul 4",
        "specialize add_mul 12",
        "rewrite add_mul",
        "rewrite h9twelve",
        "rewrite h4twelve",
        "trans (9 * 9 + (27 + 48)) + 7",
        "congr",
        "apply add_assoc",
        "refl",
        "trans 9 * 9 + ((27 + 48) + 7)",
        "apply add_assoc",
        "have htail : (27 + 48) + 7 = 2 + (8 * 10)",
        "norm_num",
        "rewrite htail",
        "symm",
        "apply add_assoc",
        "exists 3",
        "rewrite hcarrier",
        f"trans (3 + ({left})) + ({remainder})",
        "symm",
        "apply add_assoc",
        f"trans (({left}) + 3) + ({remainder})",
        "congr",
        "apply add_comm",
        "refl",
        f"trans ({left}) + (3 + ({remainder}))",
        "apply add_assoc",
        f"have hgap : 3 + ({remainder}) = {left}",
        "norm_num",
        "rewrite hgap",
        "refl",
    )


def _cover_one_sixty_three_to_three_seventeen_script() -> tuple[str, ...]:
    left = "13 * 12 + 7"
    right = "18 * 17 + 11"
    remainder = "(13 * 5 + 5 * 12) + (5 * 5 + 4)"
    return (
        "have h18 : 18 = 13 + 5",
        "norm_num",
        "have h17 : 17 = 12 + 5",
        "norm_num",
        "have h11 : 11 = 7 + 4",
        "norm_num",
        f"have hcarrier : {right} = ({left}) + ({remainder})",
        "rewrite h18",
        "rewrite h17",
        "have houter : (13 + 5) * (12 + 5) = "
        "13 * (12 + 5) + 5 * (12 + 5)",
        "apply add_mul",
        "rewrite houter",
        "have hleft_dist : 13 * (12 + 5) = 13 * 12 + 13 * 5",
        "apply mul_add",
        "rewrite hleft_dist",
        "have hright_dist : 5 * (12 + 5) = 5 * 12 + 5 * 5",
        "apply mul_add",
        "rewrite hright_dist",
        "trans ((13 * 12 + 13 * 5) + (5 * 12 + 5 * 5)) + "
        "(7 + 4)",
        "congr",
        "refl",
        "exact h11",
        f"apply {BERTRAND_ADD_SIX_PERMUTE}",
        f"have hgap : 9 + ({remainder}) = {left}",
        "have h13 : 13 = 5 + 8",
        "norm_num",
        "have hAexpand : 13 * 12 + 7 = (5 * 12 + 8 * 12) + 7",
        "trans (5 + 8) * 12 + 7",
        "congr",
        "congr",
        "exact h13",
        "refl",
        "refl",
        "trans (5 * 12 + 8 * 12) + 7",
        "congr",
        "apply add_mul",
        "refl",
        "refl",
        "rewrite hAexpand",
        "trans 9 + (13 * 5 + (5 * 12 + (5 * 5 + 4)))",
        "congr",
        "refl",
        "apply add_assoc",
        "trans 9 + (5 * 12 + (13 * 5 + (5 * 5 + 4)))",
        "congr",
        "refl",
        f"apply {BERTRAND_ADD_SWAP_NESTED}",
        "trans 5 * 12 + (9 + (13 * 5 + (5 * 5 + 4)))",
        f"apply {BERTRAND_ADD_SWAP_NESTED}",
        "have htail : 9 + (13 * 5 + (5 * 5 + 4)) = 8 * 12 + 7",
        "norm_num",
        "rewrite htail",
        "symm",
        "apply add_assoc",
        "exists 9",
        "rewrite hcarrier",
        f"trans (9 + ({left})) + ({remainder})",
        "symm",
        "apply add_assoc",
        f"trans (({left}) + 9) + ({remainder})",
        "congr",
        "apply add_comm",
        "refl",
        f"trans ({left}) + (9 + ({remainder}))",
        "apply add_assoc",
        "rewrite hgap",
        "refl",
    )


def _cover_three_seventeen_to_five_twenty_one_script() -> tuple[str, ...]:
    left = "18 * 17 + 11"
    right = "2 * (11 * 22) + 37"
    x_term = "17 * 17"
    p_term = "17 * 5"
    tail = "2 * 31"
    remainder = "17 * 12"
    return (
        "have h22 : 22 = 17 + 5",
        "norm_num",
        "have htwoeleven : 2 * 11 = 22",
        "norm_num",
        "have hsquare : 22 * 22 = (17 + 5) * (17 + 5)",
        "congr",
        "exact h22",
        "exact h22",
        "have hproduct : (17 + 5) * (17 + 5) = "
        f"({x_term} + {p_term}) + ({p_term} + 5 * 5)",
        "trans 17 * (17 + 5) + 5 * (17 + 5)",
        "apply add_mul",
        f"trans ({x_term} + {p_term}) + (5 * 17 + 5 * 5)",
        "congr",
        "apply mul_add",
        "apply mul_add",
        f"trans ({x_term} + {p_term}) + ({p_term} + 5 * 5)",
        "congr",
        "refl",
        "congr",
        "apply mul_comm",
        "refl",
        "refl",
        f"have hBnorm : {right} = "
        f"{x_term} + ({p_term} + ({p_term} + {tail}))",
        "trans (2 * 11) * 22 + 37",
        "congr",
        "symm",
        "apply mul_assoc",
        "refl",
        "rewrite htwoeleven",
        "rewrite hsquare",
        "rewrite hproduct",
        f"trans ({x_term} + {p_term}) + "
        f"(({p_term} + 5 * 5) + 37)",
        "apply add_assoc",
        f"trans {x_term} + ({p_term} + (({p_term} + 5 * 5) + 37))",
        "apply add_assoc",
        f"trans {x_term} + ({p_term} + ({p_term} + (5 * 5 + 37)))",
        "congr",
        "refl",
        "congr",
        "refl",
        "apply add_assoc",
        f"have htail_b : 5 * 5 + 37 = {tail}",
        "norm_num",
        "rewrite htail_b",
        "refl",
        "have h18 : 18 = 17 + 1",
        "norm_num",
        f"have hAexpand : {left} = ({x_term} + 17) + 11",
        "trans (17 + 1) * 17 + 11",
        "congr",
        "congr",
        "exact h18",
        "refl",
        "refl",
        f"trans ({x_term} + 1 * 17) + 11",
        "congr",
        "apply add_mul",
        "refl",
        "have hone : 1 * 17 = 17",
        "apply one_mul",
        "rewrite hone",
        "refl",
        "have h12 : 12 = 5 + 7",
        "norm_num",
        "have h7 : 7 = 5 + 2",
        "norm_num",
        f"have hRexpand : {remainder} = "
        f"{p_term} + ({p_term} + 17 * 2)",
        "trans 17 * (5 + 7)",
        "congr",
        "refl",
        "exact h12",
        f"trans {p_term} + 17 * 7",
        "apply mul_add",
        f"trans {p_term} + 17 * (5 + 2)",
        "congr",
        "refl",
        "congr",
        "refl",
        "exact h7",
        f"trans {p_term} + ({p_term} + 17 * 2)",
        "congr",
        "refl",
        "apply mul_add",
        "refl",
        f"have hRnorm : ({left}) + ({remainder}) = "
        f"{x_term} + ({p_term} + ({p_term} + {tail}))",
        "rewrite hRexpand",
        "rewrite hAexpand",
        f"trans ((({x_term} + 17) + 11) + {p_term}) + "
        f"({p_term} + 17 * 2)",
        "symm",
        "apply add_assoc",
        f"trans (({x_term} + 17) + (11 + {p_term})) + "
        f"({p_term} + 17 * 2)",
        "congr",
        "apply add_assoc",
        "refl",
        f"trans ({x_term} + {p_term}) + "
        f"((17 + 11) + ({p_term} + 17 * 2))",
        f"apply {BERTRAND_ADD_SIX_PERMUTE}",
        f"trans {x_term} + "
        f"({p_term} + ((17 + 11) + ({p_term} + 17 * 2)))",
        "apply add_assoc",
        f"trans {x_term} + "
        f"({p_term} + ({p_term} + ((17 + 11) + 17 * 2)))",
        "congr",
        "refl",
        "congr",
        "refl",
        f"trans ((17 + 11) + {p_term}) + 17 * 2",
        "symm",
        "apply add_assoc",
        f"trans ({p_term} + (17 + 11)) + 17 * 2",
        "congr",
        "apply add_comm",
        "refl",
        "apply add_assoc",
        f"have htail_r : (17 + 11) + 17 * 2 = {tail}",
        "norm_num",
        "rewrite htail_r",
        "refl",
        f"have hcarrier : {right} = ({left}) + ({remainder})",
        f"trans {x_term} + ({p_term} + ({p_term} + {tail}))",
        "exact hBnorm",
        "symm",
        "exact hRnorm",
        f"have hgap : (6 * 17 + 11) + ({remainder}) = {left}",
        f"trans 6 * 17 + (11 + ({remainder}))",
        "apply add_assoc",
        f"trans 6 * 17 + (({remainder}) + 11)",
        "congr",
        "refl",
        "apply add_comm",
        f"trans (6 * 17 + ({remainder})) + 11",
        "symm",
        "apply add_assoc",
        f"trans (17 * 6 + ({remainder})) + 11",
        "congr",
        "congr",
        "apply mul_comm",
        "refl",
        "refl",
        "trans 17 * (6 + 12) + 11",
        "congr",
        "symm",
        "apply mul_add",
        "refl",
        "have hsum : 6 + 12 = 18",
        "norm_num",
        "rewrite hsum",
        "trans 18 * 17 + 11",
        "congr",
        "apply mul_comm",
        "refl",
        "refl",
        "exists 6 * 17 + 11",
        "rewrite hcarrier",
        f"trans ((6 * 17 + 11) + ({left})) + ({remainder})",
        "symm",
        "apply add_assoc",
        f"trans (({left}) + (6 * 17 + 11)) + ({remainder})",
        "congr",
        "apply add_comm",
        "refl",
        f"trans ({left}) + ((6 * 17 + 11) + ({remainder}))",
        "apply add_assoc",
        "rewrite hgap",
        "refl",
    )


def make_bertrand_b8_covering_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered finite-covering arithmetic tranche."""

    variables = ("a", "b", "n")
    interval_prime = _prime_relation_term(
        "b",
        tag="bb8ci_prime",
        variables=variables,
    )
    interval_lower = _le_term(
        "a",
        "n",
        tag="bb8ci_lower",
        variables=variables,
    )
    interval_strict = _lt_term(
        "n",
        "b",
        tag="bb8ci_strict",
        avoid=variables,
    )
    interval_cover = _le_term(
        "b",
        "a + a",
        tag="bb8ci_cover",
        variables=variables,
    )
    result_variables = variables + ("p",)
    result_prime = _prime_relation_term(
        "p",
        tag="bb8ci_result_prime",
        variables=result_variables,
    )
    result_strict = _lt_term(
        "n",
        "p",
        tag="bb8ci_result_strict",
        avoid=result_variables,
    )
    result_upper = _le_term(
        "p",
        "n + n",
        tag="bb8ci_result_upper",
        variables=result_variables,
    )

    rows: list[Any] = [
        spec(
            BERTRAND_ADD_SWAP_NESTED,
            "forall a b c. a + (b + c) = b + (a + c)",
            ("add_assoc", "add_comm"),
            (
                "intro a",
                "intro b",
                "intro c",
                "trans (a + b) + c",
                "symm",
                "apply add_assoc",
                "trans (b + a) + c",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
            ),
            "Swap the first two addends under a fixed trailing addend.",
        ),
        spec(
            BERTRAND_ADD_SIX_PERMUTE,
            "forall a b c d e f. ((a + b) + (c + d)) + (e + f) = "
            "(a + e) + ((b + c) + (d + f))",
            ("add_assoc", BERTRAND_ADD_SWAP_NESTED),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "trans (a + (b + (c + d))) + (e + f)",
                "congr",
                "apply add_assoc",
                "refl",
                "trans a + ((b + (c + d)) + (e + f))",
                "apply add_assoc",
                "trans a + (b + ((c + d) + (e + f)))",
                "congr",
                "refl",
                "apply add_assoc",
                "trans a + (b + (c + (d + (e + f))))",
                "congr",
                "refl",
                "congr",
                "refl",
                "apply add_assoc",
                "trans a + (b + (c + (e + (d + f))))",
                "congr",
                "refl",
                "congr",
                "refl",
                "congr",
                "refl",
                f"apply {BERTRAND_ADD_SWAP_NESTED}",
                "trans a + (b + (e + (c + (d + f))))",
                "congr",
                "refl",
                "congr",
                "refl",
                f"apply {BERTRAND_ADD_SWAP_NESTED}",
                "trans a + (e + (b + (c + (d + f))))",
                "congr",
                "refl",
                f"apply {BERTRAND_ADD_SWAP_NESTED}",
                "trans (a + e) + (b + (c + (d + f)))",
                "symm",
                "apply add_assoc",
                "trans (a + e) + ((b + c) + (d + f))",
                "congr",
                "refl",
                "symm",
                "apply add_assoc",
                "refl",
            ),
            "Normalize the six addends used by the 163-to-317 cover.",
        ),
        spec(
            BERTRAND_COVERING_INTERVAL,
            "forall a b n. "
            f"({interval_prime}) -> ({interval_lower}) -> "
            f"({interval_strict}) -> ({interval_cover}) -> "
            f"exists p. ({result_prime}) /\\ (({result_strict}) /\\ "
            f"({result_upper}))",
            ("add_le_add_right", "add_le_add_left", "le_trans"),
            (
                "intro a",
                "intro b",
                "intro n",
                "intro hprime",
                "intro hlower",
                "intro hstrict",
                "intro hcover",
                "have hfirst : exists k. k + (a + a) = n + a",
                "specialize add_le_add_right a",
                "specialize add_le_add_right n",
                "specialize add_le_add_right a",
                "apply add_le_add_right",
                "exact hlower",
                "have hsecond : exists k. k + (n + a) = n + n",
                "specialize add_le_add_left a",
                "specialize add_le_add_left n",
                "specialize add_le_add_left n",
                "apply add_le_add_left",
                "exact hlower",
                "have hdouble : exists k. k + (a + a) = n + n",
                "specialize le_trans (a + a)",
                "specialize le_trans (n + a)",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
                "have hupper : exists k. k + b = n + n",
                "specialize le_trans b",
                "specialize le_trans (a + a)",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hcover",
                "exact hdouble",
                "exists b",
                "split",
                "exact hprime",
                "split",
                "exact hstrict",
                "exact hupper",
            ),
            "One checked adjacent cover supplies a Bertrand witness.",
        ),
    ]

    for name, left, right, gap, tag in _SMALL_COVERS:
        rows.append(
            spec(
                name,
                _cover_statement(left, right, tag=tag),
                (),
                _small_cover_script(gap),
                f"The checked finite cover inequality from {left} to {right}.",
            )
        )

    rows.extend(
        (
            spec(
                BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
                _cover_statement(
                    "9 * 9 + 2",
                    "13 * 12 + 7",
                    tag="bb8c_eighty_three_one_sixty_three",
                ),
                ("add_mul", "add_assoc", "add_comm"),
                _cover_eighty_three_to_one_sixty_three_script(),
                "The compact checked cover from 83 to 163.",
            ),
            spec(
                BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
                _cover_statement(
                    "13 * 12 + 7",
                    "18 * 17 + 11",
                    tag="bb8c_one_sixty_three_three_seventeen",
                ),
                (
                    "add_mul",
                    "mul_add",
                    "add_assoc",
                    "add_comm",
                    BERTRAND_ADD_SWAP_NESTED,
                    BERTRAND_ADD_SIX_PERMUTE,
                ),
                _cover_one_sixty_three_to_three_seventeen_script(),
                "The compact checked cover from 163 to 317.",
            ),
            spec(
                BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
                _cover_statement(
                    "18 * 17 + 11",
                    "2 * (11 * 22) + 37",
                    tag="bb8c_three_seventeen_five_twenty_one",
                ),
                (
                    "add_mul",
                    "mul_add",
                    "mul_assoc",
                    "mul_comm",
                    "add_assoc",
                    "add_comm",
                    "one_mul",
                    BERTRAND_ADD_SIX_PERMUTE,
                ),
                _cover_three_seventeen_to_five_twenty_one_script(),
                "The compact checked cover from 317 to 521.",
            ),
        )
    )
    return tuple(rows)


__all__ = [
    "BERTRAND_ADD_SWAP_NESTED",
    "BERTRAND_ADD_SIX_PERMUTE",
    "BERTRAND_COVERING_INTERVAL",
    "BERTRAND_COVER_ONE_TWO",
    "BERTRAND_COVER_TWO_THREE",
    "BERTRAND_COVER_THREE_FIVE",
    "BERTRAND_COVER_FIVE_SEVEN",
    "BERTRAND_COVER_SEVEN_THIRTEEN",
    "BERTRAND_COVER_THIRTEEN_TWENTY_THREE",
    "BERTRAND_COVER_TWENTY_THREE_FORTY_THREE",
    "BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE",
    "BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE",
    "BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN",
    "BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE",
    "make_bertrand_b8_covering_candidate_theorems",
]
