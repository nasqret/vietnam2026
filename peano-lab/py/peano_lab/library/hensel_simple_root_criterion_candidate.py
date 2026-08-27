"""Prime simple-root Hensel criterion without supplied inverses or powers.

The signed lifting implementation is reused unchanged. This additive bridge
constructs its derivative-unit witness from the ordinary nonzero-mod-prime
condition, then constructs the actual modulus at any positive precision.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .hensel_prime_power_candidate import _cop, _lt, _mod, _power
from .signed_hensel_lifting_candidate import (
    _arguments as _signed_arguments, _lift, _safe, _signed_pair, _simple, _unit,
)


def _arguments(*values: str) -> tuple[str, ...]:
    result = _signed_arguments(*values)
    if any(value.startswith("hsc_") for value in result):
        raise ValueError("generated simple-root-criterion binder captures an argument")
    return result


def _nonzero(p: str, dp: str, dn: str, *, tag: str) -> str:
    return f"~({_mod(p,dp,dn,tag=f'hsc_{_safe(tag)}')})"


def _nonsingular(pb: str, pc: str, nb: str, nc: str, a: str, l: str, m: str, p: str, *, tag: str) -> str:
    vp,dp,vn,dn = (f"hsc_{role}_{_safe(tag)}" for role in ("vp","dp","vn","dn"))
    return (
        f"exists {vp} {dp} {vn} {dn}. "
        f"(({_signed_pair(pb,pc,nb,nc,a,l,vp,dp,vn,dn,tag=f'hsc_{tag}_pair')}) /\\ "
        f"(({_mod(m,vp,vn,tag=f'hsc_{tag}_root')}) /\\ ({_nonzero(p,dp,dn,tag=tag)})))"
    )


def signed_derivative_nonzero_relation(p: str, dp: str, dn: str, *, tag: str) -> str:
    """The actual signed derivative is not zero modulo the chosen modulus."""
    return _nonzero(*_arguments(p,dp,dn),tag=_safe(tag))


def signed_nonsingular_horner_root_relation(pb: str, pc: str, nb: str, nc: str, a: str, l: str, m: str, p: str, *, tag: str) -> str:
    """Actual root/value/derivative witnesses, with no inverse supplied."""
    return _nonsingular(*_arguments(pb,pc,nb,nc,a,l,m,p),tag=_safe(tag))


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _call(name: str, *terms: str) -> tuple[str, ...]:
    return (*(f"specialize {name} ({term})" for term in terms),f"apply {name}")


def _all_lifts(pb: str, pc: str, nb: str, nc: str, a: str, l: str, p: str, k: str, *, tag: str) -> str:
    M,r,z = (f"hsc_{role}_{_safe(tag)}" for role in ("modulus","root","competitor"))
    return (
        f"exists {M}. (({_power(p,k,M,tag=f'hsc_{tag}_power')}) /\\ exists {r}. "
        f"(({_lift(pb,pc,nb,nc,l,p,a,M,r,tag=f'hsc_{tag}_chosen')}) /\\ "
        f"forall {z}. ({_lift(pb,pc,nb,nc,l,p,a,M,z,tag=f'hsc_{tag}_other')}) -> {z} = {r}))"
    )


def make_hensel_simple_root_criterion_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any,...]:
    """Return ordinary-HA bridge bodies, without changing a checked parent."""
    poly = ("pb","pc","nb","nc")
    result_predecessor = _all_lifts(*poly,"a","l","p","1 + x",tag="all_precision_predecessor")
    return (
        spec(
            "hensel_prime_blended_nonzero_derivative_is_unit",
            f"forall p h dp dn D. p = S h -> D = dp + h * dn -> ({prime('p',tag='hsc_blended_prime')}) -> "
            f"({_nonzero('p','dp','dn',tag='blended_nonzero')}) -> ({_unit('p','dp','dn',tag='hsc_blended_unit')})",
            ("hensel_signed_blend_zero_iff", "prime_not_divides_coprime", "coprime_symm",
             "multiple_implies_balanced_zero_congruence", "coprime_bounded_mod_inverse", "prime_nonzero",
             "hensel_signed_blend_mod_iff", "mul_one", "add_mul", "mul_assoc"),
            _intro("p","h","dp","dn","D","hsucc","hD","hp","hnonzero")
            +(f"have hiff : ((({_mod('p','D','0',tag='hsc_zero_forward')}) -> ({_mod('p','dp','dn',tag='hsc_zero_signed')})) /\\ (({_mod('p','dp','dn',tag='hsc_zero_reverse')}) -> ({_mod('p','D','0',tag='hsc_zero_blended')})))",)
            +_call("hensel_signed_blend_zero_iff","p","p","h","dp","dn","D")
            +("exact hsucc","exists 1","symm","apply mul_one","exact hD","cases hiff")
            +(f"have hcop : {_cop('D','p',tag='hsc_blended_coprime')}",)
            +_call("coprime_symm","p","D")+_call("prime_not_divides_coprime","p","D")
            +("exact hp","intro hdiv","apply hnonzero","apply hiff_left")
            +_call("multiple_implies_balanced_zero_congruence","p","D")+("exact hdiv",)
            +(f"have hinverse : exists u. (({_lt('u','p',tag='hsc_bound')}) /\\ ({_mod('p','D * u','1',tag='hsc_natural_inverse')}))",)
            +_call("coprime_bounded_mod_inverse","D","p")
            +("intro hz",)+_call("prime_nonzero","p")+("exact hp","exact hz","exact hcop","cases hinverse","cases hinverse_witness")
            +("have hproduct : D * x = dp * x + h * (dn * x)","rewrite hD","trans dp * x + (h * dn) * x","apply add_mul","congr","refl","apply mul_assoc")
            +(f"have htransport : ((({_mod('p','D * x','1',tag='hsc_inverse_forward')}) -> ({_mod('p','dp * x','1 + dn * x',tag='hsc_inverse_signed')})) /\\ (({_mod('p','dp * x','1 + dn * x',tag='hsc_inverse_reverse')}) -> ({_mod('p','D * x','1',tag='hsc_inverse_blended')})))",)
            +_call("hensel_signed_blend_mod_iff","p","p","h","dp * x","dn * x","D * x","1")
            +("exact hsucc","exists 1","symm","apply mul_one","exact hproduct","cases htransport","exists x","split","exact hinverse_witness_left","apply htransport_left","exact hinverse_witness_right"),
            "A derivative nonzero modulo a genuine prime yields a bounded signed inverse through the actual natural blend dp+(p-1)*dn, with coprimality and both residue transports proved explicitly.",
        ),
        spec(
            "hensel_prime_signed_nonzero_derivative_is_unit",
            f"forall p dp dn. ({prime('p',tag='hsc_derivative_prime')}) -> ({_nonzero('p','dp','dn',tag='derivative_criterion')}) -> "
            f"({_unit('p','dp','dn',tag='hsc_derivative_unit')})",
            ("prime_nonzero", "nonzero_is_succ", "hensel_prime_blended_nonzero_derivative_is_unit"),
            _intro("p","dp","dn","hp","hnonzero")
            +("have hpredecessor : exists h. p = S h",)+_call("nonzero_is_succ","p")
            +("intro hz",)+_call("prime_nonzero","p")+("exact hp","exact hz","cases hpredecessor")
            +_call("hensel_prime_blended_nonzero_derivative_is_unit","p","x","dp","dn","dp + x * dn")
            +("exact hpredecessor_witness","refl","exact hp","exact hnonzero"),
            "The ordinary signed nonzero-mod-prime derivative condition constructs the full bounded derivative-unit witness; neither an inverse nor a natural blend is supplied.",
        ),
        spec(
            "hensel_prime_nonsingular_root_is_simple",
            f"forall {' '.join((*poly,'a','l','m','p'))}. ({prime('p',tag='hsc_root_prime')}) -> "
            f"({_nonsingular(*poly,'a','l','m','p',tag='nonsingular_source')}) -> ({_simple(*poly,'a','l','m','p',tag='hsc_simple_result')})",
            ("hensel_prime_signed_nonzero_derivative_is_unit",),
            _intro(*poly,"a","l","m","p","hp","hroot")
            +tuple("cases hroot"+"_witness"*i for i in range(4))
            +("cases hroot_witness_witness_witness_witness","cases hroot_witness_witness_witness_witness_right")
            +("exists x","exists x1","exists x2","exists x3","split","exact hroot_witness_witness_witness_witness_left","split","exact hroot_witness_witness_witness_witness_right_left")
            +_call("hensel_prime_signed_nonzero_derivative_is_unit","p","x1","x3")
            +("exact hp","exact hroot_witness_witness_witness_witness_right_right"),
            "A genuine integer-polynomial root with derivative merely nonzero modulo the prime satisfies the unchanged unit-based simple-root interface, using the same actual Horner value and derivative witnesses.",
        ),
        spec(
            "integer_polynomial_prime_simple_root_lifts_all_positive_powers",
            f"forall {' '.join((*poly,'a','l','p','k'))}. ({prime('p',tag='hsc_all_precision_prime')}) -> ~(k = 0) -> "
            f"({_nonsingular(*poly,'a','l','p','p',tag='all_precision_source')}) -> ({_all_lifts(*poly,'a','l','p','k',tag='all_precision_result')})",
            ("hensel_prime_nonsingular_root_is_simple", "pow_exists", "pow_one", "nonzero_is_succ",
             "integer_polynomial_prime_power_hensel_iterated_exists_unique", "add_comm"),
            _intro(*poly,"a","l","p","k","hp","hk","hroot")
            +(f"have hsimple : {_simple(*poly,'a','l','p','p',tag='hsc_all_precision_simple')}",)
            +_call("hensel_prime_nonsingular_root_is_simple",*poly,"a","l","p","p")+("exact hp","exact hroot")
            +(f"have hpower : {_power('p','1','p',tag='hsc_initial_power')}",
              f"have hpowerexists : exists q. ({_power('p','1','q',tag='hsc_initial_power_exists')})")
            +_call("pow_exists","p","1")+("cases hpowerexists","have heq : x = p")
            +_call("pow_one","p","1","x")+("refl","exact hpowerexists_witness","rewrite heq at hpowerexists_witness","rewrite heq at hpowerexists_witness","exact hpowerexists_witness")
            +("have hpredecessor : exists j. k = S j",)+_call("nonzero_is_succ","k")+("exact hk","cases hpredecessor")
            +("have hexponent : 1 + x = k","trans x + 1","apply add_comm","trans S x","simp","symm","exact hpredecessor_witness")
            +(f"have hresult : {result_predecessor}",)
            +_call("integer_polynomial_prime_power_hensel_iterated_exists_unique",*poly,"a","l","p","1","x","p")
            +("exact hp","intro hz","apply PA1","exact hz","exact hpower","exact hsimple")
            +("rewrite hexponent at hresult",)*result_predecessor.count("1 + x")+("exact hresult",),
            "Exact full G095: a root modulo a prime with signed derivative nonzero modulo that prime has a uniquely determined bounded lift in its residue class at every positive precision; the actual power, inverse and lift are all constructed rather than supplied.",
        ),
    )


__all__ = [
    "signed_derivative_nonzero_relation", "signed_nonsingular_horner_root_relation",
    "make_hensel_simple_root_criterion_candidate_theorems",
]
