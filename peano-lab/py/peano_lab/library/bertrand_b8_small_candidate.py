"""Constructive finite Bertrand coverage below the factorized cutoff.

The first row proves, without literalizing 512 or 521, that the production
cutoff ``16 * 32`` lies strictly below the final certified prime carrier.
The second row walks the checked adjacent-prime cover inside first-order PA
and returns a Bertrand witness for every nonzero input below the cutoff.

This module is candidate evidence only.  It grants no registry authority or
edition membership.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b8_covering_candidate import (
    BERTRAND_ADD_SWAP_NESTED,
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
    BERTRAND_COVER_FIVE_SEVEN,
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
    BERTRAND_COVER_ONE_TWO,
    BERTRAND_COVER_SEVEN_THIRTEEN,
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
    BERTRAND_COVER_THREE_FIVE,
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
    BERTRAND_COVER_TWO_THREE,
    BERTRAND_COVERING_INTERVAL,
)
from .bertrand_b8_prime_certificates_candidate import (
    PRIME_EIGHTY_THREE,
    PRIME_FIVE,
    PRIME_FIVE_HUNDRED_TWENTY_ONE,
    PRIME_FORTY_THREE,
    PRIME_ONE_HUNDRED_SIXTY_THREE,
    PRIME_SEVEN,
    PRIME_THIRTEEN,
    PRIME_THREE_HUNDRED_SEVENTEEN,
    PRIME_TWENTY_THREE,
)
from .bertrand_primorial_choose_interval_candidate import (
    _prime_relation_term,
)
from .bertrand_primorial_foundation_candidate import _lt_term
from .bertrand_primorial_membership_candidate import _le_term


BERTRAND_CUTOFF_LT_FINAL_PRIME = "bertrand_cutoff_lt_final_prime"
BERTRAND_SMALL_CLOSED_UPPER = "bertrand_small_closed_upper"

_CUTOFF = "16 * 32"
_FINAL_PRIME = "2 * (11 * 22) + 37"

_CHAIN = (
    ("1", "2", "prime_two", BERTRAND_COVER_ONE_TWO),
    ("2", "3", "prime_three", BERTRAND_COVER_TWO_THREE),
    ("3", "5", PRIME_FIVE, BERTRAND_COVER_THREE_FIVE),
    ("5", "7", PRIME_SEVEN, BERTRAND_COVER_FIVE_SEVEN),
    ("7", "13", PRIME_THIRTEEN, BERTRAND_COVER_SEVEN_THIRTEEN),
    (
        "13",
        "23",
        PRIME_TWENTY_THREE,
        BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
    ),
    (
        "23",
        "43",
        PRIME_FORTY_THREE,
        BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
    ),
    (
        "43",
        "9 * 9 + 2",
        PRIME_EIGHTY_THREE,
        BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
    ),
    (
        "9 * 9 + 2",
        "13 * 12 + 7",
        PRIME_ONE_HUNDRED_SIXTY_THREE,
        BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
    ),
    (
        "13 * 12 + 7",
        "18 * 17 + 11",
        PRIME_THREE_HUNDRED_SEVENTEEN,
        BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
    ),
    (
        "18 * 17 + 11",
        _FINAL_PRIME,
        PRIME_FIVE_HUNDRED_TWENTY_ONE,
        BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
    ),
)


def _cutoff_script() -> tuple[str, ...]:
    common_left = "22 * 16 + (10 * 6 + (9 + 10 * 10))"
    common_right = "22 * 16 + (10 * 6 + (12 * 6 + 37))"
    return (
        "exists 8",
        f"have hsucc : 8 + S ({_CUTOFF}) = 9 + ({_CUTOFF})",
        f"trans S (8 + ({_CUTOFF}))",
        "apply PA4",
        "symm",
        "apply add_succ_left",
        "have h32 : 32 = 22 + 10",
        "norm_num",
        f"have hleft : 9 + ({_CUTOFF}) = {common_left}",
        "rewrite h32",
        "trans 9 + (16 * 22 + 16 * 10)",
        "congr",
        "refl",
        "apply mul_add",
        "trans 16 * 22 + (9 + 16 * 10)",
        f"apply {BERTRAND_ADD_SWAP_NESTED}",
        "trans 22 * 16 + (9 + 16 * 10)",
        "congr",
        "apply mul_comm",
        "refl",
        "have h16 : 16 = 10 + 6",
        "norm_num",
        "have htail16 : 16 * 10 = (10 + 6) * 10",
        "congr",
        "exact h16",
        "refl",
        "rewrite htail16",
        "trans 22 * 16 + (9 + (10 * 10 + 6 * 10))",
        "congr",
        "refl",
        "congr",
        "refl",
        "apply add_mul",
        "trans 22 * 16 + (9 + (10 * 10 + 10 * 6))",
        "congr",
        "refl",
        "congr",
        "refl",
        "congr",
        "refl",
        "apply mul_comm",
        f"trans 22 * 16 + ((9 + 10 * 10) + 10 * 6)",
        "congr",
        "refl",
        "symm",
        "apply add_assoc",
        f"trans {common_left}",
        "congr",
        "refl",
        "apply add_comm",
        "refl",
        "have htwoeleven : 2 * 11 = 22",
        "norm_num",
        "have h22sixteen : 22 = 16 + 6",
        "norm_num",
        "have h22twelve : 22 = 10 + 12",
        "norm_num",
        f"have hright : ({_FINAL_PRIME}) = {common_right}",
        "trans (2 * 11) * 22 + 37",
        "congr",
        "symm",
        "apply mul_assoc",
        "refl",
        "rewrite htwoeleven",
        "trans 22 * (16 + 6) + 37",
        "congr",
        "congr",
        "refl",
        "exact h22sixteen",
        "refl",
        "trans (22 * 16 + 22 * 6) + 37",
        "congr",
        "apply mul_add",
        "refl",
        "trans 22 * 16 + (22 * 6 + 37)",
        "apply add_assoc",
        "have htail22 : 22 * 6 = (10 + 12) * 6",
        "congr",
        "exact h22twelve",
        "refl",
        "rewrite htail22",
        "trans 22 * 16 + ((10 * 6 + 12 * 6) + 37)",
        "congr",
        "refl",
        "congr",
        "apply add_mul",
        "refl",
        f"trans {common_right}",
        "congr",
        "refl",
        "apply add_assoc",
        "refl",
        "have htail : 9 + 10 * 10 = 12 * 6 + 37",
        "norm_num",
        "rewrite htail at hleft",
        f"have hcarrier : 9 + ({_CUTOFF}) = ({_FINAL_PRIME})",
        f"trans {common_right}",
        "exact hleft",
        "symm",
        "exact hright",
        f"trans 9 + ({_CUTOFF})",
        "exact hsucc",
        "exact hcarrier",
    )


def _cover_application(
    left: str,
    right: str,
    prime_name: str,
    cover_name: str,
    lower_name: str,
    strict_name: str,
) -> tuple[str, ...]:
    return (
        f"specialize {BERTRAND_COVERING_INTERVAL} ({left})",
        f"specialize {BERTRAND_COVERING_INTERVAL} ({right})",
        f"specialize {BERTRAND_COVERING_INTERVAL} n",
        f"apply {BERTRAND_COVERING_INTERVAL}",
        f"exact {prime_name}",
        f"exact {lower_name}",
        f"exact {strict_name}",
        f"exact {cover_name}",
    )


def _small_script() -> tuple[str, ...]:
    script: list[str] = [
        "intro n",
        "intro hnonzero",
        "intro hcutoff",
        "have hshape : exists k. n = S k",
        "specialize nonzero_is_succ n",
        "apply nonzero_is_succ",
        "exact hnonzero",
        "cases hshape",
        "have hlower_1 : exists k. k + 1 = n",
        "exists x",
        "rewrite hshape_witness",
        "rewrite PA4",
        "rewrite PA3",
        "refl",
    ]
    lower_name = "hlower_1"
    for index, (left, right, prime_name, cover_name) in enumerate(
        _CHAIN[:-1],
        start=1,
    ):
        split_name = f"hsplit_{index}"
        next_lower = f"hlower_{index + 1}"
        script.extend(
            (
                f"have {split_name} : (exists k. k + ({right}) = n) \/ "
                f"(exists k. k + S n = ({right}))",
                f"specialize le_or_lt ({right})",
                "specialize le_or_lt n",
                "exact le_or_lt",
                f"cases {split_name}",
                f"have {next_lower} : exists k. k + ({right}) = n",
                f"exact {split_name}_left",
            )
        )
        lower_name = next_lower

    final_left, final_right, final_prime, final_cover = _CHAIN[-1]
    script.extend(
        (
            f"have hfinal_strict : exists k. k + S n = ({final_right})",
            "specialize lt_trans n",
            f"specialize lt_trans ({_CUTOFF})",
            f"specialize lt_trans ({final_right})",
            "apply lt_trans",
            "exact hcutoff",
            f"exact {BERTRAND_CUTOFF_LT_FINAL_PRIME}",
            *_cover_application(
                final_left,
                final_right,
                final_prime,
                final_cover,
                lower_name,
                "hfinal_strict",
            ),
        )
    )

    for index in range(len(_CHAIN) - 1, 0, -1):
        left, right, prime_name, cover_name = _CHAIN[index - 1]
        split_name = f"hsplit_{index}"
        branch_lower = "hlower_1" if index == 1 else f"hlower_{index}"
        script.extend(
            _cover_application(
                left,
                right,
                prime_name,
                cover_name,
                branch_lower,
                f"{split_name}_right",
            )
        )
    return tuple(script)


def make_bertrand_b8_small_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the cutoff bridge and constructive finite-cover theorem."""

    variables = ("n",)
    cutoff_bound = _lt_term(
        "n",
        _CUTOFF,
        tag="bb8s_cutoff_bound",
        avoid=variables,
    )
    result_variables = variables + ("p",)
    result_prime = _prime_relation_term(
        "p",
        tag="bb8s_result_prime",
        variables=result_variables,
    )
    result_lower = _lt_term(
        "n",
        "p",
        tag="bb8s_result_lower",
        avoid=result_variables,
    )
    result_upper = _le_term(
        "p",
        "n + n",
        tag="bb8s_result_upper",
        variables=result_variables,
    )
    result = (
        f"exists p. ({result_prime}) /\\ (({result_lower}) /\\ "
        f"({result_upper}))"
    )

    reverse_chain = tuple(
        item
        for _left, _right, prime_name, cover_name in reversed(_CHAIN)
        for item in (prime_name, cover_name)
    )
    return (
        spec(
            BERTRAND_CUTOFF_LT_FINAL_PRIME,
            _lt_term(
                _CUTOFF,
                _FINAL_PRIME,
                tag="bb8s_cutoff_final",
                avoid=(),
            ),
            (
                "add_succ_left",
                "mul_add",
                BERTRAND_ADD_SWAP_NESTED,
                "mul_comm",
                "add_mul",
                "add_assoc",
                "add_comm",
                "mul_assoc",
            ),
            _cutoff_script(),
            "The factorized production cutoff lies below the final prime.",
        ),
        spec(
            BERTRAND_SMALL_CLOSED_UPPER,
            f"forall n. ~(n = 0) -> ({cutoff_bound}) -> ({result})",
            (
                "nonzero_is_succ",
                "le_or_lt",
                "lt_trans",
                BERTRAND_CUTOFF_LT_FINAL_PRIME,
                BERTRAND_COVERING_INTERVAL,
                *reverse_chain,
            ),
            _small_script(),
            "Every nonzero input below 16*32 has a closed Bertrand witness.",
        ),
    )


__all__ = [
    "BERTRAND_CUTOFF_LT_FINAL_PRIME",
    "BERTRAND_SMALL_CLOSED_UPPER",
    "make_bertrand_b8_small_candidate_theorems",
]
