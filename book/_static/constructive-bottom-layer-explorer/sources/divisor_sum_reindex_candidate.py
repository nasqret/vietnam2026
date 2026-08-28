"""Constructive permutation invariance of actual finite signed sums.

Every map and composed stream is beta-coded.  The proof reconstructs real
component compositions, uses the original natural-sum permutation theorem,
and then proves independence of signed representatives.  No finite choice,
sum rearrangement, or cancellation oracle is introduced.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_table_candidate import _pack, _rep, _signed_sum, _sum, _table, _table_at, _table_equal, _components
from .finite_modular_set_candidate import _compose
from .gaussian_euclidean_candidate import _balance
from .prime_factorization_permutation_candidate import _bounded, _injective
from .prime_valuation_support_candidate import _and, _at, _call, _cases, _intro, _lt, _parts, _public, _rewrite


def _reindex(F: str, G: str, r: str, s: str, l: str, tag: str) -> str:
    i,j,a=('dsr_'+role+'_'+tag for role in ('index','image','value'))
    return (f'forall {i} {j} {a}. ({_lt(i,l,tag+"bound")}) -> ({_at(r,s,i,j,tag+"map")}) -> '
            f'({_table_at(F,j,a,tag+"source")}) -> ({_table_at(G,i,a,tag+"target")})')


def signed_arithmetic_table_reindex_relation(F: str, G: str, r: str, s: str, l: str, *, tag: str, variables: tuple[str,...]) -> str:
    """The actual map beta(r,s,i) pulls each signed source lookup into G."""
    return _public(_reindex,(F,G,r,s,l),tag=tag,variables=variables)


def _component_data(a: tuple[str,...], b: tuple[str,...], r: str, s: str, l: str, tag: str) -> str:
    return _and(_compose(r,s,*a[:2],*b[:2],l,tag=tag+'positive'),_compose(r,s,*a[2:],*b[2:],l,tag=tag+'negative'))


def _construction_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    a=('pb','pc','nb','nc'); b=('qb','qc','mb','mc')
    return (
        spec(
            'divisor_signed_table_lookup_from_components',
            f"forall F {' '.join(a)} i. ({_rep('F',*a,'lookup_rep')}) -> exists z. ({_table_at('F','i','z','lookup_result')})",
            ('divisor_signed_table_from_components','divisor_signed_table_lookup','le_refl'),
            _intro('F',*a,'i','hrep')+_call('divisor_signed_table_lookup','i','F','i')
            +_call('divisor_signed_table_from_components','i','F',*a)+('exact hrep',)+_call('le_refl','i'),
            'Actual component streams construct a canonical lookup at any specified index; finite consumers retain their explicit index bounds.',
        ),
        spec(
            'divisor_signed_table_reindex_data_exists',
            f"forall {' '.join(a)} r s l. exists {' '.join(b)}. ({_component_data(a,b,'r','s','l','data')})",
            ('finite_beta_composition_exists',),
            _intro(*a,'r','s','l')
            +(f"have hp : exists q c. ({_compose('r','s','pb','pc','q','c','l',tag='data_first')})",)
            +_call('finite_beta_composition_exists','r','s','pb','pc','l')+_cases('hp',2)
            +(f"have hn : exists m c. ({_compose('r','s','nb','nc','m','c','l',tag='data_second')})",)
            +_call('finite_beta_composition_exists','r','s','nb','nc','l')+_cases('hn',2)
            +('exists x','exists x1','exists x2','exists x3','split','exact hp_witness_witness','exact hn_witness_witness'),
            'Two real finite beta compositions are constructed before any permutation argument; no supplied composed table is assumed.',
        ),
        spec(
            'divisor_signed_table_reindex_from_components',
            f"forall F G {' '.join(a+b)} r s l. ({_rep('F',*a,'component_source')}) -> ({_rep('G',*b,'component_target')}) -> "
            f"({_component_data(a,b,'r','s','l','component_data')}) -> ({_reindex('F','G','r','s','l','component_result')})",
            ('divisor_signed_table_at_to_components','divisor_signed_table_at_from_components'),
            _intro('F','G',*a,*b,'r','s','l','hF','hG','hcompose','i','j','z','hi','hmap','hsource')+('cases hcompose',)
            +(f"have hparts : exists p n. ({_components(*a,'j','p','n','z','component_values')})",)
            +_call('divisor_signed_table_at_to_components','F',*a,'j','z')+('exact hF','exact hsource')+_cases('hparts',2)+_parts('hparts_witness_witness',3)
            +_call('divisor_signed_table_at_from_components','G',*b,'i','x','x1','z')+('exact hG',)
            +_call('hcompose_left','i','j','x')+('exact hi','exact hmap','exact hparts_witness_witness_left')
            +_call('hcompose_right','i','j','x1')+('exact hi','exact hmap','exact hparts_witness_witness_right_left','exact hparts_witness_witness_right_right'),
            'Real component composition implements the signed lookup pullback exactly, at every bounded target index.',
        ),
        spec(
            'divisor_signed_table_reindex_exists',
            f"forall N F r s l. ({_table('N','F','constructed_source')}) -> exists G. ({_table('l','G','constructed_target')}) /\\ ({_reindex('F','G','r','s','l','constructed_reindex')})",
            ('divisor_signed_table_components','divisor_signed_table_reindex_data_exists','divisor_signed_table_from_components','divisor_signed_table_reindex_from_components'),
            _intro('N','F','r','s','l','ht')+(f"have hrep : exists pb pc nb nc. ({_rep('F',*a,'construct_rep')})",)
            +_call('divisor_signed_table_components','N','F')+('exact ht',)+_cases('hrep',4)
            +(f"have hdata : exists qb qc mb mc. ({_component_data(('x','x1','x2','x3'),b,'r','s','l','construct_data')})",)
            +_call('divisor_signed_table_reindex_data_exists','x','x1','x2','x3','r','s','l')+_cases('hdata',4)
            +(f"exists {_pack('x4','x5','x6','x7')}",'split')
            +_call('divisor_signed_table_from_components','l',_pack('x4','x5','x6','x7'),'x4','x5','x6','x7')+('refl',)
            +_call('divisor_signed_table_reindex_from_components','F',_pack('x4','x5','x6','x7'),'x','x1','x2','x3','x4','x5','x6','x7','r','s','l')
            +('exact hrep_witness_witness_witness_witness','refl','exact hdata_witness_witness_witness_witness'),
            'Any actual finite signed table admits a genuinely beta-coded pullback along an actual beta map, with its new table code constructed.',
        ),
        spec(
            'divisor_signed_table_reindex_functional',
            f"forall F G H {' '.join(a)} r s l. ({_rep('F',*a,'functional_source')}) -> ({_reindex('F','G','r','s','l','functional_first')}) -> "
            f"({_reindex('F','H','r','s','l','functional_second')}) -> ({_table_equal('G','H','l','functional_result')})",
            ('beta_at_exists','divisor_signed_table_lookup_from_components','divisor_signed_table_at_functional'),
            _intro('F','G','H',*a,'r','s','l','hrep','hG','hH','i','u','v','hi','hu','hv')
            +(f"have hmap : exists j. ({_at('r','s','i','j','functional_map')})",)
            +_call('beta_at_exists','r','s','i')+('cases hmap',f"have hsource : exists z. ({_table_at('F','x','z','functional_value')})")
            +_call('divisor_signed_table_lookup_from_components','F',*a,'x')+('exact hrep','cases hsource','trans x1')
            +_call('divisor_signed_table_at_functional','G','i','u','x1')+('exact hu',)
            +_call('hG','i','x','x1')+('exact hi','exact hmap_witness','exact hsource_witness','symm')
            +_call('divisor_signed_table_at_functional','H','i','v','x1')+('exact hv',)
            +_call('hH','i','x','x1')+('exact hi','exact hmap_witness','exact hsource_witness'),
            'All actual pullbacks of the same signed table and map agree in canonical value, even when their component representatives differ.',
        ),
    )


def _sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    a=('pb','pc','nb','nc'); b=('qb','qc','mb','mc')
    return (
        spec(
            'divisor_signed_sum_component_reindex',
            f"forall F G {' '.join(a+b)} r s l u v. ({_rep('F',*a,'sum_source_pack')}) -> ({_rep('G',*b,'sum_target_pack')}) -> "
            f"({_bounded('r','s','l','sum_map_bounded')}) -> ({_injective('r','s','l','sum_map_injective')}) -> "
            f"({_component_data(a,b,'r','s','l','sum_component_composition')}) -> ({_signed_sum('F','l','u','sum_source')}) -> ({_signed_sum('G','l','v','sum_target')}) -> u = v",
            ('divisor_signed_sum_to_components','beta_sum_permutation_invariant','signed_balance_functional'),
            _intro('F','G',*a,*b,'r','s','l','u','v','hF','hG','hbound','hinj','hcomp','hu','hv')+('cases hcomp',)
            +(f"have hfirst : exists p n. {_and(_sum('pb','pc','l','p','sum_first_positive'),_sum('nb','nc','l','n','sum_first_negative'),_balance('u','p','n','sum_first_balance'))}",)
            +_call('divisor_signed_sum_to_components','F',*a,'l','u')+('exact hF','exact hu')+_cases('hfirst',2)+_parts('hfirst_witness_witness',3)
            +(f"have hsecond : exists p n. {_and(_sum('qb','qc','l','p','sum_second_positive'),_sum('mb','mc','l','n','sum_second_negative'),_balance('v','p','n','sum_second_balance'))}",)
            +_call('divisor_signed_sum_to_components','G',*b,'l','v')+('exact hG','exact hv')+_cases('hsecond',2)+_parts('hsecond_witness_witness',3)
            +('have hp : x2 = x','symm')+_call('beta_sum_permutation_invariant','l','r','s','pb','pc','qb','qc','x','x2')
            +('exact hbound','exact hinj','exact hcomp_left','exact hfirst_witness_witness_left','exact hsecond_witness_witness_left',
                'have hn : x3 = x1','symm')+_call('beta_sum_permutation_invariant','l','r','s','nb','nc','mb','mc','x1','x3')
            +('exact hbound','exact hinj','exact hcomp_right','exact hfirst_witness_witness_right_left','exact hsecond_witness_witness_right_left')
            +_rewrite('hp',_balance('v','x2','x3','sum_recode_positive'),'x2','hsecond_witness_witness_right_right')
            +_rewrite('hn',_balance('v','x','x3','sum_recode_negative'),'x3','hsecond_witness_witness_right_right')
            +_call('signed_balance_functional','x','x1','u','v')+('exact hfirst_witness_witness_right_right','exact hsecond_witness_witness_right_right'),
            'Original finite natural-sum permutation invariance preserves both actual component sums, hence their canonical signed result.',
        ),
        spec(
            'divisor_signed_sum_permutation_invariant',
            f"forall F G r s l u v. ({_bounded('r','s','l','permutation_bound')}) -> ({_injective('r','s','l','permutation_injective')}) -> "
            f"({_reindex('F','G','r','s','l','permutation_pullback')}) -> ({_signed_sum('F','l','u','permutation_source')}) -> ({_signed_sum('G','l','v','permutation_target')}) -> u = v",
            ('divisor_signed_table_reindex_data_exists','divisor_signed_sum_exists_from_components',
             'divisor_signed_sum_component_reindex','divisor_signed_sum_extensional','divisor_signed_table_reindex_functional','divisor_signed_table_reindex_from_components'),
            _intro('F','G','r','s','l','u','v','hbound','hinj','hreindex','hu','hv')+_cases('hu',6)+_parts('hu'+'_witness'*6,4)
            +(f"have hdata : exists qb qc mb mc. ({_component_data(('x','x1','x2','x3'),b,'r','s','l','permutation_constructed')})",)
            +_call('divisor_signed_table_reindex_data_exists','x','x1','x2','x3','r','s','l')+_cases('hdata',4)
            +(f"have hsum : exists z. ({_signed_sum(_pack('x6','x7','x8','x9'),'l','z','permutation_actual_sum')})",)
            +_call('divisor_signed_sum_exists_from_components',_pack('x6','x7','x8','x9'),'x6','x7','x8','x9','l')
            +('refl','cases hsum','have heq : u = x10')
            +_call('divisor_signed_sum_component_reindex','F',_pack('x6','x7','x8','x9'),'x','x1','x2','x3','x6','x7','x8','x9','r','s','l','u','x10')
            +('exact hu_witness_witness_witness_witness_witness_witness_left','refl','exact hbound','exact hinj','exact hdata_witness_witness_witness_witness','exact hu','exact hsum_witness',
                'trans x10','exact heq')
            +_call('divisor_signed_sum_extensional',_pack('x6','x7','x8','x9'),'G','l','x10','v')
            +_call('divisor_signed_table_reindex_functional','F',_pack('x6','x7','x8','x9'),'G','x','x1','x2','x3','r','s','l')
            +('exact hu_witness_witness_witness_witness_witness_witness_left',)
            +_call('divisor_signed_table_reindex_from_components','F',_pack('x6','x7','x8','x9'),'x','x1','x2','x3','x6','x7','x8','x9','r','s','l')
            +('exact hu_witness_witness_witness_witness_witness_witness_left','refl','exact hdata_witness_witness_witness_witness','exact hreindex','exact hsum_witness','exact hv'),
            'Any actual bounded injective beta permutation preserves the genuine signed sum, even for unrelated positive/negative representations of the pullback table.',
        ),
    )


def make_divisor_sum_reindex_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _construction_rows(spec)+_sum_rows(spec)


__all__=['signed_arithmetic_table_reindex_relation','make_divisor_sum_reindex_candidate_theorems']
