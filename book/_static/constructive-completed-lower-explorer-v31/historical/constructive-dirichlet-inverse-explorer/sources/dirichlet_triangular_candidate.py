"""Triangular input extension for actual finite signed Dirichlet convolution.

The remainder at n=S k is the real prefix through k, folded at length n.
Appending a new first-input value preserves that restricted prefix, not the
old arbitrary value at n.  The actual endpoint quotient is n=n*1.  Every
relation below is an unchanged earlier arithmetic-table or convolution graph;
no inverse equation, unit criterion or prescribed fold is a definition.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_table_extension_candidate import _extension
from .dirichlet_convolution_candidate import _convolution, _convolution_table, _entry, _prefix
from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at, _table_equal
from .prime_valuation_support_candidate import _and, _call, _cases, _intro, _le, _lt, _parts, _rewrite
from .signed_table_operations_candidate import _mul_code


def _transport_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    entry = _intro('F','G','H','N','l','n','d','z','hH','he','hdN','hdl','hz')
    entry += ('cases hz','cases hz_left')+_cases('hz_left_right',3)
    p='hz_left_right_witness_witness_witness'
    entry += _parts(p,4)
    entry += _call('dirichlet_convolution_entry_from_quotient','H','G','n','d','x','x1','x2','z')
    entry += ('exact hz_left_left','exact '+p+'_left')
    entry += _call('arithmetic_signed_table_equal_entry_transport','N','F','H','l','d','x1')
    entry += ('exact hH','exact he','exact hdN','exact hdl','exact '+p+'_right_left',
              'exact '+p+'_right_right_left','exact '+p+'_right_right_right','right','exact hz_right')

    prefix = _intro('F','G','H','n','k','l','M','hH','he','hkl','hm')
    prefix += ('cases hm','split','exact hm_left')+_intro('d','z','hd','hz')
    prefix += _call('dirichlet_convolution_entry_first_input_transport','F','G','H','k','l','n','d','z')
    prefix += ('exact hH','exact he','exact hd')+_call('lt_of_le_of_lt','d','k','l')
    prefix += ('exact hd','exact hkl')+_call('hm_right','d','z')+('exact hd','exact hz')

    earlier = _intro('F','G','H','l','a','m','z','he','hm','hc')+_parts('he',3)
    earlier += ('cases hc','cases hc_right','cases hc_right_witness','split','exact hc_left','exists x','split')
    earlier += _call('dirichlet_convolution_prefix_first_input_transport','F','G','H','m','m','l','x')
    earlier += _call('signed_table_domain_resize','l','m','H')
    earlier += ('exact he_left','exact he_right_left','exact hm','exact hc_right_witness_left',
                'exact hc_right_witness_right')

    tables = _intro('N','F','G','H','K','a','hc','he')+_parts('hc',4)+('cases he','split')
    tables += _call('signed_table_domain_resize','S N','N','H')
    tables += ('exact he_left','split','exact hc_right_left','split','exact hc_right_right_left')
    tables += _intro('m','z','hm','hb','hz')
    tables += _call('dirichlet_convolution_first_input_append_preserves','F','G','H','S N','a','m','z')
    tables += ('exact he',)+_call('succ_le_succ','m','N')+('exact hb',)
    tables += _call('hc_right_right_right','m','z')+('exact hm','exact hb','exact hz')
    return (
        spec('dirichlet_convolution_entry_first_input_transport',
             f"forall F G H N l n d z. ({_table('N','H','entry_valid')}) -> "
             f"({_table_equal('F','H','l','entry_equal')}) -> ({_le('d','N','entry_domain')}) -> "
             f"({_lt('d','l','entry_preserved')}) -> ({_entry('F','G','n','d','z','entry_source')}) -> "
             f"({_entry('H','G','n','d','z','entry_result')})",
             ('dirichlet_convolution_entry_from_quotient','arithmetic_signed_table_equal_entry_transport'),entry,
             'Transport only the first actual lookup at a preserved index; retain the witnessed quotient, second lookup and signed product, including omitted zero entries.'),
        spec('dirichlet_convolution_prefix_first_input_transport',
             f"forall F G H n k l M. ({_table('k','H','prefix_valid')}) -> "
             f"({_table_equal('F','H','l','prefix_equal')}) -> ({_lt('k','l','prefix_strict')}) -> "
             f"({_prefix('F','G','n','k','M','prefix_source')}) -> ({_prefix('H','G','n','k','M','prefix_result')})",
             ('dirichlet_convolution_entry_first_input_transport','lt_of_le_of_lt'),prefix,
             'The same actual summand table survives a first-input change strictly above its inclusive prefix bound; no equality at the changed endpoint is assumed.'),
        spec('dirichlet_convolution_first_input_append_preserves',
             f"forall F G H l a m z. ({_extension('F','H','l','a','earlier_extension')}) -> "
             f"({_lt('m','l','earlier_strict')}) -> ({_convolution('F','G','m','z','earlier_source')}) -> "
             f"({_convolution('H','G','m','z','earlier_result')})",
             ('dirichlet_convolution_prefix_first_input_transport','signed_table_domain_resize'),earlier,
             'Appending a first-input entry at l preserves every previously constructed convolution at m<l, with its original actual fold witnesses.'),
        spec('dirichlet_convolution_table_first_input_append_preserves',
             f"forall N F G H K a. ({_convolution_table('N','F','G','K','tables_source')}) -> "
             f"({_extension('F','H','S N','a','tables_extension')}) -> "
             f"({_convolution_table('N','H','G','K','tables_result')})",
             ('signed_table_domain_resize','dirichlet_convolution_first_input_append_preserves','succ_le_succ'),tables,
             'The whole earlier positive output table remains valid after appending the first input, including the vacuous N=0 boundary and arbitrary zero entries.'),
    )


def _endpoint_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    product=_mul_code('a','b','z','endpoint_product')
    summand=_entry('F','G','n','n','z','endpoint_summand')
    endpoint = _intro('F','G','n','a','b','z','hn','ha','hb')+('split','intro he')
    endpoint += _call('dirichlet_convolution_entry_quotient_product','F','G','n','n','1','a','b','z')
    endpoint += ('exact hn','symm','apply mul_one','exact ha','exact hb','exact he','intro hp')
    endpoint += _call('dirichlet_convolution_entry_from_quotient','F','G','n','n','1','a','b','z')
    endpoint += ('exact hn','symm','apply mul_one','exact ha','exact hb','exact hp')

    remainder = _intro('N','k','F','G','hF','hG')
    remainder += (f"have hm : exists M. ({_prefix('G','F','S k','k','M','remainder_actual_prefix')})",)
    remainder += _call('dirichlet_convolution_prefix_exists','G','F','S k','k')
    remainder += _call('signed_table_domain_resize','k','0','G')+('exact hG',)
    remainder += _call('signed_table_domain_resize','N','0','F')+('exact hF','cases hm','cases hm_witness',
                  f"have hs : exists r. ({_signed_sum('x','S k','r','remainder_actual_sum')})")
    remainder += _call('arithmetic_signed_sum_exists','k','x','S k')
    remainder += ('exact hm_witness_left','cases hs','exists x','exists x1','split','exact hm_witness','exact hs_witness')
    return (
        spec('dirichlet_convolution_last_entry_iff',
             f"forall F G n a b z. ~(n=0) -> ({_table_at('F','n','a','endpoint_first')}) -> "
             f"({_table_at('G','1','b','endpoint_second')}) -> "
             +_and(f'({summand}) -> ({product})',f'({product}) -> ({summand})'),
             ('dirichlet_convolution_entry_quotient_product','mul_one','dirichlet_convolution_entry_from_quotient'),endpoint,
             'For n>0 the final divisor entry is exactly F(n)*G(1), using the actual quotient witness n=n*1 in both directions.'),
        spec('dirichlet_convolution_strict_prefix_exists',
             f"forall N k F G. ({_table('N','F','remainder_fixed_input')}) -> ({_table('k','G','remainder_partial_input')}) -> "
             f"exists M r. ({_prefix('G','F','S k','k','M','remainder_result_prefix')}) /\\ "
             f"({_signed_sum('M','S k','r','remainder_result_sum')})",
             ('dirichlet_convolution_prefix_exists','signed_table_domain_resize','arithmetic_signed_sum_exists'),remainder,
             'Actually construct the remainder prefix through k and its S k-entry fold even when the first input is only an inclusive k-table; the arbitrary value at S k is excluded.'),
    )


def _step_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    last = _intro('F','G','k','M','r','a','b','y','z','hm','hs','ha','hb','hy','hz')
    last_entry=_entry('F','G','S k','S k','y','step_actual_entry')
    last_product=_mul_code('a','b','y','step_actual_product')
    last += (f"have he : {_and(f'({last_entry}) -> ({last_product})',f'({last_product}) -> ({last_entry})')}",)
    last += _call('dirichlet_convolution_last_entry_iff','F','G','S k','a','b','y')
    last += ('intro hn','apply PA1','exact hn','exact ha','exact hb','cases he')
    extension=_and(_prefix('F','G','S k','S k','K','step_actual_prefix'),_table_equal('M','K','S k','step_actual_equal'))
    last += (f'have hnext : exists K. ({extension})',)
    last += _call('dirichlet_convolution_prefix_append','F','G','S k','k','M','y')
    last += ('exact hm','apply he_right','exact hy','cases hnext','cases hnext_witness','cases hnext_witness_left',
             'split','intro hn','apply PA1','exact hn','exists x','split','exact hnext_witness_left')
    last += _call('arithmetic_signed_sum_append_transport','M','x','S k','r','y','z')
    last += ('exact hnext_witness_left_left','exact hnext_witness_right','exact hs')
    last += _call('dirichlet_convolution_prefix_quotient_entry','F','G','S k','S k','x','S k','1','a','b','y')
    last += ('exact hnext_witness_left',)+_call('le_refl','S k')
    last += ('intro hn','apply PA1','exact hn','symm','apply mul_one','exact ha','exact hb','exact hy','exact hz')

    append = _intro('k','G','F','M','r','H','x','u','y','e','hm','hs','he','hu','hy','ha')+_parts('he',3)
    append += _call('dirichlet_convolution_prefix_last_step','H','F','k','M','r','x','u','y','e')
    append += _call('dirichlet_convolution_prefix_first_input_transport','G','F','H','S k','k','S k','M')
    append += _call('signed_table_domain_resize','S k','k','H')
    append += ('exact he_left','exact he_right_left')+_call('le_refl','S k')
    append += ('exact hm','exact hs','exact he_right_right','exact hu','exact hy','exact ha')
    return (
        spec('dirichlet_convolution_prefix_last_step',
             f"forall F G k M r a b y z. ({_prefix('F','G','S k','k','M','step_previous')}) -> "
             f"({_signed_sum('M','S k','r','step_remainder')}) -> ({_table_at('F','S k','a','step_first')}) -> "
             f"({_table_at('G','1','b','step_second')}) -> ({_mul_code('a','b','y','step_product')}) -> "
             f"({_add_code('r','y','z','step_add')}) -> ({_convolution('F','G','S k','z','step_result')})",
             ('dirichlet_convolution_last_entry_iff','dirichlet_convolution_prefix_append',
              'arithmetic_signed_sum_append_transport','dirichlet_convolution_prefix_quotient_entry','le_refl','mul_one'),last,
             'Append the actual endpoint product to the real strict-prefix fold, constructing the full S(S k)-entry convolution without an assumed recurrence.'),
        spec('dirichlet_convolution_first_input_append_step',
             f"forall k G F M r H x u y e. ({_prefix('G','F','S k','k','M','append_previous')}) -> "
             f"({_signed_sum('M','S k','r','append_remainder')}) -> ({_extension('G','H','S k','x','append_input')}) -> "
             f"({_table_at('F','1','u','append_unit_entry')}) -> ({_mul_code('x','u','y','append_product')}) -> "
             f"({_add_code('r','y','e','append_add')}) -> ({_convolution('H','F','S k','e','append_result')})",
             ('dirichlet_convolution_prefix_last_step','dirichlet_convolution_prefix_first_input_transport',
              'signed_table_domain_resize','le_refl'),append,
             'Change G(S k) only after computing the strict remainder, preserve every earlier summand, and construct the new convolution from the independently proved signed linear equation.'),
    )


def _one_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    zero = _intro('F','G','n','M','hm')+('cases hm',)
    zero += _call('signed_prefix_sum_zero_exists','M','1')+('exact hm_left',)
    zero += _intro('i','z','hlo','hi','hz')+('have hi0 : i=0',)
    zero += _call('le_zero','i')+_call('le_of_succ_le_succ','i','0')+('exact hi',)
    zero += _rewrite('hi0',_table_at('M','i','z','zero_rewrite'),'i','hz')
    zero += _call('dirichlet_convolution_entry_omitted_value','F','G','n','0','z')
    zero += ('left','refl')+_call('hm_right','0','z')+_call('le_refl','0')+('exact hz',)

    actual=_convolution('F','G','1','z','one_convolution')
    product=_mul_code('a','b','z','one_product')
    one = _intro('F','G','a','b','z','ha','hb')+('split','intro hc','cases hc','cases hc_right','cases hc_right_witness',
           f"have hzero : {_signed_sum('x','1','0','one_zero_fold')}")
    one += _call('dirichlet_convolution_zero_prefix_sum','F','G','1','x')
    one += _call('dirichlet_convolution_prefix_restrict','F','G','1','1','0','x')
    one += ('exact hc_right_witness_left',)+_call('zero_le','1')
    decomposition=_and(_signed_sum('x','1','r','one_previous_fold'),_table_at('x','1','v','one_endpoint_lookup'),
                       _add_code('r','v','z','one_fold_add'))
    one += (f'have hd : exists r v. ({decomposition})',)
    one += _call('divisor_signed_sum_successor_decompose','x','1','z')+('exact hc_right_witness_right',)
    one += _cases('hd',2)+_parts('hd_witness_witness',3)+('have hr0 : x1=0',)
    one += _call('divisor_signed_sum_functional','x','1','x1','0')
    one += ('exact hd_witness_witness_left','exact hzero')
    one += _rewrite('hr0',_add_code('x1','x2','z','one_zero_rewrite'),'x1','hd_witness_witness_right_right')
    one += ('have hv : x2=z','symm')+_call('signed_add_functional','0','x2','z','x2')
    one += ('exact hd_witness_witness_right_right',)+_call('signed_add_zero_left','x2')
    endpoint=_entry('F','G','1','1','x2','one_actual_entry')
    endpoint_product=_mul_code('a','b','x2','one_actual_product')
    one += (f"have he : {_and(f'({endpoint}) -> ({endpoint_product})',f'({endpoint_product}) -> ({endpoint})')}",)
    one += _call('dirichlet_convolution_last_entry_iff','F','G','1','a','b','x2')
    one += ('intro hn','apply PA1','exact hn','exact ha','exact hb','cases he',
            f'have hp : {endpoint_product}','apply he_left')
    one += _call('dirichlet_convolution_prefix_lookup','F','G','1','1','x','1','x2')
    one += ('exact hc_right_witness_left',)+_call('le_refl','1')+('exact hd_witness_witness_right_left',)
    one += _rewrite('hv',endpoint_product,'x2','hp')+('exact hp','intro hp',
            f"have hm : exists M. ({_table('0','M','one_base_table')}) /\\ ({_table_at('M','0','0','one_base_entry')})")
    one += _call('arithmetic_signed_table_singleton','0')+('cases hm','cases hm_witness',
            f"have hprefix : {_prefix('F','G','1','0','x','one_base_prefix')}")
    one += _call('dirichlet_convolution_prefix_zero_constructor','F','G','1','x')
    one += ('exact hm_witness_left','exact hm_witness_right')
    one += _call('dirichlet_convolution_prefix_last_step','F','G','0','x','0','a','b','z','z')
    one += ('exact hprefix',)+_call('dirichlet_convolution_zero_prefix_sum','F','G','1','x')
    one += ('exact hprefix','exact ha','exact hb','exact hp')+_call('signed_add_zero_left','z')
    return (
        spec('dirichlet_convolution_zero_prefix_sum',
             f"forall F G n M. ({_prefix('F','G','n','0','M','zero_prefix')}) -> "
             f"({_signed_sum('M','1','0','zero_fold')})",
             ('signed_prefix_sum_zero_exists','le_zero','le_of_succ_le_succ',
              'dirichlet_convolution_entry_omitted_value','le_refl'),zero,
             'The genuine one-entry fold of an inclusive zero summand prefix is canonical zero, without restricting either input value at zero.'),
        spec('dirichlet_convolution_at_one_iff',
             f"forall F G a b z. ({_table_at('F','1','a','one_first')}) -> ({_table_at('G','1','b','one_second')}) -> "
             +_and(f'({actual}) -> ({product})',f'({product}) -> ({actual})'),
             ('dirichlet_convolution_zero_prefix_sum','dirichlet_convolution_prefix_restrict','zero_le',
              'divisor_signed_sum_successor_decompose','divisor_signed_sum_functional','signed_add_functional',
              'signed_add_zero_left','dirichlet_convolution_last_entry_iff','dirichlet_convolution_prefix_lookup',
              'le_refl','arithmetic_signed_table_singleton','dirichlet_convolution_prefix_zero_constructor',
              'dirichlet_convolution_prefix_last_step'),one,
             'Actual convolution at input one is exactly the actual signed product F(1)*G(1); both implications construct or inspect the real two-entry masked fold.'),
    )


def make_dirichlet_triangular_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _transport_rows(spec)+_endpoint_rows(spec)+_step_rows(spec)+_one_rows(spec)


__all__ = ['make_dirichlet_triangular_candidate_theorems']
