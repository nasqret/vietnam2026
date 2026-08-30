"""Constructive Cauchy--Davenport via actual finite Dyson transforms.

Finite sets are genuine beta-coded characteristic prefixes and their sizes
are existing BitCount witnesses.  Every result is an ordinary HA statement;
no set, cardinality, inverse, or finite-choice oracle is introduced.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_product_candidate import prime
from .finite_modular_set_candidate import (
    FiniteModularSetError, _AND, _OR, _arguments as _set_arguments, _at, _binary, _bits, _call,
    _count, _cover, _iff, _le, _lt, _member, _mod, _not, _pullback, _safe as _set_safe, _subset, _sumset,
)


class CauchyDavenportError(ValueError):
    """A Cauchy--Davenport surface has invalid or capturing arguments."""


def _safe(value: str) -> str:
    try:
        return _set_safe(value)
    except ValueError as error:
        raise CauchyDavenportError(str(error)) from error


def _arguments(*values: str) -> tuple[str, ...]:
    try:
        result = _set_arguments(*values)
        if any(value.startswith("cd_") for value in result):
            raise ValueError("generated additive-combinatorics binder captures an argument")
        return result
    except (FiniteModularSetError, ValueError) as error:
        raise CauchyDavenportError(str(error)) from error


def _boundary_pair(b: str, c: str, p: str, d: str, a: str, r: str, *, tag: str = "boundary") -> str:
    return (
        f"({_member(b,c,p,a,tag=f'cd_{tag}_source')}) /\\ (({_lt(r,p,tag=f'cd_{tag}_target')}) /\\ "
        f"(({_mod(p,f'{a}+{d}',r,tag=f'cd_{tag}_shift')}) /\\ ~({_at(b,c,r,'1',tag=f'cd_{tag}_outside')})))"
    )


def _boundary(b: str, c: str, p: str, d: str, *, tag: str = "boundary") -> str:
    a,r = f"cd_source_{_safe(tag)}", f"cd_target_{tag}"
    return f"exists {a} {r}. ({_boundary_pair(b,c,p,d,a,r,tag=tag)})"


def _dyson_upper(b: str, c: str, d: str, e: str, u: str, v: str, p: str, t: str, *, tag: str = "upper") -> str:
    z,a = f"cd_output_{_safe(tag)}", f"cd_source_{tag}"
    translated = f"exists {a}. ({_member(d,e,p,a,tag=f'cd_{tag}_member')}) /\\ ({_mod(p,f'{a}+{t}',z,tag=f'cd_{tag}_mod')})"
    union = f"({_at(b,c,z,'1',tag=f'cd_{tag}_old')}) \\/ ({translated})"
    return f"forall {z}. ({_lt(z,p,tag=f'cd_{tag}_bound')}) -> ({_iff(_at(u,v,z,'1',tag=f'cd_{tag}_result'),union)})"


def _dyson_lower(b: str, c: str, d: str, e: str, u: str, v: str, p: str, t: str, *, tag: str = "lower") -> str:
    z,a = f"cd_output_{_safe(tag)}", f"cd_source_{tag}"
    shifted = f"exists {a}. ({_member(b,c,p,a,tag=f'cd_{tag}_member')}) /\\ ({_mod(p,f'{z}+{t}',a,tag=f'cd_{tag}_mod')})"
    intersection = f"({_at(d,e,z,'1',tag=f'cd_{tag}_old')}) /\\ ({shifted})"
    return f"forall {z}. ({_lt(z,p,tag=f'cd_{tag}_bound')}) -> ({_iff(_at(u,v,z,'1',tag=f'cd_{tag}_result'),intersection)})"


def _dyson(b: str, c: str, d: str, e: str, ub: str, uc: str, vb: str, vc: str, p: str, t: str, *, tag: str = "dyson") -> str:
    return f"(({_dyson_upper(b,c,d,e,ub,uc,p,t,tag=f'{tag}_upper')}) /\\ ({_dyson_lower(b,c,d,e,vb,vc,p,t,tag=f'{tag}_lower')}))"


def _bound(p: str, k: str, l: str, m: str, *, tag: str = "bound") -> str:
    return f"(({_le(p,m,tag=f'cd_{tag}_full')}) \\/ ({_le(f'{k}+{l}',f'S ({m})',tag=f'cd_{tag}_sum')}))"


def _normalized_problem(bound: str | None) -> str:
    cutoff = "" if bound is None else f"({_lt('l',bound,tag='cd_induction_bound')}) -> "
    return (
        f"forall p b c d e sb sc k l m. ({prime('p',tag='cd_induction_prime')}) -> "
        f"({_count('b','c','p','k')}) -> ({_count('d','e','p','l')}) -> ({_count('sb','sc','p','m')}) -> "
        f"~(k=0) -> ({_member('d','e','p','0')}) -> ({_cover('b','c','d','e','sb','sc','p')}) -> "
        f"{cutoff}({_bound('p','k','l','m')})"
    )


def modular_translation_boundary_relation(code: str, scale: str, modulus: str, step: str, source: str, target: str, *, tag: str) -> str:
    """An actual in-set residue has an actual shifted residue outside the set."""
    return _boundary_pair(*_arguments(code,scale,modulus,step,source,target),tag=_safe(tag))


def modular_dyson_transform_relation(left_code: str, left_scale: str, right_code: str, right_scale: str, upper_code: str, upper_scale: str, lower_code: str, lower_scale: str, modulus: str, shift: str, *, tag: str) -> str:
    """Exact Ae=A union (B+e) and Be=B intersection (A-e), with actual source witnesses."""
    return _dyson(*_arguments(left_code,left_scale,right_code,right_scale,upper_code,upper_scale,lower_code,lower_scale,modulus,shift),tag=_safe(tag))


def cauchy_davenport_bound_relation(modulus: str, left_cardinality: str, right_cardinality: str, sum_cardinality: str, *, tag: str) -> str:
    """Subtraction-free exact lower bound: p<=m or k+l<=m+1."""
    return _bound(*_arguments(modulus,left_cardinality,right_cardinality,sum_cardinality),tag=_safe(tag))


def make_cauchy_davenport_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        _make_orbit_boundary_theorems(spec) + _make_dyson_constructor_theorems(spec)
        + _make_dyson_descent_theorems(spec) + _make_normalized_entrance_theorems(spec)
        + _make_normalized_induction_theorems(spec) + _make_full_cauchy_davenport_theorems(spec)
    )


def _make_orbit_boundary_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "finite_modular_add_modulus",
            f"forall p a. {_mod('p','a+p','a')}",
            ("zero_add",),
            ("intro p", "intro a", "exists 0", "exists 1", "simp [zero_add]"),
            "Adding the modulus preserves balanced congruence with explicit zero/one witnesses.",
        ),
        spec(
            "prime_modular_additive_orbit_hits",
            f"forall p d a z. ({prime('p',tag='cd_orbit_prime')}) -> ~(d=0) -> ({_lt('d','p')}) -> ({_lt('a','p')}) -> "
            f"exists n. ({_mod('p','a+n*d','z')})",
            ("prime_bounded_nonzero_mod_inverse", "finite_modular_additive_complement", "mod_eq_mul_right", "mod_eq_add", "mod_eq_refl", "mod_eq_trans", "finite_modular_add_modulus", "one_mul", "mul_assoc", "mul_comm", "add_assoc", "add_comm"),
            ("intro p", "intro d", "intro a", "intro z", "intro hp", "intro hd", "intro hdp", "intro hap",
             f"have hinv : exists u. ~(u=0) /\\ (({_lt('u','p')}) /\\ ({_mod('p','d*u','1')}))",
             *_call("prime_bounded_nonzero_mod_inverse","p","d"), "exact hp", "exact hd", "exact hdp", "cases hinv", "cases hinv_witness", "cases hinv_witness_right",
             "have hcomp : exists v. a+v=p", *_call("finite_modular_additive_complement","p","a"), "exact hap", "cases hcomp",
             "exists (z+x1)*x",
             f"have hproduct : {_mod('p','((z+x1)*x)*d','z+x1')}",
             f"have hscaled : {_mod('p','(d*x)*(z+x1)','1*(z+x1)')}", *_call("mod_eq_mul_right","p","d*x","1","z+x1"), "exact hinv_witness_right_right",
             "have hone : 1*(z+x1)=z+x1", *_call("one_mul","z+x1"), "rewrite hone at hscaled",
             "have he : ((z+x1)*x)*d=(d*x)*(z+x1)", "trans (z+x1)*(x*d)", *_call("mul_assoc","z+x1","x","d"), "trans (z+x1)*(d*x)", "congr", "refl", *_call("mul_comm","x","d"), *_call("mul_comm","z+x1","d*x"),
             "rewrite he", "exact hscaled",
             *_call("mod_eq_trans","p","a+((z+x1)*x)*d","a+(z+x1)","z"), *_call("mod_eq_add","p","a","a","((z+x1)*x)*d","z+x1"), *_call("mod_eq_refl","p","a"), "exact hproduct",
             "have he : a+(z+x1)=z+(a+x1)", "trans (a+z)+x1", "symm", *_call("add_assoc","a","z","x1"), "trans (z+a)+x1", "congr", *_call("add_comm","a","z"), "refl", *_call("add_assoc","z","a","x1"),
             "rewrite he", "rewrite hcomp_witness", *_call("finite_modular_add_modulus","p","z")),
            "An actual bounded inverse proves that every nonzero prime-field step reaches every residue from a given canonical start.",
        ),
        spec(
            "finite_modular_orbit_member_or_boundary",
            f"forall b c p d a n r. ~(p=0) -> ({_bits('b','c','p')}) -> ({_member('b','c','p','a')}) -> ({_lt('r','p')}) -> "
            f"({_mod('p','a+n*d','r')}) -> ({_at('b','c','r','1',tag='cd_orbit_inside')}) \\/ ({_boundary('b','c','p','d')})",
            ("mul_zero_left", "mod_eq_bounded_unique", "finite_modular_residue_exists", "finite_bit_membership_decidable", "mod_eq_add", "mod_eq_refl", "mod_eq_symm", "mod_eq_trans", "mul_succ_left", "add_assoc"),
            ("intro b", "intro c", "intro p", "intro d", "intro a", "induction n",
             "intro r", "intro hp", "intro hbits", "intro hstart", "intro hr", "intro hmod", "cases hstart",
             "have hzero : a+0*d=a", "simp [mul_zero_left]", "rewrite hzero at hmod",
             "have he : a=r", *_call("mod_eq_bounded_unique","p","a","r"), "exact hstart_left", "exact hr", "exact hmod",
             "left", "rewrite he at hstart_right", "rewrite he at hstart_right", "exact hstart_right",
             "intro r", "intro hp", "intro hbits", "intro hstart", "intro hr", "intro hmod",
             f"have hprev : exists v. ({_lt('v','p')}) /\\ ({_mod('p','a+n*d','v')})", *_call("finite_modular_residue_exists","p","a+n*d"), "exact hp", "cases hprev", "cases hprev_witness",
             f"have hcase : ({_at('b','c','x','1',tag='cd_orbit_previous')}) \\/ ({_boundary('b','c','p','d')})", *_call("IH","x"), "exact hp", "exact hbits", "exact hstart", "exact hprev_witness_left", "exact hprev_witness_right", "cases hcase",
             f"have hdec : ({_at('b','c','r','1',tag='cd_orbit_decision')}) \\/ ~({_at('b','c','r','1',tag='cd_orbit_decision')})", *_call("finite_bit_membership_decidable","b","c","p","r"), "exact hbits", "exact hr", "cases hdec", "left", "exact hdec_left",
             "right", "exists x", "exists r", "split", "split", "exact hprev_witness_left", "exact hcase_left", "split", "exact hr", "split",
             f"have hadd : {_mod('p','(a+n*d)+d','x+d')}", *_call("mod_eq_add","p","a+n*d","x","d","d"), "exact hprev_witness_right", *_call("mod_eq_refl","p","d"),
             *_call("mod_eq_trans","p","x+d","(a+n*d)+d","r"), *_call("mod_eq_symm","p","(a+n*d)+d","x+d"), "exact hadd",
             "have he : a+(S n)*d=(a+n*d)+d", "have hs : (S n)*d=n*d+d", *_call("mul_succ_left","n","d"), "rewrite hs", "symm", *_call("add_assoc","a","n*d","d"),
             "rewrite <- he", "exact hmod", "exact hdec_right", "right", "exact hcase_right"),
            "Finite orbit induction either proves membership at the reached residue or constructs an actual first-exit edge.",
        ),
        spec(
            "prime_modular_set_translation_boundary_exists",
            f"forall b c p d a z. ({prime('p',tag='cd_boundary_prime')}) -> ({_bits('b','c','p')}) -> "
            f"({_member('b','c','p','a')}) -> ({_lt('z','p')}) -> ~({_at('b','c','z','1',tag='cd_boundary_outside')}) -> "
            f"~(d=0) -> ({_lt('d','p')}) -> ({_boundary('b','c','p','d')})",
            ("prime_nonzero", "prime_modular_additive_orbit_hits", "finite_modular_orbit_member_or_boundary"),
            ("intro b", "intro c", "intro p", "intro d", "intro a", "intro z", "intro hp", "intro hbits", "intro hstart", "intro hz", "intro hout", "intro hd", "intro hdp",
             "have hpzero : ~(p=0)", "intro he", *_call("prime_nonzero","p"), "exact hp", "exact he",
             f"have horbit : exists n. {_mod('p','a+n*d','z')}", *_call("prime_modular_additive_orbit_hits","p","d","a","z"), "exact hp", "exact hd", "exact hdp", "cases hstart", "exact hstart_left", "cases horbit",
             f"have hcase : ({_at('b','c','z','1',tag='cd_boundary_final')}) \\/ ({_boundary('b','c','p','d')})", *_call("finite_modular_orbit_member_or_boundary","b","c","p","d","a","x","z"), "exact hpzero", "exact hbits", "exact hstart", "exact hz", "exact horbit_witness", "cases hcase", "exfalso", "apply hout", "exact hcase_left", "exact hcase_right"),
            "Every nonempty proper prime-field characteristic set has a witnessed boundary in each nonzero additive direction.",
        ),
    )


def _make_dyson_constructor_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    shifted_B = f"exists a. ({_member('d','e','p','a')}) /\\ ({_mod('p','a+t','z')})"
    upper_bits = f"({_at('b','c','z','1',tag='cd_U_A')}) \\/ ({_at('tb','tc','z','1',tag='cd_U_T')})"
    lower_source = f"exists a. ({_member('ib','ic','p','a')}) /\\ ({_mod('p','z+t','a')})"
    inter_bits = f"({_at('b','c','x','1',tag='cd_I_A')}) /\\ ({_at('tb','tc','x','1',tag='cd_I_T')})"
    return (
        spec(
            "finite_modular_dyson_upper_from_union",
            f"forall b c d e tb tc ub uc p t v. ~(p=0) -> t+v=p -> ({_pullback('d','e','tb','tc','p','v')}) -> "
            f"({_binary('b','c','tb','tc','ub','uc','p',_OR)}) -> ({_dyson_upper('b','c','d','e','ub','uc','p','t')})",
            ("finite_modular_pushforward_membership_witness",),
            ("intro b", "intro c", "intro d", "intro e", "intro tb", "intro tc", "intro ub", "intro uc", "intro p", "intro t", "intro v", "intro hp", "intro htv", "intro hpull", "intro hunion", "intro z", "intro hz",
             f"have hshift : {_iff(_at('tb','tc','z','1',tag='cd_upper_shift'),shifted_B)}", *_call("finite_modular_pushforward_membership_witness","d","e","tb","tc","p","t","v","z"), "exact hp", "exact htv", "exact hpull", "exact hz", "cases hshift",
             f"have hun : {_iff(_at('ub','uc','z','1',tag='cd_upper_new'),upper_bits)}", *_call("hunion","z"), "exact hz", "cases hun", "split", "intro hu",
             f"have hcase : {upper_bits}", "apply hun_left", "exact hu", "cases hcase", "left", "exact hcase_left", "right", "apply hshift_left", "exact hcase_right",
             "intro hcase", "apply hun_right", "cases hcase", "left", "exact hcase_left", "right", "apply hshift_right", "exact hcase_right"),
            "The actual union with a genuine forward translate has exactly the upper Dyson-transform membership.",
        ),
        spec(
            "finite_modular_dyson_lower_from_pullback",
            f"forall b c d e tb tc ib ic vb vc p t v. ~(p=0) -> t+v=p -> ({_pullback('d','e','tb','tc','p','v')}) -> "
            f"({_binary('b','c','tb','tc','ib','ic','p',_AND)}) -> ({_pullback('ib','ic','vb','vc','p','t')}) -> "
            f"({_dyson_lower('b','c','d','e','vb','vc','p','t')})",
            ("finite_modular_pullback_membership_witness", "finite_modular_inverse_shift"),
            ("intro b", "intro c", "intro d", "intro e", "intro tb", "intro tc", "intro ib", "intro ic", "intro vb", "intro vc", "intro p", "intro t", "intro v", "intro hp", "intro htv", "intro hT", "intro hI", "intro hV", "intro z", "intro hz",
             f"have hsource : {_iff(_at('vb','vc','z','1',tag='cd_lower_V'),lower_source)}", *_call("finite_modular_pullback_membership_witness","ib","ic","vb","vc","p","t","z"), "exact hp", "exact hV", "exact hz", "cases hsource", "split", "intro hmember",
             f"have hw : {lower_source}", "apply hsource_left", "exact hmember", "cases hw", "cases hw_witness", "cases hw_witness_left",
             f"have hinter : {_iff(_at('ib','ic','x','1',tag='cd_lower_I'),inter_bits)}", *_call("hI","x"), "exact hw_witness_left_left", "cases hinter",
             f"have hboth : {inter_bits}", "apply hinter_left", "exact hw_witness_left_right", "cases hboth",
             f"have hback : {_iff(_at('tb','tc','x','1',tag='cd_lower_T'),_at('d','e','z','1',tag='cd_lower_B'))}", *_call("hT","x","z"), "exact hw_witness_left_left", "exact hz", *_call("finite_modular_inverse_shift","p","t","v","z","x"), "exact htv", "exact hw_witness_right", "cases hback",
             "split", "apply hback_left", "exact hboth_right", "exists x", "split", "split", "exact hw_witness_left_left", "exact hboth_left", "exact hw_witness_right",
             "intro hmember", "cases hmember", "cases hmember_right", "cases hmember_right_witness", "cases hmember_right_witness_left",
             f"have hinter : {_iff(_at('ib','ic','x','1',tag='cd_lower_back_I'),inter_bits)}", *_call("hI","x"), "exact hmember_right_witness_left_left", "cases hinter",
             f"have hback : {_iff(_at('tb','tc','x','1',tag='cd_lower_back_T'),_at('d','e','z','1',tag='cd_lower_back_B'))}", *_call("hT","x","z"), "exact hmember_right_witness_left_left", "exact hz", *_call("finite_modular_inverse_shift","p","t","v","z","x"), "exact htv", "exact hmember_right_witness_right", "cases hback",
             "apply hsource_right", "exists x", "split", "split", "exact hmember_right_witness_left_left", "apply hinter_right", "split", "exact hmember_right_witness_left_right", "apply hback_right", "exact hmember_left", "exact hmember_right_witness_right"),
            "The genuine pullback of A intersection (B+e) is exactly B intersection (A-e), with actual canonical witnesses.",
        ),
        spec(
            "finite_modular_dyson_transform_exists",
            f"forall b c d e p k l t. ~(p=0) -> ({_count('b','c','p','k')}) -> ({_count('d','e','p','l')}) -> ({_lt('t','p')}) -> "
            f"exists ub uc vb vc K L. ({_count('ub','uc','p','K')}) /\\ (({_count('vb','vc','p','L')}) /\\ (K+L=k+l /\\ ({_dyson('b','c','d','e','ub','uc','vb','vc','p','t')})))",
            ("finite_modular_additive_complement", "finite_modular_set_pullback_exists", "finite_bit_union_exists", "finite_bit_intersection_exists", "finite_bit_union_intersection_count_balance", "finite_modular_dyson_upper_from_union", "finite_modular_dyson_lower_from_pullback"),
            ("intro b", "intro c", "intro d", "intro e", "intro p", "intro k", "intro l", "intro t", "intro hp", "intro hA", "intro hB", "intro ht",
             "have hcomp : exists v. t+v=p", *_call("finite_modular_additive_complement","p","t"), "exact ht", "cases hcomp",
             f"have hT : exists tb tc. ({_count('tb','tc','p','l')}) /\\ ({_pullback('d','e','tb','tc','p','x')})", *_call("finite_modular_set_pullback_exists","d","e","p","l","x"), "exact hp", "exact hB", "cases hT", "cases hT_witness", "cases hT_witness_witness",
             f"have hU : exists ub uc K. ({_count('ub','uc','p','K')}) /\\ ({_binary('b','c','x1','x2','ub','uc','p',_OR)})", *_call("finite_bit_union_exists","b","c","x1","x2","p","k","l"), "exact hA", "exact hT_witness_witness_left", "cases hU", "cases hU_witness", "cases hU_witness_witness", "cases hU_witness_witness_witness",
             f"have hI : exists ib ic L. ({_count('ib','ic','p','L')}) /\\ ({_binary('b','c','x1','x2','ib','ic','p',_AND)})", *_call("finite_bit_intersection_exists","b","c","x1","x2","p","k","l"), "exact hA", "exact hT_witness_witness_left", "cases hI", "cases hI_witness", "cases hI_witness_witness", "cases hI_witness_witness_witness",
             f"have hV : exists vb vc. ({_count('vb','vc','p','x8')}) /\\ ({_pullback('x6','x7','vb','vc','p','t')})", *_call("finite_modular_set_pullback_exists","x6","x7","p","x8","t"), "exact hp", "exact hI_witness_witness_witness_left", "cases hV", "cases hV_witness", "cases hV_witness_witness",
             "exists x3", "exists x4", "exists x9", "exists x10", "exists x5", "exists x8", "split", "exact hU_witness_witness_witness_left", "split", "exact hV_witness_witness_left", "split",
             *_call("finite_bit_union_intersection_count_balance","b","c","x1","x2","x3","x4","x6","x7","p","k","l","x5","x8"), "exact hA", "exact hT_witness_witness_left", "exact hU_witness_witness_witness_left", "exact hI_witness_witness_witness_left", "exact hU_witness_witness_witness_right", "exact hI_witness_witness_witness_right",
             "split", *_call("finite_modular_dyson_upper_from_union","b","c","d","e","x1","x2","x3","x4","p","t","x"), "exact hp", "exact hcomp_witness", "exact hT_witness_witness_right", "exact hU_witness_witness_witness_right",
             *_call("finite_modular_dyson_lower_from_pullback","b","c","d","e","x1","x2","x6","x7","x9","x10","p","t","x"), "exact hp", "exact hcomp_witness", "exact hT_witness_witness_right", "exact hI_witness_witness_witness_right", "exact hV_witness_witness_right"),
            "Construct both actual Dyson-transform sets and their exact cardinalities, preserving the sum of the two input sizes.",
        ),
    )


def _make_dyson_descent_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    upper_a = f"({_at('b','c','a','1',tag='cd_upper_member_A')}) \\/ exists j. ({_member('d','e','p','j')}) /\\ ({_mod('p','j+t','a')})"
    lower_i = f"({_at('d','e','i','1',tag='cd_lower_member_B')}) /\\ exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','i+t','j')})"
    lower_zero = f"({_at('d','e','0','1',tag='cd_lower_zero_B')}) /\\ exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','0+t','j')})"
    lower_h = f"({_at('d','e','h','1',tag='cd_lower_boundary_B')}) /\\ exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','h+t','j')})"
    upper_cover = f"({_at('b','c','a','1',tag='cd_cover_A')}) \\/ exists j. ({_member('d','e','p','j')}) /\\ ({_mod('p','j+t','a')})"
    lower_cover = f"({_at('d','e','z','1',tag='cd_cover_B')}) /\\ exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','z+t','j')})"
    return (
        spec(
            "finite_modular_dyson_upper_member",
            f"forall b c d e u v p t a. ({_dyson_upper('b','c','d','e','u','v','p','t')}) -> ({_member('b','c','p','a')}) -> ({_member('u','v','p','a')})",
            (),
            ("intro b", "intro c", "intro d", "intro e", "intro u", "intro v", "intro p", "intro t", "intro a", "intro hupper", "intro hmember", "cases hmember", "split", "exact hmember_left",
             f"have he : {_iff(_at('u','v','a','1',tag='cd_upper_member_U'),upper_a)}", *_call("hupper","a"), "exact hmember_left", "cases he", "apply he_right", "left", "exact hmember_right"),
            "The upper Dyson transform contains every actual member of the original first set.",
        ),
        spec(
            "finite_modular_dyson_lower_subset",
            f"forall b c d e u v p t. ({_dyson_lower('b','c','d','e','u','v','p','t')}) -> ({_subset('u','v','d','e','p')})",
            (),
            ("intro b", "intro c", "intro d", "intro e", "intro u", "intro v", "intro p", "intro t", "intro hlower", "intro i", "intro hi", "intro hmember",
             f"have he : {_iff(_at('u','v','i','1',tag='cd_lower_member_V'),lower_i)}", *_call("hlower","i"), "exact hi", "cases he",
             f"have hboth : {lower_i}", "apply he_left", "exact hmember", "cases hboth", "exact hboth_left"),
            "The lower Dyson transform is an actual subset of the original second set.",
        ),
        spec(
            "finite_modular_dyson_lower_zero_member",
            f"forall b c d e u v p t. ({_dyson_lower('b','c','d','e','u','v','p','t')}) -> ({_member('d','e','p','0')}) -> "
            f"({_member('b','c','p','t')}) -> ({_member('u','v','p','0')})",
            ("zero_add", "mod_eq_refl"),
            ("intro b", "intro c", "intro d", "intro e", "intro u", "intro v", "intro p", "intro t", "intro hlower", "intro hzero", "intro ht", "cases hzero", "split", "exact hzero_left",
             f"have he : {_iff(_at('u','v','0','1',tag='cd_lower_zero_V'),lower_zero)}", *_call("hlower","0"), "exact hzero_left", "cases he", "apply he_right", "split", "exact hzero_right", "exists t", "split", "exact ht",
             "have hz : 0+t=t", *_call("zero_add","t"), "rewrite hz", *_call("mod_eq_refl","p","t")),
            "When zero belongs to B and the shift belongs to A, zero genuinely belongs to the lower Dyson set.",
        ),
        spec(
            "finite_modular_dyson_lower_boundary_nonmember",
            f"forall b c d e u v p t h r. ({_dyson_lower('b','c','d','e','u','v','p','t')}) -> "
            f"({_boundary_pair('b','c','p','h','t','r')}) -> ({_lt('h','p')}) -> ~({_at('u','v','h','1',tag='cd_boundary_missing')})",
            ("mod_eq_bounded_unique", "mod_eq_trans", "mod_eq_symm", "add_comm"),
            ("intro b", "intro c", "intro d", "intro e", "intro u", "intro v", "intro p", "intro t", "intro h", "intro r", "intro hlower", "intro hboundary", "intro hh", "intro hmember",
             "cases hboundary", "cases hboundary_right", "cases hboundary_right_right",
             f"have he : {_iff(_at('u','v','h','1',tag='cd_boundary_V'),lower_h)}", *_call("hlower","h"), "exact hh", "cases he",
             f"have hboth : {lower_h}", "apply he_left", "exact hmember", "cases hboth", "cases hboth_right", "cases hboth_right_witness", "cases hboth_right_witness_left",
             "have heq : x=r", *_call("mod_eq_bounded_unique","p","x","r"), "exact hboth_right_witness_left_left", "exact hboundary_right_left",
             *_call("mod_eq_trans","p","x","h+t","r"), *_call("mod_eq_symm","p","h+t","x"), "exact hboth_right_witness_right",
             "have hcomm : h+t=t+h", *_call("add_comm","h","t"), "rewrite hcomm", "exact hboundary_right_right_left",
             "apply hboundary_right_right_right", "rewrite heq at hboth_right_witness_left_right", "rewrite heq at hboth_right_witness_left_right", "exact hboth_right_witness_left_right"),
            "An actual translation-boundary direction is absent from the lower Dyson transform.",
        ),
        spec(
            "finite_modular_dyson_sum_cover",
            f"forall b c d e ub uc vb vc sb sc p t. ({_dyson('b','c','d','e','ub','uc','vb','vc','p','t')}) -> "
            f"({_cover('b','c','d','e','sb','sc','p')}) -> ({_cover('ub','uc','vb','vc','sb','sc','p')})",
            ("finite_modular_shifted_sum_congruence", "mod_eq_trans", "add_comm"),
            ("intro b", "intro c", "intro d", "intro e", "intro ub", "intro uc", "intro vb", "intro vc", "intro sb", "intro sc", "intro p", "intro t", "intro hdyson", "intro hcover", "cases hdyson",
             "intro a", "intro z", "intro w", "intro ha", "intro hz", "intro hw", "intro hU", "intro hV", "intro hmod",
             f"have hupper : {_iff(_at('ub','uc','a','1',tag='cd_cover_U'),upper_cover)}", *_call("hdyson_left","a"), "exact ha", "cases hupper",
             f"have hlower : {_iff(_at('vb','vc','z','1',tag='cd_cover_V'),lower_cover)}", *_call("hdyson_right","z"), "exact hz", "cases hlower",
             f"have hboth : {lower_cover}", "apply hlower_left", "exact hV", "cases hboth",
             f"have hcase : {upper_cover}", "apply hupper_left", "exact hU", "cases hcase",
             *_call("hcover","a","z","w"), "exact ha", "exact hz", "exact hw", "exact hcase_left", "exact hboth_left", "exact hmod",
             "cases hcase_right", "cases hcase_right_witness", "cases hcase_right_witness_left", "cases hboth_right", "cases hboth_right_witness", "cases hboth_right_witness_left",
             *_call("hcover","x1","x","w"), "exact hboth_right_witness_left_left", "exact hcase_right_witness_left_left", "exact hw", "exact hboth_right_witness_left_right", "exact hcase_right_witness_left_right",
             "have hcomm : x1+x=x+x1", *_call("add_comm","x1","x"), "rewrite hcomm", *_call("mod_eq_trans","p","x+x1","a+z","w"),
             *_call("finite_modular_shifted_sum_congruence","p","x","x1","a","z","t"), "exact hcase_right_witness_right", "exact hboth_right_witness_right", "exact hmod"),
            "Every actual sum from the Dyson pair remains in every coded upper set of the original sumset.",
        ),
        spec(
            "finite_modular_dyson_strict_sizes",
            f"forall b c d e ub uc vb vc p t h r K L l. ({_count('ub','uc','p','K')}) -> ({_count('vb','vc','p','L')}) -> ({_count('d','e','p','l')}) -> "
            f"({_dyson('b','c','d','e','ub','uc','vb','vc','p','t')}) -> ({_member('d','e','p','0')}) -> ({_member('d','e','p','h')}) -> "
            f"({_boundary_pair('b','c','p','h','t','r')}) -> ~(K=0) /\\ (~(L=0) /\\ ({_lt('L','l')}))",
            ("finite_modular_dyson_upper_member", "finite_modular_dyson_lower_zero_member", "finite_bit_member_count_nonzero", "finite_modular_dyson_lower_subset", "finite_modular_dyson_lower_boundary_nonmember", "finite_bit_nonmember_zero", "finite_bit_count_proper_subset_lt"),
            ("intro b", "intro c", "intro d", "intro e", "intro ub", "intro uc", "intro vb", "intro vc", "intro p", "intro t", "intro h", "intro r", "intro K", "intro L", "intro l",
             "intro hU", "intro hV", "intro hB", "intro hdyson", "intro hzero", "intro hstep", "intro hboundary", "cases hdyson",
             f"have hsource : {_member('b','c','p','t')}", "cases hboundary", "exact hboundary_left",
             f"have hupper : {_member('ub','uc','p','t')}", *_call("finite_modular_dyson_upper_member","b","c","d","e","ub","uc","p","t","t"), "exact hdyson_left", "exact hsource",
             f"have hlower : {_member('vb','vc','p','0')}", *_call("finite_modular_dyson_lower_zero_member","b","c","d","e","vb","vc","p","t"), "exact hdyson_right", "exact hzero", "exact hsource",
             f"have hh : {_lt('h','p')}", "cases hstep", "exact hstep_left",
             f"have hmissing : ~({_at('vb','vc','h','1',tag='cd_strict_missing')})", "intro hv", *_call("finite_modular_dyson_lower_boundary_nonmember","b","c","d","e","vb","vc","p","t","h","r"), "exact hdyson_right", "exact hboundary", "exact hh", "exact hv",
             "split", "intro hz", *_call("finite_bit_member_count_nonzero","ub","uc","p","K","t"), "exact hU", "exact hupper", "exact hz",
             "split", "intro hz", *_call("finite_bit_member_count_nonzero","vb","vc","p","L","0"), "exact hV", "exact hlower", "exact hz",
             *_call("finite_bit_count_proper_subset_lt","vb","vc","d","e","p","L","l","h"), "exact hV", "exact hB", *_call("finite_modular_dyson_lower_subset","b","c","d","e","vb","vc","p","t"), "exact hdyson_right", "exact hh",
             *_call("finite_bit_nonmember_zero","vb","vc","p","h"), "cases hV", "exact hV_right", "exact hh", "exact hmissing", "cases hstep", "exact hstep_right"),
            "An actual boundary transform keeps both sets nonempty and strictly decreases the second exact cardinality.",
        ),
    )


def _make_normalized_entrance_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "finite_modular_zero_sum_left_subset",
            f"forall b c d e sb sc p. ({_cover('b','c','d','e','sb','sc','p')}) -> ({_member('d','e','p','0')}) -> ({_subset('b','c','sb','sc','p')})",
            ("mod_eq_refl",),
            ("intro b", "intro c", "intro d", "intro e", "intro sb", "intro sc", "intro p", "intro hcover", "intro hzero", "cases hzero", "intro i", "intro hi", "intro hA",
             *_call("hcover","i","0","i"), "exact hi", "exact hzero_left", "exact hi", "exact hA", "exact hzero_right",
             "have he : i+0=i", "apply PA3", "rewrite he", *_call("mod_eq_refl","p","i")),
            "When zero is a genuine second-set member, the first set is an actual subset of every upper sumset.",
        ),
        spec(
            "finite_modular_singleton_cover_bound",
            f"forall b c d e sb sc p k l m. ({_count('b','c','p','k')}) -> ({_count('sb','sc','p','m')}) -> ({_cover('b','c','d','e','sb','sc','p')}) -> "
            f"({_member('d','e','p','0')}) -> l=1 -> ({_bound('p','k','l','m')})",
            ("finite_modular_zero_sum_left_subset", "finite_bit_count_subset_le", "succ_le_succ"),
            ("intro b", "intro c", "intro d", "intro e", "intro sb", "intro sc", "intro p", "intro k", "intro l", "intro m", "intro hA", "intro hS", "intro hcover", "intro hzero", "intro hl",
             "right", "rewrite hl", "have he : k+1=S k", "simp", "rewrite he", *_call("succ_le_succ","k","m"),
             *_call("finite_bit_count_subset_le","b","c","sb","sc","p","k","m"), "exact hA", "exact hS", *_call("finite_modular_zero_sum_left_subset","b","c","d","e","sb","sc","p"), "exact hcover", "exact hzero"),
            "The normalized singleton case has the exact Cauchy--Davenport bound by genuine subset counting.",
        ),
        spec(
            "prime_modular_normalized_boundary_exists",
            f"forall b c d e sb sc p k l m. ({prime('p',tag='cd_normalized_prime')}) -> ({_count('b','c','p','k')}) -> ({_count('d','e','p','l')}) -> "
            f"({_count('sb','sc','p','m')}) -> ~(k=0) -> ({_le('2','l')}) -> ({_member('d','e','p','0')}) -> ({_cover('b','c','d','e','sb','sc','p')}) -> ~(m=p) -> "
            f"exists h t r. ({_member('d','e','p','h')}) /\\ ({_boundary_pair('b','c','p','h','t','r')})",
            ("finite_bit_count_missing_zero", "finite_bit_count_positive_member", "finite_bit_count_two_nonzero_member", "prime_modular_set_translation_boundary_exists", "finite_modular_zero_sum_left_subset", "finite_bit_zero_nonmember"),
            ("intro b", "intro c", "intro d", "intro e", "intro sb", "intro sc", "intro p", "intro k", "intro l", "intro m", "intro hp", "intro hA", "intro hB", "intro hS", "intro hk", "intro hl", "intro hzero", "intro hcover", "intro hm",
             f"have hout : exists z. ({_lt('z','p')}) /\\ ({_at('sb','sc','z','0',tag='cd_normalized_out')})", *_call("finite_bit_count_missing_zero","sb","sc","p","m"), "exact hS", "exact hm", "cases hout", "cases hout_witness",
             f"have ha : exists a. {_member('b','c','p','a')}", *_call("finite_bit_count_positive_member","b","c","p","k"), "exact hA", "exact hk", "cases ha",
             f"have hh : exists h. ({_member('d','e','p','h')}) /\\ ~(h=0)", *_call("finite_bit_count_two_nonzero_member","d","e","p","l"), "exact hB", "exact hl", "cases hh", "cases hh_witness",
             f"have hsub : {_subset('b','c','sb','sc','p')}", *_call("finite_modular_zero_sum_left_subset","b","c","d","e","sb","sc","p"), "exact hcover", "exact hzero",
             f"have hnotA : ~({_at('b','c','x','1',tag='cd_normalized_notA')})", "intro hmember", *_call("finite_bit_zero_nonmember","sb","sc","x"), "exact hout_witness_right", *_call("hsub","x"), "exact hout_witness_left", "exact hmember",
             f"have hboundary : {_boundary('b','c','p','x2')}", *_call("prime_modular_set_translation_boundary_exists","b","c","p","x2","x1","x"), "exact hp", "cases hA", "exact hA_right", "exact ha_witness", "exact hout_witness_left", "exact hnotA", "exact hh_witness_right", "cases hh_witness_left", "exact hh_witness_left_left",
             "cases hboundary", "cases hboundary_witness", "exists x2", "exists x3", "exists x4", "split", "exact hh_witness_left", "exact hboundary_witness_witness"),
            "A normalized nontrivial second set and a non-full upper sumset construct an actual boundary suitable for strict Dyson descent.",
        ),
    )


def _make_normalized_induction_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    variables = ("p","b","c","d","e","sb","sc","k","l","m")
    hypotheses = ("hprime","hA","hB","hS","hk","hzero","hcover","hbound")
    introductions = tuple(f"intro {name}" for name in variables+hypotheses)
    script = [
        "induction N", *introductions, "exfalso", "cases hbound", "have hz : S l=0",
        *_call("add_eq_zero_right","x","S l"), "exact hbound_witness", *_call("succ_ne_zero","l"), "exact hz", *introductions,
        f"have hcase : l=N \\/ ({_lt('l','N')})", *_call("finite_lt_succ_eq_or_lt","N","l"), "exact hbound", "cases hcase",
        "specialize eq_decidable m", "specialize eq_decidable p", "cases eq_decidable", "left", "rewrite eq_decidable_left", *_call("le_refl","p"),
        f"have hsmall : ({_le('l','1')}) \\/ ({_lt('1','l')})", *_call("le_or_lt","l","1"), "cases hsmall",
        "have hlone : l=1", *_call("le_antisymm","l","1"), "exact hsmall_left", *_call("one_le_of_ne_zero","l"), "intro hz", *_call("finite_bit_member_count_nonzero","d","e","p","l","0"), "exact hB", "exact hzero", "exact hz",
        *_call("finite_modular_singleton_cover_bound","b","c","d","e","sb","sc","p","k","l","m"), "exact hA", "exact hS", "exact hcover", "exact hzero", "exact hlone",
        f"have hboundary : exists h t r. ({_member('d','e','p','h')}) /\\ ({_boundary_pair('b','c','p','h','t','r')})",
        *_call("prime_modular_normalized_boundary_exists","b","c","d","e","sb","sc","p","k","l","m"),
        "exact hprime", "exact hA", "exact hB", "exact hS", "exact hk", "exact hsmall_right", "exact hzero", "exact hcover", "exact eq_decidable_right",
        "cases hboundary", "cases hboundary_witness", "cases hboundary_witness_witness", "cases hboundary_witness_witness_witness",
        f"have hsource : {_member('b','c','p','x1')}", "cases hboundary_witness_witness_witness_right", "exact hboundary_witness_witness_witness_right_left",
        "have hpzero : ~(p=0)", "intro he", *_call("prime_nonzero","p"), "exact hprime", "exact he",
        f"have htransform : exists ub uc vb vc K L. ({_count('ub','uc','p','K')}) /\\ (({_count('vb','vc','p','L')}) /\\ (K+L=k+l /\\ ({_dyson('b','c','d','e','ub','uc','vb','vc','p','x1')})))",
        *_call("finite_modular_dyson_transform_exists","b","c","d","e","p","k","l","x1"), "exact hpzero", "exact hA", "exact hB", "cases hsource", "exact hsource_left",
    ]
    package = "htransform"
    for _ in range(6):
        script.append(f"cases {package}")
        package += "_witness"
    script.extend((f"cases {package}", f"cases {package}_right", f"cases {package}_right_right"))
    count_U, count_V, balance, dyson = f"{package}_left", f"{package}_right_left", f"{package}_right_right_left", f"{package}_right_right_right"
    script.extend((
        f"have hstrict : ~(x7=0) /\\ (~(x8=0) /\\ ({_lt('x8','l')}))",
        *_call("finite_modular_dyson_strict_sizes","b","c","d","e","x3","x4","x5","x6","p","x1","x","x2","x7","x8","l"),
        f"exact {count_U}", f"exact {count_V}", "exact hB", f"exact {dyson}", "exact hzero", "exact hboundary_witness_witness_witness_left", "exact hboundary_witness_witness_witness_right", "cases hstrict", "cases hstrict_right",
        f"have hzeroV : {_member('x5','x6','p','0')}", *_call("finite_modular_dyson_lower_zero_member","b","c","d","e","x5","x6","p","x1"), f"cases {dyson}", f"exact {dyson}_right", "exact hzero", "exact hsource",
        f"have hnewcover : {_cover('x3','x4','x5','x6','sb','sc','p')}", *_call("finite_modular_dyson_sum_cover","b","c","d","e","x3","x4","x5","x6","sb","sc","p","x1"), f"exact {dyson}", "exact hcover",
        f"have hresult : {_bound('p','x7','x8','m')}", *_call("IH","p","x3","x4","x5","x6","sb","sc","x7","x8","m"),
        "exact hprime", f"exact {count_U}", f"exact {count_V}", "exact hS", "exact hstrict_left", "exact hzeroV", "exact hnewcover", "rewrite hcase_left at hstrict_right_right", "exact hstrict_right_right",
        "cases hresult", "left", "exact hresult_left", "right", f"rewrite {balance} at hresult_right", "exact hresult_right",
        *_call("IH",*variables), "exact hprime", "exact hA", "exact hB", "exact hS", "exact hk", "exact hzero", "exact hcover", "exact hcase_right",
    ))
    return (
        spec(
            "prime_cauchy_davenport_normalized_bounded_induction",
            f"forall N. {_normalized_problem('N')}",
            ("add_eq_zero_right", "succ_ne_zero", "finite_lt_succ_eq_or_lt", "eq_decidable", "le_refl", "le_or_lt", "le_antisymm", "one_le_of_ne_zero", "finite_bit_member_count_nonzero", "finite_modular_singleton_cover_bound", "prime_modular_normalized_boundary_exists", "prime_nonzero", "finite_modular_dyson_transform_exists", "finite_modular_dyson_strict_sizes", "finite_modular_dyson_lower_zero_member", "finite_modular_dyson_sum_cover"), tuple(script),
            "Ordinary bounded induction on the actual second-set cardinality proves the full normalized Cauchy--Davenport bound using genuine strict Dyson descent.",
        ),
        spec(
            "prime_cauchy_davenport_normalized_cover_bound", _normalized_problem(None),
            ("prime_cauchy_davenport_normalized_bounded_induction", "le_refl"),
            (*tuple(f"intro {name}" for name in variables+hypotheses[:-1]), *_call("prime_cauchy_davenport_normalized_bounded_induction","S l",*variables),
             "exact hprime", "exact hA", "exact hB", "exact hS", "exact hk", "exact hzero", "exact hcover", *_call("le_refl","S l")),
            "Every normalized nonempty prime-field pair has the sharp bound against every actual coded upper sumset.",
        ),
    )


def _make_full_cauchy_davenport_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    original_A = f"exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','j+t','a')})"
    original_B = f"exists j. ({_member('d','e','p','j')}) /\\ ({_mod('p','z+t','j')})"
    variables = ("p","b","c","d","e","sb","sc","k","l","m")
    hypotheses = ("hprime","hA","hB","hS","hk","hl","hcover")
    full_prefix = (
        f"forall p b c d e sb sc k l m. ({prime('p',tag='cd_full_prime')}) -> "
        f"({_count('b','c','p','k')}) -> ({_count('d','e','p','l')}) -> ({_count('sb','sc','p','m')}) -> ~(k=0) -> ~(l=0) -> "
    )
    return (
        spec(
            "finite_modular_pullback_zero_member",
            f"forall b c u v p t. ~(p=0) -> ({_pullback('b','c','u','v','p','t')}) -> ({_member('b','c','p','t')}) -> ({_member('u','v','p','0')})",
            ("one_le_of_ne_zero", "zero_add", "mod_eq_refl"),
            ("intro b", "intro c", "intro u", "intro v", "intro p", "intro t", "intro hp", "intro hpull", "intro hmember", "cases hmember",
             f"have hz : {_lt('0','p')}", *_call("one_le_of_ne_zero","p"), "exact hp", "split", "exact hz",
             f"have he : {_iff(_at('u','v','0','1',tag='cd_norm_zero_target'),_at('b','c','t','1',tag='cd_norm_zero_source'))}", *_call("hpull","0","t"), "exact hz", "exact hmember_left",
             "have hzero : 0+t=t", *_call("zero_add","t"), "rewrite hzero", *_call("mod_eq_refl","p","t"), "cases he", "apply he_right", "exact hmember_right"),
            "Pulling back by an actual source member produces an actual set containing zero.",
        ),
        spec(
            "finite_modular_opposite_translates_sum_cover",
            f"forall b c d e ab ac bb bc sb sc p t v. ~(p=0) -> t+v=p -> ({_pullback('b','c','ab','ac','p','v')}) -> "
            f"({_pullback('d','e','bb','bc','p','t')}) -> ({_cover('b','c','d','e','sb','sc','p')}) -> ({_cover('ab','ac','bb','bc','sb','sc','p')})",
            ("finite_modular_pushforward_membership_witness", "finite_modular_pullback_membership_witness", "finite_modular_shifted_sum_congruence", "mod_eq_trans"),
            ("intro b", "intro c", "intro d", "intro e", "intro ab", "intro ac", "intro bb", "intro bc", "intro sb", "intro sc", "intro p", "intro t", "intro v", "intro hp", "intro htv", "intro hApull", "intro hBpull", "intro hcover",
             "intro a", "intro z", "intro w", "intro ha", "intro hz", "intro hw", "intro hA", "intro hB", "intro hmod",
             f"have hAiff : {_iff(_at('ab','ac','a','1',tag='cd_norm_A'),original_A)}", *_call("finite_modular_pushforward_membership_witness","b","c","ab","ac","p","t","v","a"), "exact hp", "exact htv", "exact hApull", "exact ha", "cases hAiff",
             f"have hBiff : {_iff(_at('bb','bc','z','1',tag='cd_norm_B'),original_B)}", *_call("finite_modular_pullback_membership_witness","d","e","bb","bc","p","t","z"), "exact hp", "exact hBpull", "exact hz", "cases hBiff",
             f"have hAsource : {original_A}", "apply hAiff_left", "exact hA", "cases hAsource", "cases hAsource_witness", "cases hAsource_witness_left",
             f"have hBsource : {original_B}", "apply hBiff_left", "exact hB", "cases hBsource", "cases hBsource_witness", "cases hBsource_witness_left",
             *_call("hcover","x","x1","w"), "exact hAsource_witness_left_left", "exact hBsource_witness_left_left", "exact hw", "exact hAsource_witness_left_right", "exact hBsource_witness_left_right",
             *_call("mod_eq_trans","p","x+x1","a+z","w"), *_call("finite_modular_shifted_sum_congruence","p","x","x1","a","z","t"), "exact hAsource_witness_right", "exact hBsource_witness_right", "exact hmod"),
            "Opposite actual translations of the input sets preserve every coded upper bound for their sumset.",
        ),
        spec(
            "prime_cauchy_davenport_cover_bound",
            f"{full_prefix}({_cover('b','c','d','e','sb','sc','p')}) -> ({_bound('p','k','l','m')})",
            ("prime_nonzero", "finite_bit_count_positive_member", "finite_modular_additive_complement", "finite_modular_set_pullback_exists", "prime_cauchy_davenport_normalized_cover_bound", "finite_modular_pullback_zero_member", "finite_modular_opposite_translates_sum_cover"),
            (*tuple(f"intro {name}" for name in variables+hypotheses),
             "have hpzero : ~(p=0)", "intro he", *_call("prime_nonzero","p"), "exact hprime", "exact he",
             f"have hmember : exists t. {_member('d','e','p','t')}", *_call("finite_bit_count_positive_member","d","e","p","l"), "exact hB", "exact hl", "cases hmember",
             "have hcomp : exists v. x+v=p", *_call("finite_modular_additive_complement","p","x"), "cases hmember_witness", "exact hmember_witness_left", "cases hcomp",
             f"have hAnorm : exists ab ac. ({_count('ab','ac','p','k')}) /\\ ({_pullback('b','c','ab','ac','p','x1')})", *_call("finite_modular_set_pullback_exists","b","c","p","k","x1"), "exact hpzero", "exact hA", "cases hAnorm", "cases hAnorm_witness", "cases hAnorm_witness_witness",
             f"have hBnorm : exists bb bc. ({_count('bb','bc','p','l')}) /\\ ({_pullback('d','e','bb','bc','p','x')})", *_call("finite_modular_set_pullback_exists","d","e","p","l","x"), "exact hpzero", "exact hB", "cases hBnorm", "cases hBnorm_witness", "cases hBnorm_witness_witness",
             *_call("prime_cauchy_davenport_normalized_cover_bound","p","x2","x3","x4","x5","sb","sc","k","l","m"), "exact hprime", "exact hAnorm_witness_witness_left", "exact hBnorm_witness_witness_left", "exact hS", "exact hk",
             *_call("finite_modular_pullback_zero_member","d","e","x4","x5","p","x"), "exact hpzero", "exact hBnorm_witness_witness_right", "exact hmember_witness",
             *_call("finite_modular_opposite_translates_sum_cover","b","c","d","e","x2","x3","x4","x5","sb","sc","p","x","x1"), "exact hpzero", "exact hcomp_witness", "exact hAnorm_witness_witness_right", "exact hBnorm_witness_witness_right", "exact hcover"),
            "Full Cauchy--Davenport for arbitrary nonempty prime-field characteristic sets, against every actual coded upper sumset.",
        ),
        spec(
            "prime_cauchy_davenport_sumset_bound",
            f"{full_prefix}({_sumset('b','c','d','e','sb','sc','p')}) -> ({_bound('p','k','l','m')})",
            ("prime_cauchy_davenport_cover_bound", "finite_modular_sumset_cover"),
            (*tuple(f"intro {name}" for name in variables+hypotheses[:-1]+("hsum",)), *_call("prime_cauchy_davenport_cover_bound",*variables),
             "exact hprime", "exact hA", "exact hB", "exact hS", "exact hk", "exact hl", *_call("finite_modular_sumset_cover","b","c","d","e","sb","sc","p"), "exact hsum"),
            "Exact campaign G051: every actual sumset of two nonempty finite prime-field sets satisfies m >= min(p,k+l-1), in subtraction-free HA form.",
        ),
        spec(
            "prime_cauchy_davenport_sumset_exists",
            f"forall p b c d e k l. ({prime('p',tag='cd_exist_prime')}) -> ({_count('b','c','p','k')}) -> ({_count('d','e','p','l')}) -> ~(k=0) -> ~(l=0) -> "
            f"exists sb sc m. ({_count('sb','sc','p','m')}) /\\ (({_sumset('b','c','d','e','sb','sc','p')}) /\\ ({_bound('p','k','l','m')}))",
            ("prime_nonzero", "finite_modular_sumset_exists", "prime_cauchy_davenport_sumset_bound"),
            ("intro p", "intro b", "intro c", "intro d", "intro e", "intro k", "intro l", "intro hprime", "intro hA", "intro hB", "intro hk", "intro hl",
             f"have hsum : exists sb sc m. ({_count('sb','sc','p','m')}) /\\ ({_sumset('b','c','d','e','sb','sc','p')})", *_call("finite_modular_sumset_exists","b","c","d","e","p","k","l"),
             "intro he", *_call("prime_nonzero","p"), "exact hprime", "exact he", "exact hA", "exact hB", "cases hsum", "cases hsum_witness", "cases hsum_witness_witness", "cases hsum_witness_witness_witness",
             "exists x", "exists x1", "exists x2", "split", "exact hsum_witness_witness_witness_left", "split", "exact hsum_witness_witness_witness_right",
             *_call("prime_cauchy_davenport_sumset_bound","p","b","c","d","e","x","x1","k","l","x2"), "exact hprime", "exact hA", "exact hB", "exact hsum_witness_witness_witness_left", "exact hk", "exact hl", "exact hsum_witness_witness_witness_right"),
            "Construct the actual canonical sumset and its exact cardinality together with the full sharp Cauchy--Davenport bound.",
        ),
    )


__all__ = [
    "CauchyDavenportError", "modular_translation_boundary_relation", "modular_dyson_transform_relation",
    "cauchy_davenport_bound_relation", "make_cauchy_davenport_candidate_theorems",
]
