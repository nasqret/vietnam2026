"""Checked signed-prefix algebra over actual packed beta tables.

The finite sums remain the two original natural folds followed by canonical
signed balance.  These rows establish representation independence, negation,
and successor algebra without assuming a divisor identity.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_table_candidate import _components, _pack, _rep, _signed_sum, _sum, _table_at, _table_equal
from .gaussian_euclidean_candidate import _balance, _sd
from .integer_column_span_candidate import _equal
from .mobius_prime_step_candidate import _negate
from .prime_valuation_support_candidate import _and, _at, _call, _cases, _intro, _lt, _part, _parts, _rewrite


def _add_code(a: str, b: str, c: str, tag: str) -> str:
    ap,an,bp,bn,cp,cn=('dsa_'+role+'_'+tag for role in ('ap','an','bp','bn','cp','cn'))
    return f'exists {ap} {an} {bp} {bn} {cp} {cn}. '+_and(
        _sd(a,ap,an,tag+'left'),_sd(b,bp,bn,tag+'right'),_sd(c,cp,cn,tag+'output'),
        f'({ap} + {bp}) + {cn} = ({an} + {bn}) + {cp}')


def _natural_decomposition(b: str, c: str, l: str, t: str, tag: str) -> str:
    a,r='dsa_summand_'+tag,'dsa_partial_'+tag
    return f'exists {a} {r}. '+_and(_at(b,c,l,a,tag+'last'),_sum(b,c,l,r,tag+'prefix'),f'({t}) = {r} + {a}')


def _scalar_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'divisor_signed_balance_negate',
            f"forall a b p n. ({_balance('a','p','n','negate_balance')}) -> ({_negate('a','b','negate_graph')}) -> ({_balance('b','n','p','negate_result')})",
            ('signed_negate_to_swapped_decode',),
            _intro('a','b','p','n','hbalance','hneg')+_cases('hbalance',2)+('cases hbalance_witness_witness','exists x1','exists x','split')
            +_call('signed_negate_to_swapped_decode','a','b','x','x1')
            +('exact hbalance_witness_witness_left','exact hneg','symm','exact hbalance_witness_witness_right'),
            'Canonical signed negation swaps arbitrary natural-component balances, not merely normalized representatives.',
        ),
        spec(
            'divisor_signed_balance_negate_intro',
            f"forall a b p n. ({_balance('a','p','n','negate_intro_first')}) -> ({_balance('b','n','p','negate_intro_second')}) -> ({_negate('a','b','negate_intro_result')})",
            ('signed_negate_total','divisor_signed_balance_negate','signed_balance_functional'),
            _intro('a','b','p','n','ha','hb')+(f"have hn : exists c. ({_negate('a','c','negate_intro_exists')})",)
            +_call('signed_negate_total','a')+('cases hn','have heq : x = b')
            +_call('signed_balance_functional','n','p','x','b')
            +_call('divisor_signed_balance_negate','a','x','p','n')+('exact ha','exact hn_witness','exact hb')
            +_rewrite('heq',_negate('a','x','negate_intro_rewrite'),'x','hn_witness')+('exact hn_witness',),
            'Opposite arbitrary component balances imply actual canonical SignedNegate, using its constructed inverse and literal functionality.',
        ),
        spec(
            'divisor_signed_negate_fixed_zero',
            f"forall a. ({_negate('a','a','fixed_negation')}) -> a = 0",
            ('signed_decode_functional','signed_balance_zero_iff','add_comm'),
            _intro('a','hneg')+_cases('hneg',2)+('cases hneg_witness_witness','have heq : x = x1 /\\ x1 = x')
            +_call('signed_decode_functional','a','x','x1','x1','x')
            +('exact hneg_witness_witness_left','exact hneg_witness_witness_right','cases heq',
                f"have hb : {_balance('a','x','x1','fixed_balance')}",'exists x','exists x1','split','exact hneg_witness_witness_left','apply add_comm',
                'have hz : (a = 0 -> x = x1) /\\ (x = x1 -> a = 0)')
            +_call('signed_balance_zero_iff','a','x','x1')+('exact hb','cases hz','apply hz_right','exact heq_left'),
            'A canonical signed integer equal to its own additive inverse is zero; no characteristic-zero claim is assumed without proof.',
        ),
        spec(
            'divisor_natural_sum_successor_intro',
            f"forall b c l r a. ({_sum('b','c','l','r','natural_step_prefix')}) -> ({_at('b','c','l','a','natural_step_last')}) -> ({_sum('b','c','S l','r + a','natural_step_result')})",
            ('beta_sum_exists','beta_sum_succ_decompose','beta_at_unique','beta_sum_functional'),
            _intro('b','c','l','r','a','hs','ha')+(f"have ht : exists t. ({_sum('b','c','S l','t','natural_step_exists')})",)
            +_call('beta_sum_exists','b','c','S l')+('cases ht',f"have hd : {_natural_decomposition('b','c','l','x','natural_step_decomp')}")
            +_call('beta_sum_succ_decompose','b','c','l','x')+('exact ht_witness',)+_cases('hd',2)+_parts('hd_witness_witness',3)
            +('have heqa : x1 = a',)+_call('beta_at_unique','b','c','l','x1','a')
            +('exact hd_witness_witness_left','exact ha','have heqr : x2 = r')
            +_call('beta_sum_functional','b','c','l','x2','r')+('exact hd_witness_witness_right_left','exact hs',
                'have heq : x = r + a','trans x2 + x1','exact hd_witness_witness_right_right','rewrite heqr','rewrite heqa','refl')
            +_rewrite('heq',_sum('b','c','S l','x','natural_step_rewrite'),'x','ht_witness')+('exact ht_witness',),
            'The successor natural sum is genuinely constructed and identified with the previous sum plus the actual last beta entry.',
        ),
    )


def _extensional_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    a=('pb','pc','nb','nc')
    b=('qb','qc','mb','mc')
    return (
        spec(
            'divisor_signed_table_equality_component_balance',
            f"forall F G {' '.join(a+b)} l. ({_rep('F',*a,'equal_first_pack')}) -> ({_rep('G',*b,'equal_second_pack')}) -> "
            f"({_table_equal('F','G','l','equal_codes')}) -> ({_equal(*a,*b,'l','equal_components')})",
            ('signed_balance_total','divisor_signed_table_at_from_components','gaussian_signed_balance_same_code'),
            _intro('F','G',*a,*b,'l','hF','hG','hequal','i','p','n','q','m','hi','hp','hn','hq','hm')
            +(f"have hx : exists x. ({_balance('x','p','n','equal_first_value')})",)
            +_call('signed_balance_total','p','n')+('cases hx',f"have hy : exists y. ({_balance('y','q','m','equal_second_value')})")
            +_call('signed_balance_total','q','m')+('cases hy','have heq : x = x1')
            +_call('hequal','i','x','x1')+('exact hi',)
            +_call('divisor_signed_table_at_from_components','F',*a,'i','p','n','x')
            +('exact hF','exact hp','exact hn','exact hx_witness')
            +_call('divisor_signed_table_at_from_components','G',*b,'i','q','m','x1')
            +('exact hG','exact hq','exact hm','exact hy_witness')
            +_rewrite('heq',_balance('x','p','n','equal_code_rewrite'),'x','hx_witness')
            +_call('gaussian_signed_balance_same_code','x1','p','n','q','m')
            +('exact hx_witness','exact hy_witness'),
            'Pointwise equality of canonical lookup values implies balanced integer equality of arbitrary component streams, without equating the components themselves.',
        ),
        spec(
            'divisor_signed_sum_extensional',
            f"forall F G l a b. ({_table_equal('F','G','l','sum_ext_entries')}) -> ({_signed_sum('F','l','a','sum_ext_first')}) -> "
            f"({_signed_sum('G','l','b','sum_ext_second')}) -> a = b",
            ('divisor_signed_table_equality_component_balance','matrix_integer_signed_sum_balance','signed_balance_extensional','add_comm'),
            _intro('F','G','l','a','b','hequal','ha','hb')+_cases('ha',6)+_parts('ha'+'_witness'*6,4)
            +_cases('hb',6)+_parts('hb'+'_witness'*6,4)+('have hbalance : x4 + x11 = x10 + x5',)
            +_call('matrix_integer_signed_sum_balance','x','x1','x2','x3','x6','x7','x8','x9','l','x4','x5','x10','x11')
            +_call('divisor_signed_table_equality_component_balance','F','G','x','x1','x2','x3','x6','x7','x8','x9','l')
            +('exact ha_witness_witness_witness_witness_witness_witness_left','exact hb_witness_witness_witness_witness_witness_witness_left','exact hequal',
                'exact ha_witness_witness_witness_witness_witness_witness_right_left','exact ha_witness_witness_witness_witness_witness_witness_right_right_left',
                'exact hb_witness_witness_witness_witness_witness_witness_right_left','exact hb_witness_witness_witness_witness_witness_witness_right_right_left')
            +_call('signed_balance_extensional','a','b','x4','x5','x10','x11')
            +('exact ha_witness_witness_witness_witness_witness_witness_right_right_right','exact hb_witness_witness_witness_witness_witness_witness_right_right_right',
                'trans x10 + x5','exact hbalance','apply add_comm'),
            'Signed prefix sums are independent of all pointwise balanced positive/negative representatives, by the checked natural cross-sum theorem.',
        ),
        spec(
            'divisor_signed_sum_negation_transport',
            f"forall F G {' '.join(a)} l a b. ({_rep('F',*a,'negation_source_pack')}) -> ({_rep('G','nb','nc','pb','pc','negation_target_pack')}) -> "
            f"({_signed_sum('F','l','a','negation_source_sum')}) -> ({_negate('a','b','negation_relation')}) -> ({_signed_sum('G','l','b','negation_target_sum')})",
            ('divisor_signed_sum_to_components','divisor_signed_sum_from_components','divisor_signed_balance_negate'),
            _intro('F','G',*a,'l','a','b','hF','hG','hs','hn')
            +(f"have hparts : exists p n. {_and(_sum('pb','pc','l','p','negation_positive'),_sum('nb','nc','l','n','negation_negative'),_balance('a','p','n','negation_balance'))}",)
            +_call('divisor_signed_sum_to_components','F',*a,'l','a')+('exact hF','exact hs')+_cases('hparts',2)+_parts('hparts_witness_witness',3)
            +_call('divisor_signed_sum_from_components','G','nb','nc','pb','pc','l','x1','x','b')
            +('exact hG','exact hparts_witness_witness_right_left','exact hparts_witness_witness_left')
            +_call('divisor_signed_balance_negate','a','b','x','x1')+('exact hparts_witness_witness_right_right','exact hn'),
            'Swapping the actual positive/negative beta streams negates their signed sum, using the same genuine natural traces.',
        ),
    )


def _successor_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    a=('pb','pc','nb','nc')
    return (
        spec(
            'divisor_signed_sum_successor_intro',
            f"forall F l a b c. ({_signed_sum('F','l','a','step_sum')}) -> ({_table_at('F','l','b','step_entry')}) -> "
            f"({_add_code('a','b','c','step_add')}) -> ({_signed_sum('F','S l','c','step_result')})",
            ('divisor_signed_table_at_to_components','divisor_signed_sum_from_components','divisor_natural_sum_successor_intro','gaussian_signed_add_to_balance'),
            _intro('F','l','a','b','c','hs','he','hadd')+_cases('hs',6)+_parts('hs'+'_witness'*6,4)
            +(f"have hentry : exists p n. ({_components('x','x1','x2','x3','l','p','n','b','step_components')})",)
            +_call('divisor_signed_table_at_to_components','F','x','x1','x2','x3','l','b')
            +('exact hs_witness_witness_witness_witness_witness_witness_left','exact he')+_cases('hentry',2)+_parts('hentry_witness_witness',3)
            +_call('divisor_signed_sum_from_components','F','x','x1','x2','x3','S l','x4 + x6','x5 + x7','c')
            +('exact hs_witness_witness_witness_witness_witness_witness_left',)
            +_call('divisor_natural_sum_successor_intro','x','x1','l','x4','x6')
            +('exact hs_witness_witness_witness_witness_witness_witness_right_left','exact hentry_witness_witness_left')
            +_call('divisor_natural_sum_successor_intro','x2','x3','l','x5','x7')
            +('exact hs_witness_witness_witness_witness_witness_witness_right_right_left','exact hentry_witness_witness_right_left')
            +_call('gaussian_signed_add_to_balance','a','b','c','x4','x5','x6','x7')
            +('exact hs_witness_witness_witness_witness_witness_witness_right_right_right','exact hentry_witness_witness_right_right','exact hadd'),
            'A genuine signed prefix sum, its actual next entry and canonical signed addition construct the successor sum.',
        ),
        spec(
            'divisor_signed_sum_successor_decompose',
            f"forall F l z. ({_signed_sum('F','S l','z','decomp_sum')}) -> exists a b. "
            f"{_and(_signed_sum('F','l','a','decomp_prefix'),_table_at('F','l','b','decomp_entry'),_add_code('a','b','z','decomp_add'))}",
            ('beta_sum_succ_decompose','signed_balance_total','divisor_signed_sum_from_components',
             'divisor_signed_table_at_from_components','gaussian_signed_add_of_balances'),
            _intro('F','l','z','hs')+_cases('hs',6)+_parts('hs'+'_witness'*6,4)
            +(f"have hp : {_natural_decomposition('x','x1','l','x4','decomp_positive')}",)
            +_call('beta_sum_succ_decompose','x','x1','l','x4')
            +('exact hs_witness_witness_witness_witness_witness_witness_right_left',)+_cases('hp',2)+_parts('hp_witness_witness',3)
            +(f"have hn : {_natural_decomposition('x2','x3','l','x5','decomp_negative')}",)
            +_call('beta_sum_succ_decompose','x2','x3','l','x5')
            +('exact hs_witness_witness_witness_witness_witness_witness_right_right_left',)+_cases('hn',2)+_parts('hn_witness_witness',3)
            +(f"have ha : exists a. ({_balance('a','x7','x9','decomp_prefix_code')})",)
            +_call('signed_balance_total','x7','x9')+('cases ha',f"have hb : exists b. ({_balance('b','x6','x8','decomp_entry_code')})")
            +_call('signed_balance_total','x6','x8')+('cases hb','exists x10','exists x11','split')
            +_call('divisor_signed_sum_from_components','F','x','x1','x2','x3','l','x7','x9','x10')
            +('exact hs_witness_witness_witness_witness_witness_witness_left','exact hp_witness_witness_right_left','exact hn_witness_witness_right_left','exact ha_witness','split')
            +_call('divisor_signed_table_at_from_components','F','x','x1','x2','x3','l','x6','x8','x11')
            +('exact hs_witness_witness_witness_witness_witness_witness_left','exact hp_witness_witness_left','exact hn_witness_witness_left','exact hb_witness')
            +_call('gaussian_signed_add_of_balances','x10','x11','z','x7','x9','x6','x8')
            +('exact ha_witness','exact hb_witness')
            +_rewrite('hp_witness_witness_right_right',_balance('z','x4','x5','decomp_pos_rewrite'),'x4','hs_witness_witness_witness_witness_witness_witness_right_right_right')
            +_rewrite('hn_witness_witness_right_right',_balance('z','x7 + x6','x5','decomp_neg_rewrite'),'x5','hs_witness_witness_witness_witness_witness_witness_right_right_right')
            +('exact hs_witness_witness_witness_witness_witness_witness_right_right_right',),
            'Every successor signed sum supplies real predecessor and last-entry codes whose original SignedAdd graph gives its result.',
        ),
    )


def make_divisor_sum_algebra_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _scalar_rows(spec)+_extensional_rows(spec)+_successor_rows(spec)


__all__=['make_divisor_sum_algebra_candidate_theorems']
