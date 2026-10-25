"""Exact constructive foundation endpoints over the immutable Alpha-v27 core.

These ordinary HA wrappers expose already checked division, signed Bezout,
coprime cancellation, actual prime-factor-list existence, and prime
unboundedness.  The factor-list relation deliberately does not require sorted
entries: unordered uniqueness requires the separate witnessed-permutation
development, not the historical canonical-list equality theorem alone.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .fermat_residue_product_candidate import coprime
from .fermat_two_squares_factor_fold_candidate import all_prime_factor_prefix
from .finite_fold_surface import _identifier, _product_relation_term
from .ha_canonical_gcd_candidate import is_gcd
from .ha_signed_bezout_candidate import signed_bezout


def _arguments(*values: str) -> tuple[str, ...]:
    result = tuple(_identifier(value, "foundation relation argument") for value in values)
    if any(value.startswith(("fsat_", "ff_", "ftsf_", "frm_")) for value in result):
        raise ValueError("generated foundation binder captures an argument")
    return result


def _lt(left: str, right: str, tag: str) -> str:
    return f"exists fsat_gap_{tag}. fsat_gap_{tag} + S ({left}) = ({right})"


def _product(code: str, scale: str, length: str, value: str, tag: str) -> str:
    return _product_relation_term(code, scale, length, value, tag=f"fsat_{tag}", avoid=())


def _allprime(code: str, scale: str, length: str, tag: str) -> str:
    return all_prime_factor_prefix(code, scale, length, tag=f"fsat_{tag}")


def _factorization(n: str, b: str, c: str, l: str, tag: str) -> str:
    return (
        f"(~({n} = 0) /\\ (({_product(b,c,l,n,tag+'_product')}) /\\ "
        f"({_allprime(b,c,l,tag+'_primes')})))"
    )


def prime_factor_list_relation(value: str, code: str, scale: str, length: str, *, tag: str) -> str:
    """Positive n, an actual beta-coded product n, and prime entries; no sorting."""
    return _factorization(*_arguments(value,code,scale,length),_identifier(tag,"foundation binder tag"))


def _divrem(n: str, d: str, q: str, r: str, tag: str) -> str:
    return f"({n} = {d} * {q} + {r} /\\ ({_lt(r,d,tag)}))"


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} ({value})" for value in arguments)+(f"apply {name}",)


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def make_foundation_saturation_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    """Return additive original-kernel proof bodies, not admission records."""
    return (
        spec(
            "foundation_division_exists_unique",
            f"forall n d. ~(d = 0) -> exists q r. (({_divrem('n','d','q','r','chosen')}) /\\ "
            f"forall u v. ({_divrem('n','d','u','v','other')}) -> u = q /\\ v = r)",
            ("division_remainder_exists","division_remainder_unique"),
            _intro("n","d","hd")
            +(f"have hdivision : exists q r. {_divrem('n','d','q','r','exists')}",)
            +_call("division_remainder_exists","d","n")+("exact hd","cases hdivision","cases hdivision_witness","exists x","exists x1","split","exact hdivision_witness_witness")
            +_intro("u","v","hother")+("cases hdivision_witness_witness","cases hother")
            +_call("division_remainder_unique","d","n","u","v","x","x1")
            +("exact hother_left","exact hother_right","exact hdivision_witness_witness_left","exact hdivision_witness_witness_right"),
            "G001: construct the quotient and strict remainder for every nonzero divisor and prove the pair is literally unique.",
        ),
        spec(
            "foundation_signed_bezout_canonical_gcd",
            f"forall a b. exists g u v. (({is_gcd('g','a','b',tag='fsat_gcd')}) /\\ "
            f"(({signed_bezout('g','a','b','u','v',tag='fsat_bezout')}) /\\ "
            f"forall h. ({is_gcd('h','a','b',tag='fsat_comparison')}) -> h = g))",
            ("gcd_signed_bezout_exists","is_gcd_unique"),
            _intro("a","b")+("specialize gcd_signed_bezout_exists a","specialize gcd_signed_bezout_exists b","cases gcd_signed_bezout_exists","cases gcd_signed_bezout_exists_witness","cases gcd_signed_bezout_exists_witness_witness","cases gcd_signed_bezout_exists_witness_witness_witness","exists x","exists x1","exists x2","split","exact gcd_signed_bezout_exists_witness_witness_witness_left","split","exact gcd_signed_bezout_exists_witness_witness_witness_right")
            +_intro("h","hh")+_call("is_gcd_unique","h","x","a","b")+("exact hh","exact gcd_signed_bezout_exists_witness_witness_witness_left"),
            "G002: every pair, including (0,0), has a canonical gcd value and actual signed-natural Bezout coefficient codes. Only the gcd is asserted unique, not its coefficients.",
        ),
        spec(
            "foundation_coprime_product_divisor",
            f"forall a b c. (({coprime('a','b',tag='fsat_euclid')}) /\\ (exists q. b * c = a * q)) -> exists q. c = a * q",
            ("gauss_coprime_cancel",),
            _intro("a","b","c","h")+("cases h",)+_call("gauss_coprime_cancel","a","b","c")+("exact h_left","exact h_right"),
            "G003: coprimality and a witnessed divisor of the product construct an actual quotient of the other factor, with no positivity premise added.",
        ),
        spec(
            "foundation_prime_factor_list_exists",
            f"forall n. ~(n = 0) -> exists l b c. ({_factorization('n','b','c','l','exists')})",
            ("prime_factorization_existence",),
            _intro("n","hn")+("specialize prime_factorization_existence n","have hexists : "+
                "exists l b c. (("+_product("b","c","l","n","canonical_product")+") /\\ (("+_allprime("b","c","l","canonical_primes")+") /\\ "+
                "(forall i. (exists h. h + S (S i) = l) -> exists p q. "+
                "(((exists h. h + S p = S ((S i) * c)) /\\ exists w. b = w * S ((S i) * c) + p) /\\ "+
                "((((exists h. h + S q = S ((S (S i)) * c)) /\\ exists w. b = w * S ((S (S i)) * c) + q)) /\\ (exists h. h + p = q))))))",
                "apply prime_factorization_existence","exact hn","cases hexists","cases hexists_witness","cases hexists_witness_witness","cases hexists_witness_witness_witness","cases hexists_witness_witness_witness_right","exists x","exists x1","exists x2","split","exact hn","split","exact hexists_witness_witness_witness_left","exact hexists_witness_witness_witness_right_left"),
            "G004: every positive natural has a genuinely constructed finite beta-coded prime-factor list and actual product trace; the existing sorted construction is used only to obtain witnesses, not required as a premise.",
        ),
        spec(
            "foundation_primes_above_every_bound",
            f"forall B. exists p. (({prime('p',tag='fsat_unbounded')}) /\\ ({_lt('B','p','unbounded')}))",
            ("prime_unbounded",),
            _intro("B")+("specialize prime_unbounded B","cases prime_unbounded","cases prime_unbounded_witness","exists x","split","exact prime_unbounded_witness_right","exact prime_unbounded_witness_left"),
            "G021: every supplied natural bound has an actual larger prime; no nonempty list or prime-search witness is supplied.",
        ),
    )


__all__ = ["prime_factor_list_relation","make_foundation_saturation_candidate_theorems"]
