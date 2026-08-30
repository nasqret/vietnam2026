"""A genuine finite native-beta map of rectangular index products.

For positive physical width V, decode i=V*d+e with e<V and store d*e.
No injectivity, target bound, signed value, or sum identity is a definition.
In particular, zero-coordinate images legitimately collide.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _intro, _lt, _preserve, _public, _rewrite,
)


def _map(V: str, L: str, r: str, s: str, tag: str) -> str:
    i,d,e = ('dpi_'+role+'_'+tag for role in ('index','row','column'))
    return _and(f'~(({V})=0)',
                f'forall {i} {d} {e}. ({_lt(i,L,tag+"window")}) -> '
                f'({_lt(e,V,tag+"remainder")}) -> ({i})=({V})*({d})+({e}) -> '
                f'({_at(r,s,i,f"({d})*({e})",tag+"value")})')


def divisor_pair_index_map_relation(V: str, L: str, r: str, s: str,
                                    *, tag: str, variables: tuple[str, ...]) -> str:
    """Positive width and actual native-beta values for every index i<L."""
    return _public(_map,(V,L,r,s),tag=tag,variables=variables)


def _construction_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    append = _intro('V','L','r','s','hm') + ('cases hm',)
    division = _and('L=V*d+e',_lt('e','V','dpi_append_remainder'))
    append += (f'have hcoords : exists d e. ({division})',)
    append += _call('division_remainder_exists','V','L') + ('exact hm_left',)
    append += _cases('hcoords',2) + ('cases hcoords_witness_witness',)
    extension = _and(_at('t','u','L','x*x1','dpi_append_last'),
                     _preserve('r','s','t','u','L','dpi_append_preserve'))
    append += (f'have hext : exists t u. ({extension})',)
    append += _call('beta_prefix_extend','L','r','s','x*x1')
    append += _cases('hext',2) + ('cases hext_witness_witness',)
    append += ('exists x2','exists x3','split','split','exact hm_left')
    append += _intro('i','d','e','hi','he','heq')
    append += (f'have hcase : i=L \\/ ({_lt("i","L","dpi_append_cases")})',)
    append += _call('finite_lt_succ_eq_or_lt','L','i') + ('exact hi','cases hcase',)
    append += ('have hnew : L=V*d+e','trans i','symm','exact hcase_left','exact heq',
               'have hsame : d=x /\\ e=x1')
    append += _call('division_remainder_unique','V','L','d','e','x','x1')
    append += ('exact hnew','exact he','exact hcoords_witness_witness_left',
               'exact hcoords_witness_witness_right','cases hsame')
    append += _rewrite('hcase_left',_at('x2','x3','i','d*e','dpi_rewrite_index'),'i')
    append += _rewrite('hsame_left',_at('x2','x3','L','d*e','dpi_rewrite_row'),'d')
    append += _rewrite('hsame_right',_at('x2','x3','L','x*e','dpi_rewrite_column'),'e')
    append += ('exact hext_witness_witness_left',)
    append += _call('hext_witness_witness_right','i','d*e') + ('exact hcase_right',)
    append += _call('hm_right','i','d','e') + ('exact hcase_right','exact he','exact heq',
                                           'exact hext_witness_witness_right')

    exists = _intro('V','L') + ('induction L',) + _intro('hV')
    exists += ('exists 0','exists 0','split','exact hV') + _intro('i','d','e','hi','he','heq')
    exists += ('exfalso',) + _call('factor_permutation_below_zero_impossible','i') + ('exact hi',)
    exists += _intro('hV')
    exists += (f'have hp : exists r s. ({_map("V","L","r","s","dpi_previous")})','apply IH','exact hV')
    exists += _cases('hp',2)
    output = _and(_map('V','S L','t','u','dpi_next'),_preserve('x','x1','t','u','L','dpi_next_preserve'))
    exists += (f'have he : exists t u. ({output})',)
    exists += _call('divisor_pair_index_map_append','V','L','x','x1') + ('exact hp_witness_witness',)
    exists += _cases('he',2) + ('cases he_witness_witness','exists x2','exists x3','exact he_witness_witness_left')

    return (
        spec('divisor_pair_index_map_append',
             f'forall V L r s. ({_map("V","L","r","s","dpi_append_source")}) -> exists t u. '
             + _and(_map('V','S L','t','u','dpi_append_target'),
                    _preserve('r','s','t','u','L','dpi_append_old_entries')),
             ('division_remainder_exists','beta_prefix_extend','finite_lt_succ_eq_or_lt','division_remainder_unique'),
             append,
             'Actual bounded quotient and remainder determine the next product value; beta-prefix extension constructs new codes and preserves all earlier decoded entries.'),
        spec('divisor_pair_index_map_exists',
             f'forall V L. ~(V=0) -> exists r s. ({_map("V","L","r","s","dpi_exists_result")})',
             ('factor_permutation_below_zero_impossible','divisor_pair_index_map_append'), exists,
             'Finite HA induction constructs a native-beta pair-product map for every positive width and finite window, including the empty window.'),
    )


def _lookup_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    lookup = _intro('V','L','r','s','i','d','e','hm','hi','he','heq') + ('cases hm',)
    lookup += _call('hm_right','i','d','e') + ('exact hi','exact he','exact heq')
    value = _intro('V','L','r','s','i','d','e','z','hm','hi','he','heq','hz')
    value += _call('beta_at_unique','r','s','i','z','d*e') + ('exact hz',)
    value += _call('divisor_pair_index_map_lookup','V','L','r','s','i','d','e')
    value += ('exact hm','exact hi','exact he','exact heq')
    return (
        spec('divisor_pair_index_map_lookup',
             f'forall V L r s i d e. ({_map("V","L","r","s","dpi_lookup_map")}) -> '
             f'({_lt("i","L","dpi_lookup_index")}) -> ({_lt("e","V","dpi_lookup_column")}) -> '
             f'i=V*d+e -> ({_at("r","s","i","d*e","dpi_lookup_result")})',
             (), lookup,
             'At supplied genuine row and bounded column coordinates, the actual beta code stores their product.'),
        spec('divisor_pair_index_map_value',
             f'forall V L r s i d e z. ({_map("V","L","r","s","dpi_value_map")}) -> '
             f'({_lt("i","L","dpi_value_index")}) -> ({_lt("e","V","dpi_value_column")}) -> '
             f'i=V*d+e -> ({_at("r","s","i","z","dpi_value_entry")}) -> z=d*e',
             ('beta_at_unique','divisor_pair_index_map_lookup'), value,
             'Any decoded value at a certified coordinate equals the actual coordinate product; equality of beta-code components is not asserted.'),
    )


def make_divisor_pair_index_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _construction_rows(spec) + _lookup_rows(spec)


__all__ = ['divisor_pair_index_map_relation','make_divisor_pair_index_candidate_theorems']
