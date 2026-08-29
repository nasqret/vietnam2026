"""Actual affine slices and their signed finite sums over packed beta tables.

The source is an existing ArithTable, not a function/choice oracle.  A slice
constructs both output beta streams and records equality of their represented
canonical signed values at precisely i<l.  Its separately certified endpoint
i=l is unused.  Neither raw component streams nor table codes are unique.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _pack, _signed_sum, _table, _table_at, _table_equal
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _intro, _lt, _parts, _public, _rewrite,
)


def _index(o: str, s: str, i: str) -> str:
    return f'(({o}) + (({s}) * ({i})))'


def _slice_entry(F: str, G: str, o: str, s: str, i: str, z: str, tag: str) -> str:
    return _and(_table_at(F,_index(o,s,i),z,tag+'source'),_table_at(G,i,z,tag+'output'))


def _slice(F: str, G: str, o: str, s: str, l: str, tag: str) -> str:
    i,z=('srs_'+role+'_'+tag for role in ('index','value'))
    entries=f'forall {i}. ({_lt(i,l,tag+"bound")}) -> exists {z}. ({_slice_entry(F,G,o,s,i,z,tag+"entry")})'
    return _and(_table('0',F,tag+'source_table'),_table(l,G,tag+'output_table'),entries)


def _slice_sum(F: str, o: str, s: str, l: str, z: str, tag: str) -> str:
    G='srs_slice_'+tag
    return f'exists {G}. '+_and(_slice(F,G,o,s,l,tag+'slice'),_signed_sum(G,l,z,tag+'sum'))


def signed_rectangular_slice_relation(
    F: str, G: str, o: str, s: str, l: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """Actual output values G[i]=F[o+s*i] for the strict finite window i<l."""
    return _public(_slice,(F,G,o,s,l),tag=tag,variables=variables)


def signed_rectangular_slice_sum_relation(
    F: str, o: str, s: str, l: str, z: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """An actually constructed affine slice and its actual signed prefix sum."""
    return _public(_slice_sum,(F,o,s,l,z),tag=tag,variables=variables)


def _slice_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    lookup=_intro('F','G','o','s','l','i','z','hs','hi','hz')+_parts('hs',3)
    lookup+=(f"have he : exists a. ({_slice_entry('F','G','o','s','i','a','lookup_entry')})",)
    lookup+=_call('hs_right_right','i')+('exact hi','cases he','cases he_witness','have heq : x = z')
    lookup+=_call('divisor_signed_table_at_functional','G','i','x','z')+('exact he_witness_right','exact hz')
    lookup+=_rewrite('heq',_table_at('F',_index('o','s','i'),'x','lookup_rewrite'),'x','he_witness_left')+('exact he_witness_left',)

    restrict=_intro('F','G','o','s','l','hs')+_parts('hs',3)+('split','exact hs_left','split')
    restrict+=_call('signed_table_domain_resize','S l','l','G')+('exact hs_right_left',)+_intro('i','hi')
    restrict+=_call('hs_right_right','i')+_call('le_succ','S i','l')+('exact hi',)

    empty=_intro('F','G','o','s','hF','hG')+('split','exact hF','split','exact hG')+_intro('i','hi')
    empty+=('cases hi','exfalso')+_call('succ_ne_zero','i')+_call('add_eq_zero_right','x','S i')+('exact hi_witness',)

    unique=_intro('F','G','H','o','s','l','hG','hH','i','a','b','hi','ha','hb')
    unique+=_call('divisor_signed_table_at_functional','F',_index('o','s','i'),'a','b')
    unique+=_call('signed_rectangular_slice_lookup','F','G','o','s','l','i','a')+('exact hG','exact hi','exact ha')
    unique+=_call('signed_rectangular_slice_lookup','F','H','o','s','l','i','b')+('exact hH','exact hi','exact hb')

    entries='exists z. ('+_slice_entry('F','H','o','s','i','z','extend_entry')+')'
    extend=_intro('F','G','H','o','s','l','a','hs','hH','hequal','hsource','hentry')+_parts('hs',3)
    extend+=('split','exact hs_left','split')+_call('signed_table_domain_resize','l','S l','H')+('exact hH',)
    extend+=_intro('i','hi')+(f"have hcase : i = l \\/ ({_lt('i','l','extend_split')})",)
    extend+=_call('finite_lt_succ_eq_or_lt','l','i')+('exact hi','cases hcase')
    extend+=_rewrite('hcase_left',entries,'i')+('exists a','split','exact hsource','exact hentry')
    extend+=(f"have hold : exists z. ({_slice_entry('F','G','o','s','i','z','extend_old')})",)
    extend+=_call('hs_right_right','i')+('exact hcase_right','cases hold','cases hold_witness','exists x','split','exact hold_witness_left')
    extend+=_call('arithmetic_signed_table_equal_entry_transport','i','G','H','l','i','x')
    extend+=_call('signed_table_domain_resize','l','i','H')+('exact hH','exact hequal')+_call('le_refl','i')
    extend+=('exact hcase_right','exact hold_witness_right')

    zero=_pack('0','0','0','0')
    exists=('induction l',)+_intro('F','o','s','hF')+(f'exists {zero}',)
    exists+=_call('signed_rectangular_slice_empty','F',zero,'o','s')+('exact hF',)
    exists+=_call('divisor_signed_table_from_components','0',zero,'0','0','0','0')+('refl',)
    exists+=_intro('F','o','s','hF')+(f"have hp : exists G. ({_slice('F','G','o','s','l','exists_prefix')})",)
    exists+=_call('IH','F','o','s')+('exact hF','cases hp')
    exists+=(f"have hv : exists z. ({_table_at('F',_index('o','s','l'),'z','exists_source')})",)
    exists+=_call('signed_table_lookup_any','0','F',_index('o','s','l'))+('exact hF','cases hv')
    exists+=(f"have he : exists H. {_and(_table('l','H','exists_output'),_table_equal('x','H','l','exists_equal'),_table_at('H','l','x1','exists_last'))}",)
    exists+=_call('arithmetic_signed_table_extend_at','l','x','l','x1')+_parts('hp_witness',3)+('exact hp_witness_right_left','cases he')
    exists+=_parts('he_witness',3)+('exists x2',)+_call('signed_rectangular_slice_extend','F','x','x2','o','s','l','x1')
    exists+=('exact hp_witness','exact he_witness_left','exact he_witness_right_left','exact hv_witness','exact he_witness_right_right')

    exists_unique=_intro('F','o','s','l','hF')+(f"have hg : exists G. ({_slice('F','G','o','s','l','unique_construct')})",)
    exists_unique+=_call('signed_rectangular_slice_exists','l','F','o','s')+('exact hF','cases hg','exists x','split','exact hg_witness')
    exists_unique+=_intro('H','hH')+_call('signed_rectangular_slice_extensional_unique','F','x','H','o','s','l')+('exact hg_witness','exact hH')
    return (
        spec('signed_rectangular_slice_lookup',
             f"forall F G o s l i z. ({_slice('F','G','o','s','l','lookup_slice')}) -> ({_lt('i','l','lookup_bound')}) -> "
             f"({_table_at('G','i','z','lookup_value')}) -> ({_table_at('F',_index('o','s','i'),'z','lookup_source')})",
             ('divisor_signed_table_at_functional',),lookup,
             'Every actual slice lookup is the identical canonical signed value at its explicitly computed source index.'),
        spec('signed_rectangular_slice_restrict',
             f"forall F G o s l. ({_slice('F','G','o','s','S l','restrict_source')}) -> ({_slice('F','G','o','s','l','restrict_result')})",
             ('signed_table_domain_resize','le_succ'),restrict,
             'Restrict only the strict slice window, retaining the same actual output streams and source packing.'),
        spec('signed_rectangular_slice_empty',
             f"forall F G o s. ({_table('0','F','empty_source')}) -> ({_table('0','G','empty_output')}) -> ({_slice('F','G','o','s','0','empty_result')})",
             ('succ_ne_zero','add_eq_zero_right'),empty,
             'A zero-length affine slice still requires real packed source and output tables; its strict entry window is empty.'),
        spec('signed_rectangular_slice_extensional_unique',
             f"forall F G H o s l. ({_slice('F','G','o','s','l','unique_first')}) -> ({_slice('F','H','o','s','l','unique_second')}) -> ({_table_equal('G','H','l','unique_result')})",
             ('divisor_signed_table_at_functional','signed_rectangular_slice_lookup'),unique,
             'Two slices of the same window agree in their represented signed entries, not necessarily their codes or component streams.'),
        spec('signed_rectangular_slice_extend',
             f"forall F G H o s l a. ({_slice('F','G','o','s','l','extend_prefix')}) -> ({_table('l','H','extend_table')}) -> "
             f"({_table_equal('G','H','l','extend_preserved')}) -> ({_table_at('F',_index('o','s','l'),'a','extend_source')}) -> "
             f"({_table_at('H','l','a','extend_value')}) -> ({_slice('F','H','o','s','S l','extend_result')})",
             ('signed_table_domain_resize','finite_lt_succ_eq_or_lt','arithmetic_signed_table_equal_entry_transport','le_refl'),extend,
             'A preserved actual prefix and one real source lookup extend the slice without changing any earlier represented value.'),
        spec('signed_rectangular_slice_exists',
             f"forall l F o s. ({_table('0','F','exists_input')}) -> exists G. ({_slice('F','G','o','s','l','exists_result')})",
             ('signed_rectangular_slice_empty','divisor_signed_table_from_components','signed_table_lookup_any',
              'arithmetic_signed_table_extend_at','signed_rectangular_slice_extend'),exists,
             'Ordinary induction constructs the affine output by actual two-beta extension, including zero length and zero stride.'),
        spec('signed_rectangular_slice_exists_extensionally_unique',
             f"forall F o s l. ({_table('0','F','exists_unique_input')}) -> exists G. "
             +_and(_slice('F','G','o','s','l','exists_unique_result'),f"forall H. ({_slice('F','H','o','s','l','exists_unique_other')}) -> ({_table_equal('G','H','l','exists_unique_equal')})"),
             ('signed_rectangular_slice_exists','signed_rectangular_slice_extensional_unique'),exists_unique,
             'Construct an affine slice and prove extensional uniqueness, with no supplied slice, function, or finite-choice oracle.'),
    )


def _sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    exists=_intro('F','o','s','l','hF')+(f"have hg : exists G. ({_slice('F','G','o','s','l','sum_exists_slice')})",)
    exists+=_call('signed_rectangular_slice_exists','l','F','o','s')+('exact hF','cases hg')
    exists+=(f"have hz : exists z. ({_signed_sum('x','l','z','sum_exists_value')})",)
    exists+=_call('arithmetic_signed_sum_exists','l','x','l')+_parts('hg_witness',3)+('exact hg_witness_right_left','cases hz')
    exists+=('exists x1','exists x','split','exact hg_witness','exact hz_witness')

    functional=_intro('F','o','s','l','a','b','ha','hb')+('cases ha','cases ha_witness','cases hb','cases hb_witness')
    functional+=_call('divisor_signed_sum_extensional','x','x1','l','a','b')
    functional+=_call('signed_rectangular_slice_extensional_unique','F','x','x1','o','s','l')
    functional+=('exact ha_witness_left','exact hb_witness_left','exact ha_witness_right','exact hb_witness_right')

    empty_value=_intro('F','o','s','z','hz')+('cases hz','cases hz_witness')
    empty_value+=_call('divisor_signed_sum_empty_value','x','z')+('exact hz_witness_right',)
    empty_exists=_intro('F','o','s','hF')+(f"have hz : exists z. ({_slice_sum('F','o','s','0','z','sum_empty_construct')})",)
    empty_exists+=_call('signed_rectangular_slice_sum_exists','F','o','s','0')+('exact hF','cases hz','have heq : x = 0')
    empty_exists+=_call('signed_rectangular_slice_sum_empty_value','F','o','s','x')+('exact hz_witness',)
    empty_exists+=_rewrite('heq',_slice_sum('F','o','s','0','x','sum_empty_rewrite'),'x','hz_witness')+('exact hz_witness',)

    decomp=_intro('F','o','s','l','z','hz')+('cases hz','cases hz_witness')
    inner=_and(_signed_sum('x','l','a','sum_decomp_prefix'),_table_at('x','l','b','sum_decomp_entry'),_add_code('a','b','z','sum_decomp_add'))
    decomp+=(f'have hd : exists a b. ({inner})',)+_call('divisor_signed_sum_successor_decompose','x','l','z')+('exact hz_witness_right',)
    decomp+=_cases('hd',2)+_parts('hd_witness_witness',3)+('exists x1','exists x2','split','exists x','split')
    decomp+=_call('signed_rectangular_slice_restrict','F','x','o','s','l')+('exact hz_witness_left','exact hd_witness_witness_left','split')
    decomp+=_call('signed_rectangular_slice_lookup','F','x','o','s','S l','l','x2')+('exact hz_witness_left',)+_call('le_refl','S l')
    decomp+=('exact hd_witness_witness_right_left','exact hd_witness_witness_right_right')

    intro=_intro('F','o','s','l','a','b','c','ha','hb','hadd')+('cases ha','cases ha_witness')
    he=_and(_table('l','H','sum_intro_table'),_table_equal('x','H','l','sum_intro_equal'),_table_at('H','l','b','sum_intro_last'))
    intro+=(f'have he : exists H. ({he})',)+_call('arithmetic_signed_table_extend_at','l','x','l','b')
    intro+=_parts('ha_witness_left',3)+('exact ha_witness_left_right_left','cases he')+_parts('he_witness',3)
    intro+=('exists x1','split')+_call('signed_rectangular_slice_extend','F','x','x1','o','s','l','b')
    intro+=('exact ha_witness_left','exact he_witness_left','exact he_witness_right_left','exact hb','exact he_witness_right_right')
    intro+=_call('arithmetic_signed_sum_append_transport','x','x1','l','a','b','c')
    intro+=('exact he_witness_left','exact he_witness_right_left','exact ha_witness_right','exact he_witness_right_right','exact hadd')

    add=_intro('F','o','s','l','a','b','c','ha','hb','hc')
    add+=(f"have hd : exists d. ({_add_code('a','b','d','sum_add_construct')})",)+_call('signed_add_total','a','b')+('cases hd','have heq : x = c')
    add+=_call('signed_rectangular_slice_sum_functional','F','o','s','S l','x','c')
    add+=_call('signed_rectangular_slice_sum_successor_intro','F','o','s','l','a','b','x')+('exact ha','exact hb','exact hd_witness','exact hc')
    add+=_rewrite('heq',_add_code('a','b','x','sum_add_rewrite'),'x','hd_witness')+('exact hd_witness',)

    unique=_intro('F','o','s','l','hF')+(f"have hz : exists z. ({_slice_sum('F','o','s','l','z','sum_unique_construct')})",)
    unique+=_call('signed_rectangular_slice_sum_exists','F','o','s','l')+('exact hF','cases hz','exists x','split','exact hz_witness')
    unique+=_intro('w','hw')+_call('signed_rectangular_slice_sum_functional','F','o','s','l','w','x')+('exact hw','exact hz_witness')
    return (
        spec('signed_rectangular_slice_sum_exists',
             f"forall F o s l. ({_table('0','F','sum_exists_input')}) -> exists z. ({_slice_sum('F','o','s','l','z','sum_exists_result')})",
             ('signed_rectangular_slice_exists','arithmetic_signed_sum_exists'),exists,
             'Construct an actual affine slice and actual positive/negative prefix-sum traces; the result is not a supplied sum oracle.'),
        spec('signed_rectangular_slice_sum_functional',
             f"forall F o s l a b. ({_slice_sum('F','o','s','l','a','sum_functional_first')}) -> ({_slice_sum('F','o','s','l','b','sum_functional_second')}) -> a=b",
             ('divisor_signed_sum_extensional','signed_rectangular_slice_extensional_unique'),functional,
             'The canonical signed affine-sum value is independent of every permissible slice encoding.'),
        spec('signed_rectangular_slice_sum_empty_value',
             f"forall F o s z. ({_slice_sum('F','o','s','0','z','sum_empty_input')}) -> z=0",
             ('divisor_signed_sum_empty_value',),empty_value,
             'Every actual empty affine sum is the canonical signed zero, irrespective of offset or stride.'),
        spec('signed_rectangular_slice_sum_empty_exists',
             f"forall F o s. ({_table('0','F','sum_empty_input')}) -> ({_slice_sum('F','o','s','0','0','sum_empty_result')})",
             ('signed_rectangular_slice_sum_exists','signed_rectangular_slice_sum_empty_value'),empty_exists,
             'A valid source actually admits an empty slice and its zero sum, rather than merely a vacuous uniqueness assertion.'),
        spec('signed_rectangular_slice_sum_successor_decompose',
             f"forall F o s l z. ({_slice_sum('F','o','s','S l','z','sum_decomp_input')}) -> exists a b. "
             +_and(_slice_sum('F','o','s','l','a','sum_decomp_output'),_table_at('F',_index('o','s','l'),'b','sum_decomp_last'),_add_code('a','b','z','sum_decomp_result')),
             ('divisor_signed_sum_successor_decompose','signed_rectangular_slice_restrict','signed_rectangular_slice_lookup','le_refl'),decomp,
             'A successor affine sum decomposes into its actual prefix sum and actual last source entry with the original SignedAdd relation.'),
        spec('signed_rectangular_slice_sum_successor_intro',
             f"forall F o s l a b c. ({_slice_sum('F','o','s','l','a','sum_intro_prefix')}) -> "
             f"({_table_at('F',_index('o','s','l'),'b','sum_intro_source')}) -> ({_add_code('a','b','c','sum_intro_add')}) -> "
             f"({_slice_sum('F','o','s','S l','c','sum_intro_result')})",
             ('arithmetic_signed_table_extend_at','signed_rectangular_slice_extend','arithmetic_signed_sum_append_transport'),intro,
             'Extend both beta streams by the actual next source value and append the actual signed sum; no output slice is assumed.'),
        spec('signed_rectangular_slice_sum_successor_add',
             f"forall F o s l a b c. ({_slice_sum('F','o','s','l','a','sum_add_prefix')}) -> "
             f"({_table_at('F',_index('o','s','l'),'b','sum_add_source')}) -> ({_slice_sum('F','o','s','S l','c','sum_add_next')}) -> "
             f"({_add_code('a','b','c','sum_add_result')})",
             ('signed_add_total','signed_rectangular_slice_sum_functional','signed_rectangular_slice_sum_successor_intro'),add,
             'Any two actual consecutive affine sums and their true intervening source value satisfy the signed addition law.'),
        spec('signed_rectangular_slice_sum_exists_unique',
             f"forall F o s l. ({_table('0','F','sum_unique_input')}) -> exists z. "
             +_and(_slice_sum('F','o','s','l','z','sum_unique_result'),f"forall w. ({_slice_sum('F','o','s','l','w','sum_unique_other')}) -> w=z"),
             ('signed_rectangular_slice_sum_exists','signed_rectangular_slice_sum_functional'),unique,
             'Every finite affine window of a genuine source table has a constructed and literally unique canonical signed sum.'),
    )


def make_signed_rectangular_slice_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _slice_rows(spec)+_sum_rows(spec)


__all__=['signed_rectangular_slice_relation','signed_rectangular_slice_sum_relation',
         'make_signed_rectangular_slice_candidate_theorems']
