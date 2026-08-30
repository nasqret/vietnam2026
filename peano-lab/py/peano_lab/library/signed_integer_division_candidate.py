"""Witnessed floor division of genuine signed integers in unchanged HA.

The pair (positive, negative) represents their integer difference.  A floor
quotient is another such pair, with an actual natural remainder strictly
below the positive divisor.  Canonical outputs reuse the historic SignedDecode
relation, not a second integer encoding or a trusted arithmetic operation.
"""

from __future__ import annotations

from typing import Any, Callable

from ..kernel.terms import Term, parse_term_in_context, pretty_term
from .finite_fold_surface import _identifier
from .ha_signed_decode_candidate import signed_decode


def _context(variables: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(variables, tuple) or not variables:
        raise ValueError("signed-division context must be a nonempty tuple of distinct identifiers")
    checked = tuple(_identifier(value, "signed-division context variable") for value in variables)
    if len(set(checked)) != len(checked):
        raise ValueError("signed-division context variables must be distinct")
    return checked


def _floor_term(
    positive: Term, negative: Term, modulus: Term,
    quotient_positive: Term, quotient_negative: Term, remainder: Term,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Render only genuine parsed PA terms, with a capture-checked gap binder."""
    context = _context(variables)
    gap = "sif_gap_" + _identifier(tag, "signed-division binder tag")
    if gap in context:
        raise ValueError("generated signed-division binder captures an argument")
    values = (positive, negative, modulus, quotient_positive, quotient_negative, remainder)
    sources = tuple(pretty_term(value, list(context)).replace("·", "*") for value in values)
    if any(parse_term_in_context(source, list(context)) != value for source,value in zip(sources,values,strict=True)):
        raise ValueError("signed-division term is not a rigid term in its declared context")
    rendered = tuple("(" + source + ")" for source in sources)
    p, n, m, q, t, r = rendered
    return f"({p} + {m} * {t} = ({n} + {m} * {q}) + {r} /\\ exists {gap}. {gap} + S {r} = {m})"


def signed_integer_floor_relation(
    positive: str, negative: str, modulus: str,
    quotient_positive: str, quotient_negative: str, remainder: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """The exact signed floor equation and strict natural remainder bound."""
    context = _context(variables)
    values = (positive, negative, modulus, quotient_positive, quotient_negative, remainder)
    return _floor_term(*(parse_term_in_context(value, list(context)) for value in values), tag=tag, variables=context)


def _floor(p: str, n: str, m: str, q: str, t: str, r: str, *, tag: str) -> str:
    # Factory-internal arguments below are known context variables.
    return signed_integer_floor_relation(p, n, m, q, t, r, tag=tag, variables=tuple(dict.fromkeys((p,n,m,q,t,r))))


def signed_code_floor_relation(input_code: str, modulus: str, quotient_code: str, remainder: str, *, tag: str) -> str:
    """Canonical signed input/output codes with the very same floor graph."""
    arguments = tuple(_identifier(value, "signed-code floor argument") for value in (input_code,modulus,quotient_code,remainder))
    safe = _identifier(tag, "signed-code floor tag")
    p,n,q,t = tuple(f"sif_{stem}_{safe}" for stem in ("positive","negative","quotient_positive","quotient_negative"))
    if set(arguments) & {p,n,q,t,"sif_gap_"+safe}:
        raise ValueError("generated signed-code floor binder captures an argument")
    first = signed_decode(input_code,p,n,tag=f"sif_{safe}_input")
    second = signed_decode(quotient_code,q,t,tag=f"sif_{safe}_quotient")
    return f"exists {p} {n} {q} {t}. (({first}) /\\ (({second}) /\\ ({_floor(p,n,modulus,q,t,remainder,tag=safe)})))"


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return (*(f"specialize {name} {argument}" for argument in arguments),f"apply {name}")


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def make_signed_integer_division_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "natural_mul_swap_right_tail",
            "forall a b c. a * (b * c) = b * (a * c)",
            ("mul_assoc","mul_comm"),
            ("intro a","intro b","intro c","trans (a * b) * c","symm","apply mul_assoc",
             "trans (b * a) * c","congr","apply mul_comm","refl","apply mul_assoc"),
            "A checked adjacent natural-product permutation supplies small ordinary-tactic polynomial calculations for both quadratic integer rings.",
        ),
        spec(
            "signed_integer_floor_exists",
            f"forall xp xn m. ~(m = 0) -> exists qp qn r. ({_floor('xp','xn','m','qp','qn','r',tag='pair_total')})",
            ("nonzero_is_succ","division_remainder_exists","mul_succ_left","add_assoc","add_comm"),
            _intro("xp","xn","m","hm")
            +("have hpred : exists h. m = S h",)+_call("nonzero_is_succ","m")+("exact hm","cases hpred",)
            +("have hdiv : exists q r. xp + x * xn = m * q + r /\\ (exists k. k + S r = m)",)
            +_call("division_remainder_exists","m","(xp + x * xn)")
            +("exact hm","cases hdiv","cases hdiv_witness","cases hdiv_witness_witness",)
            +("exists x1","exists xn","exists x2","split",)
            +("trans (xp + x * xn) + xn","rewrite hpred_witness","simp [mul_succ_left, add_assoc]",)
            +("trans (m * x1 + x2) + xn","congr","exact hdiv_witness_witness_left","refl","simp [add_assoc, add_comm]",)
            +("exact hdiv_witness_witness_right",),
            "Every signed pair admits an actual floor quotient and strict remainder for every nonzero natural divisor; one ordinary natural division suffices.",
        ),
        spec(
            "signed_integer_floor_quotient_transport",
            "forall xp xn m qp qn Qp Qn r. qp + Qn = qn + Qp -> "
            f"({_floor('xp','xn','m','qp','qn','r',tag='source')}) -> ({_floor('xp','xn','m','Qp','Qn','r',tag='target')})",
            ("add_left_cancel","mul_add","add_assoc","add_comm","four_square_add_swap_right_tail"),
            _intro("xp","xn","m","qp","qn","Qp","Qn","r","hbalance","hfloor")
            +("cases hfloor","split",)+_call("add_left_cancel","(m * qp)","(xp + m * Qn)","((xn + m * Qp) + r)")
            +("trans xp + m * (qp + Qn)","simp [mul_add, add_assoc, add_comm, four_square_add_swap_right_tail]","rewrite hbalance",)
            +("trans (xp + m * qn) + m * Qp","simp [mul_add, add_assoc]","rewrite hfloor_left","simp [add_assoc, add_comm, four_square_add_swap_right_tail]","exact hfloor_right"),
            "Replacing a quotient pair by any equal integer preserves the exact floor equation and the same strict remainder.",
        ),
        spec(
            "signed_integer_canonical_floor_exists",
            "forall xp xn m. ~(m = 0) -> exists code qp qn r. "
            f"({signed_decode('code','qp','qn',tag='sif_canonical')}) /\\ ({_floor('xp','xn','m','qp','qn','r',tag='canonical')})",
            ("signed_integer_floor_exists","signed_balance_total","signed_integer_floor_quotient_transport"),
            _intro("xp","xn","m","hm")
            +(f"have hfloor : exists qp qn r. {_floor('xp','xn','m','qp','qn','r',tag='first')}",)
            +_call("signed_integer_floor_exists","xp","xn","m")+("exact hm","cases hfloor","cases hfloor_witness","cases hfloor_witness_witness",)
            +("specialize signed_balance_total x","specialize signed_balance_total x1","cases signed_balance_total",)
            +("cases signed_balance_total_witness","cases signed_balance_total_witness_witness","cases signed_balance_total_witness_witness_witness",)
            +("exists x3","exists x4","exists x5","exists x2","split","exact signed_balance_total_witness_witness_witness_left",)
            +_call("signed_integer_floor_quotient_transport","xp","xn","m","x","x1","x4","x5","x2")
            +("exact signed_balance_total_witness_witness_witness_right","exact hfloor_witness_witness_witness"),
            "The constructed floor quotient has an actual canonical historic signed-integer code, with its normalized decoder witnesses.",
        ),
        spec(
            "signed_code_floor_exists",
            f"forall input m. ~(m = 0) -> exists quotient r. ({signed_code_floor_relation('input','m','quotient','r',tag='total')})",
            ("signed_decode_total","signed_integer_canonical_floor_exists"),
            _intro("input","m","hm")+("specialize signed_decode_total input","cases signed_decode_total","cases signed_decode_total_witness",)
            +("have hfloor : exists code qp qn r. "
              f"({signed_decode('code','qp','qn',tag='sif_input_canonical')}) /\\ ({_floor('x','x1','m','qp','qn','r',tag='input_canonical')})",)
            +_call("signed_integer_canonical_floor_exists","x","x1","m")
            +("exact hm","cases hfloor","cases hfloor_witness","cases hfloor_witness_witness","cases hfloor_witness_witness_witness","cases hfloor_witness_witness_witness_witness",)
            +("exists x2","exists x5","exists x","exists x1","exists x3","exists x4","split","exact signed_decode_total_witness_witness",)
            +("split","exact hfloor_witness_witness_witness_witness_left","exact hfloor_witness_witness_witness_witness_right"),
            "Every canonical signed integer has a canonical floor quotient and a witnessed strict natural remainder for every positive divisor.",
        ),
    )


__all__ = ["signed_integer_floor_relation","signed_code_floor_relation","make_signed_integer_division_candidate_theorems"]
