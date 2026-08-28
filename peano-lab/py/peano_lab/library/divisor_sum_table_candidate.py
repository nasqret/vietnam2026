"""Actual finite signed tables and sums, independent of Möbius inversion.

A table packs two beta sequences of natural components with the historic
injective natural pairing.  Entries and sums return the unique canonical
signed code represented by their component balance.  Equality of signed
values never asserts equality of different positive/negative representatives.

Only ordinary first-order HA bodies are generated.  No table definition
contains a divisor transform, cancellation identity, or inversion conclusion.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_sum_theorems import _sum_relation_terms
from .gaussian_euclidean_candidate import _balance, _pair
from .integer_column_span_candidate import _equal
from .prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _intro, _le, _lt, _part, _parts, _public, _rewrite,
)


def _names(tag: str, *roles: str) -> tuple[str,...]:
    return tuple('dst_'+role+'_'+tag for role in roles)


def _pack(pb: str, pc: str, nb: str, nc: str) -> str:
    return _pair(_pair(pb,pc),_pair(nb,nc))


def _rep(F: str, pb: str, pc: str, nb: str, nc: str, tag: str) -> str:
    return f'({F}) = ({_pack(pb,pc,nb,nc)})'


def _components(pb: str, pc: str, nb: str, nc: str, i: str, p: str, n: str, z: str, tag: str) -> str:
    return _and(_at(pb,pc,i,p,tag+'positive'),_at(nb,nc,i,n,tag+'negative'),_balance(z,p,n,tag+'value'))


def _table_at(F: str, i: str, z: str, tag: str) -> str:
    pb,pc,nb,nc,p,n=_names(tag,'positive_code','positive_scale','negative_code','negative_scale','positive','negative')
    return f'exists {pb} {pc} {nb} {nc} {p} {n}. '+_and(
        _rep(F,pb,pc,nb,nc,tag+'packing'),_at(pb,pc,i,p,tag+'positive'),
        _at(nb,nc,i,n,tag+'negative'),_balance(z,p,n,tag+'value'))


def _table(N: str, F: str, tag: str) -> str:
    pb,pc,nb,nc,i,p,n,z=_names(tag,'positive_code','positive_scale','negative_code','negative_scale','index','positive','negative','value')
    return f'exists {pb} {pc} {nb} {nc}. '+_and(
        _rep(F,pb,pc,nb,nc,tag+'packing'),
        f'forall {i}. ({_le(i,N,tag+"domain")}) -> exists {p} {n} {z}. '+_components(pb,pc,nb,nc,i,p,n,z,tag+'entry'))


def _sum(b: str, c: str, l: str, s: str, tag: str) -> str:
    return _sum_relation_terms(b,c,l,s,tag='dst_'+tag)


def _signed_sum(F: str, l: str, z: str, tag: str) -> str:
    pb,pc,nb,nc,p,n=_names(tag,'positive_code','positive_scale','negative_code','negative_scale','positive_sum','negative_sum')
    return f'exists {pb} {pc} {nb} {nc} {p} {n}. '+_and(
        _rep(F,pb,pc,nb,nc,tag+'packing'),_sum(pb,pc,l,p,tag+'positive'),
        _sum(nb,nc,l,n,tag+'negative'),_balance(z,p,n,tag+'result'))


def _table_equal(F: str, G: str, l: str, tag: str) -> str:
    i,a,b=_names(tag,'index','first','second')
    return f'forall {i} {a} {b}. ({_lt(i,l,tag+"bound")}) -> ({_table_at(F,i,a,tag+"first")}) -> ({_table_at(G,i,b,tag+"second")}) -> {a} = {b}'


def signed_arithmetic_table_representation_relation(F: str, pb: str, pc: str, nb: str, nc: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_rep,(F,pb,pc,nb,nc),tag=tag,variables=variables)


def signed_arithmetic_table_relation(N: str, F: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Actual paired beta table with canonical signed entries through index N."""
    return _public(_table,(N,F),tag=tag,variables=variables)


def signed_arithmetic_table_entry_relation(F: str, i: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_table_at,(F,i,z),tag=tag,variables=variables)


def signed_arithmetic_prefix_sum_relation(F: str, l: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Sum of the actual signed entries at exactly the indices 0 <= i < l."""
    return _public(_signed_sum,(F,l,z),tag=tag,variables=variables)


def signed_arithmetic_table_equality_relation(F: str, G: str, l: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_table_equal,(F,G,l),tag=tag,variables=variables)


def _pack_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    a=('pb','pc','nb','nc')
    return (
        spec(
            'divisor_signed_table_at_from_components',
            f"forall F {' '.join(a)} i p n z. ({_rep('F',*a,'entry_pack')}) -> ({_at('pb','pc','i','p','entry_positive')}) -> "
            f"({_at('nb','nc','i','n','entry_negative')}) -> ({_balance('z','p','n','entry_balance')}) -> ({_table_at('F','i','z','entry_result')})",
            (),
            _intro('F',*a,'i','p','n','z','hrep','hp','hn','hz')
            +tuple('exists '+x for x in (*a,'p','n'))+('split','exact hrep','split','exact hp','split','exact hn','exact hz'),
            'Actual beta entries and their canonical signed balance produce a genuine table lookup.',
        ),
        spec(
            'divisor_signed_table_at_to_components',
            f"forall F {' '.join(a)} i z. ({_rep('F',*a,'unpack_known')}) -> ({_table_at('F','i','z','unpack_entry')}) -> "
            f"exists p n. ({_components(*a,'i','p','n','z','unpack_result')})",
            ('matrix_minor_four_code_components_injective',),
            _intro('F',*a,'i','z','hrep','hentry')+_cases('hentry',6)+_parts('hentry'+'_witness'*6,4)
            +(f"have heq : {_and('x = pb','x1 = pc','x2 = nb','x3 = nc')}",)
            +_call('matrix_minor_four_code_components_injective','F','x','x1','x2','x3',*a)
            +('exact hentry_witness_witness_witness_witness_witness_witness_left','exact hrep')+_parts('heq',4)
            +('exists x4','exists x5','split')
            +_rewrite('heq_left',_at('x','x1','i','x4','unpack_pos_recode'),'x','hentry_witness_witness_witness_witness_witness_witness_right_left')
            +_rewrite('heq_right_left',_at('pb','x1','i','x4','unpack_pos_scale'),'x1','hentry_witness_witness_witness_witness_witness_witness_right_left')
            +('exact hentry_witness_witness_witness_witness_witness_witness_right_left','split')
            +_rewrite('heq_right_right_left',_at('x2','x3','i','x5','unpack_neg_recode'),'x2','hentry_witness_witness_witness_witness_witness_witness_right_right_left')
            +_rewrite('heq_right_right_right',_at('nb','x3','i','x5','unpack_neg_scale'),'x3','hentry_witness_witness_witness_witness_witness_witness_right_right_left')
            +('exact hentry_witness_witness_witness_witness_witness_witness_right_right_left','exact hentry_witness_witness_witness_witness_witness_witness_right_right_right'),
            'Every lookup unpacks against any proved representation of its exact table code, with actual component witnesses.',
        ),
    )


def _table_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    a=('pb','pc','nb','nc')
    return (
        spec(
            'divisor_signed_table_from_components',
            f"forall N F {' '.join(a)}. ({_rep('F',*a,'constructor_pack')}) -> ({_table('N','F','constructor_table')})",
            ('beta_at_exists','signed_balance_total'),
            _intro('N','F',*a,'hrep')+tuple('exists '+x for x in a)+('split','exact hrep')
            +_intro('i','hbound')+(f"have hp : exists p. ({_at('pb','pc','i','p','constructor_positive')})",)
            +_call('beta_at_exists','pb','pc','i')+('cases hp',
                f"have hn : exists n. ({_at('nb','nc','i','n','constructor_negative')})")
            +_call('beta_at_exists','nb','nc','i')+('cases hn',
                f"have hz : exists z. ({_balance('z','x','x1','constructor_balance')})")
            +_call('signed_balance_total','x','x1')+('cases hz','exists x','exists x1','exists x2','split','exact hp_witness','split','exact hn_witness','exact hz_witness'),
            'Every actual pair of beta component streams gives canonical signed entries on every requested finite domain, including the zero endpoint.',
        ),
        spec(
            'divisor_signed_table_construct',
            f"forall N {' '.join(a)}. exists F. ({_table('N','F','constructed')}) /\\ ({_rep('F',*a,'constructed_rep')})",
            ('divisor_signed_table_from_components',),
            _intro('N',*a)+(f'exists {_pack(*a)}','split')
            +_call('divisor_signed_table_from_components','N',_pack(*a),*a)+('refl','refl'),
            'Natural pairing constructs the table code itself, not merely an opaque validity witness.',
        ),
        spec(
            'divisor_signed_table_components',
            f"forall N F. ({_table('N','F','extract_table')}) -> exists pb pc nb nc. ({_rep('F','pb','pc','nb','nc','extracted_pack')})",
            (),
            _intro('N','F','h')+_cases('h',4)+('cases h_witness_witness_witness_witness','exists x','exists x1','exists x2','exists x3','exact h_witness_witness_witness_witness_left'),
            'A valid finite signed table always supplies its actual nested natural-pair packing.',
        ),
        spec(
            'divisor_signed_table_lookup',
            f"forall N F i. ({_table('N','F','lookup_table')}) -> ({_le('i','N','lookup_domain')}) -> exists z. ({_table_at('F','i','z','lookup_result')})",
            ('divisor_signed_table_at_from_components',),
            _intro('N','F','i','ht','hi')+_cases('ht',4)+('cases ht_witness_witness_witness_witness',
                f"have hvalue : exists p n z. ({_components('x','x1','x2','x3','i','p','n','z','lookup_value')})")
            +_call('ht_witness_witness_witness_witness_right','i')+('exact hi',)+_cases('hvalue',3)+_parts('hvalue_witness_witness_witness',3)
            +('exists x6',)+_call('divisor_signed_table_at_from_components','F','x','x1','x2','x3','i','x4','x5','x6')
            +('exact ht_witness_witness_witness_witness_left','exact hvalue_witness_witness_witness_left','exact hvalue_witness_witness_witness_right_left','exact hvalue_witness_witness_witness_right_right'),
            'Every index in the explicitly stated finite domain has an actual canonical signed lookup code.',
        ),
        spec(
            'divisor_signed_table_at_functional',
            f"forall F i a b. ({_table_at('F','i','a','functional_first')}) -> ({_table_at('F','i','b','functional_second')}) -> a = b",
            ('divisor_signed_table_at_to_components','beta_at_unique','signed_balance_functional'),
            _intro('F','i','a','b','ha','hb')+_cases('ha',6)+_parts('ha'+'_witness'*6,4)
            +(f"have hother : exists p n. ({_components('x','x1','x2','x3','i','p','n','b','functional_other')})",)
            +_call('divisor_signed_table_at_to_components','F','x','x1','x2','x3','i','b')
            +('exact ha_witness_witness_witness_witness_witness_witness_left','exact hb')+_cases('hother',2)+_parts('hother_witness_witness',3)
            +('have hp : x6 = x4',)+_call('beta_at_unique','x','x1','i','x6','x4')
            +('exact hother_witness_witness_left','exact ha_witness_witness_witness_witness_witness_witness_right_left',
                'have hn : x7 = x5')+_call('beta_at_unique','x2','x3','i','x7','x5')
            +('exact hother_witness_witness_right_left','exact ha_witness_witness_witness_witness_witness_witness_right_right_left')
            +_rewrite('hp',_balance('b','x6','x7','functional_positive'),'x6','hother_witness_witness_right_right')
            +_rewrite('hn',_balance('b','x4','x7','functional_negative'),'x7','hother_witness_witness_right_right')
            +_call('signed_balance_functional','x4','x5','a','b')
            +('exact ha_witness_witness_witness_witness_witness_witness_right_right_right','exact hother_witness_witness_right_right'),
            'Actual beta functionality and canonical signed balance make each lookup code literally unique.',
        ),
        spec(
            'divisor_signed_table_restrict',
            f"forall N K F. ({_table('N','F','restriction_source')}) -> ({_le('K','N','restriction_bound')}) -> ({_table('K','F','restriction_target')})",
            ('divisor_signed_table_components','divisor_signed_table_from_components'),
            _intro('N','K','F','ht','hbound')
            +(f"have hrep : exists pb pc nb nc. ({_rep('F','pb','pc','nb','nc','restriction_rep')})",)
            +_call('divisor_signed_table_components','N','F')+('exact ht',)+_cases('hrep',4)
            +_call('divisor_signed_table_from_components','K','F','x','x1','x2','x3')+('exact hrep_witness_witness_witness_witness',),
            'The same packed table remains valid on every shorter finite domain, without a new encoding or changed entries.',
        ),
    )


def _sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    a=('pb','pc','nb','nc')
    return (
        spec(
            'divisor_signed_sum_from_components',
            f"forall F {' '.join(a)} l p n z. ({_rep('F',*a,'sum_constructor_rep')}) -> ({_sum('pb','pc','l','p','sum_constructor_positive')}) -> "
            f"({_sum('nb','nc','l','n','sum_constructor_negative')}) -> ({_balance('z','p','n','sum_constructor_balance')}) -> ({_signed_sum('F','l','z','sum_constructor_result')})",
            (),
            _intro('F',*a,'l','p','n','z','hrep','hp','hn','hz')+tuple('exists '+x for x in (*a,'p','n'))
            +('split','exact hrep','split','exact hp','split','exact hn','exact hz'),
            'Two genuine natural finite sums and their canonical signed balance construct the signed prefix sum.',
        ),
        spec(
            'divisor_signed_sum_to_components',
            f"forall F {' '.join(a)} l z. ({_rep('F',*a,'sum_unpacked_rep')}) -> ({_signed_sum('F','l','z','sum_unpacked_input')}) -> "
            f"exists p n. {_and(_sum('pb','pc','l','p','sum_unpacked_positive'),_sum('nb','nc','l','n','sum_unpacked_negative'),_balance('z','p','n','sum_unpacked_balance'))}",
            ('matrix_minor_four_code_components_injective',),
            _intro('F',*a,'l','z','hrep','hsum')+_cases('hsum',6)+_parts('hsum'+'_witness'*6,4)
            +(f"have heq : {_and('x = pb','x1 = pc','x2 = nb','x3 = nc')}",)
            +_call('matrix_minor_four_code_components_injective','F','x','x1','x2','x3',*a)
            +('exact hsum_witness_witness_witness_witness_witness_witness_left','exact hrep')+_parts('heq',4)
            +('exists x4','exists x5','split')
            +_rewrite('heq_left',_sum('x','x1','l','x4','sum_pos_recode'),'x','hsum_witness_witness_witness_witness_witness_witness_right_left')
            +_rewrite('heq_right_left',_sum('pb','x1','l','x4','sum_pos_scale'),'x1','hsum_witness_witness_witness_witness_witness_witness_right_left')
            +('exact hsum_witness_witness_witness_witness_witness_witness_right_left','split')
            +_rewrite('heq_right_right_left',_sum('x2','x3','l','x5','sum_neg_recode'),'x2','hsum_witness_witness_witness_witness_witness_witness_right_right_left')
            +_rewrite('heq_right_right_right',_sum('nb','x3','l','x5','sum_neg_scale'),'x3','hsum_witness_witness_witness_witness_witness_witness_right_right_left')
            +('exact hsum_witness_witness_witness_witness_witness_witness_right_right_left','exact hsum_witness_witness_witness_witness_witness_witness_right_right_right'),
            'Every signed sum unpacks into actual natural prefix sums against its proved table representation.',
        ),
        spec(
            'divisor_signed_sum_exists_from_components',
            f"forall F {' '.join(a)} l. ({_rep('F',*a,'sum_exists_rep')}) -> exists z. ({_signed_sum('F','l','z','sum_exists_result')})",
            ('beta_sum_exists','signed_balance_total','divisor_signed_sum_from_components'),
            _intro('F',*a,'l','hrep')+(f"have hp : exists p. ({_sum('pb','pc','l','p','sum_exists_positive')})",)
            +_call('beta_sum_exists','pb','pc','l')+('cases hp',f"have hn : exists n. ({_sum('nb','nc','l','n','sum_exists_negative')})")
            +_call('beta_sum_exists','nb','nc','l')+('cases hn',f"have hz : exists z. ({_balance('z','x','x1','sum_exists_balance')})")
            +_call('signed_balance_total','x','x1')+('cases hz','exists x2')
            +_call('divisor_signed_sum_from_components','F',*a,'l','x','x1','x2')
            +('exact hrep','exact hp_witness','exact hn_witness','exact hz_witness'),
            'Both natural folds and signed normalization are genuinely constructed; no supplied sum or sign oracle is required.',
        ),
        spec(
            'divisor_signed_sum_functional',
            f"forall F l a b. ({_signed_sum('F','l','a','sum_unique_first')}) -> ({_signed_sum('F','l','b','sum_unique_second')}) -> a = b",
            ('divisor_signed_sum_to_components','beta_sum_functional','signed_balance_functional'),
            _intro('F','l','a','b','ha','hb')+_cases('ha',6)+_parts('ha'+'_witness'*6,4)
            +(f"have hother : exists p n. {_and(_sum('x','x1','l','p','sum_unique_positive'),_sum('x2','x3','l','n','sum_unique_negative'),_balance('b','p','n','sum_unique_balance'))}",)
            +_call('divisor_signed_sum_to_components','F','x','x1','x2','x3','l','b')
            +('exact ha_witness_witness_witness_witness_witness_witness_left','exact hb')+_cases('hother',2)+_parts('hother_witness_witness',3)
            +('have hp : x6 = x4',)+_call('beta_sum_functional','x','x1','l','x6','x4')
            +('exact hother_witness_witness_left','exact ha_witness_witness_witness_witness_witness_witness_right_left',
                'have hn : x7 = x5')+_call('beta_sum_functional','x2','x3','l','x7','x5')
            +('exact hother_witness_witness_right_left','exact ha_witness_witness_witness_witness_witness_witness_right_right_left')
            +_rewrite('hp',_balance('b','x6','x7','sum_unique_pos_rewrite'),'x6','hother_witness_witness_right_right')
            +_rewrite('hn',_balance('b','x4','x7','sum_unique_neg_rewrite'),'x7','hother_witness_witness_right_right')
            +_call('signed_balance_functional','x4','x5','a','b')
            +('exact ha_witness_witness_witness_witness_witness_witness_right_right_right','exact hother_witness_witness_right_right'),
            'The signed sum has a literally unique canonical result code, not a supposedly unique non-normalized signed pair.',
        ),
        spec(
            'divisor_signed_sum_empty_value',
            f"forall F z. ({_signed_sum('F','0','z','empty_sum')}) -> z = 0",
            ('beta_sum_zero','signed_balance_zero_iff'),
            _intro('F','z','h')+_cases('h',6)+_parts('h'+'_witness'*6,4)
            +('have hp : x4 = 0',)+_call('beta_sum_zero','x','x1','x4')
            +('exact h_witness_witness_witness_witness_witness_witness_right_left','have hn : x5 = 0')
            +_call('beta_sum_zero','x2','x3','x5')+('exact h_witness_witness_witness_witness_witness_witness_right_right_left',
                'have hzero : (z = 0 -> x4 = x5) /\\ (x4 = x5 -> z = 0)')
            +_call('signed_balance_zero_iff','z','x4','x5')
            +('exact h_witness_witness_witness_witness_witness_witness_right_right_right','cases hzero','apply hzero_right','trans 0','exact hp','symm','exact hn'),
            'The empty signed prefix sum is exactly canonical zero, regardless of the packed component streams.',
        ),
        spec(
            'divisor_signed_sum_empty_exists',
            f"forall F {' '.join(a)}. ({_rep('F',*a,'empty_rep')}) -> ({_signed_sum('F','0','0','empty_result')})",
            ('divisor_signed_sum_exists_from_components','divisor_signed_sum_empty_value'),
            _intro('F',*a,'hrep')+(f"have hz : exists z. ({_signed_sum('F','0','z','empty_constructed')})",)
            +_call('divisor_signed_sum_exists_from_components','F',*a,'0')+('exact hrep','cases hz','have heq : x = 0')
            +_call('divisor_signed_sum_empty_value','F','x')+('exact hz_witness',)
            +_rewrite('heq',_signed_sum('F','0','x','empty_transport'),'x','hz_witness')+('exact hz_witness',),
            'The empty sum is constructed as an actual two-trace signed fold and only then identified with zero.',
        ),
    )


def make_divisor_sum_table_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _pack_rows(spec)+_table_rows(spec)+_sum_rows(spec)


__all__ = [
    'signed_arithmetic_table_representation_relation','signed_arithmetic_table_relation',
    'signed_arithmetic_table_entry_relation','signed_arithmetic_prefix_sum_relation',
    'signed_arithmetic_table_equality_relation','make_divisor_sum_table_candidate_theorems',
]
