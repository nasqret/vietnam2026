"""Finite, complete selector coding for actual rectangular rank searches.

Beta codes are not unique and their raw code parameters are unbounded.
Searching an arbitrary fixed box would therefore omit genuine minors.
These object-level HA proofs construct a uniform finite box which recodes
*every* bounded finite prefix, using CRT and a fixed common multiple.
Nothing in this authoring module confers release admission or proof authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_omission_candidate import _bounded_into_term
from .matrix_recursive_determinant_candidate import (
    _and, _apply, _arguments as _determinant_arguments, _at, _cases, _exists, _intro, _le, _lt,
    _names, _part, _parts, _prefix, _rewrite_all, _safe,
)


def _arguments(*values: str) -> tuple[str, ...]:
    result = _determinant_arguments(*values)
    if any(value.startswith('fom_') for value in result):
        raise ValueError('rank argument captures an inherited finite-omission binder')
    return result


def _bounded(b: str, c: str, length: str, bound: str, tag: str) -> str:
    return _bounded_into_term(b,c,length,bound,tag=f'mrf_{tag}',avoid=())


def _common(c: str, length: str, tag: str) -> str:
    t,h,q = _names(tag,'t','h','q')
    return f'forall {t}. (exists {h}. S {t} + S {h} = S ({length})) -> exists {q}. {c} = S {t} * {q}'


def _div(divisor: str, number: str, tag: str) -> str:
    q, = _names(tag,'q')
    return f'exists {q}. {number} = ({divisor}) * {q}'


def _mod(modulus: str, a: str, b: str, tag: str) -> str:
    u,v = _names(tag,'u','v')
    return f'exists {u} {v}. ({a}) + ({modulus}) * {u} = ({b}) + ({modulus}) * {v}'


def _moduli_divide(T: str, c: str, length: str, tag: str) -> str:
    i, = _names(tag,'i')
    return f'forall {i}. ({_lt(i,length,tag+"i")}) -> ({_div(f"S ((S ({i})) * ({c}))",T,tag+"d")})'


def _congruences(b: str, e: str, z: str, c: str, length: str, tag: str) -> str:
    i,a = _names(tag,'i','a')
    return (
        f'forall {i} {a}. ({_lt(i,length,tag+"i")}) -> '
        f'({_at(b,e,i,a,tag+"a")}) -> ({_mod(f"S ((S ({i})) * ({c}))",z,a,tag+"m")})'
    )


def _invariant(N: str, c: str, b: str, e: str, k: str, P: str, z: str, tag: str) -> str:
    j,d = _names(tag,'j','d')
    coprime = (
        f'forall {j}. ({_le(k,j,tag+"low")}) -> ({_le(j,N,tag+"high")}) -> forall {d}. '
        f'({_div(d,P,tag+"factor")}) -> ({_div(d,f"S ((S ({j})) * ({c}))",tag+"mod")}) -> {d} = 1'
    )
    return _and(f'~({P} = 0)',_moduli_divide(P,c,k,tag+'div'),_congruences(b,e,z,c,k,tag+'cong'),coprime)


def _box(c: str, T: str, length: str, bound: str, tag: str) -> str:
    b,e,z = _names(tag,'b','e','z')
    result = _and(_lt(z,T,tag+'bound'),_prefix(b,e,z,c,length,tag+'prefix'))
    return _and(f'~({T} = 0)',f'forall {b} {e}. ({_bounded(b,e,length,bound,tag+"source")}) -> exists {z}. ({result})')


def uniform_beta_prefix_box_relation(c: str, T: str, length: str, bound: str, *, tag: str) -> str:
    """One fixed scale and finite code bound represent every bounded prefix."""
    return _box(*_arguments(c,T,length,bound),_safe(tag))


def _injective(b: str, c: str, length: str, tag: str) -> str:
    i,j,a = _names(tag,'i','j','a')
    return (
        f'forall {i} {j} {a}. ({_lt(i,length,tag+"i")}) -> ({_lt(j,length,tag+"j")}) -> '
        f'({_at(b,c,i,a,tag+"first")}) -> ({_at(b,c,j,a,tag+"second")}) -> {i} = {j}'
    )


def _collision(b: str, c: str, length: str, tag: str) -> str:
    i,j,a = _names(tag,'i','j','a')
    return f'exists {i} {j} {a}. '+_and(
        _lt(i,length,tag+'i'),_lt(j,length,tag+'j'),f'~({i} = {j})',
        _at(b,c,i,a,tag+'first'),_at(b,c,j,a,tag+'second'),
    )


def _selector(b: str, c: str, length: str, bound: str, tag: str) -> str:
    return _and(_bounded(b,c,length,bound,tag+'bound'),_injective(b,c,length,tag+'distinct'))


def finite_matrix_selector_relation(b: str, c: str, length: str, bound: str, *, tag: str) -> str:
    """A finite list of distinct, genuinely in-range matrix coordinates."""
    return _selector(*_arguments(b,c,length,bound),_safe(tag))


def make_matrix_rank_finite_coding_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    inv_h = 'hinv_witness_witness'
    return (
        spec(
            'matrix_rank_bounded_prefix_value',
            f"forall b c l B i a. ({_bounded('b','c','l','B','value_source')}) -> ({_lt('i','l','value_index')}) -> "
            f"({_at('b','c','i','a','value_entry')}) -> ({_lt('a','B','value_bound')})",
            ('beta_at_unique',),
            _intro('b','c','l','B','i','a','hbounded','hi','ha')
            +(f"have hentry : exists v. {_and(_at('b','c','i','v','bounded_entry'),_lt('v','B','bounded_value'))}",)
            +_apply('hbounded','i')+('exact hi','cases hentry','cases hentry_witness','have heq : a = x')
            +_apply('beta_at_unique','b','c','i','a','x')+('exact ha','exact hentry_witness_left','rewrite heq','exact hentry_witness_right'),
            'The finite bounded-into witness bounds every actual decoded value, by beta uniqueness.',
        ),
        spec(
            'matrix_rank_common_multiple_divides',
            f"forall T B t. ({_common('T','B','common_source')}) -> ({_lt('t','B','factor_bound')}) -> ({_div('S t','T','factor_result')})",
            ('add_comm',),
            _intro('T','B','t','hcommon','ht')+('cases ht',)
            +_apply('hcommon','t')+('exists x','rewrite PA4','have hsum : S t + x = x + S t','apply add_comm','rewrite hsum','rewrite ht_witness','refl'),
            'A common multiple contains each explicitly bounded positive natural divisor, with the exact legacy bound convention.',
        ),
        spec(
            'matrix_rank_beta_moduli_common_multiple',
            f"forall k c T. ({_common('T','S (k * c)','moduli_source')}) -> ({_moduli_divide('T','c','k','moduli_result')})",
            ('matrix_rank_common_multiple_divides','succ_le_succ','mul_le_mul_right'),
            _intro('k','c','T','hcommon','i','hi')
            +_apply('matrix_rank_common_multiple_divides','T','S (k * c)','(S i) * c')+('exact hcommon',)
            +_apply('succ_le_succ','(S i) * c','k * c')+_apply('mul_le_mul_right','S i','k','c')+('exact hi',),
            'One fixed positive common multiple is divisible by all beta moduli in a finite selector prefix.',
        ),
        spec(
            'matrix_rank_recode_congruences_exists',
            f"forall k c b e. ({_common('c','k','recode_common')}) -> exists z. ({_congruences('b','e','z','c','k','recode_result')})",
            ('bounded_beta_exclusive_recode_invariant','le_refl'),
            _intro('k','c','b','e','hcommon')
            +(f"have hall : forall n. ({_le('n','k','invariant_bound')}) -> exists P z. ({_invariant('k','c','b','e','n','P','z','all_invariant')})",)
            +_apply('bounded_beta_exclusive_recode_invariant','k','c','b','e')+('exact hcommon',)
            +(f"have hinv : exists P z. ({_invariant('k','c','b','e','k','P','z','terminal_invariant')})",)
            +_apply('hall','k')+_apply('le_refl','k')+_cases('hinv',2)+_parts(inv_h,4)
            +('exists x1',f"exact {_part(inv_h,4,2)}"),
            'Existing constructive CRT recoding yields all finite congruences at a fixed common-multiple scale; no selector-code bound is assumed.',
        ),
        spec(
            'matrix_rank_bounded_recode_in_fixed_box',
            f"forall k B c T b e. ({_le('B','c','fixed_scale')}) -> ({_common('c','k','fixed_common')}) -> ~(T = 0) -> "
            f"({_moduli_divide('T','c','k','fixed_divides')}) -> ({_bounded('b','e','k','B','fixed_source')}) -> "
            f"exists z. ({_and(_lt('z','T','fixed_result_bound'),_prefix('b','e','z','c','k','fixed_result_prefix'))})",
            ('matrix_rank_recode_congruences_exists','division_remainder_exists','mul_comm',
             'remainder_decomposition_to_mod_eq','matrix_rank_bounded_prefix_value','base_le_beta_modulus',
             'le_trans','lt_of_lt_of_le','mod_eq_of_mod_eq_multiple','mod_eq_symm','mod_eq_trans','beta_at_of_mod_eq_bound'),
            _intro('k','B','c','T','b','e','hscale','hcommon','hT','hmoduli','hbounded')
            +(f"have hcodes : exists z. ({_congruences('b','e','z','c','k','fixed_crt')})",)
            +_apply('matrix_rank_recode_congruences_exists','k','c','b','e')+('exact hcommon','cases hcodes')
            +(f"have hdivision : exists q r. x = T * q + r /\\ ({_lt('r','T','division_bound')})",)
            +_apply('division_remainder_exists','T','x')+('exact hT',)+_cases('hdivision',2)+('cases hdivision_witness_witness',)
            +('have hcommute : T * x1 = x1 * T','apply mul_comm','rewrite hcommute at hdivision_witness_witness_left')
            +(f"have hremainder : {_mod('T','x','x2','fixed_remainder')}",)
            +_apply('remainder_decomposition_to_mod_eq','T','x','x1','x2')+('exact hdivision_witness_witness_left','exists x2','split','exact hdivision_witness_witness_right')
            +_intro('i','a','hi','ha')
            +(f"have hvalue : {_lt('a','B','fixed_value_bound')}",)
            +_apply('matrix_rank_bounded_prefix_value','b','e','k','B','i','a')+('exact hbounded','exact hi','exact ha')
            +(f"have hmodbound : {_le('B','S ((S i) * c)','fixed_mod_bound')}",)
            +_apply('le_trans','B','c','S ((S i) * c)')+('exact hscale',)+_apply('base_le_beta_modulus','c','i')
            +_apply('beta_at_of_mod_eq_bound','x2','c','i','a')
            +_apply('lt_of_lt_of_le','a','B','S ((S i) * c)')+('exact hvalue','exact hmodbound')
            +_apply('mod_eq_trans','S ((S i) * c)','x2','x','a')
            +_apply('mod_eq_symm','S ((S i) * c)','x','x2')
            +_apply('mod_eq_of_mod_eq_multiple','S ((S i) * c)','T','x','x2')
            +_apply('hmoduli','i')+('exact hi','exact hremainder')+_apply('hcodes_witness','i','a')+('exact hi','exact ha'),
            'Reducing a genuine CRT recoding modulo a fixed common multiple gives a strictly bounded code with every finite source value preserved.',
        ),
        spec(
            'matrix_rank_uniform_beta_prefix_box_exists',
            f"forall k B. exists c T. ({_box('c','T','k','B','uniform_box')})",
            ('bounded_common_multiple_exists','scaled_bounded_common_multiple','le_scaled_nonzero',
             'matrix_rank_beta_moduli_common_multiple','matrix_rank_bounded_recode_in_fixed_box'),
            _intro('k','B')
            +(f"have hC : exists C. {_and('~(C = 0)',_common('C','k','uniform_common'))}",)
            +_apply('bounded_common_multiple_exists','k')+('cases hC','cases hC_witness')
            +(f"have hscalecommon : {_common('x * B','k','scaled_common')}",)
            +_apply('scaled_bounded_common_multiple','k','x','B')+('exact hC_witness_right',)
            +(f"have hscale : {_le('B','x * B','uniform_scale')}",)
            +_apply('le_scaled_nonzero','x','B')+('exact hC_witness_left',)
            +(f"have hT : exists T. {_and('~(T = 0)',_common('T','S (k * (x * B))','uniform_moduli'))}",)
            +_apply('bounded_common_multiple_exists','S (k * (x * B))')+('cases hT','cases hT_witness')
            +_exists('x * B','x1')+('split','exact hT_witness_left')+_intro('b','e','hbounded')
            +_apply('matrix_rank_bounded_recode_in_fixed_box','k','B','x * B','x1','b','e')
            +('exact hscale','exact hscalecommon','exact hT_witness_left')
            +_apply('matrix_rank_beta_moduli_common_multiple','k','x * B','x1')+('exact hT_witness_right','exact hbounded'),
            'Unconditionally construct one fixed scale and one positive finite code bound representing every bounded prefix of the requested length.',
        ),
        spec(
            'matrix_rank_no_index_below_zero',
            f"forall i. ~({_lt('i','0','no_index')})",
            ('le_zero','succ_ne_zero'),
            _intro('i','hi')+('have hzero : S i = 0',)+_apply('le_zero','S i')+('exact hi',)
            +_apply('succ_ne_zero','i')+('exact hzero',),
            'The empty finite domain has no index, by natural successor nonzeroness.',
        ),
        spec(
            'matrix_rank_prefix_equality_symmetric',
            f"forall b c u v l. ({_prefix('b','c','u','v','l','symmetric_source')}) -> ({_prefix('u','v','b','c','l','symmetric_result')})",
            ('beta_at_exists','beta_at_unique'),
            _intro('b','c','u','v','l','hprefix','i','a','hi','ha')
            +(f"have hvalue : exists z. {_at('b','c','i','z','reverse_value')}",)
            +_apply('beta_at_exists','b','c','i')+('cases hvalue','have heq : a = x')
            +_apply('beta_at_unique','u','v','i','a','x')+('exact ha',)+_apply('hprefix','i','x')+('exact hi','exact hvalue_witness')
            +_rewrite_all('heq','a',_at('b','c','i','a','reverse_output'))+('exact hvalue_witness',),
            'Finite beta-prefix equality is symmetric because beta decoding is total and functional.',
        ),
        spec(
            'matrix_rank_bounded_prefix_transport',
            f"forall b c u v l B. ({_prefix('b','c','u','v','l','bounded_transport')}) -> "
            f"({_bounded('b','c','l','B','bounded_source')}) -> ({_bounded('u','v','l','B','bounded_target')})",
            (),
            _intro('b','c','u','v','l','B','hprefix','hbounded','i','hi')
            +(f"have hentry : exists a. {_and(_at('b','c','i','a','transport_source_entry'),_lt('a','B','transport_source_bound'))}",)
            +_apply('hbounded','i')+('exact hi','cases hentry','cases hentry_witness','exists x','split')
            +_apply('hprefix','i','x')+('exact hi','exact hentry_witness_left','exact hentry_witness_right'),
            'Finite selector value bounds transport across actual pointwise equality of their code prefixes.',
        ),
        spec(
            'matrix_rank_injective_prefix_transport',
            f"forall b c u v l. ({_prefix('b','c','u','v','l','injective_transport')}) -> "
            f"({_injective('b','c','l','injective_source')}) -> ({_injective('u','v','l','injective_target')})",
            ('matrix_rank_prefix_equality_symmetric',),
            _intro('b','c','u','v','l','hprefix','hinjective')
            +(f"have hreverse : {_prefix('u','v','b','c','l','reverse_injective')}",)
            +_apply('matrix_rank_prefix_equality_symmetric','b','c','u','v','l')+('exact hprefix',)
            +_intro('i','j','a','hi','hj','ha','hb')+_apply('hinjective','i','j','a')+('exact hi','exact hj')
            +_apply('hreverse','i','a')+('exact hi','exact ha')+_apply('hreverse','j','a')+('exact hj','exact hb'),
            'A recoded finite selector remains genuinely injective; code equality is not assumed.',
        ),
        spec(
            'matrix_rank_injective_prefix_decidable',
            f"forall b c l. ({_injective('b','c','l','injective_yes')}) \\/ ~({_injective('b','c','l','injective_no')})",
            ('finite_prefix_collision_or_injective',),
            _intro('b','c','l')
            +(f"have hdecision : ({_collision('b','c','l','collision_witness')}) \\/ ({_injective('b','c','l','injectivity_witness')})",)
            +_apply('finite_prefix_collision_or_injective','b','c','l')+('cases hdecision','right','intro hinjective')
            +_cases('hdecision_left',3)+_parts('hdecision_left_witness_witness_witness',5)
            +(f"apply {_part('hdecision_left_witness_witness_witness',5,2)}",)
            +_apply('hinjective','x','x1','x2')
            +tuple(f"exact {_part('hdecision_left_witness_witness_witness',5,i)}" for i in (0,1,3,4))
            +('left','exact hdecision_right'),
            'Selector injectivity is constructively decidable using the existing witnessed-collision theorem.',
        ),
        spec(
            'matrix_rank_bounded_prefix_empty',
            f"forall b c B. ({_bounded('b','c','0','B','empty_bounded')})",
            ('matrix_rank_no_index_below_zero',),
            _intro('b','c','B','i','hi')+('exfalso',)+_apply('matrix_rank_no_index_below_zero','i')+('exact hi',),
            'Every beta code describes the empty bounded selector prefix.',
        ),
        spec(
            'matrix_rank_bounded_prefix_drop_last',
            f"forall b c l B. ({_bounded('b','c','S l','B','drop_source')}) -> ({_bounded('b','c','l','B','drop_result')})",
            ('le_succ',),
            _intro('b','c','l','B','hbounded','i','hi')+_apply('hbounded','i')+_apply('le_succ','S i','l')+('exact hi',),
            'Deleting the last index preserves a finite selector value bound.',
        ),
        spec(
            'matrix_rank_bounded_prefix_extend',
            f"forall b c l B a. ({_bounded('b','c','l','B','extend_source')}) -> ({_at('b','c','l','a','extend_entry')}) -> "
            f"({_lt('a','B','extend_bound')}) -> ({_bounded('b','c','S l','B','extend_result')})",
            ('finite_lt_succ_eq_or_lt',),
            _intro('b','c','l','B','a','hbounded','ha','habound','i','hi')
            +(f"have hcase : i = l \\/ ({_lt('i','l','extend_index')})",)
            +_apply('finite_lt_succ_eq_or_lt','l','i')+('exact hi','cases hcase','exists a','split')
            +_rewrite_all('hcase_left','i',_at('b','c','i','a','extend_last'))+('exact ha','exact habound')
            +_apply('hbounded','i')+('exact hcase_right',),
            'A checked final decoded value extends an existing bounded selector prefix.',
        ),
        spec(
            'matrix_rank_bounded_prefix_decidable',
            f"forall b c l B. ({_bounded('b','c','l','B','bounded_yes')}) \\/ ~({_bounded('b','c','l','B','bounded_no')})",
            ('matrix_rank_bounded_prefix_empty','matrix_rank_bounded_prefix_drop_last','matrix_rank_bounded_prefix_extend',
             'beta_at_exists','le_or_lt','le_refl','matrix_rank_bounded_prefix_value','lt_not_le'),
            _intro('b','c')+('induction l','intro B','left')+_apply('matrix_rank_bounded_prefix_empty','b','c','B')
            +('intro B',f"have hprevious : ({_bounded('b','c','l','B','decision_previous')}) \\/ ~({_bounded('b','c','l','B','decision_absent')})")
            +_apply('IH','B')+('cases hprevious',f"have hlast : exists a. {_at('b','c','l','a','decision_last')}")
            +_apply('beta_at_exists','b','c','l')+('cases hlast',)
            +(f"have horder : ({_le('B','x','last_too_large')}) \\/ ({_lt('x','B','last_small')})",)
            +_apply('le_or_lt','B','x')+('cases horder','right','intro hfull')
            +(f"have hcontradiction : {_lt('x','B','contradiction_bound')}",)
            +_apply('matrix_rank_bounded_prefix_value','b','c','S l','B','l','x')+('exact hfull',)
            +_apply('le_refl','S l')+('exact hlast_witness',)+_apply('lt_not_le','x','B')+('exact hcontradiction','exact horder_left')
            +('left',)+_apply('matrix_rank_bounded_prefix_extend','b','c','l','B','x')+('exact hprevious_left','exact hlast_witness','exact horder_right')
            +('right','intro hfull','apply hprevious_right')+_apply('matrix_rank_bounded_prefix_drop_last','b','c','l','B')+('exact hfull',),
            'Actual finite prefix value bounds are decidable by HA induction and comparison of each decoded entry, without an unbounded-existential decision axiom.',
        ),
        spec(
            'matrix_rank_selector_transport',
            f"forall b c u v l B. ({_prefix('b','c','u','v','l','selector_transport')}) -> "
            f"({_selector('b','c','l','B','selector_source')}) -> ({_selector('u','v','l','B','selector_target')})",
            ('matrix_rank_bounded_prefix_transport','matrix_rank_injective_prefix_transport'),
            _intro('b','c','u','v','l','B','hprefix','hselector')+('cases hselector','split')
            +_apply('matrix_rank_bounded_prefix_transport','b','c','u','v','l','B')+('exact hprefix','exact hselector_left')
            +_apply('matrix_rank_injective_prefix_transport','b','c','u','v','l')+('exact hprefix','exact hselector_right'),
            'Both in-range coordinates and distinctness survive the complete finite selector recoding.',
        ),
        spec(
            'matrix_rank_selector_decidable',
            f"forall b c l B. ({_selector('b','c','l','B','selector_yes')}) \\/ ~({_selector('b','c','l','B','selector_no')})",
            ('matrix_rank_bounded_prefix_decidable','matrix_rank_injective_prefix_decidable'),
            _intro('b','c','l','B')
            +(f"have hbound : ({_bounded('b','c','l','B','select_bound_yes')}) \\/ ~({_bounded('b','c','l','B','select_bound_no')})",)
            +_apply('matrix_rank_bounded_prefix_decidable','b','c','l','B')+('cases hbound',)
            +(f"have hinjective : ({_injective('b','c','l','select_inj_yes')}) \\/ ~({_injective('b','c','l','select_inj_no')})",)
            +_apply('matrix_rank_injective_prefix_decidable','b','c','l')+('cases hinjective','left','split','exact hbound_left','exact hinjective_left')
            +('right','intro hselector','cases hselector','apply hinjective_right','exact hselector_right')
            +('right','intro hselector','cases hselector','apply hbound_right','exact hselector_left'),
            'A genuine finite matrix-selector relation, including every index bound and pairwise distinctness condition, is decidable.',
        ),
        spec(
            'matrix_rank_selector_dimension_bound',
            f"forall b c l B. ({_selector('b','c','l','B','selector_dimension')}) -> ({_le('l','B','selector_size')})",
            ('le_or_lt','finite_bounded_into_oversized_not_injective'),
            _intro('b','c','l','B','hselector')+('cases hselector',)
            +(f"have horder : ({_le('l','B','size_possible')}) \\/ ({_lt('B','l','size_impossible')})",)
            +_apply('le_or_lt','l','B')+('cases horder','exact horder_left','exfalso')
            +_apply('finite_bounded_into_oversized_not_injective','b','c','l','B')
            +('exact hselector_left','exact horder_right','exact hselector_right'),
            'Every actual distinct selector has length at most its matrix-coordinate bound, by constructive finite pigeonhole.',
        ),
        spec(
            'matrix_rank_selector_empty',
            f"forall b c B. ({_selector('b','c','0','B','selector_empty')})",
            ('matrix_rank_bounded_prefix_empty','matrix_rank_no_index_below_zero'),
            _intro('b','c','B')+('split',)+_apply('matrix_rank_bounded_prefix_empty','b','c','B')
            +_intro('i','j','a','hi','hj','ha','hb')+('exfalso',)+_apply('matrix_rank_no_index_below_zero','i')+('exact hi',),
            'The empty row or column selector is valid even when its ambient dimension is zero.',
        ),
    )


__all__ = ['uniform_beta_prefix_box_relation','finite_matrix_selector_relation','make_matrix_rank_finite_coding_candidate_theorems']
