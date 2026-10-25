"""Unordered prime-factor uniqueness with actual beta-coded bijections.

Lists are arbitrary prime prefixes with actual finite product traces.  The
permutation witness is a real decoded index map, bounded, injective,
surjective, and matching each source factor to its target occurrence.  No
sortedness or supplied canonicalization is included in the factor predicate.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .finite_fold_surface import _beta_at_term, _identifier
from .foundation_saturation_candidate import _allprime, _factorization, _product


def _safe(tag: str) -> str:
    return _identifier(tag,"factor-permutation binder tag")


def _arguments(*arguments: str) -> tuple[str,...]:
    values=tuple(_identifier(value,"factor-permutation argument") for value in arguments)
    if any(value.startswith(("pfp_","fsat_","ff_","fp_","frm_","ftsf_")) for value in values):
        raise ValueError("generated factor-permutation binder captures an argument")
    return values


def _and(*formulas: str) -> str:
    return formulas[0] if len(formulas)==1 else f"(({formulas[0]}) /\\ ({_and(*formulas[1:])}))"


def _lt(a: str, b: str, tag: str) -> str:
    return f"exists pfp_gap_{tag}. pfp_gap_{tag} + S ({a}) = ({b})"


def _at(b: str, c: str, i: str, a: str, tag: str) -> str:
    return _beta_at_term(b,c,i,a,tag=f"pfp_{tag}",avoid=())


def _preserve(b: str,c: str,d: str,e: str,l: str,tag: str) -> str:
    i,a=f"pfp_i_{tag}",f"pfp_a_{tag}"
    return f"forall {i} {a}. ({_lt(i,l,tag+'bound')}) -> ({_at(b,c,i,a,tag+'old')}) -> ({_at(d,e,i,a,tag+'new')})"


def _bounded(b: str,c: str,l: str,tag: str) -> str:
    i,a=f"pfp_i_{tag}",f"pfp_a_{tag}"
    return f"forall {i}. ({_lt(i,l,tag+'index')}) -> exists {a}. ({_at(b,c,i,a,tag+'entry')}) /\\ ({_lt(a,l,tag+'value')})"


def _injective(b: str,c: str,l: str,tag: str) -> str:
    i,j,a=(f"pfp_{role}_{tag}" for role in ("i","j","a"))
    return f"forall {i} {j} {a}. ({_lt(i,l,tag+'first')}) -> ({_lt(j,l,tag+'second')}) -> ({_at(b,c,i,a,tag+'left')}) -> ({_at(b,c,j,a,tag+'right')}) -> {i} = {j}"


def _surjective(b: str,c: str,l: str,tag: str) -> str:
    a,i=f"pfp_a_{tag}",f"pfp_i_{tag}"
    return f"forall {a}. ({_lt(a,l,tag+'value')}) -> exists {i}. ({_lt(i,l,tag+'index')}) /\\ ({_at(b,c,i,a,tag+'entry')})"


def _permutation(b: str,c: str,l: str,tag: str) -> str:
    return _and(_bounded(b,c,l,tag+'bounded'),_injective(b,c,l,tag+'injective'),_surjective(b,c,l,tag+'surjective'))


def _matching(b: str,c: str,d: str,e: str,u: str,v: str,l: str,tag: str) -> str:
    i,j,a=(f"pfp_{role}_{tag}" for role in ("i","j","a"))
    return (
        f"forall {i} {j} {a}. ({_lt(i,l,tag+'bound')}) -> ({_at(u,v,i,j,tag+'map')}) -> "
        f"({_at(b,c,i,a,tag+'source')}) -> ({_at(d,e,j,a,tag+'target')})"
    )


def _matched(b: str,c: str,d: str,e: str,u: str,v: str,l: str,tag: str) -> str:
    return _and(_permutation(u,v,l,tag+'permutation'),_matching(b,c,d,e,u,v,l,tag+'matching'))


def factor_list_matching_relation(b: str,c: str,d: str,e: str,u: str,v: str,l: str,*,tag: str) -> str:
    """Every actual source factor agrees with the factor at its decoded image."""
    return _matching(*_arguments(b,c,d,e,u,v,l),_safe(tag))


def prime_factor_list_permutation_relation(b: str,c: str,l: str,d: str,e: str,m: str,u: str,v: str,*,tag: str) -> str:
    """Equal lengths and an actual matching bounded/injective/surjective beta map."""
    b,c,l,d,e,m,u,v=_arguments(b,c,l,d,e,m,u,v)
    return _and(f"{l} = {m}",_matched(b,c,d,e,u,v,l,_safe(tag)))


def _extension(b: str,c: str,d: str,e: str,l: str,tag: str) -> str:
    return _and(_at(d,e,l,l,tag+'last'),_preserve(b,c,d,e,l,tag+'prefix'))


def _swap(b: str,c: str,d: str,e: str,l: str,i: str,p: str,q: str,tag: str) -> str:
    j,a=f"pfp_j_{tag}",f"pfp_a_{tag}"
    preserve=(f"forall {j} {a}. ({_lt(j,f'S ({l})',tag+'bound')}) -> ~({j} = {i}) -> ~({j} = {l}) -> "
              f"({_at(b,c,j,a,tag+'old')}) -> ({_at(d,e,j,a,tag+'new')})")
    return _and(_at(b,c,i,p,tag+'oldi'),_at(b,c,l,q,tag+'oldlast'),_at(d,e,i,q,tag+'newi'),_at(d,e,l,p,tag+'newlast'),preserve)


def _call(name: str,*terms: str) -> tuple[str,...]:
    return tuple(f"specialize {name} ({term})" for term in terms)+(f"apply {name}",)


def _intro(*names: str) -> tuple[str,...]:
    return tuple(f"intro {name}" for name in names)


def _cases(name: str,count: int) -> tuple[str,...]:
    return tuple("cases "+name+"_witness"*i for i in range(count))


def _parts(name: str,count: int) -> tuple[str,...]:
    return tuple("cases "+name+"_right"*i for i in range(count-1))


def _part(name: str,count: int,index: int) -> str:
    return name+"_right"*index+("_left" if index<count-1 else "")


def _rewrite(equation: str,formula: str,variable: str,at: str|None=None) -> tuple[str,...]:
    count=len(re.findall(rf"\b{re.escape(variable)}\b",formula))
    return (f"rewrite {equation}"+(f" at {at}" if at else ""),)*count


def _basic_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "factor_permutation_below_zero_impossible",
            f"forall i. ({_lt('i','0','empty')}) -> false",
            ("le_zero",),
            _intro("i","hi")+("apply PA1",)+_call("le_zero","S i")+("exact hi",),
            "There is no natural index below zero; empty list and permutation contracts are genuinely vacuous.",
        ),
        spec(
            "factor_permutation_prefix_reflect",
            f"forall b c d e l i a. ({_preserve('b','c','d','e','l','reflect')}) -> ({_lt('i','l','reflect_index')}) -> ({_at('d','e','i','a','reflect_new')}) -> ({_at('b','c','i','a','reflect_old')})",
            ("beta_at_exists","beta_at_unique"),
            _intro("b","c","d","e","l","i","a","hp","hi","hnew")
            +(f"have hold : exists z. ({_at('b','c','i','z','reflect_witness')})",)+_call("beta_at_exists","b","c","i")+("cases hold",)
            +(f"have hmoved : {_at('d','e','i','x','reflect_moved')}",)+_call("hp","i","x")+("exact hi","exact hold_witness",)
            +("have heq : a = x",)+_call("beta_at_unique","d","e","i","a","x")+("exact hnew","exact hmoved")
            +_rewrite("heq",_at('b','c','i','a','reflect_goal'),'a')+("exact hold_witness",),
            "Actual beta functionality turns a finite forward entry preservation into reverse preservation at every original index.",
        ),
        spec(
            "factor_permutation_all_prime_entry",
            f"forall b c l i p. ({_allprime('b','c','l','entry_primes')}) -> ({_lt('i','l','entry_bound')}) -> ({_at('b','c','i','p','entry')}) -> ({prime('p',tag='pfp_entry_prime')})",
            ("beta_at_unique",),
            _intro("b","c","l","i","p","hprimes","hi","hp")
            +(f"have hex : exists q. ({_at('b','c','i','q','entry_chosen')}) /\\ ({prime('q',tag='pfp_entry_chosen_prime')})",)
            +_call("hprimes","i")+("exact hi","cases hex","cases hex_witness","have heq : p = x")
            +_call("beta_at_unique","b","c","i","p","x")+("exact hp","exact hex_witness_left")
            +_rewrite("heq",prime('p',tag='pfp_entry_final'),'p')+("exact hex_witness_right",),
            "Every actual decoded entry of an all-prime prefix is prime, without a supplied choice of matching factor.",
        ),
        spec(
            "factor_permutation_product_exists",
            f"forall b c l. exists n. ({_product('b','c','l','n','product_exists')})",
            ("beta_product_exists_unique",),
            _intro("b","c","l")+("specialize beta_product_exists_unique b","specialize beta_product_exists_unique c","specialize beta_product_exists_unique l","cases beta_product_exists_unique","cases beta_product_exists_unique_witness","exists x","exact beta_product_exists_unique_witness_left"),
            "Construct an actual product value and trace for every finite beta prefix, including empty prefixes.",
        ),
        spec(
            "factor_permutation_cancel_last",
            f"forall n p r b c l. ({_factorization('n','b','c','S l','cancel_full')}) -> ({_at('b','c','l','p','cancel_last')}) -> n = r * p -> ({_factorization('r','b','c','l','cancel_prefix')})",
            ("beta_product_succ_decompose","beta_at_unique","factor_permutation_all_prime_entry","prime_nonzero","mul_right_cancel_nonzero","all_prime_succ_elim_prefix","le_refl","mul_zero_left"),
            _intro("n","p","r","b","c","l","hf","hlast","heq")+_parts("hf",3)
            +(f"have hd : exists q R. {_and(_at('b','c','l','q','cancel_decoded'),_product('b','c','l','R','cancel_product'),'n = R * q')}",)
            +_call("beta_product_succ_decompose","b","c","l","n")+("exact hf_right_left",)+_cases("hd",2)+_parts("hd_witness_witness",3)
            +("have hfactor : x = p",)+_call("beta_at_unique","b","c","l","x","p")+("exact hd_witness_witness_left","exact hlast","rewrite hfactor at hd_witness_witness_right_right")
            +("have hpzero : ~(p = 0)","intro hzero")+_call("prime_nonzero","p")+_call("factor_permutation_all_prime_entry","b","c","S l","l","p")
            +("exact hf_right_right",)+_call("le_refl","S l")+("exact hlast","exact hzero","have hquotient : x1 = r")
            +_call("mul_right_cancel_nonzero","x1","r","p")+("exact hpzero","trans n","symm","exact hd_witness_witness_right_right","exact heq","split","intro hrzero","apply hf_left","trans r * p","exact heq","rewrite hrzero","apply mul_zero_left","split")
            +_rewrite("hquotient",_product('b','c','l','x1','cancel_transport'),'x1','hd_witness_witness_right_left')+("exact hd_witness_witness_right_left",)
            +_call("all_prime_succ_elim_prefix","b","c","l")+("exact hf_right_right",),
            "Cancel an actual final prime factor, retaining the nonzero predecessor product and all actual prime prefix entries.",
        ),
        spec(
            "factor_permutation_successor_decompose",
            f"forall n b c l. ({_factorization('n','b','c','S l','decompose_full')}) -> exists p r. {_and(prime('p',tag='pfp_decompose_prime'),_at('b','c','l','p','decompose_last'),'n = r * p',_factorization('r','b','c','l','decompose_prefix'))}",
            ("beta_product_succ_decompose","factor_permutation_all_prime_entry","factor_permutation_cancel_last","le_refl"),
            _intro("n","b","c","l","hf")
            +(f"have hprod : {_product('b','c','S l','n','decompose_product')}",)+_parts("hf",3)+("exact hf_right_left",)
            +(f"have hd : exists p r. {_and(_at('b','c','l','p','decompose_entry'),_product('b','c','l','r','decompose_before'),'n = r * p')}",)
            +_call("beta_product_succ_decompose","b","c","l","n")+("exact hprod",)+_cases("hd",2)+_parts("hd_witness_witness",3)
            +("exists x","exists x1","split")+_call("factor_permutation_all_prime_entry","b","c","S l","l","x")
            +_parts("hf",3)+("exact hf_right_right",)+_call("le_refl","S l")+("exact hd_witness_witness_left","split","exact hd_witness_witness_left","split","exact hd_witness_witness_right_right")
            +_call("factor_permutation_cancel_last","n","x","x1","b","c","l")+("exact hf","exact hd_witness_witness_left","exact hd_witness_witness_right_right"),
            "Every nonempty prime factorization supplies an actual last prime, its actual quotient, and a genuine shorter factorization.",
        ),
        spec(
            "factor_permutation_unit_length_zero",
            f"forall n b c l. ({_factorization('n','b','c','l','unit')}) -> n = 1 -> l = 0",
            ("beta_all_prime_product_one_iff_length_zero",),
            _intro("n","b","c","l","hf","hunit")+_parts("hf",3)
            +(f"have hiff : (n = 1 -> l = 0) /\\ (l = 0 -> n = 1)",)
            +_call("beta_all_prime_product_one_iff_length_zero","b","c","l","n")+("exact hf_right_right","exact hf_right_left","cases hiff","apply hiff_left","exact hunit"),
            "The only prime factorization of one has empty length; this is an actual-product statement, not a convention imposed on a list.",
        ),
        spec(
            "factor_permutation_prime_member",
            f"forall n b c l p. ({_factorization('n','b','c','l','member_factorization')}) -> ({prime('p',tag='pfp_member_prime')}) -> (exists q. n = p * q) -> exists i. ({_lt('i','l','member_bound')}) /\\ ({_at('b','c','i','p','member')})",
            ("beta_prime_divisor_product_member",),
            _intro("n","b","c","l","p","hf","hp","hdiv")+_parts("hf",3)
            +_call("beta_prime_divisor_product_member","b","c","l","n","p")+("exact hp","exact hf_right_right","exact hf_right_left","exact hdiv"),
            "An actual prime divisor is found at an actual occurrence of every unordered prime factorization of the product.",
        ),
        spec(
            "factor_permutation_empty_matching",
            f"forall b c d e. ({_matched('b','c','d','e','0','0','0','empty')})",
            ("factor_permutation_below_zero_impossible",),
            _intro("b","c","d","e")+("split","split")
            +_intro("i","hi")+("exfalso",)+_call("factor_permutation_below_zero_impossible","i")+("exact hi","split")
            +_intro("i","j","a","hi","hj","hfirst","hsecond")+("exfalso",)+_call("factor_permutation_below_zero_impossible","i")+("exact hi",)
            +_intro("a","ha")+("exfalso",)+_call("factor_permutation_below_zero_impossible","a")+("exact ha",)
            +_intro("i","j","a","hi","hmap","hsource")+("exfalso",)+_call("factor_permutation_below_zero_impossible","i")+("exact hi",),
            "The actual literal zero beta code is a bounded/injective/surjective matching permutation between any two empty factor prefixes.",
        ),
    )


def _extension_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "factor_permutation_index_extend",
            f"forall b c l. ({_permutation('b','c','l','extend_old')}) -> exists d e. {_and(_permutation('d','e','S l','extend_new'),_extension('b','c','d','e','l','extension'))}",
            ("beta_prefix_extend","finite_lt_succ_eq_or_lt","le_refl","le_succ","factor_permutation_prefix_reflect","finite_prefix_injective_extend_fresh","finite_bounded_entry_lt","lt_irrefl_expanded","finite_bounded_injective_surjective"),
            _intro("b","c","l","hp")+_parts("hp",3)
            +(f"have hext : exists d e. ({_extension('b','c','d','e','l','chosen_extension')})",)
            +_call("beta_prefix_extend","l","b","c","l")+_cases("hext",2)+("cases hext_witness_witness",)
            +(f"have hbound : {_bounded('x','x1','S l','extend_bounded')}",)
            +_intro("i","hi")+(f"have hcase : i = l \\/ ({_lt('i','l','extend_case')})",)+_call("finite_lt_succ_eq_or_lt","l","i")+("exact hi","cases hcase","exists l","split","rewrite hcase_left","rewrite hcase_left","exact hext_witness_witness_left")
            +_call("le_refl","S l")
            +(f"have hvalue : exists a. ({_at('b','c','i','a','extend_old_value')}) /\\ ({_lt('a','l','extend_old_bound')})",)
            +_call("hp_left","i")+("exact hcase_right","cases hvalue","cases hvalue_witness","exists x2","split")
            +_call("hext_witness_witness_right","i","x2")+("exact hcase_right","exact hvalue_witness_left")
            +_call("le_succ","S x2","l")+("exact hvalue_witness_right",)
            +(f"have hinjectiveprefix : {_injective('x','x1','l','extend_injective_prefix')}",)
            +_intro("i","j","a","hi","hj","hfirst","hsecond")+_call("hp_right_left","i","j","a")+("exact hi","exact hj")
            +_call("factor_permutation_prefix_reflect","b","c","x","x1","l","i","a")+("exact hext_witness_witness_right","exact hi","exact hfirst")
            +_call("factor_permutation_prefix_reflect","b","c","x","x1","l","j","a")+("exact hext_witness_witness_right","exact hj","exact hsecond")
            +(f"have hinjective : {_injective('x','x1','S l','extend_injective')}",)
            +_call("finite_prefix_injective_extend_fresh","x","x1","l","l")+("exact hinjectiveprefix","exact hext_witness_witness_left","intro hcontains","cases hcontains","cases hcontains_witness")
            +_call("lt_irrefl_expanded","l")+_call("finite_bounded_entry_lt","b","c","l","x2","l")+("exact hp_left","exact hcontains_witness_left")
            +_call("factor_permutation_prefix_reflect","b","c","x","x1","l","x2","l")+("exact hext_witness_witness_right","exact hcontains_witness_left","exact hcontains_witness_right",)
            +("exists x","exists x1","split","split","exact hbound","split","exact hinjective")
            +_call("finite_bounded_injective_surjective","S l","x","x1")+("exact hbound","exact hinjective","split","exact hext_witness_witness_left","exact hext_witness_witness_right"),
            "Append the fresh top index to any actual finite permutation, construct the new beta code, and prove all three bijection conditions.",
        ),
        spec(
            "factor_permutation_matching_append",
            f"forall b c d e u v U V l p. ({_matching('b','c','d','e','u','v','l','append_old')}) -> ({_extension('u','v','U','V','l','append_extension')}) -> "
            f"({_at('b','c','l','p','append_left')}) -> ({_at('d','e','l','p','append_right')}) -> ({_matching('b','c','d','e','U','V','S l','append_new')})",
            ("finite_lt_succ_eq_or_lt","beta_at_unique","factor_permutation_prefix_reflect"),
            _intro("b","c","d","e","u","v","U","V","l","p","hm","hext","hleft","hright")+("cases hext",)
            +_intro("i","j","a","hi","hmap","hsource")
            +(f"have hcase : i = l \\/ ({_lt('i','l','append_case')})",)+_call("finite_lt_succ_eq_or_lt","l","i")+("exact hi","cases hcase","have hj : j = l")
            +_call("beta_at_unique","U","V","l","j","l")
            +_rewrite("hcase_left",_at('U','V','i','j','append_map_transport'),'i','hmap')+("exact hmap","exact hext_left","have ha : a = p")
            +_call("beta_at_unique","b","c","l","a","p")
            +_rewrite("hcase_left",_at('b','c','i','a','append_source_transport'),'i','hsource')+("exact hsource","exact hleft")
            +_rewrite("hj",_at('d','e','j','a','append_goal_j'),'j')+_rewrite("ha",_at('d','e','l','a','append_goal_a'),'a')+("exact hright",)
            +(f"have hold : {_at('u','v','i','j','append_original_map')}",)
            +_call("factor_permutation_prefix_reflect","u","v","U","V","l","i","j")+("exact hext_right","exact hcase_right","exact hmap")
            +_call("hm","i","j","a")+("exact hcase_right","exact hold","exact hsource"),
            "A matching map stays matching when the same actual last factor is appended to both lists and the fresh last index is appended to the map.",
        ),
        spec(
            "factor_permutation_matched_append",
            f"forall b c d e u v l p. ({_matched('b','c','d','e','u','v','l','matched_old')}) -> ({_at('b','c','l','p','matched_left')}) -> ({_at('d','e','l','p','matched_right')}) -> "
            f"exists U V. {_and(_matched('b','c','d','e','U','V','S l','matched_new'),_extension('u','v','U','V','l','matched_extension'))}",
            ("factor_permutation_index_extend","factor_permutation_matching_append"),
            _intro("b","c","d","e","u","v","l","p","hm","hleft","hright")+("cases hm",)
            +(f"have hex : exists U V. {_and(_permutation('U','V','S l','append_permutation'),_extension('u','v','U','V','l','append_permutation_extension'))}",)
            +_call("factor_permutation_index_extend","u","v","l")+("exact hm_left",)+_cases("hex",2)+("cases hex_witness_witness","exists x","exists x1","split","split","exact hex_witness_witness_left")
            +_call("factor_permutation_matching_append","b","c","d","e","u","v","x","x1","l","p")+("exact hm_right","exact hex_witness_witness_right","exact hleft","exact hright","exact hex_witness_witness_right"),
            "Construct a genuine matching permutation after adjoining the same last factor, retaining the exact prefix-preservation and fresh-index equations.",
        ),
        spec(
            "factor_permutation_matched_append_exists",
            f"forall b c d e u v l p. ({_matched('b','c','d','e','u','v','l','exists_append_old')}) -> ({_at('b','c','l','p','exists_append_left')}) -> ({_at('d','e','l','p','exists_append_right')}) -> "
            f"exists U V. ({_matched('b','c','d','e','U','V','S l','exists_append_new')})",
            ("factor_permutation_matched_append",),
            _intro("b","c","d","e","u","v","l","p","hm","hleft","hright")
            +(f"have hex : exists U V. {_and(_matched('b','c','d','e','U','V','S l','exists_append_witness'),_extension('u','v','U','V','l','exists_append_extension'))}",)
            +_call("factor_permutation_matched_append","b","c","d","e","u","v","l","p")+("exact hm","exact hleft","exact hright")
            +_cases("hex",2)+("cases hex_witness_witness","exists x","exists x1","exact hex_witness_witness_left"),
            "Existence-only append interface still returns an actual fully bijective matching beta map.",
        ),
    )


def _swap_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    swap=_swap('b','c','d','e','l','i','p','q','swap')
    return (
        spec(
            "factor_permutation_swap_reflect_unchanged",
            f"forall b c d e l i p q k a. ({swap}) -> ({_lt('k','S l','reflect_swap_bound')}) -> ~(k = i) -> ~(k = l) -> ({_at('d','e','k','a','reflect_swap_new')}) -> ({_at('b','c','k','a','reflect_swap_old')})",
            ("beta_at_exists","beta_at_unique"),
            _intro("b","c","d","e","l","i","p","q","k","a","hs","hk","hki","hkl","hnew")+_parts("hs",5)
            +(f"have hold : exists z. ({_at('b','c','k','z','swap_original')})",)+_call("beta_at_exists","b","c","k")+("cases hold",)
            +(f"have hmoved : {_at('d','e','k','x','swap_moved')}",)+_call("hs_right_right_right_right","k","x")+("exact hk","exact hki","exact hkl","exact hold_witness","have heq : a = x")
            +_call("beta_at_unique","d","e","k","a","x")+("exact hnew","exact hmoved")
            +_rewrite("heq",_at('b','c','k','a','swap_reflect_goal'),'a')+("exact hold_witness",),
            "An actual swapped prefix reflects back to the original entry at every index other than the two moved indices.",
        ),
        spec(
            "factor_permutation_swap_bijection",
            f"forall b c d e l i p q. ({_lt('i','l','bijection_swap_index')}) -> ({_permutation('b','c','S l','bijection_swap_old')}) -> ({swap}) -> ({_permutation('d','e','S l','bijection_swap_new')})",
            ("finite_swap_last_bounded","finite_swap_last_injective","finite_bounded_injective_surjective"),
            _intro("b","c","d","e","l","i","p","q","hi","hp","hs")+_parts("hp",3)+_parts("hs",5)
            +(f"have hb : {_bounded('d','e','S l','swap_bounded')}",)
            +_call("finite_swap_last_bounded","b","c","d","e","l","S l","i","p","q")+("refl","exact hi","exact hp_left")
            +tuple("exact "+_part("hs",5,k) for k in range(5))
            +(f"have hj : {_injective('d','e','S l','swap_injective')}",)
            +_call("finite_swap_last_injective","b","c","d","e","l","S l","i","p","q")+("refl","exact hi","exact hp_right_left")
            +tuple("exact "+_part("hs",5,k) for k in range(5))
            +("split","exact hb","split","exact hj")+_call("finite_bounded_injective_surjective","S l","d","e")+("exact hb","exact hj"),
            "Swapping two actual map entries preserves boundedness and injectivity and constructively recovers full finite surjectivity.",
        ),
        spec(
            "factor_permutation_swap_all_prime",
            f"forall b c d e l i p q. ({_lt('i','l','prime_swap_index')}) -> ({_allprime('b','c','S l','prime_swap_old')}) -> ({swap}) -> ({_allprime('d','e','S l','prime_swap_new')})",
            ("eq_decidable","beta_at_exists","beta_at_unique","factor_permutation_all_prime_entry","factor_permutation_swap_reflect_unchanged","le_refl","le_succ"),
            _intro("b","c","d","e","l","i","p","q","hi","hp","hs")
            +(f"have hcopy : {swap}","exact hs")+_parts("hcopy",5)+_intro("k","hk")
            +(f"have hvalue : exists a. ({_at('d','e','k','a','swap_prime_value')})",)+_call("beta_at_exists","d","e","k")+("cases hvalue","exists x","split","exact hvalue_witness","have hcase : k = i \\/ ~(k = i)")
            +_call("eq_decidable","k","i")+("cases hcase","have heq : x = q")
            +_call("beta_at_unique","d","e","i","x","q")+_rewrite("hcase_left",_at('d','e','k','x','swap_prime_i'),'k','hvalue_witness')+("exact hvalue_witness","exact hcopy_right_right_left")
            +_rewrite("heq",prime('x',tag='pfp_swap_i_goal'),'x')+_call("factor_permutation_all_prime_entry","b","c","S l","l","q")+("exact hp",)+_call("le_refl","S l")+("exact hcopy_right_left","have hlast : k = l \\/ ~(k = l)")
            +_call("eq_decidable","k","l")+("cases hlast","have heq : x = p")
            +_call("beta_at_unique","d","e","l","x","p")+_rewrite("hlast_left",_at('d','e','k','x','swap_prime_last'),'k','hvalue_witness')+("exact hvalue_witness","exact hcopy_right_right_right_left")
            +_rewrite("heq",prime('x',tag='pfp_swap_last_goal'),'x')+_call("factor_permutation_all_prime_entry","b","c","S l","i","p")+("exact hp",)+_call("le_succ","S i","l")+("exact hi","exact hcopy_left")
            +_call("factor_permutation_all_prime_entry","b","c","S l","k","x")+("exact hp","exact hk")
            +_call("factor_permutation_swap_reflect_unchanged","b","c","d","e","l","i","p","q","k","x")+("exact hs","exact hk","exact hcase_right","exact hlast_right","exact hvalue_witness"),
            "A genuine index swap retains every prime factor, including duplicate equal primes; no distinct-factor hypothesis is required.",
        ),
        spec(
            "factor_permutation_swap_factorization",
            f"forall N b c d e l i p q. ({_factorization('N','b','c','S l','swap_factor_old')}) -> ({_lt('i','l','swap_factor_index')}) -> ({swap}) -> ({_factorization('N','d','e','S l','swap_factor_new')})",
            ("factor_permutation_product_exists","beta_product_swap_last_invariant","factor_permutation_swap_all_prime"),
            _intro("N","b","c","d","e","l","i","p","q","hf","hi","hs")+_parts("hf",3)
            +(f"have hproduct : exists Q. ({_product('d','e','S l','Q','swap_product')})",)+_call("factor_permutation_product_exists","d","e","S l")+("cases hproduct","have hsame : N = x")
            +_parts("hs",5)+_call("beta_product_swap_last_invariant","b","c","d","e","l","i","p","q","N","x")+("exact hi",)
            +tuple("exact "+_part("hs",5,k) for k in range(5))+("exact hf_right_left","exact hproduct_witness","have hx : x = N","symm","exact hsame","split","exact hf_left","split")
            +_rewrite("hx",_product('d','e','S l','x','swap_product_transport'),'x','hproduct_witness')+("exact hproduct_witness",)
            +_call("factor_permutation_swap_all_prime","b","c","d","e","l","i","p","q")+("exact hi","exact hf_right_right","exact hs"),
            "The swapped prime list has an actual product trace with the identical nonzero product, not merely a proposed rearrangement equality.",
        ),
        spec(
            "factor_permutation_swapped_factorization_exists",
            f"forall N b c l i p. ({_factorization('N','b','c','S l','swap_exists_factor')}) -> ({_lt('i','l','swap_exists_index')}) -> ({_at('b','c','i','p','swap_exists_selected')}) -> exists d e q. "
            f"{_and(_factorization('N','d','e','S l','swap_exists_result'),_swap('b','c','d','e','l','i','p','q','swap_exists_witness'))}",
            ("beta_at_exists","beta_prefix_swap_last_from_entries","factor_permutation_swap_factorization"),
            _intro("N","b","c","l","i","p","hf","hi","hselected")
            +(f"have hlast : exists q. ({_at('b','c','l','q','swap_exists_last')})",)+_call("beta_at_exists","b","c","l")+("cases hlast",)
            +(f"have hnew : exists d e. {_and(_at('d','e','i','x','swap_new_i'),_at('d','e','l','p','swap_new_last'),'forall j a. ('+_lt('j','S l','swap_new_bound')+') -> ~(j = i) -> ~(j = l) -> ('+_at('b','c','j','a','swap_new_old')+') -> ('+_at('d','e','j','a','swap_new_new')+')')}",)
            +_call("beta_prefix_swap_last_from_entries","b","c","l","i","p","x")+("exact hi","exact hselected","exact hlast_witness")
            +_cases("hnew",2)+_parts("hnew_witness_witness",3)
            +(f"have hswap : {_swap('b','c','x1','x2','l','i','p','x','swap_constructed')}","split","exact hselected","split","exact hlast_witness","split","exact hnew_witness_witness_left","split","exact hnew_witness_witness_right_left","exact hnew_witness_witness_right_right","exists x1","exists x2","exists x","split")
            +_call("factor_permutation_swap_factorization","N","b","c","x1","x2","l","i","p","x")+("exact hf","exact hi","exact hswap","exact hswap"),
            "Construct a full recoded prime-factor list moving a selected interior prime to the last position, with exact swap witnesses and an unchanged actual product.",
        ),
    )


def _unswap_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    target_swap=_swap('d','e','D','E','l','j','p','q','target_swap')
    map_swap=_swap('u','v','U','V','l','i','j','l','map_swap')
    return (
        spec(
            "factor_permutation_matching_unswap",
            f"forall b c d e D E u v U V l i j p q. ({_lt('i','l','unswap_source')}) -> ({_lt('j','l','unswap_target')}) -> "
            f"({_permutation('u','v','S l','unswap_permutation')}) -> ({_matching('b','c','D','E','u','v','S l','unswap_matching')}) -> "
            f"({target_swap}) -> ({map_swap}) -> ({_matching('b','c','d','e','U','V','S l','unswap_result')})",
            ("eq_decidable","beta_at_unique","factor_permutation_swap_reflect_unchanged","finite_bounded_entry_lt","le_succ","le_refl"),
            _intro("b","c","d","e","D","E","u","v","U","V","l","i","j","p","q","hi","hj","hp","hm","hs","ht")+_parts("hp",3)
            +(f"have hscopy : {target_swap}","exact hs")+_parts("hscopy",5)
            +(f"have htcopy : {map_swap}","exact ht")+_parts("htcopy",5)
            +_intro("k","z","a","hk","hmap","hsource")+("have hcase : k = i \\/ ~(k = i)",)+_call("eq_decidable","k","i")+("cases hcase","have hz : z = l")
            +_call("beta_at_unique","U","V","i","z","l")+_rewrite("hcase_left",_at('U','V','k','z','unswap_selected_map'),'k','hmap')+("exact hmap","exact htcopy_right_right_left")
            +(f"have hvalue : {_at('D','E','j','a','unswap_selected_target')}",)+_call("hm","i","j","a")+_call("le_succ","S i","l")+("exact hi","exact htcopy_left")
            +_rewrite("hcase_left",_at('b','c','k','a','unswap_selected_source'),'k','hsource')+("exact hsource","have ha : a = q")
            +_call("beta_at_unique","D","E","j","a","q")+("exact hvalue","exact hscopy_right_right_left")
            +_rewrite("hz",_at('d','e','z','a','unswap_selected_goal_index'),'z')+_rewrite("ha",_at('d','e','l','a','unswap_selected_goal_value'),'a')+("exact hscopy_right_left","have hlast : k = l \\/ ~(k = l)")
            +_call("eq_decidable","k","l")+("cases hlast","have hz : z = j")
            +_call("beta_at_unique","U","V","l","z","j")+_rewrite("hlast_left",_at('U','V','k','z','unswap_last_map'),'k','hmap')+("exact hmap","exact htcopy_right_right_right_left")
            +(f"have hvalue : {_at('D','E','l','a','unswap_last_target')}",)+_call("hm","l","l","a")+_call("le_refl","S l")+("exact htcopy_right_left",)
            +_rewrite("hlast_left",_at('b','c','k','a','unswap_last_source'),'k','hsource')+("exact hsource","have ha : a = p")
            +_call("beta_at_unique","D","E","l","a","p")+("exact hvalue","exact hscopy_right_right_right_left")
            +_rewrite("hz",_at('d','e','z','a','unswap_last_goal_index'),'z')+_rewrite("ha",_at('d','e','j','a','unswap_last_goal_value'),'a')+("exact hscopy_left",)
            +(f"have hold : {_at('u','v','k','z','unswap_unchanged_map')}",)
            +_call("factor_permutation_swap_reflect_unchanged","u","v","U","V","l","i","j","l","k","z")+("exact ht","exact hk","exact hcase_right","exact hlast_right","exact hmap")
            +(f"have hvalue : {_at('D','E','z','a','unswap_unchanged_target')}",)+_call("hm","k","z","a")+("exact hk","exact hold","exact hsource")
            +(f"have hzbound : {_lt('z','S l','unswap_image_bound')}",)+_call("finite_bounded_entry_lt","u","v","S l","k","z")+("exact hp_left","exact hk","exact hold","have hzj : ~(z = j)","intro heq","apply hcase_right")
            +_call("hp_right_left","k","i","j")+("exact hk",)+_call("le_succ","S i","l")+("exact hi",)
            +_rewrite("heq",_at('u','v','k','z','unswap_image_not_j'),'z','hold')+("exact hold","exact htcopy_left","have hzl : ~(z = l)","intro heq","apply hlast_right")
            +_call("hp_right_left","k","l","l")+("exact hk",)+_call("le_refl","S l")
            +_rewrite("heq",_at('u','v','k','z','unswap_image_not_last'),'z','hold')+("exact hold","exact htcopy_right_left")
            +_call("factor_permutation_swap_reflect_unchanged","d","e","D","E","l","j","p","q","z","a")+("exact hs","exact hzbound","exact hzj","exact hzl","exact hvalue"),
            "Undo a target-list swap by swapping the two corresponding actual source-map entries. Entry alignment follows at the two moved positions and everywhere else by map injectivity.",
        ),
        spec(
            "factor_permutation_matched_unswap_exists",
            f"forall b c d e D E u v l j p q. ({_lt('j','l','unswap_exists_index')}) -> ({_matched('b','c','D','E','u','v','l','unswap_exists_prefix')}) -> "
            f"({_at('b','c','l','p','unswap_exists_last')}) -> ({target_swap}) -> exists U V. ({_matched('b','c','d','e','U','V','S l','unswap_exists_result')})",
            ("factor_permutation_matched_append","beta_prefix_swap_last_from_entries","factor_permutation_swap_bijection","factor_permutation_matching_unswap"),
            _intro("b","c","d","e","D","E","u","v","l","j","p","q","hj","hm","hleft","hs")
            +(f"have hright : {_at('D','E','l','p','unswap_exists_target_last')}",)+_parts("hs",5)+("exact hs_right_right_right_left",)
            +(f"have hfull : exists U V. {_and(_matched('b','c','D','E','U','V','S l','unswap_full_matching'),_extension('u','v','U','V','l','unswap_full_extension'))}",)
            +_call("factor_permutation_matched_append","b","c","D","E","u","v","l","p")+("exact hm","exact hleft","exact hright")
            +_cases("hfull",2)+("cases hfull_witness_witness","cases hfull_witness_witness_left","cases hfull_witness_witness_right","cases hm")+_parts("hm_left",3)
            +(f"have hpreimage : exists i. ({_lt('i','l','unswap_preimage_bound')}) /\\ ({_at('u','v','i','j','unswap_preimage_entry')})",)
            +_call("hm_left_right_right","j")+("exact hj","cases hpreimage","cases hpreimage_witness")
            +(f"have hmapi : {_at('x','x1','x2','j','unswap_full_image')}",)+_call("hfull_witness_witness_right_right","x2","j")+("exact hpreimage_witness_left","exact hpreimage_witness_right")
            +(f"have hmapnew : exists U V. {_and(_at('U','V','x2','l','unswap_map_new_selected'),_at('U','V','l','j','unswap_map_new_last'),'forall k a. ('+_lt('k','S l','unswap_map_preserve_bound')+') -> ~(k = x2) -> ~(k = l) -> ('+_at('x','x1','k','a','unswap_map_preserve_old')+') -> ('+_at('U','V','k','a','unswap_map_preserve_new')+')')}",)
            +_call("beta_prefix_swap_last_from_entries","x","x1","l","x2","j","l")+("exact hpreimage_witness_left","exact hmapi","exact hfull_witness_witness_right_left")
            +_cases("hmapnew",2)+_parts("hmapnew_witness_witness",3)
            +(f"have hmapswap : {_swap('x','x1','x3','x4','l','x2','j','l','unswap_actual_map')}","split","exact hmapi","split","exact hfull_witness_witness_right_left","split","exact hmapnew_witness_witness_left","split","exact hmapnew_witness_witness_right_left","exact hmapnew_witness_witness_right_right","exists x3","exists x4","split")
            +_call("factor_permutation_swap_bijection","x","x1","x3","x4","l","x2","j","l")+("exact hpreimage_witness_left","exact hfull_witness_witness_left_left","exact hmapswap")
            +_call("factor_permutation_matching_unswap","b","c","d","e","D","E","x","x1","x3","x4","l","x2","j","p","q")+("exact hpreimage_witness_left","exact hj","exact hfull_witness_witness_left_left","exact hfull_witness_witness_left_right","exact hs","exact hmapswap"),
            "Use the recursively constructed finite permutation's actual preimage, construct both extended and transposed map codes, and return a full matching bijection into the original unswapped target list.",
        ),
    )


def _length_result(b: str,c: str,l: str,d: str,e: str,m: str,tag: str) -> str:
    u,v=f"pfp_u_{tag}",f"pfp_v_{tag}"
    return _and(f"{l} = {m}",f"exists {u} {v}. ({_matched(b,c,d,e,u,v,l,tag+'matching')})")


def _complete_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    source_decomposition=_and(prime('p',tag='pfp_induction_prime'),_at('b','c','l','p','induction_last'),'n = r * p',_factorization('r','b','c','l','induction_source_prefix'))
    target_recoded=_and(_factorization('n','B','C','S x3','induction_recoded_factorization'),_swap('d','e','B','C','x3','x2','x','q','induction_target_swap'))
    return (
        spec(
            "prime_factor_lists_matching_by_length",
            f"forall l n b c m d e. ({_factorization('n','b','c','l','uniqueness_source')}) -> ({_factorization('n','d','e','m','uniqueness_target')}) -> "
            f"({_length_result('b','c','l','d','e','m','uniqueness_result')})",
            ("beta_product_zero","factor_permutation_unit_length_zero","factor_permutation_empty_matching","factor_permutation_successor_decompose","factor_permutation_prime_member","mul_comm","factor_permutation_below_zero_impossible","nonzero_is_succ","finite_lt_succ_eq_or_lt","factor_permutation_cancel_last","factor_permutation_matched_append_exists","factor_permutation_swapped_factorization_exists","factor_permutation_matched_unswap_exists"),
            ("induction l",)+_intro("n","b","c","m","d","e","hA","hB")
            +(f"have hproduct : {_product('b','c','0','n','zero_source_product')}",)+_parts("hA",3)+("exact hA_right_left","have hone : n = 1")
            +_call("beta_product_zero","b","c","n")+("exact hproduct","have hlength : m = 0")+_call("factor_permutation_unit_length_zero","n","d","e","m")+("exact hB","exact hone","split","symm","exact hlength","exists 0","exists 0")+_call("factor_permutation_empty_matching","b","c","d","e")
            +_intro("n","b","c","m","d","e","hA","hB")
            +(f"have hd : exists p r. ({source_decomposition})",)+_call("factor_permutation_successor_decompose","n","b","c","l")+("exact hA",)+_cases("hd",2)+_parts("hd_witness_witness",4)
            +(f"have hmember : exists i. ({_lt('i','m','induction_member_bound')}) /\\ ({_at('d','e','i','x','induction_member_entry')})",)
            +_call("factor_permutation_prime_member","n","d","e","m","x")+("exact hB","exact hd_witness_witness_left","exists x1","trans x1 * x","exact hd_witness_witness_right_right_left","apply mul_comm","cases hmember","cases hmember_witness","have hmnonzero : ~(m = 0)","intro hzero")
            +_call("factor_permutation_below_zero_impossible","x2")+("rewrite hzero at hmember_witness_left","exact hmember_witness_left","have hpredecessor : exists t. m = S t")+_call("nonzero_is_succ","m")+("exact hmnonzero","cases hpredecessor")
            +(f"have hBsuccessor : {_factorization('n','d','e','S x3','induction_target_successor')}",)
            +_rewrite("hpredecessor_witness",_factorization('n','d','e','m','induction_target_length_transport'),'m','hB')+("exact hB",)
            +(f"have hbound : {_lt('x2','S x3','induction_target_index')}","rewrite hpredecessor_witness at hmember_witness_left","exact hmember_witness_left",f"have hposition : x2 = x3 \\/ ({_lt('x2','x3','induction_target_position')})")
            +_call("finite_lt_succ_eq_or_lt","x3","x2")+("exact hbound","cases hposition",)
            +(f"have hlast : {_at('d','e','x3','x','induction_already_last')}",)
            +_rewrite("hposition_left",_at('d','e','x2','x','induction_already_last_transport'),'x2','hmember_witness_right')+("exact hmember_witness_right",)
            +(f"have hprefix : {_factorization('x1','d','e','x3','induction_direct_prefix')}",)
            +_call("factor_permutation_cancel_last","n","x","x1","d","e","x3")+("exact hBsuccessor","exact hlast","exact hd_witness_witness_right_right_left")
            +(f"have hrec : {_length_result('b','c','l','d','e','x3','induction_direct_recursion')}",)
            +_call("IH","x1","b","c","x3","d","e")+("exact hd_witness_witness_right_right_right","exact hprefix","cases hrec")+_cases("hrec_right",2)
            +(f"have hlastaligned : {_at('d','e','l','x','induction_direct_aligned_last')}",)
            +_rewrite("hrec_left",_at('d','e','l','x','induction_direct_last_transport'),'l')+("exact hlast","split","trans S x3","congr","exact hrec_left","symm","exact hpredecessor_witness")
            +_call("factor_permutation_matched_append_exists","b","c","d","e","x4","x5","l","x")+("exact hrec_right_witness_witness","exact hd_witness_witness_right_left","exact hlastaligned",)
            +(f"have hswap : exists B C q. ({target_recoded})",)
            +_call("factor_permutation_swapped_factorization_exists","n","d","e","x3","x2","x")+("exact hBsuccessor","exact hposition_right","exact hmember_witness_right")
            +_cases("hswap",3)+("cases hswap_witness_witness_witness",)
            +(f"have hlast : {_at('x4','x5','x3','x','induction_recoded_last')}",)+_parts("hswap_witness_witness_witness_right",5)+("exact hswap_witness_witness_witness_right_right_right_right_left",)
            +(f"have hprefix : {_factorization('x1','x4','x5','x3','induction_recoded_prefix')}",)
            +_call("factor_permutation_cancel_last","n","x","x1","x4","x5","x3")+("exact hswap_witness_witness_witness_left","exact hlast","exact hd_witness_witness_right_right_left")
            +(f"have hrec : {_length_result('b','c','l','x4','x5','x3','induction_recoded_recursion')}",)
            +_call("IH","x1","b","c","x3","x4","x5")+("exact hd_witness_witness_right_right_right","exact hprefix","cases hrec")+_cases("hrec_right",2)
            +(f"have hpivot : {_lt('x2','l','induction_pivot_aligned')}","rewrite hrec_left","exact hposition_right")
            +(f"have hswapaligned : {_swap('d','e','x4','x5','l','x2','x','x6','induction_swap_aligned')}",)
            +_rewrite("hrec_left",_swap('d','e','x4','x5','l','x2','x','x6','induction_swap_length_transport'),'l')+("exact hswap_witness_witness_witness_right","split","trans S x3","congr","exact hrec_left","symm","exact hpredecessor_witness")
            +_call("factor_permutation_matched_unswap_exists","b","c","d","e","x4","x5","x7","x8","l","x2","x","x6")+("exact hpivot","exact hrec_right_witness_witness","exact hd_witness_witness_right_left","exact hswapaligned"),
            "Full induction on an arbitrary source factor list: locate the last prime in the arbitrary target, genuinely swap and cancel it, recursively match the shorter lists, and construct the restored index bijection. Neither list is assumed sorted or distinct.",
        ),
        spec(
            "prime_factor_lists_permutation_exists",
            f"forall n b c l d e m. (({_factorization('n','b','c','l','root_source')}) /\\ ({_factorization('n','d','e','m','root_target')})) -> exists u v. "
            f"({prime_factor_list_permutation_relation('b','c','l','d','e','m','u','v',tag='root_permutation')})",
            ("prime_factor_lists_matching_by_length",),
            _intro("n","b","c","l","d","e","m","hf")+("cases hf",)
            +(f"have hresult : {_length_result('b','c','l','d','e','m','root_induction')}",)
            +_call("prime_factor_lists_matching_by_length","l","n","b","c","m","d","e")+("exact hf_left","exact hf_right","cases hresult")+_cases("hresult_right",2)+("exists x","exists x1","split","exact hresult_left","exact hresult_right_witness_witness"),
            "Exact G005: every two arbitrary unordered prime factorizations of the same positive natural admit an actual coded matching bijection, with equal lengths and explicit boundedness, injectivity, and surjectivity.",
        ),
        spec(
            "prime_factorization_exists_unique_up_to_permutation",
            f"forall n. ~(n = 0) -> exists l b c. (({_factorization('n','b','c','l','complete_source')}) /\\ "
            f"forall m d e. ({_factorization('n','d','e','m','complete_target')}) -> exists u v. "
            f"({prime_factor_list_permutation_relation('b','c','l','d','e','m','u','v',tag='complete_permutation')}))",
            ("foundation_prime_factor_list_exists","prime_factor_lists_permutation_exists"),
            _intro("n","hn")+(f"have hsource : exists l b c. ({_factorization('n','b','c','l','complete_constructed')})",)
            +_call("foundation_prime_factor_list_exists","n")+("exact hn",)+_cases("hsource",3)+("exists x","exists x1","exists x2","split","exact hsource_witness_witness_witness")
            +_intro("m","d","e","htarget")+_call("prime_factor_lists_permutation_exists","n","x1","x2","x","d","e","m")+("split","exact hsource_witness_witness_witness","exact htarget"),
            "Construct an actual prime-factor list for every positive natural and an actual matching permutation to every competing unordered factorization. Both factor-list existence and uniqueness witnesses are conclusions, with no supplied canonical factorization.",
        ),
    )


def make_prime_factorization_permutation_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    """Return additive ordinary-HA candidate bodies; no release authority."""
    return _basic_rows(spec)+_extension_rows(spec)+_swap_rows(spec)+_unswap_rows(spec)+_complete_rows(spec)


__all__=["factor_list_matching_relation","prime_factor_list_permutation_relation","make_prime_factorization_permutation_candidate_theorems"]
