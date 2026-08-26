"""Constructive gcd transport along actual beta-coded Euclidean histories.

Every readable relation here is an untrusted, hygienic source expansion in
the unchanged first-order Heyting-arithmetic language.  No host calculation,
new predicate constant, axiom, proof rule, or classical principle is used.

Unlike the historical ``EuclidExecution`` pairing, the strengthened anchored
relation explicitly identifies the zeroth beta-history state with its gcd
output.  The corresponding theorems prove that identification from genuine
division-step invariants and injectivity of the existing beta/pair encoding.
The separate campaign BitLen/logarithmic bound still remains unproved.
"""

from __future__ import annotations

from typing import Any, Callable

from .continued_fraction_candidate import (
    _packed_state,
    _pair_term,
    _state_at_term,
    _trace_term,
    continued_fraction_trace,
)
from .euclidean_complexity_candidate import _gcd_term, euclidean_division, euclidean_execution
from .finite_fold_surface import _identifier, _lt
from .ha_canonical_gcd_candidate import is_gcd
from .ha_pair_cell_seed_candidate import cell


EUCLIDEAN_DIVISOR_REMAINDER_TRANSPORT = "euclidean_divisor_remainder_transport"
EUCLIDEAN_DIVISOR_DIVIDEND_TRANSPORT = "euclidean_divisor_dividend_transport"
EUCLIDEAN_COMMON_DIVISOR_FORWARD = "euclidean_common_divisor_forward"
EUCLIDEAN_COMMON_DIVISOR_BACKWARD = "euclidean_common_divisor_backward"
EUCLIDEAN_COMMON_DIVISOR_IFF = "euclidean_common_divisor_iff"
EUCLIDEAN_GCD_STEP_FORWARD = "euclidean_gcd_step_forward"
EUCLIDEAN_GCD_STEP_BACKWARD = "euclidean_gcd_step_backward"
EUCLIDEAN_GCD_STEP_IFF = "euclidean_gcd_step_iff"
EUCLIDEAN_GCD_STEP_OUTPUT_UNIQUE = "euclidean_gcd_step_output_unique"
EUCLIDEAN_GCD_ZERO_TERMINAL_UNIQUE = "euclidean_gcd_zero_terminal_unique"
EUCLIDEAN_EXECUTION_OUTPUT_UNIQUE = "euclidean_execution_output_unique"
EUCLIDEAN_BETA_STATE_FUNCTIONAL = "euclidean_beta_state_functional"
EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT = "euclidean_trace_prefix_gcd_invariant"
EUCLIDEAN_TRACE_INITIAL_STATE_IS_GCD = "euclidean_trace_initial_state_is_gcd"
EUCLIDEAN_TRACE_TERMINAL_GCD_EXISTS = "euclidean_trace_terminal_gcd_exists"
EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED = "euclidean_execution_terminal_identified"
EUCLIDEAN_ANCHORED_EXECUTION_EXISTS = "euclidean_anchored_execution_exists"
EUCLIDEAN_ANCHORED_EXECUTION_LINEAR_BOUND = "euclidean_anchored_execution_linear_bound"
EUCLIDEAN_ANCHORED_EXECUTION_GCD_CORRECT = "euclidean_anchored_execution_gcd_correct"
EUCLIDEAN_ANCHORED_EXECUTION_STATE_CORRECT = "euclidean_anchored_execution_state_correct"


def _variables(*items: tuple[str, str]) -> tuple[str, ...]:
    return tuple(_identifier(value, label) for value, label in items)


def _fresh(tag: str, arguments: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    safe = _identifier(tag, "Euclidean gcd-transport binder tag")
    names = tuple(f"egt_{role}_{safe}" for role in roles)
    if len(set(names)) != len(names) or set(names) & set(arguments):
        raise ValueError("generated Euclidean gcd-transport binder captures an argument")
    return names


def _multiple_term(divisor: str, value: str, *, tag: str, arguments: tuple[str, ...]) -> str:
    (factor,) = _fresh(tag, arguments, "factor")
    return f"exists {factor}. {value} = {divisor} * {factor}"


def euclidean_common_divisor(
    common: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand the exact witnessed common-divisor relation in plain HA."""

    arguments = _variables(
        (common, "common divisor"),
        (left, "left divisible value"),
        (right, "right divisible value"),
    )
    safe_tag = _identifier(tag, "Euclidean gcd-transport binder tag")
    first = _multiple_term(common, left, tag=f"{safe_tag}_left", arguments=arguments)
    second = _multiple_term(common, right, tag=f"{safe_tag}_right", arguments=arguments)
    return f"(({first}) /\\ ({second}))"


def euclidean_state_at(
    history: str,
    scale: str,
    index: str,
    dividend: str,
    divisor: str,
    quotient_list: str,
    *,
    tag: str,
) -> str:
    """Expand the exact doubled-Cantor-packed beta-history state."""

    arguments = _variables(
        (history, "Euclidean beta history"),
        (scale, "Euclidean beta scale"),
        (index, "Euclidean beta index"),
        (dividend, "Euclidean state dividend"),
        (divisor, "Euclidean state divisor"),
        (quotient_list, "Euclidean state quotient list"),
    )
    safe_tag = _identifier(tag, "Euclidean gcd-transport binder tag")
    return _state_at_term(*arguments, tag=f"egt_{safe_tag}", avoid=arguments)


def _anchored_term(
    dividend: str,
    divisor: str,
    result: str,
    length: str,
    *,
    tag: str,
    arguments: tuple[str, ...],
) -> str:
    quotient_list, history, scale = _fresh(tag, arguments, "list", "history", "scale")
    owned = arguments + (quotient_list, history, scale)
    trace = _trace_term(
        dividend,
        divisor,
        quotient_list,
        history,
        scale,
        length,
        tag=f"egt_{tag}_trace",
        arguments=owned,
    )
    initial = _state_at_term(
        history,
        scale,
        "0",
        result,
        "0",
        "0",
        tag=f"egt_{tag}_initial",
        avoid=owned,
    )
    result_relation = _gcd_term(
        result,
        dividend,
        divisor,
        tag=f"egt_{tag}_result",
        arguments=owned,
    )
    return (
        f"exists {quotient_list} {history} {scale}. "
        f"(({trace}) /\\ (({initial}) /\\ ({result_relation})))"
    )


def euclidean_anchored_execution(
    dividend: str,
    divisor: str,
    result: str,
    steps: str,
    *,
    tag: str,
) -> str:
    """Expand a real beta-history whose terminal zero state IS its gcd output."""

    arguments = _variables(
        (dividend, "initial dividend"),
        (divisor, "initial divisor"),
        (result, "terminal Euclidean gcd"),
        (steps, "exact division count"),
    )
    return _anchored_term(*arguments, tag=tag, arguments=arguments)


def _invariant_term(
    history: str,
    scale: str,
    index: str,
    result: str,
    *,
    tag: str,
    arguments: tuple[str, ...],
) -> str:
    left, right, quotient_list = _fresh(tag, arguments, "left", "right", "list")
    owned = arguments + (left, right, quotient_list)
    state = _state_at_term(
        history,
        scale,
        index,
        left,
        right,
        quotient_list,
        tag=f"egt_{tag}_state",
        avoid=owned,
    )
    result_relation = _gcd_term(
        result, left, right, tag=f"egt_{tag}_gcd", arguments=owned
    )
    return f"exists {left} {right} {quotient_list}. (({state}) /\\ ({result_relation}))"


def _transition_term(
    history: str,
    scale: str,
    index: str,
    *,
    tag: str,
    arguments: tuple[str, ...],
) -> str:
    old_a, old_b, old_list, new_a, new_b, new_list, quotient = _fresh(
        tag, arguments, "old_a", "old_b", "old_list", "new_a", "new_b", "new_list", "quotient"
    )
    owned = arguments + (
        old_a,
        old_b,
        old_list,
        new_a,
        new_b,
        new_list,
        quotient,
    )
    previous = _state_at_term(
        history,
        scale,
        index,
        old_a,
        old_b,
        old_list,
        tag=f"egt_{tag}_previous",
        avoid=owned,
    )
    following = _state_at_term(
        history,
        scale,
        f"S {index}",
        new_a,
        new_b,
        new_list,
        tag=f"egt_{tag}_following",
        avoid=owned,
    )
    bound = _lt(old_b, new_b, tag=f"egt_{tag}_remainder", avoid=owned)
    return (
        f"exists {old_a} {old_b} {old_list} {new_a} {new_b} {new_list} {quotient}. "
        f"(({previous}) /\\ (({following}) /\\ ({new_b} = {old_a} /\\ "
        f"({new_a} = {new_b} * {quotient} + {old_b} /\\ "
        f"(({bound}) /\\ ({cell(new_list, quotient, old_list)}))))))"
    )


def make_euclidean_gcd_transport_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build genuine original-kernel Euclidean gcd/history invariant proofs."""

    step = euclidean_division("a", "b", "q", "r", tag="egt_step")
    common_before = euclidean_common_divisor("d", "a", "b", tag="before")
    common_after = euclidean_common_divisor("d", "b", "r", tag="after")
    divides_a = _multiple_term("d", "a", tag="da", arguments=("d", "a"))
    divides_b = _multiple_term("d", "b", tag="db", arguments=("d", "b"))
    divides_r = _multiple_term("d", "r", tag="dr", arguments=("d", "r"))
    gcd_before = is_gcd("g", "a", "b", tag="egt_before")
    gcd_after = is_gcd("g", "b", "r", tag="egt_after")
    other_after = is_gcd("G", "b", "r", tag="egt_other_after")

    state_left = euclidean_state_at("h", "e", "i", "a", "b", "s", tag="left")
    state_right = euclidean_state_at("h", "e", "i", "A", "B", "t", tag="right")
    packed_left = _packed_state("a", "b", "s")
    packed_right = _packed_state("A", "B", "t")
    pair_left = _pair_term("b", "s")
    pair_right = _pair_term("B", "t")

    trace = continued_fraction_trace("a", "b", "s", "h", "e", "l", tag="egt_trace")
    start = _state_at_term(
        "h", "e", "0", "g", "0", "0", tag="egt_start", avoid=("a", "b", "s", "h", "e", "l", "g")
    )
    invariant = _invariant_term(
        "h", "e", "i", "g", tag="at", arguments=("a", "b", "s", "h", "e", "l", "g", "i")
    )
    previous_invariant = _invariant_term(
        "h", "e", "i", "g", tag="previous", arguments=("a", "b", "s", "h", "e", "l", "g", "i")
    )
    transition = _transition_term(
        "h", "e", "i", tag="induction", arguments=("a", "b", "s", "h", "e", "l", "g", "i")
    )
    terminal_gcd = is_gcd("g", "a", "b", tag="egt_terminal")
    execution = euclidean_execution("a", "b", "g", "l", tag="egt_execution")
    other_execution = euclidean_execution("a", "b", "G", "L", tag="egt_other_execution")
    anchored = euclidean_anchored_execution("a", "b", "g", "l", tag="egt_anchored")
    projected_state = _state_at_term(
        "h", "e", "0", "g", "0", "0", tag="egt_projected", avoid=("a", "b", "g", "l", "s", "h", "e")
    )
    projected_trace = continued_fraction_trace(
        "a", "b", "s", "h", "e", "l", tag="egt_projected"
    )

    return (
        spec(
            EUCLIDEAN_DIVISOR_REMAINDER_TRANSPORT,
            f"forall d a b q r. ({step}) -> ({divides_a}) -> ({divides_b}) -> ({divides_r})",
            ("divides_remainder",),
            (
                "intro d", "intro a", "intro b", "intro q", "intro r",
                "intro hstep", "intro ha", "intro hb", "cases hstep",
                "specialize divides_remainder d", "specialize divides_remainder a",
                "specialize divides_remainder b", "specialize divides_remainder q",
                "specialize divides_remainder r", "apply divides_remainder",
                "exact ha", "exact hb", "exact hstep_left",
            ),
            "Every witnessed common divisor of dividend and divisor also divides the exact Euclidean remainder.",
        ),
        spec(
            EUCLIDEAN_DIVISOR_DIVIDEND_TRANSPORT,
            f"forall d a b q r. ({step}) -> ({divides_b}) -> ({divides_r}) -> ({divides_a})",
            ("divides_linear_step",),
            (
                "intro d", "intro a", "intro b", "intro q", "intro r",
                "intro hstep", "intro hb", "intro hr", "cases hstep",
                "rewrite hstep_left", "specialize divides_linear_step d",
                "specialize divides_linear_step b", "specialize divides_linear_step q",
                "specialize divides_linear_step r", "apply divides_linear_step",
                "exact hb", "exact hr",
            ),
            "Every witnessed common divisor of divisor and remainder also divides the exact Euclidean dividend.",
        ),
        spec(
            EUCLIDEAN_COMMON_DIVISOR_FORWARD,
            f"forall d a b q r. ({step}) -> ({common_before}) -> ({common_after})",
            (EUCLIDEAN_DIVISOR_REMAINDER_TRANSPORT,),
            (
                "intro d", "intro a", "intro b", "intro q", "intro r",
                "intro hstep", "intro hcommon", "cases hcommon", "split",
                "exact hcommon_right",
                "specialize euclidean_divisor_remainder_transport d",
                "specialize euclidean_divisor_remainder_transport a",
                "specialize euclidean_divisor_remainder_transport b",
                "specialize euclidean_divisor_remainder_transport q",
                "specialize euclidean_divisor_remainder_transport r",
                "apply euclidean_divisor_remainder_transport", "exact hstep",
                "exact hcommon_left", "exact hcommon_right",
            ),
            "Every constructive common divisor of (a,b) remains a common divisor of the next Euclidean pair (b,r).",
        ),
        spec(
            EUCLIDEAN_COMMON_DIVISOR_BACKWARD,
            f"forall d a b q r. ({step}) -> ({common_after}) -> ({common_before})",
            (EUCLIDEAN_DIVISOR_DIVIDEND_TRANSPORT,),
            (
                "intro d", "intro a", "intro b", "intro q", "intro r",
                "intro hstep", "intro hcommon", "cases hcommon", "split",
                "specialize euclidean_divisor_dividend_transport d",
                "specialize euclidean_divisor_dividend_transport a",
                "specialize euclidean_divisor_dividend_transport b",
                "specialize euclidean_divisor_dividend_transport q",
                "specialize euclidean_divisor_dividend_transport r",
                "apply euclidean_divisor_dividend_transport", "exact hstep",
                "exact hcommon_left", "exact hcommon_right", "exact hcommon_left",
            ),
            "Every constructive common divisor of (b,r) is already a common divisor of the previous Euclidean pair (a,b).",
        ),
        spec(
            EUCLIDEAN_COMMON_DIVISOR_IFF,
            f"forall d a b q r. ({step}) -> "
            f"((({common_before}) -> ({common_after})) /\\ "
            f"(({common_after}) -> ({common_before})))",
            (EUCLIDEAN_COMMON_DIVISOR_FORWARD, EUCLIDEAN_COMMON_DIVISOR_BACKWARD),
            (
                "intro d", "intro a", "intro b", "intro q", "intro r", "intro hstep", "split",
                "intro hcommon", "specialize euclidean_common_divisor_forward d",
                "specialize euclidean_common_divisor_forward a",
                "specialize euclidean_common_divisor_forward b",
                "specialize euclidean_common_divisor_forward q",
                "specialize euclidean_common_divisor_forward r",
                "apply euclidean_common_divisor_forward", "exact hstep", "exact hcommon",
                "intro hcommon", "specialize euclidean_common_divisor_backward d",
                "specialize euclidean_common_divisor_backward a",
                "specialize euclidean_common_divisor_backward b",
                "specialize euclidean_common_divisor_backward q",
                "specialize euclidean_common_divisor_backward r",
                "apply euclidean_common_divisor_backward", "exact hstep", "exact hcommon",
            ),
            "An exact bounded Euclidean division preserves the entire witnessed common-divisor relation in both constructive directions.",
        ),
        spec(
            EUCLIDEAN_GCD_STEP_FORWARD,
            f"forall g a b q r. ({step}) -> ({gcd_after}) -> ({gcd_before})",
            ("is_gcd_euclid_forward",),
            (
                "intro g", "intro a", "intro b", "intro q", "intro r",
                "intro hstep", "intro hg", "cases hstep",
                "specialize is_gcd_euclid_forward g",
                "specialize is_gcd_euclid_forward a",
                "specialize is_gcd_euclid_forward b",
                "specialize is_gcd_euclid_forward q",
                "specialize is_gcd_euclid_forward r",
                "apply is_gcd_euclid_forward", "exact hstep_left", "exact hg",
            ),
            "A relational gcd of the next Euclidean pair is a relational gcd of the previous exact pair.",
        ),
        spec(
            EUCLIDEAN_GCD_STEP_BACKWARD,
            f"forall g a b q r. ({step}) -> ({gcd_before}) -> ({gcd_after})",
            ("is_gcd_euclid_backward",),
            (
                "intro g", "intro a", "intro b", "intro q", "intro r",
                "intro hstep", "intro hg", "cases hstep",
                "specialize is_gcd_euclid_backward g",
                "specialize is_gcd_euclid_backward a",
                "specialize is_gcd_euclid_backward b",
                "specialize is_gcd_euclid_backward q",
                "specialize is_gcd_euclid_backward r",
                "apply is_gcd_euclid_backward", "exact hstep_left", "exact hg",
            ),
            "A relational gcd of the previous exact Euclidean pair is a relational gcd of the next pair.",
        ),
        spec(
            EUCLIDEAN_GCD_STEP_IFF,
            f"forall g a b q r. ({step}) -> "
            f"((({gcd_before}) -> ({gcd_after})) /\\ "
            f"(({gcd_after}) -> ({gcd_before})))",
            (EUCLIDEAN_GCD_STEP_BACKWARD, EUCLIDEAN_GCD_STEP_FORWARD),
            (
                "intro g", "intro a", "intro b", "intro q", "intro r", "intro hstep", "split",
                "intro hg", "specialize euclidean_gcd_step_backward g",
                "specialize euclidean_gcd_step_backward a",
                "specialize euclidean_gcd_step_backward b",
                "specialize euclidean_gcd_step_backward q",
                "specialize euclidean_gcd_step_backward r",
                "apply euclidean_gcd_step_backward", "exact hstep", "exact hg",
                "intro hg", "specialize euclidean_gcd_step_forward g",
                "specialize euclidean_gcd_step_forward a",
                "specialize euclidean_gcd_step_forward b",
                "specialize euclidean_gcd_step_forward q",
                "specialize euclidean_gcd_step_forward r",
                "apply euclidean_gcd_step_forward", "exact hstep", "exact hg",
            ),
            "The full greatest-common-divisor specification is constructively equivalent before and after each exact Euclidean division.",
        ),
        spec(
            EUCLIDEAN_GCD_STEP_OUTPUT_UNIQUE,
            f"forall g G a b q r. ({step}) -> ({gcd_before}) -> ({other_after}) -> g = G",
            (EUCLIDEAN_GCD_STEP_FORWARD, "is_gcd_unique"),
            (
                "intro g", "intro G", "intro a", "intro b", "intro q", "intro r",
                "intro hstep", "intro hg", "intro hG",
                f"have htransport : {is_gcd('G','a','b',tag='egt_transport_other')}",
                "specialize euclidean_gcd_step_forward G",
                "specialize euclidean_gcd_step_forward a",
                "specialize euclidean_gcd_step_forward b",
                "specialize euclidean_gcd_step_forward q",
                "specialize euclidean_gcd_step_forward r",
                "apply euclidean_gcd_step_forward", "exact hstep", "exact hG",
                "specialize is_gcd_unique g", "specialize is_gcd_unique G",
                "specialize is_gcd_unique a", "specialize is_gcd_unique b",
                "apply is_gcd_unique", "exact hg", "exact htransport",
            ),
            "Independently witnessed greatest common divisors before and after one exact Euclidean step are equal.",
        ),
        spec(
            EUCLIDEAN_GCD_ZERO_TERMINAL_UNIQUE,
            "forall g a. "
            f"({_gcd_term('g','a','0',tag='egt_zero',arguments=('g','a'))}) -> g = a",
            ("is_gcd_zero_right", "is_gcd_unique"),
            (
                "intro g", "intro a", "intro hg",
                "specialize is_gcd_unique g", "specialize is_gcd_unique a",
                "specialize is_gcd_unique a", "specialize is_gcd_unique 0",
                "apply is_gcd_unique", "exact hg",
                "specialize is_gcd_zero_right a", "exact is_gcd_zero_right",
            ),
            "Any relational gcd at a zero-remainder terminal state is exactly its nonzero-side dividend, including a=0.",
        ),
        spec(
            EUCLIDEAN_EXECUTION_OUTPUT_UNIQUE,
            f"forall a b g l G L. ({execution}) -> ({other_execution}) -> g = G",
            ("euclidean_execution_gcd_correct", "is_gcd_unique"),
            (
                "intro a", "intro b", "intro g", "intro l", "intro G", "intro L",
                "intro hfirst", "intro hsecond",
                f"have hg : {is_gcd('g','a','b',tag='egt_unique_first')}",
                "specialize euclidean_execution_gcd_correct a",
                "specialize euclidean_execution_gcd_correct b",
                "specialize euclidean_execution_gcd_correct g",
                "specialize euclidean_execution_gcd_correct l",
                "apply euclidean_execution_gcd_correct", "exact hfirst",
                f"have hG : {is_gcd('G','a','b',tag='egt_unique_second')}",
                "cases hsecond", "cases hsecond_witness", "cases hsecond_witness_witness",
                "cases hsecond_witness_witness_witness",
                "exact hsecond_witness_witness_witness_right",
                "specialize is_gcd_unique g", "specialize is_gcd_unique G",
                "specialize is_gcd_unique a", "specialize is_gcd_unique b",
                "apply is_gcd_unique", "exact hg", "exact hG",
            ),
            "Any two Alpha-v21 Euclidean executions for the same input certify the same unique relational gcd output.",
        ),
        spec(
            EUCLIDEAN_BETA_STATE_FUNCTIONAL,
            "forall h e i a b s A B t. "
            f"({state_left}) -> ({state_right}) -> a = A /\\ (b = B /\\ s = t)",
            ("beta_at_unique", "pair_code_injective"),
            (
                "intro h", "intro e", "intro i", "intro a", "intro b", "intro s",
                "intro A", "intro B", "intro t", "intro hleft", "intro hright",
                f"have hpacked : {packed_left} = {packed_right}",
                "specialize beta_at_unique h", "specialize beta_at_unique e",
                "specialize beta_at_unique i", f"specialize beta_at_unique ({packed_left})",
                f"specialize beta_at_unique ({packed_right})", "apply beta_at_unique",
                "exact hleft", "exact hright",
                f"have houter : a = A /\\ {pair_left} = {pair_right}",
                f"specialize pair_code_injective ({packed_left})",
                "specialize pair_code_injective a",
                f"specialize pair_code_injective ({pair_left})",
                "specialize pair_code_injective A",
                f"specialize pair_code_injective ({pair_right})",
                "apply pair_code_injective", "refl", "exact hpacked",
                "cases houter", "split", "exact houter_left",
                f"specialize pair_code_injective ({pair_left})",
                "specialize pair_code_injective b", "specialize pair_code_injective s",
                "specialize pair_code_injective B", "specialize pair_code_injective t",
                "apply pair_code_injective", "refl", "exact houter_right",
            ),
            "Two actual beta-history states at the same index have identical dividend, divisor, and encoded quotient list.",
        ),
        spec(
            EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT,
            "forall a b s h e l g. "
            f"({trace}) -> ({start}) -> forall i. "
            f"(exists gap. gap + i = l) -> ({invariant})",
            (
                EUCLIDEAN_BETA_STATE_FUNCTIONAL,
                "is_gcd_zero_right",
                "lt_to_le",
                "is_gcd_euclid_forward",
            ),
            (
                "intro a", "intro b", "intro s", "intro h", "intro e", "intro l",
                "intro g", "intro htrace", "intro hstart",
                "cases htrace", "cases htrace_witness", "cases htrace_witness_right",
                "intro i", "induction i",
                "intro hbound", "exists g", "exists 0", "exists 0", "split",
                "exact hstart", "specialize is_gcd_zero_right g", "exact is_gcd_zero_right",
                "intro hbound",
                "have hprevbound : exists gap. gap + i = l",
                "specialize lt_to_le i", "specialize lt_to_le l",
                "apply lt_to_le", "exact hbound",
                f"have hprevious : {previous_invariant}",
                "apply IH", "exact hprevbound",
                "cases hprevious", "cases hprevious_witness", "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_witness",
                f"have htransition : {transition}",
                "specialize htrace_witness_right_right i",
                "apply htrace_witness_right_right", "exact hbound",
                "cases htransition", "cases htransition_witness",
                "cases htransition_witness_witness", "cases htransition_witness_witness_witness",
                "cases htransition_witness_witness_witness_witness",
                "cases htransition_witness_witness_witness_witness_witness",
                "cases htransition_witness_witness_witness_witness_witness_witness",
                "cases htransition_witness_witness_witness_witness_witness_witness_witness",
                "cases htransition_witness_witness_witness_witness_witness_witness_witness_right",
                "cases htransition_witness_witness_witness_witness_witness_witness_witness_right_right",
                "cases htransition_witness_witness_witness_witness_witness_witness_witness_right_right_right",
                "have halign : x1 = x4 /\\ (x2 = x5 /\\ x3 = x6)",
                "specialize euclidean_beta_state_functional h",
                "specialize euclidean_beta_state_functional e",
                "specialize euclidean_beta_state_functional i",
                "specialize euclidean_beta_state_functional x1",
                "specialize euclidean_beta_state_functional x2",
                "specialize euclidean_beta_state_functional x3",
                "specialize euclidean_beta_state_functional x4",
                "specialize euclidean_beta_state_functional x5",
                "specialize euclidean_beta_state_functional x6",
                "apply euclidean_beta_state_functional",
                "exact hprevious_witness_witness_witness_left",
                "exact htransition_witness_witness_witness_witness_witness_witness_witness_left",
                "cases halign", "cases halign_right",
                "rewrite halign_left at hprevious_witness_witness_witness_right",
                "rewrite halign_left at hprevious_witness_witness_witness_right",
                "rewrite halign_right_left at hprevious_witness_witness_witness_right",
                "rewrite halign_right_left at hprevious_witness_witness_witness_right",
                "exists x7", "exists x8", "exists x9", "split",
                "exact htransition_witness_witness_witness_witness_witness_witness_witness_right_left",
                "specialize is_gcd_euclid_forward g",
                "specialize is_gcd_euclid_forward x7",
                "specialize is_gcd_euclid_forward x8",
                "specialize is_gcd_euclid_forward x10",
                "specialize is_gcd_euclid_forward x5",
                "apply is_gcd_euclid_forward",
                "exact htransition_witness_witness_witness_witness_witness_witness_witness_right_right_right_left",
                "rewrite htransition_witness_witness_witness_witness_witness_witness_witness_right_right_left",
                "rewrite htransition_witness_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact hprevious_witness_witness_witness_right",
            ),
            "Natural induction over every actual beta-coded Euclidean transition preserves the gcd of the initial zero-divisor state at every history prefix.",
        ),
        spec(
            EUCLIDEAN_TRACE_INITIAL_STATE_IS_GCD,
            f"forall a b s h e l g. ({trace}) -> ({start}) -> ({terminal_gcd})",
            (EUCLIDEAN_TRACE_PREFIX_GCD_INVARIANT, EUCLIDEAN_BETA_STATE_FUNCTIONAL, "le_refl"),
            (
                "intro a", "intro b", "intro s", "intro h", "intro e", "intro l",
                "intro g", "intro htrace", "intro hstart",
                f"have hinvariant : {_invariant_term('h','e','l','g',tag='terminal',arguments=('a','b','s','h','e','l','g'))}",
                "specialize euclidean_trace_prefix_gcd_invariant a",
                "specialize euclidean_trace_prefix_gcd_invariant b",
                "specialize euclidean_trace_prefix_gcd_invariant s",
                "specialize euclidean_trace_prefix_gcd_invariant h",
                "specialize euclidean_trace_prefix_gcd_invariant e",
                "specialize euclidean_trace_prefix_gcd_invariant l",
                "specialize euclidean_trace_prefix_gcd_invariant g",
                f"have hall : forall i. (exists gap. gap + i = l) -> ({_invariant_term('h','e','i','g',tag='terminal_all',arguments=('a','b','s','h','e','l','g','i'))})",
                "apply euclidean_trace_prefix_gcd_invariant", "exact htrace", "exact hstart",
                "specialize hall l", "apply hall",
                "specialize le_refl l", "exact le_refl",
                "cases hinvariant", "cases hinvariant_witness", "cases hinvariant_witness_witness",
                "cases hinvariant_witness_witness_witness",
                "cases htrace", "cases htrace_witness", "cases htrace_witness_right",
                "have halign : x = a /\\ (x1 = b /\\ x2 = s)",
                "specialize euclidean_beta_state_functional h",
                "specialize euclidean_beta_state_functional e",
                "specialize euclidean_beta_state_functional l",
                "specialize euclidean_beta_state_functional x",
                "specialize euclidean_beta_state_functional x1",
                "specialize euclidean_beta_state_functional x2",
                "specialize euclidean_beta_state_functional a",
                "specialize euclidean_beta_state_functional b",
                "specialize euclidean_beta_state_functional s",
                "apply euclidean_beta_state_functional",
                "exact hinvariant_witness_witness_witness_left",
                "exact htrace_witness_right_left",
                "cases halign", "cases halign_right",
                "rewrite halign_left at hinvariant_witness_witness_witness_right",
                "rewrite halign_left at hinvariant_witness_witness_witness_right",
                "rewrite halign_right_left at hinvariant_witness_witness_witness_right",
                "rewrite halign_right_left at hinvariant_witness_witness_witness_right",
                "exact hinvariant_witness_witness_witness_right",
            ),
            "The actual value encoded in the zeroth terminal Euclidean beta-state is a relational gcd of the original terminal input pair.",
        ),
        spec(
            EUCLIDEAN_TRACE_TERMINAL_GCD_EXISTS,
            f"forall a b s h e l. ({trace}) -> exists g. (({start}) /\\ ({terminal_gcd}))",
            (EUCLIDEAN_TRACE_INITIAL_STATE_IS_GCD,),
            (
                "intro a", "intro b", "intro s", "intro h", "intro e", "intro l", "intro htrace",
                f"have hcopy : {trace}", "exact htrace",
                "cases htrace", "cases htrace_witness", "cases htrace_witness_right",
                "exists x", "split", "exact htrace_witness_left",
                "specialize euclidean_trace_initial_state_is_gcd a",
                "specialize euclidean_trace_initial_state_is_gcd b",
                "specialize euclidean_trace_initial_state_is_gcd s",
                "specialize euclidean_trace_initial_state_is_gcd h",
                "specialize euclidean_trace_initial_state_is_gcd e",
                "specialize euclidean_trace_initial_state_is_gcd l",
                "specialize euclidean_trace_initial_state_is_gcd x",
                "apply euclidean_trace_initial_state_is_gcd", "exact hcopy",
                "exact htrace_witness_left",
            ),
            "Every complete actual beta-coded Euclidean history contains a witnessed terminal zero state whose encoded value is the genuine gcd of its inputs.",
        ),
        spec(
            EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED,
            f"forall a b g l. ({execution}) -> "
            f"exists s h e. (({projected_trace}) /\\ ({projected_state}))",
            (EUCLIDEAN_TRACE_TERMINAL_GCD_EXISTS, "is_gcd_unique"),
            (
                "intro a", "intro b", "intro g", "intro l", "intro hexecution",
                "cases hexecution", "cases hexecution_witness", "cases hexecution_witness_witness",
                "cases hexecution_witness_witness_witness",
                "exists x", "exists x1", "exists x2", "split",
                "exact hexecution_witness_witness_witness_left",
                f"have hterminal : exists G. (({_state_at_term('x1','x2','0','G','0','0',tag='egt_identified_terminal',avoid=('a','b','g','l','x','x1','x2','G'))}) /\\ ({is_gcd('G','a','b',tag='egt_identified_terminal')}))",
                "specialize euclidean_trace_terminal_gcd_exists a",
                "specialize euclidean_trace_terminal_gcd_exists b",
                "specialize euclidean_trace_terminal_gcd_exists x",
                "specialize euclidean_trace_terminal_gcd_exists x1",
                "specialize euclidean_trace_terminal_gcd_exists x2",
                "specialize euclidean_trace_terminal_gcd_exists l",
                "apply euclidean_trace_terminal_gcd_exists",
                "exact hexecution_witness_witness_witness_left",
                "cases hterminal", "cases hterminal_witness",
                "have hequal : x3 = g",
                "specialize is_gcd_unique x3", "specialize is_gcd_unique g",
                "specialize is_gcd_unique a", "specialize is_gcd_unique b",
                "apply is_gcd_unique", "exact hterminal_witness_right",
                "exact hexecution_witness_witness_witness_right",
                "rewrite hequal at hterminal_witness_left",
                "rewrite hequal at hterminal_witness_left",
                "rewrite hequal at hterminal_witness_left",
                "rewrite hequal at hterminal_witness_left",
                "exact hterminal_witness_left",
            ),
            "The independently certified output of every Alpha-v21 EuclidExecution is exactly the natural encoded in its actual terminal zero-divisor beta state.",
        ),
        spec(
            EUCLIDEAN_ANCHORED_EXECUTION_EXISTS,
            f"forall a b. exists g l. ({anchored})",
            ("euclidean_execution_exists", EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED),
            (
                "intro a", "intro b", "specialize euclidean_execution_exists a",
                "specialize euclidean_execution_exists b", "cases euclidean_execution_exists",
                "cases euclidean_execution_exists_witness",
                f"have hidentified : exists s h e. (({continued_fraction_trace('a','b','s','h','e','x1',tag='egt_exists_trace')}) /\\ ({_state_at_term('h','e','0','x','0','0',tag='egt_exists_state',avoid=('a','b','x','x1','s','h','e'))}))",
                "specialize euclidean_execution_terminal_identified a",
                "specialize euclidean_execution_terminal_identified b",
                "specialize euclidean_execution_terminal_identified x",
                "specialize euclidean_execution_terminal_identified x1",
                "apply euclidean_execution_terminal_identified",
                "exact euclidean_execution_exists_witness_witness",
                "cases hidentified", "cases hidentified_witness", "cases hidentified_witness_witness",
                "cases hidentified_witness_witness_witness",
                "cases euclidean_execution_exists_witness_witness",
                "cases euclidean_execution_exists_witness_witness_witness",
                "cases euclidean_execution_exists_witness_witness_witness_witness",
                "cases euclidean_execution_exists_witness_witness_witness_witness_witness",
                "exists x", "exists x1", "exists x2", "exists x3", "exists x4",
                "split", "exact hidentified_witness_witness_witness_left", "split",
                "exact hidentified_witness_witness_witness_right",
                "exact euclidean_execution_exists_witness_witness_witness_witness_witness_right",
            ),
            "Every natural input pair has a genuine complete Euclidean beta execution whose actual terminal zero state is its certified gcd output.",
        ),
        spec(
            EUCLIDEAN_ANCHORED_EXECUTION_LINEAR_BOUND,
            f"forall a b. exists g l. (({anchored}) /\\ exists gap. gap + l = b)",
            ("euclidean_gcd_execution_linear_bound", EUCLIDEAN_EXECUTION_TERMINAL_IDENTIFIED),
            (
                "intro a", "intro b", "specialize euclidean_gcd_execution_linear_bound a",
                "specialize euclidean_gcd_execution_linear_bound b",
                "cases euclidean_gcd_execution_linear_bound",
                "cases euclidean_gcd_execution_linear_bound_witness",
                "cases euclidean_gcd_execution_linear_bound_witness_witness",
                f"have hidentified : exists s h e. (({continued_fraction_trace('a','b','s','h','e','x1',tag='egt_linear_trace')}) /\\ ({_state_at_term('h','e','0','x','0','0',tag='egt_linear_state',avoid=('a','b','x','x1','s','h','e'))}))",
                "specialize euclidean_execution_terminal_identified a",
                "specialize euclidean_execution_terminal_identified b",
                "specialize euclidean_execution_terminal_identified x",
                "specialize euclidean_execution_terminal_identified x1",
                "apply euclidean_execution_terminal_identified",
                "exact euclidean_gcd_execution_linear_bound_witness_witness_left",
                "cases hidentified", "cases hidentified_witness", "cases hidentified_witness_witness",
                "cases hidentified_witness_witness_witness",
                "cases euclidean_gcd_execution_linear_bound_witness_witness_left",
                "cases euclidean_gcd_execution_linear_bound_witness_witness_left_witness",
                "cases euclidean_gcd_execution_linear_bound_witness_witness_left_witness_witness",
                "cases euclidean_gcd_execution_linear_bound_witness_witness_left_witness_witness_witness",
                "exists x", "exists x1", "split", "exists x2", "exists x3", "exists x4",
                "split", "exact hidentified_witness_witness_witness_left", "split",
                "exact hidentified_witness_witness_witness_right",
                "exact euclidean_gcd_execution_linear_bound_witness_witness_left_witness_witness_witness_right",
                "exact euclidean_gcd_execution_linear_bound_witness_witness_right",
            ),
            "Every pair has a complete actual beta-coded Euclidean execution whose terminal state is provably its gcd and whose exact step count satisfies steps <= b; the BitLen bound remains open.",
        ),
        spec(
            EUCLIDEAN_ANCHORED_EXECUTION_GCD_CORRECT,
            f"forall a b g l. ({anchored}) -> ({terminal_gcd})",
            (),
            (
                "intro a", "intro b", "intro g", "intro l", "intro hanchored",
                "cases hanchored", "cases hanchored_witness", "cases hanchored_witness_witness",
                "cases hanchored_witness_witness_witness",
                "cases hanchored_witness_witness_witness_right",
                "exact hanchored_witness_witness_witness_right_right",
            ),
            "Every anchored Euclidean execution independently satisfies the full original relational greatest-common-divisor specification.",
        ),
        spec(
            EUCLIDEAN_ANCHORED_EXECUTION_STATE_CORRECT,
            f"forall a b g l. ({anchored}) -> "
            f"exists s h e. (({projected_trace}) /\\ ({projected_state}))",
            (),
            (
                "intro a", "intro b", "intro g", "intro l", "intro hanchored",
                "cases hanchored", "cases hanchored_witness", "cases hanchored_witness_witness",
                "cases hanchored_witness_witness_witness",
                "cases hanchored_witness_witness_witness_right",
                "exists x", "exists x1", "exists x2", "split",
                "exact hanchored_witness_witness_witness_left",
                "exact hanchored_witness_witness_witness_right_left",
            ),
            "Every anchored execution contains an actual complete beta history whose zeroth state encodes precisely the reported gcd value.",
        ),
    )


__all__ = [
    "euclidean_anchored_execution",
    "euclidean_common_divisor",
    "euclidean_state_at",
    "make_euclidean_gcd_transport_candidate_theorems",
]
