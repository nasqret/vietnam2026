"""Scratch actual signed outer-product tables and product-of-sums proofs.

The new graph contains only valid packed beta tables and the actual signed
entry products at n*i+j, i<m and j<n. Its separately certified endpoint m*n
is unused. No sum identity, constructor or uniqueness law is a definition.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.arithmetic_table_extension_candidate import _extension
from peano_lab.library.divisor_sum_table_candidate import _signed_sum, _table, _table_at, _table_equal
from peano_lab.library.prime_valuation_support_candidate import (
    _and, _call, _cases, _intro, _le, _lt, _part, _parts, _public, _rewrite,
)
from peano_lab.library.signed_rectangular_slice_candidate import _index as _affine, _slice, _slice_sum
from peano_lab.library.signed_rectangular_sums_candidate import _rect_sum, _row_sums
from peano_lab.library.signed_table_operations_candidate import _mul_code, _scalar
from peano_lab.library.signed_block_sum_candidate import _iff


def _index(n: str, i: str, j: str) -> str:
    return f'(({n})*({i})+({j}))'


def _product(F: str, G: str, T: str, m: str, n: str, tag: str) -> str:
    i,j,a,b,c = ('scp_'+role+'_'+tag for role in ('row','column','first','second','value'))
    entries = (f'forall {i} {j} {a} {b} {c}. ({_lt(i,m,tag+"rows")}) -> '
               f'({_lt(j,n,tag+"columns")}) -> ({_table_at(F,i,a,tag+"first")}) -> '
               f'({_table_at(G,j,b,tag+"second")}) -> ({_table_at(T,_index(n,i,j),c,tag+"entry")}) -> '
               f'({_mul_code(a,b,c,tag+"multiply")})')
    return _and(_table('0',F,tag+'F'),_table('0',G,tag+'G'),
                _table(f'({m})*({n})',T,tag+'T'),entries)


def signed_cartesian_product_relation(
    F: str, G: str, T: str, m: str, n: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """Actual canonical signed products T[n*i+j]=F[i]*G[j], i<m,j<n."""
    return _public(_product,(F,G,T,m,n),tag=tag,variables=variables)


def _flat_entry(F: str, G: str, n: str, k: str, z: str, tag: str) -> str:
    i,j,a,b = ('scp_flat_'+role+'_'+tag for role in ('row','column','first','second'))
    return f'exists {i} {j} {a} {b}. '+_and(f'({k})={_index(n,i,j)}',
        _lt(j,n,tag+'remainder'),_table_at(F,i,a,tag+'F'),_table_at(G,j,b,tag+'G'),_mul_code(a,b,z,tag+'value'))


def _flat_prefix(F: str, G: str, n: str, l: str, T: str, tag: str) -> str:
    k,z = 'scp_flat_index_'+tag,'scp_flat_value_'+tag
    return _and(_table(l,T,tag+'table'),f'forall {k} {z}. ({_le(k,l,tag+"bound")}) -> '
                f'({_table_at(T,k,z,tag+"entry")}) -> ({_flat_entry(F,G,n,k,z,tag+"product")})')


def _coordinates(m: str, n: str, k: str, tag: str) -> str:
    i,j = 'scp_coordinate_row_'+tag,'scp_coordinate_column_'+tag
    return f'exists {i} {j}. '+_and(f'({k})={_index(n,i,j)}',_lt(i,m,tag+'row'),_lt(j,n,tag+'column'))


def _flat_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    total = _intro('F','G','n','k','hF','hG','hn')
    total += (f"have hd : exists i j. {_and('k=n*i+j',_lt('j','n','flat_division'))}",)
    total += _call('division_remainder_exists','n','k') + ('exact hn',) + _cases('hd',2) + ('cases hd_witness_witness',)
    total += (f"have ha : exists a. ({_table_at('F','x','a','flat_first')})",)
    total += _call('signed_table_lookup_any','0','F','x') + ('exact hF','cases ha',)
    total += (f"have hb : exists b. ({_table_at('G','x1','b','flat_second')})",)
    total += _call('signed_table_lookup_any','0','G','x1') + ('exact hG','cases hb',)
    total += (f"have hz : exists z. ({_mul_code('x2','x3','z','flat_product')})",)
    total += _call('signed_mul_total','x2','x3') + ('cases hz','exists x4','exists x','exists x1','exists x2','exists x3',
             'split','exact hd_witness_witness_left','split','exact hd_witness_witness_right',
             'split','exact ha_witness','split','exact hb_witness','exact hz_witness')

    read = _intro('F','G','n','i','j','a','b','z','hj','ha','hb','hv') + _cases('hv',4)
    p = 'hv'+'_witness'*4
    read += _parts(p,5) + ('have hcoord : x=i /\\ x1=j',)
    read += _call('division_remainder_unique','n',_index('n','i','j'),'x','x1','i','j')
    read += ('exact '+_part(p,5,0),'exact '+_part(p,5,1),'refl','exact hj','cases hcoord')
    read += _rewrite('hcoord_left',_table_at('F','x','x2','flat_read_row'),'x',_part(p,5,2))
    read += _rewrite('hcoord_right',_table_at('G','x1','x3','flat_read_column'),'x1',_part(p,5,3))
    read += ('have hfirst : x2=a',) + _call('divisor_signed_table_at_functional','F','i','x2','a')
    read += ('exact '+_part(p,5,2),'exact ha','have hsecond : x3=b')
    read += _call('divisor_signed_table_at_functional','G','j','x3','b') + ('exact '+_part(p,5,3),'exact hb')
    read += _rewrite('hfirst',_mul_code('x2','x3','z','flat_read_first'),'x2',_part(p,5,4))
    read += _rewrite('hsecond',_mul_code('a','x3','z','flat_read_second'),'x3',_part(p,5,4)) + ('exact '+_part(p,5,4),)
    return (
        spec('signed_cartesian_flat_entry_exists',
             f"forall F G n k. ({_table('0','F','flat_exists_F')}) -> ({_table('0','G','flat_exists_G')}) -> ~(n=0) -> "
             f"exists z. ({_flat_entry('F','G','n','k','z','flat_exists_result')})",
             ('division_remainder_exists','signed_table_lookup_any','signed_mul_total'), total,
             'For positive physical width, actual quotient/remainder and actual signed lookups construct each flattened product value.'),
        spec('signed_cartesian_flat_entry_lookup',
             f"forall F G n i j a b z. ({_lt('j','n','flat_lookup_bound')}) -> ({_table_at('F','i','a','flat_lookup_F')}) -> "
             f"({_table_at('G','j','b','flat_lookup_G')}) -> ({_flat_entry('F','G','n',_index('n','i','j'),'z','flat_lookup_entry')}) -> "
             f"({_mul_code('a','b','z','flat_lookup_result')})",
             ('division_remainder_unique','divisor_signed_table_at_functional'), read,
             'Unique bounded remainder coordinates and signed lookup functionality recover the actual prescribed cell product.'),
    )


def _prefix_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    base = _intro('F','G','n','T','z','hT','hz','hv') + ('split','exact hT') + _intro('i','u','hi','hu')
    base += ('have hi0 : i=0',) + _call('le_zero','i') + ('exact hi',)
    base += _rewrite('hi0',_table_at('T','i','u','base_lookup'),'i','hu')
    base += ('have heq : z=u',) + _call('divisor_signed_table_at_functional','T','0','z','u') + ('exact hz','exact hu')
    base += _rewrite('heq',_flat_entry('F','G','n','0','z','base_value'),'z','hv')
    base += _rewrite('hi0',_flat_entry('F','G','n','i','u','base_target'),'i') + ('exact hv',)

    append = _intro('F','G','n','l','T','z','ht','hz') + ('cases ht',)
    append += (f"have hx : exists U. ({_extension('T','U','S l','z','prefix_append_actual')})",)
    append += _call('arithmetic_signed_table_append','l','T','z') + ('exact ht_left','cases hx') + _parts('hx_witness',3)
    append += ('exists x','split','split','exact hx_witness_left') + _intro('i','u','hi','hu')
    append += (f"have hc : i=S l \\/ ({_lt('i','S l','prefix_append_cases')})",)
    append += _call('le_eq_or_lt','i','S l') + ('exact hi','cases hc')
    append += _rewrite('hc_left',_table_at('x','i','u','prefix_append_last'),'i','hu')
    append += ('have heq : z=u',) + _call('divisor_signed_table_at_functional','x','S l','z','u')
    append += ('exact hx_witness_right_right','exact hu')
    append += _rewrite('heq',_flat_entry('F','G','n','S l','z','prefix_append_value'),'z','hz')
    append += _rewrite('hc_left',_flat_entry('F','G','n','i','u','prefix_append_target'),'i') + ('exact hz',)
    append += (f"have hib : {_le('i','l','prefix_append_old_bound')}",)
    append += _call('le_of_succ_le_succ','i','l') + ('exact hc_right',)
    append += (f"have hv : exists v. ({_table_at('T','i','v','prefix_append_old_value')})",)
    append += _call('divisor_signed_table_lookup','l','T','i') + ('exact ht_left','exact hib','cases hv','have heq : x1=u')
    append += _call('hx_witness_right_left','i','x1','u') + ('exact hc_right','exact hv_witness','exact hu')
    append += _rewrite('heq',_table_at('T','i','x1','prefix_append_old_transport'),'x1','hv_witness')
    append += _call('ht_right','i','u') + ('exact hib','exact hv_witness','exact hx_witness_right_left')

    exists = _intro('F','G','n','l') + ('induction l',) + _intro('hF','hG','hn')
    exists += (f"have hv : exists z. ({_flat_entry('F','G','n','0','z','prefix_base_value')})",)
    exists += _call('signed_cartesian_flat_entry_exists','F','G','n','0') + ('exact hF','exact hG','exact hn','cases hv')
    exists += (f"have ht : exists T. ({_and(_table('0','T','prefix_base_table'),_table_at('T','0','x','prefix_base_entry'))})",)
    exists += _call('arithmetic_signed_table_singleton','x') + ('cases ht','cases ht_witness','exists x1')
    exists += _call('signed_cartesian_flat_prefix_zero','F','G','n','x1','x')
    exists += ('exact ht_witness_left','exact ht_witness_right','exact hv_witness')
    exists += _intro('hF','hG','hn') + (f"have hp : exists T. ({_flat_prefix('F','G','n','l','T','prefix_previous')})",'apply IH')
    exists += ('exact hF','exact hG','exact hn','cases hp',f"have hv : exists z. ({_flat_entry('F','G','n','S l','z','prefix_next_value')})")
    exists += _call('signed_cartesian_flat_entry_exists','F','G','n','S l') + ('exact hF','exact hG','exact hn','cases hv')
    exists += (f"have he : exists U. ({_and(_flat_prefix('F','G','n','S l','U','prefix_next'),_table_equal('x','U','S l','prefix_preserved'))})",)
    exists += _call('signed_cartesian_flat_prefix_append','F','G','n','l','x','x1')
    exists += ('exact hp_witness','exact hv_witness','cases he','cases he_witness','exists x2','exact he_witness_left')
    return (
        spec('signed_cartesian_flat_prefix_zero',
             f"forall F G n T z. ({_table('0','T','prefix_zero_table')}) -> ({_table_at('T','0','z','prefix_zero_entry')}) -> "
             f"({_flat_entry('F','G','n','0','z','prefix_zero_value')}) -> ({_flat_prefix('F','G','n','0','T','prefix_zero_result')})",
             ('le_zero','divisor_signed_table_at_functional'), base,
             'A real singleton and actual flat product provide the inclusive base prefix.'),
        spec('signed_cartesian_flat_prefix_append',
             f"forall F G n l T z. ({_flat_prefix('F','G','n','l','T','prefix_append_before')}) -> "
             f"({_flat_entry('F','G','n','S l','z','prefix_append_value')}) -> exists U. "
             + _and(_flat_prefix('F','G','n','S l','U','prefix_append_after'),_table_equal('T','U','S l','prefix_append_equal')),
             ('arithmetic_signed_table_append','le_eq_or_lt','le_of_succ_le_succ','divisor_signed_table_at_functional','divisor_signed_table_lookup'), append,
             'Actually recode both beta streams, preserve the old represented values, and install the next independently constructed flat product.'),
        spec('signed_cartesian_flat_prefix_exists',
             f"forall F G n l. ({_table('0','F','prefix_exists_F')}) -> ({_table('0','G','prefix_exists_G')}) -> ~(n=0) -> "
             f"exists T. ({_flat_prefix('F','G','n','l','T','prefix_exists_result')})",
             ('signed_cartesian_flat_entry_exists','arithmetic_signed_table_singleton','signed_cartesian_flat_prefix_zero','signed_cartesian_flat_prefix_append'), exists,
             'Ordinary induction constructs the entire actual finite flattened product prefix; no finite-choice or output-table oracle is supplied.'),
    )


def _cell_bound(m: str, n: str, i: str, j: str, row_hyp: str, column_hyp: str) -> tuple[str,...]:
    """Proof commands, not a new scalar theorem or a hidden operation law."""
    return (f'have hindex_comm : ({n})*({i})=({i})*({n})','apply mul_comm','rewrite hindex_comm') + \
        _call('matrix_integer_rectangular_index_bound',m,n,i,j) + ('exact '+row_hyp,'exact '+column_hyp)


def _constructor_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    from_flat = _intro('F','G','T','m','n','hF','hG','hp') + ('cases hp','split','exact hF','split','exact hG','split','exact hp_left')
    from_flat += _intro('i','j','a','b','c','hi','hj','ha','hb','hc')
    from_flat += _call('signed_cartesian_flat_entry_lookup','F','G','n','i','j','a','b','c') + ('exact hj','exact ha','exact hb')
    from_flat += _call('hp_right',_index('n','i','j'),'c')
    from_flat += _call('lt_to_le',_index('n','i','j'),'m*n') + _cell_bound('m','n','i','j','hi','hj') + ('exact hc',)

    empty = _intro('F','G','T','m','hF','hG','hT') + ('split','exact hF','split','exact hG','split')
    empty += _call('signed_table_domain_resize','0','m*0','T') + ('exact hT',)
    empty += _intro('i','j','a','b','c','hi','hj','ha','hb','hc') + ('exfalso','cases hj')
    empty += _call('succ_ne_zero','j') + _call('add_eq_zero_right','x','S j') + ('exact hj_witness',)

    exists = _intro('F','G','m','n','hF','hG') + ('have hn : n=0 \\/ ~(n=0)',) + _call('eq_decidable','n','0') + ('cases hn',)
    exists += _rewrite('hn_left',_product('F','G','T','m','n','construct_empty'),'n')
    exists += (f"have ht : exists T. ({_and(_table('0','T','construct_zero_table'),_table_at('T','0','0','construct_zero_entry'))})",)
    exists += _call('arithmetic_signed_table_singleton','0') + ('cases ht','cases ht_witness','exists x')
    exists += _call('signed_cartesian_product_empty_columns','F','G','x','m') + ('exact hF','exact hG','exact ht_witness_left')
    exists += (f"have hp : exists T. ({_flat_prefix('F','G','n','m*n','T','construct_flat')})",)
    exists += _call('signed_cartesian_flat_prefix_exists','F','G','n','m*n') + ('exact hF','exact hG','exact hn_right','cases hp','exists x')
    exists += _call('signed_cartesian_product_from_flat_prefix','F','G','x','m','n') + ('exact hF','exact hG','exact hp_witness')
    return (
        spec('signed_cartesian_product_from_flat_prefix',
             f"forall F G T m n. ({_table('0','F','from_flat_F')}) -> ({_table('0','G','from_flat_G')}) -> "
             f"({_flat_prefix('F','G','n','m*n','T','from_flat_input')}) -> ({_product('F','G','T','m','n','from_flat_result')})",
             ('signed_cartesian_flat_entry_lookup','lt_to_le','mul_comm','matrix_integer_rectangular_index_bound'), from_flat,
             'The actual finite flat construction supplies every in-range row-major product by proved index bounds and unique decoding.'),
        spec('signed_cartesian_product_empty_columns',
             f"forall F G T m. ({_table('0','F','empty_F')}) -> ({_table('0','G','empty_G')}) -> "
             f"({_table('0','T','empty_T')}) -> ({_product('F','G','T','m','0','empty_result')})",
             ('signed_table_domain_resize','succ_ne_zero','add_eq_zero_right'), empty,
             'A zero-column rectangle has no constrained cell, but all three table packings remain genuine.'),
        spec('signed_cartesian_product_exists',
             f"forall F G m n. ({_table('0','F','exists_F')}) -> ({_table('0','G','exists_G')}) -> "
             f"exists T. ({_product('F','G','T','m','n','exists_result')})",
             ('eq_decidable','arithmetic_signed_table_singleton','signed_cartesian_product_empty_columns',
              'signed_cartesian_flat_prefix_exists','signed_cartesian_product_from_flat_prefix'), exists,
             'Construct an actual finite signed outer-product beta table for arbitrary dimensions, explicitly including zero width and zero height.'),
    )


def _sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    offset = _affine('0','n','i')
    row = _intro('F','G','T','V','m','n','i','a','hp','hi','ha','hv') + _parts('hp',4) + _parts('hv',3)
    row += ('split',) + _call('signed_table_domain_resize','0','n','G') + ('exact hp_right_left','split','exact hv_right_left')
    row += _intro('j','hj') + (f"have hb : exists b. ({_table_at('G','j','b','row_first')})",)
    row += _call('signed_table_lookup_any','0','G','j') + ('exact hp_right_left','cases hb',)
    row += (f"have hc : exists c. ({_table_at('V','j','c','row_second')})",)
    row += _call('signed_table_lookup_any','n','V','j') + ('exact hv_right_left','cases hc','exists x','exists x1',
            'split','exact hb_witness','split','exact hc_witness')
    row += _call('hp_right_right_right','i','j','a','x','x1') + ('exact hi','exact hj','exact ha','exact hb_witness')
    row += (f"have ht : {_table_at('T',_affine(offset,'1','j'),'x1','row_source')}",)
    row += _call('signed_rectangular_slice_lookup','T','V',offset,'1','n','j','x1') + ('exact hv','exact hj','exact hc_witness')
    row += (f"have hindex : {_affine(offset,'1','j')} = {_index('n','i','j')}",'congr')
    row += _call('zero_add','n*i') + _call('one_mul','j')
    row += _rewrite('hindex',_table_at('T','coord','x1','row_rewrite'),'coord','ht') + ('exact ht',)

    row_value = _intro('F','G','T','m','n','i','a','b','c','hp','hi','ha','hb','hc') + ('cases hc','cases hc_witness')
    row_value += _call('signed_prefix_sum_scalar_multiply','n','a','G','x','b','c')
    row_value += _call('signed_cartesian_product_row_scalar','F','G','T','x','m','n','i','a')
    row_value += ('exact hp','exact hi','exact ha','exact hc_witness_left','exact hb','exact hc_witness_right')

    rows_scalar = _intro('F','G','T','R','m','n','b','hp','hb','hr') + _parts('hp',4) + _parts('hr',3)
    rows_scalar += ('split',) + _call('signed_table_domain_resize','0','m','F') + ('exact hp_left','split','exact hr_right_left')
    rows_scalar += _intro('i','hi') + (f"have ha : exists a. ({_table_at('F','i','a','rows_scalar_source')})",)
    rows_scalar += _call('signed_table_lookup_any','0','F','i') + ('exact hp_left','cases ha',)
    rows_scalar += (f"have hc : exists c. ({_table_at('R','i','c','rows_scalar_output')})",)
    rows_scalar += _call('signed_table_lookup_any','m','R','i') + ('exact hr_right_left','cases hc','exists x','exists x1',
                   'split','exact ha_witness','split','exact hc_witness')
    rows_scalar += _call('signed_mul_commutative','x','b','x1')
    rows_scalar += _call('signed_cartesian_product_row_sum','F','G','T','m','n','i','x','b','x1')
    rows_scalar += ('exact hp','exact hi','exact ha_witness','exact hb')
    rows_scalar += _call('signed_rectangular_row_sums_lookup','T','R','0','n','1','m','n','i','x1')
    rows_scalar += ('exact hr','exact hi','exact hc_witness')

    rectangular = _intro('F','G','T','m','n','a','b','c','hp','ha','hb','hc') + ('cases hc','cases hc_witness')
    rectangular += _call('signed_mul_commutative','b','a','c')
    rectangular += _call('signed_prefix_sum_scalar_multiply','m','b','F','x','a','c')
    rectangular += _call('signed_cartesian_product_row_sums_scalar','F','G','T','x','m','n','b')
    rectangular += ('exact hp','exact hb','exact hc_witness_left','exact ha','exact hc_witness_right')

    flat = _intro('F','G','T','m','n','a','b','c','hp','ha','hb','hc')
    flat += _call('signed_cartesian_product_rectangular_sum','F','G','T','m','n','a','b','c') + ('exact hp','exact ha','exact hb')
    hi = _iff(_signed_sum('T','m*n','c','product_flat_prefix'),_rect_sum('T','0','n','1','m','n','c','product_flat_rectangle'))
    flat += (f'have hi : {hi}',) + _call('signed_prefix_sum_row_major_iff','T','m','n','c')
    flat += _call('signed_table_domain_resize','m*n','0','T') + _parts('hp',4) + ('exact hp_right_right_left','cases hi','apply hi_left','exact hc')

    exists = _intro('F','G','m','n','hF','hG') + (f"have ht : exists T. ({_product('F','G','T','m','n','values_table')})",)
    exists += _call('signed_cartesian_product_exists','F','G','m','n') + ('exact hF','exact hG','cases ht')
    for table, length, name, hyp in (('F','m','ha','hF'),('G','n','hb','hG'),('x','m*n','hc','ht_witness_right_right_left')):
        exists += (f"have {name} : exists z. ({_signed_sum(table,length,'z','values_'+name)})",)
        exists += _call('arithmetic_signed_sum_exists','0' if table != 'x' else 'm*n',table,length)
        if table == 'x': exists += _parts('ht_witness',4)
        exists += ('exact '+hyp,'cases '+name)
    exists += ('exists x','exists x1','exists x2','exists x3','split','exact ht_witness','split','exact ha_witness',
               'split','exact hb_witness','split','exact hc_witness')
    exists += _call('signed_cartesian_product_prefix_sum','F','G','x','m','n','x1','x2','x3')
    exists += ('exact ht_witness','exact ha_witness','exact hb_witness','exact hc_witness')
    return (
        spec('signed_cartesian_product_row_scalar',
             f"forall F G T V m n i a. ({_product('F','G','T','m','n','row_product')}) -> ({_lt('i','m','row_bound')}) -> "
             f"({_table_at('F','i','a','row_scalar')}) -> ({_slice('T','V',offset,'1','n','row_slice')}) -> ({_scalar('a','G','V','n','row_result')})",
             ('signed_table_domain_resize','signed_table_lookup_any','signed_rectangular_slice_lookup','zero_add','one_mul'), row,
             'Each actual row slice is a genuine pointwise scalar product by its actual first-input value.'),
        spec('signed_cartesian_product_row_sum',
             f"forall F G T m n i a b c. ({_product('F','G','T','m','n','row_sum_product')}) -> ({_lt('i','m','row_sum_bound')}) -> "
             f"({_table_at('F','i','a','row_sum_entry')}) -> ({_signed_sum('G','n','b','row_sum_second')}) -> "
             f"({_slice_sum('T',offset,'1','n','c','row_sum_slice')}) -> ({_mul_code('a','b','c','row_sum_result')})",
             ('signed_prefix_sum_scalar_multiply','signed_cartesian_product_row_scalar'), row_value,
             'The actual sum of each product row is the signed product of its row scalar and the actual second-input sum.'),
        spec('signed_cartesian_product_row_sums_scalar',
             f"forall F G T R m n b. ({_product('F','G','T','m','n','row_sums_product')}) -> ({_signed_sum('G','n','b','row_sums_second')}) -> "
             f"({_row_sums('T','R','0','n','1','m','n','row_sums_actual')}) -> ({_scalar('b','F','R','m','row_sums_result')})",
             ('signed_table_domain_resize','signed_table_lookup_any','signed_mul_commutative','signed_cartesian_product_row_sum',
              'signed_rectangular_row_sums_lookup'), rows_scalar,
             'The genuinely constructed row-sum table is pointwise the first input multiplied by the actual second-input sum.'),
        spec('signed_cartesian_product_rectangular_sum',
             f"forall F G T m n a b c. ({_product('F','G','T','m','n','rect_product')}) -> ({_signed_sum('F','m','a','rect_first')}) -> "
             f"({_signed_sum('G','n','b','rect_second')}) -> ({_rect_sum('T','0','n','1','m','n','c','rect_total')}) -> "
             f"({_mul_code('a','b','c','rect_result')})",
             ('signed_mul_commutative','signed_prefix_sum_scalar_multiply','signed_cartesian_product_row_sums_scalar'), rectangular,
             'Two applications of actual signed scalar linearity prove that the rectangular outer-product total is the product of the two actual sums.'),
        spec('signed_cartesian_product_prefix_sum',
             f"forall F G T m n a b c. ({_product('F','G','T','m','n','product_prefix_table')}) -> ({_signed_sum('F','m','a','product_prefix_first')}) -> "
             f"({_signed_sum('G','n','b','product_prefix_second')}) -> ({_signed_sum('T','m*n','c','product_prefix_total')}) -> "
             f"({_mul_code('a','b','c','product_prefix_result')})",
             ('signed_cartesian_product_rectangular_sum','signed_prefix_sum_row_major_iff','signed_table_domain_resize'), flat,
             'The actual flattened product prefix sums to the canonical signed product, using the separately proved flattening bridge; both zero dimensions are included.'),
        spec('signed_cartesian_product_sums_exists',
             f"forall F G m n. ({_table('0','F','values_source_F')}) -> ({_table('0','G','values_source_G')}) -> exists T a b c. "
             + _and(_product('F','G','T','m','n','values_product'),_signed_sum('F','m','a','values_first'),
                    _signed_sum('G','n','b','values_second'),_signed_sum('T','m*n','c','values_total'),_mul_code('a','b','c','values_result')),
             ('signed_cartesian_product_exists','arithmetic_signed_sum_exists','signed_cartesian_product_prefix_sum'), exists,
             'Construct the actual outer-product table and all three signed sum traces, and prove their product relation without an assumed constructor or sum witness.'),
    )


def _representation_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    quotient = _intro('m','n','k','i','j','hk','hbound') + ('have hcase : ('+_le('m','i','quotient_case')+') \\/ ('+_lt('i','m','quotient_other')+')',)
    quotient += _call('le_or_lt','m','i') + ('cases hcase','exfalso',f"have hreverse : {_le('m*n','k','quotient_reverse')}",
                 'have hcomm : m*n=n*m','apply mul_comm','rewrite hcomm','rewrite hk')
    quotient += _call('le_trans','n*m','n*i','n*i+j') + _call('mul_le_mul_left','m','i','n') + ('exact hcase_left',)
    quotient += _call('le_add_right','n*i','j') + _call('lt_not_le','k','m*n') + ('exact hbound','exact hreverse','exact hcase_right')

    coordinates = _intro('m','n','k','hk') + ('have hn : ~(n=0)','intro hnzero','have hlength : m*n=0','rewrite hnzero','simp')
    coordinates += _rewrite('hlength',_lt('k','bound','coordinate_zero_bound'),'bound','hk')
    coordinates += _call('lt_not_le','k','0') + ('exact hk',) + _call('zero_le','k')
    coordinates += (f"have hd : exists i j. {_and('k=n*i+j',_lt('j','n','coordinate_division'))}",)
    coordinates += _call('division_remainder_exists','n','k') + ('exact hn',) + _cases('hd',2) + ('cases hd_witness_witness',)
    coordinates += ('exists x','exists x1','split','exact hd_witness_witness_left','split')
    coordinates += _call('signed_cartesian_quotient_row_bound','m','n','k','x','x1')
    coordinates += ('exact hd_witness_witness_left','exact hk','exact hd_witness_witness_right')

    flat_lookup = _intro('F','G','T','m','n','k','z','hp','hk','hz') + _parts('hp',4)
    flat_lookup += (f"have hd : {_coordinates('m','n','k','lookup_coordinates')}",)
    flat_lookup += _call('signed_cartesian_coordinates_exists','m','n','k') + ('exact hk',) + _cases('hd',2) + _parts('hd_witness_witness',3)
    flat_lookup += (f"have ha : exists a. ({_table_at('F','x','a','lookup_first')})",)
    flat_lookup += _call('signed_table_lookup_any','0','F','x') + ('exact hp_left','cases ha',)
    flat_lookup += (f"have hb : exists b. ({_table_at('G','x1','b','lookup_second')})",)
    flat_lookup += _call('signed_table_lookup_any','0','G','x1') + ('exact hp_right_left','cases hb',)
    flat_lookup += ('exists x','exists x1','exists x2','exists x3','split','exact hd_witness_witness_left',
                    'split','exact hd_witness_witness_right_left','split','exact hd_witness_witness_right_right',
                    'split','exact ha_witness','split','exact hb_witness')
    flat_lookup += _call('hp_right_right_right','x','x1','x2','x3','z')
    flat_lookup += ('exact hd_witness_witness_right_left','exact hd_witness_witness_right_right','exact ha_witness','exact hb_witness')
    flat_lookup += _rewrite('hd_witness_witness_left',_table_at('T','k','z','lookup_index'),'k','hz') + ('exact hz',)

    unique = _intro('F','G','T','U','m','n','hT','hU','k','a','b','hk','ha','hb') + _parts('hT',4) + _parts('hU',4)
    unique += (f"have hd : {_coordinates('m','n','k','unique_coordinates')}",)
    unique += _call('signed_cartesian_coordinates_exists','m','n','k') + ('exact hk',) + _cases('hd',2) + _parts('hd_witness_witness',3)
    unique += (f"have hf : exists z. ({_table_at('F','x','z','unique_first')})",)
    unique += _call('signed_table_lookup_any','0','F','x') + ('exact hT_left','cases hf',)
    unique += (f"have hg : exists z. ({_table_at('G','x1','z','unique_second')})",)
    unique += _call('signed_table_lookup_any','0','G','x1') + ('exact hT_right_left','cases hg',)
    unique += _rewrite('hd_witness_witness_left',_table_at('T','k','a','unique_first_index'),'k','ha')
    unique += _rewrite('hd_witness_witness_left',_table_at('U','k','b','unique_second_index'),'k','hb')
    unique += _call('signed_mul_functional','x2','x3','a','b')
    for name, value, hyp in (('hT','a','ha'),('hU','b','hb')):
        unique += _call(name+'_right_right_right','x','x1','x2','x3',value)
        unique += ('exact hd_witness_witness_right_left','exact hd_witness_witness_right_right','exact hf_witness','exact hg_witness','exact '+hyp)

    transport = _intro('F','G','T','U','m','n','hp','hU','he') + _parts('hp',4)
    transport += ('split','exact hp_left','split','exact hp_right_left','split')
    transport += _call('signed_table_domain_resize','0','m*n','U') + ('exact hU',)
    transport += _intro('i','j','a','b','c','hi','hj','ha','hb','hc')
    transport += (f"have ht : exists z. ({_table_at('T',_index('n','i','j'),'z','reencode_original')})",)
    transport += _call('signed_table_lookup_any','m*n','T',_index('n','i','j')) + ('exact hp_right_right_left','cases ht','have heq : x=c')
    transport += _call('he',_index('n','i','j'),'x','c') + _cell_bound('m','n','i','j','hi','hj') + ('exact ht_witness','exact hc')
    transport += _rewrite('heq',_table_at('T',_index('n','i','j'),'x','reencode_value'),'x','ht_witness')
    transport += _call('hp_right_right_right','i','j','a','b','c') + ('exact hi','exact hj','exact ha','exact hb','exact ht_witness')

    exists = _intro('F','G','m','n','hF','hG') + (f"have ht : exists T. ({_product('F','G','T','m','n','unique_construct')})",)
    exists += _call('signed_cartesian_product_exists','F','G','m','n') + ('exact hF','exact hG','cases ht','exists x','split','exact ht_witness')
    exists += _intro('U','hU') + _call('signed_cartesian_product_extensional_unique','F','G','x','U','m','n') + ('exact ht_witness','exact hU')
    return (
        spec('signed_cartesian_quotient_row_bound',
             f"forall m n k i j. k=n*i+j -> ({_lt('k','m*n','quotient_source')}) -> ({_lt('i','m','quotient_result')})",
             ('le_or_lt','mul_comm','le_trans','mul_le_mul_left','le_add_right','lt_not_le'), quotient,
             'An actual flattened index below a rectangular area has its quotient row below the height, including vacuous zero-area cases.'),
        spec('signed_cartesian_coordinates_exists',
             f"forall m n k. ({_lt('k','m*n','coordinate_source')}) -> ({_coordinates('m','n','k','coordinate_result')})",
             ('lt_not_le','zero_le','division_remainder_exists','signed_cartesian_quotient_row_bound'), coordinates,
             'Every actual index in a finite rectangular window has constructed bounded row and column coordinates, with no positive-width assumption supplied.'),
        spec('signed_cartesian_product_flat_lookup',
             f"forall F G T m n k z. ({_product('F','G','T','m','n','lookup_product')}) -> ({_lt('k','m*n','lookup_bound')}) -> "
             f"({_table_at('T','k','z','lookup_value')}) -> exists d e a b. "
             + _and('k=n*d+e',_lt('d','m','lookup_row'),_lt('e','n','lookup_column'),
                    _table_at('F','d','a','lookup_F'),_table_at('G','e','b','lookup_G'),_mul_code('a','b','z','lookup_result')),
             ('signed_cartesian_coordinates_exists','signed_table_lookup_any'), flat_lookup,
             'An actual in-range product-table lookup supplies real bounded coordinates, both actual source values and their genuine signed product.'),
        spec('signed_cartesian_product_extensional_unique',
             f"forall F G T U m n. ({_product('F','G','T','m','n','unique_first')}) -> ({_product('F','G','U','m','n','unique_second')}) -> "
             f"({_table_equal('T','U','m*n','unique_result')})",
             ('signed_cartesian_coordinates_exists','signed_table_lookup_any','signed_mul_functional'), unique,
             'Every in-range flat index has actual bounded row and column coordinates, so all outer-product encodings represent the same signed value there.'),
        spec('signed_cartesian_product_reencode',
             f"forall F G T U m n. ({_product('F','G','T','m','n','reencode_source')}) -> ({_table('0','U','reencode_valid')}) -> "
             f"({_table_equal('T','U','m*n','reencode_preserved')}) -> ({_product('F','G','U','m','n','reencode_result')})",
             ('signed_table_domain_resize','signed_table_lookup_any','mul_comm','matrix_integer_rectangular_index_bound'), transport,
             'Any real recoding preserving precisely the flattened product window remains the same outer product; the unused endpoint may change.'),
        spec('signed_cartesian_product_exists_extensionally_unique',
             f"forall F G m n. ({_table('0','F','unique_exists_F')}) -> ({_table('0','G','unique_exists_G')}) -> exists T. "
             + _and(_product('F','G','T','m','n','unique_exists_table'),
                    f"forall U. ({_product('F','G','U','m','n','unique_exists_other')}) -> ({_table_equal('T','U','m*n','unique_exists_equal')})"),
             ('signed_cartesian_product_exists','signed_cartesian_product_extensional_unique'), exists,
             'Construct the actual outer product and prove value uniqueness on its exact strict finite window, without asserting uniqueness of beta codes.'),
    )


def make_signed_cartesian_product_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _flat_rows(spec) + _prefix_rows(spec) + _constructor_rows(spec) + _sum_rows(spec) + _representation_rows(spec)


__all__ = ['signed_cartesian_product_relation','make_signed_cartesian_product_candidate_theorems']
