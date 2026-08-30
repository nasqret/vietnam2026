"""Finite, normalized signed multiplicativity over actual arithmetic tables.

The nonempty prefix graph contains the coprime product law only for positive
inputs whose product lies in the represented prefix. Canonical positive one
is code 2; the signed-unit disjunction is deliberately not this normalization.
These authoring factories alone do not grant checked-use or admission.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_mask_candidate import _positive_equal
from .divisor_sum_table_candidate import _table, _table_at
from .fermat_residue_product_candidate import coprime
from .prime_valuation_support_candidate import (
    _and, _call, _intro, _le, _parts, _public, _rewrite,
)
from .signed_table_operations_candidate import _mul_code


def _multiplicative(N: str, F: str, tag: str) -> str:
    a, b, x, y, z = ('mp_' + role + '_' + tag for role in ('a', 'b', 'x', 'y', 'z'))
    law = (f'forall {a} {b} {x} {y} {z}. ~({a}=0) -> ~({b}=0) -> '
           f'({_le(a+"*"+b,N,tag+"bound")}) -> ({coprime(a,b,tag=tag+"coprime")}) -> '
           f'({_table_at(F,a,x,tag+"first")}) -> ({_table_at(F,b,y,tag+"second")}) -> '
           f'({_table_at(F,a+"*"+b,z,tag+"product")}) -> ({_mul_code(x,y,z,tag+"law")})')
    return _and(f'~(({N})=0)', _table(N,F,tag+'table'), _table_at(F,'1','2',tag+'one'), law)


def signed_multiplicative_prefix_relation(
    N: str, F: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual nonempty signed prefix, F(1)=+1, and its bounded coprime law."""
    return _public(_multiplicative, (N,F), tag=tag, variables=variables)


def _law(N: str, F: str, tag: str) -> str:
    return (f'forall a b x y z. ~(a=0) -> ~(b=0) -> ({_le("a*b",N,tag+"bound")}) -> '
            f'({coprime("a","b",tag=tag+"coprime")}) -> '
            f'({_table_at(F,"a","x",tag+"first")}) -> ({_table_at(F,"b","y",tag+"second")}) -> '
            f'({_table_at(F,"a*b","z",tag+"product")}) -> ({_mul_code("x","y","z",tag+"law")})')


def _projection_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    result = []
    for name, target, index, summary in (
        ('signed_multiplicative_nonempty', '~(N=0)', 0,
         'The finite multiplicativity relation excludes an empty positive domain.'),
        ('signed_multiplicative_table', _table('N','F','project_table'), 1,
         'Finite multiplicativity includes a genuine arithmetic table, not vacuous missing lookups.'),
        ('signed_multiplicative_normalized', _table_at('F','1','2','project_one'), 2,
         'The actual value at one is canonical signed positive one, not an arbitrary signed unit.'),
    ):
        hypothesis = 'hm' + '_right' * index + '_left'
        result.append(spec(name, f'forall N F. ({_multiplicative("N","F",name)}) -> ({target})', (),
                           _intro('N','F','hm') + _parts('hm',4) + ('exact '+hypothesis,), summary))
    result.append(spec(
        'signed_multiplicative_coprime_product',
        f'forall N F. ({_multiplicative("N","F","project_law_source")}) -> ({_law("N","F","project_law_target")})',
        (), _intro('N','F','hm') + _parts('hm',4) + ('exact hm_right_right_right',),
        'Read the exact coprime-product law, including positivity and the inclusive product bound.'))
    result.append(spec(
        'signed_multiplicative_intro',
        f'forall N F. ~(N=0) -> ({_table("N","F","intro_table")}) -> '
        f'({_table_at("F","1","2","intro_one")}) -> ({_law("N","F","intro_law")}) -> '
        f'({_multiplicative("N","F","intro_result")})', (),
        _intro('N','F','hn','ht','ho','hl') + ('split','exact hn','split','exact ht','split','exact ho','exact hl'),
        'Combine the actual table, positive normalization and bounded coprime law without any hidden premise.'))
    result.append(spec(
        'signed_multiplicative_zero_excluded',
        f'forall F. ~({_multiplicative("0","F","empty_excluded")})', (),
        _intro('F','hm') + ('cases hm','apply hm_left','refl'),
        'No zero-window table satisfies the strict nonempty multiplicativity convention.'))
    result.append(spec(
        'signed_multiplicative_at_one_value',
        f'forall N F z. ({_multiplicative("N","F","unique_one_source")}) -> '
        f'({_table_at("F","1","z","unique_one_input")}) -> z=2',
        ('divisor_signed_table_at_functional',),
        _intro('N','F','z','hm','hz') + _parts('hm',4)
        + _call('divisor_signed_table_at_functional','F','1','z','2')
        + ('exact hz','exact hm_right_right_left'),
        'Every actual lookup at one has the unique positive-one signed code 2.'))
    return tuple(result)


def _transport_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    restrict = _intro('N','K','F','hm','hk','hkn') + _parts('hm',4) + ('split','exact hk','split')
    restrict += _call('divisor_signed_table_restrict','N','K','F') + ('exact hm_right_left','exact hkn','split','exact hm_right_right_left')
    restrict += _intro('a','b','x','y','z','ha','hb','hp','hc','hx','hy','hz')
    restrict += _call('hm_right_right_right','a','b','x','y','z') + ('exact ha','exact hb')
    restrict += _call('le_trans','a*b','K','N') + ('exact hp','exact hkn','exact hc','exact hx','exact hy','exact hz')

    values = _intro('N','F','a','b','hm','ha','hb','hp','hc') + _parts('hm',4)
    for name, index in (('hx','a'), ('hy','b'), ('hz','a*b')):
        values += (f'have {name} : exists v. ({_table_at("F",index,"v",name+"actual")})',)
        values += _call('signed_table_lookup_any','N','F',index) + ('exact hm_right_left','cases '+name)
    values += ('exists x','exists x1','exists x2','split','exact hx_witness','split','exact hy_witness','split','exact hz_witness')
    values += _call('hm_right_right_right','a','b','x','x1','x2')
    values += ('exact ha','exact hb','exact hp','exact hc','exact hx_witness','exact hy_witness','exact hz_witness')

    entry = _intro('N','F','G','i','z','hG','he','hi','hb','hz')
    entry += (f'have hv : exists v. ({_table_at("G","i","v","positive_entry_actual")})',)
    entry += _call('signed_table_lookup_any','N','G','i') + ('exact hG','cases hv','have heq : z=x')
    entry += _call('he','i','z','x') + ('exact hi','exact hb','exact hz','exact hv_witness')
    entry += _rewrite('heq',_table_at('G','i','z','positive_entry_result'),'z') + ('exact hv_witness',)

    transport = _intro('N','F','G','hm','hG','he') + _parts('hm',4)
    transport += (f'have hr : {_positive_equal("G","F","N","reverse_positive")}',)
    transport += _intro('d','u','v','hd','hb','hu','hv') + ('symm',)
    transport += _call('he','d','v','u') + ('exact hd','exact hb','exact hv','exact hu')
    transport += ('split','exact hm_left','split','exact hG','split')
    transport += _call('signed_positive_table_entry_transport','N','F','G','1','2') + ('exact hG','exact he',)
    transport += _call('succ_ne_zero','0') + _call('one_le_of_ne_zero','N') + ('exact hm_left','exact hm_right_right_left')
    transport += _intro('a','b','x','y','z','ha','hb','hp','hc','hx','hy','hz')
    for name, index, value, lookup in (('hfx','a','x','hx'), ('hfy','b','y','hy'), ('hfz','a*b','z','hz')):
        transport += (f'have {name} : {_table_at("F",index,value,name+"source")}',)
        transport += _call('signed_positive_table_entry_transport','N','G','F',index,value)
        transport += ('exact hm_right_left','exact hr')
        if index == 'a':
            transport += ('exact ha',) + _call('le_trans','a','a*b','N')
            transport += _call('le_mul_of_one_le_right','a','b') + _call('one_le_of_ne_zero','b') + ('exact hb','exact hp')
        elif index == 'b':
            transport += ('exact hb',) + _call('le_trans','b','a*b','N')
            transport += _call('le_mul_of_one_le_left','a','b') + _call('one_le_of_ne_zero','a') + ('exact ha','exact hp')
        else:
            transport += ('intro hproductzero',) + _call('mul_ne_zero','a','b')
            transport += ('exact ha','exact hb','exact hproductzero','exact hp')
        transport += ('exact '+lookup,)
    transport += _call('hm_right_right_right','a','b','x','y','z')
    transport += ('exact ha','exact hb','exact hp','exact hc','exact hfx','exact hfy','exact hfz')
    return (
        spec('signed_multiplicative_restrict',
             f'forall N K F. ({_multiplicative("N","F","restrict_source")}) -> ~(K=0) -> '
             f'({_le("K","N","restrict_bound")}) -> ({_multiplicative("K","F","restrict_target")})',
             ('divisor_signed_table_restrict','le_trans'), restrict,
             'The same normalized table is multiplicative on every smaller nonempty positive prefix.'),
        spec('signed_multiplicative_product_values_exist',
             f'forall N F a b. ({_multiplicative("N","F","values_source")}) -> ~(a=0) -> ~(b=0) -> '
             f'({_le("a*b","N","values_bound")}) -> ({coprime("a","b",tag="values_coprime")}) -> exists x y z. '
             + _and(_table_at('F','a','x','values_first'), _table_at('F','b','y','values_second'),
                    _table_at('F','a*b','z','values_product'), _mul_code('x','y','z','values_law')),
             ('signed_table_lookup_any',), values,
             'Construct all three actual signed values and their multiplication witness; the law is not merely conditional on absent entries.'),
        spec('signed_positive_table_entry_transport',
             f'forall N F G i z. ({_table("N","G","entry_target_table")}) -> '
             f'({_positive_equal("F","G","N","entry_positive_equal")}) -> ~(i=0) -> '
             f'({_le("i","N","entry_bound")}) -> ({_table_at("F","i","z","entry_source")}) -> '
             f'({_table_at("G","i","z","entry_target")})',
             ('signed_table_lookup_any',), entry,
             'Transport a real positive lookup across prefix equality by first constructing the target lookup; no encoding or zero-value equality is required.'),
        spec('signed_multiplicative_positive_extensional',
             f'forall N F G. ({_multiplicative("N","F","extensional_source")}) -> '
             f'({_table("N","G","extensional_target_table")}) -> ({_positive_equal("F","G","N","extensional_equality")}) -> '
             f'({_multiplicative("N","G","extensional_target")})',
             ('signed_positive_table_entry_transport','succ_ne_zero','one_le_of_ne_zero','le_trans',
              'le_mul_of_one_le_right','le_mul_of_one_le_left','mul_ne_zero'), transport,
             'Multiplicativity depends only on the represented positive prefix, not on table codes, zeroth values or entries outside the product bound.'),
    )


def make_arithmetic_multiplicative_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _projection_rows(spec) + _transport_rows(spec)


__all__ = ['signed_multiplicative_prefix_relation', 'make_arithmetic_multiplicative_candidate_theorems']
