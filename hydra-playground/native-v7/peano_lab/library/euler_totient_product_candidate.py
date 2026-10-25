"""Euler's product from actual complete prime-valuation support and unit counts.

EulerFactor(p,e,c) computes c=p^(e-1)*(p-1) with explicit predecessor and
power witnesses.  It does NOT mention Phi.  EulerProduct(n,t) uses the
independently constructed complete, distinct prime-valuation support and a
real beta-coded product of those factors.  The equality with Phi is a theorem.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from ..kernel.formulas import parse_formula_with_names
from .euler_totient_count_candidate import _call, _intro, _cop, _phi, _lt
from .euler_totient_prime_step_candidate import _prime
from .euler_totient_algebra_candidate import _pow
from .finite_fold_surface import _identifier
from .finite_sum_theorems import _at
from .foundation_saturation_candidate import _product, _factorization
from .prime_valuation_support_candidate import (
    _and, _parts, _part, _cases, _entries, _entry, _support, _injective, _rewrite, _preserve,
)


def _factor(p: str, e: str, c: str, tag: str) -> str:
    h,d,Q=(f"eutprod_{role}_{tag}" for role in ("prime_predecessor","exponent_predecessor","previous_power"))
    return _and(
        _prime(p,tag=tag+'_prime'), f"~(({e})=0)",
        f"exists {h} {d} {Q}. ({p})=S {h} /\\ (({e})=S {d} /\\ (({_pow(p,d,Q,tag=tag+'_power')}) /\\ ({c})={Q}*{h}))",
    )


def _factor_entry(pb: str, pc: str, eb: str, ec: str, fb: str, fc: str, i: str, p: str, e: str, c: str, tag: str) -> str:
    return _and(_at(pb,pc,i,p,tag=tag+'_prime'), _at(eb,ec,i,e,tag=tag+'_exponent'), _at(fb,fc,i,c,tag=tag+'_factor'), _factor(p,e,c,tag+'_arithmetic'))


def _factors(pb: str, pc: str, eb: str, ec: str, fb: str, fc: str, l: str, tag: str) -> str:
    i,p,e,c=(f"eutprod_{role}_{tag}" for role in ("index","prime","exponent","factor"))
    return f"forall {i}. ({_lt(i,l,tag=tag+'_bound')}) -> exists {p} {e} {c}. ({_factor_entry(pb,pc,eb,ec,fb,fc,i,p,e,c,tag)})"


def _euler(n: str, t: str, tag: str) -> str:
    pb,pc,eb,ec,vb,vc,l,fb,fc=(f"eutprod_{role}_{tag}" for role in ("prime_code","prime_scale","exponent_code","exponent_scale","power_code","power_scale","length","factor_code","factor_scale"))
    return f"exists {pb} {pc} {eb} {ec} {vb} {vc} {l} {fb} {fc}. " + _and(
        _support(n,pb,pc,eb,ec,vb,vc,l,tag+'_support'),
        _factors(pb,pc,eb,ec,fb,fc,l,tag+'_factors'), _product(fb,fc,l,t,tag+'_product'),
    )


def _checked(builder: Callable[..., str], arguments: tuple[str,...], tag: str) -> str:
    _identifier(tag,"totient Euler-product definition tag")
    for argument in arguments:
        _identifier(argument,"totient Euler-product definition argument")
    formula=builder(*arguments,tag)
    binders={name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.",formula) for name in clause.split()}
    if binders.intersection(arguments):
        raise ValueError("totient Euler-product definition binder captures an argument")
    _,free=parse_formula_with_names(formula)
    if set(free)!=set(arguments):
        raise ValueError("totient Euler-product definition has lost or introduced a parameter")
    return formula


def totient_prime_power_factor_relation(prime: str, exponent: str, factor: str, *, tag: str) -> str:
    """Compute p^(e-1)*(p-1) using positive prime/exponent and actual Pow witnesses."""
    return _checked(_factor,(prime,exponent,factor),tag)


def totient_euler_factor_prefix_relation(prime_code: str, prime_scale: str, exponent_code: str, exponent_scale: str, factor_code: str, factor_scale: str, length: str, *, tag: str) -> str:
    """A real beta list of Euler factors for the primes and exponents at the same indices."""
    return _checked(_factors,(prime_code,prime_scale,exponent_code,exponent_scale,factor_code,factor_scale,length),tag)


def totient_euler_product_relation(value: str, product: str, *, tag: str) -> str:
    """The actual Euler product over complete distinct positive prime valuations; independent of Phi."""
    return _checked(_euler,(value,product),tag)


def _pairs(b: str,c: str,l: str,tag: str) -> str:
    i,j,a,z=(f"eutprod_{role}_{tag}" for role in ("left_index","right_index","left_value","right_value"))
    return f"forall {i} {j} {a} {z}. ({_lt(i,l,tag=tag+'_left_bound')}) -> ({_lt(j,l,tag=tag+'_right_bound')}) -> " \
        f"({_at(b,c,i,a,tag=tag+'_left_at')}) -> ({_at(b,c,j,z,tag=tag+'_right_at')}) -> ~({i}={j}) -> ({_cop(a,z,tag=tag+'_coprime')})"


def _phi_prefix(vb: str,vc: str,fb: str,fc: str,l: str,tag: str) -> str:
    i,a,c=(f"eutprod_{role}_{tag}" for role in ("index","modulus","value"))
    return f"forall {i} {a} {c}. ({_lt(i,l,tag=tag+'_bound')}) -> ({_at(vb,vc,i,a,tag=tag+'_modulus')}) -> ({_at(fb,fc,i,c,tag=tag+'_value')}) -> ({_phi(a,c,tag=tag+'_phi')})"


def _factor_rows(spec: Callable[..., Any]) -> tuple[Any,...]:
    return (
        spec(
            "totient_euler_factor_exists",
            f"forall p e. ({_prime('p',tag='factor_exists_prime')}) -> ~(e=0) -> exists c. ({_factor('p','e','c','factor_exists')})",
            ("nonzero_is_succ", "prime_nonzero", "pow_exists"),
            (*_intro("p","e","hp","he"), "have hpred : exists h. p=S h", *_call("nonzero_is_succ","p"), "intro hz", *_call("prime_nonzero","p"), "exact hp", "exact hz", "cases hpred",
             "have hepred : exists d. e=S d", *_call("nonzero_is_succ","e"), "exact he", "cases hepred",
             f"have hQ : exists Q. {_pow('p','x1','Q',tag='factor_actual_power')}", *_call("pow_exists","p","x1"), "cases hQ",
             "exists x2*x", "split", "exact hp", "split", "exact he", "exists x", "exists x1", "exists x2", "split", "exact hpred_witness", "split", "exact hepred_witness", "split", "exact hQ_witness", "refl"),
            "Construct the arithmetic Euler factor from the actual prime and positive exponent, independently of any unit count.",
        ),
        spec(
            "totient_euler_factor_correct",
            f"forall p e P c. ({_pow('p','e','P',tag='factor_full_power')}) -> ({_factor('p','e','c','factor_given')}) -> ({_phi('P','c',tag='factor_correct')})",
            ("pow_successor_pair_mul", "totient_prime_power_successor_value", "totient_modulus_transport", "totient_value_transport", "mul_comm"),
            (*_intro("p","e","P","c","hP","hf"), *_parts("hf",3), *_cases("hf_right_right",3), *_parts("hf_right_right_witness_witness_witness",4),
             "have hPeq : P=x2*p", *_call("pow_successor_pair_mul","p","x1","e","x2","P"), "exact hf_right_right_witness_witness_witness_right_left",
             "exact hf_right_right_witness_witness_witness_right_right_left", "exact hP",
             *_call("totient_modulus_transport","x2*p","P","c"), "symm", "exact hPeq", *_call("totient_value_transport","x2*p","x*x2","c"),
             "trans x2*x", *_call("mul_comm","x","x2"), "symm", "exact hf_right_right_witness_witness_witness_right_right_right",
             *_call("totient_prime_power_successor_value","x1","p","x","x2"), "exact hf_left", "exact hf_right_right_witness_witness_witness_left", "exact hf_right_right_witness_witness_witness_right_right_left"),
            "The independently computed Euler factor equals the actual unit count of its prime power.",
        ),
        spec(
            "totient_euler_factor_functional",
            f"forall p e c C. ({_factor('p','e','c','factor_first')}) -> ({_factor('p','e','C','factor_second')}) -> c=C",
            ("pow_exists", "totient_euler_factor_correct", "totient_functional"),
            (*_intro("p","e","c","C","hc","hC"), f"have hP : exists P. {_pow('p','e','P',tag='factor_unique_power')}", *_call("pow_exists","p","e"), "cases hP",
             *_call("totient_functional","x","c","C"), *_call("totient_euler_factor_correct","p","e","x","c"), "exact hP_witness", "exact hc",
             *_call("totient_euler_factor_correct","p","e","x","C"), "exact hP_witness", "exact hC"),
            "Predecessor and beta-encoding choices cannot change the computed arithmetic Euler factor.",
        ),
        spec(
            "totient_prime_entries_decoded_power",
            f"forall n pb pc eb ec vb vc l i P. ({_entries('n','pb','pc','eb','ec','vb','vc','l','decoded_entries')}) -> ({_lt('i','l',tag='decoded_bound')}) -> "
            f"({_at('vb','vc','i','P',tag='decoded_value')}) -> exists p e. " + _and(
                _at('pb','pc','i','p',tag='decoded_prime'), _at('eb','ec','i','e',tag='decoded_exponent'), _prime('p',tag='decoded_domain'), "~(e=0)", _pow('p','e','P',tag='decoded_power'),
            ),
            ("beta_at_unique",),
            (*_intro("n","pb","pc","eb","ec","vb","vc","l","i","P","hentries","hi","hP"),
             f"have hrow : exists p e v. {_entry('n','pb','pc','eb','ec','vb','vc','i','p','e','v','decoded_actual_entry')}", "specialize hentries i", "apply hentries", "exact hi", *_cases("hrow",3), *_parts("hrow_witness_witness_witness",7),
             "have heq : x2=P", *_call("beta_at_unique","vb","vc","i","x2","P"), "exact "+_part("hrow_witness_witness_witness",7,2), "exact hP",
             "exists x", "exists x1", "split", "exact "+_part("hrow_witness_witness_witness",7,0), "split", "exact "+_part("hrow_witness_witness_witness",7,1),
             "split", "exact "+_part("hrow_witness_witness_witness",7,3), "split", "exact "+_part("hrow_witness_witness_witness",7,4),
             "rewrite heq at "+_part("hrow_witness_witness_witness",7,6), "rewrite heq at "+_part("hrow_witness_witness_witness",7,6), "exact "+_part("hrow_witness_witness_witness",7,6)),
            "Every actually decoded support power has its prime, positive exponent and genuine power witnesses at the same index.",
        ),
        spec(
            "totient_prime_entries_selected_power",
            f"forall n pb pc eb ec vb vc l i p e P. ({_entries('n','pb','pc','eb','ec','vb','vc','l','selected_entries')}) -> ({_lt('i','l',tag='selected_bound')}) -> "
            f"({_at('pb','pc','i','p',tag='selected_prime')}) -> ({_at('eb','ec','i','e',tag='selected_exponent')}) -> ({_at('vb','vc','i','P',tag='selected_value')}) -> ({_pow('p','e','P',tag='selected_power')})",
            ("totient_prime_entries_decoded_power", "beta_at_unique"),
            (*_intro("n","pb","pc","eb","ec","vb","vc","l","i","p","e","P","hentries","hi","hp","he","hP"),
             "have hrow : exists q d. "+_and(_at('pb','pc','i','q',tag='selected_actual_prime'), _at('eb','ec','i','d',tag='selected_actual_exponent'), _prime('q',tag='selected_actual_domain'), "~(d=0)", _pow('q','d','P',tag='selected_actual_power')),
             *_call("totient_prime_entries_decoded_power","n","pb","pc","eb","ec","vb","vc","l","i","P"), "exact hentries", "exact hi", "exact hP", *_cases("hrow",2), *_parts("hrow_witness_witness",5),
             "have hprime : x=p", *_call("beta_at_unique","pb","pc","i","x","p"), "exact "+_part("hrow_witness_witness",5,0), "exact hp",
             "have hexponent : x1=e", *_call("beta_at_unique","eb","ec","i","x1","e"), "exact "+_part("hrow_witness_witness",5,1), "exact he",
             *_rewrite("hprime",_pow('x','x1','P',tag='selected_rewrite'),"x",_part("hrow_witness_witness",5,4)),
             *_rewrite("hexponent",_pow('p','x1','P',tag='selected_rewrite'),"x1",_part("hrow_witness_witness",5,4)), "exact "+_part("hrow_witness_witness",5,4)),
            "The selected prime/exponent beta entries refer to the same actual power, not merely some unrelated factorization witnesses.",
        ),
        spec(
            "totient_prime_support_powers_pairwise_coprime",
            f"forall n pb pc eb ec vb vc l. ({_entries('n','pb','pc','eb','ec','vb','vc','l','pairs_entries')}) -> "
            f"({_injective('pb','pc','l','pairs_distinct')}) -> ({_pairs('vb','vc','l','pairs_result')})",
            ("totient_prime_entries_decoded_power", "coprime_powers", "distinct_primes_coprime"),
            (*_intro("n","pb","pc","eb","ec","vb","vc","l","hentries","hinjective","i","j","A","B","hi","hj","hA","hB","hne"),
             "have hfirst : exists p e. "+_and(_at('pb','pc','i','p',tag='pairs_first_prime'), _at('eb','ec','i','e',tag='pairs_first_exponent'), _prime('p',tag='pairs_first_domain'), "~(e=0)", _pow('p','e','A',tag='pairs_first_power')),
             *_call("totient_prime_entries_decoded_power","n","pb","pc","eb","ec","vb","vc","l","i","A"), "exact hentries", "exact hi", "exact hA", *_cases("hfirst",2), *_parts("hfirst_witness_witness",5),
             "have hsecond : exists q f. "+_and(_at('pb','pc','j','q',tag='pairs_second_prime'), _at('eb','ec','j','f',tag='pairs_second_exponent'), _prime('q',tag='pairs_second_domain'), "~(f=0)", _pow('q','f','B',tag='pairs_second_power')),
             *_call("totient_prime_entries_decoded_power","n","pb","pc","eb","ec","vb","vc","l","j","B"), "exact hentries", "exact hj", "exact hB", *_cases("hsecond",2), *_parts("hsecond_witness_witness",5),
             *_call("coprime_powers","x","x2","x1","x3","A","B"), *_call("distinct_primes_coprime","x","x2"), "exact "+_part("hfirst_witness_witness",5,2), "exact "+_part("hsecond_witness_witness",5,2),
             "intro heq", "apply hne", *_call("hinjective","i","j","x"), "exact hi", "exact hj", "exact "+_part("hfirst_witness_witness",5,0), "rewrite heq", "rewrite heq", "exact "+_part("hsecond_witness_witness",5,0),
             "exact "+_part("hfirst_witness_witness",5,4), "exact "+_part("hsecond_witness_witness",5,4)),
            "Distinct prime entries force their actual prime-power factors to be pairwise coprime; injectivity supplies the needed inequality witnesses.",
        ),
        spec(
            "totient_pairwise_coprime_product_fold",
            f"forall l vb vc fb fc N T. ({_pairs('vb','vc','l','fold_pairs')}) -> ({_phi_prefix('vb','vc','fb','fc','l','fold_values')}) -> "
            f"({_product('vb','vc','l','N','fold_modulus')}) -> ({_product('fb','fc','l','T','fold_product')}) -> ({_phi('N','T',tag='fold_result')})",
            ("beta_product_zero", "totient_modulus_transport", "totient_value_transport", "totient_one_value", "beta_product_succ_decompose", "crt_pairwise_coprime_prefix_drop_last", "le_succ", "le_refl",
             "totient_coprime_multiplicative", "crt_pairwise_coprime_prefix_product_coprime_last"),
            ("induction l", *_intro("vb","vc","fb","fc","N","T","hpairs","hvalues","hN","hT"),
             "have hNone : N=1", *_call("beta_product_zero","vb","vc","N"), "exact hN", "have hTone : T=1", *_call("beta_product_zero","fb","fc","T"), "exact hT",
             *_call("totient_modulus_transport","1","N","T"), "symm", "exact hNone", *_call("totient_value_transport","1","1","T"), "symm", "exact hTone", "exact totient_one_value",
             *_intro("vb","vc","fb","fc","N","T","hpairs","hvalues","hN","hT"),
             f"have hNd : exists A R. ({_at('vb','vc','l','A',tag='fold_last_modulus')}) /\\ (({_product('vb','vc','l','R','fold_previous_modulus')}) /\\ N=R*A)",
             *_call("beta_product_succ_decompose","vb","vc","l","N"), "exact hN", *_cases("hNd",2), *_parts("hNd_witness_witness",3),
             f"have hTd : exists B s. ({_at('fb','fc','l','B',tag='fold_last_value')}) /\\ (({_product('fb','fc','l','s','fold_previous_value')}) /\\ T=s*B)",
             *_call("beta_product_succ_decompose","fb","fc","l","T"), "exact hT", *_cases("hTd",2), *_parts("hTd_witness_witness",3),
             f"have hpre : {_phi('x1','x3',tag='fold_previous_phi')}", *_call("IH","vb","vc","fb","fc","x1","x3"), *_call("crt_pairwise_coprime_prefix_drop_last","vb","vc","l"), "exact hpairs",
             *_intro("i","a","c","hi","ha","hc"), *_call("hvalues","i","a","c"), *_call("le_succ","S i","l"), "exact hi", "exact ha", "exact hc",
             "exact hNd_witness_witness_right_left", "exact hTd_witness_witness_right_left",
             *_call("totient_modulus_transport","x1*x","N","T"), "symm", "exact hNd_witness_witness_right_right", *_call("totient_value_transport","x1*x","x3*x2","T"), "symm", "exact hTd_witness_witness_right_right",
             *_call("totient_coprime_multiplicative","x1","x","x3","x2"), "exact hpre", *_call("hvalues","l","x","x2"), *_call("le_refl","S l"), "exact hNd_witness_witness_left", "exact hTd_witness_witness_left",
             *_call("crt_pairwise_coprime_prefix_product_coprime_last","vb","vc","l","x1","x"), "exact hpairs", "exact hNd_witness_witness_right_left", "exact hNd_witness_witness_left"),
            "Actual beta products of pairwise coprime moduli multiply their actual totient counts, including the empty product one.",
        ),
    )


def _prefix_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "totient_euler_factor_prefix_empty",
            f"forall pb pc eb ec fb fc. {_factors('pb','pc','eb','ec','fb','fc','0','factors_empty')}",
            ("lt_not_le", "zero_le"),
            (*_intro("pb","pc","eb","ec","fb","fc","i","hi"), "exfalso", *_call("lt_not_le","i","0"), "exact hi", *_call("zero_le","i")),
            "The empty actual Euler-factor list has no entries or artificial zero-exponent factors.",
        ),
        spec(
            "totient_euler_factor_prefix_drop_last",
            f"forall pb pc eb ec fb fc l. ({_factors('pb','pc','eb','ec','fb','fc','S l','factors_full')}) -> ({_factors('pb','pc','eb','ec','fb','fc','l','factors_prefix')})",
            ("le_succ",),
            (*_intro("pb","pc","eb","ec","fb","fc","l","h","i","hi"), "specialize h i", "apply h", *_call("le_succ","S i","l"), "exact hi"),
            "A prefix retains all actual prime, exponent, factor, and preceding-power witnesses.",
        ),
        spec(
            "totient_euler_factor_prefix_append",
            f"forall pb pc eb ec fb fc l p e C. ({_factors('pb','pc','eb','ec','fb','fc','l','append_prefix')}) -> ({_at('pb','pc','l','p',tag='append_prime')}) -> "
            f"({_at('eb','ec','l','e',tag='append_exponent')}) -> ({_factor('p','e','C','append_arithmetic')}) -> exists d f. ({_factors('pb','pc','eb','ec','d','f','S l','append_result')})",
            ("beta_prefix_extend", "le_eq_or_lt", "le_of_succ_le_succ"),
            (*_intro("pb","pc","eb","ec","fb","fc","l","p","e","C","hprefix","hp","he","hC"),
             f"have hext : exists d f. ({_at('d','f','l','C',tag='append_last_factor')}) /\\ ({_preserve('fb','fc','d','f','l','append_preserved')})",
             *_call("beta_prefix_extend","l","fb","fc","C"), *_cases("hext",2), "cases hext_witness_witness", "exists x", "exists x1", *_intro("i","hi"),
             "have hcases : i=l \\/ exists g. g+S i=l", *_call("le_eq_or_lt","i","l"), *_call("le_of_succ_le_succ","i","l"), "exact hi", "cases hcases",
             "exists p", "exists e", "exists C", "split", "rewrite hcases_left", "rewrite hcases_left", "exact hp", "split", "rewrite hcases_left", "rewrite hcases_left", "exact he",
             "split", "rewrite hcases_left", "rewrite hcases_left", "exact hext_witness_witness_left", "exact hC",
             f"have hrow : exists q d D. {_factor_entry('pb','pc','eb','ec','fb','fc','i','q','d','D','append_old_row')}", "specialize hprefix i", "apply hprefix", "exact hcases_right", *_cases("hrow",3), *_parts("hrow_witness_witness_witness",4),
             "exists x2", "exists x3", "exists x4", "split", "exact "+_part("hrow_witness_witness_witness",4,0), "split", "exact "+_part("hrow_witness_witness_witness",4,1),
             "split", *_call("hext_witness_witness_right","i","x4"), "exact hcases_right", "exact "+_part("hrow_witness_witness_witness",4,2), "exact "+_part("hrow_witness_witness_witness",4,3)),
            "Actually append the computed Euler factor while preserving every earlier beta-decoded value and its arithmetic witnesses.",
        ),
        spec(
            "totient_euler_factor_prefix_exists",
            f"forall l n pb pc eb ec vb vc. ({_entries('n','pb','pc','eb','ec','vb','vc','l','prefix_source')}) -> "
            f"exists fb fc. ({_factors('pb','pc','eb','ec','fb','fc','l','prefix_exists')})",
            ("totient_euler_factor_prefix_empty", "totient_euler_factor_prefix_append", "totient_euler_factor_exists", "le_succ", "le_refl"),
            ("induction l", *_intro("n","pb","pc","eb","ec","vb","vc","hentries"), "exists 0", "exists 0", *_call("totient_euler_factor_prefix_empty","pb","pc","eb","ec","0","0"),
             *_intro("n","pb","pc","eb","ec","vb","vc","hentries"), f"have hprefix : exists fb fc. {_factors('pb','pc','eb','ec','fb','fc','l','prefix_previous')}",
             *_call("IH","n","pb","pc","eb","ec","vb","vc"), *_intro("i","hi"), "specialize hentries i", "apply hentries", *_call("le_succ","S i","l"), "exact hi", *_cases("hprefix",2),
             f"have hrow : exists p e P. {_entry('n','pb','pc','eb','ec','vb','vc','l','p','e','P','prefix_last_support')}", "specialize hentries l", "apply hentries", *_call("le_refl","S l"), *_cases("hrow",3), *_parts("hrow_witness_witness_witness",7),
             f"have hfactor : exists C. {_factor('x2','x3','C','prefix_last_arithmetic')}", *_call("totient_euler_factor_exists","x2","x3"),
             "exact "+_part("hrow_witness_witness_witness",7,3), "exact "+_part("hrow_witness_witness_witness",7,4), "cases hfactor",
             *_call("totient_euler_factor_prefix_append","pb","pc","eb","ec","x","x1","l","x2","x3","x5"), "exact hprefix_witness_witness",
             "exact "+_part("hrow_witness_witness_witness",7,0), "exact "+_part("hrow_witness_witness_witness",7,1), "exact hfactor_witness"),
            "HA induction constructs the full beta-coded list of p^(e-1)*(p-1) from actual positive prime-valuation entries.",
        ),
        spec(
            "totient_euler_factor_prefix_counts",
            f"forall n pb pc eb ec vb vc fb fc l. ({_entries('n','pb','pc','eb','ec','vb','vc','l','counts_support')}) -> "
            f"({_factors('pb','pc','eb','ec','fb','fc','l','counts_factors')}) -> ({_phi_prefix('vb','vc','fb','fc','l','counts_result')})",
            ("totient_prime_entries_selected_power", "beta_at_unique", "totient_euler_factor_correct"),
            (*_intro("n","pb","pc","eb","ec","vb","vc","fb","fc","l","hentries","hfactors","i","P","C","hi","hP","hC"),
             f"have hrow : exists p e c. {_factor_entry('pb','pc','eb','ec','fb','fc','i','p','e','c','counts_actual_row')}", "specialize hfactors i", "apply hfactors", "exact hi", *_cases("hrow",3), *_parts("hrow_witness_witness_witness",4),
             "have heq : x2=C", *_call("beta_at_unique","fb","fc","i","x2","C"), "exact "+_part("hrow_witness_witness_witness",4,2), "exact hC",
             *_call("totient_euler_factor_correct","x","x1","P","C"), *_call("totient_prime_entries_selected_power","n","pb","pc","eb","ec","vb","vc","l","i","x","x1","P"),
             "exact hentries", "exact hi", "exact "+_part("hrow_witness_witness_witness",4,0), "exact "+_part("hrow_witness_witness_witness",4,1), "exact hP",
             "rewrite heq at "+_part("hrow_witness_witness_witness",4,3), "exact "+_part("hrow_witness_witness_witness",4,3)),
            "The factor and support lists share the very same decoded prime and exponent at each index, so each Euler factor is the actual totient of its power.",
        ),
        spec(
            "totient_euler_product_from_support",
            f"forall n pb pc eb ec vb vc l fb fc t. ({_support('n','pb','pc','eb','ec','vb','vc','l','product_support')}) -> "
            f"({_factors('pb','pc','eb','ec','fb','fc','l','product_factors')}) -> ({_product('fb','fc','l','t','product_actual')}) -> ({_phi('n','t',tag='product_totient')})",
            ("totient_prime_support_powers_pairwise_coprime", "totient_euler_factor_prefix_counts", "totient_pairwise_coprime_product_fold"),
            (*_intro("n","pb","pc","eb","ec","vb","vc","l","fb","fc","t","hsupport","hfactors","ht"), *_parts("hsupport",5),
             *_call("totient_pairwise_coprime_product_fold","l","vb","vc","fb","fc","n","t"), *_call("totient_prime_support_powers_pairwise_coprime","n","pb","pc","eb","ec","vb","vc","l"),
             "exact "+_part("hsupport",5,2), "exact "+_part("hsupport",5,1), *_call("totient_euler_factor_prefix_counts","n","pb","pc","eb","ec","vb","vc","fb","fc","l"),
             "exact "+_part("hsupport",5,2), "exact hfactors", "exact "+_part("hsupport",5,4), "exact ht"),
            "The actual Euler-factor product over complete distinct prime-valuation support equals the independently defined unit count of n.",
        ),
    )


def _root_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "totient_euler_product_correct",
            f"forall n t. ({_euler('n','t','correct_product')}) -> ({_phi('n','t',tag='correct_count')})",
            ("totient_euler_product_from_support",),
            (*_intro("n","t","h"), *_cases("h",9), *_parts("h"+"_witness"*9,3),
             *_call("totient_euler_product_from_support","n","x","x1","x2","x3","x4","x5","x6","x7","x8","t"),
             "exact "+_part("h"+"_witness"*9,3,0), "exact "+_part("h"+"_witness"*9,3,1), "exact "+_part("h"+"_witness"*9,3,2)),
            "Every genuine complete Euler product computes Phi; this is proved, not stipulated in either definition.",
        ),
        spec(
            "totient_euler_product_exists",
            f"forall n. ~(n=0) -> exists t. ({_euler('n','t','exists_product')})",
            ("prime_valuation_support_exists", "totient_euler_factor_prefix_exists", "beta_product_exists"),
            (*_intro("n","hn"), f"have hs : exists pb pc eb ec vb vc l. {_support('n','pb','pc','eb','ec','vb','vc','l','exists_support')}", *_call("prime_valuation_support_exists","n"), "exact hn", *_cases("hs",7),
             f"have hf : exists fb fc. {_factors('x','x1','x2','x3','fb','fc','x6','exists_factors')}", *_call("totient_euler_factor_prefix_exists","x6","n","x","x1","x2","x3","x4","x5"),
             *_parts("hs"+"_witness"*7,5), "exact "+_part("hs"+"_witness"*7,5,2), *_cases("hf",2),
             f"have ht : exists t. {_product('x7','x8','x6','t','exists_actual_product')}", *_call("beta_product_exists","x7","x8","x6"), "cases ht",
             "exists x9", *("exists "+name for name in ("x","x1","x2","x3","x4","x5","x6","x7","x8")), "split", "exact hs"+"_witness"*7,
             "split", "exact hf_witness_witness", "exact ht_witness"),
            "For every positive n construct complete distinct valuation support, every preceding power and Euler factor, and their actual finite product.",
        ),
        spec(
            "totient_euler_product_functional",
            f"forall n t u. ({_euler('n','t','functional_first')}) -> ({_euler('n','u','functional_second')}) -> t=u",
            ("totient_euler_product_correct", "totient_functional"),
            (*_intro("n","t","u","ht","hu"), *_call("totient_functional","n","t","u"), *_call("totient_euler_product_correct","n","t"), "exact ht", *_call("totient_euler_product_correct","n","u"), "exact hu"),
            "Changing the complete support ordering or any beta code cannot change the Euler-product value.",
        ),
        spec(
            "totient_euler_product_from_count",
            f"forall n t. ({_phi('n','t',tag='count_given')}) -> ({_euler('n','t','count_product')})",
            ("totient_euler_product_exists", "totient_euler_product_correct", "totient_functional"),
            (*_intro("n","t","ht"), f"have heuler : exists u. {_euler('n','u','count_actual_product')}", *_call("totient_euler_product_exists","n"), "cases ht", "exact ht_left", "cases heuler",
             "have heq : x=t", *_call("totient_functional","n","x","t"), *_call("totient_euler_product_correct","n","x"), "exact heuler_witness", "exact ht",
             "rewrite heq at heuler_witness", "rewrite heq at heuler_witness", "exact heuler_witness"),
            "Every actual totient count has a fully constructed complete prime-support Euler product with that exact value.",
        ),
        spec(
            "totient_euler_product_iff",
            f"forall n t. (({_phi('n','t',tag='iff_count_forward')}) -> ({_euler('n','t','iff_product_forward')})) /\\ "
            f"(({_euler('n','t','iff_product_backward')}) -> ({_phi('n','t',tag='iff_count_backward')}))",
            ("totient_euler_product_from_count", "totient_euler_product_correct"),
            (*_intro("n","t"), "split", "intro h", *_call("totient_euler_product_from_count","n","t"), "exact h", "intro h", *_call("totient_euler_product_correct","n","t"), "exact h"),
            "The independently defined actual unit count and complete prime-support Euler product are equivalent on precisely the positive domain.",
        ),
        spec(
            "totient_euler_product_one",
            _euler('1','1','unit_euler_product'),
            ("prime_valuation_support_one", "totient_euler_factor_prefix_empty"),
            (*( "exists 0" for _ in range(9)), "split", "exact prime_valuation_support_one", "split",
             *_call("totient_euler_factor_prefix_empty","0","0","0","0","0","0"), *_parts("prime_valuation_support_one",5), "exact "+_part("prime_valuation_support_one",5,4)),
            "At n=1 construct the genuinely empty prime support and empty Euler-factor product one, with every list code explicitly zero.",
        ),
        spec(
            "totient_euler_product_zero_excluded",
            f"forall t. ~({_euler('0','t','zero_euler_product')})",
            ("totient_euler_product_correct", "totient_zero_excluded"),
            (*_intro("t","h"), *_call("totient_zero_excluded","t"), *_call("totient_euler_product_correct","0","t"), "exact h"),
            "The Euler product preserves the positive domain: no finite complete-support product is fabricated for zero.",
        ),
        spec(
            "totient_euler_product_formula",
            f"forall n. ~(n=0) -> exists f g l t. ({_factorization('n','f','g','l','formula_prime_list')}) /\\ "
            f"(({_phi('n','t',tag='formula_actual_count')}) /\\ ({_euler('n','t','formula_euler_product')}))",
            ("foundation_prime_factor_list_exists", "totient_euler_product_exists", "totient_euler_product_correct"),
            (*_intro("n","hn"), f"have hlist : exists l f g. {_factorization('n','f','g','l','formula_actual_list')}", *_call("foundation_prime_factor_list_exists","n"), "exact hn", *_cases("hlist",3),
             f"have hproduct : exists t. {_euler('n','t','formula_actual_euler')}", *_call("totient_euler_product_exists","n"), "exact hn", "cases hproduct",
             "exists x1", "exists x2", "exists x", "exists x3", "split", "exact hlist_witness_witness_witness", "split", *_call("totient_euler_product_correct","n","x3"), "exact hproduct_witness", "exact hproduct_witness"),
            "G006: for every positive n construct an actual prime factorization, the actual unit count, and its equal product of p^(Val(p,n)-1)*(p-1) over every distinct prime divisor; n=1 gives the empty product one.",
        ),
    )


def make_euler_totient_product_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_factor_rows(spec), *_prefix_rows(spec), *_root_rows(spec))


__all__ = ["totient_prime_power_factor_relation", "totient_euler_factor_prefix_relation", "totient_euler_product_relation", "make_euler_totient_product_candidate_theorems"]
