"""Exact constructive QRes classifications for the moduli 3, 5, and 7.

This module is deliberately isolated from the public theorem registry.  It is
an untrusted authoring layer whose contracts expand quadratic residuosity,
bounded roots, and balanced congruence into ordinary first-order PA formulas.
Every generated script is replayed and checked independently by the focused
admission tests.

For a canonical value ``a < m``, the checked classifications are exactly::

    m = 3:  a is a square iff a is 0 or 1
    m = 5:  a is a square iff a is 0, 1, or 4
    m = 7:  a is a square iff a is 0, 1, 2, or 4

The individual positive and negative facts make both directions directly
usable without unpacking the classification conjunction.
"""

from __future__ import annotations

from typing import Any, Callable


_RESIDUES: dict[int, tuple[int, ...]] = {
    3: (0, 1),
    5: (0, 1, 4),
    7: (0, 1, 2, 4),
}

_ROOT_RESIDUES: dict[int, tuple[int, ...]] = {
    3: (0, 1, 1),
    5: (0, 1, 4, 4, 1),
    7: (0, 1, 4, 2, 2, 4, 1),
}

_NUMBER_WORD = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
}


def _qres(modulus: str, value: str, *, tag: str) -> str:
    """Fully expand ``QRes(modulus,value)`` for trusted internal terms."""

    return (
        f"exists sm_x_{tag}. exists sm_u_{tag} sm_v_{tag}. "
        f"sm_x_{tag} * sm_x_{tag} + {modulus} * sm_u_{tag} = "
        f"{value} + {modulus} * sm_v_{tag}"
    )


def _bounded_qres(modulus: str, value: str, *, tag: str) -> str:
    """Fully expand a canonical root and its square congruence."""

    return (
        f"exists sm_x_{tag}. "
        f"(exists sm_h_{tag}. sm_h_{tag} + S sm_x_{tag} = {modulus}) /\\ "
        f"exists sm_u_{tag} sm_v_{tag}. "
        f"sm_x_{tag} * sm_x_{tag} + {modulus} * sm_u_{tag} = "
        f"{value} + {modulus} * sm_v_{tag}"
    )


def _equalities(variable: str, values: tuple[int, ...]) -> str:
    # Disjunction is intentionally left associative in Peano Lab.
    return " \\/ ".join(f"{variable} = {value}" for value in values)


def _lt_three_spec(spec: Callable[..., Any]) -> Any:
    return spec(
        "lt_three_cases",
        "forall x. (exists h. h + S x = 3) -> "
        f"{_equalities('x', (0, 1, 2))}",
        ("le_of_succ_le_succ", "le_eq_or_lt", "le_zero"),
        (
            "intro x",
            "intro hb",
            "have hle2 : exists h. h + x = 2",
            "specialize le_of_succ_le_succ x",
            "specialize le_of_succ_le_succ 2",
            "apply le_of_succ_le_succ",
            "exact hb",
            "have hc2 : x = 2 \\/ exists h. h + S x = 2",
            "specialize le_eq_or_lt x",
            "specialize le_eq_or_lt 2",
            "apply le_eq_or_lt",
            "exact hle2",
            "cases hc2",
            "right",
            "exact hc2_left",
            "left",
            "have hle1 : exists h. h + x = 1",
            "specialize le_of_succ_le_succ x",
            "specialize le_of_succ_le_succ 1",
            "apply le_of_succ_le_succ",
            "exact hc2_right",
            "have hc1 : x = 1 \\/ exists h. h + S x = 1",
            "specialize le_eq_or_lt x",
            "specialize le_eq_or_lt 1",
            "apply le_eq_or_lt",
            "exact hle1",
            "cases hc1",
            "right",
            "exact hc1_left",
            "left",
            "have hle0 : exists h. h + x = 0",
            "specialize le_of_succ_le_succ x",
            "specialize le_of_succ_le_succ 0",
            "apply le_of_succ_le_succ",
            "exact hc1_right",
            "specialize le_zero x",
            "apply le_zero",
            "exact hle0",
        ),
        "Every natural strictly below three is zero, one, or two.",
    )


def _larger_bound_spec(
    spec: Callable[..., Any],
    *,
    modulus: int,
    base: int,
    base_name: str,
) -> Any:
    commands = ["intro x", "intro hb"]
    previous_bound = "hb"
    for high in range(modulus - 1, base - 1, -1):
        commands.extend(
            (
                f"have hle{high} : exists h. h + x = {high}",
                "specialize le_of_succ_le_succ x",
                f"specialize le_of_succ_le_succ {high}",
                "apply le_of_succ_le_succ",
                f"exact {previous_bound}",
                f"have hc{high} : x = {high} \\/ "
                f"exists h. h + S x = {high}",
                "specialize le_eq_or_lt x",
                f"specialize le_eq_or_lt {high}",
                "apply le_eq_or_lt",
                f"exact hle{high}",
                f"cases hc{high}",
                "right",
                f"exact hc{high}_left",
                "left",
            )
        )
        previous_bound = f"hc{high}_right"
    commands.extend(
        (
            f"specialize {base_name} x",
            f"apply {base_name}",
            f"exact {previous_bound}",
        )
    )
    word = _NUMBER_WORD[modulus]
    return spec(
        f"lt_{word}_cases",
        f"forall x. (exists h. h + S x = {modulus}) -> "
        f"{_equalities('x', tuple(range(modulus)))}",
        ("le_of_succ_le_succ", "le_eq_or_lt", base_name),
        tuple(commands),
        f"Every natural strictly below {word} is one of its canonical values.",
    )


def _select_disjunct(index: int, count: int) -> list[str]:
    if count == 1:
        return []
    if index == count - 1:
        return ["right"]
    return ["left", *_select_disjunct(index, count - 1)]


def _case_left_associated(
    hypothesis: str,
    values: tuple[int, ...],
    branch: Callable[[int, str], list[str]],
) -> list[str]:
    if len(values) == 1:
        return branch(values[0], hypothesis)
    return [
        f"cases {hypothesis}",
        *_case_left_associated(f"{hypothesis}_left", values[:-1], branch),
        *branch(values[-1], f"{hypothesis}_right"),
    ]


def _bounded_square_classification_spec(
    spec: Callable[..., Any],
    modulus: int,
    bound_name: str,
) -> Any:
    residues = _RESIDUES[modulus]
    root_residues = _ROOT_RESIDUES[modulus]
    bounded = _bounded_qres(str(modulus), "a", tag=f"bc{modulus}")
    commands: list[str] = [
        "intro a",
        "intro ha",
        "intro hb",
        "cases hb",
        "cases hb_witness",
        f"have hroots : {_equalities('x', tuple(range(modulus)))}",
        f"specialize {bound_name} x",
        f"apply {bound_name}",
        "exact hb_witness_left",
    ]

    def root_branch(root: int, equality: str) -> list[str]:
        residue = root_residues[root]
        quotient = (root * root - residue) // modulus
        result = [
            f"have hsq : exists u v. {root} * {root} + {modulus} * u = "
            f"a + {modulus} * v",
            f"rewrite {equality} at hb_witness_right",
            f"rewrite {equality} at hb_witness_right",
            "exact hb_witness_right",
            f"have hc : exists u v. {residue} + {modulus} * u = "
            f"({root} * {root}) + {modulus} * v",
            f"exists {quotient}",
            "exists 0",
            "norm_num",
            f"have hra : exists u v. {residue} + {modulus} * u = "
            f"a + {modulus} * v",
            f"specialize mod_eq_trans {modulus}",
            f"specialize mod_eq_trans {residue}",
            f"specialize mod_eq_trans ({root} * {root})",
            "specialize mod_eq_trans a",
            "apply mod_eq_trans",
            "exact hc",
            "exact hsq",
            f"have hrb : exists h. h + S {residue} = {modulus}",
            f"exists {modulus - residue - 1}",
            "norm_num",
            f"have heq : {residue} = a",
            f"specialize mod_eq_bounded_unique {modulus}",
            f"specialize mod_eq_bounded_unique {residue}",
            "specialize mod_eq_bounded_unique a",
            "apply mod_eq_bounded_unique",
            "exact hrb",
            "exact ha",
            "exact hra",
            *_select_disjunct(residues.index(residue), len(residues)),
            "symm",
            "exact heq",
        ]
        return result

    commands.extend(
        _case_left_associated(
            "hroots", tuple(range(modulus)), root_branch
        )
    )
    return spec(
        f"bounded_square_mod{modulus}_classify",
        f"forall a. (exists h. h + S a = {modulus}) -> "
        f"({bounded}) -> ({_equalities('a', residues)})",
        (bound_name, "mod_eq_trans", "mod_eq_bounded_unique"),
        tuple(commands),
        f"A bounded square modulo {modulus} has exactly a canonical square residue.",
    )


def _positive_spec(
    spec: Callable[..., Any],
    modulus: int,
    residue: int,
) -> Any:
    # Use the least convenient root; the only nontrivial directed witness is
    # 3^2 = 2 + 7 for residue two modulo seven.
    roots = {
        (3, 0): (0, 0),
        (3, 1): (1, 0),
        (5, 0): (0, 0),
        (5, 1): (1, 0),
        (5, 4): (2, 0),
        (7, 0): (0, 0),
        (7, 1): (1, 0),
        (7, 2): (3, 1),
        (7, 4): (2, 0),
    }
    root, right_multiple = roots[(modulus, residue)]
    word = _NUMBER_WORD[residue]
    return spec(
        f"qres_mod{modulus}_{word}",
        _qres(str(modulus), str(residue), tag=f"p{modulus}_{residue}"),
        (),
        (
            f"exists {root}",
            "exists 0",
            f"exists {right_multiple}",
            "norm_num",
        ),
        f"The canonical value {residue} is a quadratic residue modulo {modulus}.",
    )


def _canonical_iff_spec(
    spec: Callable[..., Any],
    modulus: int,
) -> Any:
    residues = _RESIDUES[modulus]
    qres = _qres(str(modulus), "a", tag=f"iffq{modulus}")
    bounded = _bounded_qres(str(modulus), "a", tag=f"iffb{modulus}")
    residue_cases = _equalities("a", residues)
    positive_names = tuple(
        f"qres_mod{modulus}_{_NUMBER_WORD[residue]}" for residue in residues
    )
    commands: list[str] = [
        "intro a",
        "intro ha",
        "split",
        "intro hq",
        f"have hequiv : (({qres}) -> ({bounded})) /\\ "
        f"(({bounded}) -> ({qres}))",
        f"specialize quadratic_residue_bounded_equiv {modulus}",
        "specialize quadratic_residue_bounded_equiv a",
        "apply quadratic_residue_bounded_equiv",
        f"specialize succ_ne_zero {modulus - 1}",
        "exact succ_ne_zero",
        "cases hequiv",
        f"have hb : {bounded}",
        "apply hequiv_left",
        "exact hq",
        f"specialize bounded_square_mod{modulus}_classify a",
        f"apply bounded_square_mod{modulus}_classify",
        "exact ha",
        "exact hb",
        "intro hcases",
    ]

    def positive_branch(residue: int, equality: str) -> list[str]:
        name = f"qres_mod{modulus}_{_NUMBER_WORD[residue]}"
        return [f"rewrite {equality}", f"exact {name}"]

    commands.extend(
        _case_left_associated("hcases", residues, positive_branch)
    )
    return spec(
        f"qres_mod{modulus}_canonical_iff",
        f"forall a. (exists h. h + S a = {modulus}) -> "
        f"((({qres}) -> ({residue_cases})) /\\ "
        f"(({residue_cases}) -> ({qres})))",
        (
            "quadratic_residue_bounded_equiv",
            "succ_ne_zero",
            f"bounded_square_mod{modulus}_classify",
            *positive_names,
        ),
        tuple(commands),
        f"For canonical values, the displayed list is exactly QRes modulo {modulus}.",
    )


def _close_distinct_numerals(
    left: int,
    right: int,
    hypothesis: str,
    *,
    tag: str,
) -> list[str]:
    commands: list[str] = []
    current = hypothesis
    step = 0
    while left > 0 and right > 0:
        next_name = f"hne_{tag}_{step}"
        commands.extend(
            (
                f"have {next_name} : {left - 1} = {right - 1}",
                f"specialize succ_injective {left - 1}",
                f"specialize succ_injective {right - 1}",
                "apply succ_injective",
                f"exact {current}",
            )
        )
        current = next_name
        left -= 1
        right -= 1
        step += 1
    commands.append("apply PA1")
    if left == 0:
        commands.append("symm")
    commands.append(f"exact {current}")
    return commands


def _negative_spec(
    spec: Callable[..., Any],
    modulus: int,
    nonresidue: int,
) -> Any:
    residues = _RESIDUES[modulus]
    qres = _qres(
        str(modulus), str(nonresidue), tag=f"n{modulus}_{nonresidue}"
    )
    qres_for_iff = _qres(
        str(modulus), str(nonresidue), tag=f"ni{modulus}_{nonresidue}"
    )
    residue_cases = _equalities(str(nonresidue), residues)
    commands: list[str] = [
        "intro hq",
        f"have ha : exists h. h + S {nonresidue} = {modulus}",
        f"exists {modulus - nonresidue - 1}",
        "norm_num",
        f"have hiff : ((({qres_for_iff}) -> ({residue_cases})) /\\ "
        f"(({residue_cases}) -> ({qres_for_iff})))",
        f"specialize qres_mod{modulus}_canonical_iff {nonresidue}",
        f"apply qres_mod{modulus}_canonical_iff",
        "exact ha",
        "cases hiff",
        f"have hcases : {residue_cases}",
        "apply hiff_left",
        "exact hq",
    ]

    def impossible_branch(residue: int, equality: str) -> list[str]:
        return _close_distinct_numerals(
            nonresidue,
            residue,
            equality,
            tag=f"{modulus}_{nonresidue}_{residue}",
        )

    commands.extend(
        _case_left_associated("hcases", residues, impossible_branch)
    )
    word = _NUMBER_WORD[nonresidue]
    return spec(
        f"not_qres_mod{modulus}_{word}",
        f"~({qres})",
        (f"qres_mod{modulus}_canonical_iff", "succ_injective"),
        tuple(commands),
        f"The canonical value {nonresidue} is not a quadratic residue modulo {modulus}.",
    )


def make_qr_small_moduli_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the complete isolated small-modulus QRes tranche."""

    bound_specs = (
        _lt_three_spec(spec),
        _larger_bound_spec(
            spec,
            modulus=5,
            base=3,
            base_name="lt_three_cases",
        ),
        _larger_bound_spec(
            spec,
            modulus=7,
            base=5,
            base_name="lt_five_cases",
        ),
    )
    bound_names = {
        3: "lt_three_cases",
        5: "lt_five_cases",
        7: "lt_seven_cases",
    }
    bounded_classifications = tuple(
        _bounded_square_classification_spec(spec, modulus, bound_names[modulus])
        for modulus in (3, 5, 7)
    )
    positives = tuple(
        _positive_spec(spec, modulus, residue)
        for modulus in (3, 5, 7)
        for residue in _RESIDUES[modulus]
    )
    canonical_classifications = tuple(
        _canonical_iff_spec(spec, modulus) for modulus in (3, 5, 7)
    )
    negatives = tuple(
        _negative_spec(spec, modulus, value)
        for modulus in (3, 5, 7)
        for value in range(modulus)
        if value not in _RESIDUES[modulus]
    )
    return (
        *bound_specs,
        *bounded_classifications,
        *positives,
        *canonical_classifications,
        *negatives,
    )


__all__ = ["make_qr_small_moduli_theorems"]
