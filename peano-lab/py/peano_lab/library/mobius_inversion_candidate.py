"""Finite signed Möbius inversion over genuinely constructed arithmetic tables.

The transform graph uses the independently defined actual divisor sum at every
positive input in its finite domain.  Möbius values retain their original
prime-factor definition.  Neither inversion nor a rearrangement identity is
assumed in a definition; convolution associativity supplies the finite algebra.
"""

from __future__ import annotations

from typing import Any, Callable

from .dirichlet_convolution_candidate import _convolution, _convolution_table
from .dirichlet_units_candidate import _one, _delta, _delta_value
from .divisor_mask_candidate import _divisor_sum, _positive_equal
from .divisor_sum_table_candidate import _table, _table_at
from .mobius_divisor_cancellation_candidate import _cancellation_iff
from .mobius_table_candidate import _mu_table
from .prime_valuation_support_candidate import _and, _call, _intro, _le, _parts, _public, _rewrite


def _transform(N: str, F: str, G: str, tag: str) -> str:
    n,z='mi_index_'+tag,'mi_value_'+tag
    return (f'forall {n} {z}. ~({n}=0) -> ({_le(n,N,tag+"bound")}) -> '
            f'({_table_at(G,n,z,tag+"entry")}) -> ({_divisor_sum(F,n,z,tag+"sum")})')


def signed_arithmetic_divisor_transform_relation(
    N: str, F: str, G: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Every positive in-domain value of G is the genuine divisor sum of F."""
    return _public(_transform,(N,F,G),tag=tag,variables=variables)


def _one_iff(F: str, U: str, n: str, z: str, tag: str) -> str:
    convolution,divisor=_convolution(F,U,n,z,tag+'convolution'),_divisor_sum(F,n,z,tag+'divisor')
    return _and(f'({convolution}) -> ({divisor})',f'({divisor}) -> ({convolution})')


def _construct_units() -> tuple[str, ...]:
    body=(f"have hU : exists U. ({_one('N','U','inversion_actual_one')}) /\\ ({_table_at('U','0','0','inversion_one_zero')})",)
    body+=_call('dirichlet_constant_one_table_exists','N','0')+('cases hU','cases hU_witness')
    body+=(f"have hE : exists E. ({_delta('N','E','inversion_actual_delta')}) /\\ ({_table_at('E','0','0','inversion_delta_zero')})",)
    body+=_call('dirichlet_kronecker_delta_table_exists','N','0')+('cases hE','cases hE_witness')
    return body


def _transform_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    forward=_intro('N','F','G','U','hF','hG','hU','htransform')+('cases hU','split','exact hF','split','exact hU_left','split','exact hG')
    forward+=_intro('n','z','hn','hbound','hz')+(f"have hi : {_one_iff('F','U','n','z','transform_one_iff')}",)
    forward+=_call('dirichlet_constant_one_sum_iff','N','F','U','n','z')
    forward+=('exact hF','exact hU','exact hn','exact hbound','cases hi','apply hi_right')
    forward+=_call('htransform','n','z')+('exact hn','exact hbound','exact hz')

    reverse=_intro('N','F','G','U','hU','hc')+_parts('hc',4)+_intro('n','z','hn','hbound','hz')
    reverse+=(f"have hi : {_one_iff('F','U','n','z','transform_reverse_iff')}",)
    reverse+=_call('dirichlet_constant_one_sum_iff','N','F','U','n','z')
    reverse+=('exact hc_left','exact hU','exact hn','exact hbound','cases hi','apply hi_left')
    reverse+=_call('hc_right_right_right','n','z')+('exact hn','exact hbound','exact hz')
    return (
        spec('arithmetic_divisor_transform_convolution',
             f"forall N F G U. ({_table('N','F','transform_source')}) -> ({_table('N','G','transform_output')}) -> "
             f"({_one('N','U','transform_one')}) -> ({_transform('N','F','G','transform_values')}) -> "
             f"({_convolution_table('N','F','U','G','transform_result')})",
             ('dirichlet_constant_one_sum_iff',),forward,
             'A genuine divisor transform is the actual convolution with a constructed positive constant-one table, on the whole positive domain.'),
        spec('arithmetic_divisor_convolution_transform',
             f"forall N F G U. ({_one('N','U','transform_reverse_one')}) -> "
             f"({_convolution_table('N','F','U','G','transform_reverse_source')}) -> ({_transform('N','F','G','transform_reverse_result')})",
             ('dirichlet_constant_one_sum_iff',),reverse,
             'Actual convolution with the positive constant-one table supplies the original divisor-transform relation, including all required finite sum witnesses.'),
    )


def _cancellation_row(spec: Callable[..., Any]) -> Any:
    body=_intro('N','M','U','E','hM','hU','hE')+_parts('hM',3)+('cases hU','cases hE',
          'split','exact hM_left','split','exact hU_left','split','exact hE_left')
    body+=_intro('n','z','hn','hbound','hz')+(f"have hi : {_one_iff('M','U','n','z','mu_one_sum_iff')}",)
    body+=_call('dirichlet_constant_one_sum_iff','N','M','U','n','z')
    body+=('exact hM_left','exact hU','exact hn','exact hbound','cases hi','apply hi_right',
           f"have hc : {_cancellation_iff('M','n','z','mu_one_actual_cancellation')}")
    body+=_call('mobius_divisor_sum_cancellation','N','M','n','z')
    body+=('exact hM','exact hn','exact hbound','cases hc','apply hc_right',f"have hv : {_delta_value('n','z')}")
    body+=_call('hE_right','n','z')+('exact hn','exact hbound','exact hz','cases hv','have heq : n=1 \\/ ~(n=1)')
    body+=_call('eq_decidable','n','1')+('cases heq','left','split','exact heq_left','apply hv_left','exact heq_left',
           'right','split','exact heq_right','apply hv_right','exact heq_right')
    return spec('mobius_constant_one_convolution_delta',
                f"forall N M U E. ({_mu_table('N','M','mu_one_mobius')}) -> ({_one('N','U','mu_one_one')}) -> "
                f"({_delta('N','E','mu_one_delta')}) -> ({_convolution_table('N','M','U','E','mu_one_result')})",
                ('dirichlet_constant_one_sum_iff','mobius_divisor_sum_cancellation','eq_decidable'),body,
                'The previously proved prime-toggle cancellation identifies the actual convolution of independently defined Möbius values and constant one with every actual delta table.')


def _inversion_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    value=_intro('N','F','G','M','U','E','n','a','b','hF','hG','hM','hU','hE','ht','hn','hbound','ha','hb')
    value+=(f"have hMU : {_convolution_table('N','M','U','E','value_mu_one')}",)
    value+=_call('mobius_constant_one_convolution_delta','N','M','U','E')+('exact hM','exact hU','exact hE')
    value+=(f"have hUF : {_convolution_table('N','U','F','G','value_transform')}",)
    value+=_call('dirichlet_convolution_table_commutative','N','F','U','G')
    value+=_call('arithmetic_divisor_transform_convolution','N','F','G','U')+('exact hF','exact hG','exact hU','exact ht')
    value+=(f"have hEF : {_convolution_table('N','E','F','F','value_unit')}",)
    value+=_call('dirichlet_delta_left_table','N','F','E')+('exact hF','exact hE')+_parts('hEF',4)
    value+=_call('dirichlet_convolution_associative','N','M','U','F','E','G','n','a','b')
    value+=('exact hMU','exact hUF','exact hn','exact hbound')
    value+=_call('hEF_right_right_right','n','a')+('exact hn','exact hbound','exact ha','exact hb')

    table=_intro('N','F','G','M','hF','hG','hM','ht')+_parts('hM',3)+_construct_units()
    table+=('split','exact hM_left','split','exact hG','split','exact hF')+_intro('n','z','hn','hbound','hz')
    table+=(f"have hs : exists a. ({_convolution('M','G','n','a','inversion_construct_fold')})",)
    table+=_call('dirichlet_convolution_sum_exists','N','M','G','n')+('exact hM_left','exact hG','exact hn','exact hbound','cases hs','have he : z=x2')
    table+=_call('mobius_dirichlet_inversion_value','N','F','G','M','x','x1','n','z','x2')
    table+=('exact hF','exact hG','exact hM','exact hU_witness_left','exact hE_witness_left','exact ht',
            'exact hn','exact hbound','exact hz','exact hs_witness')
    table+=_rewrite('he',_convolution('M','G','n','z','inversion_result_rewrite'),'z')+('exact hs_witness',)

    constructed=_intro('N','F','G','hF','hG','ht')+(f"have hM : exists M. ({_mu_table('N','M','inversion_actual_mobius')})",)
    constructed+=_call('mobius_table_exists','N')+('cases hM','exists x','exists F','split','exact hM_witness','split')
    constructed+=_call('mobius_inversion_for_actual_mobius_table','N','F','G','x')+('exact hF','exact hG','exact hM_witness','exact ht')
    constructed+=_intro('n','a','b','hn','hbound','ha','hb')+_call('divisor_signed_table_at_functional','F','n','a','b')
    constructed+=('exact ha','exact hb')
    return (
        spec('mobius_dirichlet_inversion_value',
             f"forall N F G M U E n a b. ({_table('N','F','value_source')}) -> ({_table('N','G','value_transform_table')}) -> "
             f"({_mu_table('N','M','value_mobius')}) -> ({_one('N','U','value_one')}) -> ({_delta('N','E','value_delta')}) -> "
             f"({_transform('N','F','G','value_all_quotients')}) -> ~(n=0) -> ({_le('n','N','value_bound')}) -> "
             f"({_table_at('F','n','a','value_original')}) -> ({_convolution('M','G','n','b','value_weighted_sum')}) -> a=b",
             ('mobius_constant_one_convolution_delta','dirichlet_convolution_table_commutative',
              'arithmetic_divisor_transform_convolution','dirichlet_delta_left_table','dirichlet_convolution_associative'),value,
             'Actual finite associativity changes Möbius times the divisor transform into delta times the original input; the transform premise covers every required positive quotient.'),
        spec('mobius_inversion_for_actual_mobius_table',
             f"forall N F G M. ({_table('N','F','inversion_source')}) -> ({_table('N','G','inversion_transform_table')}) -> "
             f"({_mu_table('N','M','inversion_mobius')}) -> ({_transform('N','F','G','inversion_all_inputs')}) -> "
             f"({_convolution_table('N','M','G','F','inversion_result')})",
             ('dirichlet_constant_one_table_exists','dirichlet_kronecker_delta_table_exists',
              'dirichlet_convolution_sum_exists','mobius_dirichlet_inversion_value'),table,
             'Construct one and delta tables and every genuine weighted fold before proving that the actual original table is the full positive-window Möbius inverse.'),
        spec('mobius_inversion_arithmetic_tables',
             f"forall N F G. ({_table('N','F','full_source')}) -> ({_table('N','G','full_transform_table')}) -> "
             f"({_transform('N','F','G','full_all_inputs')}) -> exists M H. "+
             _and(_mu_table('N','M','full_mobius_witness'),_convolution_table('N','M','G','H','full_weighted_output'),
                  _positive_equal('H','F','N','full_original_values')),
             ('mobius_table_exists','mobius_inversion_for_actual_mobius_table','divisor_signed_table_at_functional'),constructed,
             'Full finite signed Möbius inversion constructs the independent Möbius table and a real output table whose actual weighted divisor sums recover every positive original value, including the genuine empty-window case N=0.'),
    )


def _reverse_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    reverse=_intro('N','F','G','M','hF','hG','hM','hc')+_construct_units()
    reverse+=(f"have hUM : {_convolution_table('N','x','M','x1','reverse_one_mu')}",)
    reverse+=_call('dirichlet_convolution_table_commutative','N','M','x','x1')
    reverse+=_call('mobius_constant_one_convolution_delta','N','M','x','x1')+('exact hM','exact hU_witness_left','exact hE_witness_left')
    reverse+=(f"have hEG : {_convolution_table('N','x1','G','G','reverse_unit')}",)
    reverse+=_call('dirichlet_delta_left_table','N','G','x1')+('exact hG','exact hE_witness_left')+_parts('hEG',4)
    reverse+=('cases hU_witness_left',)+_intro('n','z','hn','hbound','hz')
    reverse+=(f"have hs : exists a. ({_convolution('F','x','n','a','reverse_actual_fold')})",)
    reverse+=_call('dirichlet_convolution_sum_exists','N','F','x','n')
    reverse+=('exact hF','exact hU_witness_left_left','exact hn','exact hbound','cases hs','have he : x2=z','symm')
    reverse+=_call('dirichlet_convolution_associative','N','x','M','G','x1','F','n','z','x2')
    reverse+=('exact hUM','exact hc','exact hn','exact hbound')
    reverse+=_call('hEG_right_right_right','n','z')+('exact hn','exact hbound','exact hz')
    reverse+=_call('dirichlet_convolution_sum_swap','N','F','x','n','x2')
    reverse+=('exact hF','exact hU_witness_left_left','exact hbound','exact hs_witness')
    reverse+=_rewrite('he',_convolution('F','x','n','x2','reverse_actual_rewrite'),'x2','hs_witness')
    reverse+=(f"have hi : {_one_iff('F','x','n','z','reverse_one_iff')}",)
    reverse+=_call('dirichlet_constant_one_sum_iff','N','F','x','n','z')
    reverse+=('exact hF','exact hU_witness_left','exact hn','exact hbound','cases hi','apply hi_left','exact hs_witness')

    implication=_transform('N','F','G','inversion_iff_transform')
    convolution=_convolution_table('N','M','G','F','inversion_iff_convolution')
    iff=_intro('N','F','G','M','hF','hG','hM')+('split','intro ht')
    iff+=_call('mobius_inversion_for_actual_mobius_table','N','F','G','M')+('exact hF','exact hG','exact hM','exact ht','intro hc')
    iff+=_call('mobius_inversion_reconstructs_divisor_transform','N','F','G','M')+('exact hF','exact hG','exact hM','exact hc')
    return (
        spec('mobius_inversion_reconstructs_divisor_transform',
             f"forall N F G M. ({_table('N','F','reverse_source')}) -> ({_table('N','G','reverse_transform_table')}) -> "
             f"({_mu_table('N','M','reverse_mobius')}) -> ({_convolution_table('N','M','G','F','reverse_inverse')}) -> "
             f"({_transform('N','F','G','reverse_result')})",
             ('dirichlet_constant_one_table_exists','dirichlet_kronecker_delta_table_exists','dirichlet_convolution_table_commutative',
              'mobius_constant_one_convolution_delta','dirichlet_delta_left_table','dirichlet_convolution_sum_exists',
              'dirichlet_convolution_associative','dirichlet_convolution_sum_swap','dirichlet_constant_one_sum_iff'),reverse,
             'The converse constructs actual unit tables and finite folds; associativity turns one times a Möbius convolution back into the original divisor transform.'),
        spec('mobius_inversion_iff',
             f"forall N F G M. ({_table('N','F','iff_source')}) -> ({_table('N','G','iff_transform_table')}) -> "
             f"({_mu_table('N','M','iff_mobius')}) -> "+_and(f'({implication}) -> ({convolution})',f'({convolution}) -> ({implication})'),
             ('mobius_inversion_for_actual_mobius_table','mobius_inversion_reconstructs_divisor_transform'),iff,
             'For actual finite signed tables, being the divisor transform is equivalent to being inverted by the independently defined Möbius convolution; no values at zero are constrained on either input.'),
    )


def make_mobius_inversion_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _transform_rows(spec)+(_cancellation_row(spec),)+_inversion_rows(spec)+_reverse_rows(spec)


__all__=['signed_arithmetic_divisor_transform_relation','make_mobius_inversion_candidate_theorems']
