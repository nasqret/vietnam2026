"""Actual natural solution classes of linear congruences: unadmitted scripts.

The modulus quotient is an explicit natural cofactor, never a division
primitive.  Counting means a proved bijection with t<g, not an assumed finite
list or cardinality oracle.  Modulus zero has separate equality contracts.
"""
from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_canonical_gcd_candidate import is_gcd
from peano_lab.library.ha_generalized_crt_congruence_candidate import balanced_mod_eq
from peano_lab.library.ha_modular_inverse_candidate import coprime
from peano_lab.library.fermat_endpoints_candidate import make_fermat_endpoint_candidate_theorems


CONTEXT = ('a', 'm', 'g', 'A', 'M', 'b', 'r', 'x', 'y', 't', 'u', 'q',
           'x0', 'x1', 'x2', 'x3', 'x4')
BASE = ('a', 'm', 'g', 'A', 'M')


def _mod(m, a, b, tag):
    return balanced_mod_eq(m, a, b, tag='lcc_' + tag, variables=CONTEXT)


def _lt(a, b, tag):
    return f'exists lcc_gap_{tag}. lcc_gap_{tag}+S ({a})=({b})'


def _le(a, b, tag):
    return f'exists lcc_gap_{tag}. lcc_gap_{tag}+({a})=({b})'


def _and(*clauses):
    result = '(' + clauses[-1] + ')'
    for clause in reversed(clauses[:-1]):
        result = '((' + clause + ') /\\ (' + result + '))'
    return result


def _iff(a, b):
    return _and(f'({a}) -> ({b})', f'({b}) -> ({a})')


def _contract(parameters, premises, conclusion):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, conclusion))


def _intro(*names):
    return tuple('intro ' + name for name in names)


def _call(name, *terms):
    return tuple(f'specialize {name} ({term})' for term in terms) + ('apply ' + name,)


def _base(tag):
    return ('~(m=0)', is_gcd('g', 'a', 'm', tag='lcc_' + tag), 'a=g*A', 'm=g*M')


def _positive_cofactors():
    # Derived from the actual modulus equation, not assumed separately.
    return ('have hg0 : ~(g=0)', 'intro hz', 'apply hm0', 'trans g*M', 'exact hm',
            'rewrite hz', 'apply mul_zero_left',
            'have hM0 : ~(M=0)', 'intro hz', 'apply hm0', 'trans g*M', 'exact hm',
            'rewrite hz', 'simp')


def _cancel_row(spec):
    pars = BASE + ('x', 'y')
    left = _mod('m', 'a*x', 'a*y', 'cancel_left')
    right = _mod('M', 'x', 'y', 'cancel_right')
    body = _intro(*pars, 'hm0', 'hg', 'ha', 'hm') + _positive_cofactors()
    body += ('have hc : ' + coprime('A', 'M', tag='lcc_cancel_coprime'),)
    body += _call('is_gcd_quotients_coprime_nonzero', 'g', 'a', 'm', 'A', 'M')
    body += ('exact hg', 'exact hg0', 'exact ha', 'exact hm',
             'have hx : a*x=g*(A*x)', 'rewrite ha', 'apply mul_assoc',
             'have hy : a*y=g*(A*y)', 'rewrite ha', 'apply mul_assoc', 'split', 'intro h')
    body += _call('mod_eq_cancel_coprime', 'M', 'A', 'x', 'y') + ('exact hM0', 'exact hc')
    body += _call('mod_eq_unscale_nonzero', 'g', 'M', 'A*x', 'A*y')
    body += ('exact hg0', 'rewrite <- hm', 'rewrite <- hm', 'rewrite <- hx', 'rewrite <- hy', 'exact h',
             'intro h', 'rewrite hm', 'rewrite hm', 'rewrite hx', 'rewrite hy')
    body += _call('mod_eq_scale', 'g', 'M', 'A*x', 'A*y')
    body += _call('mod_eq_mul_left', 'M', 'x', 'y', 'A') + ('exact h',)
    return spec('mod_eq_cancel_gcd_cofactor', _contract(pars, _base('cancel'), _iff(left, right)),
        ('mul_zero_left', 'is_gcd_quotients_coprime_nonzero', 'mul_assoc',
         'mod_eq_cancel_coprime', 'mod_eq_unscale_nonzero', 'mod_eq_scale', 'mod_eq_mul_left'), body,
        'The actual quotient modulus m/g exactly classifies cancellation of a common coefficient at nonzero m.')


def _class_row(spec):
    pars = BASE + ('b', 'r', 'x')
    solution = _mod('m', 'a*x', 'b', 'class_solution')
    reference = _mod('m', 'a*r', 'b', 'class_reference')
    reduced = _mod('M', 'x', 'r', 'class_reduced')
    cancellation = _iff(_mod('m', 'a*x', 'a*r', 'class_pair'), reduced)
    body = _intro(*pars, 'hm0', 'hg', 'ha', 'hm', 'hr')
    body += ('have hc : ' + cancellation,) + _call('mod_eq_cancel_gcd_cofactor', *BASE, 'x', 'r')
    body += ('exact hm0', 'exact hg', 'exact ha', 'exact hm', 'cases hc', 'split', 'intro hx', 'apply hc_left')
    body += _call('mod_eq_trans', 'm', 'a*x', 'b', 'a*r') + ('exact hx',)
    body += _call('mod_eq_symm', 'm', 'a*r', 'b') + ('exact hr', 'intro hx')
    body += _call('mod_eq_trans', 'm', 'a*x', 'a*r', 'b')
    body += ('apply hc_right', 'exact hx', 'exact hr')
    return spec('linear_congruence_solution_class_iff_reduced_modulus',
        _contract(pars, (*_base('class'), reference), _iff(solution, reduced)),
        ('mod_eq_cancel_gcd_cofactor', 'mod_eq_trans', 'mod_eq_symm'), body,
        'Relative to any actual solution, every natural solution is exactly its class modulo the actual gcd cofactor.')


def _representative_row(spec):
    pars = BASE + ('b',)
    divides = 'exists lcc_bfactor. b=g*lcc_bfactor'
    result = 'exists r. ' + _and(_lt('r', 'M', 'representative_bound'), _mod('m', 'a*r', 'b', 'representative_solution'))
    body = _intro(*pars, 'hm0', 'hg', 'ha', 'hm', 'hb') + _positive_cofactors()
    body += ('have hs : exists x. ' + _mod('m', 'a*x', 'b', 'representative_original'),)
    body += _call('linear_congruence_gcd_divisibility_constructs_solution', 'a', 'm', 'b', 'g')
    body += ('exact hg', 'exact hb', 'cases hs',
             'have hd : exists q r. ' + _and('x=M*q+r', _lt('r', 'M', 'representative_division')),)
    body += _call('division_remainder_exists', 'M', 'x') + ('exact hM0', 'cases hd', 'cases hd_witness', 'cases hd_witness_witness',
             'exists x2', 'split', 'exact hd_witness_witness_right',
             'have he : ' + _mod('M', 'x2', 'x', 'representative_equal'),)
    body += _call('mod_eq_symm', 'M', 'x', 'x2')
    body += _call('remainder_decomposition_to_mod_eq', 'M', 'x', 'x1', 'x2')
    body += ('trans M*x1+x2', 'exact hd_witness_witness_left', 'congr', 'apply mul_comm', 'refl',
             'have hc : ' + _iff(_mod('m', 'a*x2', 'b', 'representative_target'), _mod('M', 'x2', 'x', 'representative_class')),)
    body += _call('linear_congruence_solution_class_iff_reduced_modulus', *BASE, 'b', 'x', 'x2')
    body += ('exact hm0', 'exact hg', 'exact ha', 'exact hm', 'exact hs_witness', 'cases hc', 'apply hc_right', 'exact he')
    return spec('linear_congruence_reduced_representative_exists', _contract(pars, (*_base('representative'), divides), result),
        ('mul_zero_left', 'linear_congruence_gcd_divisibility_constructs_solution', 'division_remainder_exists',
         'mod_eq_symm', 'remainder_decomposition_to_mod_eq', 'mul_comm', 'linear_congruence_solution_class_iff_reduced_modulus'), body,
        'Construct a genuine solution strictly below m/g, not merely below m, from the actual gcd divisibility witness.')


def _progression_bound_row(spec):
    pars = ('M', 'g', 'r', 't')
    small = _lt('r+M*t', 'g*M', 'progression_small')
    index = _lt('t', 'g', 'progression_index')
    body = _intro(*pars, 'hr') + ('split', 'intro hb',
        'have ho : (' + _le('g', 't', 'progression_order') + ') \\/ (' + index + ')',)
    body += _call('le_or_lt', 'g', 't') + ('cases ho', 'exfalso',)
    body += _call('lt_not_le', 'r+M*t', 'g*M') + ('exact hb',)
    body += _call('le_trans', 'g*M', 't*M', 'r+M*t')
    body += _call('mul_le_mul_right', 'g', 't', 'M') + ('exact ho_left',
        'have he : t*M=M*t', 'apply mul_comm', 'rewrite he')
    body += _call('le_add_left', 'M*t', 'r') + ('exact ho_right', 'intro ht',
        'have hs : ' + _lt('r+M*t', 'M+M*t', 'progression_next'),)
    body += _call('finite_add_lt_of_lt_of_le', 'r', 'M', 'M*t', 'M*t') + ('exact hr', 'apply le_refl',
        'have he : M+M*t=S t*M', 'trans M*t+M', 'apply add_comm',
        'trans t*M+M', 'congr', 'apply mul_comm', 'refl', 'symm', 'apply mul_succ_left')
    body += _call('lt_of_lt_of_le', 'r+M*t', 'M+M*t', 'g*M') + ('exact hs', 'rewrite he')
    body += _call('mul_le_mul_right', 'S t', 'g', 'M') + ('exact ht',)
    return spec('linear_congruence_progression_bound_iff', _contract(pars,
        (_lt('r', 'M', 'progression_remainder'),), _iff(small, index)),
        ('le_or_lt', 'lt_not_le', 'le_trans', 'mul_le_mul_right', 'mul_comm', 'le_add_left',
         'finite_add_lt_of_lt_of_le', 'le_refl', 'add_comm', 'mul_succ_left', 'lt_of_lt_of_le'), body,
        'With an actual remainder r<M, r+M*t is below g*M exactly when t<g; no field or coprimality hypothesis is used.')


def _parameter(g, M, r, x, tag):
    return 'exists t. ' + _and(_lt('t', g, tag + '_bound'), f'({x})=({r})+({M})*t')


def _residue_parameter_row(spec):
    pars = ('M', 'g', 'r', 'x')
    left = _and(_lt('x', 'g*M', 'residue_bound'), _mod('M', 'x', 'r', 'residue_mod'))
    right = _parameter('g', 'M', 'r', 'x', 'residue_parameter')
    body = _intro(*pars, 'hr') + ('have hM0 : ~(M=0)', 'intro hz',
        'have hbad : ' + _lt('r', '0', 'residue_bad'), 'rewrite <- hz', 'exact hr',
        'have hs : S r=0', 'specialize le_zero (S r)', 'apply le_zero', 'exact hbad',
        'specialize succ_ne_zero r', 'apply succ_ne_zero', 'exact hs',
        'split', 'intro h', 'cases h', 'have hq : exists q. x=q*M+r')
    body += _call('mod_eq_to_remainder_decomposition', 'M', 'x', 'r')
    body += ('exact hM0', 'exact hr', 'exact h_right', 'cases hq',
        'have he : x=r+M*x1', 'trans x1*M+r', 'exact hq_witness', 'trans r+x1*M', 'apply add_comm',
        'congr', 'refl', 'apply mul_comm', 'exists x1', 'split',
        'have hc : ' + _iff(_lt('r+M*x1', 'g*M', 'residue_forward'), _lt('x1', 'g', 'residue_forward_index')),)
    body += _call('linear_congruence_progression_bound_iff', 'M', 'g', 'r', 'x1')
    body += ('exact hr', 'cases hc', 'apply hc_left', 'rewrite <- he', 'exact h_left', 'exact he',
        'intro h', 'cases h', 'cases h_witness', 'split', 'rewrite h_witness_right',
        'have hc : ' + _iff(_lt('r+M*x1', 'g*M', 'residue_backward'), _lt('x1', 'g', 'residue_backward_index')),)
    body += _call('linear_congruence_progression_bound_iff', 'M', 'g', 'r', 'x1')
    body += ('exact hr', 'cases hc', 'apply hc_right', 'exact h_witness_left')
    body += _call('remainder_decomposition_to_mod_eq', 'M', 'x', 'x1', 'r')
    body += ('trans r+M*x1', 'exact h_witness_right', 'trans M*x1+r', 'apply add_comm',
        'congr', 'apply mul_comm', 'refl')
    return spec('linear_congruence_bounded_residue_parametrized', _contract(pars,
        (_lt('r', 'M', 'residue_reference'),), _iff(left, right)),
        ('le_zero', 'succ_ne_zero', 'mod_eq_to_remainder_decomposition', 'add_comm', 'mul_comm',
         'linear_congruence_progression_bound_iff', 'remainder_decomposition_to_mod_eq'), body,
        'Construct the exact interval parameter for every bounded member of a residue class, and conversely.')


def _parameter_unique_row(spec):
    pars = ('M', 'r', 'x', 't', 'u')
    body = _intro(*pars, 'hM', 'ht', 'hu')
    body += _call('mul_left_cancel_nonzero', 'M', 't', 'u') + ('exact hM',)
    body += _call('add_left_cancel', 'r', 'M*t', 'M*u') + ('trans x', 'symm', 'exact ht', 'exact hu')
    return spec('linear_congruence_bounded_parameter_unique', _contract(pars,
        ('~(M=0)', 'x=r+M*t', 'x=r+M*u'), 't=u'),
        ('mul_left_cancel_nonzero', 'add_left_cancel'), body,
        'The actual progression parameter is unique for nonzero M, even without imposing a redundant parameter bound.')


def _bounded_row(spec):
    pars = BASE + ('b', 'r', 'x')
    sol = _mod('m', 'a*x', 'b', 'bounded_sol')
    red = _mod('M', 'x', 'r', 'bounded_red')
    left = _and(_lt('x', 'm', 'bounded_x'), sol)
    right = _parameter('g', 'M', 'r', 'x', 'bounded_parameter')
    body = _intro(*pars, 'hm0', 'hg', 'ha', 'hm', 'hr', 'hs')
    body += ('have hc : ' + _iff(sol, red),) + _call('linear_congruence_solution_class_iff_reduced_modulus', *BASE, 'b', 'r', 'x')
    body += ('exact hm0', 'exact hg', 'exact ha', 'exact hm', 'exact hs', 'cases hc',
        'have hp : ' + _iff(_and(_lt('x', 'g*M', 'bounded_p'), red), right),)
    body += _call('linear_congruence_bounded_residue_parametrized', 'M', 'g', 'r', 'x')
    body += ('exact hr', 'cases hp', 'split', 'intro h', 'cases h', 'apply hp_left', 'split',
        'rewrite <- hm', 'exact h_left', 'apply hc_left', 'exact h_right', 'intro h',
        'have he : ' + _and(_lt('x', 'g*M', 'bounded_back'), red),
        'apply hp_right', 'exact h', 'cases he', 'split', 'rewrite hm', 'exact he_left', 'apply hc_right', 'exact he_right')
    return spec('linear_congruence_bounded_solutions_parametrized', _contract(pars,
        (*_base('bounded'), _lt('r', 'M', 'bounded_r'), _mod('m', 'a*r', 'b', 'bounded_reference')), _iff(left, right)),
        ('linear_congruence_solution_class_iff_reduced_modulus', 'linear_congruence_bounded_residue_parametrized'), body,
        'All solutions below the original nonzero modulus are exactly r+M*t for t<g, for an actual reduced representative r.')


def _enumeration(r, tag):
    classification = 'forall x. ' + _iff(_and(_lt('x', 'm', tag + '_x'),
        _mod('m', 'a*x', 'b', tag + '_solution')), _parameter('g', 'M', r, 'x', tag + '_param'))
    injective = 'forall t u. (' + _lt('t', 'g', tag + '_t') + ') -> (' + _lt('u', 'g', tag + '_u') + \
        f') -> (({r})+M*t=({r})+M*u) -> t=u'
    return _and(_lt(r, 'M', tag + '_r'), _mod('m', f'a*({r})', 'b', tag + '_reference'), classification, injective)


def _enumeration_row(spec):
    pars = BASE + ('b',)
    result = 'exists r. ' + _enumeration('r', 'enumeration')
    body = _intro(*pars, 'hm0', 'hg', 'ha', 'hm', 'hb') + _positive_cofactors()
    body += ('have hr : exists r. ' + _and(_lt('r', 'M', 'enum_constructed'), _mod('m', 'a*r', 'b', 'enum_sol')),)
    body += _call('linear_congruence_reduced_representative_exists', *BASE, 'b')
    body += ('exact hm0', 'exact hg', 'exact ha', 'exact hm', 'exact hb', 'cases hr', 'cases hr_witness',
        'exists x', 'split', 'exact hr_witness_left', 'split', 'exact hr_witness_right', 'split', 'intro y')
    body += _call('linear_congruence_bounded_solutions_parametrized', *BASE, 'b', 'x', 'y')
    body += ('exact hm0', 'exact hg', 'exact ha', 'exact hm', 'exact hr_witness_left', 'exact hr_witness_right',
        'intro t', 'intro u', 'intro ht', 'intro hu', 'intro he')
    body += _call('linear_congruence_bounded_parameter_unique', 'M', 'x', 'x+M*t', 't', 'u')
    body += ('exact hM0', 'refl', 'exact he')
    return spec('linear_congruence_exact_bounded_enumeration_exists', _contract(pars,
        (*_base('enumeration'), 'exists lcc_enum_bfactor. b=g*lcc_enum_bfactor'), result),
        ('mul_zero_left', 'linear_congruence_reduced_representative_exists',
         'linear_congruence_bounded_solutions_parametrized', 'linear_congruence_bounded_parameter_unique'), body,
        'Construct r and an actual bijection from t<g to all solutions x<m. This is a cardinality witness, not a claimed beta-coded list.')


def _zero_unique_row(spec):
    pars = ('a', 'b', 'x', 'y')
    body = _intro(*pars, 'ha', 'hx', 'hy')
    for variable, hypothesis in (('x', 'hx'), ('y', 'hy')):
        body += ('have he_' + variable + ' : ' + _iff(_mod('0', 'a*'+variable, 'b', 'zero_'+variable), 'a*'+variable+'=b'),)
        body += _call('mod_eq_zero_iff_eq', 'a*'+variable, 'b')
        body += ('cases he_' + variable, 'have h' + variable + 'eq : a*'+variable+'=b',
                 'apply he_' + variable + '_left', 'exact ' + hypothesis)
    body += _call('mul_left_cancel_nonzero', 'a', 'x', 'y') + ('exact ha', 'trans b', 'exact hxeq', 'symm', 'exact hyeq')
    return spec('linear_congruence_zero_modulus_nonzero_coefficient_unique', _contract(pars,
        ('~(a=0)', _mod('0', 'a*x', 'b', 'zero_unique_x'), _mod('0', 'a*y', 'b', 'zero_unique_y')), 'x=y'),
        ('mod_eq_zero_iff_eq', 'mul_left_cancel_nonzero'), body,
        'At modulus zero a nonzero coefficient has at most one natural solution; no bounded residue or finite-class formula is asserted.')


def _zero_coefficient_row(spec):
    left = _mod('0', '0*x', 'b', 'zero_coefficient')
    body = _intro('b', 'x') + ('have h0 : 0*x=0', 'apply mul_zero_left',
        'have hc : ' + _iff(left, '0*x=b'),) + _call('mod_eq_zero_iff_eq', '0*x', 'b')
    body += ('cases hc', 'split', 'intro h', 'symm', 'trans 0*x', 'symm', 'exact h0', 'apply hc_left', 'exact h',
        'intro h', 'apply hc_right', 'trans 0', 'exact h0', 'symm', 'exact h')
    return spec('linear_congruence_zero_modulus_zero_coefficient_iff', _contract(('b', 'x'), (), _iff(left, 'b=0')),
        ('mul_zero_left', 'mod_eq_zero_iff_eq'), body,
        'With coefficient and modulus both zero, every natural x is a solution exactly when the target is zero.')


def _one_row(spec):
    left = _and(_lt('x', '1', 'one_bound'), _mod('1', 'a*x', 'b', 'one_sol'))
    body = _intro('a', 'b', 'x') + ('split', 'intro h', 'cases h')
    body += _call('le_zero', 'x') + _call('le_of_succ_le_succ', 'x', '0')
    body += ('exact h_left', 'intro h', 'split', 'rewrite h', 'exists 0', 'apply zero_add')
    body += _call('crt_mod_one_universal', 'a*x', 'b')
    return spec('linear_congruence_modulus_one_bounded_iff_zero', _contract(('a', 'b', 'x'), (), _iff(left, 'x=0')),
        ('le_zero', 'le_of_succ_le_succ', 'zero_add', 'crt_mod_one_universal'), body,
        'For modulus one the unique strictly bounded solution is zero for every coefficient and target.')


def make_linear_congruence_classification_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Eleven new scripts followed by one unchanged isolated Fermat candidate."""
    result = tuple(builder(spec) for builder in (
        _cancel_row, _class_row, _representative_row, _progression_bound_row,
        _residue_parameter_row, _parameter_unique_row, _bounded_row, _enumeration_row,
        _zero_unique_row, _zero_coefficient_row, _one_row))
    old = tuple(row for row in make_fermat_endpoint_candidate_theorems(spec)
                if row.name == 'fermat_little_all_inputs')
    if len(old) != 1:
        raise ValueError('expected exactly one original all-input Fermat candidate')
    return (*result, *old)
