"""Actual first/last-factor grids for finite signed Dirichlet convolution.

The middle factor is witnessed by n=(a*e)*c.  A retained cell contains actual
signed lookups and the two products F(a)*(H(e)*G(c)); all omitted cells are
canonical zero.  Flat beta prefixes are constructed using genuine division
by S n and the existing signed-table append theorem.  Neither a sum identity
nor any convolution associativity assertion occurs in these definitions.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_table_extension_candidate import _extension
from .dirichlet_convolution_candidate import (
    _entry as _convolution_entry, _prefix as _convolution_prefix,
    _convolution, _convolution_table,
)
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at, _table_equal
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _dvd, _intro, _le, _lt, _part, _parts, _public, _rewrite,
)
from .signed_table_operations_candidate import _mul_code, _scalar
from .signed_rectangular_slice_candidate import _slice, _slice_sum
from .signed_rectangular_sums_candidate import _row_sums, _fubini_data


def _triple(u: str, v: str, w: str, z: str, tag: str) -> str:
    r='dfg_inner_'+tag
    return f'exists {r}. '+_and(_mul_code(v,w,r,tag+'inner'),_mul_code(u,r,z,tag+'outer'))


def _omitted(n: str, a: str, e: str, tag: str) -> str:
    return f'({a})=0 \\/ (({e})=0 \\/ ~({_dvd(f"({a})*({e})",n,tag+"nondivisor")}))'


def _entry(F: str, G: str, H: str, n: str, a: str, e: str, z: str, tag: str) -> str:
    c,u,v,w=('dfg_'+role+'_'+tag for role in ('middle','first','last','value'))
    active=_and(f'~(({a})=0)',f'~(({e})=0)',f'exists {c} {u} {v} {w}. '+_and(
        f'({n})=(({a})*({e}))*{c}',_table_at(F,a,u,tag+'first'),
        _table_at(H,e,v,tag+'last'),_table_at(G,c,w,tag+'middle'),_triple(u,v,w,z,tag+'product')))
    return f'({active}) \\/ ({_and(_omitted(n,a,e,tag+"omitted"),f"({z})=0")})'


def _index(n: str, a: str, e: str) -> str:
    return f'(S ({n}))*({a})+({e})'


def _flat_entry(F: str, G: str, H: str, n: str, i: str, z: str, tag: str) -> str:
    a,e='dfg_flat_row_'+tag,'dfg_flat_column_'+tag
    return f'exists {a} {e}. '+_and(f'({i})=({_index(n,a,e)})',
        _lt(e,f'S ({n})',tag+'remainder'),_entry(F,G,H,n,a,e,z,tag+'cell'))


def _flat_prefix(F: str, G: str, H: str, n: str, l: str, T: str, tag: str) -> str:
    i,z='dfg_flat_index_'+tag,'dfg_flat_value_'+tag
    return _and(_table(l,T,tag+'table'),f'forall {i} {z}. ({_le(i,l,tag+"bound")}) -> '
        f'({_table_at(T,i,z,tag+"lookup")}) -> ({_flat_entry(F,G,H,n,i,z,tag+"entry")})')


def _grid(F: str, G: str, H: str, n: str, T: str, tag: str) -> str:
    a,e,z=('dfg_grid_'+role+'_'+tag for role in ('row','column','value'))
    return _and(_table(f'(S ({n}))*(S ({n}))',T,tag+'table'),
        f'forall {a} {e} {z}. ({_le(a,n,tag+"row")}) -> ({_le(e,n,tag+"column")}) -> '
        f'({_table_at(T,_index(n,a,e),z,tag+"lookup")}) -> ({_entry(F,G,H,n,a,e,z,tag+"entry")})')


def _factor_row(F: str, G: str, H: str, n: str, a: str, V: str, tag: str) -> str:
    e,z='dfg_factor_column_'+tag,'dfg_factor_value_'+tag
    return _and(_table(f'S ({n})',V,tag+'table'),
        f'forall {e} {z}. ({_le(e,n,tag+"bound")}) -> ({_table_at(V,e,z,tag+"lookup")}) -> '
        f'({_entry(F,G,H,n,a,e,z,tag+"entry")})')


def signed_dirichlet_grid_entry_relation(F: str, G: str, H: str, n: str, a: str, e: str, z: str,
                                        *, tag: str, variables: tuple[str,...]) -> str:
    """A real middle factor and two signed products, or an explicit zero cell."""
    return _public(_entry,(F,G,H,n,a,e,z),tag=tag,variables=variables)


def signed_dirichlet_grid_table_relation(F: str, G: str, H: str, n: str, T: str,
                                        *, tag: str, variables: tuple[str,...]) -> str:
    """The actual row-major (S n)-square grid, without any supplied sum law."""
    return _public(_grid,(F,G,H,n,T),tag=tag,variables=variables)


def signed_dirichlet_flat_entry_relation(F: str, G: str, H: str, n: str, i: str, z: str,
                                        *, tag: str, variables: tuple[str,...]) -> str:
    """Actual quotient/remainder coordinates and the corresponding factor cell."""
    return _public(_flat_entry,(F,G,H,n,i,z),tag=tag,variables=variables)


def signed_dirichlet_flat_prefix_relation(F: str, G: str, H: str, n: str, l: str, T: str,
                                         *, tag: str, variables: tuple[str,...]) -> str:
    """A constructed inclusive beta prefix of the real flat factor cells."""
    return _public(_flat_prefix,(F,G,H,n,l,T),tag=tag,variables=variables)


def signed_dirichlet_factor_row_relation(F: str, G: str, H: str, n: str, a: str, V: str,
                                        *, tag: str, variables: tuple[str,...]) -> str:
    """An actual signed row records factor cells through the inclusive n bound."""
    return _public(_factor_row,(F,G,H,n,a,V),tag=tag,variables=variables)


def _omitted_contradiction(hyp: str, a_nonzero: str, e_nonzero: str, equation: str, factor: str) -> tuple[str,...]:
    return ('exfalso','cases '+hyp,'apply '+a_nonzero,'exact '+hyp+'_left',
            'cases '+hyp+'_right','apply '+e_nonzero,'exact '+hyp+'_right_left',
            'apply '+hyp+'_right_right','exists '+factor,'exact '+equation)


def _entry_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    omitted=_intro('F','G','H','n','a','e','z','ho','hv')+('cases hv',)+_parts('hv_left',3)
    omitted+=_cases('hv_left_right_right',4)+_parts('hv_left_right_right'+'_witness'*4,5)
    p='hv_left_right_right'+'_witness'*4
    omitted+=_omitted_contradiction('ho','hv_left_left','hv_left_right_left',p+'_left','x')
    omitted+=('cases hv_right','exact hv_right_right')

    read=_intro('F','G','H','n','a','e','c','u','v','w','z','ha','he','hc','hu','hv','hw','hentry')
    read+=('cases hentry',)+_parts('hentry_left',3)+_cases('hentry_left_right_right',4)
    p='hentry_left_right_right'+'_witness'*4
    read+=_parts(p,5)+('have hfactor : x=c',)+_call('mul_left_cancel_nonzero','a*e','x','c')
    read+=('intro hmulzero',)+_call('mul_ne_zero','a','e')+('exact ha','exact he','exact hmulzero','trans n','symm','exact '+p+'_left','exact hc')
    read+=_rewrite('hfactor',_table_at('G','x','x3','read_middle'),'x',_part(p,5,3))
    for old,table,index,value,assumption in (('x1','F','a','u','hu'),('x2','H','e','v','hv'),('x3','G','c','w','hw')):
        field={'x1':1,'x2':2,'x3':3}[old]
        read+=(f'have h{old} : {old}={value}',)+_call('divisor_signed_table_at_functional',table,index,old,value)
        read+=('exact '+_part(p,5,field),'exact '+assumption)
    target=_part(p,5,4)
    read+=_rewrite('hx1',_triple('x1','x2','x3','z','read_first'),'x1',target)
    read+=_rewrite('hx2',_triple('u','x2','x3','z','read_last'),'x2',target)
    read+=_rewrite('hx3',_triple('u','v','x3','z','read_middle_value'),'x3',target)+('exact '+target,)
    read+=('cases hentry_right',)+_omitted_contradiction('hentry_right_left','ha','he','hc','c')

    unique=_intro('F','G','H','n','a','e','z','Z','hz','hZ')+('cases hz',)+_parts('hz_left',3)
    unique+=_cases('hz_left_right_right',4)
    p='hz_left_right_right'+'_witness'*4
    unique+=_parts(p,5)+(f'have hother : {_triple("x1","x2","x3","Z","unique_other")}',)
    unique+=_call('dirichlet_grid_entry_factor_product','F','G','H','n','a','e','x','x1','x2','x3','Z')
    unique+=('exact hz_left_left','exact hz_left_right_left')+tuple('exact '+_part(p,5,i) for i in range(4))+('exact hZ',)
    unique+=('cases '+_part(p,5,4),'cases '+_part(p,5,4)+'_witness','cases hother','cases hother_witness',
             'have hinner : x4=x5')
    unique+=_call('signed_mul_functional','x2','x3','x4','x5')
    unique+=('exact '+_part(p,5,4)+'_witness_left','exact hother_witness_left')
    unique+=_rewrite('hinner',_mul_code('x1','x4','z','unique_outer'),'x4',_part(p,5,4)+'_witness_right')
    unique+=_call('signed_mul_functional','x1','x5','z','Z')
    unique+=('exact '+_part(p,5,4)+'_witness_right','exact hother_witness_right',
             'cases hz_right','trans 0','exact hz_right_right','symm')
    unique+=_call('dirichlet_grid_entry_omitted_value','F','G','H','n','a','e','Z')+('exact hz_right_left','exact hZ')

    total=_intro('F','G','H','n','a','e','hF','hG','hH')+('have ha : a=0 \\/ ~(a=0)',)+_call('eq_decidable','a','0')
    total+=('cases ha','exists 0')+_call('dirichlet_grid_entry_omitted','F','G','H','n','a','e')+('left','exact ha_left',
             'have he : e=0 \\/ ~(e=0)')+_call('eq_decidable','e','0')
    total+=('cases he','exists 0')+_call('dirichlet_grid_entry_omitted','F','G','H','n','a','e')
    total+=('right','left','exact he_left',f'have hd : ({_dvd("a*e","n","choice_yes")}) \\/ ~({_dvd("a*e","n","choice_no")})')
    total+=_call('multiple_decidable_nonzero','a*e','n')+('intro hmulzero',)+_call('mul_ne_zero','a','e')+('exact ha_right','exact he_right','exact hmulzero',
             'cases hd','cases hd_left')
    for table,index,value,hyp in (('F','a','u','hF'),('H','e','v','hH'),('G','x','w','hG')):
        total+=(f'have h{value} : exists z. ({_table_at(table,index,"z","choice_"+value)})',)
        total+=_call('signed_table_lookup_any','0',table,index)+('exact '+hyp,'cases h'+value)
    total+=(f'have hi : exists r. ({_mul_code("x2","x3","r","choice_inner")})',)
    total+=_call('signed_mul_total','x2','x3')+('cases hi',f'have ho : exists z. ({_mul_code("x1","x4","z","choice_outer")})')
    total+=_call('signed_mul_total','x1','x4')+('cases ho','exists x5')
    total+=_call('dirichlet_grid_entry_from_factorization','F','G','H','n','a','e','x','x1','x2','x3','x4','x5')
    total+=('exact ha_right','exact he_right','exact hd_left_witness','exact hu_witness','exact hv_witness','exact hw_witness',
             'exact hi_witness','exact ho_witness','exists 0')
    total+=_call('dirichlet_grid_entry_omitted','F','G','H','n','a','e')+('right','right','exact hd_right')

    transpose=_intro('F','G','H','n','a','e','z','hv')+('cases hv',)+_parts('hv_left',3)+_cases('hv_left_right_right',4)
    p='hv_left_right_right'+'_witness'*4
    transpose+=_parts(p,5)+('cases '+_part(p,5,4),'cases '+_part(p,5,4)+'_witness',
        f'have hi : exists r. ({_mul_code("x1","x3","r","transpose_inner")})')
    transpose+=_call('signed_mul_total','x1','x3')+('cases hi',f'have ho : {_mul_code("x2","x5","z","transpose_outer")}')
    transpose+=_call('signed_weighted_scalar_commute','x2','x3','x1','x4','x5','z')
    transpose+=('exact '+_part(p,5,4)+'_witness_left','exact hi_witness','exact '+_part(p,5,4)+'_witness_right')
    transpose+=_call('dirichlet_grid_entry_from_factorization','H','G','F','n','e','a','x','x2','x1','x3','x5','z')
    transpose+=('exact hv_left_right_left','exact hv_left_left','trans (a*e)*x','exact '+p+'_left',
                'congr','apply mul_comm','refl','exact '+_part(p,5,2),'exact '+_part(p,5,1),'exact '+_part(p,5,3),
                'exact hi_witness','exact ho','cases hv_right')
    transpose+=_rewrite('hv_right_right',_entry('H','G','F','n','e','a','z','transpose_zero'),'z')
    transpose+=_call('dirichlet_grid_entry_omitted','H','G','F','n','e','a')
    transpose+=('cases hv_right_left','right','left','exact hv_right_left_left',
                'cases hv_right_left_right','left','exact hv_right_left_right_left','right','right','intro hd','cases hd',
                'apply hv_right_left_right_right','exists x','trans (e*a)*x','exact hd_witness','congr','apply mul_comm','refl')

    return (
        spec('dirichlet_grid_entry_omitted',
             f'forall F G H n a e. ({_omitted("n","a","e","omit_guard")}) -> ({_entry("F","G","H","n","a","e","0","omit_result")})',
             (),_intro('F','G','H','n','a','e','h')+('right','split','exact h','refl'),
             'Zero first or last factors and genuine nondivisor products give canonical zero without reading either zero-index input.'),
        spec('dirichlet_grid_entry_from_factorization',
             f'forall F G H n a e c u v w r z. ~(a=0) -> ~(e=0) -> n=(a*e)*c -> '
             f'({_table_at("F","a","u","factor_first")}) -> ({_table_at("H","e","v","factor_last")}) -> ({_table_at("G","c","w","factor_middle")}) -> '
             f'({_mul_code("v","w","r","factor_inner")}) -> ({_mul_code("u","r","z","factor_outer")}) -> ({_entry("F","G","H","n","a","e","z","factor_result")})',
             (),_intro('F','G','H','n','a','e','c','u','v','w','r','z','ha','he','hc','hu','hv','hw','hr','hz')
             +('left','split','exact ha','split','exact he','exists c','exists u','exists v','exists w','split','exact hc',
               'split','exact hu','split','exact hv','split','exact hw','exists r','split','exact hr','exact hz'),
             'A real three-factor equation, three actual signed lookups and two actual products construct a retained grid cell.'),
        spec('dirichlet_grid_entry_omitted_value',
             f'forall F G H n a e z. ({_omitted("n","a","e","omitted_guard")}) -> ({_entry("F","G","H","n","a","e","z","omitted_cell")}) -> z=0',
             (),omitted,'Every actually omitted grid cell is zero; a retained factorization cannot coexist with its omitted guard.'),
        spec('dirichlet_grid_entry_factor_product',
             f'forall F G H n a e c u v w z. ~(a=0) -> ~(e=0) -> n=(a*e)*c -> '
             f'({_table_at("F","a","u","read_first")}) -> ({_table_at("H","e","v","read_last")}) -> ({_table_at("G","c","w","read_middle")}) -> '
             f'({_entry("F","G","H","n","a","e","z","read_cell")}) -> ({_triple("u","v","w","z","read_product")})',
             ('mul_left_cancel_nonzero','mul_ne_zero','divisor_signed_table_at_functional'),read,
             'Nonzero product cancellation identifies the supplied middle factor; canonical input lookups recover both actual signed products.'),
        spec('dirichlet_grid_entry_functional',
             f'forall F G H n a e z Z. ({_entry("F","G","H","n","a","e","z","unique_first")}) -> ({_entry("F","G","H","n","a","e","Z","unique_second")}) -> z=Z',
             ('dirichlet_grid_entry_factor_product','signed_mul_functional','dirichlet_grid_entry_omitted_value'),unique,
             'Each genuine first/last-factor cell has one canonical signed value, without identifying any table representation.'),
        spec('dirichlet_grid_entry_exists',
             f'forall F G H n a e. ({_table("0","F","choice_F")}) -> ({_table("0","G","choice_G")}) -> ({_table("0","H","choice_H")}) -> exists z. ({_entry("F","G","H","n","a","e","z","choice_result")})',
             ('eq_decidable','dirichlet_grid_entry_omitted','multiple_decidable_nonzero','mul_ne_zero','signed_table_lookup_any','signed_mul_total','dirichlet_grid_entry_from_factorization'),total,
             'Constructively decide the factor guards, extract the actual middle factor, and construct three signed lookups and both products.'),
        spec('dirichlet_grid_entry_transpose',
             f'forall F G H n a e z. ({_entry("F","G","H","n","a","e","z","transpose_source")}) -> ({_entry("H","G","F","n","e","a","z","transpose_target")})',
             ('signed_mul_total','signed_weighted_scalar_commute','dirichlet_grid_entry_from_factorization','mul_comm','dirichlet_grid_entry_omitted'),transpose,
             'Interchanging the first and last factors preserves an actual cell, by proved signed scalar interchange and a real factor-equation permutation.'),
    )


def _flat_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    total=_intro('F','G','H','n','i','hF','hG','hH')+(f'have hd : exists a e. '+_and('i=(S n)*a+e',_lt('e','S n','flat_division')),)
    total+=_call('division_remainder_exists','S n','i')+_call('succ_ne_zero','n')+_cases('hd',2)+('cases hd_witness_witness',)
    total+=(f'have hv : exists z. ({_entry("F","G","H","n","x","x1","z","flat_value")})',)
    total+=_call('dirichlet_grid_entry_exists','F','G','H','n','x','x1')+('exact hF','exact hG','exact hH','cases hv','exists x2','exists x','exists x1',
             'split','exact hd_witness_witness_left','split','exact hd_witness_witness_right','exact hv_witness')
    read=_intro('F','G','H','n','a','e','z','he','hv')+_cases('hv',2)+_parts('hv_witness_witness',3)
    read+=('have hcoordinates : x=a /\\ x1=e',)+_call('division_remainder_unique','S n',_index('n','a','e'),'x','x1','a','e')
    read+=('exact hv_witness_witness_left','exact hv_witness_witness_right_left','refl','exact he','cases hcoordinates')
    read+=_rewrite('hcoordinates_left',_entry('F','G','H','n','x','x1','z','flat_read_first'),'x','hv_witness_witness_right_right')
    read+=_rewrite('hcoordinates_right',_entry('F','G','H','n','a','x1','z','flat_read_last'),'x1','hv_witness_witness_right_right')
    read+=('exact hv_witness_witness_right_right',)
    return (
        spec('dirichlet_grid_flat_entry_exists',
             f'forall F G H n i. ({_table("0","F","flat_F")}) -> ({_table("0","G","flat_G")}) -> ({_table("0","H","flat_H")}) -> exists z. ({_flat_entry("F","G","H","n","i","z","flat_total")})',
             ('division_remainder_exists','succ_ne_zero','dirichlet_grid_entry_exists'),total,
             'Actual division by S n decodes every flat index, then the genuinely constructed factor cell supplies its signed value.'),
        spec('dirichlet_grid_flat_entry_coordinates',
             f'forall F G H n a e z. ({_lt("e","S n","flat_read_bound")}) -> ({_flat_entry("F","G","H","n",_index("n","a","e"),"z","flat_read_source")}) -> ({_entry("F","G","H","n","a","e","z","flat_read_target")})',
             ('division_remainder_unique',),read,
             'Uniqueness of the actual quotient and strict remainder recovers the specified grid coordinates, rather than assuming a decoding oracle.'),
    )


def _prefix_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    base=_intro('F','G','H','n','T','z','hT','hz','hv')+('split','exact hT')+_intro('i','u','hi','hu')
    base+=('have hi0 : i=0',)+_call('le_zero','i')+('exact hi',)
    base+=_rewrite('hi0',_table_at('T','i','u','base_read'),'i','hu')
    base+=('have hvalue : z=u',)+_call('divisor_signed_table_at_functional','T','0','z','u')+('exact hz','exact hu')
    base+=_rewrite('hvalue',_flat_entry('F','G','H','n','0','z','base_value'),'z','hv')
    base+=_rewrite('hi0',_flat_entry('F','G','H','n','i','u','base_target'),'i')+('exact hv',)

    append=_intro('F','G','H','n','l','T','z','ht','hz')+('cases ht',)
    append+=(f'have hx : exists U. ({_extension("T","U","S l","z","append_actual")})',)
    append+=_call('arithmetic_signed_table_append','l','T','z')+('exact ht_left','cases hx')+_parts('hx_witness',3)
    append+=('exists x','split','split','exact hx_witness_left')+_intro('i','u','hi','hu')
    append+=(f'have hc : i=S l \\/ ({_lt("i","S l","append_cases")})',)
    append+=_call('le_eq_or_lt','i','S l')+('exact hi','cases hc')
    append+=_rewrite('hc_left',_table_at('x','i','u','append_last_read'),'i','hu')
    append+=('have heq : z=u',)+_call('divisor_signed_table_at_functional','x','S l','z','u')
    append+=('exact hx_witness_right_right','exact hu')
    append+=_rewrite('heq',_flat_entry('F','G','H','n','S l','z','append_last_value'),'z','hz')
    append+=_rewrite('hc_left',_flat_entry('F','G','H','n','i','u','append_last_target'),'i')+('exact hz',)
    append+=(f'have hib : {_le("i","l","append_previous_bound")}',)+_call('le_of_succ_le_succ','i','l')+('exact hc_right',)
    append+=(f'have hv : exists v. ({_table_at("T","i","v","append_previous_value")})',)
    append+=_call('divisor_signed_table_lookup','l','T','i')+('exact ht_left','exact hib','cases hv','have heq : x1=u')
    append+=_call('hx_witness_right_left','i','x1','u')+('exact hc_right','exact hv_witness','exact hu')
    append+=_rewrite('heq',_table_at('T','i','x1','append_previous_transport'),'x1','hv_witness')
    append+=_call('ht_right','i','u')+('exact hib','exact hv_witness','exact hx_witness_right_left')

    exists=_intro('F','G','H','n','l')+('induction l',)+_intro('hF','hG','hH')
    exists+=(f'have hv : exists z. ({_flat_entry("F","G","H","n","0","z","prefix_base_value")})',)
    exists+=_call('dirichlet_grid_flat_entry_exists','F','G','H','n','0')+('exact hF','exact hG','exact hH','cases hv')
    exists+=(f'have ht : exists T. ({_and(_table("0","T","prefix_base_table"),_table_at("T","0","x","prefix_base_entry"))})',)
    exists+=_call('arithmetic_signed_table_singleton','x')+('cases ht','cases ht_witness','exists x1')
    exists+=_call('dirichlet_grid_flat_prefix_zero','F','G','H','n','x1','x')
    exists+=('exact ht_witness_left','exact ht_witness_right','exact hv_witness')
    exists+=_intro('hF','hG','hH')+(f'have hp : exists T. ({_flat_prefix("F","G","H","n","l","T","prefix_previous")})','apply IH')
    exists+=('exact hF','exact hG','exact hH','cases hp',
             f'have hv : exists z. ({_flat_entry("F","G","H","n","S l","z","prefix_next_value")})')
    exists+=_call('dirichlet_grid_flat_entry_exists','F','G','H','n','S l')+('exact hF','exact hG','exact hH','cases hv')
    exists+=(f'have hext : exists U. ({_and(_flat_prefix("F","G","H","n","S l","U","prefix_next"),_table_equal("x","U","S l","prefix_preserved"))})',)
    exists+=_call('dirichlet_grid_flat_prefix_append','F','G','H','n','l','x','x1')
    exists+=('exact hp_witness','exact hv_witness','cases hext','cases hext_witness','exists x2','exact hext_witness_left')

    return (
        spec('dirichlet_grid_flat_prefix_zero',
             f'forall F G H n T z. ({_table("0","T","base_table")}) -> ({_table_at("T","0","z","base_entry")}) -> '
             f'({_flat_entry("F","G","H","n","0","z","base_value")}) -> ({_flat_prefix("F","G","H","n","0","T","base_prefix")})',
             ('le_zero','divisor_signed_table_at_functional'),base,
             'A genuinely constructed singleton supplies the first flat cell; no finite table or choice axiom is used.'),
        spec('dirichlet_grid_flat_prefix_append',
             f'forall F G H n l T z. ({_flat_prefix("F","G","H","n","l","T","append_prefix")}) -> '
             f'({_flat_entry("F","G","H","n","S l","z","append_value")}) -> exists U. '
             +_and(_flat_prefix('F','G','H','n','S l','U','append_result'),_table_equal('T','U','S l','append_preserved')),
             ('arithmetic_signed_table_append','le_eq_or_lt','le_of_succ_le_succ','divisor_signed_table_at_functional','divisor_signed_table_lookup'),append,
             'Append one actual signed flat cell by real beta-stream extension and preserve all preceding represented values.'),
        spec('dirichlet_grid_flat_prefix_exists',
             f'forall F G H n l. ({_table("0","F","prefix_F")}) -> ({_table("0","G","prefix_G")}) -> ({_table("0","H","prefix_H")}) -> exists T. ({_flat_prefix("F","G","H","n","l","T","prefix_result")})',
             ('dirichlet_grid_flat_entry_exists','arithmetic_signed_table_singleton','dirichlet_grid_flat_prefix_zero','dirichlet_grid_flat_prefix_append'),exists,
             'Ordinary induction constructs each actual inclusive flat prefix, with an independently witnessed quotient, remainder and signed value at every extension.'),
    )


def _grid_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    square='(S n)*(S n)'
    construct=_intro('F','G','H','n','T','hp')+('cases hp','split','exact hp_left')+_intro('a','e','z','ha','he','hz')
    construct+=_call('dirichlet_grid_flat_entry_coordinates','F','G','H','n','a','e','z')
    construct+=_call('succ_le_succ','e','n')+('exact he',)
    construct+=_call('hp_right',_index('n','a','e'),'z')
    construct+=('have hcomm : (S n)*a=a*(S n)','apply mul_comm','rewrite hcomm')
    construct+=_call('lt_to_le','a*(S n)+e',square)+_call('matrix_recursive_flattened_index_bound','S n','a','e')
    construct+=_call('succ_le_succ','a','n')+('exact ha',)+_call('succ_le_succ','e','n')+('exact he','exact hz')
    exists=_intro('F','G','H','n','hF','hG','hH')+(f'have hp : exists T. ({_flat_prefix("F","G","H","n",square,"T","grid_flat")})',)
    exists+=_call('dirichlet_grid_flat_prefix_exists','F','G','H','n',square)
    exists+=('exact hF','exact hG','exact hH','cases hp','exists x')
    exists+=_call('dirichlet_grid_from_flat_prefix','F','G','H','n','x')+('exact hp_witness',)
    return (
        spec('dirichlet_grid_from_flat_prefix',
             f'forall F G H n T. ({_flat_prefix("F","G","H","n",square,"T","grid_source")}) -> ({_grid("F","G","H","n","T","grid_result")})',
             ('dirichlet_grid_flat_entry_coordinates','succ_le_succ','mul_comm','lt_to_le','matrix_recursive_flattened_index_bound'),construct,
             'The actual flat prefix supplies every bounded grid cell; the old checked matrix index bound and unique division prove the row-major decoding.'),
        spec('dirichlet_grid_table_exists',
             f'forall F G H n. ({_table("0","F","grid_F")}) -> ({_table("0","G","grid_G")}) -> ({_table("0","H","grid_H")}) -> exists T. ({_grid("F","G","H","n","T","grid_total")})',
             ('dirichlet_grid_flat_prefix_exists','dirichlet_grid_from_flat_prefix'),exists,
             'Construct the entire real first/last-factor grid, including its harmless extra certified endpoint, from actual input tables.'),
        spec('dirichlet_grid_table_lookup',
             f'forall F G H n T a e z. ({_grid("F","G","H","n","T","grid_lookup")}) -> ({_le("a","n","grid_row_bound")}) -> '
             f'({_le("e","n","grid_column_bound")}) -> ({_table_at("T",_index("n","a","e"),"z","grid_lookup_value")}) -> ({_entry("F","G","H","n","a","e","z","grid_lookup_result")})',
             (),_intro('F','G','H','n','T','a','e','z','hg','ha','he','hz')+('cases hg',)
             +_call('hg_right','a','e','z')+('exact ha','exact he','exact hz'),
             'Every actual bounded row-major lookup has precisely the independently defined factor-cell graph.'),
    )


def _factor_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    factor=_intro('n','a','e','c','q','ha','hq','hc')+_call('mul_left_cancel_nonzero','a','q','e*c')
    factor+=('exact ha','trans n','symm','exact hq','trans (a*e)*c','exact hc','apply mul_assoc')

    lift=_intro('F','G','H','n','a','q','u','e','v','z','ha','hq','hu','hv','hz')
    lift+=('cases hv','cases hv_left')+_cases('hv_left_right',3)+_parts('hv_left_right'+'_witness'*3,4)
    p='hv_left_right'+'_witness'*3
    lift+=_call('dirichlet_grid_entry_from_factorization','F','G','H','n','a','e','x','u','x1','x2','v','z')
    lift+=('exact ha','exact hv_left_left','trans a*q','exact hq','rewrite '+p+'_left','symm','apply mul_assoc',
           'exact hu','exact '+_part(p,4,1),'exact '+_part(p,4,2),'exact '+_part(p,4,3),'exact hz','cases hv_right')
    lift+=_rewrite('hv_right_right',_mul_code('u','v','z','lift_zero_product'),'v','hz')
    lift+=('have hz0 : z=0',)+_call('signed_mul_functional','u','0','z','0')+('exact hz',)+_call('signed_mul_zero_right','u')
    lift+=_rewrite('hz0',_entry('F','G','H','n','a','e','z','lift_zero_cell'),'z')
    lift+=_call('dirichlet_grid_entry_omitted','F','G','H','n','a','e')
    lift+=('cases hv_right_left','right','left','exact hv_right_left_left','right','right','intro hdiv','cases hdiv',
           'apply hv_right_left_right','exists x')
    lift+=_call('dirichlet_grid_middle_factor_equation','n','a','e','x','q')
    lift+=('exact ha','exact hq','exact hdiv_witness')

    read=_intro('F','G','H','n','a','q','u','e','v','z','ha','hq','hu','hv','hz')
    read+=(f'have hp : exists w. ({_mul_code("u","v","w","row_read_product")})',)
    read+=_call('signed_mul_total','u','v')+('cases hp','have heq : x=z')
    read+=_call('dirichlet_grid_entry_functional','F','G','H','n','a','e','x','z')
    read+=_call('dirichlet_grid_entry_from_convolution_entry','F','G','H','n','a','q','u','e','v','x')
    read+=('exact ha','exact hq','exact hu','exact hv','exact hp_witness','exact hz')
    read+=_rewrite('heq',_mul_code('u','v','x','row_read_transport'),'x','hp_witness')+('exact hp_witness',)

    omitted=_intro('F','G','H','n','a','e','z','ho','hz')
    omitted+=_call('dirichlet_grid_entry_omitted_value','F','G','H','n','a','e','z')
    omitted+=('cases ho','left','exact ho_left','right','right','intro hdiv','cases hdiv',
              'apply ho_right','exists e*x','trans (a*e)*x','exact hdiv_witness','apply mul_assoc','exact hz')

    scalar=_intro('F','G','H','n','a','q','u','V','P','ha','hq','hu','hP','hV')
    scalar+=('split',)+_call('signed_table_domain_resize','n','S n','P')+('cases hP','exact hP_left','split','cases hV','exact hV_left')
    scalar+=_intro('e','he')+(f'have hp : exists v. ({_table_at("P","e","v","row_scalar_input")})',)
    scalar+=_call('signed_table_lookup_any','n','P','e')+('cases hP','exact hP_left','cases hp')
    scalar+=(f'have hv : exists z. ({_table_at("V","e","z","row_scalar_output")})',)
    scalar+=_call('signed_table_lookup_any','S n','V','e')+('cases hV','exact hV_left','cases hv','exists x','exists x1',
             'split','exact hp_witness','split','exact hv_witness')
    scalar+=_call('dirichlet_grid_entry_convolution_product','F','G','H','n','a','q','u','e','x','x1')
    scalar+=('exact ha','exact hq','exact hu')
    scalar+=_call('dirichlet_convolution_prefix_lookup','H','G','q','n','P','e','x')+('exact hP',)
    scalar+=_call('le_of_succ_le_succ','e','n')+('exact he','exact hp_witness','cases hV')
    scalar+=_call('hV_right','e','x1')+_call('le_of_succ_le_succ','e','n')+('exact he','exact hv_witness')
    return (
        spec('dirichlet_grid_middle_factor_equation',
             'forall n a e c q. ~(a=0) -> n=a*q -> n=(a*e)*c -> q=e*c',
             ('mul_left_cancel_nonzero','mul_assoc'),factor,
             'A positive first factor cancels from the actual nested factor equations, identifying the inner convolution quotient.'),
        spec('dirichlet_grid_entry_from_convolution_entry',
             f'forall F G H n a q u e v z. ~(a=0) -> n=a*q -> ({_table_at("F","a","u","row_lift_first")}) -> '
             f'({_convolution_entry("H","G","q","e","v","row_lift_inner")}) -> ({_mul_code("u","v","z","row_lift_product")}) -> ({_entry("F","G","H","n","a","e","z","row_lift_result")})',
             ('dirichlet_grid_entry_from_factorization','mul_assoc','signed_mul_functional','signed_mul_zero_right','dirichlet_grid_entry_omitted','dirichlet_grid_middle_factor_equation'),lift,
             'Multiplying an actual inner convolution summand gives the exact factor cell, including zero and omitted inner divisors.'),
        spec('dirichlet_grid_entry_convolution_product',
             f'forall F G H n a q u e v z. ~(a=0) -> n=a*q -> ({_table_at("F","a","u","row_product_first")}) -> '
             f'({_convolution_entry("H","G","q","e","v","row_product_inner")}) -> ({_entry("F","G","H","n","a","e","z","row_product_cell")}) -> ({_mul_code("u","v","z","row_product_result")})',
             ('signed_mul_total','dirichlet_grid_entry_functional','dirichlet_grid_entry_from_convolution_entry'),read,
             'Canonical factor-cell functionality identifies its value with the actual scalar multiple of any witnessed inner convolution summand.'),
        spec('dirichlet_grid_nondivisor_row_value_zero',
             f'forall F G H n a e z. (a=0 \\/ ~({_dvd("a","n","zero_row_guard")})) -> ({_entry("F","G","H","n","a","e","z","zero_row_cell")}) -> z=0',
             ('dirichlet_grid_entry_omitted_value','mul_assoc'),omitted,
             'A zero or nondivisor first factor forces every actual row cell to zero, independently of input values at zero.'),
        spec('dirichlet_factor_row_scalar',
             f'forall F G H n a q u V P. ~(a=0) -> n=a*q -> ({_table_at("F","a","u","row_scalar_first")}) -> '
             f'({_convolution_prefix("H","G","q","n","P","row_scalar_prefix")}) -> ({_factor_row("F","G","H","n","a","V","row_scalar_cells")}) -> ({_scalar("u","P","V","S n","row_scalar_result")})',
             ('signed_table_domain_resize','signed_table_lookup_any','dirichlet_grid_entry_convolution_product','dirichlet_convolution_prefix_lookup','le_of_succ_le_succ'),scalar,
             'A genuine factor row is the actual pointwise scalar product of a constructed padded convolution prefix, on the identical S n-entry window.'),
    )


def _physical_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    rows=[]
    for transpose in (False,True):
        name='dirichlet_grid_'+('column' if transpose else 'row')+'_slice'
        first,last=('H','F') if transpose else ('F','H')
        offset,stride=('0+1*a','S n') if transpose else ('0+(S n)*a','1')
        source_index=f'({offset})+({stride})*e'
        target_index=_index('n','e','a') if transpose else _index('n','a','e')
        body=_intro('F','G','H','n','T','a','V','hg','ha','hs')+('split',)+_parts('hs',3)
        body+=('exact hs_right_left',)+_intro('e','z','he','hz')
        body+=(f'have hl : {_table_at("T",source_index,"z",name+"_source_entry")}',)
        body+=_call('signed_rectangular_slice_lookup','T','V',offset,stride,'S n','e','z')
        body+=('exact hs',)+_call('succ_le_succ','e','n')+('exact he','exact hz',
                f'have hindex : {source_index}={target_index}')
        if transpose:
            body+=('trans a+(S n)*e','congr','trans 1*a','apply zero_add','apply one_mul','refl','apply add_comm')
        else:
            body+=('congr','apply zero_add','apply one_mul')
        body+=_rewrite('hindex',_table_at('T','i','z',name+'_index_transport'),'i','hl')
        if transpose:
            body+=_call('dirichlet_grid_entry_transpose','F','G','H','n','e','a','z')
        body+=_call('dirichlet_grid_table_lookup','F','G','H','n','T',* (('e','a') if transpose else ('a','e')),'z')
        body+=('exact hg',*(('exact he','exact ha') if transpose else ('exact ha','exact he')),'exact hl')
        deps=('signed_rectangular_slice_lookup','succ_le_succ','zero_add','one_mul','dirichlet_grid_table_lookup')
        if transpose:deps+=('add_comm','dirichlet_grid_entry_transpose')
        rows.append(spec(name,
            f'forall F G H n T a V. ({_grid("F","G","H","n","T",name+"_grid")}) -> ({_le("a","n",name+"_bound")}) -> '
            f'({_slice("T","V",offset,stride,"S n",name+"_slice")}) -> ({_factor_row(first,"G",last,"n","a","V",name+"_result")})',
            deps,body,
            'An actual '+('column' if transpose else 'row')+' slice supplies the exact factor-row values; every affine coordinate is transported by a proved natural equality.'))
    exists=_intro('F','G','H','n','hF','hG','hH')+(f'have hg : exists T. ({_grid("F","G","H","n","T","fubini_grid")})',)
    exists+=_call('dirichlet_grid_table_exists','F','G','H','n')+('exact hF','exact hG','exact hH','cases hg')
    exists+=(f'have hf : exists R C z. ({_fubini_data("x","R","C","0","S n","1","S n","S n","z","fubini_rows")})',)
    exists+=_call('signed_rectangular_row_major_fubini','x','S n','S n')+('cases hg_witness','exact hg_witness_left')
    exists+=_cases('hf',3)+('exists x','exists x1','exists x2','exists x3','split','exact hg_witness','exact hf_witness_witness_witness')
    rows.append(spec('dirichlet_grid_fubini_exists',
        f'forall F G H n. ({_table("0","F","fubini_F")}) -> ({_table("0","G","fubini_G")}) -> ({_table("0","H","fubini_H")}) -> exists T R C z. '
        +_and(_grid('F','G','H','n','T','fubini_actual_grid'),_fubini_data('T','R','C','0','S n','1','S n','S n','z','fubini_actual_sums')),
        ('dirichlet_grid_table_exists','signed_rectangular_row_major_fubini'),exists,
        'Construct the actual factor grid, both actual signed row/column tables and genuine prefix-sum traces with one common value, by the already proved finite Fubini theorem.'))
    return tuple(rows)


def _row_sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    zero=_intro('F','G','H','n','a','V','z','hr','ho','hs')
    zero+=_call('signed_prefix_sum_zero_value','V','S n','z')+_intro('i','w','hzero','hi','hw')
    zero+=_call('dirichlet_grid_nondivisor_row_value_zero','F','G','H','n','a','i','w')
    zero+=('exact ho','cases hr')+_call('hr_right','i','w')+_call('le_of_succ_le_succ','i','n')
    zero+=('exact hi','exact hw','exact hs')

    product=_intro('F','G','H','n','a','q','u','V','z','hH','hG','hn','ha','hq','hu','hr','hz')
    product+=('have hq0 : ~(q=0)','intro hzero')+_call('factor_nonzero_right','n','a','q')
    product+=('exact hn','exact hq','exact hzero',f'have hqn : {_le("q","n","row_sum_quotient_bound")}')
    product+=_call('divisor_le_nonzero','q','n')+('exact hn','exists a','trans a*q','exact hq','apply mul_comm')
    product+=(f'have hp : exists P. ({_convolution_prefix("H","G","q","n","P","row_sum_prefix")})',)
    product+=_call('dirichlet_convolution_prefix_exists','H','G','q','n')+('exact hH','exact hG','cases hp')
    product+=(f'have hs : exists v. ({_signed_sum("x","S n","v","row_sum_actual_sum")})',)
    product+=_call('arithmetic_signed_sum_exists','n','x','S n')+('cases hp_witness','exact hp_witness_left','cases hs','exists x1','split')
    product+=_call('dirichlet_convolution_from_padded_prefix','H','G','q','n','x','x1')
    product+=('exact hq0','exact hqn','exact hp_witness','exact hs_witness')
    product+=_call('signed_prefix_sum_scalar_multiply','S n','u','x','V','x1','z')
    product+=_call('dirichlet_factor_row_scalar','F','G','H','n','a','q','u','V','x')
    product+=('exact ha','exact hq','exact hu','exact hp_witness','exact hr','exact hs_witness','exact hz')

    entry=_intro('N','F','G','H','U','n','a','V','z','hF','hU','hn','hnN','haN','hr','hz')
    entry+=('have ha : a=0 \\/ ~(a=0)',)+_call('eq_decidable','a','0')+('cases ha','right','split','left','exact ha_left')
    entry+=_call('dirichlet_factor_row_zero_sum','F','G','H','n','a','V','z')
    entry+=('exact hr','left','exact ha_left','exact hz',f'have hd : ({_dvd("a","n","row_entry_divisor")}) \\/ ~({_dvd("a","n","row_entry_nondivisor")})')
    entry+=_call('multiple_decidable_nonzero','a','n')+('exact ha_right','cases hd','cases hd_left')
    entry+=(f'have hf : exists u. ({_table_at("F","a","u","row_entry_first")})',)
    entry+=_call('signed_table_lookup_any','N','F','a')+('exact hF','cases hf')
    entry+=(f'have hi : exists v. ({_and(_convolution("H","G","x","v","row_entry_inner"),_mul_code("x1","v","z","row_entry_scaled"))})',)
    entry+=_call('dirichlet_factor_row_sum_product','F','G','H','n','a','x','x1','V','z')
    entry+=_call('signed_table_domain_resize','N','0','H')+_parts('hU',4)+('exact hU_left',)
    entry+=_call('signed_table_domain_resize','N','0','G')+_parts('hU',4)+('exact hU_right_left',
             'exact hn','exact ha_right','exact hd_left_witness','exact hf_witness','exact hr','exact hz','cases hi','cases hi_witness')
    entry+=(f'have ht : exists v. ({_and(_table_at("U","x","v","row_entry_output_lookup"),_convolution("H","G","x","v","row_entry_output_conv"))})',)
    entry+=_call('dirichlet_convolution_table_lookup','N','H','G','U','x')+('exact hU','intro hx0')
    entry+=_call('factor_nonzero_right','n','a','x')+('exact hn','exact hd_left_witness','exact hx0')
    entry+=_call('le_trans','x','n','N')+_call('divisor_le_nonzero','x','n')
    entry+=('exact hn','exists a','trans a*x','exact hd_left_witness','apply mul_comm','exact hnN','cases ht','cases ht_witness',
             'have hvalue : x2=x3')
    entry+=_call('dirichlet_convolution_sum_functional','H','G','x','x2','x3')+('exact hi_witness_left','exact ht_witness_right')
    entry+=_rewrite('hvalue',_mul_code('x1','x2','z','row_entry_value_transport'),'x2','hi_witness_right')
    entry+=_call('dirichlet_convolution_entry_from_quotient','F','U','n','a','x','x1','x3','z')
    entry+=('exact ha_right','exact hd_left_witness','exact hf_witness','exact ht_witness_left','exact hi_witness_right',
             'right','split','right','exact hd_right')
    entry+=_call('dirichlet_factor_row_zero_sum','F','G','H','n','a','V','z')+('exact hr','right','exact hd_right','exact hz')
    return (
        spec('dirichlet_factor_row_zero_sum',
             f'forall F G H n a V z. ({_factor_row("F","G","H","n","a","V","row_zero_values")}) -> (a=0 \\/ ~({_dvd("a","n","row_zero_guard")})) -> '
             f'({_signed_sum("V","S n","z","row_zero_sum")}) -> z=0',
             ('signed_prefix_sum_zero_value','dirichlet_grid_nondivisor_row_value_zero','le_of_succ_le_succ'),zero,
             'The actual signed sum of a zero or nondivisor factor row is zero; no value at either input zero index is used.'),
        spec('dirichlet_factor_row_sum_product',
             f'forall F G H n a q u V z. ({_table("0","H","row_sum_H")}) -> ({_table("0","G","row_sum_G")}) -> ~(n=0) -> ~(a=0) -> n=a*q -> '
             f'({_table_at("F","a","u","row_sum_first")}) -> ({_factor_row("F","G","H","n","a","V","row_sum_values")}) -> ({_signed_sum("V","S n","z","row_sum_given")}) -> '
             f'exists v. ({_and(_convolution("H","G","q","v","row_sum_inner"),_mul_code("u","v","z","row_sum_result"))})',
             ('factor_nonzero_right','divisor_le_nonzero','mul_comm','dirichlet_convolution_prefix_exists','arithmetic_signed_sum_exists',
              'dirichlet_convolution_from_padded_prefix','signed_prefix_sum_scalar_multiply','dirichlet_factor_row_scalar'),product,
             'Construct the actual inner convolution sum, prove its positive quotient bound, remove its zero padding and identify the row total by actual signed scalar linearity.'),
        spec('dirichlet_factor_row_nested_entry',
             f'forall N F G H U n a V z. ({_table("N","F","row_entry_F")}) -> ({_convolution_table("N","H","G","U","row_entry_inner_table")}) -> ~(n=0) -> '
             f'({_le("n","N","row_entry_domain")}) -> ({_le("a","n","row_entry_index")}) -> ({_factor_row("F","G","H","n","a","V","row_entry_values")}) -> '
             f'({_signed_sum("V","S n","z","row_entry_sum")}) -> ({_convolution_entry("F","U","n","a","z","row_entry_result")})',
             ('eq_decidable','dirichlet_factor_row_zero_sum','multiple_decidable_nonzero','signed_table_lookup_any',
              'dirichlet_factor_row_sum_product','signed_table_domain_resize','dirichlet_convolution_table_lookup','factor_nonzero_right',
              'le_trans','divisor_le_nonzero','mul_comm','dirichlet_convolution_sum_functional','dirichlet_convolution_entry_from_quotient'),entry,
             'Each actual factor-row total is precisely an outer convolution summand of the genuine inner output table, with all positive-index bounds proved.'),
    )


def _nested_prefix_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    rows=[]
    for transpose in (False,True):
        name='dirichlet_grid_'+('column' if transpose else 'row')+'_sums_convolution_prefix'
        first,last=('H','F') if transpose else ('F','H')
        s,t=('1','S n') if transpose else ('S n','1')
        physical='dirichlet_grid_'+('column' if transpose else 'row')+'_slice'
        body=_intro('N','F','G','H','U','n','T','R','hF','hU','hn','hnN','hg','hr')
        body+=('split',)+_call('signed_table_domain_resize','S n','n','R')+_parts('hr',3)+('exact hr_right_left',)
        body+=_intro('a','z','ha','hz')
        body+=(f'have hs : {_slice_sum("T",f"0+({s})*a",t,"S n","z",name+"_slice_sum")}',)
        body+=_call('signed_rectangular_row_sums_lookup','T','R','0',s,t,'S n','S n','a','z')
        body+=('exact hr',)+_call('succ_le_succ','a','n')+('exact ha','exact hz','cases hs','cases hs_witness')
        body+=_call('dirichlet_factor_row_nested_entry','N',first,'G',last,'U','n','a','x','z')
        body+=('exact hF','exact hU','exact hn','exact hnN','exact ha')
        body+=_call(physical,'F','G','H','n','T','a','x')+('exact hg','exact ha','exact hs_witness_left','exact hs_witness_right')
        rows.append(spec(name,
            f'forall N F G H U n T R. ({_table("N",first,name+"_outer_input")}) -> ({_convolution_table("N",last,"G","U",name+"_inner_table")}) -> '
            f'~(n=0) -> ({_le("n","N",name+"_domain")}) -> ({_grid("F","G","H","n","T",name+"_grid")}) -> '
            f'({_row_sums("T","R","0",s,t,"S n","S n",name+"_rows")}) -> ({_convolution_prefix(first,"U","n","n","R",name+"_result")})',
            ('signed_table_domain_resize','signed_rectangular_row_sums_lookup','succ_le_succ','dirichlet_factor_row_nested_entry',physical),body,
            'The actual '+('column' if transpose else 'row')+' sum table is the genuine nested-convolution summand prefix, including every omitted zero row and every proved positive quotient bound.'))
    return tuple(rows)


def _interchange_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    data=_and(_grid('F','G','H','n','T','interchange_grid'),
              _fubini_data('T','R','C','0','S n','1','S n','S n','z','interchange_sums'))
    body=_intro('N','F','G','H','U','V','n','a','b','hU','hV','hn','hN','ha','hb')
    body+=(f'have hf : exists T R C z. ({data})',)+_call('dirichlet_grid_fubini_exists','F','G','H','n')
    for table,hyp,part in (('F','hV',0),('G','hU',1),('H','hU',0)):
        body+=_call('signed_table_domain_resize','N','0',table)+_parts(hyp,4)+('exact '+_part(hyp,4,part),)
    body+=_cases('hf',4)
    p='hf'+'_witness'*4
    body+=_parts(p,5)+('trans x3',)
    body+=_call('dirichlet_convolution_sum_functional','F','U','n','a','x3')+('exact ha','split','exact hn','exists x1','split')
    body+=_call('dirichlet_grid_row_sums_convolution_prefix','N','F','G','H','U','n','x','x1')
    body+=_parts('hV',4)+('exact hV_left','exact hU','exact hn','exact hN','exact '+_part(p,5,0),'exact '+_part(p,5,1),'exact '+_part(p,5,3))
    body+=_call('dirichlet_convolution_sum_functional','H','V','n','x3','b')+('split','exact hn','exists x2','split')
    body+=_call('dirichlet_grid_column_sums_convolution_prefix','N','F','G','H','V','n','x','x2')
    body+=_parts('hU',4)+('exact hU_left','exact hV','exact hn','exact hN','exact '+_part(p,5,0),'exact '+_part(p,5,2),'exact '+_part(p,5,4),'exact hb')
    return (spec('dirichlet_convolution_fubini_interchange',
        f'forall N F G H U V n a b. ({_convolution_table("N","H","G","U","interchange_HG")}) -> '
        f'({_convolution_table("N","F","G","V","interchange_FG")}) -> ~(n=0) -> ({_le("n","N","interchange_domain")}) -> '
        f'({_convolution("F","U","n","a","interchange_first")}) -> ({_convolution("H","V","n","b","interchange_second")}) -> a=b',
        ('dirichlet_grid_fubini_exists','signed_table_domain_resize','dirichlet_convolution_sum_functional',
         'dirichlet_grid_row_sums_convolution_prefix','dirichlet_grid_column_sums_convolution_prefix'),body,
        'Actual first/last-factor grid construction and finite Fubini prove F*(H*G)=H*(F*G) at every positive in-domain index; neither a pair permutation nor a rearrangement oracle is supplied.'),)


def make_dirichlet_fubini_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (_entry_rows(spec)+_flat_rows(spec)+_prefix_rows(spec)+_grid_rows(spec)+_factor_rows(spec)
            +_physical_rows(spec)+_row_sum_rows(spec)+_nested_prefix_rows(spec)+_interchange_rows(spec))


__all__=['signed_dirichlet_grid_entry_relation','signed_dirichlet_grid_table_relation',
         'signed_dirichlet_flat_entry_relation','signed_dirichlet_flat_prefix_relation','signed_dirichlet_factor_row_relation',
         'make_dirichlet_fubini_candidate_theorems']
