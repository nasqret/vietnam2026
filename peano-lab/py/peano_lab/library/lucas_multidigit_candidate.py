"""Constructive coherent, arbitrarily long base-p digit traces for Lucas.

All decoded streams are real beta-coded natural witnesses.  Their step graph
records the exact successive quotient and bounded remainder, rather than an
independent list of unrelated digit divisions.  Every authoring relation is
fully expanded into the unchanged first-order language of Heyting arithmetic.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_choose_foundation_candidate import _choose_relation_term
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import _beta_at_term, product_relation, product_successor_relation


LUCAS_DIGIT_CHAIN_INITIAL_CODE_EXISTS = "lucas_digit_chain_initial_code_exists"
LUCAS_DIGIT_CHAIN_EMPTY = "lucas_digit_chain_empty"
LUCAS_DIGIT_CHAIN_EMPTY_EXISTS = "lucas_digit_chain_empty_exists"
LUCAS_DIGIT_CHAIN_EXTEND = "lucas_digit_chain_extend"
LUCAS_DIGIT_CHAIN_EXISTS = "lucas_digit_chain_exists"
LUCAS_PRIME_DIGIT_CHAIN_EXISTS = "lucas_prime_digit_chain_exists"
LUCAS_DIGIT_CHAIN_INITIAL_VALUE = "lucas_digit_chain_initial_value"
LUCAS_DIGIT_CHAIN_STEP_EXISTS = "lucas_digit_chain_step_exists"
LUCAS_MODULAR_BACKWARD_PRODUCT_FOLD = "lucas_modular_backward_product_fold"
LUCAS_CHOOSE_PREFIX_EMPTY = "lucas_choose_prefix_empty"
LUCAS_CHOOSE_PREFIX_EXTEND = "lucas_choose_prefix_extend"
LUCAS_CHOOSE_PREFIX_EXISTS = "lucas_choose_prefix_exists"
LUCAS_CHOOSE_PREFIX_POINT = "lucas_choose_prefix_point"
LUCAS_MULTIDIGIT_CONGRUENCE_FROM_ONE_STEP = (
    "lucas_multidigit_congruence_from_one_step"
)
LUCAS_TERMINATING_MULTIDIGIT_THEOREM_FROM_ONE_STEP = (
    "lucas_terminating_multidigit_theorem_from_one_step"
)
LUCAS_PRIME_DIGIT_NONZERO_QUOTIENT_STRICT = (
    "lucas_prime_digit_nonzero_quotient_strict"
)
LUCAS_PRIME_DIGIT_CHAIN_NONZERO_INDEX_BOUND = (
    "lucas_prime_digit_chain_nonzero_index_bound"
)
LUCAS_PRIME_DIGIT_CHAIN_TERMINAL_ZERO = "lucas_prime_digit_chain_terminal_zero"
LUCAS_TERMINATING_PRIME_DIGIT_CHAIN_EXISTS = (
    "lucas_terminating_prime_digit_chain_exists"
)
LUCAS_MULTIDIGIT_CONGRUENCE = "lucas_multidigit_congruence"
LUCAS_TERMINATING_MULTIDIGIT_THEOREM = "lucas_terminating_multidigit_theorem"
LUCAS_THEOREM_FOR_LENGTH = "lucas_theorem_for_length"
LUCAS_THEOREM = "lucas_theorem"


def _at(code: str, scale: str, index: str, value: str, *, tag: str) -> str:
    return _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"lmd_{tag}",
        avoid=(
            "p", "n", "qb", "qc", "db", "dc", "l", "i", "q", "Q", "d",
            "z", "t", "u", "v", "x", "x1", "x2", "x3", "x4", "x5", "x6",
            "x7", "x8", "x9", "y", "j",
        ),
    )


def _lt(left: str, right: str, *, tag: str) -> str:
    gap = f"lmd_gap_{tag}"
    return f"exists {gap}. {gap} + S ({left}) = ({right})"


def _le(left: str, right: str, *, tag: str) -> str:
    gap = f"lmd_le_gap_{tag}"
    return f"exists {gap}. {gap} + ({left}) = ({right})"


def _mod_equal(modulus: str, left: str, right: str, *, tag: str) -> str:
    source = f"lmd_mod_left_{tag}"
    target = f"lmd_mod_right_{tag}"
    return (
        f"exists {source} {target}. ({left}) + ({modulus}) * {source} = "
        f"({right}) + ({modulus}) * {target}"
    )


def lucas_digit_chain(
    base: str,
    value: str,
    quotient_code: str,
    quotient_scale: str,
    digit_code: str,
    digit_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a coherent beta-coded length-``length`` base-p digit chain."""

    index = f"lmd_index_{tag}"
    current = f"lmd_current_{tag}"
    successor = f"lmd_successor_{tag}"
    digit = f"lmd_digit_{tag}"
    initial = _at(quotient_code, quotient_scale, "0", value, tag=f"{tag}_initial")
    bounded = _lt(index, length, tag=f"{tag}_index")
    at_current = _at(
        quotient_code, quotient_scale, index, current, tag=f"{tag}_current"
    )
    at_next = _at(
        quotient_code,
        quotient_scale,
        f"S {index}",
        successor,
        tag=f"{tag}_successor",
    )
    at_digit = _at(digit_code, digit_scale, index, digit, tag=f"{tag}_digit")
    digit_bound = _lt(digit, base, tag=f"{tag}_digit_bound")
    return (
        f"(({initial}) /\\ forall {index}. ({bounded}) -> "
        f"exists {current} {successor} {digit}. "
        f"(({at_current}) /\\ (({at_next}) /\\ (({at_digit}) /\\ "
        f"(({current} = ({base}) * ({successor}) + ({digit})) /\\ "
        f"({digit_bound}))))))"
    )


def lucas_modular_step_trace(
    modulus: str,
    factor_code: str,
    factor_scale: str,
    value_code: str,
    value_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand backward pointwise congruence along a beta-coded value trace."""

    index = f"lmd_step_index_{tag}"
    source = f"lmd_step_source_{tag}"
    successor = f"lmd_step_successor_{tag}"
    factor = f"lmd_step_factor_{tag}"
    bound = _lt(index, length, tag=f"{tag}_bound")
    at_source = _at(value_code, value_scale, index, source, tag=f"{tag}_source")
    at_successor = _at(
        value_code,
        value_scale,
        f"S {index}",
        successor,
        tag=f"{tag}_successor",
    )
    at_factor = _at(factor_code, factor_scale, index, factor, tag=f"{tag}_factor")
    congruence = _mod_equal(
        modulus,
        source,
        f"{successor} * {factor}",
        tag=f"{tag}_congruence",
    )
    return (
        f"forall {index} {source} {successor} {factor}. "
        f"({bound}) -> ({at_source}) -> ({at_successor}) -> "
        f"({at_factor}) -> ({congruence})"
    )


def lucas_choose_prefix(
    upper_code: str,
    upper_scale: str,
    lower_code: str,
    lower_scale: str,
    output_code: str,
    output_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a beta-coded prefix of relational binomial coefficients."""

    index = f"lmd_choose_index_{tag}"
    upper = f"lmd_choose_upper_{tag}"
    lower = f"lmd_choose_lower_{tag}"
    coefficient = f"lmd_choose_value_{tag}"
    upper_entry = _at(upper_code, upper_scale, index, upper, tag=f"{tag}_upper")
    lower_entry = _at(lower_code, lower_scale, index, lower, tag=f"{tag}_lower")
    result_entry = _at(
        output_code, output_scale, index, coefficient, tag=f"{tag}_result"
    )
    choose = _choose_relation_term(
        upper,
        lower,
        coefficient,
        tag=f"lmd_{tag}_choose",
        variables=(index, upper, lower, coefficient),
    )
    return (
        f"forall {index}. ({_lt(index, length, tag=f'{tag}_bound')}) -> "
        f"exists {upper} {lower} {coefficient}. "
        f"(({upper_entry}) /\\ (({lower_entry}) /\\ "
        f"(({result_entry}) /\\ ({choose}))))"
    )


def lucas_one_step_division_hypothesis(*, tag: str) -> str:
    """Expand the exact universal prime-block Lucas step, with named divisions."""

    variables = ("p", "n", "k", "q", "r", "a", "b", "C", "A", "D")
    whole = _choose_relation_term("n", "k", "C", tag=f"lmd_{tag}_whole", variables=variables)
    upper = _choose_relation_term("q", "r", "A", tag=f"lmd_{tag}_upper", variables=variables)
    digit = _choose_relation_term("a", "b", "D", tag=f"lmd_{tag}_digit", variables=variables)
    return (
        "forall p n k q r a b C A D. "
        f"({prime('p', tag=f'lmd_{tag}_prime')}) -> "
        "n = p * q + a -> k = p * r + b -> "
        f"({_lt('a', 'p', tag=f'{tag}_a')}) -> "
        f"({_lt('b', 'p', tag=f'{tag}_b')}) -> "
        f"({whole}) -> ({upper}) -> ({digit}) -> "
        f"({_mod_equal('p', 'C', 'A * D', tag=f'{tag}_result')})"
    )


def make_lucas_multidigit_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build arbitrarily long, coherent constructive quotient/digit traces."""

    initial = _at("qb", "qc", "0", "n", tag="initial_source")
    empty_chain = lucas_digit_chain(
        "p", "n", "qb", "qc", "db", "dc", "0", tag="empty"
    )
    current_chain = lucas_digit_chain(
        "p", "n", "qb", "qc", "db", "dc", "l", tag="extend_source"
    )
    next_chain = lucas_digit_chain(
        "p", "n", "z", "t", "u", "v", "S l", tag="extend_result"
    )
    general_chain = lucas_digit_chain(
        "p", "n", "qb", "qc", "db", "dc", "l", tag="total_result"
    )
    next_total = lucas_digit_chain(
        "p", "n", "qb", "qc", "db", "dc", "S l", tag="total_next"
    )
    previous_total = lucas_digit_chain(
        "p", "n", "qb", "qc", "db", "dc", "l", tag="total_previous"
    )
    step_bound = _lt("i", "l", tag="point_index")
    step_current = _at("qb", "qc", "i", "q", tag="point_current")
    step_next = _at("qb", "qc", "S i", "Q", tag="point_next")
    step_digit = _at("db", "dc", "i", "d", tag="point_digit")
    step_digit_bound = _lt("d", "p", tag="point_digit_bound")
    step_result = (
        "exists q Q d. "
        f"(({step_current}) /\\ (({step_next}) /\\ (({step_digit}) /\\ "
        f"((q = p * Q + d) /\\ ({step_digit_bound})))))"
    )

    quotient_extension = (
        "exists z t. "
        f"(({_at('z', 't', 'S l', 'x1', tag='quotient_new')}) /\\ "
        "forall i y. "
        f"({_lt('i', 'S l', tag='quotient_preserve_bound')}) -> "
        f"({_at('qb', 'qc', 'i', 'y', tag='quotient_preserve_old')}) -> "
        f"({_at('z', 't', 'i', 'y', tag='quotient_preserve_new')}))"
    )
    digit_extension = (
        "exists u v. "
        f"(({_at('u', 'v', 'l', 'x2', tag='digit_new')}) /\\ "
        "forall i y. "
        f"({_lt('i', 'l', tag='digit_preserve_bound')}) -> "
        f"({_at('db', 'dc', 'i', 'y', tag='digit_preserve_old')}) -> "
        f"({_at('u', 'v', 'i', 'y', tag='digit_preserve_new')}))"
    )
    previous_step = (
        "exists q Q d. "
        f"(({_at('qb', 'qc', 'i', 'q', tag='old_current')}) /\\ "
        f"(({_at('qb', 'qc', 'S i', 'Q', tag='old_next')}) /\\ "
        f"(({_at('db', 'dc', 'i', 'd', tag='old_digit')}) /\\ "
        f"((q = p * Q + d) /\\ ({_lt('d', 'p', tag='old_bound')})))))"
    )
    modular_product = product_relation("b", "c", "l", "P", tag="lmd_fold_product")
    modular_start = _at("z", "t", "0", "n", tag="fold_start")
    modular_terminal = _at("z", "t", "l", "k", tag="fold_terminal")
    modular_trace = lucas_modular_step_trace(
        "p", "b", "c", "z", "t", "l", tag="fold_trace"
    )
    modular_result = _mod_equal("p", "n", "k * P", tag="fold_result")
    modular_decomposition = (
        "exists D R. "
        f"(({_at('b', 'c', 'l', 'D', tag='fold_last_factor')}) /\\ "
        f"(({product_relation('b', 'c', 'l', 'R', tag='lmd_fold_previous')}) /\\ "
        "P = R * D))"
    )
    restricted_trace = lucas_modular_step_trace(
        "p", "b", "c", "z", "t", "l", tag="fold_restricted"
    )
    choose_empty = lucas_choose_prefix(
        "qb", "qc", "db", "dc", "z", "t", "0", tag="choose_empty"
    )
    choose_before = lucas_choose_prefix(
        "qb", "qc", "db", "dc", "z", "t", "l", tag="choose_before"
    )
    choose_after = lucas_choose_prefix(
        "qb", "qc", "db", "dc", "u", "v", "S l", tag="choose_after"
    )
    choose_total = lucas_choose_prefix(
        "qb", "qc", "db", "dc", "z", "t", "l", tag="choose_total"
    )
    choose_previous = lucas_choose_prefix(
        "qb", "qc", "db", "dc", "z", "t", "l", tag="choose_previous"
    )
    choose_extended_code = (
        "exists u v. "
        f"(({_at('u', 'v', 'l', 'x2', tag='choose_extended_new')}) /\\ "
        "forall i y. "
        f"({_lt('i', 'l', tag='choose_extended_bound')}) -> "
        f"({_at('z', 't', 'i', 'y', tag='choose_extended_old')}) -> "
        f"({_at('u', 'v', 'i', 'y', tag='choose_extended_target')}))"
    )
    choose_old_entry = (
        "exists a b C. "
        f"(({_at('qb', 'qc', 'i', 'a', tag='choose_old_upper')}) /\\ "
        f"(({_at('db', 'dc', 'i', 'b', tag='choose_old_lower')}) /\\ "
        f"(({_at('z', 't', 'i', 'C', tag='choose_old_value')}) /\\ "
        f"({_choose_relation_term('a', 'b', 'C', tag='lmd_old_choose', variables=('a','b','C'))}))))"
    )
    choose_point = _choose_relation_term(
        "a", "b", "C", tag="lmd_choose_point", variables=("a", "b", "C")
    )
    choose_point_script: list[str] = [
        "intro qb", "intro qc", "intro db", "intro dc", "intro z", "intro t",
        "intro l", "intro i", "intro a", "intro b", "intro C", "intro hprefix",
        "intro hi", "intro ha", "intro hb", "intro hC",
        f"have hchoice : {choose_old_entry}",
        "specialize hprefix i", "apply hprefix", "exact hi",
        "cases hchoice", "cases hchoice_witness", "cases hchoice_witness_witness",
        "cases hchoice_witness_witness_witness",
        "cases hchoice_witness_witness_witness_right",
        "cases hchoice_witness_witness_witness_right_right",
        "have hupper : x = a",
        "specialize beta_at_unique qb", "specialize beta_at_unique qc",
        "specialize beta_at_unique i", "specialize beta_at_unique x",
        "specialize beta_at_unique a", "apply beta_at_unique",
        "exact hchoice_witness_witness_witness_left", "exact ha",
        "have hlower : x1 = b",
        "specialize beta_at_unique db", "specialize beta_at_unique dc",
        "specialize beta_at_unique i", "specialize beta_at_unique x1",
        "specialize beta_at_unique b", "apply beta_at_unique",
        "exact hchoice_witness_witness_witness_right_left", "exact hb",
        "have hvalue : x2 = C",
        "specialize beta_at_unique z", "specialize beta_at_unique t",
        "specialize beta_at_unique i", "specialize beta_at_unique x2",
        "specialize beta_at_unique C", "apply beta_at_unique",
        "exact hchoice_witness_witness_witness_right_right_left", "exact hC",
    ]
    choose_point_script.extend(
        "rewrite hupper at hchoice_witness_witness_witness_right_right_right"
        for _ in range(9)
    )
    choose_point_script.extend(
        "rewrite hlower at hchoice_witness_witness_witness_right_right_right"
        for _ in range(4)
    )
    choose_point_script.extend(
        "rewrite hvalue at hchoice_witness_witness_witness_right_right_right"
        for _ in range(3)
    )
    choose_point_script.append("exact hchoice_witness_witness_witness_right_right_right")
    one_step = lucas_one_step_division_hypothesis(tag="universal")
    full_n_chain = lucas_digit_chain(
        "p", "n", "qb", "qc", "db", "dc", "l", tag="full_n"
    )
    full_k_chain = lucas_digit_chain(
        "p", "k", "ub", "uc", "vb", "vc", "l", tag="full_k"
    )
    full_quotient_choose = lucas_choose_prefix(
        "qb", "qc", "ub", "uc", "z", "t", "S l", tag="full_quotient_choose"
    )
    full_digit_choose = lucas_choose_prefix(
        "db", "dc", "vb", "vc", "s", "w", "l", tag="full_digit_choose"
    )
    full_product = product_relation("s", "w", "l", "P", tag="lmd_full_product")
    full_start = _at("z", "t", "0", "C", tag="full_coefficient_start")
    full_end = _at("z", "t", "l", "T", tag="full_coefficient_end")
    full_trace = lucas_modular_step_trace(
        "p", "s", "w", "z", "t", "l", tag="full_trace"
    )
    full_result = _mod_equal("p", "C", "T * P", tag="full_result")
    full_variables = (
        "p", "n", "k", "l", "qb", "qc", "db", "dc", "ub", "uc", "vb", "vc",
        "z", "t", "s", "w", "P", "C", "T",
    )
    full_tail = (
        f"forall {' '.join(full_variables)}. "
        f"({prime('p',tag='lmd_full_prime')}) -> ({full_n_chain}) -> "
        f"({full_k_chain}) -> ({full_quotient_choose}) -> "
        f"({full_digit_choose}) -> ({full_product}) -> "
        f"({full_start}) -> ({full_end}) -> ({full_result})"
    )
    full_introductions = tuple(f"intro {value}" for value in full_variables)
    full_n_step = (
        "exists q Q d. "
        f"(({_at('qb','qc','i','q',tag='full_n_current')}) /\\ "
        f"(({_at('qb','qc','S i','Q',tag='full_n_next')}) /\\ "
        f"(({_at('db','dc','i','d',tag='full_n_digit')}) /\\ "
        f"((q = p * Q + d) /\\ ({_lt('d','p',tag='full_n_digit_bound')})))))"
    )
    full_k_step = (
        "exists q Q d. "
        f"(({_at('ub','uc','i','q',tag='full_k_current')}) /\\ "
        f"(({_at('ub','uc','S i','Q',tag='full_k_next')}) /\\ "
        f"(({_at('vb','vc','i','d',tag='full_k_digit')}) /\\ "
        f"((q = p * Q + d) /\\ ({_lt('d','p',tag='full_k_digit_bound')})))))"
    )
    whole_choice = _choose_relation_term(
        "x", "x3", "A", tag="lmd_full_whole", variables=("x", "x3", "A")
    )
    quotient_choice = _choose_relation_term(
        "x1", "x4", "B", tag="lmd_full_upper", variables=("x1", "x4", "B")
    )
    digit_choice = _choose_relation_term(
        "x2", "x5", "D", tag="lmd_full_digit", variables=("x2", "x5", "D")
    )
    full_endpoint_script: list[str] = ["intro hstep", *full_introductions]
    full_endpoint_script.extend(
        (
            "intro hprime", "intro hnchain", "intro hkchain", "intro hquotientchoose",
            "intro hdigitchoose", "intro hproduct", "intro hstart", "intro hterminal",
            f"have htrace : {full_trace}",
            "intro i", "intro A", "intro B", "intro D", "intro hi",
            "intro hA", "intro hB", "intro hD",
            "cases hnchain", "cases hkchain",
            f"have hnstep : {full_n_step}",
            "specialize hnchain_right i", "apply hnchain_right", "exact hi",
            "cases hnstep", "cases hnstep_witness", "cases hnstep_witness_witness",
            "cases hnstep_witness_witness_witness",
            "cases hnstep_witness_witness_witness_right",
            "cases hnstep_witness_witness_witness_right_right",
            "cases hnstep_witness_witness_witness_right_right_right",
            f"have hkstep : {full_k_step}",
            "specialize hkchain_right i", "apply hkchain_right", "exact hi",
            "cases hkstep", "cases hkstep_witness", "cases hkstep_witness_witness",
            "cases hkstep_witness_witness_witness",
            "cases hkstep_witness_witness_witness_right",
            "cases hkstep_witness_witness_witness_right_right",
            "cases hkstep_witness_witness_witness_right_right_right",
            "have hindex : exists gap. gap + S i = S l",
            "specialize lt_of_lt_of_le i", "specialize lt_of_lt_of_le l",
            "specialize lt_of_lt_of_le (S l)", "apply lt_of_lt_of_le",
            "exact hi", "specialize le_succ_self l", "exact le_succ_self",
            "have hnextindex : exists gap. gap + S (S i) = S l",
            "specialize succ_le_succ (S i)", "specialize succ_le_succ l",
            "apply succ_le_succ", "exact hi",
            f"have hwhole : ({whole_choice})",
            "specialize lucas_choose_prefix_point qb",
            "specialize lucas_choose_prefix_point qc",
            "specialize lucas_choose_prefix_point ub",
            "specialize lucas_choose_prefix_point uc",
            "specialize lucas_choose_prefix_point z",
            "specialize lucas_choose_prefix_point t",
            "specialize lucas_choose_prefix_point (S l)",
            "specialize lucas_choose_prefix_point i",
            "specialize lucas_choose_prefix_point x",
            "specialize lucas_choose_prefix_point x3",
            "specialize lucas_choose_prefix_point A",
            "apply lucas_choose_prefix_point", "exact hquotientchoose", "exact hindex",
            "exact hnstep_witness_witness_witness_left",
            "exact hkstep_witness_witness_witness_left", "exact hA",
            f"have hupper : ({quotient_choice})",
            "specialize lucas_choose_prefix_point qb",
            "specialize lucas_choose_prefix_point qc",
            "specialize lucas_choose_prefix_point ub",
            "specialize lucas_choose_prefix_point uc",
            "specialize lucas_choose_prefix_point z",
            "specialize lucas_choose_prefix_point t",
            "specialize lucas_choose_prefix_point (S l)",
            "specialize lucas_choose_prefix_point (S i)",
            "specialize lucas_choose_prefix_point x1",
            "specialize lucas_choose_prefix_point x4",
            "specialize lucas_choose_prefix_point B",
            "apply lucas_choose_prefix_point", "exact hquotientchoose", "exact hnextindex",
            "exact hnstep_witness_witness_witness_right_left",
            "exact hkstep_witness_witness_witness_right_left", "exact hB",
            f"have hdigit : ({digit_choice})",
            "specialize lucas_choose_prefix_point db",
            "specialize lucas_choose_prefix_point dc",
            "specialize lucas_choose_prefix_point vb",
            "specialize lucas_choose_prefix_point vc",
            "specialize lucas_choose_prefix_point s",
            "specialize lucas_choose_prefix_point w",
            "specialize lucas_choose_prefix_point l",
            "specialize lucas_choose_prefix_point i",
            "specialize lucas_choose_prefix_point x2",
            "specialize lucas_choose_prefix_point x5",
            "specialize lucas_choose_prefix_point D",
            "apply lucas_choose_prefix_point", "exact hdigitchoose", "exact hi",
            "exact hnstep_witness_witness_witness_right_right_left",
            "exact hkstep_witness_witness_witness_right_right_left", "exact hD",
            "specialize hstep p", "specialize hstep x", "specialize hstep x3",
            "specialize hstep x1", "specialize hstep x4", "specialize hstep x2",
            "specialize hstep x5", "specialize hstep A", "specialize hstep B",
            "specialize hstep D", "apply hstep", "exact hprime",
            "exact hnstep_witness_witness_witness_right_right_right_left",
            "exact hkstep_witness_witness_witness_right_right_right_left",
            "exact hnstep_witness_witness_witness_right_right_right_right",
            "exact hkstep_witness_witness_witness_right_right_right_right",
            "exact hwhole", "exact hupper", "exact hdigit",
            "specialize lucas_modular_backward_product_fold l",
            "specialize lucas_modular_backward_product_fold p",
            "specialize lucas_modular_backward_product_fold s",
            "specialize lucas_modular_backward_product_fold w",
            "specialize lucas_modular_backward_product_fold z",
            "specialize lucas_modular_backward_product_fold t",
            "specialize lucas_modular_backward_product_fold C",
            "specialize lucas_modular_backward_product_fold T",
            "specialize lucas_modular_backward_product_fold P",
            "apply lucas_modular_backward_product_fold", "exact hproduct",
            "exact hstart", "exact hterminal", "exact htrace",
        )
    )
    terminal_zero_upper = _at("qb", "qc", "l", "0", tag="terminal_upper_zero")
    terminal_zero_lower = _at("ub", "uc", "l", "0", tag="terminal_lower_zero")
    terminal_choose = _choose_relation_term(
        "0", "0", "T", tag="lmd_terminal_zero_choose", variables=("T",)
    )
    terminal_script: list[str] = ["intro hstep", *full_introductions]
    terminal_script.extend(
        (
            "intro hprime", "intro hnchain", "intro hkchain", "intro hquotientchoose",
            "intro hdigitchoose", "intro hproduct", "intro hstart", "intro hterminal",
            "intro hnzero", "intro hkzero",
            f"have hchoose : ({terminal_choose})",
            "specialize lucas_choose_prefix_point qb",
            "specialize lucas_choose_prefix_point qc",
            "specialize lucas_choose_prefix_point ub",
            "specialize lucas_choose_prefix_point uc",
            "specialize lucas_choose_prefix_point z",
            "specialize lucas_choose_prefix_point t",
            "specialize lucas_choose_prefix_point (S l)",
            "specialize lucas_choose_prefix_point l",
            "specialize lucas_choose_prefix_point 0",
            "specialize lucas_choose_prefix_point 0",
            "specialize lucas_choose_prefix_point T",
            "apply lucas_choose_prefix_point", "exact hquotientchoose",
            "exists 0", "apply zero_add", "exact hnzero", "exact hkzero", "exact hterminal",
            "have hone : T = 1",
            "specialize choose_zero 0", "specialize choose_zero T",
            "apply choose_zero", "exact hchoose",
            f"have hglobal : {full_tail}",
            "apply lucas_multidigit_congruence_from_one_step", "exact hstep",
        )
    )
    terminal_tail = (
        f"forall {' '.join(full_variables)}. "
        f"({prime('p',tag='lmd_terminal_prime')}) -> ({full_n_chain}) -> "
        f"({full_k_chain}) -> ({full_quotient_choose}) -> "
        f"({full_digit_choose}) -> ({full_product}) -> "
        f"({full_start}) -> ({full_end}) -> ({terminal_zero_upper}) -> "
        f"({terminal_zero_lower}) -> "
        f"({_mod_equal('p','C','P',tag='terminal_final')})"
    )
    unconditional_full_script: list[str] = list(full_introductions)
    unconditional_full_script.extend(
        (
            "intro hprime", "intro hnchain", "intro hkchain", "intro hquotientchoose",
            "intro hdigitchoose", "intro hproduct", "intro hstart", "intro hterminal",
            f"have hglobal : {full_tail}",
            "apply lucas_multidigit_congruence_from_one_step",
            "exact lucas_one_step_division_congruence",
        )
    )
    unconditional_full_script.extend(f"specialize hglobal {value}" for value in full_variables)
    unconditional_full_script.extend(
        (
            "apply hglobal", "exact hprime", "exact hnchain", "exact hkchain",
            "exact hquotientchoose", "exact hdigitchoose", "exact hproduct",
            "exact hstart", "exact hterminal",
        )
    )
    unconditional_terminal_script: list[str] = list(full_introductions)
    unconditional_terminal_script.extend(
        (
            "intro hprime", "intro hnchain", "intro hkchain", "intro hquotientchoose",
            "intro hdigitchoose", "intro hproduct", "intro hstart", "intro hterminal",
            "intro hnzero", "intro hkzero",
            f"have hglobal : {terminal_tail}",
            "apply lucas_terminating_multidigit_theorem_from_one_step",
            "exact lucas_one_step_division_congruence",
        )
    )
    witness_package = (
        f"(({full_n_chain}) /\\ (({full_k_chain}) /\\ "
        f"(({terminal_zero_upper}) /\\ (({terminal_zero_lower}) /\\ "
        f"(({full_quotient_choose}) /\\ (({full_digit_choose}) /\\ "
        f"(({full_product}) /\\ (({full_start}) /\\ "
        f"({_mod_equal('p','C','P',tag='universal_result')})))))))))"
    )
    package_variables = (
        "qb", "qc", "db", "dc", "ub", "uc", "vb", "vc", "z", "t", "s", "w", "P"
    )
    package_exists = f"exists {' '.join(package_variables)}. ({witness_package})"
    length_choose = _choose_relation_term(
        "n", "k", "C", tag="lmd_universal_choose", variables=("p", "n", "k", "C", "l")
    )
    hn_construct = (
        "exists qb qc db dc. "
        f"(({lucas_digit_chain('p','n','qb','qc','db','dc','l',tag='universal_n_chain')}) /\\ "
        f"({_at('qb','qc','l','0',tag='universal_n_zero')}))"
    )
    hk_construct = (
        "exists ub uc vb vc. "
        f"(({lucas_digit_chain('p','k','ub','uc','vb','vc','l',tag='universal_k_chain')}) /\\ "
        f"({_at('ub','uc','l','0',tag='universal_k_zero')}))"
    )
    quotient_construct = (
        "exists z t. "
        f"({lucas_choose_prefix('x','x1','x4','x5','z','t','S l',tag='universal_quotient')})"
    )
    digit_construct = (
        "exists s w. "
        f"({lucas_choose_prefix('x2','x3','x6','x7','s','w','l',tag='universal_digit')})"
    )
    product_construct = (
        "exists P. "
        f"({product_relation('x10','x11','l','P',tag='lmd_universal_construct_product')})"
    )
    current_choose = _choose_relation_term(
        "n", "k", "x13", tag="lmd_universal_current_choose", variables=("n", "k", "x13")
    )
    length_script: list[str] = [
        "intro p", "intro n", "intro k", "intro C", "intro l",
        "intro hprime", "intro hnlength", "intro hklength", "intro hchoose",
        f"have hnchain : {hn_construct}",
        "specialize lucas_terminating_prime_digit_chain_exists p",
        "specialize lucas_terminating_prime_digit_chain_exists n",
        "specialize lucas_terminating_prime_digit_chain_exists l",
        "apply lucas_terminating_prime_digit_chain_exists", "exact hprime", "exact hnlength",
        "cases hnchain", "cases hnchain_witness", "cases hnchain_witness_witness",
        "cases hnchain_witness_witness_witness", "cases hnchain_witness_witness_witness_witness",
        f"have hkchain : {hk_construct}",
        "specialize lucas_terminating_prime_digit_chain_exists p",
        "specialize lucas_terminating_prime_digit_chain_exists k",
        "specialize lucas_terminating_prime_digit_chain_exists l",
        "apply lucas_terminating_prime_digit_chain_exists", "exact hprime", "exact hklength",
        "cases hkchain", "cases hkchain_witness", "cases hkchain_witness_witness",
        "cases hkchain_witness_witness_witness", "cases hkchain_witness_witness_witness_witness",
        f"have hquotient : {quotient_construct}",
        "specialize lucas_choose_prefix_exists x", "specialize lucas_choose_prefix_exists x1",
        "specialize lucas_choose_prefix_exists x4", "specialize lucas_choose_prefix_exists x5",
        "specialize lucas_choose_prefix_exists (S l)", "exact lucas_choose_prefix_exists",
        "cases hquotient", "cases hquotient_witness",
        f"have hdigit : {digit_construct}",
        "specialize lucas_choose_prefix_exists x2", "specialize lucas_choose_prefix_exists x3",
        "specialize lucas_choose_prefix_exists x6", "specialize lucas_choose_prefix_exists x7",
        "specialize lucas_choose_prefix_exists l", "exact lucas_choose_prefix_exists",
        "cases hdigit", "cases hdigit_witness",
        f"have hproduct : {product_construct}",
        "specialize beta_product_exists x10", "specialize beta_product_exists x11",
        "specialize beta_product_exists l", "exact beta_product_exists", "cases hproduct",
        f"have hdecoded : exists A. ({_at('x8','x9','0','A',tag='universal_coefficient_zero')})",
        "specialize beta_at_exists x8", "specialize beta_at_exists x9",
        "specialize beta_at_exists 0", "exact beta_at_exists", "cases hdecoded",
        f"have hninitial : ({_at('x','x1','0','n',tag='universal_n_initial')})",
        "specialize lucas_digit_chain_initial_value p",
        "specialize lucas_digit_chain_initial_value n",
        "specialize lucas_digit_chain_initial_value x",
        "specialize lucas_digit_chain_initial_value x1",
        "specialize lucas_digit_chain_initial_value x2",
        "specialize lucas_digit_chain_initial_value x3",
        "specialize lucas_digit_chain_initial_value l",
        "apply lucas_digit_chain_initial_value", "exact hnchain_witness_witness_witness_witness_left",
        f"have hkinitial : ({_at('x4','x5','0','k',tag='universal_k_initial')})",
        "specialize lucas_digit_chain_initial_value p",
        "specialize lucas_digit_chain_initial_value k",
        "specialize lucas_digit_chain_initial_value x4",
        "specialize lucas_digit_chain_initial_value x5",
        "specialize lucas_digit_chain_initial_value x6",
        "specialize lucas_digit_chain_initial_value x7",
        "specialize lucas_digit_chain_initial_value l",
        "apply lucas_digit_chain_initial_value", "exact hkchain_witness_witness_witness_witness_left",
        f"have hcoefficient : ({current_choose})",
        "specialize lucas_choose_prefix_point x", "specialize lucas_choose_prefix_point x1",
        "specialize lucas_choose_prefix_point x4", "specialize lucas_choose_prefix_point x5",
        "specialize lucas_choose_prefix_point x8", "specialize lucas_choose_prefix_point x9",
        "specialize lucas_choose_prefix_point (S l)", "specialize lucas_choose_prefix_point 0",
        "specialize lucas_choose_prefix_point n", "specialize lucas_choose_prefix_point k",
        "specialize lucas_choose_prefix_point x13", "apply lucas_choose_prefix_point",
        "exact hquotient_witness_witness", "exists l", "simp", "exact hninitial",
        "exact hkinitial", "exact hdecoded_witness",
        "have hsame : x13 = C", "specialize choose_functional n",
        "specialize choose_functional k", "specialize choose_functional x13",
        "specialize choose_functional C", "apply choose_functional", "exact hcoefficient",
        "exact hchoose", "rewrite hsame at hdecoded_witness",
        "rewrite hsame at hdecoded_witness",
        f"have hterminal : exists T. ({_at('x8','x9','l','T',tag='universal_terminal')})",
        "specialize beta_at_exists x8", "specialize beta_at_exists x9",
        "specialize beta_at_exists l", "exact beta_at_exists", "cases hterminal",
        f"have hcongruence : ({_mod_equal('p','C','x12',tag='universal_congruence')})",
        "specialize lucas_terminating_multidigit_theorem p",
        "specialize lucas_terminating_multidigit_theorem n",
        "specialize lucas_terminating_multidigit_theorem k",
        "specialize lucas_terminating_multidigit_theorem l",
        "specialize lucas_terminating_multidigit_theorem x",
        "specialize lucas_terminating_multidigit_theorem x1",
        "specialize lucas_terminating_multidigit_theorem x2",
        "specialize lucas_terminating_multidigit_theorem x3",
        "specialize lucas_terminating_multidigit_theorem x4",
        "specialize lucas_terminating_multidigit_theorem x5",
        "specialize lucas_terminating_multidigit_theorem x6",
        "specialize lucas_terminating_multidigit_theorem x7",
        "specialize lucas_terminating_multidigit_theorem x8",
        "specialize lucas_terminating_multidigit_theorem x9",
        "specialize lucas_terminating_multidigit_theorem x10",
        "specialize lucas_terminating_multidigit_theorem x11",
        "specialize lucas_terminating_multidigit_theorem x12",
        "specialize lucas_terminating_multidigit_theorem C",
        "specialize lucas_terminating_multidigit_theorem x14",
        "apply lucas_terminating_multidigit_theorem", "exact hprime",
        "exact hnchain_witness_witness_witness_witness_left",
        "exact hkchain_witness_witness_witness_witness_left",
        "exact hquotient_witness_witness", "exact hdigit_witness_witness",
        "exact hproduct_witness", "exact hdecoded_witness", "exact hterminal_witness",
        "exact hnchain_witness_witness_witness_witness_right",
        "exact hkchain_witness_witness_witness_witness_right",
    ]
    length_script.extend(f"exists x{index}" if index else "exists x" for index in range(13))
    length_script.extend(
        (
            "split", "exact hnchain_witness_witness_witness_witness_left",
            "split", "exact hkchain_witness_witness_witness_witness_left",
            "split", "exact hnchain_witness_witness_witness_witness_right",
            "split", "exact hkchain_witness_witness_witness_witness_right",
            "split", "exact hquotient_witness_witness", "split", "exact hdigit_witness_witness",
            "split", "exact hproduct_witness", "split", "exact hdecoded_witness",
            "exact hcongruence",
        )
    )
    universal_surface = (
        f"forall p n k C. ({prime('p',tag='lmd_universal_prime')}) -> "
        f"({_choose_relation_term('n','k','C',tag='lmd_universal_input',variables=('p','n','k','C'))}) -> "
        f"exists l. (({_lt('n','l',tag='universal_n_length')}) /\\ "
        f"(({_lt('k','l',tag='universal_k_length')}) /\\ ({package_exists})))"
    )
    unconditional_terminal_script.extend(
        f"specialize hglobal {value}" for value in full_variables
    )
    unconditional_terminal_script.extend(
        (
            "apply hglobal", "exact hprime", "exact hnchain", "exact hkchain",
            "exact hquotientchoose", "exact hdigitchoose", "exact hproduct",
            "exact hstart", "exact hterminal", "exact hnzero", "exact hkzero",
        )
    )
    index_chain = lucas_digit_chain(
        "p", "n", "qb", "qc", "db", "dc", "l", tag="index_chain"
    )
    index_entry = _at("qb", "qc", "i", "q", tag="index_entry")
    predecessor_step = (
        "exists a Q d. "
        f"(({_at('qb','qc','i','a',tag='index_previous')}) /\\ "
        f"(({_at('qb','qc','S i','Q',tag='index_successor')}) /\\ "
        f"(({_at('db','dc','i','d',tag='index_digit')}) /\\ "
        f"((a = p * Q + d) /\\ ({_lt('d','p',tag='index_digit_bound')})))))"
    )
    terminal_chain = lucas_digit_chain(
        "p", "n", "qb", "qc", "db", "dc", "l", tag="zero_terminal_chain"
    )
    terminal_entry = _at("qb", "qc", "l", "q", tag="zero_terminal_entry")
    zero_entry = _at("qb", "qc", "l", "0", tag="zero_terminal_result")
    terminal_script.extend(f"specialize hglobal {value}" for value in full_variables)
    terminal_script.extend(
        (
            f"have hfull : ({full_result})",
            "apply hglobal", "exact hprime", "exact hnchain", "exact hkchain",
            "exact hquotientchoose", "exact hdigitchoose", "exact hproduct",
            "exact hstart", "exact hterminal",
            "rewrite hone at hfull", "specialize one_mul P",
            "rewrite one_mul at hfull", "exact hfull",
        )
    )

    return (
        spec(
            LUCAS_DIGIT_CHAIN_INITIAL_CODE_EXISTS,
            f"forall n. exists qb qc. ({initial})",
            ("beta_prefix_extend",),
            (
                "intro n",
                "specialize beta_prefix_extend 0",
                "specialize beta_prefix_extend 0",
                "specialize beta_prefix_extend 0",
                "specialize beta_prefix_extend n",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "exact beta_prefix_extend_witness_witness_left",
            ),
            "Every natural is the zeroth decoded entry of an actual beta-coded quotient stream.",
        ),
        spec(
            LUCAS_DIGIT_CHAIN_EMPTY,
            f"forall p n qb qc db dc. ({initial}) -> ({empty_chain})",
            (),
            (
                "intro p", "intro n", "intro qb", "intro qc", "intro db", "intro dc",
                "intro hinitial", "split", "exact hinitial",
                "intro i", "intro hi", "exfalso", "cases hi",
                "rewrite PA4 at hi_witness", "apply PA1", "exact hi_witness",
            ),
            "A decoded initial quotient constructively supplies the empty coherent digit chain.",
        ),
        spec(
            LUCAS_DIGIT_CHAIN_EMPTY_EXISTS,
            f"forall p n. exists qb qc db dc. ({empty_chain})",
            (LUCAS_DIGIT_CHAIN_INITIAL_CODE_EXISTS, LUCAS_DIGIT_CHAIN_EMPTY),
            (
                "intro p", "intro n",
                "specialize lucas_digit_chain_initial_code_exists n",
                "cases lucas_digit_chain_initial_code_exists",
                "cases lucas_digit_chain_initial_code_exists_witness",
                "exists x", "exists x1", "exists 0", "exists 0",
                "apply lucas_digit_chain_empty",
                "exact lucas_digit_chain_initial_code_exists_witness_witness",
            ),
            "An actual initial quotient code and arbitrary empty digit code exist for every natural.",
        ),
        spec(
            LUCAS_DIGIT_CHAIN_EXTEND,
            "forall p n qb qc db dc l. ~(p = 0) -> "
            f"({current_chain}) -> exists z t u v. ({next_chain})",
            (
                "beta_at_exists",
                "division_remainder_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
                "zero_add",
                "lt_of_lt_of_le",
                "le_succ_self",
                "succ_le_succ",
            ),
            (
                "intro p", "intro n", "intro qb", "intro qc", "intro db", "intro dc", "intro l",
                "intro hnonzero", "intro hchain", "cases hchain",
                f"have hlast : exists q. ({_at('qb', 'qc', 'l', 'q', tag='last_old')})",
                "specialize beta_at_exists qb", "specialize beta_at_exists qc",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hlast",
                "have hdivision : exists Q d. "
                f"((x = p * Q + d) /\\ ({_lt('d', 'p', tag='new_digit_bound')}))",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists x",
                "apply division_remainder_exists", "exact hnonzero",
                "cases hdivision", "cases hdivision_witness", "cases hdivision_witness_witness",
                f"have hqextend : {quotient_extension}",
                "specialize beta_prefix_extend (S l)",
                "specialize beta_prefix_extend qb", "specialize beta_prefix_extend qc",
                "specialize beta_prefix_extend x1", "exact beta_prefix_extend",
                "cases hqextend", "cases hqextend_witness", "cases hqextend_witness_witness",
                f"have hdextend : {digit_extension}",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend db", "specialize beta_prefix_extend dc",
                "specialize beta_prefix_extend x2", "exact beta_prefix_extend",
                "cases hdextend", "cases hdextend_witness", "cases hdextend_witness_witness",
                "exists x3", "exists x4", "exists x5", "exists x6", "split",
                "specialize hqextend_witness_witness_right 0",
                "specialize hqextend_witness_witness_right n",
                "apply hqextend_witness_witness_right",
                "exists l", "simp", "exact hchain_left",
                "intro i", "intro hi",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "rewrite hsplit_left", "rewrite hsplit_left", "rewrite hsplit_left",
                "rewrite hsplit_left", "rewrite hsplit_left", "rewrite hsplit_left",
                "exists x", "exists x1", "exists x2", "split",
                "specialize hqextend_witness_witness_right l",
                "specialize hqextend_witness_witness_right x",
                "apply hqextend_witness_witness_right",
                "exists 0", "apply zero_add", "exact hlast_witness", "split",
                "exact hqextend_witness_witness_left", "split",
                "exact hdextend_witness_witness_left", "split",
                "exact hdivision_witness_witness_left", "exact hdivision_witness_witness_right",
                f"have hprevious : {previous_step}",
                "specialize hchain_right i", "apply hchain_right", "exact hsplit_right",
                "cases hprevious", "cases hprevious_witness", "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_witness",
                "cases hprevious_witness_witness_witness_right",
                "cases hprevious_witness_witness_witness_right_right",
                "cases hprevious_witness_witness_witness_right_right_right",
                "have hipreserve : exists gap. gap + S i = S l",
                "specialize lt_of_lt_of_le i", "specialize lt_of_lt_of_le l",
                "specialize lt_of_lt_of_le (S l)", "apply lt_of_lt_of_le",
                "exact hsplit_right", "specialize le_succ_self l", "exact le_succ_self",
                "have hnextpreserve : exists gap. gap + S (S i) = S l",
                "specialize succ_le_succ (S i)", "specialize succ_le_succ l",
                "apply succ_le_succ", "exact hsplit_right",
                "exists x7", "exists x8", "exists x9", "split",
                "specialize hqextend_witness_witness_right i",
                "specialize hqextend_witness_witness_right x7",
                "apply hqextend_witness_witness_right", "exact hipreserve",
                "exact hprevious_witness_witness_witness_left", "split",
                "specialize hqextend_witness_witness_right (S i)",
                "specialize hqextend_witness_witness_right x8",
                "apply hqextend_witness_witness_right", "exact hnextpreserve",
                "exact hprevious_witness_witness_witness_right_left", "split",
                "specialize hdextend_witness_witness_right i",
                "specialize hdextend_witness_witness_right x9",
                "apply hdextend_witness_witness_right", "exact hsplit_right",
                "exact hprevious_witness_witness_witness_right_right_left", "split",
                "exact hprevious_witness_witness_witness_right_right_right_left",
                "exact hprevious_witness_witness_witness_right_right_right_right",
            ),
            "One constructive quotient division and two beta-prefix extensions append the next genuinely successive digit without disturbing any earlier step.",
        ),
        spec(
            LUCAS_DIGIT_CHAIN_EXISTS,
            f"forall p n l. ~(p = 0) -> exists qb qc db dc. ({general_chain})",
            (LUCAS_DIGIT_CHAIN_EMPTY_EXISTS, LUCAS_DIGIT_CHAIN_EXTEND),
            (
                "intro p", "intro n", "intro l", "induction l",
                "intro hnonzero", "apply lucas_digit_chain_empty_exists",
                "intro hnonzero",
                f"have hprevious : exists qb qc db dc. ({previous_total})",
                "apply IH", "exact hnonzero", "cases hprevious",
                "cases hprevious_witness", "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_witness",
                "specialize lucas_digit_chain_extend p",
                "specialize lucas_digit_chain_extend n",
                "specialize lucas_digit_chain_extend x",
                "specialize lucas_digit_chain_extend x1",
                "specialize lucas_digit_chain_extend x2",
                "specialize lucas_digit_chain_extend x3",
                "specialize lucas_digit_chain_extend l",
                "apply lucas_digit_chain_extend", "exact hnonzero",
                "exact hprevious_witness_witness_witness_witness",
            ),
            "Every nonzero base and natural input possess a coherent successive quotient/digit chain of every finite requested length.",
        ),
        spec(
            LUCAS_PRIME_DIGIT_CHAIN_EXISTS,
            f"forall p n l. ({prime('p', tag='lmd_chain_prime')}) -> "
            f"exists qb qc db dc. ({general_chain})",
            ("prime_nonzero", LUCAS_DIGIT_CHAIN_EXISTS),
            (
                "intro p", "intro n", "intro l", "intro hprime",
                "specialize lucas_digit_chain_exists p",
                "specialize lucas_digit_chain_exists n",
                "specialize lucas_digit_chain_exists l",
                "apply lucas_digit_chain_exists", "intro hzero",
                "specialize prime_nonzero p", "apply prime_nonzero",
                "exact hprime", "exact hzero",
            ),
            "Every prime modulus admits arbitrarily long coherent constructive beta-coded base-p digit streams.",
        ),
        spec(
            LUCAS_DIGIT_CHAIN_INITIAL_VALUE,
            f"forall p n qb qc db dc l. ({general_chain}) -> ({initial})",
            (),
            (
                "intro p", "intro n", "intro qb", "intro qc", "intro db", "intro dc",
                "intro l", "intro hchain", "cases hchain", "exact hchain_left",
            ),
            "The zeroth quotient of every coherent beta-coded digit trace is exactly its original natural input.",
        ),
        spec(
            LUCAS_DIGIT_CHAIN_STEP_EXISTS,
            f"forall p n qb qc db dc l i. ({general_chain}) -> "
            f"({step_bound}) -> ({step_result})",
            (),
            (
                "intro p", "intro n", "intro qb", "intro qc", "intro db", "intro dc",
                "intro l", "intro i", "intro hchain", "intro hi", "cases hchain",
                "specialize hchain_right i", "apply hchain_right", "exact hi",
            ),
            "Every position below an arbitrary finite chain length exposes its actual consecutive quotients and bounded base-p digit.",
        ),
        spec(
            LUCAS_MODULAR_BACKWARD_PRODUCT_FOLD,
            f"forall l p b c z t n k P. ({modular_product}) -> "
            f"({modular_start}) -> ({modular_terminal}) -> "
            f"({modular_trace}) -> ({modular_result})",
            (
                "beta_product_zero",
                "beta_at_unique",
                "mul_one",
                "mod_eq_refl",
                "beta_product_succ_decompose",
                "beta_at_exists",
                "lt_of_lt_of_le",
                "le_succ_self",
                "zero_add",
                "mod_eq_mul_right",
                "mod_eq_trans",
                "mul_assoc",
                "mul_comm",
            ),
            (
                "intro l", "induction l",
                "intro p", "intro b", "intro c", "intro z", "intro t",
                "intro n", "intro k", "intro P", "intro hproduct",
                "intro hstart", "intro hterminal", "intro htrace",
                "have hone : P = 1",
                "specialize beta_product_zero b", "specialize beta_product_zero c",
                "specialize beta_product_zero P", "apply beta_product_zero",
                "exact hproduct",
                "have hequal : n = k",
                "specialize beta_at_unique z", "specialize beta_at_unique t",
                "specialize beta_at_unique 0", "specialize beta_at_unique n",
                "specialize beta_at_unique k", "apply beta_at_unique",
                "exact hstart", "exact hterminal",
                "have hright : k * P = n",
                "rewrite hone", "trans k", "apply mul_one", "symm", "exact hequal",
                "rewrite hright", "specialize mod_eq_refl p",
                "specialize mod_eq_refl n", "exact mod_eq_refl",
                "intro p", "intro b", "intro c", "intro z", "intro t",
                "intro n", "intro k", "intro P", "intro hproduct",
                "intro hstart", "intro hterminal", "intro htrace",
                f"have hdecomposition : {modular_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose P",
                "apply beta_product_succ_decompose", "exact hproduct",
                "cases hdecomposition", "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                f"have hmiddle : exists q. ({_at('z', 't', 'l', 'q', tag='fold_middle')})",
                "specialize beta_at_exists z", "specialize beta_at_exists t",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hmiddle",
                f"have hrestricted : {restricted_trace}",
                "intro i", "intro A", "intro K", "intro D", "intro hi",
                "intro hA", "intro hK", "intro hD",
                "specialize htrace i", "specialize htrace A",
                "specialize htrace K", "specialize htrace D", "apply htrace",
                "specialize lt_of_lt_of_le i", "specialize lt_of_lt_of_le l",
                "specialize lt_of_lt_of_le (S l)", "apply lt_of_lt_of_le",
                "exact hi", "specialize le_succ_self l", "exact le_succ_self",
                "exact hA", "exact hK", "exact hD",
                f"have hbefore : ({_mod_equal('p', 'n', 'x2 * x1', tag='fold_before')})",
                "specialize IH p", "specialize IH b", "specialize IH c",
                "specialize IH z", "specialize IH t", "specialize IH n",
                "specialize IH x2", "specialize IH x1", "apply IH",
                "exact hdecomposition_witness_witness_right_left",
                "exact hstart", "exact hmiddle_witness", "exact hrestricted",
                f"have hlast : ({_mod_equal('p', 'x2', 'k * x', tag='fold_last')})",
                "specialize htrace l", "specialize htrace x2",
                "specialize htrace k", "specialize htrace x", "apply htrace",
                "exists 0", "apply zero_add", "exact hmiddle_witness",
                "exact hterminal", "exact hdecomposition_witness_witness_left",
                f"have hscaled : ({_mod_equal('p', 'x2 * x1', '(k * x) * x1', tag='fold_scaled')})",
                "specialize mod_eq_mul_right p", "specialize mod_eq_mul_right x2",
                "specialize mod_eq_mul_right (k * x)",
                "specialize mod_eq_mul_right x1", "apply mod_eq_mul_right", "exact hlast",
                f"have hcombined : ({_mod_equal('p', 'n', '(k * x) * x1', tag='fold_combined')})",
                "specialize mod_eq_trans p", "specialize mod_eq_trans n",
                "specialize mod_eq_trans (x2 * x1)",
                "specialize mod_eq_trans ((k * x) * x1)", "apply mod_eq_trans",
                "exact hbefore", "exact hscaled",
                "have htarget : (k * x) * x1 = k * P",
                "trans k * (x * x1)", "apply mul_assoc",
                "trans k * (x1 * x)", "congr", "refl", "apply mul_comm",
                "rewrite hdecomposition_witness_witness_right_right", "refl",
                "rewrite <- htarget", "exact hcombined",
            ),
            "Any beta-coded chain of pointwise backward modular recurrences folds into the exact terminal value times the entire beta-coded finite product.",
        ),
        spec(
            LUCAS_CHOOSE_PREFIX_EMPTY,
            f"forall qb qc db dc. exists z t. ({choose_empty})",
            (),
            (
                "intro qb", "intro qc", "intro db", "intro dc",
                "exists 0", "exists 0", "intro i", "intro hi", "exfalso",
                "cases hi", "rewrite PA4 at hi_witness", "apply PA1", "exact hi_witness",
            ),
            "Any pair of beta-coded source streams has a constructively empty relational-Choose coefficient prefix.",
        ),
        spec(
            LUCAS_CHOOSE_PREFIX_EXTEND,
            f"forall qb qc db dc z t l. ({choose_before}) -> "
            f"exists u v. ({choose_after})",
            (
                "beta_at_exists",
                "choose_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro qb", "intro qc", "intro db", "intro dc",
                "intro z", "intro t", "intro l", "intro hprefix",
                f"have hupper : exists a. ({_at('qb', 'qc', 'l', 'a', tag='choose_last_upper')})",
                "specialize beta_at_exists qb", "specialize beta_at_exists qc",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hupper",
                f"have hlower : exists b. ({_at('db', 'dc', 'l', 'b', tag='choose_last_lower')})",
                "specialize beta_at_exists db", "specialize beta_at_exists dc",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hlower",
                "have hchoose : exists C. "
                f"({_choose_relation_term('x','x1','C',tag='lmd_last_choose',variables=('x','x1','C'))})",
                "specialize choose_exists x", "specialize choose_exists x1",
                "exact choose_exists", "cases hchoose",
                f"have hextend : {choose_extended_code}",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend z",
                "specialize beta_prefix_extend t", "specialize beta_prefix_extend x2",
                "exact beta_prefix_extend", "cases hextend", "cases hextend_witness",
                "cases hextend_witness_witness", "exists x3", "exists x4",
                "intro i", "intro hi", "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "rewrite hsplit_left", "rewrite hsplit_left", "rewrite hsplit_left",
                "rewrite hsplit_left", "rewrite hsplit_left", "rewrite hsplit_left",
                "exists x", "exists x1", "exists x2", "split", "exact hupper_witness",
                "split", "exact hlower_witness", "split",
                "exact hextend_witness_witness_left", "exact hchoose_witness",
                f"have hold : {choose_old_entry}",
                "specialize hprefix i", "apply hprefix", "exact hsplit_right",
                "cases hold", "cases hold_witness", "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "cases hold_witness_witness_witness_right_right",
                "exists x5", "exists x6", "exists x7", "split",
                "exact hold_witness_witness_witness_left", "split",
                "exact hold_witness_witness_witness_right_left", "split",
                "specialize hextend_witness_witness_right i",
                "specialize hextend_witness_witness_right x7",
                "apply hextend_witness_witness_right", "exact hsplit_right",
                "exact hold_witness_witness_witness_right_right_left",
                "exact hold_witness_witness_witness_right_right_right",
            ),
            "Beta-prefix extension and relational binomial totality append the exact coefficient for the next two decoded source entries.",
        ),
        spec(
            LUCAS_CHOOSE_PREFIX_EXISTS,
            f"forall qb qc db dc l. exists z t. ({choose_total})",
            (LUCAS_CHOOSE_PREFIX_EMPTY, LUCAS_CHOOSE_PREFIX_EXTEND),
            (
                "intro qb", "intro qc", "intro db", "intro dc", "intro l", "induction l",
                "apply lucas_choose_prefix_empty",
                f"have hprevious : exists z t. ({choose_previous})",
                "exact IH", "cases hprevious", "cases hprevious_witness",
                "specialize lucas_choose_prefix_extend qb",
                "specialize lucas_choose_prefix_extend qc",
                "specialize lucas_choose_prefix_extend db",
                "specialize lucas_choose_prefix_extend dc",
                "specialize lucas_choose_prefix_extend x",
                "specialize lucas_choose_prefix_extend x1",
                "specialize lucas_choose_prefix_extend l",
                "apply lucas_choose_prefix_extend",
                "exact hprevious_witness_witness",
            ),
            "Every pair of beta-coded natural source streams has an actual beta-coded relational-binomial coefficient stream of every finite length.",
        ),
        spec(
            LUCAS_CHOOSE_PREFIX_POINT,
            f"forall qb qc db dc z t l i a b C. ({choose_total}) -> "
            f"({_lt('i', 'l', tag='choose_point_bound')}) -> "
            f"({_at('qb','qc','i','a',tag='choose_point_upper')}) -> "
            f"({_at('db','dc','i','b',tag='choose_point_lower')}) -> "
            f"({_at('z','t','i','C',tag='choose_point_value')}) -> "
            f"({choose_point})",
            ("beta_at_unique",),
            tuple(choose_point_script),
            "Every independently supplied decoded upper index, lower index, and coefficient satisfies the exact relational binomial theorem at that prefix position.",
        ),
        spec(
            LUCAS_MULTIDIGIT_CONGRUENCE_FROM_ONE_STEP,
            f"({one_step}) -> ({full_tail})",
            (
                "lt_of_lt_of_le",
                "le_succ_self",
                "succ_le_succ",
                LUCAS_CHOOSE_PREFIX_POINT,
                LUCAS_MODULAR_BACKWARD_PRODUCT_FOLD,
            ),
            tuple(full_endpoint_script),
            "A universal one-step Lucas prime-block law implies the full arbitrary-length beta-coded digit product congruence with its exact terminal binomial factor.",
        ),
        spec(
            LUCAS_TERMINATING_MULTIDIGIT_THEOREM_FROM_ONE_STEP,
            f"({one_step}) -> ({terminal_tail})",
            (
                LUCAS_CHOOSE_PREFIX_POINT,
                "zero_add",
                "choose_zero",
                LUCAS_MULTIDIGIT_CONGRUENCE_FROM_ONE_STEP,
                "one_mul",
            ),
            tuple(terminal_script),
            "For genuinely terminating quotient chains the full multidigit Lucas congruence is exactly the product of their beta-coded digit binomial coefficients, conditional solely on its explicit one-step law.",
        ),
        spec(
            LUCAS_PRIME_DIGIT_NONZERO_QUOTIENT_STRICT,
            f"forall p n q d. ({prime('p',tag='lmd_strict_prime')}) -> "
            "~(q = 0) -> n = p * q + d -> "
            f"({_lt('q','n',tag='strict_result')})",
            (
                "prime_two_le",
                "succ_le_mul_of_two_le_right",
                "le_add_right",
                "mul_comm",
                "le_trans",
            ),
            (
                "intro p", "intro n", "intro q", "intro d",
                "intro hprime", "intro hnonzero", "intro hdivision",
                "have htwo : exists gap. gap + 2 = p",
                "specialize prime_two_le p", "apply prime_two_le", "exact hprime",
                "have hscaled : exists gap. gap + S q = q * p",
                "specialize succ_le_mul_of_two_le_right q",
                "specialize succ_le_mul_of_two_le_right p",
                "apply succ_le_mul_of_two_le_right", "exact hnonzero", "exact htwo",
                "have hordered : n = q * p + d",
                "trans p * q + d", "exact hdivision", "congr", "apply mul_comm", "refl",
                "have hupper : exists gap. gap + (q * p) = n",
                "specialize le_add_right (q * p)", "specialize le_add_right d",
                "rewrite <- hordered at le_add_right", "exact le_add_right",
                "specialize le_trans (S q)", "specialize le_trans (q * p)",
                "specialize le_trans n", "apply le_trans", "exact hscaled", "exact hupper",
            ),
            "For a prime base every nonzero successive digit quotient is strictly below its predecessor natural.",
        ),
        spec(
            LUCAS_PRIME_DIGIT_CHAIN_NONZERO_INDEX_BOUND,
            f"forall i p n qb qc db dc l q. ({_le('i','l',tag='index_domain')}) -> "
            f"({prime('p',tag='lmd_index_prime')}) -> ({index_chain}) -> "
            f"({index_entry}) -> ~(q = 0) -> "
            f"({_le('q + i','n',tag='index_bound_result')})",
            (
                "beta_at_unique",
                "zero_add",
                "le_succ_self",
                "le_trans",
                LUCAS_PRIME_DIGIT_NONZERO_QUOTIENT_STRICT,
                "add_le_add_right",
                "add_succ_left",
            ),
            (
                "intro i", "induction i",
                "intro p", "intro n", "intro qb", "intro qc", "intro db", "intro dc",
                "intro l", "intro q", "intro hdomain", "intro hprime",
                "intro hchain", "intro hentry", "intro hnonzero", "cases hchain",
                "have hequal : n = q", "specialize beta_at_unique qb",
                "specialize beta_at_unique qc", "specialize beta_at_unique 0",
                "specialize beta_at_unique n", "specialize beta_at_unique q",
                "apply beta_at_unique", "exact hchain_left", "exact hentry",
                "exists 0", "trans q", "trans q + 0", "apply zero_add",
                "apply PA3", "symm", "exact hequal",
                "intro p", "intro n", "intro qb", "intro qc", "intro db", "intro dc",
                "intro l", "intro q", "intro hdomain", "intro hprime",
                "intro hchain", "intro hentry", "intro hnonzero", "cases hchain",
                f"have hprevious : {predecessor_step}",
                "specialize hchain_right i", "apply hchain_right", "exact hdomain",
                "cases hprevious", "cases hprevious_witness",
                "cases hprevious_witness_witness", "cases hprevious_witness_witness_witness",
                "cases hprevious_witness_witness_witness_right",
                "cases hprevious_witness_witness_witness_right_right",
                "cases hprevious_witness_witness_witness_right_right_right",
                "have hquotient : x1 = q",
                "specialize beta_at_unique qb", "specialize beta_at_unique qc",
                "specialize beta_at_unique (S i)", "specialize beta_at_unique x1",
                "specialize beta_at_unique q", "apply beta_at_unique",
                "exact hprevious_witness_witness_witness_right_left", "exact hentry",
                "have hqnonzero : ~(x1 = 0)", "intro hzero", "apply hnonzero",
                "trans x1", "symm", "exact hquotient", "exact hzero",
                "have hstrict : exists gap. gap + S x1 = x",
                "specialize lucas_prime_digit_nonzero_quotient_strict p",
                "specialize lucas_prime_digit_nonzero_quotient_strict x",
                "specialize lucas_prime_digit_nonzero_quotient_strict x1",
                "specialize lucas_prime_digit_nonzero_quotient_strict x2",
                "apply lucas_prime_digit_nonzero_quotient_strict", "exact hprime",
                "exact hqnonzero", "exact hprevious_witness_witness_witness_right_right_right_left",
                "have hprevious_nonzero : ~(x = 0)", "intro hzero", "rewrite hzero at hstrict",
                "cases hstrict", "rewrite PA4 at hstrict_witness", "apply PA1", "exact hstrict_witness",
                "have hprevious_domain : exists gap. gap + i = l",
                "specialize le_trans i", "specialize le_trans (S i)",
                "specialize le_trans l", "apply le_trans",
                "specialize le_succ_self i", "exact le_succ_self", "exact hdomain",
                "have hprevious_bound : exists gap. gap + (x + i) = n",
                "specialize IH p", "specialize IH n", "specialize IH qb",
                "specialize IH qc", "specialize IH db", "specialize IH dc",
                "specialize IH l", "specialize IH x", "apply IH", "exact hprevious_domain",
                "exact hprime", "split", "exact hchain_left", "exact hchain_right",
                "exact hprevious_witness_witness_witness_left", "exact hprevious_nonzero",
                "rewrite hquotient at hstrict",
                "have hadded : exists gap. gap + (S q + i) = x + i",
                "specialize add_le_add_right (S q)", "specialize add_le_add_right x",
                "specialize add_le_add_right i", "apply add_le_add_right", "exact hstrict",
                "have hswap : S q + i = q + S i",
                "trans S (q + i)", "apply add_succ_left", "symm", "apply PA4",
                "rewrite hswap at hadded",
                "specialize le_trans (q + S i)", "specialize le_trans (x + i)",
                "specialize le_trans n", "apply le_trans", "exact hadded", "exact hprevious_bound",
            ),
            "Any nonzero quotient at chain position i obeys the constructive global bound q+i<=n.",
        ),
        spec(
            LUCAS_PRIME_DIGIT_CHAIN_TERMINAL_ZERO,
            f"forall p n qb qc db dc l q. ({prime('p',tag='lmd_terminal_bound_prime')}) -> "
            f"({_lt('n','l',tag='terminal_length')}) -> ({terminal_chain}) -> "
            f"({terminal_entry}) -> q = 0",
            (
                "eq_decidable",
                "le_refl",
                LUCAS_PRIME_DIGIT_CHAIN_NONZERO_INDEX_BOUND,
                "le_add_left",
                "le_trans",
                "lt_not_le",
            ),
            (
                "intro p", "intro n", "intro qb", "intro qc", "intro db", "intro dc",
                "intro l", "intro q", "intro hprime", "intro hlength",
                "intro hchain", "intro hentry",
                "specialize eq_decidable q", "specialize eq_decidable 0",
                "cases eq_decidable", "exact eq_decidable_left", "exfalso",
                "have hbound : exists gap. gap + (q + l) = n",
                "specialize lucas_prime_digit_chain_nonzero_index_bound l",
                "specialize lucas_prime_digit_chain_nonzero_index_bound p",
                "specialize lucas_prime_digit_chain_nonzero_index_bound n",
                "specialize lucas_prime_digit_chain_nonzero_index_bound qb",
                "specialize lucas_prime_digit_chain_nonzero_index_bound qc",
                "specialize lucas_prime_digit_chain_nonzero_index_bound db",
                "specialize lucas_prime_digit_chain_nonzero_index_bound dc",
                "specialize lucas_prime_digit_chain_nonzero_index_bound l",
                "specialize lucas_prime_digit_chain_nonzero_index_bound q",
                "apply lucas_prime_digit_chain_nonzero_index_bound",
                "specialize le_refl l", "exact le_refl", "exact hprime",
                "exact hchain", "exact hentry", "exact eq_decidable_right",
                "have hreverse : exists gap. gap + l = n",
                "specialize le_trans l", "specialize le_trans (q + l)",
                "specialize le_trans n", "apply le_trans",
                "specialize le_add_left l", "specialize le_add_left q", "exact le_add_left",
                "exact hbound", "specialize lt_not_le n", "specialize lt_not_le l",
                "apply lt_not_le", "exact hlength", "exact hreverse",
            ),
            "Every prime-base digit trace longer than its original natural has an actual terminal quotient equal to zero.",
        ),
        spec(
            LUCAS_TERMINATING_PRIME_DIGIT_CHAIN_EXISTS,
            f"forall p n l. ({prime('p',tag='lmd_terminating_prime')}) -> "
            f"({_lt('n','l',tag='terminating_length')}) -> exists qb qc db dc. "
            f"(({terminal_chain}) /\\ ({zero_entry}))",
            (
                LUCAS_PRIME_DIGIT_CHAIN_EXISTS,
                "beta_at_exists",
                LUCAS_PRIME_DIGIT_CHAIN_TERMINAL_ZERO,
            ),
            (
                "intro p", "intro n", "intro l", "intro hprime", "intro hlength",
                "specialize lucas_prime_digit_chain_exists p",
                "specialize lucas_prime_digit_chain_exists n",
                "specialize lucas_prime_digit_chain_exists l",
                "have hcodes : exists qb qc db dc. "
                f"({lucas_digit_chain('p','n','qb','qc','db','dc','l',tag='terminating_codes')})",
                "apply lucas_prime_digit_chain_exists", "exact hprime",
                "cases hcodes", "cases hcodes_witness", "cases hcodes_witness_witness",
                "cases hcodes_witness_witness_witness",
                f"have hterminal : exists q. ({_at('x','x1','l','q',tag='terminating_decoded')})",
                "specialize beta_at_exists x", "specialize beta_at_exists x1",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hterminal",
                "have hzero : x4 = 0",
                "specialize lucas_prime_digit_chain_terminal_zero p",
                "specialize lucas_prime_digit_chain_terminal_zero n",
                "specialize lucas_prime_digit_chain_terminal_zero x",
                "specialize lucas_prime_digit_chain_terminal_zero x1",
                "specialize lucas_prime_digit_chain_terminal_zero x2",
                "specialize lucas_prime_digit_chain_terminal_zero x3",
                "specialize lucas_prime_digit_chain_terminal_zero l",
                "specialize lucas_prime_digit_chain_terminal_zero x4",
                "apply lucas_prime_digit_chain_terminal_zero", "exact hprime", "exact hlength",
                "exact hcodes_witness_witness_witness_witness", "exact hterminal_witness",
                "rewrite hzero at hterminal_witness", "rewrite hzero at hterminal_witness",
                "exists x", "exists x1", "exists x2", "exists x3", "split",
                "exact hcodes_witness_witness_witness_witness", "exact hterminal_witness",
            ),
            "For every prime base and every length strictly above n, a genuinely coherent beta-coded digit chain exists and provably terminates with quotient zero.",
        ),
        spec(
            LUCAS_MULTIDIGIT_CONGRUENCE,
            full_tail,
            (
                "lucas_one_step_division_congruence",
                LUCAS_MULTIDIGIT_CONGRUENCE_FROM_ONE_STEP,
            ),
            tuple(unconditional_full_script),
            "Unconditional full multidigit Lucas congruence: every actual beta-coded coherent digit pair has coefficient congruent to its terminal binomial times the complete digit-binomial product.",
        ),
        spec(
            LUCAS_TERMINATING_MULTIDIGIT_THEOREM,
            terminal_tail,
            (
                "lucas_one_step_division_congruence",
                LUCAS_TERMINATING_MULTIDIGIT_THEOREM_FROM_ONE_STEP,
            ),
            tuple(unconditional_terminal_script),
            "Unconditional constructive Lucas theorem for any two genuinely terminating beta-coded prime-base digit streams: Choose(n,k) is congruent to the entire digitwise binomial product modulo p.",
        ),
        spec(
            LUCAS_THEOREM_FOR_LENGTH,
            f"forall p n k C l. ({prime('p',tag='lmd_length_prime')}) -> "
            f"({_lt('n','l',tag='length_n')}) -> ({_lt('k','l',tag='length_k')}) -> "
            f"({length_choose}) -> ({package_exists})",
            (
                LUCAS_TERMINATING_PRIME_DIGIT_CHAIN_EXISTS,
                LUCAS_CHOOSE_PREFIX_EXISTS,
                "beta_product_exists",
                "beta_at_exists",
                LUCAS_DIGIT_CHAIN_INITIAL_VALUE,
                LUCAS_CHOOSE_PREFIX_POINT,
                "choose_functional",
                LUCAS_TERMINATING_MULTIDIGIT_THEOREM,
            ),
            tuple(length_script),
            "For every prime p, every n,k, and every common length exceeding both, there exist actual terminating coherent digit streams, digit-binomial beta coefficients, their finite product, and the exact Lucas congruence.",
        ),
        spec(
            LUCAS_THEOREM,
            universal_surface,
            (
                "lt_of_le_of_lt",
                "le_add_right",
                "le_add_left",
                "zero_add",
                LUCAS_THEOREM_FOR_LENGTH,
            ),
            (
                "intro p", "intro n", "intro k", "intro C", "intro hprime", "intro hchoose",
                "exists S (n + k)", "split",
                "specialize lt_of_le_of_lt n", "specialize lt_of_le_of_lt (n + k)",
                "specialize lt_of_le_of_lt (S (n + k))", "apply lt_of_le_of_lt",
                "specialize le_add_right n", "specialize le_add_right k", "exact le_add_right",
                "exists 0", "apply zero_add", "split",
                "specialize lt_of_le_of_lt k", "specialize lt_of_le_of_lt (n + k)",
                "specialize lt_of_le_of_lt (S (n + k))", "apply lt_of_le_of_lt",
                "specialize le_add_left k", "specialize le_add_left n", "exact le_add_left",
                "exists 0", "apply zero_add",
                "specialize lucas_theorem_for_length p",
                "specialize lucas_theorem_for_length n",
                "specialize lucas_theorem_for_length k",
                "specialize lucas_theorem_for_length C",
                "specialize lucas_theorem_for_length (S (n + k))",
                "apply lucas_theorem_for_length", "exact hprime",
                "specialize lt_of_le_of_lt n", "specialize lt_of_le_of_lt (n + k)",
                "specialize lt_of_le_of_lt (S (n + k))", "apply lt_of_le_of_lt",
                "specialize le_add_right n", "specialize le_add_right k", "exact le_add_right",
                "exists 0", "apply zero_add",
                "specialize lt_of_le_of_lt k", "specialize lt_of_le_of_lt (n + k)",
                "specialize lt_of_le_of_lt (S (n + k))", "apply lt_of_le_of_lt",
                "specialize le_add_left k", "specialize le_add_left n", "exact le_add_left",
                "exists 0", "apply zero_add", "exact hchoose",
            ),
            "Full constructive Lucas theorem: for every prime p and every relational Choose(n,k,C), explicit terminating beta-coded base-p digit streams and their complete digit-binomial product exist and satisfy C congruent to that product modulo p.",
        ),
    )


__all__ = [
    "LUCAS_DIGIT_CHAIN_EMPTY",
    "LUCAS_DIGIT_CHAIN_EMPTY_EXISTS",
    "LUCAS_DIGIT_CHAIN_EXISTS",
    "LUCAS_DIGIT_CHAIN_EXTEND",
    "LUCAS_DIGIT_CHAIN_INITIAL_CODE_EXISTS",
    "LUCAS_DIGIT_CHAIN_INITIAL_VALUE",
    "LUCAS_DIGIT_CHAIN_STEP_EXISTS",
    "LUCAS_CHOOSE_PREFIX_EMPTY",
    "LUCAS_CHOOSE_PREFIX_EXTEND",
    "LUCAS_CHOOSE_PREFIX_EXISTS",
    "LUCAS_CHOOSE_PREFIX_POINT",
    "LUCAS_PRIME_DIGIT_CHAIN_EXISTS",
    "LUCAS_PRIME_DIGIT_CHAIN_NONZERO_INDEX_BOUND",
    "LUCAS_PRIME_DIGIT_CHAIN_TERMINAL_ZERO",
    "LUCAS_PRIME_DIGIT_NONZERO_QUOTIENT_STRICT",
    "LUCAS_MODULAR_BACKWARD_PRODUCT_FOLD",
    "LUCAS_MULTIDIGIT_CONGRUENCE",
    "LUCAS_MULTIDIGIT_CONGRUENCE_FROM_ONE_STEP",
    "LUCAS_TERMINATING_MULTIDIGIT_THEOREM_FROM_ONE_STEP",
    "LUCAS_TERMINATING_MULTIDIGIT_THEOREM",
    "LUCAS_TERMINATING_PRIME_DIGIT_CHAIN_EXISTS",
    "LUCAS_THEOREM",
    "LUCAS_THEOREM_FOR_LENGTH",
    "lucas_digit_chain",
    "lucas_choose_prefix",
    "lucas_modular_step_trace",
    "lucas_one_step_division_hypothesis",
    "make_lucas_multidigit_candidate_theorems",
]
