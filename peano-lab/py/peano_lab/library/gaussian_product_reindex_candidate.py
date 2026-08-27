"""Actual Gaussian product balance under replacement and finite factor swaps.

The two input products are genuine beta-coded multiplication histories.  The
proofs use the checked canonical Gaussian ring laws; they do not multiply the
natural factor codes or assume a permutation-invariant product oracle.
"""

from __future__ import annotations

from typing import Any,Callable

from . import gaussian_ring_candidate as gr
from . import gaussian_euclidean_candidate as ge
from . import gaussian_factorization_candidate as gf
from . import prime_factorization_permutation_candidate as permutation


_call=gr._call
_intro=gr._intro
_exists=gr._exists
_cases=gr._cases
_parts=gr._parts
_part=gr._part
_and=gr._and
_mul=gr._mul
_product=gf._product
_at=gf._at
_lt=ge._lt
_swap=permutation._swap


def _preserve_except(b: str,c: str,d: str,e: str,k: str,i: str,tag: str) -> str:
    j,a=gr._names(tag,'replacement_index','replacement_value')
    return f"forall {j} {a}. ({_lt(j,k,tag+'bound')}) -> ~({j}=({i})) -> ({_at(b,c,j,a,tag+'old')}) -> ({_at(d,e,j,a,tag+'new')})"


def _decomposition(b: str,c: str,k: str,P: str,tag: str) -> str:
    return f"exists a R. "+_and(_at(b,c,k,'a',tag+'factor'),_product(b,c,k,'R',tag+'prefix'),_mul('R','a',P,tag+'last'))


def _replacement_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    old=tuple(_part('hold_witness_witness',3,i) for i in range(3))
    new=tuple(_part('hnew_witness_witness',3,i) for i in range(3))
    arguments=('b','c','d','e','i','p','q','P','Q','T','hi','hp','hq','hpreserve','hP','hQ','hmultiply')
    script=('induction k',)+_intro(*arguments)+('exfalso',)+_call('gaussian_search_no_index_below_zero','i')+('exact hi',)
    script+=_intro(*arguments)+(f"have hcases : i=k \\/ ({_lt('i','k','replacement_last_cases')})",)+_call('finite_lt_succ_eq_or_lt','k','i')+('exact hi',)
    script+=(f"have hold : {_decomposition('b','c','k','P','replacement_old')}",)+_call('gaussian_product_successor_decompose','b','c','k','P')+('exact hP',)
    script+=(f"have hnew : {_decomposition('d','e','k','Q','replacement_new')}",)+_call('gaussian_product_successor_decompose','d','e','k','Q')+('exact hQ',)
    script+=_cases('hold',2)+_parts('hold_witness_witness',3)+_cases('hnew',2)+_parts('hnew_witness_witness',3)+('cases hcases','have hlastold : x=p')
    script+=_call('beta_at_unique','b','c','k','x','p')+(f'exact {old[0]}',)+_call('gaussian_product_beta_index_transport','b','c','i','k','p')+('exact hcases_left','exact hp','have hlastnew : x2=q')
    script+=_call('beta_at_unique','d','e','k','x2','q')+(f'exact {new[0]}',)+_call('gaussian_product_beta_index_transport','d','e','i','k','q')+('exact hcases_left','exact hq')
    script+=(f"have hprefix : {_product('d','e','k','x1','replacement_equal_prefix')}",)+_call('gaussian_product_prefix_recode','b','c','d','e','k','x1')+(f'exact {old[1]}',)
    script+=_intro('j','a','hj','hentry')+_call('hpreserve','j','a')+_call('le_succ','S j','k')+('exact hj','intro heq')
    script+=_call('lt_irrefl_expanded','k')+('rewrite heq at hj','rewrite hcases_left at hj','exact hj','exact hentry','have hprefixeq : x1=x3')
    script+=_call('gaussian_product_functional','k','d','e','x1','x3')+('exact hprefix',f'exact {new[1]}',f'rewrite hlastold at {old[2]}',f'rewrite hprefixeq at {old[2]}',f'rewrite hlastnew at {new[2]}')
    script+=_call('gaussian_multiply_swap_tail','x3','q','p','Q','P','T')+(f'exact {new[2]}','exact hmultiply',f'exact {old[2]}','have hki : ~(k=i)','intro heq')
    script+=_call('lt_irrefl_expanded','k')+('rewrite <- heq at hcases_right','exact hcases_right',f"have hlast : {_at('d','e','k','x','replacement_preserved_last')}")
    script+=_call('hpreserve','k','x')+_call('le_refl','S k')+('exact hki',f'exact {old[0]}','have hlastmatch : x2=x')
    script+=_call('beta_at_unique','d','e','k','x2','x')+(f'exact {new[0]}','exact hlast',f'rewrite hlastmatch at {new[2]}')
    script+=(f"have hR : exists R. ({_mul('x3','p','R','replacement_short_balance_product')})",)+_call('gaussian_multiply_exists','x3','p')
    script+=_call('gaussian_product_result_valid','k','d','e','x3')+(f'exact {new[1]}',)+_call('gaussian_multiply_input_right_valid','Q','p','T')+('exact hmultiply','cases hR')
    script+=(f"have hmiddle : {_mul('x4','x','T','replacement_balanced_tail')}",)+_call('gaussian_multiply_swap_tail','x3','x','p','Q','x4','T')+(f'exact {new[2]}','exact hmultiply','exact hR_witness')
    script+=(f"have hbalance : {_mul('x1','q','x4','replacement_recursive_balance')}",)+_call('IH','b','c','d','e','i','p','q','x1','x3','x4')+('exact hcases_right','exact hp','exact hq')
    script+=_intro('j','a','hj','hne','hentry')+_call('hpreserve','j','a')+_call('le_succ','S j','k')+('exact hj','exact hne','exact hentry',f'exact {old[1]}',f'exact {new[1]}','exact hR_witness')
    script+=_call('gaussian_multiply_swap_tail','x1','q','x','x4','P','T')+('exact hbalance','exact hmiddle',f'exact {old[2]}')
    statement=(f"forall k b c d e i p q P Q T. ({_lt('i','k','replace_index')}) -> ({_at('b','c','i','p','replace_old_factor')}) -> ({_at('d','e','i','q','replace_new_factor')}) -> "
               f"({_preserve_except('b','c','d','e','k','i','replace_other_factors')}) -> ({_product('b','c','k','P','replace_old_product')}) -> ({_product('d','e','k','Q','replace_new_product')}) -> "
               f"({_mul('Q','p','T','replace_balance_source')}) -> ({_mul('P','q','T','replace_balance_target')})")
    return (spec(
        'gaussian_product_replace_balance',statement,
        ('gaussian_search_no_index_below_zero','finite_lt_succ_eq_or_lt','gaussian_product_successor_decompose','beta_at_unique','gaussian_product_beta_index_transport','gaussian_product_prefix_recode','le_succ','lt_irrefl_expanded','gaussian_product_functional','gaussian_multiply_swap_tail','le_refl','gaussian_multiply_exists','gaussian_product_result_valid','gaussian_multiply_input_right_valid'),
        script,
        'Ordinary induction proves the actual Gaussian replacement balance Q*p=P*q with genuine product traces and actual common output code, including zero and unit factors.',
    ),)


def _iff_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    actual=(f"forall k b c d e i p q P Q T. ({_lt('i','k','replace_iff_index')}) -> ({_at('b','c','i','p','replace_iff_old_factor')}) -> ({_at('d','e','i','q','replace_iff_new_factor')}) -> "
            f"({_preserve_except('b','c','d','e','k','i','replace_iff_other_factors')}) -> ({_product('b','c','k','P','replace_iff_old_product')}) -> ({_product('d','e','k','Q','replace_iff_new_product')}) -> "
            f"((({_mul('Q','p','T','replace_iff_source_first')}) -> ({_mul('P','q','T','replace_iff_target_first')})) /\\ "
            f"(({_mul('P','q','T','replace_iff_source_second')}) -> ({_mul('Q','p','T','replace_iff_target_second')})))")
    script=_intro('k','b','c','d','e','i','p','q','P','Q','T','hi','hp','hq','hpreserve','hP','hQ')+('split','intro hmul')
    script+=_call('gaussian_product_replace_balance','k','b','c','d','e','i','p','q','P','Q','T')+('exact hi','exact hp','exact hq','exact hpreserve','exact hP','exact hQ','exact hmul','intro hmul')
    script+=_call('gaussian_product_replace_balance','k','d','e','b','c','i','q','p','Q','P','T')+('exact hi','exact hq','exact hp')
    script+=_intro('j','a','hj','hne','hentry')+(f"have hreflect : forall J A. ({_lt('J','k','replace_iff_reflect_bound')}) -> ({_at('d','e','J','A','replace_iff_reflect_new')}) -> ((J=i /\\ A=q) \\/ (~(J=i) /\\ ({_at('b','c','J','A','replace_iff_reflect_old')})))",)
    script+=_call('beta_prefix_replace_reflect','b','c','d','e','k','i','q')+('exact hi','exact hq','exact hpreserve',f"have hcases : (j=i /\\ a=q) \\/ (~(j=i) /\\ ({_at('b','c','j','a','replace_iff_reflected')}))")
    script+=_call('hreflect','j','a')+('exact hj','exact hentry','cases hcases','cases hcases_left','exfalso','apply hne','exact hcases_left_left','cases hcases_right','exact hcases_right_right','exact hQ','exact hP','exact hmul')
    return (spec(
        'gaussian_product_replace_balance_iff',actual,
        ('gaussian_product_replace_balance','beta_prefix_replace_reflect'),script,
        'The actual Gaussian replacement balance holds in both directions; reflection of unchanged beta entries is proved rather than assumed.',
    ),)


def _swap_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    old=tuple(_part('hold_witness_witness',3,i) for i in range(3))
    new=tuple(_part('hnew_witness_witness',3,i) for i in range(3))
    swap=tuple(_part('hswap',5,i) for i in range(5))
    script=_intro('b','c','d','e','l','i','p','q','P','Q','hi','hswap','hP','hQ')+_parts('hswap',5)
    script+=(f"have hold : {_decomposition('b','c','l','P','swap_old')}",)+_call('gaussian_product_successor_decompose','b','c','l','P')+('exact hP',)
    script+=(f"have hnew : {_decomposition('d','e','l','Q','swap_new')}",)+_call('gaussian_product_successor_decompose','d','e','l','Q')+('exact hQ',)
    script+=_cases('hold',2)+_parts('hold_witness_witness',3)+_cases('hnew',2)+_parts('hnew_witness_witness',3)+('have hlastold : x=q',)
    script+=_call('beta_at_unique','b','c','l','x','q')+(f'exact {old[0]}',f'exact {swap[1]}','have hlastnew : x2=p')
    script+=_call('beta_at_unique','d','e','l','x2','p')+(f'exact {new[0]}',f'exact {swap[3]}',f'rewrite hlastold at {old[2]}',f'rewrite hlastnew at {new[2]}')
    script+=_call('gaussian_multiply_functional','x1','q','P','Q')+(f'exact {old[2]}',)
    script+=_call('gaussian_product_replace_balance','l','b','c','d','e','i','p','q','x1','x3','Q')+('exact hi',f'exact {swap[0]}',f'exact {swap[2]}')
    script+=_intro('j','a','hj','hne','hentry')+_call(swap[4],'j','a')+_call('le_succ','S j','l')+('exact hj','exact hne','intro heq')
    script+=_call('lt_irrefl_expanded','l')+('rewrite heq at hj','exact hj','exact hentry',f'exact {old[1]}',f'exact {new[1]}',f'exact {new[2]}')
    return (spec(
        'gaussian_product_swap_last_invariant',f"forall b c d e l i p q P Q. ({_lt('i','l','swap_interior')}) -> ({_swap('b','c','d','e','l','i','p','q','swap_actual_entries')}) -> "
        f"({_product('b','c','S l','P','swap_first_product')}) -> ({_product('d','e','S l','Q','swap_second_product')}) -> P=Q",
        ('gaussian_product_successor_decompose','beta_at_unique','gaussian_multiply_functional','gaussian_product_replace_balance','le_succ','lt_irrefl_expanded'),script,
        'An actual interior/last beta swap preserves the literal canonical value of a genuine Gaussian multiplication trace, without nonzero, irreducibility or unit hypotheses.',
    ),)


def make_gaussian_product_reindex_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_replacement_rows(spec),*_iff_rows(spec),*_swap_rows(spec))


__all__=['make_gaussian_product_reindex_candidate_theorems']
