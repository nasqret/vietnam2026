"""Actual beta-coded square-and-multiply histories in first-order HA.

Every displayed predicate is only hygienic authoring notation for an expanded
formula in the unchanged language ``0, S, +, *, =``.  In particular the digit
and accumulator histories are genuine independently beta-coded finite
prefixes.  A caller supplies an actual valid zero/one digit code: construction
of canonical binary digits for every exponent, an object-level ``BitLen``
interface, and a logarithmic bound remain separate, unproved milestones.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from typing import Any, Callable, Iterable

from .binary_modular_exponentiation_candidate import (
    _canonical_terms,
    _congruence_terms,
    binary_exponent_split,
    binary_modular_power,
    binary_modular_step,
    binary_modulus_relation,
    canonical_modular_residue,
)
from .finite_fold_surface import (
    _beta_at_term,
    _binders,
    _identifier,
    _lt,
    _variables,
    power_relation,
)
from .polynomial_horner_candidate import _horner_relation_terms


BINARY_DIGIT_PREFIX_EMPTY = "binary_digit_prefix_empty"
BINARY_DIGIT_PREFIX_RESTRICT = "binary_digit_prefix_restrict"
BINARY_DIGIT_PREFIX_TERMINAL_BIT = "binary_digit_prefix_terminal_bit"
BINARY_EXECUTION_INITIAL_STATE = "binary_execution_initial_state"
BINARY_EXECUTION_STEP_DIGIT = "binary_execution_step_digit"
BINARY_EXECUTION_POWER_ZERO = "binary_execution_power_zero"
BINARY_EXECUTION_EVEN_POWER_INVARIANT = "binary_execution_even_power_invariant"
BINARY_EXECUTION_ODD_POWER_INVARIANT = "binary_execution_odd_power_invariant"
BINARY_EXECUTION_STEP_POWER_INVARIANT = "binary_execution_step_power_invariant"
BINARY_EXECUTION_PREFIX_EXTEND = "binary_execution_prefix_extend"
BINARY_EXECUTION_PREFIX_EXISTS = "binary_execution_prefix_exists"
BINARY_MODULAR_EXECUTION_EXISTS = "binary_modular_execution_exists"
BINARY_MODULAR_EXECUTION_EMPTY = "binary_modular_execution_empty"
BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE = (
    "binary_modular_execution_successor_decompose"
)
BINARY_EXECUTION_HORNER_DIGIT_SPLIT = "binary_execution_horner_digit_split"
BINARY_MODULAR_EXECUTION_POWER_CORRECT = "binary_modular_execution_power_correct"
BINARY_MODULAR_EXECUTION_HORNER_EXISTS = "binary_modular_execution_horner_exists"
BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL = (
    "binary_modular_execution_result_functional"
)
BINARY_MODULAR_EXECUTION_RESULT_EXISTS_UNIQUE = (
    "binary_modular_execution_result_exists_unique"
)

MAX_BINARY_EXECUTION_DIGITS = 4_096
MAX_BINARY_EXECUTION_BASE_BITS = 16_384
MAX_BINARY_EXECUTION_MODULUS_BITS = 4_096


class BinaryModularExecutionError(ValueError):
    """A conservative execution formula or bounded concrete history failed."""


def _safe(tag: str) -> str:
    try:
        return _identifier(tag, "binary modular execution binder tag")
    except ValueError as error:
        raise BinaryModularExecutionError(str(error)) from error


def _arguments(*labelled: tuple[str, str]) -> tuple[str, ...]:
    try:
        arguments = _variables(*labelled)
        if len(set(arguments)) != len(arguments):
            raise ValueError("binary execution arguments must be distinct identifiers")
        return arguments
    except ValueError as error:
        raise BinaryModularExecutionError(str(error)) from error


def _digit_prefix_terms(code: str, scale: str, length: str, *, tag: str) -> str:
    safe = _safe(tag)
    arguments = (code, scale, length)
    index, digit = _binders(f"be_{safe}", arguments, ("index", "digit"))
    owned = arguments + (index, digit)
    bound = _lt(index, length, tag=f"be_{safe}_bound", avoid=owned)
    entry = _beta_at_term(
        code, scale, index, digit, tag=f"be_{safe}_digit", avoid=owned
    )
    return f"forall {index} {digit}. ({bound}) -> ({entry}) -> ({digit} = 0 \\/ {digit} = 1)"


def binary_digit_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand a genuine beta-coded finite prefix of zero/one digits."""

    arguments = _arguments(
        (code, "binary digit code"),
        (scale, "binary digit scale"),
        (length, "binary digit length"),
    )
    return _digit_prefix_terms(*arguments, tag=tag)


def _trace_terms(
    digit_code: str,
    digit_scale: str,
    base: str,
    modulus: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    arguments = (
        digit_code,
        digit_scale,
        base,
        modulus,
        length,
        trace_code,
        trace_scale,
    )
    index, digit, previous, current = _binders(
        f"be_{safe}", arguments, ("index", "digit", "previous", "current")
    )
    owned = arguments + (index, digit, previous, current)
    start = _beta_at_term(
        trace_code, trace_scale, "0", "1", tag=f"be_{safe}_start", avoid=owned
    )
    bound = _lt(index, length, tag=f"be_{safe}_bound", avoid=owned)
    source = _beta_at_term(
        digit_code,
        digit_scale,
        index,
        digit,
        tag=f"be_{safe}_source",
        avoid=owned,
    )
    before = _beta_at_term(
        trace_code,
        trace_scale,
        index,
        previous,
        tag=f"be_{safe}_before",
        avoid=owned,
    )
    after = _beta_at_term(
        trace_code,
        trace_scale,
        f"S {index}",
        current,
        tag=f"be_{safe}_after",
        avoid=owned,
    )
    transition = binary_modular_step(
        modulus, previous, base, digit, current, tag=f"be_{safe}_transition"
    )
    return (
        f"(({start}) /\\ forall {index}. ({bound}) -> "
        f"exists {digit} {previous} {current}. "
        f"(({source}) /\\ (({before}) /\\ (({after}) /\\ ({transition})))))"
    )


def binary_execution_trace(
    digit_code: str,
    digit_scale: str,
    base: str,
    modulus: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    """Expand a real beta-coded MSB-first square-and-multiply execution."""

    arguments = _arguments(
        (digit_code, "binary digit code"),
        (digit_scale, "binary digit scale"),
        (base, "square-and-multiply base"),
        (modulus, "square-and-multiply modulus"),
        (length, "binary execution length"),
        (trace_code, "binary execution history code"),
        (trace_scale, "binary execution history scale"),
    )
    return _trace_terms(*arguments, tag=tag)


def _execution_terms(
    digit_code: str,
    digit_scale: str,
    base: str,
    modulus: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    arguments = (digit_code, digit_scale, base, modulus, length, result)
    trace_code, trace_scale = _binders(
        f"be_{safe}", arguments, ("trace_code", "trace_scale")
    )
    owned = arguments + (trace_code, trace_scale)
    trace = _trace_terms(
        digit_code,
        digit_scale,
        base,
        modulus,
        length,
        trace_code,
        trace_scale,
        tag=f"{safe}_trace",
    )
    terminal = _beta_at_term(
        trace_code,
        trace_scale,
        length,
        result,
        tag=f"be_{safe}_terminal",
        avoid=owned,
    )
    return f"exists {trace_code} {trace_scale}. (({trace}) /\\ ({terminal}))"


def binary_modular_execution(
    digit_code: str,
    digit_scale: str,
    base: str,
    modulus: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand exact execution existence and its beta-decoded terminal result."""

    arguments = _arguments(
        (digit_code, "binary digit code"),
        (digit_scale, "binary digit scale"),
        (base, "square-and-multiply base"),
        (modulus, "square-and-multiply modulus"),
        (length, "binary execution length"),
        (result, "binary execution result"),
    )
    return _execution_terms(*arguments, tag=tag)


def binary_execution_power_invariant(
    digit_code: str,
    digit_scale: str,
    base: str,
    modulus: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand a base-two Horner exponent and its canonical modular power."""

    arguments = _arguments(
        (digit_code, "binary digit code"),
        (digit_scale, "binary digit scale"),
        (base, "square-and-multiply base"),
        (modulus, "square-and-multiply modulus"),
        (length, "binary execution length"),
        (result, "binary execution result"),
    )
    safe = _safe(tag)
    (exponent,) = _binders(f"be_{safe}", arguments, ("exponent",))
    horner = _horner_relation_terms(
        digit_code, digit_scale, "2", length, exponent, tag=f"be_{safe}_horner"
    )
    power = binary_modular_power(
        base, exponent, modulus, result, tag=f"be_{safe}_power"
    )
    return f"exists {exponent}. (({horner}) /\\ ({power}))"


def _at(code: str, scale: str, index: str, value: str, *, tag: str) -> str:
    """Use only trusted internally assembled term fragments in proof scripts."""

    return _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"be_{_safe(tag)}",
        avoid=tuple(item for item in (code, scale, index, value) if item.isidentifier()),
    )


def make_binary_modular_execution_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return independently original-kernel-checkable binary execution rows."""

    digits = binary_digit_prefix("b", "c", "l", tag="prefix")
    digits_next = _digit_prefix_terms("b", "c", "S l", tag="prefix_next")
    modulus = binary_modulus_relation("m", tag="execution_guard")
    trace = binary_execution_trace("b", "c", "a", "m", "l", "u", "v", tag="trace")
    trace_next = _trace_terms("b", "c", "a", "m", "S l", "z", "d", tag="trace_next")
    digit_at = _at("b", "c", "l", "x", tag="terminal_digit")
    one_at = _at("z", "d", "0", "1", tag="initial")
    step = binary_modular_step("m", "r", "a", "d", "s", tag="step")
    previous_power = binary_modular_power("a", "h", "m", "r", tag="previous_power")
    current_power = binary_modular_power("a", "e", "m", "s", tag="current_power")
    initial_power = binary_modular_power("a", "e", "m", "r", tag="initial_power")
    square_residue = _canonical_terms(
        "m", "r * r", "s", tag="execution_even", variables=("a", "h", "e", "m", "r", "s")
    )
    product_residue = _canonical_terms(
        "m",
        "(r * r) * a",
        "s",
        tag="execution_odd",
        variables=("a", "h", "e", "m", "r", "s"),
    )
    split = binary_exponent_split("e", "h", "d", tag="execution_split")
    extend_digit = _at("b", "c", "l", "q", tag="extend_digit")
    extend_trace = _trace_terms("b", "c", "a", "m", "S l", "z", "e", tag="extend_trace")
    extend_last = _at("u", "v", "l", "r", tag="extend_last")
    extend_step = binary_modular_step("m", "x", "a", "q", "s", tag="extend_step")
    extend_surface = (
        "exists z e. "
        f"(({_at('z', 'e', 'S l', 'x1', tag='extend_new_terminal')}) /\\ "
        "forall i y. (exists gap. gap + S i = S l) -> "
        f"({_at('u', 'v', 'i', 'y', tag='extend_old_entry')}) -> "
        f"({_at('z', 'e', 'i', 'y', tag='extend_new_entry')}))"
    )
    old_step = (
        "exists digit previous current. "
        f"(({_at('b', 'c', 'i', 'digit', tag='extend_hold_digit')}) /\\ "
        f"(({_at('u', 'v', 'i', 'previous', tag='extend_hold_previous')}) /\\ "
        f"(({_at('u', 'v', 'S i', 'current', tag='extend_hold_current')}) /\\ "
        f"({binary_modular_step('m', 'previous', 'a', 'digit', 'current', tag='extend_hold_step')}))))"
    )
    exists_trace = f"exists u v. ({trace})"
    execution = binary_modular_execution("b", "c", "a", "m", "l", "r", tag="execution")
    execution_empty = _execution_terms("b", "c", "a", "m", "0", "r", tag="empty")
    execution_successor = _execution_terms("b", "c", "a", "m", "S l", "r", tag="successor")
    execution_prefix = binary_modular_execution("b", "c", "a", "m", "l", "s", tag="prefix_result")
    successor_digit = _at("b", "c", "l", "d", tag="successor_digit")
    successor_step = binary_modular_step("m", "s", "a", "d", "r", tag="successor_step")
    successor_last = (
        "exists d s t. "
        f"(({_at('b', 'c', 'l', 'd', tag='successor_last_digit')}) /\\ "
        f"(({_at('x', 'x1', 'l', 's', tag='successor_last_previous')}) /\\ "
        f"(({_at('x', 'x1', 'S l', 't', tag='successor_last_current')}) /\\ "
        f"({binary_modular_step('m', 's', 'a', 'd', 't', tag='successor_last_step')}))))"
    )
    horner_exponent = _horner_relation_terms("b", "c", "2", "l", "e", tag="be_exponent")
    terminal_power = binary_modular_power("a", "e", "m", "r", tag="terminal_power")
    other_execution = binary_modular_execution("b", "c", "a", "m", "l", "s", tag="other_execution")
    horner_last = (
        "exists digit half. "
        f"(({_at('b', 'c', 'l', 'digit', tag='power_horner_digit')}) /\\ "
        f"(({_horner_relation_terms('b', 'c', '2', 'l', 'half', tag='be_power_horner_prefix')}) /\\ "
        "e = half * 2 + digit))"
    )
    execution_last = (
        "exists digit previous. "
        f"(({_at('b', 'c', 'l', 'digit', tag='power_execution_digit')}) /\\ "
        f"(({_execution_terms('b', 'c', 'a', 'm', 'l', 'previous', tag='power_execution_prefix')}) /\\ "
        f"({binary_modular_step('m', 'previous', 'a', 'digit', 'r', tag='power_execution_step')})))"
    )

    return (
        spec(
            BINARY_DIGIT_PREFIX_EMPTY,
            f"forall b c. ({_digit_prefix_terms('b', 'c', '0', tag='empty')})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro b", "intro c", "intro i", "intro d", "intro hi",
                "intro hat", "exfalso", "cases hi", "have hzero : S i = 0",
                "specialize add_eq_zero_right x", "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right", "exact hi_witness",
                "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hzero",
            ),
            "Every empty beta-coded prefix is constructively a valid binary digit sequence.",
        ),
        spec(
            BINARY_DIGIT_PREFIX_RESTRICT,
            f"forall b c l. ({digits_next}) -> ({digits})",
            ("le_succ",),
            (
                "intro b", "intro c", "intro l", "intro hnext",
                "intro i", "intro d", "intro hi", "intro hat",
                "specialize hnext i", "specialize hnext d", "apply hnext",
                "specialize le_succ (S i)", "specialize le_succ l",
                "apply le_succ", "exact hi", "exact hat",
            ),
            "Every valid successor-length binary digit prefix has a valid predecessor prefix.",
        ),
        spec(
            BINARY_DIGIT_PREFIX_TERMINAL_BIT,
            f"forall b c l. ({digits_next}) -> exists x. (({digit_at}) /\\ (x = 0 \\/ x = 1))",
            ("beta_at_exists", "le_refl"),
            (
                "intro b", "intro c", "intro l", "intro hdigits",
                f"have hdigit : exists x. ({digit_at})",
                "specialize beta_at_exists b", "specialize beta_at_exists c",
                "specialize beta_at_exists l", "exact beta_at_exists",
                "cases hdigit", "exists x", "split", "exact hdigit_witness",
                "specialize hdigits l", "specialize hdigits x", "apply hdigits",
                "specialize le_refl (S l)", "exact le_refl", "exact hdigit_witness",
            ),
            "Every nonempty valid beta-coded binary prefix has a genuine final zero-or-one digit.",
        ),
        spec(
            BINARY_EXECUTION_INITIAL_STATE,
            f"exists z d. ({one_at})",
            ("beta_at_self_of_bound",),
            (
                "exists 1", "exists 1", "specialize beta_at_self_of_bound 1",
                "specialize beta_at_self_of_bound 0", "specialize beta_at_self_of_bound 1",
                "apply beta_at_self_of_bound", "exists 0", "simp",
            ),
            "There is a real beta code whose initial square-and-multiply accumulator is one.",
        ),
        spec(
            BINARY_EXECUTION_STEP_DIGIT,
            f"forall m r a d s. ({step}) -> (d = 0 \\/ d = 1)",
            (),
            (
                "intro m", "intro r", "intro a", "intro d", "intro s",
                "intro hstep", "cases hstep", "cases hstep_left", "left",
                "exact hstep_left_left", "cases hstep_right", "right",
                "exact hstep_right_left",
            ),
            "Every actual modular square-and-multiply transition explicitly carries a binary digit.",
        ),
        spec(
            BINARY_EXECUTION_POWER_ZERO,
            f"forall a e m r. ({modulus}) -> e = 0 -> r = 1 -> ({initial_power})",
            ("pow_exists", "pow_zero", "mod_eq_refl"),
            (
                "intro a", "intro e", "intro m", "intro r", "intro hmodulus",
                "intro he", "intro hr",
                f"have hpower : exists n. ({power_relation('a', 'e', 'n', tag='be_initial_power')})",
                "specialize pow_exists a", "specialize pow_exists e", "exact pow_exists",
                "cases hpower", "have hone : x = 1", "specialize pow_zero a",
                "specialize pow_zero e", "specialize pow_zero x", "apply pow_zero",
                "exact he", "exact hpower_witness", "exists x", "split",
                "exact hpower_witness", "split", "rewrite hr", "exact hmodulus",
                "rewrite hone", "rewrite hr", "specialize mod_eq_refl m",
                "specialize mod_eq_refl 1", "exact mod_eq_refl",
            ),
            "For every guarded modulus, the actual initial accumulator one is the canonical zeroth power.",
        ),
        spec(
            BINARY_EXECUTION_EVEN_POWER_INVARIANT,
            f"forall a h e m r s. e = h + h -> ({previous_power}) -> ({square_residue}) -> ({current_power})",
            (
                "pow_exists",
                "binary_exponent_doubled_power",
                "binary_modular_square_congruence",
                "mod_eq_trans",
            ),
            (
                "intro a", "intro h", "intro e", "intro m", "intro r", "intro s",
                "intro he", "intro hprevious", "intro hresidue", "cases hprevious",
                "cases hprevious_witness", "cases hprevious_witness_right",
                "cases hresidue",
                f"have hpower : exists y. ({power_relation('a', 'e', 'y', tag='be_even_full')})",
                "specialize pow_exists a", "specialize pow_exists e", "exact pow_exists",
                "cases hpower", "have hsquare : x1 = x * x",
                "specialize binary_exponent_doubled_power a",
                "specialize binary_exponent_doubled_power h",
                "specialize binary_exponent_doubled_power e",
                "specialize binary_exponent_doubled_power x",
                "specialize binary_exponent_doubled_power x1",
                "apply binary_exponent_doubled_power", "split", "exact he", "split",
                "exact hprevious_witness_left", "exact hpower_witness",
                f"have hsquare_congruence : {_congruence_terms('m', 'x * x', 'r * r', tag='execution_square', variables=('m','x','r','s'))}",
                "specialize binary_modular_square_congruence m",
                "specialize binary_modular_square_congruence x",
                "specialize binary_modular_square_congruence r",
                "apply binary_modular_square_congruence",
                "exact hprevious_witness_right_right",
                f"have htotal : {_congruence_terms('m', 'x * x', 's', tag='execution_square_total', variables=('m','x','r','s'))}",
                "specialize mod_eq_trans m", "specialize mod_eq_trans (x * x)",
                "specialize mod_eq_trans (r * r)", "specialize mod_eq_trans s",
                "apply mod_eq_trans", "exact hsquare_congruence", "exact hresidue_right",
                "exists x1", "split", "exact hpower_witness", "split",
                "exact hresidue_left", "rewrite hsquare", "exact htotal",
            ),
            "One exact binary zero transition preserves the witnessed canonical power invariant.",
        ),
        spec(
            BINARY_EXECUTION_ODD_POWER_INVARIANT,
            f"forall a h e m r s. e = S (h + h) -> ({previous_power}) -> ({product_residue}) -> ({current_power})",
            (
                "pow_exists",
                "binary_exponent_odd_power",
                "binary_modular_square_congruence",
                "mod_eq_refl",
                "mod_eq_mul",
                "mod_eq_trans",
            ),
            (
                "intro a", "intro h", "intro e", "intro m", "intro r", "intro s",
                "intro he", "intro hprevious", "intro hresidue", "cases hprevious",
                "cases hprevious_witness", "cases hprevious_witness_right",
                "cases hresidue",
                f"have hpower : exists y. ({power_relation('a', 'e', 'y', tag='be_odd_full')})",
                "specialize pow_exists a", "specialize pow_exists e", "exact pow_exists",
                "cases hpower", "have hodd : x1 = (x * x) * a",
                "specialize binary_exponent_odd_power a",
                "specialize binary_exponent_odd_power h",
                "specialize binary_exponent_odd_power e",
                "specialize binary_exponent_odd_power x",
                "specialize binary_exponent_odd_power x1",
                "apply binary_exponent_odd_power", "split", "exact he", "split",
                "exact hprevious_witness_left", "exact hpower_witness",
                f"have hsquare : {_congruence_terms('m', 'x * x', 'r * r', tag='execution_odd_square', variables=('m','x','r','s','a'))}",
                "specialize binary_modular_square_congruence m",
                "specialize binary_modular_square_congruence x",
                "specialize binary_modular_square_congruence r",
                "apply binary_modular_square_congruence",
                "exact hprevious_witness_right_right",
                f"have hbase : {_congruence_terms('m', 'a', 'a', tag='execution_odd_base', variables=('m','x','r','s','a'))}",
                "specialize mod_eq_refl m", "specialize mod_eq_refl a", "exact mod_eq_refl",
                f"have hproduct : {_congruence_terms('m', '(x * x) * a', '(r * r) * a', tag='execution_odd_product', variables=('m','x','r','s','a'))}",
                "specialize mod_eq_mul m", "specialize mod_eq_mul (x * x)",
                "specialize mod_eq_mul (r * r)", "specialize mod_eq_mul a",
                "specialize mod_eq_mul a", "apply mod_eq_mul", "exact hsquare", "exact hbase",
                f"have htotal : {_congruence_terms('m', '(x * x) * a', 's', tag='execution_odd_total', variables=('m','x','r','s','a'))}",
                "specialize mod_eq_trans m", "specialize mod_eq_trans ((x * x) * a)",
                "specialize mod_eq_trans ((r * r) * a)", "specialize mod_eq_trans s",
                "apply mod_eq_trans", "exact hproduct", "exact hresidue_right",
                "exists x1", "split", "exact hpower_witness", "split",
                "exact hresidue_left", "rewrite hodd", "exact htotal",
            ),
            "One exact binary one transition preserves the witnessed canonical power invariant.",
        ),
        spec(
            BINARY_EXECUTION_STEP_POWER_INVARIANT,
            f"forall a h e m r d s. ({previous_power}) -> ({split}) -> ({step}) -> ({current_power})",
            (
                BINARY_EXECUTION_EVEN_POWER_INVARIANT,
                BINARY_EXECUTION_ODD_POWER_INVARIANT,
                "succ_ne_zero",
            ),
            (
                "intro a", "intro h", "intro e", "intro m", "intro r", "intro d", "intro s",
                "intro hpower", "intro hsplit", "intro hstep", "cases hsplit",
                "cases hsplit_left", "rewrite hsplit_left_left at hsplit_right",
                "rewrite hsplit_left_left at hstep", "cases hstep", "cases hstep_left",
                "have heven : e = h + h", "trans (h + h) + 0", "exact hsplit_right", "simp",
                f"specialize {BINARY_EXECUTION_EVEN_POWER_INVARIANT} a",
                f"specialize {BINARY_EXECUTION_EVEN_POWER_INVARIANT} h",
                f"specialize {BINARY_EXECUTION_EVEN_POWER_INVARIANT} e",
                f"specialize {BINARY_EXECUTION_EVEN_POWER_INVARIANT} m",
                f"specialize {BINARY_EXECUTION_EVEN_POWER_INVARIANT} r",
                f"specialize {BINARY_EXECUTION_EVEN_POWER_INVARIANT} s",
                f"apply {BINARY_EXECUTION_EVEN_POWER_INVARIANT}", "exact heven",
                "exact hpower", "exact hstep_left_right",
                "cases hstep_right", "rewrite hsplit_left_left at hstep_right_left",
                "exfalso", "specialize succ_ne_zero 0",
                "apply succ_ne_zero", "symm",
                "exact hstep_right_left",
                "rewrite hsplit_left_right at hsplit_right",
                "rewrite hsplit_left_right at hstep", "cases hstep", "cases hstep_left",
                "exfalso",
                "specialize succ_ne_zero 0", "apply succ_ne_zero",
                "exact hstep_left_left",
                "cases hstep_right", "have hodd : e = S (h + h)",
                "trans (h + h) + 1", "exact hsplit_right", "simp",
                f"specialize {BINARY_EXECUTION_ODD_POWER_INVARIANT} a",
                f"specialize {BINARY_EXECUTION_ODD_POWER_INVARIANT} h",
                f"specialize {BINARY_EXECUTION_ODD_POWER_INVARIANT} e",
                f"specialize {BINARY_EXECUTION_ODD_POWER_INVARIANT} m",
                f"specialize {BINARY_EXECUTION_ODD_POWER_INVARIANT} r",
                f"specialize {BINARY_EXECUTION_ODD_POWER_INVARIANT} s",
                f"apply {BINARY_EXECUTION_ODD_POWER_INVARIANT}", "exact hodd",
                "exact hpower", "exact hstep_right_right",
            ),
            "Every actual zero-or-one modular transition preserves the matching binary-prefix power.",
        ),
        spec(
            BINARY_EXECUTION_PREFIX_EXTEND,
            f"forall b c a m l u v q. ({modulus}) -> (q = 0 \\/ q = 1) -> "
            f"({extend_digit}) -> ({trace}) -> exists z e. ({extend_trace})",
            (
                "beta_at_exists",
                "binary_modular_step_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
                "zero_le",
                "succ_le_succ",
                "le_refl",
            ),
            (
                "intro b", "intro c", "intro a", "intro m", "intro l", "intro u",
                "intro v", "intro q", "intro hmodulus", "intro hbit", "intro hdigit",
                "intro htrace", "cases htrace",
                f"have hlast : exists r. ({extend_last})",
                "specialize beta_at_exists u", "specialize beta_at_exists v",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hlast",
                f"have hstep : exists s. ({extend_step})",
                "specialize binary_modular_step_exists m",
                "specialize binary_modular_step_exists x",
                "specialize binary_modular_step_exists a",
                "specialize binary_modular_step_exists q",
                "apply binary_modular_step_exists", "exact hmodulus", "exact hbit",
                "cases hstep", f"have hext : {extend_surface}",
                "specialize beta_prefix_extend (S l)", "specialize beta_prefix_extend u",
                "specialize beta_prefix_extend v", "specialize beta_prefix_extend x1",
                "exact beta_prefix_extend", "cases hext", "cases hext_witness",
                "cases hext_witness_witness", "exists x2", "exists x3", "split",
                "specialize hext_witness_witness_right 0",
                "specialize hext_witness_witness_right 1",
                "apply hext_witness_witness_right",
                "specialize succ_le_succ 0", "specialize succ_le_succ l",
                "apply succ_le_succ", "specialize zero_le l", "exact zero_le",
                "exact htrace_left", "intro i", "intro hi",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "exists q", "exists x", "exists x1", "split",
                "rewrite hsplit_left", "rewrite hsplit_left", "exact hdigit", "split",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "specialize hext_witness_witness_right l",
                "specialize hext_witness_witness_right x",
                "apply hext_witness_witness_right", "specialize le_refl (S l)",
                "exact le_refl", "exact hlast_witness", "split",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "exact hext_witness_witness_left", "exact hstep_witness",
                f"have hold : {old_step}", "specialize htrace_right i",
                "apply htrace_right", "exact hsplit_right", "cases hold",
                "cases hold_witness", "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "cases hold_witness_witness_witness_right_right",
                "exists x4", "exists x5", "exists x6", "split",
                "exact hold_witness_witness_witness_left", "split",
                "specialize hext_witness_witness_right i",
                "specialize hext_witness_witness_right x5",
                "apply hext_witness_witness_right", "exact hi",
                "exact hold_witness_witness_witness_right_left", "split",
                "specialize hext_witness_witness_right (S i)",
                "specialize hext_witness_witness_right x6",
                "apply hext_witness_witness_right",
                "specialize succ_le_succ (S i)", "specialize succ_le_succ l",
                "apply succ_le_succ", "exact hsplit_right",
                "exact hold_witness_witness_witness_right_right_left",
                "exact hold_witness_witness_witness_right_right_right",
            ),
            "Append one genuine beta-coded binary digit and canonical modular transition while preserving every previous execution state.",
        ),
        spec(
            BINARY_EXECUTION_PREFIX_EXISTS,
            f"forall b c a m l. ({modulus}) -> ({digits}) -> {exists_trace}",
            (
                BINARY_EXECUTION_INITIAL_STATE,
                "add_eq_zero_right",
                "succ_ne_zero",
                BINARY_DIGIT_PREFIX_RESTRICT,
                BINARY_DIGIT_PREFIX_TERMINAL_BIT,
                BINARY_EXECUTION_PREFIX_EXTEND,
            ),
            (
                "intro b", "intro c", "intro a", "intro m", "induction l",
                "intro hmodulus", "intro hdigits",
                f"cases {BINARY_EXECUTION_INITIAL_STATE}",
                f"cases {BINARY_EXECUTION_INITIAL_STATE}_witness",
                "exists x", "exists x1", "split",
                f"exact {BINARY_EXECUTION_INITIAL_STATE}_witness_witness",
                "intro i", "intro hi", "exfalso", "cases hi",
                "have hzero : S i = 0", "specialize add_eq_zero_right x2",
                "specialize add_eq_zero_right (S i)", "apply add_eq_zero_right",
                "exact hi_witness", "specialize succ_ne_zero i", "apply succ_ne_zero",
                "exact hzero", "intro hmodulus", "intro hdigits",
                f"have hprefix : ({digits})",
                f"specialize {BINARY_DIGIT_PREFIX_RESTRICT} b",
                f"specialize {BINARY_DIGIT_PREFIX_RESTRICT} c",
                f"specialize {BINARY_DIGIT_PREFIX_RESTRICT} l",
                f"apply {BINARY_DIGIT_PREFIX_RESTRICT}", "exact hdigits",
                f"have htrace : {exists_trace}", "apply IH", "exact hmodulus",
                "exact hprefix", "cases htrace", "cases htrace_witness",
                f"have hlast : exists x. (({digit_at}) /\\ (x = 0 \\/ x = 1))",
                f"specialize {BINARY_DIGIT_PREFIX_TERMINAL_BIT} b",
                f"specialize {BINARY_DIGIT_PREFIX_TERMINAL_BIT} c",
                f"specialize {BINARY_DIGIT_PREFIX_TERMINAL_BIT} l",
                f"apply {BINARY_DIGIT_PREFIX_TERMINAL_BIT}", "exact hdigits",
                "cases hlast", "cases hlast_witness",
                f"specialize {BINARY_EXECUTION_PREFIX_EXTEND} b",
                f"specialize {BINARY_EXECUTION_PREFIX_EXTEND} c",
                f"specialize {BINARY_EXECUTION_PREFIX_EXTEND} a",
                f"specialize {BINARY_EXECUTION_PREFIX_EXTEND} m",
                f"specialize {BINARY_EXECUTION_PREFIX_EXTEND} l",
                f"specialize {BINARY_EXECUTION_PREFIX_EXTEND} x",
                f"specialize {BINARY_EXECUTION_PREFIX_EXTEND} x1",
                f"specialize {BINARY_EXECUTION_PREFIX_EXTEND} x2",
                f"apply {BINARY_EXECUTION_PREFIX_EXTEND}", "exact hmodulus",
                "exact hlast_witness_right", "exact hlast_witness_left",
                "exact htrace_witness_witness",
            ),
            "Natural induction constructs a complete genuine beta-coded square-and-multiply trace for every supplied valid finite binary digit prefix.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_EXISTS,
            f"forall b c a m l. ({modulus}) -> ({digits}) -> exists r. ({execution})",
            (BINARY_EXECUTION_PREFIX_EXISTS, "beta_at_exists"),
            (
                "intro b", "intro c", "intro a", "intro m", "intro l",
                "intro hmodulus", "intro hdigits", f"have htrace : {exists_trace}",
                f"specialize {BINARY_EXECUTION_PREFIX_EXISTS} b",
                f"specialize {BINARY_EXECUTION_PREFIX_EXISTS} c",
                f"specialize {BINARY_EXECUTION_PREFIX_EXISTS} a",
                f"specialize {BINARY_EXECUTION_PREFIX_EXISTS} m",
                f"specialize {BINARY_EXECUTION_PREFIX_EXISTS} l",
                f"apply {BINARY_EXECUTION_PREFIX_EXISTS}", "exact hmodulus",
                "exact hdigits", "cases htrace", "cases htrace_witness",
                f"have hterminal : exists r. ({_at('x', 'x1', 'l', 'r', tag='execution_terminal')})",
                "specialize beta_at_exists x", "specialize beta_at_exists x1",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hterminal",
                "exists x2", "exists x", "exists x1", "split",
                "exact htrace_witness_witness", "exact hterminal_witness",
            ),
            "Every guarded valid coded binary digit prefix has a genuine witnessed modular execution and decoded terminal result.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_EMPTY,
            f"forall b c a m r. ({execution_empty}) -> r = 1",
            ("beta_at_unique",),
            (
                "intro b", "intro c", "intro a", "intro m", "intro r", "intro hexecution",
                "cases hexecution", "cases hexecution_witness",
                "cases hexecution_witness_witness",
                "cases hexecution_witness_witness_left",
                "specialize beta_at_unique x", "specialize beta_at_unique x1",
                "specialize beta_at_unique 0", "specialize beta_at_unique r",
                "specialize beta_at_unique 1", "apply beta_at_unique",
                "exact hexecution_witness_witness_right",
                "exact hexecution_witness_witness_left_left",
            ),
            "The terminal accumulator of any actual empty binary execution is exactly one.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE,
            f"forall b c a m l r. ({execution_successor}) -> "
            f"exists d s. (({successor_digit}) /\\ (({execution_prefix}) /\\ ({successor_step})))",
            ("le_refl", "le_succ", "beta_at_unique"),
            (
                "intro b", "intro c", "intro a", "intro m", "intro l", "intro r",
                "intro hexecution", "cases hexecution", "cases hexecution_witness",
                "cases hexecution_witness_witness",
                "cases hexecution_witness_witness_left", f"have hlast : {successor_last}",
                "specialize hexecution_witness_witness_left_right l",
                "apply hexecution_witness_witness_left_right",
                "specialize le_refl (S l)", "exact le_refl", "cases hlast",
                "cases hlast_witness", "cases hlast_witness_witness",
                "cases hlast_witness_witness_witness",
                "cases hlast_witness_witness_witness_right",
                "cases hlast_witness_witness_witness_right_right",
                "have hterminal : x4 = r", "specialize beta_at_unique x",
                "specialize beta_at_unique x1", "specialize beta_at_unique (S l)",
                "specialize beta_at_unique x4", "specialize beta_at_unique r",
                "apply beta_at_unique",
                "exact hlast_witness_witness_witness_right_right_left",
                "exact hexecution_witness_witness_right", "exists x2", "exists x3",
                "split", "exact hlast_witness_witness_witness_left", "split",
                "exists x", "exists x1", "split", "split",
                "exact hexecution_witness_witness_left_left", "intro i", "intro hi",
                "specialize hexecution_witness_witness_left_right i",
                "apply hexecution_witness_witness_left_right",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ",
                "exact hi", "exact hlast_witness_witness_witness_right_left",
                "rewrite <- hterminal", "rewrite <- hterminal",
                "rewrite <- hterminal", "rewrite <- hterminal",
                "exact hlast_witness_witness_witness_right_right_right",
            ),
            "Every nonempty actual binary execution decomposes into its exact valid predecessor and final modular transition.",
        ),
        spec(
            BINARY_EXECUTION_HORNER_DIGIT_SPLIT,
            f"forall h e d. (d = 0 \\/ d = 1) -> e = h * 2 + d -> ({split})",
            ("mul_comm", "two_mul_eq_add_self"),
            (
                "intro h", "intro e", "intro d", "intro hbit", "intro hexponent",
                "have hdouble : h * 2 = h + h", "trans 2 * h",
                "specialize mul_comm h", "specialize mul_comm 2", "exact mul_comm",
                "specialize two_mul_eq_add_self h", "exact two_mul_eq_add_self",
                "split", "exact hbit", "rewrite <- hdouble", "exact hexponent",
            ),
            "A valid final Horner digit yields the exact exponent decomposition e=2h+d.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_POWER_CORRECT,
            f"forall b c a m l e r. ({modulus}) -> ({horner_exponent}) -> "
            f"({execution}) -> ({terminal_power})",
            (
                "beta_horner_eval_empty",
                BINARY_MODULAR_EXECUTION_EMPTY,
                BINARY_EXECUTION_POWER_ZERO,
                "beta_horner_eval_successor_decompose",
                BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE,
                "beta_at_unique",
                BINARY_EXECUTION_STEP_DIGIT,
                BINARY_EXECUTION_HORNER_DIGIT_SPLIT,
                BINARY_EXECUTION_STEP_POWER_INVARIANT,
            ),
            (
                "intro b", "intro c", "intro a", "intro m", "induction l", "intro e",
                "intro r", "intro hmodulus", "intro hhorner", "intro hexecution",
                "have hzero : e = 0", "specialize beta_horner_eval_empty b",
                "specialize beta_horner_eval_empty c", "specialize beta_horner_eval_empty 2",
                "specialize beta_horner_eval_empty e", "apply beta_horner_eval_empty",
                "exact hhorner", "have hone : r = 1",
                f"specialize {BINARY_MODULAR_EXECUTION_EMPTY} b",
                f"specialize {BINARY_MODULAR_EXECUTION_EMPTY} c",
                f"specialize {BINARY_MODULAR_EXECUTION_EMPTY} a",
                f"specialize {BINARY_MODULAR_EXECUTION_EMPTY} m",
                f"specialize {BINARY_MODULAR_EXECUTION_EMPTY} r",
                f"apply {BINARY_MODULAR_EXECUTION_EMPTY}", "exact hexecution",
                f"specialize {BINARY_EXECUTION_POWER_ZERO} a",
                f"specialize {BINARY_EXECUTION_POWER_ZERO} e",
                f"specialize {BINARY_EXECUTION_POWER_ZERO} m",
                f"specialize {BINARY_EXECUTION_POWER_ZERO} r",
                f"apply {BINARY_EXECUTION_POWER_ZERO}", "exact hmodulus", "exact hzero",
                "exact hone", "intro e", "intro r", "intro hmodulus", "intro hhorner",
                "intro hexecution", f"have hhstep : {horner_last}",
                "specialize beta_horner_eval_successor_decompose b",
                "specialize beta_horner_eval_successor_decompose c",
                "specialize beta_horner_eval_successor_decompose 2",
                "specialize beta_horner_eval_successor_decompose l",
                "specialize beta_horner_eval_successor_decompose e",
                "apply beta_horner_eval_successor_decompose", "exact hhorner",
                "cases hhstep", "cases hhstep_witness", "cases hhstep_witness_witness",
                "cases hhstep_witness_witness_right",
                f"have hxstep : {execution_last}",
                f"specialize {BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE} b",
                f"specialize {BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE} c",
                f"specialize {BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE} a",
                f"specialize {BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE} m",
                f"specialize {BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE} l",
                f"specialize {BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE} r",
                f"apply {BINARY_MODULAR_EXECUTION_SUCCESSOR_DECOMPOSE}", "exact hexecution",
                "cases hxstep", "cases hxstep_witness", "cases hxstep_witness_witness",
                "cases hxstep_witness_witness_right", "have hdigit : x = x2",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique l", "specialize beta_at_unique x",
                "specialize beta_at_unique x2", "apply beta_at_unique",
                "exact hhstep_witness_witness_left", "exact hxstep_witness_witness_left",
                "rewrite hdigit at hhstep_witness_witness_right_right",
                "have hbit : x2 = 0 \\/ x2 = 1",
                f"specialize {BINARY_EXECUTION_STEP_DIGIT} m",
                f"specialize {BINARY_EXECUTION_STEP_DIGIT} x3",
                f"specialize {BINARY_EXECUTION_STEP_DIGIT} a",
                f"specialize {BINARY_EXECUTION_STEP_DIGIT} x2",
                f"specialize {BINARY_EXECUTION_STEP_DIGIT} r",
                f"apply {BINARY_EXECUTION_STEP_DIGIT}",
                "exact hxstep_witness_witness_right_right",
                f"have hsplit : ({binary_exponent_split('e', 'x1', 'x2', tag='correctness_split')})",
                f"specialize {BINARY_EXECUTION_HORNER_DIGIT_SPLIT} x1",
                f"specialize {BINARY_EXECUTION_HORNER_DIGIT_SPLIT} e",
                f"specialize {BINARY_EXECUTION_HORNER_DIGIT_SPLIT} x2",
                f"apply {BINARY_EXECUTION_HORNER_DIGIT_SPLIT}", "exact hbit",
                "exact hhstep_witness_witness_right_right",
                f"have hprevious : ({binary_modular_power('a', 'x1', 'm', 'x3', tag='correctness_previous')})",
                "specialize IH x1", "specialize IH x3", "apply IH", "exact hmodulus",
                "exact hhstep_witness_witness_right_left",
                "exact hxstep_witness_witness_right_left",
                f"specialize {BINARY_EXECUTION_STEP_POWER_INVARIANT} a",
                f"specialize {BINARY_EXECUTION_STEP_POWER_INVARIANT} x1",
                f"specialize {BINARY_EXECUTION_STEP_POWER_INVARIANT} e",
                f"specialize {BINARY_EXECUTION_STEP_POWER_INVARIANT} m",
                f"specialize {BINARY_EXECUTION_STEP_POWER_INVARIANT} x3",
                f"specialize {BINARY_EXECUTION_STEP_POWER_INVARIANT} x2",
                f"specialize {BINARY_EXECUTION_STEP_POWER_INVARIANT} r",
                f"apply {BINARY_EXECUTION_STEP_POWER_INVARIANT}", "exact hprevious",
                "exact hsplit", "exact hxstep_witness_witness_right_right",
            ),
            "Every genuine coded square-and-multiply execution is the canonical modular power of the exact base-two Horner exponent represented by its digit prefix.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_HORNER_EXISTS,
            f"forall b c a m l. ({modulus}) -> ({digits}) -> exists e r. "
            f"(({horner_exponent}) /\\ (({execution}) /\\ ({terminal_power})))",
            (
                "beta_horner_eval_exists",
                BINARY_MODULAR_EXECUTION_EXISTS,
                BINARY_MODULAR_EXECUTION_POWER_CORRECT,
            ),
            (
                "intro b", "intro c", "intro a", "intro m", "intro l", "intro hmodulus",
                "intro hdigits",
                f"have hhorner : exists e. ({horner_exponent})",
                "specialize beta_horner_eval_exists b", "specialize beta_horner_eval_exists c",
                "specialize beta_horner_eval_exists 2", "specialize beta_horner_eval_exists l",
                "exact beta_horner_eval_exists", "cases hhorner",
                f"have hexecution : exists r. ({execution})",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} b",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} c",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} a",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} m",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} l",
                f"apply {BINARY_MODULAR_EXECUTION_EXISTS}", "exact hmodulus", "exact hdigits",
                "cases hexecution", "exists x", "exists x1", "split", "exact hhorner_witness",
                "split", "exact hexecution_witness",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} b",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} c",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} a",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} m",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} l",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} x",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} x1",
                f"apply {BINARY_MODULAR_EXECUTION_POWER_CORRECT}", "exact hmodulus",
                "exact hhorner_witness", "exact hexecution_witness",
            ),
            "Every valid beta-coded binary prefix has a witnessed Horner exponent, complete actual modular execution, and independently proved canonical power invariant.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL,
            f"forall b c a m l r s. ({modulus}) -> ({execution}) -> ({other_execution}) -> r = s",
            (
                "beta_horner_eval_exists",
                BINARY_MODULAR_EXECUTION_POWER_CORRECT,
                "binary_modular_exponentiation_result_functional",
            ),
            (
                "intro b", "intro c", "intro a", "intro m", "intro l", "intro r",
                "intro s", "intro hmodulus", "intro hleft", "intro hright",
                f"have hhorner : exists e. ({horner_exponent})",
                "specialize beta_horner_eval_exists b", "specialize beta_horner_eval_exists c",
                "specialize beta_horner_eval_exists 2", "specialize beta_horner_eval_exists l",
                "exact beta_horner_eval_exists", "cases hhorner",
                f"have hfirst : ({binary_modular_power('a', 'x', 'm', 'r', tag='functional_left')})",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} b",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} c",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} a",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} m",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} l",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} x",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} r",
                f"apply {BINARY_MODULAR_EXECUTION_POWER_CORRECT}", "exact hmodulus",
                "exact hhorner_witness", "exact hleft",
                f"have hsecond : ({binary_modular_power('a', 'x', 'm', 's', tag='functional_right')})",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} b",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} c",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} a",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} m",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} l",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} x",
                f"specialize {BINARY_MODULAR_EXECUTION_POWER_CORRECT} s",
                f"apply {BINARY_MODULAR_EXECUTION_POWER_CORRECT}", "exact hmodulus",
                "exact hhorner_witness", "exact hright",
                "specialize binary_modular_exponentiation_result_functional a",
                "specialize binary_modular_exponentiation_result_functional x",
                "specialize binary_modular_exponentiation_result_functional m",
                "specialize binary_modular_exponentiation_result_functional r",
                "specialize binary_modular_exponentiation_result_functional s",
                "apply binary_modular_exponentiation_result_functional",
                "exact hfirst", "exact hsecond",
            ),
            "Any two complete actual coded square-and-multiply executions of the same guarded binary prefix have identical terminal residues.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_RESULT_EXISTS_UNIQUE,
            f"forall b c a m l. ({modulus}) -> ({digits}) -> exists r. "
            f"(({execution}) /\\ forall s. ({other_execution}) -> r = s)",
            (BINARY_MODULAR_EXECUTION_EXISTS, BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL),
            (
                "intro b", "intro c", "intro a", "intro m", "intro l", "intro hmodulus",
                "intro hdigits", f"have hrun : exists r. ({execution})",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} b",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} c",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} a",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} m",
                f"specialize {BINARY_MODULAR_EXECUTION_EXISTS} l",
                f"apply {BINARY_MODULAR_EXECUTION_EXISTS}", "exact hmodulus", "exact hdigits",
                "cases hrun", "exists x", "split", "exact hrun_witness", "intro s",
                "intro hother",
                f"specialize {BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL} b",
                f"specialize {BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL} c",
                f"specialize {BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL} a",
                f"specialize {BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL} m",
                f"specialize {BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL} l",
                f"specialize {BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL} x",
                f"specialize {BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL} s",
                f"apply {BINARY_MODULAR_EXECUTION_RESULT_FUNCTIONAL}", "exact hmodulus",
                "exact hrun_witness", "exact hother",
            ),
            "Every supplied valid beta-coded binary prefix has exactly one genuine guarded square-and-multiply execution result.",
        ),
    )


@dataclass(frozen=True, slots=True)
class BinaryExecutionStep:
    """A bounded, inspectable host-side transition; never formal proof evidence."""

    index: int
    digit: int
    exponent: int
    previous: int
    result: int


@dataclass(frozen=True, slots=True)
class BinaryExecutionCertificate:
    """Concrete square-and-multiply data; checked theorem authority is separate."""

    base: int
    modulus: int
    digits: tuple[int, ...]
    exponent: int
    result: int
    steps: tuple[BinaryExecutionStep, ...]


def execute_binary_digits(
    base: int,
    modulus: int,
    digits: Iterable[int],
) -> BinaryExecutionCertificate:
    """Construct a strictly bounded concrete MSB-first execution certificate."""

    if type(base) is not int or base < 0 or base.bit_length() > MAX_BINARY_EXECUTION_BASE_BITS:
        raise BinaryModularExecutionError("base must be a bounded nonnegative natural")
    if (
        type(modulus) is not int
        or modulus <= 1
        or modulus.bit_length() > MAX_BINARY_EXECUTION_MODULUS_BITS
    ):
        raise BinaryModularExecutionError("modulus must be a bounded natural greater than one")
    try:
        values = tuple(islice(iter(digits), MAX_BINARY_EXECUTION_DIGITS + 1))
    except (TypeError, ValueError) as error:
        raise BinaryModularExecutionError("digits must be a finite iterable") from error
    if len(values) > MAX_BINARY_EXECUTION_DIGITS:
        raise BinaryModularExecutionError("binary digit prefix exceeds its reviewed resource cap")
    if any(type(value) is not int or value not in (0, 1) for value in values):
        raise BinaryModularExecutionError("every binary digit must be exactly integer zero or one")

    accumulator = 1
    exponent = 0
    steps: list[BinaryExecutionStep] = []
    for index, digit in enumerate(values):
        previous = accumulator
        exponent = exponent * 2 + digit
        accumulator = (previous * previous * (base if digit else 1)) % modulus
        if accumulator != pow(base, exponent, modulus):
            raise BinaryModularExecutionError("concrete prefix-to-power invariant failed")
        steps.append(BinaryExecutionStep(index, digit, exponent, previous, accumulator))
    result = accumulator % modulus
    certificate = BinaryExecutionCertificate(base, modulus, values, exponent, result, tuple(steps))
    verify_binary_execution_certificate(certificate)
    return certificate


def verify_binary_execution_certificate(certificate: BinaryExecutionCertificate) -> None:
    """Audit concrete witnesses, not an object-level proof or admission receipt."""

    if type(certificate) is not BinaryExecutionCertificate:
        raise BinaryModularExecutionError("expected an exact immutable binary execution certificate")
    if (
        type(certificate.base) is not int
        or certificate.base < 0
        or certificate.base.bit_length() > MAX_BINARY_EXECUTION_BASE_BITS
        or type(certificate.modulus) is not int
        or certificate.modulus <= 1
        or certificate.modulus.bit_length() > MAX_BINARY_EXECUTION_MODULUS_BITS
        or type(certificate.digits) is not tuple
        or len(certificate.digits) > MAX_BINARY_EXECUTION_DIGITS
        or type(certificate.steps) is not tuple
        or len(certificate.steps) != len(certificate.digits)
    ):
        raise BinaryModularExecutionError("concrete execution exceeded its reviewed input limits")
    accumulator = 1
    exponent = 0
    for index, (digit, step) in enumerate(zip(certificate.digits, certificate.steps, strict=True)):
        if type(digit) is not int or digit not in (0, 1) or type(step) is not BinaryExecutionStep:
            raise BinaryModularExecutionError("invalid binary digit or concrete transition object")
        exponent = exponent * 2 + digit
        reduced = (accumulator * accumulator * (certificate.base if digit else 1)) % certificate.modulus
        if step != BinaryExecutionStep(index, digit, exponent, accumulator, reduced):
            raise BinaryModularExecutionError("concrete binary transition or power invariant changed")
        accumulator = reduced
    if certificate.exponent != exponent or certificate.result != accumulator % certificate.modulus:
        raise BinaryModularExecutionError("concrete binary execution has a forged terminal state")
    if certificate.result != pow(certificate.base, exponent, certificate.modulus):
        raise BinaryModularExecutionError("concrete binary execution has a forged modular power")
