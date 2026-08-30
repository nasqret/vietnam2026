"""Constructed row/column sums and finite signed Fubini in ordinary HA.

The affine grid entry (i,j) is the actual signed table lookup at
(o+s*i)+t*j.  Row sums are an explicitly constructed packed table whose
entries are actual affine-slice sums, not prescribed arbitrary function values.
Swapping the two strides and dimensions gives the same sum.  Both dimensions
and both strides may be zero.  The row-major instance is o=0,s=n,t=1.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _pack, _signed_sum, _table, _table_at, _table_equal
from .prime_valuation_support_candidate import _and, _call, _cases, _intro, _lt, _parts, _public, _rewrite
from .signed_rectangular_slice_candidate import _index, _slice, _slice_sum
from .signed_table_operations_candidate import _pointwise_add


def _row_entry(F: str, R: str, o: str, s: str, t: str, n: str, i: str, z: str, tag: str) -> str:
    return _and(_table_at(R,i,z,tag+'entry'),_slice_sum(F,_index(o,s,i),t,n,z,tag+'row_sum'))


def _row_sums(F: str, R: str, o: str, s: str, t: str, m: str, n: str, tag: str) -> str:
    i,z=('srt_'+role+'_'+tag for role in ('index','value'))
    entries=f'forall {i}. ({_lt(i,m,tag+"bound")}) -> exists {z}. ({_row_entry(F,R,o,s,t,n,i,z,tag+"row")})'
    return _and(_table('0',F,tag+'source_table'),_table(m,R,tag+'row_table'),entries)


def _rect_sum(F: str, o: str, s: str, t: str, m: str, n: str, z: str, tag: str) -> str:
    R='srt_rows_'+tag
    return f'exists {R}. '+_and(_row_sums(F,R,o,s,t,m,n,tag+'rows'),_signed_sum(R,m,z,tag+'total'))


def _fubini_data(F: str, R: str, C: str, o: str, s: str, t: str, m: str, n: str, z: str, tag: str) -> str:
    return _and(_row_sums(F,R,o,s,t,m,n,tag+'rows'),_row_sums(F,C,o,t,s,n,m,tag+'columns'),
                _signed_sum(R,m,z,tag+'row_total'),_signed_sum(C,n,z,tag+'column_total'))


def signed_rectangular_row_sums_relation(
    F: str, R: str, o: str, s: str, t: str, m: str, n: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """Actual row-sum table for the grid F[(o+s*i)+t*j], i<m and j<n."""
    return _public(_row_sums,(F,R,o,s,t,m,n),tag=tag,variables=variables)


def signed_rectangular_sum_relation(
    F: str, o: str, s: str, t: str, m: str, n: str, z: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """Actual row-sum table followed by the existing actual signed prefix sum."""
    return _public(_rect_sum,(F,o,s,t,m,n,z),tag=tag,variables=variables)


def _row_table_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    lookup=_intro('F','R','o','s','t','m','n','i','z','hr','hi','hz')+_parts('hr',3)
    lookup+=(f"have he : exists a. ({_row_entry('F','R','o','s','t','n','i','a','lookup_entry')})",)
    lookup+=_call('hr_right_right','i')+('exact hi','cases he','cases he_witness','have heq : x = z')
    lookup+=_call('divisor_signed_table_at_functional','R','i','x','z')+('exact he_witness_left','exact hz')
    lookup+=_rewrite('heq',_slice_sum('F',_index('o','s','i'),'t','n','x','lookup_rewrite'),'x','he_witness_right')+('exact he_witness_right',)

    restrict=_intro('F','R','o','s','t','m','n','hr')+_parts('hr',3)+('split','exact hr_left','split')
    restrict+=_call('signed_table_domain_resize','S m','m','R')+('exact hr_right_left',)+_intro('i','hi')
    restrict+=_call('hr_right_right','i')+_call('le_succ','S i','m')+('exact hi',)

    empty=_intro('F','R','o','s','t','n','hF','hR')+('split','exact hF','split','exact hR')+_intro('i','hi')
    empty+=('cases hi','exfalso')+_call('succ_ne_zero','i')+_call('add_eq_zero_right','x','S i')+('exact hi_witness',)

    unique=_intro('F','R','Q','o','s','t','m','n','hR','hQ','i','a','b','hi','ha','hb')
    unique+=_call('signed_rectangular_slice_sum_functional','F',_index('o','s','i'),'t','n','a','b')
    unique+=_call('signed_rectangular_row_sums_lookup','F','R','o','s','t','m','n','i','a')+('exact hR','exact hi','exact ha')
    unique+=_call('signed_rectangular_row_sums_lookup','F','Q','o','s','t','m','n','i','b')+('exact hQ','exact hi','exact hb')

    new_entry='exists z. ('+_row_entry('F','Q','o','s','t','n','i','z','extend_target')+')'
    extend=_intro('F','R','Q','o','s','t','m','n','a','hr','hQ','hequal','hentry','hsum')+_parts('hr',3)
    extend+=('split','exact hr_left','split')+_call('signed_table_domain_resize','m','S m','Q')+('exact hQ',)
    extend+=_intro('i','hi')+(f"have hcase : i=m \\/ ({_lt('i','m','extend_cases')})",)
    extend+=_call('finite_lt_succ_eq_or_lt','m','i')+('exact hi','cases hcase')
    extend+=_rewrite('hcase_left',new_entry,'i')+('exists a','split','exact hentry','exact hsum')
    extend+=(f"have hold : exists z. ({_row_entry('F','R','o','s','t','n','i','z','extend_old')})",)
    extend+=_call('hr_right_right','i')+('exact hcase_right','cases hold','cases hold_witness','exists x','split')
    extend+=_call('arithmetic_signed_table_equal_entry_transport','i','R','Q','m','i','x')
    extend+=_call('signed_table_domain_resize','m','i','Q')+('exact hQ','exact hequal')+_call('le_refl','i')
    extend+=('exact hcase_right','exact hold_witness_left','exact hold_witness_right')

    zero=_pack('0','0','0','0')
    exists=('induction m',)+_intro('F','o','s','t','n','hF')+(f'exists {zero}',)
    exists+=_call('signed_rectangular_row_sums_empty','F',zero,'o','s','t','n')+('exact hF',)
    exists+=_call('divisor_signed_table_from_components','0',zero,'0','0','0','0')+('refl',)
    exists+=_intro('F','o','s','t','n','hF')+(f"have hp : exists R. ({_row_sums('F','R','o','s','t','m','n','exists_prefix')})",)
    exists+=_call('IH','F','o','s','t','n')+('exact hF','cases hp')
    exists+=(f"have hv : exists z. ({_slice_sum('F',_index('o','s','m'),'t','n','z','exists_row')})",)
    exists+=_call('signed_rectangular_slice_sum_exists','F',_index('o','s','m'),'t','n')+('exact hF','cases hv')
    exists+=(f"have he : exists Q. {_and(_table('m','Q','exists_table'),_table_equal('x','Q','m','exists_equal'),_table_at('Q','m','x1','exists_entry'))}",)
    exists+=_call('arithmetic_signed_table_extend_at','m','x','m','x1')+_parts('hp_witness',3)+('exact hp_witness_right_left','cases he')
    exists+=_parts('he_witness',3)+('exists x2',)+_call('signed_rectangular_row_sums_extend','F','x','x2','o','s','t','m','n','x1')
    exists+=('exact hp_witness','exact he_witness_left','exact he_witness_right_left','exact he_witness_right_right','exact hv_witness')

    exists_unique=_intro('F','o','s','t','m','n','hF')+(f"have hr : exists R. ({_row_sums('F','R','o','s','t','m','n','unique_construct')})",)
    exists_unique+=_call('signed_rectangular_row_sums_exists','m','F','o','s','t','n')+('exact hF','cases hr','exists x','split','exact hr_witness')
    exists_unique+=_intro('Q','hQ')+_call('signed_rectangular_row_sums_extensional_unique','F','x','Q','o','s','t','m','n')+('exact hr_witness','exact hQ')
    return (
        spec('signed_rectangular_row_sums_lookup',
             f"forall F R o s t m n i z. ({_row_sums('F','R','o','s','t','m','n','lookup_rows')}) -> ({_lt('i','m','lookup_bound')}) -> "
             f"({_table_at('R','i','z','lookup_value')}) -> ({_slice_sum('F',_index('o','s','i'),'t','n','z','lookup_sum')})",
             ('divisor_signed_table_at_functional',),lookup,
             'Each actual row-table entry is the actual signed sum of the corresponding affine source slice.'),
        spec('signed_rectangular_row_sums_restrict_outer',
             f"forall F R o s t m n. ({_row_sums('F','R','o','s','t','S m','n','restrict_source')}) -> ({_row_sums('F','R','o','s','t','m','n','restrict_result')})",
             ('signed_table_domain_resize','le_succ'),restrict,
             'Removing the last row preserves every actual earlier row sum and the same output encoding.'),
        spec('signed_rectangular_row_sums_empty',
             f"forall F R o s t n. ({_table('0','F','empty_source')}) -> ({_table('0','R','empty_table')}) -> ({_row_sums('F','R','o','s','t','0','n','empty_result')})",
             ('succ_ne_zero','add_eq_zero_right'),empty,
             'Zero rows impose no fictitious row values but still certify genuine source and row-table packings.'),
        spec('signed_rectangular_row_sums_extensional_unique',
             f"forall F R Q o s t m n. ({_row_sums('F','R','o','s','t','m','n','unique_first')}) -> ({_row_sums('F','Q','o','s','t','m','n','unique_second')}) -> ({_table_equal('R','Q','m','unique_equal')})",
             ('signed_rectangular_slice_sum_functional','signed_rectangular_row_sums_lookup'),unique,
             'All genuine row-sum tables agree entrywise in canonical signed values, without identifying arbitrary beta encodings.'),
        spec('signed_rectangular_row_sums_extend',
             f"forall F R Q o s t m n a. ({_row_sums('F','R','o','s','t','m','n','extend_prefix')}) -> ({_table('m','Q','extend_table')}) -> "
             f"({_table_equal('R','Q','m','extend_equal')}) -> ({_table_at('Q','m','a','extend_entry')}) -> "
             f"({_slice_sum('F',_index('o','s','m'),'t','n','a','extend_sum')}) -> ({_row_sums('F','Q','o','s','t','S m','n','extend_result')})",
             ('signed_table_domain_resize','finite_lt_succ_eq_or_lt','arithmetic_signed_table_equal_entry_transport','le_refl'),extend,
             'A preserved row-table prefix extends by one actually proved slice sum, never by an assumed finite-choice table.'),
        spec('signed_rectangular_row_sums_exists',
             f"forall m F o s t n. ({_table('0','F','exists_source')}) -> exists R. ({_row_sums('F','R','o','s','t','m','n','exists_result')})",
             ('signed_rectangular_row_sums_empty','divisor_signed_table_from_components','signed_rectangular_slice_sum_exists',
              'arithmetic_signed_table_extend_at','signed_rectangular_row_sums_extend'),exists,
             'Ordinary induction computes each finite slice sum and appends its actual signed value to construct the entire row-sum table.'),
        spec('signed_rectangular_row_sums_exists_extensionally_unique',
             f"forall F o s t m n. ({_table('0','F','unique_source')}) -> exists R. "
             +_and(_row_sums('F','R','o','s','t','m','n','unique_result'),f"forall Q. ({_row_sums('F','Q','o','s','t','m','n','unique_other')}) -> ({_table_equal('R','Q','m','unique_equal')})"),
             ('signed_rectangular_row_sums_exists','signed_rectangular_row_sums_extensional_unique'),exists_unique,
             'Construct a genuine row-sum table and prove its precise extensional uniqueness at every i<m.'),
    )


def _rectangular_sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    exists=_intro('F','o','s','t','m','n','hF')+(f"have hr : exists R. ({_row_sums('F','R','o','s','t','m','n','sum_exists_rows')})",)
    exists+=_call('signed_rectangular_row_sums_exists','m','F','o','s','t','n')+('exact hF','cases hr')
    exists+=(f"have hz : exists z. ({_signed_sum('x','m','z','sum_exists_value')})",)
    exists+=_call('arithmetic_signed_sum_exists','m','x','m')+_parts('hr_witness',3)+('exact hr_witness_right_left','cases hz')
    exists+=('exists x1','exists x','split','exact hr_witness','exact hz_witness')

    functional=_intro('F','o','s','t','m','n','a','b','ha','hb')+('cases ha','cases ha_witness','cases hb','cases hb_witness')
    functional+=_call('divisor_signed_sum_extensional','x','x1','m','a','b')
    functional+=_call('signed_rectangular_row_sums_extensional_unique','F','x','x1','o','s','t','m','n')
    functional+=('exact ha_witness_left','exact hb_witness_left','exact ha_witness_right','exact hb_witness_right')

    unique=_intro('F','o','s','t','m','n','hF')+(f"have hz : exists z. ({_rect_sum('F','o','s','t','m','n','z','sum_unique_construct')})",)
    unique+=_call('signed_rectangular_sum_exists','F','o','s','t','m','n')+('exact hF','cases hz','exists x','split','exact hz_witness')
    unique+=_intro('w','hw')+_call('signed_rectangular_sum_functional','F','o','s','t','m','n','w','x')+('exact hw','exact hz_witness')

    outer_zero=_intro('F','o','s','t','n','z','hz')+('cases hz','cases hz_witness')
    outer_zero+=_call('divisor_signed_sum_empty_value','x','z')+('exact hz_witness_right',)

    inner_zero=('induction m',)+_intro('F','R','o','s','t','z','hr','hz')
    inner_zero+=_call('divisor_signed_sum_empty_value','R','z')+('exact hz',)
    inner_zero+=_intro('F','R','o','s','t','z','hr','hz')
    dec=_and(_signed_sum('R','m','a','zero_prefix'),_table_at('R','m','b','zero_entry'),_add_code('a','b','z','zero_add'))
    inner_zero+=(f'have hd : exists a b. ({dec})',)+_call('divisor_signed_sum_successor_decompose','R','m','z')+('exact hz',)
    inner_zero+=_cases('hd',2)+_parts('hd_witness_witness',3)+('have ha : x=0',)
    inner_zero+=_call('IH','F','R','o','s','t','x')+_call('signed_rectangular_row_sums_restrict_outer','F','R','o','s','t','m','0')
    inner_zero+=('exact hr','exact hd_witness_witness_left','have hb : x1=0')
    inner_zero+=_call('signed_rectangular_slice_sum_empty_value','F',_index('o','s','m'),'t','x1')
    inner_zero+=_call('signed_rectangular_row_sums_lookup','F','R','o','s','t','S m','0','m','x1')+('exact hr',)+_call('le_refl','S m')
    inner_zero+=('exact hd_witness_witness_right_left',)
    inner_zero+=_rewrite('ha',_add_code('x','x1','z','zero_rewrite_prefix'),'x','hd_witness_witness_right_right')
    inner_zero+=_rewrite('hb',_add_code('0','x1','z','zero_rewrite_entry'),'x1','hd_witness_witness_right_right')
    inner_zero+=_call('signed_add_functional','0','0','z','0')+('exact hd_witness_witness_right_right',)+_call('signed_add_zero_left','0')

    zero_rect=_intro('F','o','s','t','m','z','hz')+('cases hz','cases hz_witness')
    zero_rect+=_call('signed_rectangular_row_sums_zero_inner','m','F','x','o','s','t','z')+('exact hz_witness_left','exact hz_witness_right')
    return (
        spec('signed_rectangular_sum_exists',
             f"forall F o s t m n. ({_table('0','F','sum_exists_source')}) -> exists z. ({_rect_sum('F','o','s','t','m','n','z','sum_exists_result')})",
             ('signed_rectangular_row_sums_exists','arithmetic_signed_sum_exists'),exists,
             'Construct the whole row-sum table and then its actual finite sum; both finite dimensions are arbitrary.'),
        spec('signed_rectangular_sum_functional',
             f"forall F o s t m n a b. ({_rect_sum('F','o','s','t','m','n','a','sum_functional_first')}) -> ({_rect_sum('F','o','s','t','m','n','b','sum_functional_second')}) -> a=b",
             ('divisor_signed_sum_extensional','signed_rectangular_row_sums_extensional_unique'),functional,
             'All actual representations of the same rectangular sum have the identical canonical signed result.'),
        spec('signed_rectangular_sum_exists_unique',
             f"forall F o s t m n. ({_table('0','F','sum_unique_source')}) -> exists z. "
             +_and(_rect_sum('F','o','s','t','m','n','z','sum_unique_result'),f"forall w. ({_rect_sum('F','o','s','t','m','n','w','sum_unique_other')}) -> w=z"),
             ('signed_rectangular_sum_exists','signed_rectangular_sum_functional'),unique,
             'Every genuine source and every finite affine rectangle admit a constructed, unique signed double-sum value.'),
        spec('signed_rectangular_sum_zero_outer',
             f"forall F o s t n z. ({_rect_sum('F','o','s','t','0','n','z','zero_outer_input')}) -> z=0",
             ('divisor_signed_sum_empty_value',),outer_zero,
             'A rectangle with zero rows has actual signed total zero, including when its column count is nonzero.'),
        spec('signed_rectangular_row_sums_zero_inner',
             f"forall m F R o s t z. ({_row_sums('F','R','o','s','t','m','0','zero_inner_rows')}) -> ({_signed_sum('R','m','z','zero_inner_sum')}) -> z=0",
             ('divisor_signed_sum_empty_value','divisor_signed_sum_successor_decompose','signed_rectangular_row_sums_restrict_outer',
              'signed_rectangular_slice_sum_empty_value','signed_rectangular_row_sums_lookup','le_refl','signed_add_functional','signed_add_zero_left'),inner_zero,
             'Induction proves the sum of any actual table of empty row sums is zero; a positive number of zero-length rows is not silently discarded.'),
        spec('signed_rectangular_sum_zero_inner',
             f"forall F o s t m z. ({_rect_sum('F','o','s','t','m','0','z','zero_inner_input')}) -> z=0",
             ('signed_rectangular_row_sums_zero_inner',),zero_rect,
             'A rectangle with zero columns has actual signed total zero for every row count.'),
    )


def _fubini_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    step=_intro('F','C','V','D','o','s','t','m','n','hC','hV','hD')
    step+=_parts('hC',3)+_parts('hV',3)+_parts('hD',3)
    step+=('split','exact hC_right_left','split','exact hV_right_left','split','exact hD_right_left')+_intro('j','hj')
    for letter in ('C','V','D'):
        step+=(f"have he{letter} : exists z. ({_table_at(letter,'j','z','step_entry_'+letter)})",)
        step+=_call('signed_table_lookup_any','n',letter,'j')+(f'exact h{letter}_right_left',f'cases he{letter}')
    step+=('exists x','exists x1','exists x2','split','exact heC_witness','split','exact heV_witness','split','exact heD_witness')
    left=_index(_index('o','s','m'),'t','j')
    right=_index(_index('o','t','j'),'s','m')
    step+=(f'have hindex : {left} = {right}',)+_call('four_square_euler_add_swap_last','o','s*m','t*j')
    step+=(f"have hentry : {_table_at('F',left,'x1','step_source')}",)
    step+=_call('signed_rectangular_slice_lookup','F','V',_index('o','s','m'),'t','n','j','x1')+('exact hV','exact hj','exact heV_witness')
    step+=_rewrite('hindex',_table_at('F','coord','x1','step_index_rewrite'),'coord','hentry')
    step+=_call('signed_rectangular_slice_sum_successor_add','F',_index('o','t','j'),'s','m','x','x1','x2')
    step+=_call('signed_rectangular_row_sums_lookup','F','C','o','t','s','n','m','j','x')+('exact hC','exact hj','exact heC_witness','exact hentry')
    step+=_call('signed_rectangular_row_sums_lookup','F','D','o','t','s','n','S m','j','x2')+('exact hD','exact hj','exact heD_witness')

    fubini=('induction m',)+_intro('F','o','s','t','n','a','b','ha','hb')+('trans 0',)
    fubini+=_call('signed_rectangular_sum_zero_outer','F','o','s','t','n','a')+('exact ha','symm')
    fubini+=_call('signed_rectangular_sum_zero_inner','F','o','t','s','n','b')+('exact hb',)
    fubini+=_intro('F','o','s','t','n','a','b','ha','hb')+('cases ha','cases ha_witness','cases hb','cases hb_witness')
    dec=_and(_signed_sum('x','m','u','fubini_prefix'),_table_at('x','m','v','fubini_last'),_add_code('u','v','a','fubini_add'))
    fubini+=(f'have hd : exists u v. ({dec})',)+_call('divisor_signed_sum_successor_decompose','x','m','a')+('exact ha_witness_right',)
    fubini+=_cases('hd',2)+_parts('hd_witness_witness',3)
    fubini+=(f"have hC : exists C. ({_row_sums('F','C','o','t','s','n','m','fubini_columns')})",)
    fubini+=_call('signed_rectangular_row_sums_exists','n','F','o','t','s','m')+_parts('ha_witness_left',3)+('exact ha_witness_left_left','cases hC')
    fubini+=(f"have hsumC : exists z. ({_signed_sum('x4','n','z','fubini_column_sum')})",)
    fubini+=_call('arithmetic_signed_sum_exists','n','x4','n')+_parts('hC_witness',3)+('exact hC_witness_right_left','cases hsumC')
    fubini+=('have heq : x2 = x5',)+_call('IH','F','o','s','t','n','x2','x5')
    fubini+=('exists x','split')+_call('signed_rectangular_row_sums_restrict_outer','F','x','o','s','t','m','n')
    fubini+=('exact ha_witness_left','exact hd_witness_witness_left','exists x4','split','exact hC_witness','exact hsumC_witness')
    fubini+=(f"have hlast : {_slice_sum('F',_index('o','s','m'),'t','n','x3','fubini_last_sum')}",)
    fubini+=_call('signed_rectangular_row_sums_lookup','F','x','o','s','t','S m','n','m','x3')+('exact ha_witness_left',)+_call('le_refl','S m')
    fubini+=('exact hd_witness_witness_right_left','cases hlast','cases hlast_witness')
    fubini+=(f"have hpoint : {_pointwise_add('x4','x6','x1','n','fubini_pointwise')}",)
    fubini+=_call('signed_rectangular_columns_successor_add','F','x4','x6','x1','o','s','t','m','n')
    fubini+=('exact hC_witness','exact hlast_witness_left','exact hb_witness_left')
    fubini+=(f"have hadd : {_add_code('x5','x3','b','fubini_column_add')}",)
    fubini+=_call('signed_prefix_sum_pointwise_add','n','x4','x6','x1','x5','x3','b')
    fubini+=('exact hpoint','exact hsumC_witness','exact hlast_witness_right','exact hb_witness_right')
    fubini+=_rewrite('heq',_add_code('x2','x3','a','fubini_rewrite'),'x2','hd_witness_witness_right_right')
    fubini+=_call('signed_add_functional','x5','x3','a','b')+('exact hd_witness_witness_right_right','exact hadd')

    exists=_intro('F','o','s','t','m','n','hF')
    exists+=(f"have hR : exists R. ({_row_sums('F','R','o','s','t','m','n','fubini_exists_rows')})",)
    exists+=_call('signed_rectangular_row_sums_exists','m','F','o','s','t','n')+('exact hF','cases hR')
    exists+=(f"have hz : exists z. ({_signed_sum('x','m','z','fubini_exists_row_sum')})",)
    exists+=_call('arithmetic_signed_sum_exists','m','x','m')+_parts('hR_witness',3)+('exact hR_witness_right_left','cases hz')
    exists+=(f"have hC : exists C. ({_row_sums('F','C','o','t','s','n','m','fubini_exists_columns')})",)
    exists+=_call('signed_rectangular_row_sums_exists','n','F','o','t','s','m')+('exact hF','cases hC')
    exists+=(f"have hw : exists w. ({_signed_sum('x2','n','w','fubini_exists_column_sum')})",)
    exists+=_call('arithmetic_signed_sum_exists','n','x2','n')+_parts('hC_witness',3)+('exact hC_witness_right_left','cases hw','have heq : x3 = x1','symm')
    exists+=_call('signed_rectangular_fubini','m','F','o','s','t','n','x1','x3')
    exists+=('exists x','split','exact hR_witness','exact hz_witness','exists x2','split','exact hC_witness','exact hw_witness')
    exists+=_rewrite('heq',_signed_sum('x2','n','x3','fubini_exists_rewrite'),'x3','hw_witness')
    exists+=('exists x','exists x2','exists x1','split','exact hR_witness','split','exact hC_witness','split','exact hz_witness','exact hw_witness')

    row_major=_intro('F','m','n','hF')+_call('signed_rectangular_fubini_exists','F','0','n','1','m','n')
    row_major+=_call('signed_table_domain_resize','m*n','0','F')+('exact hF',)
    return (
        spec('signed_rectangular_columns_successor_add',
             f"forall F C V D o s t m n. ({_row_sums('F','C','o','t','s','n','m','column_step_before')}) -> "
             f"({_slice('F','V',_index('o','s','m'),'t','n','column_step_row')}) -> "
             f"({_row_sums('F','D','o','t','s','n','S m','column_step_after')}) -> ({_pointwise_add('C','V','D','n','column_step_add')})",
             ('signed_table_lookup_any','four_square_euler_add_swap_last','signed_rectangular_slice_lookup',
              'signed_rectangular_slice_sum_successor_add','signed_rectangular_row_sums_lookup'),step,
             'Appending one real grid row adds its actual entries pointwise to the actual column-sum table, using only the elementary equality of the two coordinate expressions.'),
        spec('signed_rectangular_fubini',
             f"forall m F o s t n a b. ({_rect_sum('F','o','s','t','m','n','a','fubini_rows')}) -> "
             f"({_rect_sum('F','o','t','s','n','m','b','fubini_columns')}) -> a=b",
             ('signed_rectangular_sum_zero_outer','signed_rectangular_sum_zero_inner','divisor_signed_sum_successor_decompose',
              'signed_rectangular_row_sums_exists','arithmetic_signed_sum_exists','signed_rectangular_row_sums_restrict_outer',
              'signed_rectangular_row_sums_lookup','le_refl','signed_rectangular_columns_successor_add',
              'signed_prefix_sum_pointwise_add','signed_add_functional'),fubini,
             'Ordinary row-count induction proves finite signed Fubini for arbitrary affine grids, including both zero dimensions, by constructing the missing prefix column table and applying actual signed sum linearity.'),
        spec('signed_rectangular_fubini_exists',
             f"forall F o s t m n. ({_table('0','F','fubini_exists_source')}) -> exists R C z. ({_fubini_data('F','R','C','o','s','t','m','n','z','fubini_exists_result')})",
             ('signed_rectangular_row_sums_exists','arithmetic_signed_sum_exists','signed_rectangular_fubini'),exists,
             'Construct actual row and column sum tables and actual signed sum traces sharing one canonical value; no supplied slice, table, sum, or permutation witness is required.'),
        spec('signed_rectangular_row_major_fubini',
             f"forall F m n. ({_table('m*n','F','row_major_source')}) -> exists R C z. ({_fubini_data('F','R','C','0','n','1','m','n','z','row_major_result')})",
             ('signed_rectangular_fubini_exists','signed_table_domain_resize'),row_major,
             'Every actual row-major m-by-n signed beta table has constructed row and column sums with exactly the same total, including zero rows or columns.'),
    )


def make_signed_rectangular_sums_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _row_table_rows(spec)+_rectangular_sum_rows(spec)+_fubini_rows(spec)


__all__=['signed_rectangular_row_sums_relation','signed_rectangular_sum_relation',
         'make_signed_rectangular_sums_candidate_theorems']
