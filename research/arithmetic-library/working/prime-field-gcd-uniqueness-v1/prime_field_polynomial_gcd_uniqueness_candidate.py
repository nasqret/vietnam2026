"""Formal uniqueness of normalized right associates: working HA candidates.

Quotients in RightDivides are actual left factors, not assumed monic or
nonzero-leading.  They are trimmed before the field degree law is used.
Empty normal forms are treated without assigning a degree to zero.  Every
conclusion compares formal coefficients, never beta codes or evaluations.
These scripts are not admission or completed-proof evidence.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _and, _call, _intro, _lt, _mul, _parts, _prime
from peano_lab.library.prime_field_polynomial_candidate import _at, _coeff, _equal
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution, _length, _le
from peano_lab.library.prime_field_polynomial_degree_candidate import _degree
from peano_lab.library.prime_field_polynomial_monic_candidate import _monic
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent
from peano_lab.library.prime_field_polynomial_trim_candidate import _trim
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters, premises, result):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, result))


def _right_divides(p, db, dc, D, ab, ac, L, tag):
    """Literal conservative ND0342, with only hygienic binder renaming."""
    qb, qc, Q, pb, pc, P = tuple('pfgu_' + role + '_' + tag
        for role in ('qb', 'qc', 'Q', 'pb', 'pc', 'P'))
    return _and(_coeff(p, ab, ac, L, tag + '_canonical'),
        'exists ' + ' '.join((qb, qc, Q, pb, pc, P)) + '. ' + _and(
            _convolution(p, qb, qc, Q, db, dc, D, pb, pc, P, tag + '_product'),
            _equivalent(pb, pc, P, ab, ac, L, tag + '_target')))


def _common(p, db, dc, D, ab, ac, L, bb, bc, M, tag):
    return _and(_right_divides(p, db, dc, D, ab, ac, L, tag + '_left'),
                _right_divides(p, db, dc, D, bb, bc, M, tag + '_right'))


def _normal(p, gb, gc, G, tag):
    return f'({G})=0 \\/ (' + _monic(p, gb, gc, G, tag + '_monic') + ')'


def _right_gcd(p, gb, gc, G, ab, ac, L, bb, bc, M, tag):
    db, dc, D = tuple('pfgu_' + role + '_' + tag for role in ('db', 'dc', 'D'))
    greatest = 'forall ' + ' '.join((db, dc, D)) + '. (' + _common(
        p, db, dc, D, ab, ac, L, bb, bc, M, tag + '_divisor') + ') -> (' + _right_divides(
        p, db, dc, D, gb, gc, G, tag + '_greatest') + ')'
    return _and(_common(p, gb, gc, G, ab, ac, L, bb, bc, M, tag + '_common'), greatest)


def _normalized_gcd(p, gb, gc, G, ab, ac, L, bb, bc, M, tag):
    return _and(_normal(p, gb, gc, G, tag + '_normal'),
        _right_gcd(p, gb, gc, G, ab, ac, L, bb, bc, M, tag + '_gcd'))


def _leading_length_row(spec):
    pars = ('ab', 'ac', 'd', 'bb', 'bc', 'M', 'a')
    body = _intro(*pars, 'ha', 'hne', 'he')
    body += ('have horder : (' + _le('M', 'd', 'length_order') + ') \\/ (' + _lt('d', 'M', 'length_strict') + ')',)
    body += _call('le_or_lt', 'M', 'd')
    body += ('cases horder', 'exfalso', 'apply hne')
    body += _call('he', 'd', 'a', '0')
    body += ('left', 'exists 0', 'split', 'apply zero_add', 'exact ha',
             'right', 'split', 'exact horder_left', 'refl', 'exact horder_right')
    return spec('prime_field_polynomial_nonzero_leading_equivalent_length_bound',
        _contract(pars, (_at('ab', 'ac', '0', 'a', 'length_head'), '~(a=0)',
            _equivalent('ab', 'ac', 'S d', 'bb', 'bc', 'M', 'length_equivalent')),
            _le('S d', 'M', 'length_result')),
        ('le_or_lt', 'zero_add'), body,
        'A nonzero coefficient at the leading power cannot be matched by an outside-prefix zero. This length bound needs neither primality nor canonical coefficients.')


def _degree_equivalent_row(spec):
    pars = ('p', 'ab', 'ac', 'L', 'd', 'bb', 'bc', 'M', 'e')
    eq = _equivalent('ab', 'ac', 'L', 'bb', 'bc', 'M', 'degree_equivalent')
    body = _intro(*pars, 'ha', 'hb', 'he') + _parts('ha', 3) + _parts('hb', 3)
    body += ('have hsame : ' + _equivalent('ab', 'ac', 'S d', 'bb', 'bc', 'S e', 'degree_lengths'),
             'have hcopy : ' + eq, 'exact he')
    body += _rewrite_all('ha_left', eq, 'L', 'hcopy')
    body += _rewrite_all('hb_left', _equivalent('ab', 'ac', 'S d', 'bb', 'bc', 'M', 'degree_rewrite'), 'M', 'hcopy')
    body += ('exact hcopy', 'cases ha_right_right', 'cases ha_right_right_witness',
             'cases hb_right_right', 'cases hb_right_right_witness', 'have hlength : S d=S e')
    body += _call('le_antisymm', 'S d', 'S e')
    body += _call('prime_field_polynomial_nonzero_leading_equivalent_length_bound',
                  'ab', 'ac', 'd', 'bb', 'bc', 'S e', 'x')
    body += ('exact ha_right_right_witness_left', 'exact ha_right_right_witness_right', 'exact hsame')
    body += _call('prime_field_polynomial_nonzero_leading_equivalent_length_bound',
                  'bb', 'bc', 'e', 'ab', 'ac', 'S d', 'x1')
    body += ('exact hb_right_right_witness_left', 'exact hb_right_right_witness_right')
    body += _call('prime_field_polynomial_equivalent_symmetric', 'ab', 'ac', 'S d', 'bb', 'bc', 'S e')
    body += ('exact hsame',) + _call('succ_injective', 'd', 'e') + ('exact hlength',)
    return spec('prime_field_polynomial_equivalent_represented_degrees_equal',
        _contract(pars, (_degree('p', 'ab', 'ac', 'L', 'd', 'degree_left'),
            _degree('p', 'bb', 'bc', 'M', 'e', 'degree_right'), eq), 'd=e'),
        ('prime_field_polynomial_nonzero_leading_equivalent_length_bound', 'le_antisymm',
         'prime_field_polynomial_equivalent_symmetric', 'succ_injective'), body,
        'Formal equivalence preserves genuine represented degree across independently encoded and independently length-annotated nonzero-leading prefixes.')


def _product_nonempty_row(spec):
    pars = ('p', 'qb', 'qc', 'Q', 'db', 'dc', 'D', 'pb', 'pc', 'P', 'ab', 'ac', 'L', 'a')
    body = _intro(*pars, 'ha', 'hc', 'he', 'hz')
    body += ('have hlength : ' + _length('Q', 'D', 'P', 'nonempty_length'),)
    body += _parts('hc', 4) + ('exact hc_right_right_left',)
    body += _parts('ha', 3) + ('cases ha_right_right', 'cases ha_right_right_witness',
             'have hbound : ' + _le('S a', 'P', 'nonempty_bound'))
    body += _call('prime_field_polynomial_nonzero_leading_equivalent_length_bound',
                  'ab', 'ac', 'a', 'pb', 'pc', 'P', 'x')
    body += ('exact ha_right_right_witness_left', 'exact ha_right_right_witness_right',
             'have hsame : ' + _equivalent('ab', 'ac', 'L', 'pb', 'pc', 'P', 'nonempty_symmetric'))
    body += _call('prime_field_polynomial_equivalent_symmetric', 'pb', 'pc', 'P', 'ab', 'ac', 'L') + ('exact he',)
    body += _rewrite_all('ha_left', _equivalent('ab', 'ac', 'L', 'pb', 'pc', 'P', 'nonempty_rewrite_L'), 'L', 'hsame')
    body += ('exact hsame', 'cases hlength', 'cases hlength_left',
             'have hzero : S a=0') + _call('le_zero', 'S a')
    body += ('rewrite <- hlength_left_right', 'exact hbound')
    body += _call('succ_ne_zero', 'a') + ('exact hzero',)
    body += _parts('hlength_right', 3) + ('apply hlength_right_left', 'exact hz')
    return spec('prime_field_polynomial_product_equivalent_nonzero_left_nonempty',
        _contract(pars, (_degree('p', 'ab', 'ac', 'L', 'a', 'nonempty_target'),
            _convolution('p', 'qb', 'qc', 'Q', 'db', 'dc', 'D', 'pb', 'pc', 'P', 'nonempty_product'),
            _equivalent('pb', 'pc', 'P', 'ab', 'ac', 'L', 'nonempty_target_equivalent')), '~(Q=0)'),
        ('prime_field_polynomial_nonzero_leading_equivalent_length_bound',
         'prime_field_polynomial_equivalent_symmetric', 'succ_ne_zero', 'le_zero'), body,
        'An actual product formally equal to a nonzero-leading representation cannot have an empty left factor. No degree is assigned to empty factors.')


def _factorization_result(p, db, dc, D, ab, ac, L, d, a, tag):
    qb, qc, e, pb, pc = tuple('pfgu_' + role + '_' + tag for role in ('qb', 'qc', 'e', 'pb', 'pc'))
    return 'exists ' + ' '.join((qb, qc, e, pb, pc)) + '. ' + _and(
        _degree(p, qb, qc, 'S (' + e + ')', e, tag + '_quotient'),
        _convolution(p, qb, qc, 'S (' + e + ')', db, dc, D, pb, pc, 'S (' + a + ')', tag + '_product'),
        _equivalent(pb, pc, 'S (' + a + ')', ab, ac, L, tag + '_equivalent'),
        '(' + e + ')+(' + d + ')=(' + a + ')')


def _factorization_row(spec):
    pars = ('p', 'db', 'dc', 'D', 'd', 'ab', 'ac', 'L', 'a')
    body = _intro(*pars, 'hp', 'hd', 'ha', 'hrd')
    body += ('have hpn : ~(p=0)', 'intro hpzero') + _call('prime_nonzero', 'p') + ('exact hp', 'exact hpzero')
    body += ('have hdbound : ' + _coeff('p', 'db', 'dc', 'D', 'factor_divisor_bound'),)
    body += _parts('hd', 3) + ('exact hd_right_left', 'cases hrd')
    body += tuple('cases hrd_right' + '_witness' * i for i in range(6))
    data = 'hrd_right' + '_witness' * 6
    body += ('cases ' + data, 'have hqbound : ' + _coeff('p', 'x', 'x1', 'x2', 'factor_quotient_bound'))
    body += _parts(data + '_left', 4) + ('exact ' + data + '_left_left',)
    trimmed = _trim('p', 'x', 'x1', 'x2', 't', 'tb', 'tc', 'T', 'factor_trim')
    body += ('have ht : exists t tb tc T. ' + trimmed,)
    body += _call('prime_field_polynomial_trim_exists', 'p', 'x', 'x1', 'x2') + ('exact hqbound',)
    body += tuple('cases ht' + '_witness' * i for i in range(4))
    ht = 'ht' + '_witness' * 4
    body += ('have htbound : ' + _coeff('p', 'x7', 'x8', 'x9', 'factor_trim_bound'),)
    body += _call('prime_field_polynomial_trim_output_coefficients', 'p', 'x', 'x1', 'x2', 'x6', 'x7', 'x8', 'x9') + ('exact ' + ht,)
    body += ('have hqe : ' + _equivalent('x', 'x1', 'x2', 'x7', 'x8', 'x9', 'factor_trim_equivalent'),)
    body += _call('prime_field_polynomial_trim_equivalent', 'p', 'x', 'x1', 'x2', 'x6', 'x7', 'x8', 'x9') + ('exact ' + ht,)
    body += ('have hplen : exists N. ' + _length('x9', 'D', 'N', 'factor_new_length'),)
    body += _call('polynomial_product_length_exists', 'x9', 'D') + ('cases hplen',)
    cv = _convolution('p', 'x7', 'x8', 'x9', 'db', 'dc', 'D', 'vb', 'vc', 'x10', 'factor_new_product')
    body += ('have hpnew : exists vb vc. ' + cv,)
    body += _call('prime_field_polynomial_convolution_at_length_exists', 'p', 'x7', 'x8', 'x9', 'db', 'dc', 'D', 'x10')
    body += ('exact hpn', 'exact htbound', 'exact hdbound', 'exact hplen_witness', 'cases hpnew', 'cases hpnew_witness')
    newcv = _convolution('p', 'x7', 'x8', 'x9', 'db', 'dc', 'D', 'x11', 'x12', 'x10', 'factor_actual_new')
    eq = _equivalent('x11', 'x12', 'x10', 'ab', 'ac', 'L', 'factor_actual_equivalent')
    body += ('have hequiv : ' + eq,)
    body += _call('prime_field_polynomial_equivalent_transitive', 'x11', 'x12', 'x10', 'x3', 'x4', 'x5', 'ab', 'ac', 'L')
    body += _call('prime_field_polynomial_equivalent_symmetric', 'x3', 'x4', 'x5', 'x11', 'x12', 'x10')
    body += _call('prime_field_polynomial_convolution_equivalent_congruent_left',
                  'p', 'x', 'x1', 'x2', 'db', 'dc', 'D', 'x3', 'x4', 'x5', 'x7', 'x8', 'x9', 'x11', 'x12', 'x10')
    body += ('exact hpn', 'exact hqe', 'exact ' + data + '_left', 'exact hpnew_witness_witness', 'exact ' + data + '_right')
    body += ('have hn : ~(x9=0)', 'intro htzero')
    body += _call('prime_field_polynomial_product_equivalent_nonzero_left_nonempty',
                  'p', 'x7', 'x8', 'x9', 'db', 'dc', 'D', 'x11', 'x12', 'x10', 'ab', 'ac', 'L', 'a')
    body += ('exact ha', 'exact hpnew_witness_witness', 'exact hequiv', 'exact htzero',
             'have hqd : exists e. ' + _degree('p', 'x7', 'x8', 'x9', 'e', 'factor_trim_degree'))
    body += _call('prime_field_polynomial_trim_nonempty_degree_exists', 'p', 'x', 'x1', 'x2', 'x6', 'x7', 'x8', 'x9')
    body += ('exact ' + ht, 'exact hn', 'cases hqd',
             'have hpd : ' + _degree('p', 'x11', 'x12', 'x10', 'x13+d', 'factor_product_degree'))
    body += _call('prime_field_polynomial_convolution_represented_degree',
                  'p', 'x7', 'x8', 'x9', 'x13', 'db', 'dc', 'D', 'd', 'x11', 'x12', 'x10')
    body += ('exact hp', 'exact hqd_witness', 'exact hd', 'exact hpnew_witness_witness', 'have hsum : x13+d=a')
    body += _call('prime_field_polynomial_equivalent_represented_degrees_equal',
                  'p', 'x11', 'x12', 'x10', 'x13+d', 'ab', 'ac', 'L', 'a')
    body += ('exact hpd', 'exact ha', 'exact hequiv', 'have hqlen : x9=S x13', 'cases hqd_witness', 'exact hqd_witness_left',
             'have hplen2 : x10=S a', 'cases hpd', 'rewrite hpd_left', 'rewrite hsum', 'refl',
             'exists x7', 'exists x8', 'exists x13', 'exists x11', 'exists x12', 'split',
             'have hqdnew : ' + _degree('p', 'x7', 'x8', 'x9', 'x13', 'factor_pack_degree'), 'exact hqd_witness')
    body += _rewrite_all('hqlen', _degree('p', 'x7', 'x8', 'x9', 'x13', 'factor_pack_degree'), 'x9', 'hqdnew')
    body += ('exact hqdnew', 'split', 'have hcp : ' + newcv, 'exact hpnew_witness_witness')
    body += _rewrite_all('hqlen', newcv, 'x9', 'hcp')
    body += _rewrite_all('hplen2', _convolution('p', 'x7', 'x8', 'S x13', 'db', 'dc', 'D', 'x11', 'x12', 'x10', 'factor_pack_product'), 'x10', 'hcp')
    body += ('exact hcp', 'split', 'have hep : ' + eq, 'exact hequiv')
    body += _rewrite_all('hplen2', eq, 'x10', 'hep') + ('exact hep', 'exact hsum')
    return spec('prime_field_polynomial_right_divides_represented_factorization',
        _contract(pars, (_prime('p', 'factor_prime'), _degree('p', 'db', 'dc', 'D', 'd', 'factor_divisor'),
            _degree('p', 'ab', 'ac', 'L', 'a', 'factor_target'),
            _right_divides('p', 'db', 'dc', 'D', 'ab', 'ac', 'L', 'factor_divisibility')),
            _factorization_result('p', 'db', 'dc', 'D', 'ab', 'ac', 'L', 'd', 'a', 'factor_result')),
        ('prime_nonzero', 'prime_field_polynomial_trim_exists', 'prime_field_polynomial_trim_output_coefficients',
         'prime_field_polynomial_trim_equivalent', 'polynomial_product_length_exists',
         'prime_field_polynomial_convolution_at_length_exists', 'prime_field_polynomial_equivalent_transitive',
         'prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_convolution_equivalent_congruent_left',
         'prime_field_polynomial_product_equivalent_nonzero_left_nonempty',
         'prime_field_polynomial_trim_nonempty_degree_exists', 'prime_field_polynomial_convolution_represented_degree',
         'prime_field_polynomial_equivalent_represented_degrees_equal'), body,
        'Trim the actual quotient, construct an independent proper-length product, and transport formal coefficients. Its genuine nonzero degree e satisfies e+d=a; no quotient degree or domain cancellation is assumed.')


def _divisor_degree_row(spec):
    pars = ('p', 'db', 'dc', 'D', 'd', 'ab', 'ac', 'L', 'a')
    body = _intro(*pars, 'hp', 'hd', 'ha', 'hrd')
    body += ('have hf : ' + _factorization_result('p', 'db', 'dc', 'D', 'ab', 'ac', 'L', 'd', 'a', 'bound_factor'),)
    body += _call('prime_field_polynomial_right_divides_represented_factorization', *pars)
    body += ('exact hp', 'exact hd', 'exact ha', 'exact hrd')
    body += tuple('cases hf' + '_witness' * i for i in range(5))
    data = 'hf' + '_witness' * 5
    body += _parts(data, 4) + ('exists x2', 'exact ' + data + '_right_right_right')
    return spec('prime_field_polynomial_right_divides_represented_degree_bound',
        _contract(pars, (_prime('p', 'bound_prime'), _degree('p', 'db', 'dc', 'D', 'd', 'bound_divisor'),
            _degree('p', 'ab', 'ac', 'L', 'a', 'bound_target'),
            _right_divides('p', 'db', 'dc', 'D', 'ab', 'ac', 'L', 'bound_divisibility')), _le('d', 'a', 'bound_result')),
        ('prime_field_polynomial_right_divides_represented_factorization',), body,
        'A nonzero represented right divisor has degree at most that of its nonzero represented multiple, using the actual retained quotient degree as the natural witness.')


def _singleton_monic_row(spec):
    pars = ('p', 'kb', 'kc', 'db', 'dc', 'ab', 'ac', 'd', 'pb', 'pc')
    product = _convolution('p', 'kb', 'kc', '1', 'db', 'dc', 'S d', 'pb', 'pc', 'S d', 'singleton_product')
    body = _intro(*pars, 'hp', 'hd', 'ha', 'hc', 'he') + _parts('hd', 3) + _parts('ha', 3)
    body += ('have hk : exists k. ' + _at('kb', 'kc', '0', 'k', 'singleton_head'),)
    body += _call('beta_at_exists', 'kb', 'kc', '0') + ('cases hk',)
    body += ('have hpa : ' + _at('pb', 'pc', '0', '1', 'singleton_product_head'),
             'have hprefix : ' + _equal('ab', 'ac', 'pb', 'pc', 'S d', 'singleton_prefix'))
    body += _call('prime_field_polynomial_equivalent_implies_equal_same_length', 'ab', 'ac', 'pb', 'pc', 'S d')
    body += _call('prime_field_polynomial_equivalent_symmetric', 'pb', 'pc', 'S d', 'ab', 'ac', 'S d')
    body += ('exact he',) + _call('hprefix', '0', '1') + ('exists d', 'simp', 'exact ha_right_right')
    body += ('have hm : ' + _mul('p', 'x', '1', '1', 'singleton_leading_multiply'),)
    body += _call('prime_field_polynomial_convolution_leading_coefficient',
                  'p', 'kb', 'kc', '0', 'db', 'dc', 'd', 'pb', 'pc', 'S d', 'x', '1', '1')
    body += ('exact hc', 'exact hk_witness', 'exact hd_right_right', 'exact hpa', 'have hone : x=1')
    body += _call('prime_field_multiply_functional', 'p', 'x', '1', 'x', '1')
    body += _call('prime_field_multiply_one_right', 'p', 'x')
    body += ('exact hp', 'cases hm', 'exact hm_left', 'exact hm',
             'have hkone : ' + _at('kb', 'kc', '0', '1', 'singleton_unit_head'),
             'have hcopy : ' + _at('kb', 'kc', '0', 'x', 'singleton_copy_head'), 'exact hk_witness')
    body += _rewrite_all('hone', _at('kb', 'kc', '0', 'x', 'singleton_copy_head'), 'x', 'hcopy')
    body += ('exact hcopy',)
    body += _call('prime_field_polynomial_equivalent_transitive', 'db', 'dc', 'S d', 'pb', 'pc', 'S d', 'ab', 'ac', 'S d')
    body += _call('prime_field_polynomial_equivalent_symmetric', 'pb', 'pc', 'S d', 'db', 'dc', 'S d')
    body += _call('prime_field_polynomial_convolution_left_unit_equivalent', 'p', 'kb', 'kc', 'db', 'dc', 'S d', 'pb', 'pc')
    body += ('exact hkone', 'exact hc', 'exact he')
    return spec('prime_field_polynomial_monic_singleton_multiple_equivalent',
        _contract(pars, (_prime('p', 'singleton_prime'), _monic('p', 'db', 'dc', 'S d', 'singleton_divisor'),
            _monic('p', 'ab', 'ac', 'S d', 'singleton_target'), product,
            _equivalent('pb', 'pc', 'S d', 'ab', 'ac', 'S d', 'singleton_target_equivalent')),
            _equivalent('db', 'dc', 'S d', 'ab', 'ac', 'S d', 'singleton_result')),
        ('beta_at_exists', 'prime_field_polynomial_equivalent_implies_equal_same_length',
         'prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_convolution_leading_coefficient',
         'prime_field_multiply_functional', 'prime_field_multiply_one_right',
         'prime_field_polynomial_equivalent_transitive', 'prime_field_polynomial_convolution_left_unit_equivalent'), body,
        'Both monic heads force an actual left singleton quotient to have coefficient one, by the ordered leading product k*1. The genuine left-unit convolution law then gives formal equivalence.')


def _monic_degree_row(spec):
    pars = ('p', 'db', 'dc', 'ab', 'ac', 'd')
    body = _intro(*pars, 'hp', 'hd', 'ha', 'hrd')
    body += ('have hdd : ' + _degree('p', 'db', 'dc', 'S d', 'd', 'monic_degree_divisor'),)
    body += _call('prime_field_polynomial_monic_represented_degree', 'p', 'db', 'dc', 'S d', 'd') + ('exact hd', 'refl')
    body += ('have had : ' + _degree('p', 'ab', 'ac', 'S d', 'd', 'monic_degree_target'),)
    body += _call('prime_field_polynomial_monic_represented_degree', 'p', 'ab', 'ac', 'S d', 'd') + ('exact ha', 'refl')
    body += ('have hf : ' + _factorization_result('p', 'db', 'dc', 'S d', 'ab', 'ac', 'S d', 'd', 'd', 'monic_degree_factor'),)
    body += _call('prime_field_polynomial_right_divides_represented_factorization', 'p', 'db', 'dc', 'S d', 'd', 'ab', 'ac', 'S d', 'd')
    body += ('exact hp', 'exact hdd', 'exact had', 'exact hrd')
    body += tuple('cases hf' + '_witness' * i for i in range(5))
    data = 'hf' + '_witness' * 5
    body += _parts(data, 4) + ('have hezero : x2=0',)
    body += _call('add_right_cancel', 'x2', '0', 'd')
    body += ('trans d', 'exact ' + data + '_right_right_right', 'symm', 'apply zero_add')
    body += _call('prime_field_polynomial_monic_singleton_multiple_equivalent',
                  'p', 'x', 'x1', 'db', 'dc', 'ab', 'ac', 'd', 'x3', 'x4')
    body += ('exact hp', 'exact hd', 'exact ha',
             'have hproduct : ' + _convolution('p', 'x', 'x1', 'S x2', 'db', 'dc', 'S d', 'x3', 'x4', 'S d', 'monic_degree_product'),
             'exact ' + data + '_right_left')
    body += _rewrite_all('hezero', _convolution('p', 'x', 'x1', 'S x2', 'db', 'dc', 'S d', 'x3', 'x4', 'S d', 'monic_degree_product'), 'x2', 'hproduct')
    body += ('exact hproduct', 'exact ' + data + '_right_right_left')
    return spec('prime_field_polynomial_monic_equal_degree_right_divides_equivalent',
        _contract(pars, (_prime('p', 'monic_degree_prime'), _monic('p', 'db', 'dc', 'S d', 'monic_degree_D'),
            _monic('p', 'ab', 'ac', 'S d', 'monic_degree_A'),
            _right_divides('p', 'db', 'dc', 'S d', 'ab', 'ac', 'S d', 'monic_degree_RD')),
            _equivalent('db', 'dc', 'S d', 'ab', 'ac', 'S d', 'monic_degree_result')),
        ('prime_field_polynomial_monic_represented_degree', 'prime_field_polynomial_right_divides_represented_factorization',
         'add_right_cancel', 'zero_add', 'prime_field_polynomial_monic_singleton_multiple_equivalent'), body,
        'Equal-degree monic right divisibility has a genuinely constructed degree-zero quotient. Its head must be one, so divisor and target are formally equivalent.')


def _monic_associates_row(spec):
    pars = ('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H')
    body = _intro(*pars, 'hp', 'hg', 'hh', 'hgh', 'hhg')
    body += ('have hgn : ~(G=0)', 'cases hg', 'exact hg_left',
             'have hhn : ~(H=0)', 'cases hh', 'exact hh_left',
             'have hgl : exists d. G=S d')
    body += _call('nonzero_is_succ', 'G') + ('exact hgn', 'cases hgl', 'have hhl : exists e. H=S e')
    body += _call('nonzero_is_succ', 'H') + ('exact hhn', 'cases hhl',
             'have hgd : ' + _degree('p', 'gb', 'gc', 'G', 'x', 'associates_degree_G'))
    body += _call('prime_field_polynomial_monic_represented_degree', 'p', 'gb', 'gc', 'G', 'x') + ('exact hg', 'exact hgl_witness',)
    body += ('have hhd : ' + _degree('p', 'hb', 'hc', 'H', 'x1', 'associates_degree_H'),)
    body += _call('prime_field_polynomial_monic_represented_degree', 'p', 'hb', 'hc', 'H', 'x1') + ('exact hh', 'exact hhl_witness', 'have hde : x=x1')
    body += _call('le_antisymm', 'x', 'x1')
    body += _call('prime_field_polynomial_right_divides_represented_degree_bound', 'p', 'gb', 'gc', 'G', 'x', 'hb', 'hc', 'H', 'x1')
    body += ('exact hp', 'exact hgd', 'exact hhd', 'exact hgh')
    body += _call('prime_field_polynomial_right_divides_represented_degree_bound', 'p', 'hb', 'hc', 'H', 'x1', 'gb', 'gc', 'G', 'x')
    body += ('exact hp', 'exact hhd', 'exact hgd', 'exact hhg', 'have hsame : H=S x',
             'rewrite hhl_witness', 'rewrite hde', 'refl',
             'have hge : ' + _monic('p', 'gb', 'gc', 'S x', 'associates_monic_G'),
             'have hcopy : ' + _monic('p', 'gb', 'gc', 'G', 'associates_monic_Gcopy'), 'exact hg')
    body += _rewrite_all('hgl_witness', _monic('p', 'gb', 'gc', 'G', 'associates_monic_Gcopy'), 'G', 'hcopy') + ('exact hcopy',)
    body += ('have hhe : ' + _monic('p', 'hb', 'hc', 'S x', 'associates_monic_H'),
             'have hcopy : ' + _monic('p', 'hb', 'hc', 'H', 'associates_monic_Hcopy'), 'exact hh')
    body += _rewrite_all('hsame', _monic('p', 'hb', 'hc', 'H', 'associates_monic_Hcopy'), 'H', 'hcopy') + ('exact hcopy',)
    body += ('have hr : ' + _right_divides('p', 'gb', 'gc', 'S x', 'hb', 'hc', 'S x', 'associates_RD'),
             'have hcopy : ' + _right_divides('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H', 'associates_RDcopy'), 'exact hgh')
    body += _rewrite_all('hgl_witness', _right_divides('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H', 'associates_RDcopy'), 'G', 'hcopy')
    body += _rewrite_all('hsame', _right_divides('p', 'gb', 'gc', 'S x', 'hb', 'hc', 'H', 'associates_RDcopy2'), 'H', 'hcopy') + ('exact hcopy',)
    goal = _equivalent('gb', 'gc', 'G', 'hb', 'hc', 'H', 'associates_result')
    body += _rewrite_all('hgl_witness', goal, 'G')
    body += _rewrite_all('hsame', _equivalent('gb', 'gc', 'S x', 'hb', 'hc', 'H', 'associates_result2'), 'H')
    body += _call('prime_field_polynomial_monic_equal_degree_right_divides_equivalent', 'p', 'gb', 'gc', 'hb', 'hc', 'x')
    body += ('exact hp', 'exact hge', 'exact hhe', 'exact hr')
    return spec('prime_field_polynomial_monic_right_associates_equivalent',
        _contract(pars, (_prime('p', 'associates_prime'), _monic('p', 'gb', 'gc', 'G', 'associates_G'),
            _monic('p', 'hb', 'hc', 'H', 'associates_H'),
            _right_divides('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H', 'associates_GH'),
            _right_divides('p', 'hb', 'hc', 'H', 'gb', 'gc', 'G', 'associates_HG')), goal),
        ('nonzero_is_succ', 'prime_field_polynomial_monic_represented_degree', 'le_antisymm',
         'prime_field_polynomial_right_divides_represented_degree_bound',
         'prime_field_polynomial_monic_equal_degree_right_divides_equivalent'), body,
        'Mutual right divisibility forces equal represented degrees. Both actual monic normalizations then force formal coefficient equivalence, without selecting unique beta codes.')


def _empty_divisor_row(spec):
    pars = ('p', 'db', 'dc', 'ab', 'ac', 'L')
    body = _intro(*pars, 'hrd') + ('cases hrd',)
    body += tuple('cases hrd_right' + '_witness' * i for i in range(6))
    data = 'hrd_right' + '_witness' * 6
    body += ('cases ' + data, 'have hlength : ' + _length('x2', '0', 'x5', 'empty_length')) + _parts(data + '_left', 4)
    length = data + '_left_right_right_left'
    body += ('exact ' + length, 'cases hlength', 'cases hlength_left')
    body += _call('prime_field_polynomial_equivalent_transitive', 'ab', 'ac', 'L', 'x3', 'x4', '0', 'db', 'dc', '0')
    body += _call('prime_field_polynomial_equivalent_symmetric', 'x3', 'x4', '0', 'ab', 'ac', 'L')
    formula = _equivalent('x3', 'x4', 'x5', 'ab', 'ac', 'L', 'empty_copy')
    body += ('have hcopy : ' + formula, 'exact ' + data + '_right')
    body += _rewrite_all('hlength_left_right', formula, 'x5', 'hcopy') + ('exact hcopy',)
    body += _call('prime_field_polynomial_equal_implies_equivalent', 'x3', 'x4', 'db', 'dc', '0')
    body += _intro('i', 'a', 'hi', 'ha') + ('exfalso',)
    body += _call('lt_not_le', 'i', '0') + ('exact hi',) + _call('zero_le', 'i')
    body += _parts('hlength_right', 3) + ('exfalso', 'apply hlength_right_right_left', 'refl')
    return spec('prime_field_polynomial_empty_right_divisor_implies_equivalent_zero',
        _contract(pars, (_right_divides('p', 'db', 'dc', '0', 'ab', 'ac', 'L', 'empty_divisor'),),
            _equivalent('ab', 'ac', 'L', 'db', 'dc', '0', 'empty_divisor_result')),
        ('prime_field_polynomial_equivalent_transitive', 'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_equal_implies_equivalent', 'lt_not_le', 'zero_le'), body,
        'An empty right divisor has only formally zero multiples, at any target representation length. The actual product length is zero; no zero-degree assertion or prime hypothesis is used.')


def _normal_associates_row(spec):
    pars = ('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H')
    body = _intro(*pars, 'hp', 'hg', 'hh', 'hgh', 'hhg') + ('cases hg',)
    goal = _equivalent('gb', 'gc', 'G', 'hb', 'hc', 'H', 'normal_result')
    body += _rewrite_all('hg_left', goal, 'G')
    body += _call('prime_field_polynomial_equivalent_symmetric', 'hb', 'hc', 'H', 'gb', 'gc', '0')
    body += _call('prime_field_polynomial_empty_right_divisor_implies_equivalent_zero', 'p', 'gb', 'gc', 'hb', 'hc', 'H')
    formula = _right_divides('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H', 'normal_empty_G')
    body += ('have hcopy : ' + formula, 'exact hgh') + _rewrite_all('hg_left', formula, 'G', 'hcopy') + ('exact hcopy', 'cases hh')
    body += _rewrite_all('hh_left', goal, 'H')
    body += _call('prime_field_polynomial_empty_right_divisor_implies_equivalent_zero', 'p', 'hb', 'hc', 'gb', 'gc', 'G')
    formula = _right_divides('p', 'hb', 'hc', 'H', 'gb', 'gc', 'G', 'normal_empty_H')
    body += ('have hcopy : ' + formula, 'exact hhg') + _rewrite_all('hh_left', formula, 'H', 'hcopy') + ('exact hcopy',)
    body += _call('prime_field_polynomial_monic_right_associates_equivalent', *pars)
    body += ('exact hp', 'exact hg_right', 'exact hh_right', 'exact hgh', 'exact hhg')
    return spec('prime_field_polynomial_normal_right_associates_equivalent',
        _contract(pars, (_prime('p', 'normal_prime'), _normal('p', 'gb', 'gc', 'G', 'normal_G'),
            _normal('p', 'hb', 'hc', 'H', 'normal_H'),
            _right_divides('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H', 'normal_GH'),
            _right_divides('p', 'hb', 'hc', 'H', 'gb', 'gc', 'G', 'normal_HG')), goal),
        ('prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_empty_right_divisor_implies_equivalent_zero',
         'prime_field_polynomial_monic_right_associates_equivalent'), body,
        'Two zero-or-monic mutual right associates are formally equivalent, including both-zero and one-empty branches. Both normalization premises are essential; beta encodings need not agree.')


def _gcd_unique_row(spec):
    pars = ('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H', 'ab', 'ac', 'L', 'bb', 'bc', 'M')
    body = _intro(*pars, 'hp', 'hg', 'hh') + ('cases hg', 'cases hg_right', 'cases hh', 'cases hh_right')
    body += _call('prime_field_polynomial_normal_right_associates_equivalent', 'p', 'gb', 'gc', 'G', 'hb', 'hc', 'H')
    body += ('exact hp', 'exact hg_left', 'exact hh_left')
    body += _call('hh_right_right', 'gb', 'gc', 'G') + ('exact hg_right_left',)
    body += _call('hg_right_right', 'hb', 'hc', 'H') + ('exact hh_right_left',)
    return spec('prime_field_polynomial_normalized_gcd_equivalent_unique',
        _contract(pars, (_prime('p', 'gcd_unique_prime'),
            _normalized_gcd('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'gcd_unique_G'),
            _normalized_gcd('p', 'hb', 'hc', 'H', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'gcd_unique_H')),
            _equivalent('gb', 'gc', 'G', 'hb', 'hc', 'H', 'gcd_unique_result')),
        ('prime_field_polynomial_normal_right_associates_equivalent',), body,
        'The grouped normal/common-divisor/greatestness graph yields mutual right associates, hence uniqueness only up to formal coefficient equivalence. This does not assert unique beta codes or Bezout coefficients.')


def make_prime_field_polynomial_gcd_uniqueness_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_leading_length_row(spec), _degree_equivalent_row(spec), _product_nonempty_row(spec),
            _factorization_row(spec), _divisor_degree_row(spec), _singleton_monic_row(spec),
            _monic_degree_row(spec), _monic_associates_row(spec), _empty_divisor_row(spec),
            _normal_associates_row(spec), _gcd_unique_row(spec))
