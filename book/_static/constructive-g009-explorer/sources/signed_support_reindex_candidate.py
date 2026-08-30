"""Scratch ordinary-HA support reindexing via an actually constructed incidence.

Native beta codes map natural indices. Only nonzero represented signed values
must have bounded, injective, value-preserving images and actual preimages.
The independently defined incidence has no sum equation or choice oracle.
Nothing in this scratch factory enrolls a theorem or changes a frozen source.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.divisor_sum_table_candidate import _signed_sum, _table, _table_at, _table_equal
from peano_lab.library.prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _intro, _le, _lt, _part, _parts, _public, _rewrite,
)
from peano_lab.library.signed_finite_support_candidate import _zero_window
from peano_lab.library.signed_rectangular_slice_candidate import _index, _slice, _slice_sum
from peano_lab.library.signed_rectangular_sums_candidate import _fubini_data, _row_sums


def _preserve(A: str, B: str, r: str, s: str, L: str, M: str, tag: str) -> str:
    i, a, j = ('ssr_' + role + '_' + tag for role in ('source', 'value', 'target'))
    return (f'forall {i} {a}. ({_lt(i,L,tag+"source_bound")}) -> '
            f'({_table_at(A,i,a,tag+"source_value")}) -> ~({a}=0) -> exists {j}. '
            + _and(_at(r,s,i,j,tag+'map'), _lt(j,M,tag+'target_bound'),
                   _table_at(B,j,a,tag+'target_value')))


def _injective(A: str, r: str, s: str, L: str, tag: str) -> str:
    i, k, j, a, b = ('ssr_' + role + '_' + tag for role in ('first', 'second', 'image', 'a', 'b'))
    return (f'forall {i} {k} {j} {a} {b}. ({_lt(i,L,tag+"first_bound")}) -> '
            f'({_lt(k,L,tag+"second_bound")}) -> ({_table_at(A,i,a,tag+"first_value")}) -> ~({a}=0) -> '
            f'({_table_at(A,k,b,tag+"second_value")}) -> ~({b}=0) -> '
            f'({_at(r,s,i,j,tag+"first_map")}) -> ({_at(r,s,k,j,tag+"second_map")}) -> {i}={k}')


def _cover(A: str, B: str, r: str, s: str, L: str, M: str, tag: str) -> str:
    j, b, i = ('ssr_' + role + '_' + tag for role in ('target', 'value', 'source'))
    return (f'forall {j} {b}. ({_lt(j,M,tag+"target_bound")}) -> '
            f'({_table_at(B,j,b,tag+"target_value")}) -> ~({b}=0) -> exists {i}. '
            + _and(_lt(i,L,tag+'source_bound'), _at(r,s,i,j,tag+'map'),
                   _table_at(A,i,b,tag+'source_value')))


def _reindex(A: str, B: str, r: str, s: str, L: str, M: str, tag: str) -> str:
    return _and(_table('0',A,tag+'source_table'), _table('0',B,tag+'target_table'),
                _preserve(A,B,r,s,L,M,tag+'preserve'), _injective(A,r,s,L,tag+'injective'),
                _cover(A,B,r,s,L,M,tag+'cover'))


def _choice(j: str, k: str, z: str, a: str) -> str:
    return f'({_and(f"({j})=({k})",f"({z})=({a})")}) \\/ ({_and(f"~(({j})=({k}))",f"({z})=0")})'


def _entry(A: str, r: str, s: str, i: str, j: str, z: str, tag: str) -> str:
    a, k = 'ssr_entry_value_' + tag, 'ssr_entry_image_' + tag
    return f'exists {a} {k}. ' + _and(_table_at(A,i,a,tag+'source'),
        _at(r,s,i,k,tag+'map'), _choice(j,k,z,a))


def _flat_index(M: str, i: str, j: str) -> str:
    return f'((S ({M}))*({i})+({j}))'


def _flat_entry(A: str, r: str, s: str, M: str, k: str, z: str, tag: str) -> str:
    i, j = 'ssr_flat_row_' + tag, 'ssr_flat_column_' + tag
    return f'exists {i} {j}. ' + _and(f'({k})=({_flat_index(M,i,j)})',
        _lt(j,f'S ({M})',tag+'remainder'), _entry(A,r,s,i,j,z,tag+'entry'))


def _flat_prefix(A: str, r: str, s: str, M: str, l: str, T: str, tag: str) -> str:
    k, z = 'ssr_prefix_index_' + tag, 'ssr_prefix_value_' + tag
    return _and(_table(l,T,tag+'table'),
        f'forall {k} {z}. ({_le(k,l,tag+"bound")}) -> ({_table_at(T,k,z,tag+"lookup")}) -> '
        f'({_flat_entry(A,r,s,M,k,z,tag+"entry")})')


def _incidence(A: str, r: str, s: str, L: str, M: str, T: str, tag: str) -> str:
    i, j, z = ('ssr_grid_' + role + '_' + tag for role in ('row', 'column', 'value'))
    return _and(_table('0',A,tag+'source'), _table(f'({L})*(S ({M}))',T,tag+'table'),
        f'forall {i} {j} {z}. ({_lt(i,L,tag+"row_bound")}) -> ({_lt(j,M,tag+"column_bound")}) -> '
        f'({_table_at(T,_flat_index(M,i,j),z,tag+"lookup")}) -> ({_entry(A,r,s,i,j,z,tag+"entry")})')


def _off_spike(F: str, l: str, p: str, tag: str) -> str:
    i, z = 'ssr_spike_index_' + tag, 'ssr_spike_value_' + tag
    return (f'forall {i} {z}. ({_lt(i,l,tag+"bound")}) -> ~({i}=({p})) -> '
            f'({_table_at(F,i,z,tag+"entry")}) -> {z}=0')


def signed_support_reindex_relation(A: str, B: str, r: str, s: str, L: str, M: str,
                                    *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual beta map bijects nonzero represented values, not whole windows."""
    return _public(_reindex,(A,B,r,s,L,M),tag=tag,variables=variables)


def signed_support_incidence_entry_relation(A: str, r: str, s: str, i: str, j: str, z: str,
                                            *, tag: str, variables: tuple[str, ...]) -> str:
    """A cell is the actual source value at its beta image and zero elsewhere."""
    return _public(_entry,(A,r,s,i,j,z),tag=tag,variables=variables)


def signed_support_incidence_flat_entry_relation(A: str, r: str, s: str, M: str, k: str, z: str,
                                                 *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual quotient/remainder by S M, followed by an actual incidence cell."""
    return _public(_flat_entry,(A,r,s,M,k,z),tag=tag,variables=variables)


def signed_support_incidence_flat_prefix_relation(A: str, r: str, s: str, M: str, l: str, T: str,
                                                  *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual inclusive signed prefix encoding of incidence cells, through l."""
    return _public(_flat_prefix,(A,r,s,M,l,T),tag=tag,variables=variables)


def signed_support_incidence_relation(A: str, r: str, s: str, L: str, M: str, T: str,
                                      *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual L-by-M incidence at stride S M; padding and endpoint are unused."""
    return _public(_incidence,(A,r,s,L,M,T),tag=tag,variables=variables)


def _spike_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    value=_intro('F','l','p','a','z','hF','hp','hz0','ha','hz1','hs')
    value+=(f'have hshort : exists u. ({_signed_sum("F","S p","u","spike_short")})',)
    value+=_call('arithmetic_signed_sum_exists','0','F','S p')+('exact hF','cases hshort','have hvalue : x=a')
    value+=_call('signed_prefix_sum_last_value','F','p','a','x')+('exact hz0','exact ha','exact hshort_witness')
    value+=('have hequal : x=z',)+_call('signed_prefix_sum_zero_tail','F','S p','l','x','z')
    value+=('exact hp','exact hz1','exact hshort_witness','exact hs','trans x','symm','exact hequal','exact hvalue')

    exists=_intro('F','l','p','a','hF','hp','hz0','ha','hz1')
    exists+=(f'have hs : exists z. ({_signed_sum("F","l","z","spike_actual_sum")})',)
    exists+=_call('arithmetic_signed_sum_exists','0','F','l')+('exact hF','cases hs','have heq : x=a')
    exists+=_call('signed_prefix_sum_single_spike_value','F','l','p','a','x')
    exists+=('exact hF','exact hp','exact hz0','exact ha','exact hz1','exact hs_witness')
    exists+=_rewrite('heq',_signed_sum('F','l','x','spike_exists_rewrite'),'x','hs_witness')+('exact hs_witness',)

    point=_intro('F','l','p','a','z','hF','hp','ha','hoff','hs')
    point+=_call('signed_prefix_sum_single_spike_value','F','l','p','a','z')+('exact hF','exact hp')
    point+=_intro('i','u','h0i','hip','hi')+_call('hoff','i','u')
    point+=_call('lt_trans','i','p','l')+('exact hip','exact hp','intro heq')
    point+=_rewrite('heq',_lt('i','p','point_left_rewrite'),'i','hip')
    point+=_call('lt_irrefl_expanded','p')+('exact hip','exact hi','exact ha')
    point+=_intro('i','u','hpi','hil','hi')+_call('hoff','i','u')+('exact hil','intro heq')
    point+=_rewrite('heq',_le('S p','i','point_right_rewrite'),'i','hpi')
    point+=_call('lt_irrefl_expanded','p')+('exact hpi','exact hi','exact hs')
    return (
        spec('signed_prefix_sum_single_spike_value',
             f'forall F l p a z. ({_table("0","F","spike_table")}) -> ({_lt("p","l","spike_bound")}) -> '
             f'({_zero_window("F","0","p","spike_before")}) -> ({_table_at("F","p","a","spike_value")}) -> '
             f'({_zero_window("F","S p","l","spike_after")}) -> ({_signed_sum("F","l","z","spike_sum")}) -> z=a',
             ('arithmetic_signed_sum_exists','signed_prefix_sum_last_value','signed_prefix_sum_zero_tail'),value,
             'An actual signed sum with one arbitrary-position entry and proved zero windows has exactly that entry value.'),
        spec('signed_prefix_sum_single_spike_exists',
             f'forall F l p a. ({_table("0","F","spike_exists_table")}) -> ({_lt("p","l","spike_exists_bound")}) -> '
             f'({_zero_window("F","0","p","spike_exists_before")}) -> ({_table_at("F","p","a","spike_exists_value")}) -> '
             f'({_zero_window("F","S p","l","spike_exists_after")}) -> ({_signed_sum("F","l","a","spike_exists_sum")})',
             ('arithmetic_signed_sum_exists','signed_prefix_sum_single_spike_value'),exists,
             'Construct actual fold traces for an arbitrary-position signed spike, including zero and negative values.'),
        spec('signed_prefix_sum_point_spike_value',
             f'forall F l p a z. ({_table("0","F","point_table")}) -> ({_lt("p","l","point_bound")}) -> '
             f'({_table_at("F","p","a","point_value")}) -> ({_off_spike("F","l","p","point_other")}) -> '
             f'({_signed_sum("F","l","z","point_sum")}) -> z=a',
             ('signed_prefix_sum_single_spike_value','lt_trans','lt_irrefl_expanded'),point,
             'Pointwise zero values away from one actual bounded index imply the two zero windows needed for the spike sum.'),
    )


def _entry_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    hit=_intro('A','r','s','i','j','a','ha','hm')+('exists a','exists j','split','exact ha',
        'split','exact hm','left','split','refl','refl')
    miss=_intro('A','r','s','i','j','k','a','ha','hm','hne')+('exists a','exists k','split','exact ha',
        'split','exact hm','right','split','exact hne','refl')

    decode=_intro('A','r','s','i','j','a','k','z','ha','hm','he')+_cases('he',2)+_parts('he_witness_witness',3)
    decode+=('have hvalue : x=a',)+_call('divisor_signed_table_at_functional','A','i','x','a')
    decode+=('exact he_witness_witness_left','exact ha','have himage : x1=k')
    decode+=_call('beta_at_unique','r','s','i','x1','k')+('exact he_witness_witness_right_left','exact hm')
    decode+=_rewrite('hvalue',_choice('j','x1','z','x'),'x','he_witness_witness_right_right')
    decode+=_rewrite('himage',_choice('j','x1','z','a'),'x1','he_witness_witness_right_right')
    decode+=('exact he_witness_witness_right_right',)

    functional=_intro('A','r','s','i','j','z','w','hz','hw')+_cases('hz',2)+_parts('hz_witness_witness',3)
    functional+=(f'have hd : {_choice("j","x1","w","x")}',)
    functional+=_call('signed_support_incidence_entry_decode','A','r','s','i','j','x','x1','w')
    functional+=('exact hz_witness_witness_left','exact hz_witness_witness_right_left','exact hw',
        'cases hz_witness_witness_right_right','cases hz_witness_witness_right_right_left','cases hd',
        'cases hd_left','trans x','exact hz_witness_witness_right_right_left_right','symm','exact hd_left_right',
        'cases hd_right','exfalso','apply hd_right_left','exact hz_witness_witness_right_right_left_left',
        'cases hz_witness_witness_right_right_right','cases hd','cases hd_left','exfalso',
        'apply hz_witness_witness_right_right_right_left','exact hd_left_left','cases hd_right',
        'trans 0','exact hz_witness_witness_right_right_right_right','symm','exact hd_right_right')

    total=_intro('A','r','s','i','j','hA')+(f'have ha : exists a. ({_table_at("A","i","a","entry_actual_source")})',)
    total+=_call('signed_table_lookup_any','0','A','i')+('exact hA','cases ha')
    total+=(f'have hm : exists k. ({_at("r","s","i","k","entry_actual_map")})',)
    total+=_call('beta_at_exists','r','s','i')+('cases hm','have hc : j=x1 \\/ ~(j=x1)')
    total+=_call('eq_decidable','j','x1')+('cases hc','exists x')
    total+=_rewrite('hc_left',_entry('A','r','s','i','j','x','entry_total_hit'),'j')
    total+=_call('signed_support_incidence_entry_hit','A','r','s','i','x1','x')+('exact ha_witness','exact hm_witness','exists 0')
    total+=_call('signed_support_incidence_entry_miss','A','r','s','i','j','x1','x')+('exact ha_witness','exact hm_witness','exact hc_right')

    zero=_intro('A','r','s','i','j','z','ha','he')+_cases('he',2)+_parts('he_witness_witness',3)
    zero+=('have hv : x=0',)+_call('divisor_signed_table_at_functional','A','i','x','0')
    zero+=('exact he_witness_witness_left','exact ha','cases he_witness_witness_right_right',
        'cases he_witness_witness_right_right_left','trans x','exact he_witness_witness_right_right_left_right','exact hv',
        'cases he_witness_witness_right_right_right','exact he_witness_witness_right_right_right_right')

    nonzero=_intro('A','r','s','i','j','z','he','hnz')+_cases('he',2)+_parts('he_witness_witness',3)
    nonzero+=('cases he_witness_witness_right_right','cases he_witness_witness_right_right_left','split')
    nonzero+=_rewrite('he_witness_witness_right_right_left_right',_table_at('A','i','z','nonzero_value_rewrite'),'z')
    nonzero+=('exact he_witness_witness_left',)
    nonzero+=_rewrite('he_witness_witness_right_right_left_left',_at('r','s','i','j','nonzero_map_rewrite'),'j')
    nonzero+=('exact he_witness_witness_right_left','cases he_witness_witness_right_right_right',
              'exfalso','apply hnz','exact he_witness_witness_right_right_right_right')
    return (
        spec('signed_support_incidence_entry_hit',
             f'forall A r s i j a. ({_table_at("A","i","a","hit_source")}) -> ({_at("r","s","i","j","hit_map")}) -> '
             f'({_entry("A","r","s","i","j","a","hit_entry")})',(),hit,
             'An actual source lookup and actual beta image supply the retained incidence cell.'),
        spec('signed_support_incidence_entry_miss',
             f'forall A r s i j k a. ({_table_at("A","i","a","miss_source")}) -> ({_at("r","s","i","k","miss_map")}) -> '
             f'~(j=k) -> ({_entry("A","r","s","i","j","0","miss_entry")})',(),miss,
             'An actual source lookup and beta image construct a zero cell at every different target index.'),
        spec('signed_support_incidence_entry_decode',
             f'forall A r s i j a k z. ({_table_at("A","i","a","decode_source")}) -> ({_at("r","s","i","k","decode_map")}) -> '
             f'({_entry("A","r","s","i","j","z","decode_entry")}) -> ({_choice("j","k","z","a")})',
             ('divisor_signed_table_at_functional','beta_at_unique'),decode,
             'Actual signed lookup and beta uniqueness recover the independently stated hit-or-zero cell cases.'),
        spec('signed_support_incidence_entry_functional',
             f'forall A r s i j z w. ({_entry("A","r","s","i","j","z","functional_first")}) -> '
             f'({_entry("A","r","s","i","j","w","functional_second")}) -> z=w',
             ('signed_support_incidence_entry_decode',),functional,
             'The actual incidence value is unique, independent of witnesses and component representations.'),
        spec('signed_support_incidence_entry_exists',
             f'forall A r s i j. ({_table("0","A","entry_source_table")}) -> exists z. '
             f'({_entry("A","r","s","i","j","z","entry_total")})',
             ('signed_table_lookup_any','beta_at_exists','eq_decidable','signed_support_incidence_entry_hit','signed_support_incidence_entry_miss'),total,
             'Every cell is constructively computed from a real signed lookup, a real natural beta image, and decidable equality.'),
        spec('signed_support_incidence_zero_source_value',
             f'forall A r s i j z. ({_table_at("A","i","0","zero_source")}) -> '
             f'({_entry("A","r","s","i","j","z","zero_entry")}) -> z=0',
             ('divisor_signed_table_at_functional',),zero,
             'Every incidence cell of a represented zero source is zero, even at an out-of-window image.'),
        spec('signed_support_incidence_nonzero_source_image',
             f'forall A r s i j z. ({_entry("A","r","s","i","j","z","nonzero_entry")}) -> ~(z=0) -> '
             +_and(_table_at('A','i','z','nonzero_source'),_at('r','s','i','j','nonzero_map')),(),nonzero,
             'A nonzero incidence value witnesses both the identical actual source value and the actual beta image.'),
    )


def _flat_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    total=_intro('A','r','s','M','k','hA')+(f'have hd : exists i j. '+_and('k=(S M)*i+j',_lt('j','S M','flat_division')),)
    total+=_call('division_remainder_exists','S M','k')+_call('succ_ne_zero','M')+_cases('hd',2)+('cases hd_witness_witness',)
    total+=(f'have hv : exists z. ({_entry("A","r","s","x","x1","z","flat_value")})',)
    total+=_call('signed_support_incidence_entry_exists','A','r','s','x','x1')+('exact hA','cases hv',
        'exists x2','exists x','exists x1','split','exact hd_witness_witness_left','split',
        'exact hd_witness_witness_right','exact hv_witness')

    read=_intro('A','r','s','M','i','j','z','hj','hv')+_cases('hv',2)+_parts('hv_witness_witness',3)
    read+=('have he : x=i /\\ x1=j',)+_call('division_remainder_unique','S M',_flat_index('M','i','j'),'x','x1','i','j')
    read+=('exact hv_witness_witness_left','exact hv_witness_witness_right_left','refl','exact hj','cases he')
    read+=_rewrite('he_left',_entry('A','r','s','x','x1','z','flat_read_first'),'x','hv_witness_witness_right_right')
    read+=_rewrite('he_right',_entry('A','r','s','i','x1','z','flat_read_second'),'x1','hv_witness_witness_right_right')
    read+=('exact hv_witness_witness_right_right',)
    return (
        spec('signed_support_incidence_flat_entry_exists',
             f'forall A r s M k. ({_table("0","A","flat_source_table")}) -> exists z. '
             f'({_flat_entry("A","r","s","M","k","z","flat_total")})',
             ('division_remainder_exists','succ_ne_zero','signed_support_incidence_entry_exists'),total,
             'Division by the positive padded width S M and actual incidence lookup construct every flat value, including M=0.'),
        spec('signed_support_incidence_flat_entry_coordinates',
             f'forall A r s M i j z. ({_lt("j","S M","flat_column_bound")}) -> '
             f'({_flat_entry("A","r","s","M",_flat_index("M","i","j"),"z","flat_read")}) -> '
             f'({_entry("A","r","s","i","j","z","flat_coordinates")})',
             ('division_remainder_unique',),read,
             'Uniqueness of actual quotient and strict remainder recovers the specified incidence coordinates.'),
    )


def _prefix_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    base=_intro('A','r','s','M','T','z','hT','hz','hv')+('split','exact hT')+_intro('k','u','hk','hu')
    base+=('have hk0 : k=0',)+_call('le_zero','k')+('exact hk',)
    base+=_rewrite('hk0',_table_at('T','k','u','base_read'),'k','hu')
    base+=('have he : z=u',)+_call('divisor_signed_table_at_functional','T','0','z','u')+('exact hz','exact hu')
    base+=_rewrite('he',_flat_entry('A','r','s','M','0','z','base_value'),'z','hv')
    base+=_rewrite('hk0',_flat_entry('A','r','s','M','k','u','base_target'),'k')+('exact hv',)

    extension=_and(_table('S l','U','append_table'),_table_equal('T','U','S l','append_equal'),_table_at('U','S l','z','append_last'))
    append=_intro('A','r','s','M','l','T','z','ht','hz')+('cases ht',f'have hx : exists U. ({extension})')
    append+=_call('arithmetic_signed_table_append','l','T','z')+('exact ht_left','cases hx')+_parts('hx_witness',3)
    append+=('exists x','split','split','exact hx_witness_left')+_intro('k','u','hk','hu')
    append+=(f'have hc : k=S l \\/ ({_lt("k","S l","append_cases")})',)
    append+=_call('le_eq_or_lt','k','S l')+('exact hk','cases hc')
    append+=_rewrite('hc_left',_table_at('x','k','u','append_last_read'),'k','hu')
    append+=('have he : z=u',)+_call('divisor_signed_table_at_functional','x','S l','z','u')+('exact hx_witness_right_right','exact hu')
    append+=_rewrite('he',_flat_entry('A','r','s','M','S l','z','append_last_value'),'z','hz')
    append+=_rewrite('hc_left',_flat_entry('A','r','s','M','k','u','append_last_target'),'k')+('exact hz',)
    append+=(f'have hkl : {_le("k","l","append_previous_bound")}',)+_call('le_of_succ_le_succ','k','l')+('exact hc_right',)
    append+=(f'have hv : exists v. ({_table_at("T","k","v","append_previous_value")})',)
    append+=_call('divisor_signed_table_lookup','l','T','k')+('exact ht_left','exact hkl','cases hv','have he : x1=u')
    append+=_call('hx_witness_right_left','k','x1','u')+('exact hc_right','exact hv_witness','exact hu')
    append+=_rewrite('he',_table_at('T','k','x1','append_previous_transport'),'x1','hv_witness')
    append+=_call('ht_right','k','u')+('exact hkl','exact hv_witness','exact hx_witness_right_left')

    exists=_intro('A','r','s','M','l')+('induction l',)+_intro('hA')
    exists+=(f'have hv : exists z. ({_flat_entry("A","r","s","M","0","z","prefix_first_value")})',)
    exists+=_call('signed_support_incidence_flat_entry_exists','A','r','s','M','0')+('exact hA','cases hv')
    exists+=(f'have ht : exists T. ({_and(_table("0","T","prefix_first_table"),_table_at("T","0","x","prefix_first_entry"))})',)
    exists+=_call('arithmetic_signed_table_singleton','x')+('cases ht','cases ht_witness','exists x1')
    exists+=_call('signed_support_incidence_flat_prefix_zero','A','r','s','M','x1','x')
    exists+=('exact ht_witness_left','exact ht_witness_right','exact hv_witness')
    exists+=_intro('hA')+(f'have hp : exists T. ({_flat_prefix("A","r","s","M","l","T","prefix_previous")})',)
    exists+=_call('IH')+('exact hA','cases hp',f'have hv : exists z. ({_flat_entry("A","r","s","M","S l","z","prefix_next_value")})')
    exists+=_call('signed_support_incidence_flat_entry_exists','A','r','s','M','S l')+('exact hA','cases hv')
    exists+=(f'have hext : exists U. ({_and(_flat_prefix("A","r","s","M","S l","U","prefix_next"),_table_equal("x","U","S l","prefix_preserved"))})',)
    exists+=_call('signed_support_incidence_flat_prefix_append','A','r','s','M','l','x','x1')
    exists+=('exact hp_witness','exact hv_witness','cases hext','cases hext_witness','exists x2','exact hext_witness_left')
    return (
        spec('signed_support_incidence_flat_prefix_zero',
             f'forall A r s M T z. ({_table("0","T","prefix_zero_table")}) -> ({_table_at("T","0","z","prefix_zero_lookup")}) -> '
             f'({_flat_entry("A","r","s","M","0","z","prefix_zero_value")}) -> ({_flat_prefix("A","r","s","M","0","T","prefix_zero")})',
             ('le_zero','divisor_signed_table_at_functional'),base,
             'A real singleton encodes the first actual flat incidence cell.'),
        spec('signed_support_incidence_flat_prefix_append',
             f'forall A r s M l T z. ({_flat_prefix("A","r","s","M","l","T","prefix_append_input")}) -> '
             f'({_flat_entry("A","r","s","M","S l","z","prefix_append_value")}) -> exists U. '
             +_and(_flat_prefix('A','r','s','M','S l','U','prefix_append_result'),_table_equal('T','U','S l','prefix_append_equal')),
             ('arithmetic_signed_table_append','le_eq_or_lt','le_of_succ_le_succ','divisor_signed_table_at_functional','divisor_signed_table_lookup'),append,
             'Constructively append one actual flat cell and preserve every preceding represented value.'),
        spec('signed_support_incidence_flat_prefix_exists',
             f'forall A r s M l. ({_table("0","A","prefix_exists_source")}) -> exists T. '
             f'({_flat_prefix("A","r","s","M","l","T","prefix_exists_result")})',
             ('signed_support_incidence_flat_entry_exists','arithmetic_signed_table_singleton','signed_support_incidence_flat_prefix_zero','signed_support_incidence_flat_prefix_append'),exists,
             'Ordinary induction constructs the entire inclusive prefix by real beta-stream extension, with no choice or sum oracle.'),
    )


def _incidence_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    length='L*(S M)'
    from_flat=_intro('A','r','s','L','M','T','hA','hp')+('cases hp','split','exact hA','split','exact hp_left')
    from_flat+=_intro('i','j','z','hi','hj','hz')+_call('signed_support_incidence_flat_entry_coordinates','A','r','s','M','i','j','z')
    from_flat+=_call('le_succ','S j','M')+('exact hj',)
    from_flat+=_call('hp_right',_flat_index('M','i','j'),'z')
    from_flat+=('have hcomm : (S M)*i=i*(S M)','apply mul_comm','rewrite hcomm')
    from_flat+=_call('lt_to_le','i*(S M)+j',length)
    from_flat+=_call('matrix_integer_rectangular_index_bound','L','S M','i','j')+('exact hi',)
    from_flat+=_call('le_succ','S j','M')+('exact hj','exact hz')

    exists=_intro('A','r','s','L','M','hA')+(f'have hp : exists T. ({_flat_prefix("A","r","s","M",length,"T","grid_flat")})',)
    exists+=_call('signed_support_incidence_flat_prefix_exists','A','r','s','M',length)+('exact hA','cases hp','exists x')
    exists+=_call('signed_support_incidence_from_flat_prefix','A','r','s','L','M','x')+('exact hA','exact hp_witness')
    return (
        spec('signed_support_incidence_from_flat_prefix',
             f'forall A r s L M T. ({_table("0","A","grid_input_table")}) -> '
             f'({_flat_prefix("A","r","s","M",length,"T","grid_input_prefix")}) -> '
             f'({_incidence("A","r","s","L","M","T","grid_output")})',
             ('signed_support_incidence_flat_entry_coordinates','le_succ','mul_comm','lt_to_le','matrix_integer_rectangular_index_bound'),from_flat,
             'The genuine inclusive flat prefix covers every strict rectangular cell; the extra column and endpoint are unused.'),
        spec('signed_support_incidence_exists',
             f'forall A r s L M. ({_table("0","A","grid_source_table")}) -> exists T. '
             f'({_incidence("A","r","s","L","M","T","grid_exists")})',
             ('signed_support_incidence_flat_prefix_exists','signed_support_incidence_from_flat_prefix'),exists,
             'Construct an actual padded incidence table for every pair of finite dimensions, including either zero dimension.'),
    )


def _slice_lookup_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    row_origin=_index('0','S M','i')
    row_coordinate=_index(row_origin,'1','j')
    row=_intro('A','r','s','L','M','T','V','i','j','z','hg','hv','hi','hj','hz')+_parts('hg',3)
    row+=_call('hg_right_right','i','j','z')+('exact hi','exact hj',)
    row+=(f'have hs : {_table_at("T",row_coordinate,"z","row_actual_source")}',)
    row+=_call('signed_rectangular_slice_lookup','T','V',row_origin,'1','M','j','z')+('exact hv','exact hj','exact hz')
    row+=(f'have he : {row_coordinate}={_flat_index("M","i","j")}',
          'specialize zero_add ((S M)*i)','rewrite zero_add',
          'specialize one_mul (j)','rewrite one_mul','refl')
    row+=_rewrite('he',_table_at('T','coord','z','row_index_rewrite'),'coord','hs')+('exact hs',)

    column_origin=_index('0','1','j')
    column_coordinate=_index(column_origin,'S M','i')
    column=_intro('A','r','s','L','M','T','V','i','j','z','hg','hv','hi','hj','hz')+_parts('hg',3)
    column+=_call('hg_right_right','i','j','z')+('exact hi','exact hj',)
    column+=(f'have hs : {_table_at("T",column_coordinate,"z","column_actual_source")}',)
    column+=_call('signed_rectangular_slice_lookup','T','V',column_origin,'S M','L','i','z')+('exact hv','exact hi','exact hz')
    column+=(f'have he : {column_coordinate}={_flat_index("M","i","j")}',
             'specialize zero_add (1*j)','rewrite zero_add',
             'specialize one_mul (j)','rewrite one_mul','apply add_comm')
    column+=_rewrite('he',_table_at('T','coord','z','column_index_rewrite'),'coord','hs')+('exact hs',)
    return (
        spec('signed_support_incidence_row_lookup',
             f'forall A r s L M T V i j z. ({_incidence("A","r","s","L","M","T","row_lookup_grid")}) -> '
             f'({_slice("T","V",row_origin,"1","M","row_lookup_slice")}) -> ({_lt("i","L","row_lookup_bound")}) -> '
             f'({_lt("j","M","row_lookup_column")}) -> ({_table_at("V","j","z","row_lookup_value")}) -> '
             f'({_entry("A","r","s","i","j","z","row_lookup_entry")})',
             ('signed_rectangular_slice_lookup','zero_add','one_mul'),row,
             'An actual affine row-slice entry is the incidence cell at the same strict row and column indices.'),
        spec('signed_support_incidence_column_lookup',
             f'forall A r s L M T V i j z. ({_incidence("A","r","s","L","M","T","column_lookup_grid")}) -> '
             f'({_slice("T","V",column_origin,"S M","L","column_lookup_slice")}) -> ({_lt("i","L","column_lookup_row")}) -> '
             f'({_lt("j","M","column_lookup_bound")}) -> ({_table_at("V","i","z","column_lookup_value")}) -> '
             f'({_entry("A","r","s","i","j","z","column_lookup_entry")})',
             ('signed_rectangular_slice_lookup','zero_add','one_mul','add_comm'),column,
             'An actual affine column-slice entry is the same incidence cell after proved natural index commutation.'),
    )


def _row_value_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    row_origin=_index('0','S M','i')
    preserve=_part('hp',5,2)
    body=_intro('A','B','r','s','L','M','T','i','a','z','hp','hg','hi','ha','hs')+_parts('hp',5)
    body+=('cases hs','cases hs_witness','have hc : a=0 \\/ ~(a=0)')+_call('eq_decidable','a','0')+('cases hc',)
    body+=_rewrite('hc_left',_table_at('A','i','a','row_zero_source'),'a','ha')
    body+=_rewrite('hc_left','z=a','a')+_call('signed_prefix_sum_zero_value','x','M','z')
    body+=_intro('j','v','h0j','hj','hv')+_call('signed_support_incidence_zero_source_value','A','r','s','i','j','v')
    body+=('exact ha',)+_call('signed_support_incidence_row_lookup','A','r','s','L','M','T','x','i','j','v')
    body+=('exact hg','exact hs_witness_left','exact hi','exact hj','exact hv','exact hs_witness_right')

    image=_and(_at('r','s','i','j','row_active_map'),_lt('j','M','row_active_bound'),_table_at('B','j','a','row_active_value'))
    body+=(f'have hm : exists j. ({image})',)+_call(preserve,'i','a')+('exact hi','exact ha','exact hc_right','cases hm')
    body+=_parts('hm_witness',3)+_call('signed_prefix_sum_point_spike_value','x','M','x1','a','z')
    body+=_parts('hs_witness_left',3)+_call('signed_table_domain_resize','M','0','x')
    body+=('exact hs_witness_left_right_left','exact hm_witness_right_left')
    body+=(f'have hv : exists v. ({_table_at("x","x1","v","row_spike_actual_lookup")})',)
    body+=_call('signed_table_lookup_any','M','x','x1')+_parts('hs_witness_left',3)+('exact hs_witness_left_right_left','cases hv','have he : x2=a')
    body+=_call('signed_support_incidence_entry_functional','A','r','s','i','x1','x2','a')
    body+=_call('signed_support_incidence_row_lookup','A','r','s','L','M','T','x','i','x1','x2')
    body+=('exact hg','exact hs_witness_left','exact hi','exact hm_witness_right_left','exact hv_witness')
    body+=_call('signed_support_incidence_entry_hit','A','r','s','i','x1','a')+('exact ha','exact hm_witness_left')
    body+=_rewrite('he',_table_at('x','x1','x2','row_spike_entry_rewrite'),'x2','hv_witness')+('exact hv_witness',)
    body+=_intro('j','v','hj','hne','hv')+_call('signed_support_incidence_entry_functional','A','r','s','i','j','v','0')
    body+=_call('signed_support_incidence_row_lookup','A','r','s','L','M','T','x','i','j','v')
    body+=('exact hg','exact hs_witness_left','exact hi','exact hj','exact hv')
    body+=_call('signed_support_incidence_entry_miss','A','r','s','i','j','x1','a')
    body+=('exact ha','exact hm_witness_left','exact hne','exact hs_witness_right')
    return (
        spec('signed_support_incidence_row_sum_value',
             f'forall A B r s L M T i a z. ({_reindex("A","B","r","s","L","M","row_value_support")}) -> '
             f'({_incidence("A","r","s","L","M","T","row_value_grid")}) -> ({_lt("i","L","row_value_bound")}) -> '
             f'({_table_at("A","i","a","row_value_source")}) -> ({_slice_sum("T",row_origin,"1","M","z","row_value_sum")}) -> z=a',
             ('eq_decidable','signed_prefix_sum_zero_value','signed_support_incidence_zero_source_value',
              'signed_support_incidence_row_lookup','signed_prefix_sum_point_spike_value','signed_table_domain_resize',
              'signed_table_lookup_any','signed_support_incidence_entry_functional','signed_support_incidence_entry_hit','signed_support_incidence_entry_miss'),body,
             'Each actual incidence row is zero or one genuinely bounded spike, so its actual sum is the actual source value.'),
    )


def _column_value_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    column_origin=_index('0','1','j')
    preserve,injective,cover=(_part('hp',5,index) for index in (2,3,4))
    body=_intro('A','B','r','s','L','M','T','j','b','z','hp','hg','hj','hb','hs')+_parts('hp',5)
    body+=('cases hs','cases hs_witness','have hc : b=0 \\/ ~(b=0)')+_call('eq_decidable','b','0')+('cases hc',)
    body+=_rewrite('hc_left',_table_at('B','j','b','column_zero_target'),'b','hb')
    body+=_rewrite('hc_left','z=b','b')+_call('signed_prefix_sum_zero_value','x','L','z')
    body+=_intro('i','v','h0i','hi','hv')+('have hn : v=0 \\/ ~(v=0)',)+_call('eq_decidable','v','0')
    body+=('cases hn','exact hn_left')
    source=_and(_table_at('A','i','v','column_zero_source'),_at('r','s','i','j','column_zero_map'))
    body+=(f'have hsource : {source}',)+_call('signed_support_incidence_nonzero_source_image','A','r','s','i','j','v')
    body+=_call('signed_support_incidence_column_lookup','A','r','s','L','M','T','x','i','j','v')
    body+=('exact hg','exact hs_witness_left','exact hi','exact hj','exact hv','exact hn_right','cases hsource')
    image=_and(_at('r','s','i','k','column_zero_preserved_map'),_lt('k','M','column_zero_preserved_bound'),_table_at('B','k','v','column_zero_preserved_value'))
    body+=(f'have hm : exists k. ({image})',)+_call(preserve,'i','v')
    body+=('exact hi','exact hsource_left','exact hn_right','cases hm')+_parts('hm_witness',3)
    body+=('have he : x1=j',)+_call('beta_at_unique','r','s','i','x1','j')+('exact hm_witness_left','exact hsource_right')
    body+=_rewrite('he',_table_at('B','x1','v','column_zero_index_rewrite'),'x1','hm_witness_right_right')
    body+=_call('divisor_signed_table_at_functional','B','j','v','0')+('exact hm_witness_right_right','exact hb','exact hs_witness_right')

    preimage=_and(_lt('i','L','column_active_bound'),_at('r','s','i','j','column_active_map'),_table_at('A','i','b','column_active_source'))
    body+=(f'have hm : exists i. ({preimage})',)+_call(cover,'j','b')+('exact hj','exact hb','exact hc_right','cases hm')
    body+=_parts('hm_witness',3)+_call('signed_prefix_sum_point_spike_value','x','L','x1','b','z')
    body+=_parts('hs_witness_left',3)+_call('signed_table_domain_resize','L','0','x')
    body+=('exact hs_witness_left_right_left','exact hm_witness_left')
    body+=(f'have hv : exists v. ({_table_at("x","x1","v","column_spike_actual_lookup")})',)
    body+=_call('signed_table_lookup_any','L','x','x1')+_parts('hs_witness_left',3)+('exact hs_witness_left_right_left','cases hv','have he : x2=b')
    body+=_call('signed_support_incidence_entry_functional','A','r','s','x1','j','x2','b')
    body+=_call('signed_support_incidence_column_lookup','A','r','s','L','M','T','x','x1','j','x2')
    body+=('exact hg','exact hs_witness_left','exact hm_witness_left','exact hj','exact hv_witness')
    body+=_call('signed_support_incidence_entry_hit','A','r','s','x1','j','b')+('exact hm_witness_right_right','exact hm_witness_right_left')
    body+=_rewrite('he',_table_at('x','x1','x2','column_spike_entry_rewrite'),'x2','hv_witness')+('exact hv_witness',)
    body+=_intro('i','v','hi','hne','hv')+('have hn : v=0 \\/ ~(v=0)',)+_call('eq_decidable','v','0')
    body+=('cases hn','exact hn_left','exfalso','apply hne')
    source=_and(_table_at('A','i','v','column_other_source'),_at('r','s','i','j','column_other_map'))
    body+=(f'have hsource : {source}',)+_call('signed_support_incidence_nonzero_source_image','A','r','s','i','j','v')
    body+=_call('signed_support_incidence_column_lookup','A','r','s','L','M','T','x','i','j','v')
    body+=('exact hg','exact hs_witness_left','exact hi','exact hj','exact hv','exact hn_right','cases hsource')
    body+=_call(injective,'i','x1','j','v','b')
    body+=('exact hi','exact hm_witness_left','exact hsource_left','exact hn_right','exact hm_witness_right_right',
           'exact hc_right','exact hsource_right','exact hm_witness_right_left','exact hs_witness_right')
    return (
        spec('signed_support_incidence_column_sum_value',
             f'forall A B r s L M T j b z. ({_reindex("A","B","r","s","L","M","column_value_support")}) -> '
             f'({_incidence("A","r","s","L","M","T","column_value_grid")}) -> ({_lt("j","M","column_value_bound")}) -> '
             f'({_table_at("B","j","b","column_value_target")}) -> ({_slice_sum("T",column_origin,"S M","L","z","column_value_sum")}) -> z=b',
             ('eq_decidable','signed_prefix_sum_zero_value','signed_support_incidence_nonzero_source_image',
              'signed_support_incidence_column_lookup','beta_at_unique','divisor_signed_table_at_functional',
              'signed_prefix_sum_point_spike_value','signed_table_domain_resize','signed_table_lookup_any',
              'signed_support_incidence_entry_functional','signed_support_incidence_entry_hit'),body,
             'Target coverage supplies the actual nonzero spike; active injectivity excludes other nonzero cells and preservation handles zero targets.'),
    )


def _sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    row_equal=_intro('A','B','r','s','L','M','T','R','hp','hg','hr','i','a','b','hi','ha','hb')+('have he : b=a',)
    row_equal+=_call('signed_support_incidence_row_sum_value','A','B','r','s','L','M','T','i','a','b')
    row_equal+=('exact hp','exact hg','exact hi','exact ha')
    row_equal+=_call('signed_rectangular_row_sums_lookup','T','R','0','S M','1','L','M','i','b')
    row_equal+=('exact hr','exact hi','exact hb','symm','exact he')

    column_equal=_intro('A','B','r','s','L','M','T','C','hp','hg','hc','j','a','b','hj','ha','hb')+('have he : b=a',)
    column_equal+=_call('signed_support_incidence_column_sum_value','A','B','r','s','L','M','T','j','a','b')
    column_equal+=('exact hp','exact hg','exact hj','exact ha')
    column_equal+=_call('signed_rectangular_row_sums_lookup','T','C','0','1','S M','M','L','j','b')
    column_equal+=('exact hc','exact hj','exact hb','symm','exact he')

    equal=_intro('A','B','r','s','L','M','u','v','hp','hu','hv')+_parts('hp',5)
    equal+=(f'have hg : exists T. ({_incidence("A","r","s","L","M","T","sum_actual_grid")})',)
    equal+=_call('signed_support_incidence_exists','A','r','s','L','M')+('exact hp_left','cases hg')
    equal+=(f'have hf : exists R C z. ({_fubini_data("x","R","C","0","S M","1","L","M","z","sum_actual_fubini")})',)
    equal+=_call('signed_rectangular_fubini_exists','x','0','S M','1','L','M')
    equal+=_parts('hg_witness',3)+_call('signed_table_domain_resize','L*(S M)','0','x')+('exact hg_witness_right_left',)
    equal+=_cases('hf',3)+_parts('hf_witness_witness_witness',4)+('have ha : u=x3',)
    equal+=_call('divisor_signed_sum_extensional','A','x1','L','u','x3')
    equal+=_call('signed_support_incidence_row_sums_equal','A','B','r','s','L','M','x','x1')
    equal+=('exact hp','exact hg_witness','exact '+_part('hf_witness_witness_witness',4,0),'exact hu',
            'exact '+_part('hf_witness_witness_witness',4,2),'have hb : v=x3')
    equal+=_call('divisor_signed_sum_extensional','B','x2','M','v','x3')
    equal+=_call('signed_support_incidence_column_sums_equal','A','B','r','s','L','M','x','x2')
    equal+=('exact hp','exact hg_witness','exact '+_part('hf_witness_witness_witness',4,1),'exact hv',
            'exact '+_part('hf_witness_witness_witness',4,3),'trans x3','exact ha','symm','exact hb')

    exists=_intro('A','B','r','s','L','M','hp')+_parts('hp',5)
    exists+=(f'have ha : exists u. ({_signed_sum("A","L","u","common_source_sum")})',)
    exists+=_call('arithmetic_signed_sum_exists','0','A','L')+('exact hp_left','cases ha')
    exists+=(f'have hb : exists v. ({_signed_sum("B","M","v","common_target_sum")})',)
    exists+=_call('arithmetic_signed_sum_exists','0','B','M')+('exact hp_right_left','cases hb','have he : x1=x','symm')
    exists+=_call('signed_support_reindex_sum_equal','A','B','r','s','L','M','x','x1')
    exists+=('exact hp','exact ha_witness','exact hb_witness')
    exists+=_rewrite('he',_signed_sum('B','M','x1','common_value_rewrite'),'x1','hb_witness')
    exists+=('exists x','split','exact ha_witness','exact hb_witness')
    return (
        spec('signed_support_incidence_row_sums_equal',
             f'forall A B r s L M T R. ({_reindex("A","B","r","s","L","M","row_equal_support")}) -> '
             f'({_incidence("A","r","s","L","M","T","row_equal_grid")}) -> '
             f'({_row_sums("T","R","0","S M","1","L","M","row_equal_rows")}) -> '
             f'({_table_equal("A","R","L","row_equal_result")})',
             ('signed_support_incidence_row_sum_value','signed_rectangular_row_sums_lookup'),row_equal,
             'Every actual incidence row-sum table agrees with the represented source values on precisely the strict source window.'),
        spec('signed_support_incidence_column_sums_equal',
             f'forall A B r s L M T C. ({_reindex("A","B","r","s","L","M","column_equal_support")}) -> '
             f'({_incidence("A","r","s","L","M","T","column_equal_grid")}) -> '
             f'({_row_sums("T","C","0","1","S M","M","L","column_equal_rows")}) -> '
             f'({_table_equal("B","C","M","column_equal_result")})',
             ('signed_support_incidence_column_sum_value','signed_rectangular_row_sums_lookup'),column_equal,
             'Every actual incidence column-sum table agrees with the represented target values on precisely the strict target window.'),
        spec('signed_support_reindex_sum_equal',
             f'forall A B r s L M u v. ({_reindex("A","B","r","s","L","M","equal_support")}) -> '
             f'({_signed_sum("A","L","u","equal_source_sum")}) -> ({_signed_sum("B","M","v","equal_target_sum")}) -> u=v',
             ('signed_support_incidence_exists','signed_rectangular_fubini_exists','signed_table_domain_resize',
              'divisor_signed_sum_extensional','signed_support_incidence_row_sums_equal','signed_support_incidence_column_sums_equal'),equal,
             'Construct the actual incidence and both fold tables; ordinary finite Fubini proves equality under support-only reindexing, including unequal or empty windows.'),
        spec('signed_support_reindex_sum_exists',
             f'forall A B r s L M. ({_reindex("A","B","r","s","L","M","exists_support")}) -> exists z. '
             +_and(_signed_sum('A','L','z','exists_source_sum'),_signed_sum('B','M','z','exists_target_sum')),
             ('arithmetic_signed_sum_exists','signed_support_reindex_sum_equal'),exists,
             'Actually construct both signed finite folds and their common canonical value; neither fold is assumed as an oracle.'),
    )


def make_signed_support_reindex_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (_spike_rows(spec)+_entry_rows(spec)+_flat_rows(spec)+_prefix_rows(spec)+_incidence_rows(spec)
            +_slice_lookup_rows(spec)+_row_value_rows(spec)+_column_value_rows(spec)+_sum_rows(spec))


__all__ = [
    'signed_support_reindex_relation', 'signed_support_incidence_entry_relation',
    'signed_support_incidence_flat_entry_relation', 'signed_support_incidence_flat_prefix_relation',
    'signed_support_incidence_relation', 'make_signed_support_reindex_candidate_theorems',
]
