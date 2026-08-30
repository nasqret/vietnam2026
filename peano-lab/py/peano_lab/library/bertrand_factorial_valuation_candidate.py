"""Prime-factorial valuation candidates for the Bertrand campaign.

``FactorialVal(p,n,e)`` is authoring notation only.  The helper below expands
it to an existential relational factorial value together with the existing
bounded ``PowerVal`` graph.  Consequently every exported statement remains a
formula of the unchanged first-order Peano language.

This module is deliberately isolated and unregistered.  It consumes the
reviewed relational factorial surface and the exact multiplicativity theorem
from the preceding Bertrand tranche, but grants neither theorem-name
authority nor any new kernel primitive.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_power_valuation_candidate import power_divides, power_valuation
from .fermat_residue_map_candidate import prime
from .finite_factorial_theorems import factorial_relation
from .finite_fold_surface import power_relation


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def factorial_valuation(
    base: str,
    length: str,
    exponent: str,
    *,
    tag: str,
) -> str:
    """Fully expand ``exists F. Factorial(length,F) /\\ PowerVal(base,F,exponent)``."""

    variables = {
        _identifier(base, "valuation base"),
        _identifier(length, "factorial length"),
        _identifier(exponent, "valuation exponent"),
    }
    safe_tag = _identifier(tag, "binder tag")
    value = f"bfv_factorial_{safe_tag}"
    if value in variables:
        raise ValueError("generated factorial-value binder captures an argument")
    factorial = factorial_relation(length, value, tag=f"{safe_tag}_factorial")
    valuation = power_valuation(base, value, exponent, tag=f"{safe_tag}_valuation")
    return f"exists {value}. (({factorial}) /\\ ({valuation}))"


def make_bertrand_factorial_valuation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered prime-factorial valuation tranche."""

    prime_p = prime("p", tag="bfv_prime")

    factorial_n_F = factorial_relation("n", "F", tag="bfv_nonzero")

    valuation_one = power_valuation("p", "one", "e", tag="bfv_one")
    selected_one = power_divides("p", "e", "one", tag="bfv_one_selected")
    successor_prefix = power_relation("p", "x2", "R", tag="bfv_one_prefix")

    total = factorial_valuation("p", "n", "e", tag="bfv_total")
    functional_left = factorial_valuation("p", "n", "e", tag="bfv_functional_left")
    functional_right = factorial_valuation("p", "n", "f", tag="bfv_functional_right")
    zero_value = factorial_valuation("p", "n", "e", tag="bfv_zero")

    predecessor_value = factorial_valuation(
        "p", "n", "e", tag="bfv_successor_predecessor"
    )
    successor_value = factorial_valuation(
        "p", "sn", "g", tag="bfv_successor_value"
    )
    successor_factor_valuation = power_valuation(
        "p", "sn", "f", tag="bfv_successor_factor"
    )

    inversion_predecessor = factorial_valuation(
        "p", "n", "e", tag="bfv_inversion_predecessor"
    )
    inversion_successor = factorial_valuation(
        "p", "sn", "g", tag="bfv_inversion_successor"
    )
    inversion_factor = power_valuation(
        "p", "sn", "f", tag="bfv_inversion_factor"
    )

    return (
        spec(
            "factorial_nonzero",
            f"forall n F. ({factorial_n_F}) -> ~(F = 0)",
            ("factorial_zero", "factorial_succ_decompose", "succ_ne_zero", "mul_ne_zero"),
            (
                "intro n",
                "induction n",
                "intro F",
                "intro hfactorial",
                "have hvalue : F = 1",
                "specialize factorial_zero 0",
                "specialize factorial_zero F",
                "apply factorial_zero",
                "refl",
                "exact hfactorial",
                "intro hzero",
                "specialize succ_ne_zero 0",
                "apply succ_ne_zero",
                "trans F",
                "symm",
                "exact hvalue",
                "exact hzero",
                "intro F",
                "intro hfactorial",
                "have hdecomposition : exists R. "
                f"({factorial_relation('n', 'R', tag='bfv_nonzero_predecessor')}) /\\ "
                "F = R * S n",
                "specialize factorial_succ_decompose n",
                "specialize factorial_succ_decompose (S n)",
                "specialize factorial_succ_decompose F",
                "apply factorial_succ_decompose",
                "refl",
                "exact hfactorial",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "have hpredecessor : ~(x = 0)",
                "intro hpredecessor_zero",
                "specialize IH x",
                "apply IH",
                "exact hdecomposition_witness_left",
                "exact hpredecessor_zero",
                "have hsuccessor : ~(S n = 0)",
                "specialize succ_ne_zero n",
                "exact succ_ne_zero",
                "intro hzero",
                "specialize mul_ne_zero x",
                "specialize mul_ne_zero (S n)",
                "apply mul_ne_zero",
                "exact hpredecessor",
                "exact hsuccessor",
                "trans F",
                "symm",
                "exact hdecomposition_witness_right",
                "exact hzero",
            ),
            "A relational factorial value is never zero.",
        ),
        spec(
            "prime_power_valuation_one_zero",
            f"forall p one e. one = 1 -> ({prime_p}) -> ({valuation_one}) -> e = 0",
            (
                "power_valuation_power_divides",
                "zero_or_succ",
                "pow_successor_decompose",
                "mul_eq_one_components",
            ),
            (
                "intro p",
                "intro one",
                "intro e",
                "intro hone",
                "intro hp",
                "intro hvaluation",
                "cases hp",
                f"have hselected : {selected_one}",
                "specialize power_valuation_power_divides p",
                "specialize power_valuation_power_divides one",
                "specialize power_valuation_power_divides e",
                "apply power_valuation_power_divides",
                "exact hvaluation",
                "cases hselected",
                "cases hselected_witness",
                "cases hselected_witness_right",
                "specialize zero_or_succ e",
                "cases zero_or_succ",
                "exact zero_or_succ_left",
                "cases zero_or_succ_right",
                f"have hstep : exists R. ({successor_prefix}) /\\ x = R * p",
                "specialize pow_successor_decompose p",
                "specialize pow_successor_decompose x2",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose x",
                "apply pow_successor_decompose",
                "exact zero_or_succ_right_witness",
                "exact hselected_witness_left",
                "cases hstep",
                "cases hstep_witness",
                "have hresult_one : x = 1",
                "specialize mul_eq_one_components x",
                "specialize mul_eq_one_components x1",
                "have hresult_parts : x = 1 /\\ x1 = 1",
                "apply mul_eq_one_components",
                "symm",
                "trans one",
                "symm",
                "exact hone",
                "exact hselected_witness_right_witness",
                "cases hresult_parts",
                "exact hresult_parts_left",
                "have hprime_one : p = 1",
                "specialize mul_eq_one_components x3",
                "specialize mul_eq_one_components p",
                "have hstep_parts : x3 = 1 /\\ p = 1",
                "apply mul_eq_one_components",
                "trans x",
                "symm",
                "exact hstep_witness_right",
                "exact hresult_one",
                "cases hstep_parts",
                "exact hstep_parts_right",
                "exfalso",
                "apply hp_left",
                "exact hprime_one",
            ),
            "At a prime base, the bounded valuation of one has exponent zero.",
        ),
        spec(
            "factorial_valuation_exists",
            f"forall p n. exists e. ({total})",
            ("factorial_exists", "power_valuation_exists"),
            (
                "intro p",
                "intro n",
                "have hfactorial : exists F. "
                f"({factorial_relation('n', 'F', tag='bfv_total_witness')})",
                "specialize factorial_exists n",
                "exact factorial_exists",
                "cases hfactorial",
                "have hvaluation : exists e. "
                f"({power_valuation('p', 'x', 'e', tag='bfv_total_graph')})",
                "specialize power_valuation_exists p",
                "specialize power_valuation_exists x",
                "exact power_valuation_exists",
                "cases hvaluation",
                "exists x1",
                "exists x",
                "split",
                "exact hfactorial_witness",
                "exact hvaluation_witness",
            ),
            "Every factorial has a canonical bounded valuation at every base.",
        ),
        spec(
            "factorial_valuation_functional",
            f"forall p n e f. ({functional_left}) -> "
            f"({functional_right}) -> e = f",
            ("factorial_functional", "power_valuation_functional"),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro f",
                "intro he",
                "intro hf",
                "cases he",
                "cases he_witness",
                "cases hf",
                "cases hf_witness",
                "have hfactorial_value : x = x1",
                "specialize factorial_functional n",
                "specialize factorial_functional x",
                "specialize factorial_functional x1",
                "apply factorial_functional",
                "exact he_witness_left",
                "exact hf_witness_left",
                "rewrite <- hfactorial_value at hf_witness_right",
                "rewrite <- hfactorial_value at hf_witness_right",
                "rewrite <- hfactorial_value at hf_witness_right",
                "rewrite <- hfactorial_value at hf_witness_right",
                "specialize power_valuation_functional p",
                "specialize power_valuation_functional x",
                "specialize power_valuation_functional e",
                "specialize power_valuation_functional f",
                "apply power_valuation_functional",
                "exact he_witness_right",
                "exact hf_witness_right",
            ),
            "The factorial valuation exponent is functional at every base.",
        ),
        spec(
            "prime_factorial_valuation_zero",
            f"forall p n e. n = 0 -> ({prime_p}) -> ({zero_value}) -> e = 0",
            ("factorial_zero", "prime_power_valuation_one_zero"),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro hn",
                "intro hp",
                "intro hvaluation",
                "cases hvaluation",
                "cases hvaluation_witness",
                "have hfactorial_value : x = 1",
                "specialize factorial_zero n",
                "specialize factorial_zero x",
                "apply factorial_zero",
                "exact hn",
                "exact hvaluation_witness_left",
                "specialize prime_power_valuation_one_zero p",
                "specialize prime_power_valuation_one_zero x",
                "specialize prime_power_valuation_one_zero e",
                "apply prime_power_valuation_one_zero",
                "exact hfactorial_value",
                "exact hp",
                "exact hvaluation_witness_right",
            ),
            "The prime valuation of zero factorial is zero.",
        ),
        spec(
            "prime_factorial_valuation_succ",
            f"forall p n sn e f g. sn = S n -> ({prime_p}) -> "
            f"({predecessor_value}) -> ({successor_factor_valuation}) -> "
            f"({successor_value}) -> g = e + f",
            (
                "factorial_succ_decompose",
                "factorial_functional",
                "factorial_nonzero",
                "succ_ne_zero",
                "prime_power_valuation_mul",
            ),
            (
                "intro p",
                "intro n",
                "intro sn",
                "intro e",
                "intro f",
                "intro g",
                "intro hsn",
                "intro hp",
                "intro hpredecessor",
                "intro hfactor",
                "intro hsuccessor",
                "cases hpredecessor",
                "cases hpredecessor_witness",
                "cases hsuccessor",
                "cases hsuccessor_witness",
                "have hdecomposition : exists R. "
                f"({factorial_relation('n', 'R', tag='bfv_successor_decomposition')}) /\\ "
                "x1 = R * S n",
                "specialize factorial_succ_decompose n",
                "specialize factorial_succ_decompose sn",
                "specialize factorial_succ_decompose x1",
                "apply factorial_succ_decompose",
                "exact hsn",
                "exact hsuccessor_witness_left",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "have hpredecessor_value : x2 = x",
                "specialize factorial_functional n",
                "specialize factorial_functional x2",
                "specialize factorial_functional x",
                "apply factorial_functional",
                "exact hdecomposition_witness_left",
                "exact hpredecessor_witness_left",
                "have hproduct : x1 = x * sn",
                "trans x2 * S n",
                "exact hdecomposition_witness_right",
                "congr",
                "exact hpredecessor_value",
                "symm",
                "exact hsn",
                "have hpredecessor_nonzero : ~(x = 0)",
                "intro hpredecessor_zero",
                "specialize factorial_nonzero n",
                "specialize factorial_nonzero x",
                "apply factorial_nonzero",
                "exact hpredecessor_witness_left",
                "exact hpredecessor_zero",
                "have hfactor_nonzero : ~(sn = 0)",
                "intro hzero",
                "specialize succ_ne_zero n",
                "apply succ_ne_zero",
                "trans sn",
                "symm",
                "exact hsn",
                "exact hzero",
                "rewrite hproduct at hsuccessor_witness_right",
                "rewrite hproduct at hsuccessor_witness_right",
                "rewrite hproduct at hsuccessor_witness_right",
                "rewrite hproduct at hsuccessor_witness_right",
                "specialize prime_power_valuation_mul p",
                "specialize prime_power_valuation_mul x",
                "specialize prime_power_valuation_mul sn",
                "specialize prime_power_valuation_mul e",
                "specialize prime_power_valuation_mul f",
                "specialize prime_power_valuation_mul g",
                "apply prime_power_valuation_mul",
                "exact hp",
                "exact hpredecessor_nonzero",
                "exact hfactor_nonzero",
                "exact hpredecessor_witness_right",
                "exact hfactor",
                "exact hsuccessor_witness_right",
            ),
            "A successor factorial valuation is the sum of the predecessor and successor-factor valuations.",
        ),
        spec(
            "prime_factorial_valuation_succ_invert",
            f"forall p n sn e g. sn = S n -> ({prime_p}) -> "
            f"({inversion_predecessor}) -> ({inversion_successor}) -> "
            f"exists f. ({inversion_factor}) /\\ g = e + f",
            ("power_valuation_exists", "prime_factorial_valuation_succ"),
            (
                "intro p",
                "intro n",
                "intro sn",
                "intro e",
                "intro g",
                "intro hsn",
                "intro hp",
                "intro hpredecessor",
                "intro hsuccessor",
                "have hfactor : exists f. "
                f"({power_valuation('p', 'sn', 'f', tag='bfv_inversion_graph')})",
                "specialize power_valuation_exists p",
                "specialize power_valuation_exists sn",
                "exact power_valuation_exists",
                "cases hfactor",
                "exists x",
                "split",
                "exact hfactor_witness",
                "specialize prime_factorial_valuation_succ p",
                "specialize prime_factorial_valuation_succ n",
                "specialize prime_factorial_valuation_succ sn",
                "specialize prime_factorial_valuation_succ e",
                "specialize prime_factorial_valuation_succ x",
                "specialize prime_factorial_valuation_succ g",
                "apply prime_factorial_valuation_succ",
                "exact hsn",
                "exact hp",
                "exact hpredecessor",
                "exact hfactor_witness",
                "exact hsuccessor",
            ),
            "A successor factorial valuation exposes the valuation contribution of its new factor.",
        ),
    )


__all__ = [
    "factorial_valuation",
    "make_bertrand_factorial_valuation_candidate_theorems",
]
