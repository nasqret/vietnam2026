"""Gaussian factor uniqueness by actual unit witnesses and beta bijections.

The permutation is an actual finite beta-coded bounded, injective and
surjective map.  Matching means an actual multiplicative unit transports
each source Gaussian prime to its matched target.  Literal prime codes and
the leading unit are not asserted to be unique, and no sorted canonical
choice is inserted into the factorization predicate.
"""

from __future__ import annotations

from typing import Any,Callable

from . import gaussian_ring_candidate as gr
from . import gaussian_euclidean_candidate as ge
from . import gaussian_factorization_candidate as factor
from . import prime_factorization_permutation_candidate as permutation


_and=gr._and
_call=gr._call
_intro=gr._intro
_exists=gr._exists
_cases=gr._cases
_parts=gr._parts
_part=gr._part
_mul=gr._mul
_unit=gr._unit
_valid=gr._valid
_associate=gr._associate
_irreducible=gr._irreducible
_prime=gr._prime
_dvd=gr._dvd
_norm=gr._norm
_lt=ge._lt
_le=ge._le
_at=factor._at
_product=factor._product
_all_irreducible=factor._all_irreducible
_factor=factor._factor
_prime_factor=factor._prime_factor
_permutation=permutation._permutation
_preserve=permutation._preserve
_swap=permutation._swap
_extension=permutation._extension


def _matching(b: str,c: str,d: str,e: str,u: str,v: str,l: str,tag: str) -> str:
    i,j,p,q=gr._names(tag,'match_index','match_image','match_source','match_target')
    return f"forall {i} {j} {p} {q}. ({_lt(i,l,tag+'index')}) -> ({_at(u,v,i,j,tag+'map')}) -> ({_at(b,c,i,p,tag+'source')}) -> ({_at(d,e,j,q,tag+'target')}) -> ({_associate(p,q,tag+'unit_witness')})"


def _matched(b: str,c: str,d: str,e: str,u: str,v: str,l: str,tag: str) -> str:
    return _and(_permutation(u,v,l,tag+'bijection'),_matching(b,c,d,e,u,v,l,tag+'matching'))


def _equal_lengths_matched(b: str,c: str,l: str,d: str,e: str,m: str,u: str,v: str,tag: str) -> str:
    return _and(f'({l})=({m})',_matched(b,c,d,e,u,v,l,tag+'matched'))


def gaussian_factor_associate_matching_relation(b: str,c: str,d: str,e: str,u: str,v: str,l: str,*,tag: str,variables: tuple[str,...]) -> str:
    """Every decoded source/image/target pair is related by an actual unit."""
    return gr._definition(_matching,(b,c,d,e,u,v,l),tag=tag,variables=variables)


def gaussian_factor_permutation_relation(b: str,c: str,l: str,d: str,e: str,m: str,u: str,v: str,*,tag: str,variables: tuple[str,...]) -> str:
    """Equal lengths, a real beta bijection, and witnessed per-factor associates."""
    return gr._definition(_equal_lengths_matched,(b,c,l,d,e,m,u,v),tag=tag,variables=variables)


def _association_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_factor_associate_code_transport',f"forall a b c d. a=c -> b=d -> ({_associate('a','b','associate_code_source')}) -> ({_associate('c','d','associate_code_target')})",
            (),_intro('a','b','c','d','heq','heq2','h')+('rewrite heq at h','rewrite heq2 at h','exact h'),
            'Equality of actual canonical codes transports an unchanged witnessed Gaussian unit association.',
        ),
        spec(
            'gaussian_factor_associate_unit',f"forall a b. ({_associate('a','b','associate_unit_input')}) -> ({_unit('a','associate_unit_source')}) -> ({_unit('b','associate_unit_result')})",
            ('gaussian_unit_product',),_intro('a','b','h','hu')+('cases h','cases h_witness')+_call('gaussian_unit_product','x','a','b')+('exact h_witness_right','exact h_witness_left','exact hu'),
            'A witnessed Gaussian association transports actual unit status by multiplying the two actual units.',
        ),
        spec(
            'gaussian_factor_associate_cancel_products',f"forall R p P T q Q. ({_mul('R','p','P','cancel_first_product')}) -> ({_mul('T','q','Q','cancel_second_product')}) -> ({_associate('P','Q','cancel_total_associate')}) -> ({_associate('p','q','cancel_factor_associate')}) -> ~(p=0) -> ({_associate('R','T','cancel_prefix_associate')})",
            ('gaussian_multiply_exists','gaussian_unit_valid','gaussian_multiply_input_left_valid','gaussian_multiply_associative_reverse','gaussian_multiply_commutative','gaussian_multiply_cancel_right','gaussian_factor_associate_code_transport','gaussian_associate_transitive','gaussian_associate_symmetric'),
            _intro('R','p','P','T','q','Q','hRP','hTQ','hPQ','hpq','hp')+('cases hPQ','cases hPQ_witness','cases hpq','cases hpq_witness',
              f"have hC : exists C. ({_mul('x','R','C','cancel_first_scaled')})")
            +_call('gaussian_multiply_exists','x','R')+_call('gaussian_unit_valid','x')+('exact hPQ_witness_left',)+_call('gaussian_multiply_input_left_valid','R','p','P')+('exact hRP','cases hC',
              f"have hD : exists D. ({_mul('x1','T','D','cancel_second_scaled')})")
            +_call('gaussian_multiply_exists','x1','T')+_call('gaussian_unit_valid','x1')+('exact hpq_witness_left',)+_call('gaussian_multiply_input_left_valid','T','q','Q')+('exact hTQ','cases hD','have heq : x2=x3')
            +_call('gaussian_multiply_cancel_right','x2','x3','p','Q')+('exact hp',)+_call('gaussian_multiply_associative_reverse','x','R','p','x2','P','Q')+('exact hC_witness','exact hRP','exact hPQ_witness_right')
            +_call('gaussian_multiply_associative_reverse','T','x1','p','x3','q','Q')+_call('gaussian_multiply_commutative','x1','T','x3')+('exact hD_witness','exact hpq_witness_right','exact hTQ')
            +_call('gaussian_associate_transitive','R','x3','T')+_call('gaussian_factor_associate_code_transport','R','x2','R','x3')+('refl','exact heq')+_exists('x')+('split','exact hPQ_witness_left','exact hC_witness')
            +_call('gaussian_associate_symmetric','T','x3')+_exists('x1')+('split','exact hpq_witness_left','exact hD_witness'),
            'Cancel associated nonzero last factors from associated actual products, constructing the resulting prefix association from actual unit witnesses.',
        ),
        spec(
            'gaussian_product_decompose_at_last',f"forall b c l P p. ({_product('b','c','S l','P','last_fixed_product')}) -> ({_at('b','c','l','p','last_fixed_factor')}) -> exists R. "
            +_and(_product('b','c','l','R','last_fixed_prefix'),_mul('R','p','P','last_fixed_multiply')),
            ('gaussian_product_successor_decompose','beta_at_unique'),
            _intro('b','c','l','P','p','hP','hp')+(f"have hs : exists a R. {_and(_at('b','c','l','a','last_fixed_actual_factor'),_product('b','c','l','R','last_fixed_actual_prefix'),_mul('R','a','P','last_fixed_actual_step'))}",)
            +_call('gaussian_product_successor_decompose','b','c','l','P')+('exact hP',)+_cases('hs',2)+_parts('hs_witness_witness',3)+('have heq : x=p',)
            +_call('beta_at_unique','b','c','l','x','p')+('exact hs_witness_witness_left','exact hp')+_exists('x1')+('split','exact hs_witness_witness_right_left','rewrite heq at hs_witness_witness_right_right','exact hs_witness_witness_right_right'),
            'Expose the actual prefix product before a specifically decoded last Gaussian factor; beta functionality fixes the chosen factor exactly.',
        ),
    )


def _matching_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_factor_empty_matching',f"forall b c d e. ({_matched('b','c','d','e','0','0','0','empty_matching')})",
            ('gaussian_search_no_index_below_zero',),
            _intro('b','c','d','e')+('split','split')+_intro('i','hi')+('exfalso',)+_call('gaussian_search_no_index_below_zero','i')+('exact hi','split')
            +_intro('i','j','a','hi','hj','hfirst','hsecond')+('exfalso',)+_call('gaussian_search_no_index_below_zero','i')+('exact hi',)
            +_intro('a','ha')+('exfalso',)+_call('gaussian_search_no_index_below_zero','a')+('exact ha',)
            +_intro('i','j','a','t','hi','hmap','hsource','htarget')+('exfalso',)+_call('gaussian_search_no_index_below_zero','i')+('exact hi',),
            'The actual zero beta map is a bounded, injective, surjective unit-matching bijection between any two empty factor prefixes.',
        ),
        spec(
            'gaussian_factor_matching_append',f"forall b c d e u v U V l p q. ({_matching('b','c','d','e','u','v','l','append_matching_old')}) -> ({_extension('u','v','U','V','l','append_matching_extension')}) -> ({_at('b','c','l','p','append_matching_source_last')}) -> ({_at('d','e','l','q','append_matching_target_last')}) -> ({_associate('p','q','append_matching_last_unit')}) -> ({_matching('b','c','d','e','U','V','S l','append_matching_new')})",
            ('finite_lt_succ_eq_or_lt','gaussian_product_beta_index_transport','beta_at_unique','gaussian_factor_associate_code_transport','factor_permutation_prefix_reflect'),
            _intro('b','c','d','e','u','v','U','V','l','p','q','hm','hext','hp','hq','hpq')+('cases hext',)+_intro('i','j','a','t','hi','hmap','hsource','htarget')
            +(f"have hc : i=l \\/ ({_lt('i','l','append_matching_index_case')})",)+_call('finite_lt_succ_eq_or_lt','l','i')+('exact hi','cases hc','have hj : j=l')
            +_call('beta_at_unique','U','V','l','j','l')+_call('gaussian_product_beta_index_transport','U','V','i','l','j')+('exact hc_left','exact hmap','exact hext_left','have ha : p=a')
            +_call('beta_at_unique','b','c','l','p','a')+('exact hp',)+_call('gaussian_product_beta_index_transport','b','c','i','l','a')+('exact hc_left','exact hsource','have ht : q=t')
            +_call('beta_at_unique','d','e','l','q','t')+('exact hq',)+_call('gaussian_product_beta_index_transport','d','e','j','l','t')+('exact hj','exact htarget')
            +_call('gaussian_factor_associate_code_transport','p','q','a','t')+('exact ha','exact ht','exact hpq')
            +_call('hm','i','j','a','t')+('exact hc_right',)+_call('factor_permutation_prefix_reflect','u','v','U','V','l','i','j')+('exact hext_right','exact hc_right','exact hmap','exact hsource','exact htarget'),
            'Adjoining associated actual last factors and a fresh fixed last index preserves witnessed unit matching; literal factor-code equality is not required.',
        ),
        spec(
            'gaussian_factor_matched_append',f"forall b c d e u v l p q. ({_matched('b','c','d','e','u','v','l','matched_append_old')}) -> ({_at('b','c','l','p','matched_append_source_last')}) -> ({_at('d','e','l','q','matched_append_target_last')}) -> ({_associate('p','q','matched_append_unit')}) -> exists U V. "
            +_and(_matched('b','c','d','e','U','V','S l','matched_append_new'),_extension('u','v','U','V','l','matched_append_extension')),
            ('factor_permutation_index_extend','gaussian_factor_matching_append'),
            _intro('b','c','d','e','u','v','l','p','q','hm','hp','hq','hpq')+('cases hm',
              f"have hext : exists U V. {_and(_permutation('U','V','S l','matching_new_bijection'),_extension('u','v','U','V','l','matching_new_extension'))}")
            +_call('factor_permutation_index_extend','u','v','l')+('exact hm_left',)+_cases('hext',2)+('cases hext_witness_witness',)+_exists('x','x1')+('split','split','exact hext_witness_witness_left')
            +_call('gaussian_factor_matching_append','b','c','d','e','u','v','x','x1','l','p','q')+('exact hm_right','exact hext_witness_witness_right','exact hp','exact hq','exact hpq','exact hext_witness_witness_right'),
            'Construct a real fully bijective beta index map after appending any two associated Gaussian factors, retaining all actual prefix entries.',
        ),
    )


def _swap_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    target_swap=_swap('d','e','D','E','l','j','p','q','matching_target_swap')
    map_swap=_swap('u','v','U','V','l','i','j','l','matching_map_swap')
    return (
        spec(
            'gaussian_factor_swap_all_irreducible',f"forall b c d e l i p q. ({_lt('i','l','swap_irreducible_index')}) -> ({_all_irreducible('b','c','S l','swap_irreducible_old')}) -> ({_swap('b','c','d','e','l','i','p','q','swap_irreducible_data')}) -> ({_all_irreducible('d','e','S l','swap_irreducible_new')})",
            ('eq_decidable','beta_at_unique','gaussian_product_beta_index_transport','gaussian_irreducible_code_transport','le_refl','le_succ','factor_permutation_swap_reflect_unchanged'),
            _intro('b','c','d','e','l','i','p','q','hi','hall','hs')+_parts('hs',5)+_intro('k','a','hk','ha')+('have hki : k=i \\/ ~(k=i)',)+_call('eq_decidable','k','i')+('cases hki','have heq : q=a')
            +_call('beta_at_unique','d','e','i','q','a')+('exact hs_right_right_left',)+_call('gaussian_product_beta_index_transport','d','e','k','i','a')+('exact hki_left','exact ha')
            +_call('gaussian_irreducible_code_transport','q','a')+('exact heq',)+_call('hall','l','q')+_call('le_refl','S l')+('exact hs_right_left','have hkl : k=l \\/ ~(k=l)')
            +_call('eq_decidable','k','l')+('cases hkl','have heq : p=a')+_call('beta_at_unique','d','e','l','p','a')+('exact hs_right_right_right_left',)
            +_call('gaussian_product_beta_index_transport','d','e','k','l','a')+('exact hkl_left','exact ha')+_call('gaussian_irreducible_code_transport','p','a')+('exact heq',)
            +_call('hall','i','p')+_call('le_succ','S i','l')+('exact hi','exact hs_left')+_call('hall','k','a')+('exact hk',)
            +_call('factor_permutation_swap_reflect_unchanged','b','c','d','e','l','i','p','q','k','a')+('exact hs','exact hk','exact hki_right','exact hkl_right','exact ha'),
            'An actual finite swap retains all Gaussian irreducible factors, including repetitions and distinct unit associates.',
        ),
        spec(
            'gaussian_factor_matching_unswap',f"forall b c d e D E u v U V l i j p q. ({_lt('i','l','unswap_source_index')}) -> ({_lt('j','l','unswap_target_index')}) -> ({_permutation('u','v','S l','unswap_old_bijection')}) -> ({_matching('b','c','D','E','u','v','S l','unswap_old_matching')}) -> ({target_swap}) -> ({map_swap}) -> ({_matching('b','c','d','e','U','V','S l','unswap_new_matching')})",
            ('eq_decidable','beta_at_unique','gaussian_product_beta_index_transport','gaussian_product_beta_value_transport','factor_permutation_swap_reflect_unchanged','finite_bounded_entry_lt','le_succ','le_refl'),
            _intro('b','c','d','e','D','E','u','v','U','V','l','i','j','p','q','hi','hj','hp','hm','hs','ht')+_parts('hp',3)+_parts('hs',5)+_parts('ht',5)
            +_intro('k','z','a','t','hk','hmap','hsource','htarget')+('have hki : k=i \\/ ~(k=i)',)+_call('eq_decidable','k','i')+('cases hki','have hz : z=l')
            +_call('beta_at_unique','U','V','i','z','l')+_call('gaussian_product_beta_index_transport','U','V','k','i','z')+('exact hki_left','exact hmap','exact ht_right_right_left','have hb : q=t')
            +_call('beta_at_unique','d','e','l','q','t')+('exact hs_right_left',)+_call('gaussian_product_beta_index_transport','d','e','z','l','t')+('exact hz','exact htarget')
            +_call('hm','i','j','a','t')+_call('le_succ','S i','l')+('exact hi','exact ht_left')+_call('gaussian_product_beta_index_transport','b','c','k','i','a')+('exact hki_left','exact hsource')
            +_call('gaussian_product_beta_value_transport','D','E','j','q','t')+('exact hb','exact hs_right_right_left','have hkl : k=l \\/ ~(k=l)')
            +_call('eq_decidable','k','l')+('cases hkl','have hz : z=j')+_call('beta_at_unique','U','V','l','z','j')+_call('gaussian_product_beta_index_transport','U','V','k','l','z')+('exact hkl_left','exact hmap','exact ht_right_right_right_left','have hb : p=t')
            +_call('beta_at_unique','d','e','j','p','t')+('exact hs_left',)+_call('gaussian_product_beta_index_transport','d','e','z','j','t')+('exact hz','exact htarget')
            +_call('hm','l','l','a','t')+_call('le_refl','S l')+('exact ht_right_left',)+_call('gaussian_product_beta_index_transport','b','c','k','l','a')+('exact hkl_left','exact hsource')
            +_call('gaussian_product_beta_value_transport','D','E','l','p','t')+('exact hb','exact hs_right_right_right_left',
              f"have hold : ({_at('u','v','k','z','unswap_unchanged_map')})")
            +_call('factor_permutation_swap_reflect_unchanged','u','v','U','V','l','i','j','l','k','z')+('exact ht','exact hk','exact hki_right','exact hkl_right','exact hmap',
              f"have hzbound : ({_lt('z','S l','unswap_image_bound')})")
            +_call('finite_bounded_entry_lt','u','v','S l','k','z')+('exact hp_left','exact hk','exact hold','have hzj : ~(z=j)','intro heq','apply hki_right')
            +_call('hp_right_left','k','i','j')+('exact hk',)+_call('le_succ','S i','l')+('exact hi',)+_call('gaussian_product_beta_value_transport','u','v','k','z','j')+('exact heq','exact hold','exact ht_left',
              'have hzl : ~(z=l)','intro heq','apply hkl_right')
            +_call('hp_right_left','k','l','l')+('exact hk',)+_call('le_refl','S l')+_call('gaussian_product_beta_value_transport','u','v','k','z','l')+('exact heq','exact hold','exact ht_right_left')
            +_call('hm','k','z','a','t')+('exact hk','exact hold','exact hsource')+_call('hs_right_right_right_right','z','t')+('exact hzbound','exact hzj','exact hzl','exact htarget'),
            'Undo an actual target factor swap by swapping the corresponding actual map entries; original unit witnesses remain valid at both moved positions and every unchanged index.',
        ),
        spec(
            'gaussian_factor_matched_unswap_exists',f"forall b c d e D E u v l j a p q. ({_lt('j','l','unswap_exists_index')}) -> ({_matched('b','c','D','E','u','v','l','unswap_exists_prefix')}) -> ({_at('b','c','l','a','unswap_exists_source_last')}) -> ({target_swap}) -> ({_associate('a','p','unswap_exists_last_associate')}) -> exists U V. ({_matched('b','c','d','e','U','V','S l','unswap_exists_result')})",
            ('gaussian_factor_matched_append','beta_prefix_swap_last_from_entries','factor_permutation_swap_bijection','gaussian_factor_matching_unswap'),
            _intro('b','c','d','e','D','E','u','v','l','j','a','p','q','hj','hm','ha','hs','hap')+_parts('hs',5)
            +(f"have hfull : exists U V. {_and(_matched('b','c','D','E','U','V','S l','unswap_full_matching'),_extension('u','v','U','V','l','unswap_full_extension'))}",)
            +_call('gaussian_factor_matched_append','b','c','D','E','u','v','l','a','p')+('exact hm','exact ha','exact hs_right_right_right_left','exact hap')+_cases('hfull',2)
            +('cases hfull_witness_witness','cases hfull_witness_witness_left','cases hfull_witness_witness_right','cases hm')+_parts('hm_left',3)
            +(f"have hpreimage : exists i. {_and(_lt('i','l','unswap_actual_preimage'),_at('u','v','i','j','unswap_actual_preimage_entry'))}",)
            +_call('hm_left_right_right','j')+('exact hj','cases hpreimage','cases hpreimage_witness',f"have hmapi : ({_at('x','x1','x2','j','unswap_extended_preimage')})")
            +_call('hfull_witness_witness_right_right','x2','j')+('exact hpreimage_witness_left','exact hpreimage_witness_right',
              f"have hnew : exists U V. {_and(_at('U','V','x2','l','unswap_map_new_selected'),_at('U','V','l','j','unswap_map_new_last'),'forall k a. ('+_lt('k','S l','unswap_map_preserve_index')+') -> ~(k=x2) -> ~(k=l) -> ('+_at('x','x1','k','a','unswap_map_preserve_old')+') -> ('+_at('U','V','k','a','unswap_map_preserve_new')+')')}")
            +_call('beta_prefix_swap_last_from_entries','x','x1','l','x2','j','l')+('exact hpreimage_witness_left','exact hmapi','exact hfull_witness_witness_right_left')+_cases('hnew',2)+_parts('hnew_witness_witness',3)
            +(f"have hswap : ({_swap('x','x1','x3','x4','l','x2','j','l','unswap_constructed_map')})",'split','exact hmapi','split','exact hfull_witness_witness_right_left','split','exact hnew_witness_witness_left','split','exact hnew_witness_witness_right_left','exact hnew_witness_witness_right_right')
            +_exists('x3','x4')+('split',)+_call('factor_permutation_swap_bijection','x','x1','x3','x4','l','x2','j','l')+('exact hpreimage_witness_left','exact hfull_witness_witness_left_left','exact hswap')
            +_call('gaussian_factor_matching_unswap','b','c','d','e','D','E','x','x1','x3','x4','l','x2','j','p','q')+('exact hpreimage_witness_left','exact hj','exact hfull_witness_witness_left_left','exact hfull_witness_witness_left_right','exact hs','exact hswap'),
            'Construct a real full unit-matching bijection into the unswapped target list using the recursive permutation, its actual preimage, a fresh last index and an actual transposed beta map.',
        ),
    )


def _swapped_product(b: str,c: str,d: str,e: str,l: str,i: str,p: str,q: str,P: str,tag: str) -> str:
    return _and(_all_irreducible(d,e,f'S ({l})',tag+'factors'),_product(d,e,f'S ({l})',P,tag+'product'),_swap(b,c,d,e,l,i,p,q,tag+'swap'))


def _swap_product_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_factor_swap_length_transport',f"forall b c d e k l i p q. k=l -> ({_swap('b','c','d','e','k','i','p','q','swap_length_source')}) -> ({_swap('b','c','d','e','l','i','p','q','swap_length_target')})",
            (),_intro('b','c','d','e','k','l','i','p','q','heq','h')+('rewrite heq at h',)*6+('exact h',),
            'Equality of lengths transports all actual last-entry indices and the finite preservation bound of a witnessed swap.',
        ),
        spec(
            'gaussian_factor_swapped_product_exists',f"forall b c l i p P. ({_all_irreducible('b','c','S l','swap_product_original_factors')}) -> ({_product('b','c','S l','P','swap_product_original_trace')}) -> ({_lt('i','l','swap_product_selected_index')}) -> ({_at('b','c','i','p','swap_product_selected_factor')}) -> exists d e q. ({_swapped_product('b','c','d','e','l','i','p','q','P','swap_product_result')})",
            ('beta_at_exists','beta_prefix_swap_last_from_entries','gaussian_factor_swap_all_irreducible','gaussian_all_irreducible_product_exists','gaussian_product_swap_last_invariant','gaussian_product_value_transport'),
            _intro('b','c','l','i','p','P','hall','hP','hi','hp')+(f"have hlast : exists q. ({_at('b','c','l','q','swap_product_old_last')})",)+_call('beta_at_exists','b','c','l')+('cases hlast',
              f"have hnew : exists d e. {_and(_at('d','e','i','x','swap_product_new_selected'),_at('d','e','l','p','swap_product_new_last'),'forall j a. ('+_lt('j','S l','swap_product_preserve_index')+') -> ~(j=i) -> ~(j=l) -> ('+_at('b','c','j','a','swap_product_preserve_old')+') -> ('+_at('d','e','j','a','swap_product_preserve_new')+')')}")
            +_call('beta_prefix_swap_last_from_entries','b','c','l','i','p','x')+('exact hi','exact hp','exact hlast_witness')+_cases('hnew',2)+_parts('hnew_witness_witness',3)
            +(f"have hs : ({_swap('b','c','x1','x2','l','i','p','x','swap_product_constructed_swap')})",'split','exact hp','split','exact hlast_witness','split','exact hnew_witness_witness_left','split','exact hnew_witness_witness_right_left','exact hnew_witness_witness_right_right',
              f"have hallnew : ({_all_irreducible('x1','x2','S l','swap_product_constructed_irreducible')})")
            +_call('gaussian_factor_swap_all_irreducible','b','c','x1','x2','l','i','p','x')+('exact hi','exact hall','exact hs',
              f"have hQ : exists Q. ({_product('x1','x2','S l','Q','swap_product_constructed_trace')})")
            +_call('gaussian_all_irreducible_product_exists','S l','x1','x2')+('exact hallnew','cases hQ','have heq : P=x3')
            +_call('gaussian_product_swap_last_invariant','b','c','x1','x2','l','i','p','x','P','x3')+('exact hi','exact hs','exact hP','exact hQ_witness')
            +_exists('x1','x2','x')+('split','exact hallnew','split')+_call('gaussian_product_value_transport','x1','x2','S l','x3','P')+('symm','exact heq','exact hQ_witness','exact hs'),
            'Construct a swapped actual irreducible beta list and a real product trace with exactly the original Gaussian value, using the independently proved Gaussian swap law.',
        ),
    )


def _uniqueness(b: str,c: str,l: str,d: str,e: str,m: str,tag: str) -> str:
    u,v=gr._names(tag,'unique_map','unique_scale')
    return _and(f'({l})=({m})',f"exists {u} {v}. ({_matched(b,c,d,e,u,v,l,tag+'matching')})")


def _product_uniqueness_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    args=('b','c','P','m','d','e','Q','hall','hP','hrall','hQ','hassoc')
    result=_uniqueness('b','c','l','d','e','m','product_unique')
    proof=('induction l',)+_intro(*args)+('have hidentity : P=6',)+_call('gaussian_product_empty_value','b','c','P')+('exact hP',
        f"have hunit : ({_unit('Q','unique_empty_target_unit')})")
    proof+=_call('gaussian_factor_associate_unit','P','Q')+('exact hassoc','rewrite hidentity','exact gaussian_one_unit','have hlength : m=0')
    proof+=_call('gaussian_all_irreducible_product_unit_length_zero','d','e','m','Q')+('exact hrall','exact hQ','exact hunit','split','symm','exact hlength')+_exists('0','0')+_call('gaussian_factor_empty_matching','b','c','d','e')
    proof+=_intro(*args)+(f"have hfirst : exists p R. {_and(_at('b','c','l','p','unique_source_last'),_product('b','c','l','R','unique_source_prefix'),_mul('R','p','P','unique_source_multiply'))}",)
    proof+=_call('gaussian_product_successor_decompose','b','c','l','P')+('exact hP',)+_cases('hfirst',2)+_parts('hfirst_witness_witness',3)
    proof+=(f"have hir : ({_irreducible('x','unique_selected_irreducible')})",)+_call('hall','l','x')+_call('le_refl','S l')+('exact hfirst_witness_witness_left',)
    proof+=(f"have hdiv : ({_dvd('x','Q','unique_selected_divides_target')})",)+_call('gaussian_divides_transitive','x','P','Q')+_exists('x1')+_call('gaussian_multiply_commutative','x1','x','P')+('exact hfirst_witness_witness_right_right',)+_call('gaussian_associate_divides','P','Q')+('exact hassoc',)
    proof+=(f"have hmember : exists i q. {_and(_lt('i','m','unique_target_member_index'),_at('d','e','i','q','unique_target_member_entry'),_associate('x','q','unique_target_member_unit'))}",)
    proof+=_call('gaussian_irreducible_divisor_product_member','m','d','e','Q','x')+('exact hrall','exact hQ','exact hir','exact hdiv')+_cases('hmember',2)+_parts('hmember_witness_witness',3)
    proof+=('have hm : m=0 \\/ exists k. m=S k',)+_call('zero_or_succ','m')+('cases hm','exfalso',)+_call('gaussian_search_no_index_below_zero','x2')+('rewrite hm_left at hmember_witness_witness_left','exact hmember_witness_witness_left','cases hm_right',
        f"have hright : ({_product('d','e','S x4','Q','unique_target_nonempty_product')})")
    proof+=_call('gaussian_product_length_transport','d','e','m','S x4','Q')+('exact hm_right_witness','exact hQ',f"have hrightall : ({_all_irreducible('d','e','S x4','unique_target_nonempty_factors')})")
    proof+=_call('gaussian_all_irreducible_length_transport','d','e','m','S x4')+('exact hm_right_witness','exact hrall','rewrite hm_right_witness at hmember_witness_witness_left',
        f"have hcase : x2=x4 \\/ ({_lt('x2','x4','unique_target_interior_case')})")
    proof+=_call('finite_lt_succ_eq_or_lt','x4','x2')+('exact hmember_witness_witness_left','cases hcase',f"have hlast : ({_at('d','e','x4','x3','unique_target_last_match')})")
    proof+=_call('gaussian_product_beta_index_transport','d','e','x2','x4','x3')+('exact hcase_left','exact hmember_witness_witness_right_left',
        f"have htail : exists T. {_and(_product('d','e','x4','T','unique_target_last_prefix'),_mul('T','x3','Q','unique_target_last_multiply'))}")
    proof+=_call('gaussian_product_decompose_at_last','d','e','x4','Q','x3')+('exact hright','exact hlast','cases htail','cases htail_witness',
        f"have hprefix : ({_associate('x1','x5','unique_last_prefix_associate')})")
    proof+=_call('gaussian_factor_associate_cancel_products','x1','x','P','x5','x3','Q')+('exact hfirst_witness_witness_right_right','exact htail_witness_right','exact hassoc','exact hmember_witness_witness_right_right')+_parts('hir',4)+('exact hir_right_left',
        f"have hrec : ({_uniqueness('b','c','l','d','e','x4','unique_last_recursive')})")
    proof+=_call('IH','b','c','x1','x4','d','e','x5')+_call('gaussian_all_irreducible_prefix','b','c','l')+('exact hall','exact hfirst_witness_witness_right_left')+_call('gaussian_all_irreducible_prefix','d','e','x4')+('exact hrightall','exact htail_witness_left','exact hprefix','cases hrec')+_cases('hrec_right',2)
    proof+=('split','trans S x4','congr','exact hrec_left','symm','exact hm_right_witness',
        f"have hfull : exists U V. {_and(_matched('b','c','d','e','U','V','S l','unique_last_full_matching'),_extension('x6','x7','U','V','l','unique_last_full_extension'))}")
    proof+=_call('gaussian_factor_matched_append','b','c','d','e','x6','x7','l','x','x3')+('exact hrec_right_witness_witness','exact hfirst_witness_witness_left')+_call('gaussian_product_beta_index_transport','d','e','x4','l','x3')+('symm','exact hrec_left','exact hlast','exact hmember_witness_witness_right_right')+_cases('hfull',2)+('cases hfull_witness_witness',)+_exists('x8','x9')+('exact hfull_witness_witness_left',)
    proof+=(f"have hswap : exists D E t. ({_swapped_product('d','e','D','E','x4','x2','x3','t','Q','unique_interior_swapped')})",)
    proof+=_call('gaussian_factor_swapped_product_exists','d','e','x4','x2','x3','Q')+('exact hrightall','exact hright','exact hcase_right','exact hmember_witness_witness_right_left')+_cases('hswap',3)+_parts('hswap_witness_witness_witness',3)
    proof+=(f"have hlast : ({_at('x5','x6','x4','x3','unique_swapped_last')})",)+_parts('hswap_witness_witness_witness_right_right',5)+('exact hswap_witness_witness_witness_right_right_right_right_right_left',
        f"have htail : exists T. {_and(_product('x5','x6','x4','T','unique_swapped_prefix'),_mul('T','x3','Q','unique_swapped_multiply'))}")
    proof+=_call('gaussian_product_decompose_at_last','x5','x6','x4','Q','x3')+('exact hswap_witness_witness_witness_right_left','exact hlast','cases htail','cases htail_witness',
        f"have hprefix : ({_associate('x1','x8','unique_swapped_prefix_associate')})")
    proof+=_call('gaussian_factor_associate_cancel_products','x1','x','P','x8','x3','Q')+('exact hfirst_witness_witness_right_right','exact htail_witness_right','exact hassoc','exact hmember_witness_witness_right_right')+_parts('hir',4)+('exact hir_right_left',
        f"have hrec : ({_uniqueness('b','c','l','x5','x6','x4','unique_swapped_recursive')})")
    proof+=_call('IH','b','c','x1','x4','x5','x6','x8')+_call('gaussian_all_irreducible_prefix','b','c','l')+('exact hall','exact hfirst_witness_witness_right_left')+_call('gaussian_all_irreducible_prefix','x5','x6','x4')+('exact hswap_witness_witness_witness_left','exact htail_witness_left','exact hprefix','cases hrec')+_cases('hrec_right',2)
    proof+=('split','trans S x4','congr','exact hrec_left','symm','exact hm_right_witness')
    proof+=_call('gaussian_factor_matched_unswap_exists','b','c','d','e','x5','x6','x9','x10','l','x2','x','x3','x7')+('rewrite <- hrec_left at hcase_right','exact hcase_right','exact hrec_right_witness_witness','exact hfirst_witness_witness_left')
    proof+=_call('gaussian_factor_swap_length_transport','d','e','x5','x6','x4','l','x2','x3','x7')+('symm','exact hrec_left','exact hswap_witness_witness_witness_right_right','exact hmember_witness_witness_right_right')
    return (
        spec(
            'gaussian_irreducible_products_associate_unique',f"forall l b c P m d e Q. ({_all_irreducible('b','c','l','unique_source_irreducible')}) -> ({_product('b','c','l','P','unique_source_product')}) -> ({_all_irreducible('d','e','m','unique_target_irreducible')}) -> ({_product('d','e','m','Q','unique_target_product')}) -> ({_associate('P','Q','unique_products_associate')}) -> ({result})",
            ('gaussian_product_empty_value','gaussian_factor_associate_unit','gaussian_one_unit','gaussian_all_irreducible_product_unit_length_zero','gaussian_factor_empty_matching','gaussian_product_successor_decompose','le_refl','gaussian_divides_transitive','gaussian_multiply_commutative','gaussian_associate_divides','gaussian_irreducible_divisor_product_member','zero_or_succ','gaussian_search_no_index_below_zero','gaussian_product_length_transport','gaussian_all_irreducible_length_transport','finite_lt_succ_eq_or_lt','gaussian_product_beta_index_transport','gaussian_product_decompose_at_last','gaussian_factor_associate_cancel_products','gaussian_all_irreducible_prefix','gaussian_factor_matched_append','gaussian_factor_swapped_product_exists','gaussian_factor_matched_unswap_exists','gaussian_factor_swap_length_transport'),
            proof,
            'Any two actual finite irreducible Gaussian products which differ by a witnessed unit have equal length and an actually constructed bounded/injective/surjective matching permutation, including empty lists and repeated associates.',
        ),
    )


def _unique_prime_factorization(z: str,tag: str) -> str:
    u,b,c,l,v,d,e,m=gr._names(tag,'chosen_unit','chosen_code','chosen_scale','chosen_length',
                             'other_unit','other_code','other_scale','other_length')
    uniqueness=f"forall {v} {d} {e} {m}. ({_prime_factor(z,v,d,e,m,tag+'other_factorization')}) -> ({_uniqueness(b,c,l,d,e,m,tag+'unique')})"
    return f"exists {u} {b} {c} {l}. "+_and(_prime_factor(z,u,b,c,l,tag+'chosen_factorization'),uniqueness)


def gaussian_unique_prime_factorization_relation(z: str,*,tag: str,variables: tuple[str,...]) -> str:
    """A genuine RingPrime factorization, unique by actual units and beta bijections."""
    return gr._definition(_unique_prime_factorization,(z,),tag=tag,variables=variables)


def _complete_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_irreducible_factorizations_unique',f"forall z u b c l v d e m. ({_factor('z','u','b','c','l','unique_first_factorization')}) -> ({_factor('z','v','d','e','m','unique_second_factorization')}) -> ({_uniqueness('b','c','l','d','e','m','unique_irreducible_factorizations')})",
            ('gaussian_irreducible_products_associate_unique','gaussian_associate_transitive','gaussian_associate_symmetric'),
            _intro('z','u','b','c','l','v','d','e','m','hf','hg')+_parts('hf',3)+_parts('hg',3)+('cases hf_right_right','cases hf_right_right_witness','cases hg_right_right','cases hg_right_right_witness')
            +_call('gaussian_irreducible_products_associate_unique','l','b','c','x','m','d','e','x1')+('exact hf_right_left','exact hf_right_right_witness_left','exact hg_right_left','exact hg_right_right_witness_left')
            +_call('gaussian_associate_transitive','x','z','x1')+_exists('u')+('split','exact hf_left','exact hf_right_right_witness_right')+_call('gaussian_associate_symmetric','x1','z')+_exists('v')+('split','exact hg_left','exact hg_right_right_witness_right'),
            'Any two actual irreducible Gaussian factorizations of the same value have equal length and an actual unit-matching finite bijection; distinct leading units are allowed.',
        ),
        spec(
            'gaussian_prime_factorizations_unique',f"forall z u b c l v d e m. ({_prime_factor('z','u','b','c','l','unique_first_prime_factorization')}) -> ({_prime_factor('z','v','d','e','m','unique_second_prime_factorization')}) -> ({_uniqueness('b','c','l','d','e','m','unique_prime_factorizations')})",
            ('gaussian_irreducible_factorizations_unique','gaussian_prime_factorization_is_irreducible'),
            _intro('z','u','b','c','l','v','d','e','m','hf','hg')+_call('gaussian_irreducible_factorizations_unique','z','u','b','c','l','v','d','e','m')
            +_call('gaussian_prime_factorization_is_irreducible','z','u','b','c','l')+('exact hf',)+_call('gaussian_prime_factorization_is_irreducible','z','v','d','e','m')+('exact hg',),
            'The uniqueness theorem applies to every actual RingPrime factorization, using the proved prime/irreducible equivalence rather than redefining a prime label.',
        ),
        spec(
            'gaussian_unique_prime_factorization',f"forall z. ({_valid('z','unique_factorization_domain')}) -> ~(z=0) -> ({_unique_prime_factorization('z','unique_factorization_result')})",
            ('gaussian_prime_factorization_exists','gaussian_prime_factorizations_unique'),
            _intro('z','hv','hz')+(f"have hf : exists u b c l. ({_prime_factor('z','u','b','c','l','unique_factorization_constructed')})",)
            +_call('gaussian_prime_factorization_exists','z')+('exact hv','exact hz')+_cases('hf',4)+_exists('x','x1','x2','x3')+('split','exact hf_witness_witness_witness_witness')
            +_intro('v','d','e','m','hg')+_call('gaussian_prime_factorizations_unique','z','x','x1','x2','x3','v','d','e','m')+('exact hf_witness_witness_witness_witness','exact hg'),
            'Full constructive G082: every actual nonzero Gaussian integer has a finite actual RingPrime factorization, and every other such factorization differs by a constructed beta permutation and witnessed multiplicative units.',
        ),
        spec(
            'gaussian_zero_has_no_prime_factorization',f"forall u b c l. ~({_prime_factor('0','u','b','c','l','zero_prime_factorization')})",
            ('gaussian_factorization_value_nonzero','gaussian_prime_factorization_is_irreducible'),
            _intro('u','b','c','l','hf')+_call('gaussian_factorization_value_nonzero','0','u','b','c','l')+_call('gaussian_prime_factorization_is_irreducible','0','u','b','c','l')+('exact hf','refl'),
            'The actual zero Gaussian code has no finite unit-times-prime factorization; the nonzero guard is mathematically necessary.',
        ),
        spec(
            'gaussian_unit_prime_factorization_length_zero',f"forall z u b c l. ({_prime_factor('z','u','b','c','l','unit_prime_factorization')}) -> ({_unit('z','unit_prime_value')}) -> l=0",
            ('gaussian_prime_factorization_is_irreducible','gaussian_all_irreducible_product_unit_length_zero','gaussian_unit_factor_right'),
            _intro('z','u','b','c','l','hf','hu')+(f"have hg : ({_factor('z','u','b','c','l','unit_irreducible_factorization')})",)
            +_call('gaussian_prime_factorization_is_irreducible','z','u','b','c','l')+('exact hf',)+_parts('hg',3)+('cases hg_right_right','cases hg_right_right_witness')
            +_call('gaussian_all_irreducible_product_unit_length_zero','b','c','l','x')+('exact hg_right_left','exact hg_right_right_witness_left')+_call('gaussian_unit_factor_right','u','x','z')+('exact hg_right_right_witness_right','exact hu'),
            'Every factorization of any of the four actual Gaussian units has an empty prime list, proved from actual product and inverse witnesses.',
        ),
    )


def make_gaussian_factor_permutation_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _association_rows(spec)+_matching_rows(spec)+_swap_rows(spec)+_swap_product_rows(spec)+_product_uniqueness_rows(spec)+_complete_rows(spec)
