"""Genuine finite signed-table extension over the frozen non-admitting basis.

Both natural beta streams are actually recoded.  The preserved prefix consists
of precisely i<l, and the new entry is the arbitrary canonical signed code z.
The old inclusive table bound N supplies a genuine packing; beta streams are
total, so l need not equal N.  No table-code or component uniqueness is inferred
from equality of represented signed values.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import (
    _components, _pack, _rep, _signed_sum, _table, _table_at, _table_equal,
)
from .gaussian_euclidean_candidate import _balance, _sd
from .prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _intro, _le, _lt, _parts, _preserve, _public, _rewrite,
)


def _extension(F: str, G: str, l: str, z: str, tag: str) -> str:
    return _and(_table(l,G,tag+'table'), _table_equal(F,G,l,tag+'prefix'),
                _table_at(G,l,z,tag+'last'))


def signed_arithmetic_table_extension_relation(
    F: str, G: str, l: str, z: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """Actual output table, preserved signed prefix i<l and prescribed entry l."""
    return _public(_extension,(F,G,l,z),tag=tag,variables=variables)


def _component_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    old=('pb','pc','nb','nc')
    new=('qb','qc','mb','mc')
    return (
        spec(
            'arithmetic_signed_table_component_prefix_preserved',
            f"forall F G {' '.join(old+new)} l. ({_rep('F',*old,'preserve_source')}) -> "
            f"({_rep('G',*new,'preserve_target')}) -> ({_preserve('pb','pc','qb','qc','l','preserve_positive')}) -> "
            f"({_preserve('nb','nc','mb','mc','l','preserve_negative')}) -> ({_table_equal('F','G','l','preserve_result')})",
            ('divisor_signed_table_at_to_components','divisor_signed_table_at_from_components',
             'divisor_signed_table_at_functional'),
            _intro('F','G',*old,*new,'l','hF','hG','hp','hn','i','a','b','hi','ha','hb')
            +(f"have hparts : exists p n. ({_components(*old,'i','p','n','a','preserve_components')})",)
            +_call('divisor_signed_table_at_to_components','F',*old,'i','a')
            +('exact hF','exact ha')+_cases('hparts',2)+_parts('hparts_witness_witness',3)
            +_call('divisor_signed_table_at_functional','G','i','a','b')
            +_call('divisor_signed_table_at_from_components','G',*new,'i','x','x1','a')
            +('exact hG',)+_call('hp','i','x')+('exact hi','exact hparts_witness_witness_left')
            +_call('hn','i','x1')+('exact hi','exact hparts_witness_witness_right_left',
                'exact hparts_witness_witness_right_right','exact hb'),
            'Preservation of both actual natural beta prefixes preserves canonical signed values without identifying distinct component representations.',
        ),
        spec(
            'arithmetic_signed_table_equal_entry_transport',
            f"forall N F G l i z. ({_table('N','G','transport_valid')}) -> ({_table_equal('F','G','l','transport_prefix')}) -> "
            f"({_le('i','N','transport_domain')}) -> ({_lt('i','l','transport_index')}) -> "
            f"({_table_at('F','i','z','transport_source')}) -> ({_table_at('G','i','z','transport_target')})",
            ('divisor_signed_table_lookup',),
            _intro('N','F','G','l','i','z','ht','he','hiN','hil','hz')
            +(f"have hb : exists b. ({_table_at('G','i','b','transport_lookup')})",)
            +_call('divisor_signed_table_lookup','N','G','i')+('exact ht','exact hiN','cases hb','have heq : x = z','symm')
            +_call('he','i','z','x')+('exact hil','exact hz','exact hb_witness')
            +_rewrite('heq',_table_at('G','i','x','transport_rewrite'),'x','hb_witness')+('exact hb_witness',),
            'Actual finite-domain lookup plus prefix equality transports a signed value; no table-component equality or unspecified choice is used.',
        ),
    )


def _extension_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    positive=_and(_at('b','c','l','x4','extend_last_positive'),_preserve('x','x1','b','c','l','extend_old_positive'))
    negative=_and(_at('b','c','l','x5','extend_last_negative'),_preserve('x2','x3','b','c','l','extend_old_negative'))
    new=('x6','x7','x8','x9')
    G=_pack(*new)
    empty=_pack('0','0','0','0')
    return (
        spec(
            'arithmetic_signed_table_extend_at',
            f"forall N F l z. ({_table('N','F','extend_input')}) -> exists G. ({_extension('F','G','l','z','extend_output')})",
            ('divisor_signed_table_components','signed_decode_total','beta_prefix_extend',
             'divisor_signed_table_from_components','arithmetic_signed_table_component_prefix_preserved',
             'divisor_signed_table_at_from_components','add_comm'),
            _intro('N','F','l','z','ht')
            +(f"have hrep : exists pb pc nb nc. ({_rep('F','pb','pc','nb','nc','extend_packing')})",)
            +_call('divisor_signed_table_components','N','F')+('exact ht',)+_cases('hrep',4)
            +(f"have hd : exists p n. ({_sd('z','p','n','extend_decode')})",)
            +_call('signed_decode_total','z')+_cases('hd',2)
            +(f"have hp : exists b c. ({positive})",)+_call('beta_prefix_extend','l','x','x1','x4')
            +_cases('hp',2)+('cases hp_witness_witness',)
            +(f"have hn : exists b c. ({negative})",)+_call('beta_prefix_extend','l','x2','x3','x5')
            +_cases('hn',2)+('cases hn_witness_witness',f'exists {G}','split')
            +_call('divisor_signed_table_from_components','l',G,*new)+('refl','split')
            +_call('arithmetic_signed_table_component_prefix_preserved','F',G,'x','x1','x2','x3',*new,'l')
            +('exact hrep_witness_witness_witness_witness','refl','exact hp_witness_witness_right','exact hn_witness_witness_right')
            +_call('divisor_signed_table_at_from_components',G,*new,'l','x4','x5','z')
            +('refl','exact hp_witness_witness_left','exact hn_witness_witness_left',
                'exists x4','exists x5','split','exact hd_witness_witness','apply add_comm'),
            'Decode the requested signed value, extend both beta streams at l, and explicitly construct the new packed table preserving exactly its earlier signed entries.',
        ),
        spec(
            'arithmetic_signed_table_append',
            f"forall N F z. ({_table('N','F','append_input')}) -> exists G. ({_extension('F','G','S N','z','append_output')})",
            ('arithmetic_signed_table_extend_at',),
            _intro('N','F','z','ht')+_call('arithmetic_signed_table_extend_at','N','F','S N','z')+('exact ht',),
            'Append at the next index after the inclusive input domain, preserving every existing value through N.',
        ),
        spec(
            'arithmetic_signed_table_singleton',
            f"forall z. exists F. ({_table('0','F','singleton_valid')}) /\\ ({_table_at('F','0','z','singleton_value')})",
            ('arithmetic_signed_table_extend_at','divisor_signed_table_from_components'),
            _intro('z')+(f"have he : exists G. ({_extension(empty,'G','0','z','singleton_construct')})",)
            +_call('arithmetic_signed_table_extend_at','0',empty,'0','z')
            +_call('divisor_signed_table_from_components','0',empty,'0','0','0','0')+('refl','cases he')
            +_parts('he_witness',3)+('exists x','split','exact he_witness_left','exact he_witness_right_right'),
            'The base table contains an arbitrary prescribed signed value at index zero, with actual beta and packing witnesses.',
        ),
    )


def _sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'arithmetic_signed_sum_exists',
            f"forall N F l. ({_table('N','F','sum_exists_input')}) -> exists z. ({_signed_sum('F','l','z','sum_exists_output')})",
            ('divisor_signed_table_components','divisor_signed_sum_exists_from_components'),
            _intro('N','F','l','ht')+(f"have hrep : exists pb pc nb nc. ({_rep('F','pb','pc','nb','nc','sum_exists_rep')})",)
            +_call('divisor_signed_table_components','N','F')+('exact ht',)+_cases('hrep',4)
            +_call('divisor_signed_sum_exists_from_components','F','x','x1','x2','x3','l')
            +('exact hrep_witness_witness_witness_witness',),
            'A genuinely packed signed table has actual finite positive and negative sum traces at every requested prefix length.',
        ),
        spec(
            'arithmetic_signed_sum_append_transport',
            f"forall F G l a b c. ({_table('l','G','append_sum_valid')}) -> ({_table_equal('F','G','l','append_sum_prefix')}) -> "
            f"({_signed_sum('F','l','a','append_sum_before')}) -> ({_table_at('G','l','b','append_sum_entry')}) -> "
            f"({_add_code('a','b','c','append_sum_add')}) -> ({_signed_sum('G','S l','c','append_sum_result')})",
            ('arithmetic_signed_sum_exists','divisor_signed_sum_extensional','divisor_signed_sum_successor_intro'),
            _intro('F','G','l','a','b','c','ht','he','hs','hb','hadd')
            +(f"have hx : exists x. ({_signed_sum('G','l','x','append_sum_actual')})",)
            +_call('arithmetic_signed_sum_exists','l','G','l')+('exact ht','cases hx','have heq : x = a','symm')
            +_call('divisor_signed_sum_extensional','F','G','l','a','x')+('exact he','exact hs','exact hx_witness')
            +_rewrite('heq',_signed_sum('G','l','x','append_sum_rewrite'),'x','hx_witness')
            +_call('divisor_signed_sum_successor_intro','G','l','a','b','c')
            +('exact hx_witness','exact hb','exact hadd'),
            'A recoded prefix has the same actual signed sum; adding its prescribed next entry constructs the extended fold.',
        ),
    )


def make_arithmetic_table_extension_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _component_rows(spec)+_extension_rows(spec)+_sum_rows(spec)


__all__ = ['signed_arithmetic_table_extension_relation','make_arithmetic_table_extension_candidate_theorems']
