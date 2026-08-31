"""Formal coefficient distributivity for actual finite polynomial products.

These working-only candidates compare the inherited antidiagonal tables,
their actual natural finite sums, and their bounded residues.  Equality of
evaluations is never substituted for equality of formal coefficients.  The
coefficient laws do not require a spurious prime hypothesis: their actual
residue premises already supply the relevant canonical bounds.  Constructors
state the nonzero-modulus guard separately and construct real beta tables.

No algebraic conclusion is put into a constructor premise.  This is an
unregistered dependency-curried tranche, not an admission or a gcd proof.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _add as _field_add, _and, _call, _intro, _lt, _mod, _part, _parts,
)
from peano_lab.library.prime_field_polynomial_candidate import (
    _add, _at, _coeff,
)
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _coefficient, _convolution, _diagonal, _length, _pad, _prefix, _sum, _term,
)
from peano_lab.library.prime_field_polynomial_subtraction_candidate import _subtract
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ''.join(
        '(' + premise + ') -> ' for premise in premises
    ) + '(' + result + ')'


def _pointwise_add_congruence(length: str, tag: str) -> str:
    return 'forall i a b c. ' + ''.join('(' + premise + ') -> ' for premise in (
        _lt('i', length, tag + '_bound'),
        _at('ab', 'ac', 'i', 'a', tag + '_a'),
        _at('bb', 'bc', 'i', 'b', tag + '_b'),
        _at('cb', 'cc', 'i', 'c', tag + '_c'),
    )) + '(' + _mod('p', 'a+b', 'c', tag + '_value') + ')'


def _sum_add_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', 'A', 'B', 'C')
    body = _intro(*parameters[:7]) + ('induction L',)
    body += _intro('A', 'B', 'C', 'ha', 'hb', 'hc', 'hpw')
    for value, code, scale, hypothesis in (
        ('A', 'ab', 'ac', 'ha'), ('B', 'bb', 'bc', 'hb'), ('C', 'cb', 'cc', 'hc'),
    ):
        body += ('have h' + value + ' : ' + value + '=0',)
        body += _call('beta_sum_zero', code, scale, value) + ('exact ' + hypothesis,)
    body += ('rewrite hA', 'rewrite hB', 'rewrite hC', 'exists 0', 'exists 0', 'simp')
    body += _intro('A', 'B', 'C', 'ha', 'hb', 'hc', 'hpw')
    for value, code, scale, hypothesis, decomposition in (
        ('A', 'ab', 'ac', 'ha', 'hda'),
        ('B', 'bb', 'bc', 'hb', 'hdb'),
        ('C', 'cb', 'cc', 'hc', 'hdc'),
    ):
        graph = _and(_at(code, scale, 'L', 'a', decomposition + '_entry'),
                     _sum(code, scale, 'L', 'r', decomposition + '_prefix'), value + '=r+a')
        body += (f'have {decomposition} : exists a r. {graph}',)
        body += _call('beta_sum_succ_decompose', code, scale, 'L', value)
        body += ('exact ' + hypothesis, 'cases ' + decomposition,
                 'cases ' + decomposition + '_witness')
        body += _parts(decomposition + '_witness_witness', 3)
    body += (f"have hprefix : {_mod('p','x1+x3','x5','distribution_sum_prefix')}",)
    body += _call('IH', 'x1', 'x3', 'x5')
    body += ('exact hda_witness_witness_right_left',
             'exact hdb_witness_witness_right_left',
             'exact hdc_witness_witness_right_left')
    body += _intro('i', 'a', 'b', 'c', 'hi', 'hea', 'heb', 'hec')
    body += _call('hpw', 'i', 'a', 'b', 'c')
    body += _call('le_succ', 'S i', 'L')
    body += ('exact hi', 'exact hea', 'exact heb', 'exact hec')
    body += (f"have hlast : {_mod('p','x+x2','x4','distribution_sum_last')}",)
    body += _call('hpw', 'L', 'x', 'x2', 'x4') + _call('le_refl', 'S L')
    body += ('exact hda_witness_witness_left', 'exact hdb_witness_witness_left',
             'exact hdc_witness_witness_left')
    body += (f"have hcombined : {_mod('p','(x1+x3)+(x+x2)','x5+x4','distribution_sum_combined')}",)
    body += _call('mod_eq_add', 'p', 'x1+x3', 'x5', 'x+x2', 'x4')
    body += ('exact hprefix', 'exact hlast',
             'have hshuffle : (x1+x)+(x3+x2)=(x1+x3)+(x+x2)',
             'trans x1+(x+(x3+x2))', 'apply add_assoc',
             'trans x1+((x+x3)+x2)', 'congr', 'refl', 'symm', 'apply add_assoc',
             'trans x1+((x3+x)+x2)', 'congr', 'refl', 'congr', 'apply add_comm', 'refl',
             'trans x1+(x3+(x+x2))', 'congr', 'refl', 'apply add_assoc',
             'symm', 'apply add_assoc',
             'rewrite hda_witness_witness_right_right',
             'rewrite hdb_witness_witness_right_right',
             'rewrite hdc_witness_witness_right_right', 'rewrite hshuffle', 'exact hcombined')
    return spec(
        'beta_sum_pointwise_mod_add',
        _contract(parameters, (
            _sum('ab', 'ac', 'L', 'A', 'distribution_sum_a'),
            _sum('bb', 'bc', 'L', 'B', 'distribution_sum_b'),
            _sum('cb', 'cc', 'L', 'C', 'distribution_sum_c'),
            _pointwise_add_congruence('L', 'distribution_sum_pointwise'),
        ), _mod('p', 'A+B', 'C', 'distribution_sum_result')),
        ('beta_sum_zero', 'beta_sum_succ_decompose', 'le_succ', 'le_refl',
         'mod_eq_add', 'add_assoc', 'add_comm'), body,
        'Actual pointwise additive congruences lift by finite induction to the three actual Sum endpoints, for every modulus and also for the empty prefix.',
    )


def _padded_add_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', 'i', 'a', 'b', 'r')
    body = _intro(*parameters, 'hs', 'ha', 'hb', 'hr')
    body += ('cases ha', 'cases ha_left')
    for code, scale, value, hypothesis, chosen in (
        ('bb', 'bc', 'b', 'hb', 'heb'), ('cb', 'cc', 'r', 'hr', 'her'),
    ):
        body += (f'have {chosen} : {_at(code,scale,"i",value,"padded_add_"+chosen)}',)
        body += _call('polynomial_zero_extended_entry_inside', code, scale, 'L', 'i', value)
        body += ('exact ha_left_left', 'exact ' + hypothesis)
    body += (f"have hfield : {_field_add('p','a','b','r','padded_add_inside_value')}",)
    body += _call('prime_field_polynomial_add_entry', *parameters)
    body += ('exact hs', 'exact ha_left_left', 'exact ha_left_right', 'exact heb', 'exact her')
    body += _parts('hfield', 4) + ('exact hfield_right_right_right', 'cases ha_right')
    for code, scale, value, hypothesis, chosen in (
        ('bb', 'bc', 'b', 'hb', 'hbzero'), ('cb', 'cc', 'r', 'hr', 'hrzero'),
    ):
        body += ('have ' + chosen + ' : ' + value + '=0',)
        body += _call('polynomial_zero_extended_entry_functional', code, scale, 'L', 'i', value, '0')
        body += ('exact ' + hypothesis, 'right', 'split', 'exact ha_right_left', 'refl')
    body += ('rewrite ha_right_right', 'rewrite hbzero', 'rewrite hrzero',
             'exists 0', 'exists 0', 'simp')
    return spec(
        'polynomial_zero_extended_add_congruent',
        _contract(parameters, (
            _add('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', 'padded_add_source'),
            _pad('ab', 'ac', 'L', 'i', 'a', 'padded_add_a'),
            _pad('bb', 'bc', 'L', 'i', 'b', 'padded_add_b'),
            _pad('cb', 'cc', 'L', 'i', 'r', 'padded_add_r'),
        ), _mod('p', 'a+b', 'r', 'padded_add_result')),
        ('polynomial_zero_extended_entry_inside', 'prime_field_polynomial_add_entry',
         'polynomial_zero_extended_entry_functional'), body,
        'An actual coefficient sum extends by actual zeros to an additive congruence at every index; no claim is made about arbitrary decoded entries outside the original prefixes.',
    )


PARAMETERS = ('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', 'db', 'dc', 'M')
OPERANDS = (('ab', 'ac'), ('bb', 'bc'), ('cb', 'cc'))


def _factors(side: str, code: str, scale: str) -> tuple[str, ...]:
    if side == 'left':
        return 'db', 'dc', 'M', code, scale, 'L'
    if side == 'right':
        return code, scale, 'L', 'db', 'dc', 'M'
    raise ValueError('a distributive side must be left or right')


def _term_add_row(spec: Callable[..., Any], side: str) -> Any:
    body = _intro(*PARAMETERS, 'i', 'j', 'u', 'v', 'w', 'hs', 'hu', 'hv', 'hw')
    for hypothesis in ('hu', 'hv', 'hw'):
        body += tuple('cases ' + hypothesis + '_witness' * index for index in range(3))
        body += _parts(hypothesis + '_witness_witness_witness', 4)
    for complement, hypothesis, equality, operand in (
        ('x', 'hu', 'hku', OPERANDS[0]), ('x3', 'hv', 'hkv', OPERANDS[1]),
    ):
        graph = hypothesis + '_witness_witness_witness'
        body += ('have ' + equality + ' : ' + complement + '=x6',)
        body += _call('add_left_cancel', 'j', complement, 'x6')
        body += ('trans i', 'exact ' + graph + '_left', 'symm',
                 'exact hw_witness_witness_witness_left')
        code, scale, length = ((*operand, 'L') if side == 'left' else ('db', 'dc', 'M'))
        value = 'x2' if hypothesis == 'hu' else 'x5'
        body += _rewrite_all(equality, _pad(code, scale, length, complement, value,
                                            'term_add_' + side + '_' + equality),
                             complement, graph + '_right_right_left')
    fixed_values = ('x1', 'x4', 'x7') if side == 'left' else ('x2', 'x5', 'x8')
    variable_values = ('x2', 'x5', 'x8') if side == 'left' else ('x1', 'x4', 'x7')
    fixed_index, variable_index = ('j', 'x6') if side == 'left' else ('x6', 'j')
    fixed_field = '_right_left' if side == 'left' else '_right_right_left'
    variable_field = '_right_right_left' if side == 'left' else '_right_left'
    for value, hypothesis, equality in zip(fixed_values[:2], ('hu', 'hv'), ('hfu', 'hfv'), strict=True):
        body += (f'have {equality} : {value}={fixed_values[2]}',)
        body += _call('polynomial_zero_extended_entry_functional', 'db', 'dc', 'M',
                      fixed_index, value, fixed_values[2])
        body += ('exact ' + hypothesis + '_witness_witness_witness' + fixed_field,
                 'exact hw_witness_witness_witness' + fixed_field)
    raw_sum = variable_values[0] + '+' + variable_values[1]
    body += (f"have hsum : {_mod('p',raw_sum,variable_values[2],'term_add_'+side+'_sum')}",)
    body += _call('polynomial_zero_extended_add_congruent',
                  *PARAMETERS[:8], variable_index, *variable_values)
    body += ('exact hs',) + tuple('exact ' + h + '_witness_witness_witness' + variable_field
                                  for h in ('hu', 'hv', 'hw'))
    body += tuple('rewrite ' + h + '_witness_witness_witness_right_right_right'
                  for h in ('hu', 'hv', 'hw'))
    body += ('rewrite hfu', 'rewrite hfv')
    fixed = fixed_values[2]
    if side == 'left':
        expanded = fixed + '*' + variable_values[0] + '+' + fixed + '*' + variable_values[1]
        factored = fixed + '*(' + raw_sum + ')'
        arithmetic, congruence = 'mul_add', 'mod_eq_mul_left'
        arithmetic_arguments = (fixed, variable_values[0], variable_values[1])
    else:
        expanded = variable_values[0] + '*' + fixed + '+' + variable_values[1] + '*' + fixed
        factored = '(' + raw_sum + ')*' + fixed
        arithmetic, congruence = 'add_mul', 'mod_eq_mul_right'
        arithmetic_arguments = (variable_values[0], variable_values[1], fixed)
    body += (f'have hfactor : {expanded}={factored}', 'symm')
    body += _call(arithmetic, *arithmetic_arguments) + ('rewrite hfactor',)
    body += _call(congruence, 'p', raw_sum, variable_values[2], fixed) + ('exact hsum',)
    return spec(
        'polynomial_diagonal_term_' + side + '_add_congruent',
        _contract((*PARAMETERS, 'i', 'j', 'u', 'v', 'w'), (
            _add('p', *PARAMETERS[1:8], 'term_add_' + side + '_source'),
            *(_term(*_factors(side, code, scale), 'i', 'j', value,
                    'term_add_' + side + '_' + value)
              for (code, scale), value in zip(OPERANDS, ('u', 'v', 'w'), strict=True)),
        ), _mod('p', 'u+v', 'w', 'term_add_' + side + '_result')),
        ('add_left_cancel', 'polynomial_zero_extended_entry_functional',
         'polynomial_zero_extended_add_congruent', arithmetic, congruence), body,
        'At one actual antidiagonal position, ' + side + ' multiplication carries the genuine padded coefficient sum to the sum of the two genuine multiplication terms modulo the same modulus.',
    )


def _diagonal_add_row(spec: Callable[..., Any], side: str) -> Any:
    tables = (('ub', 'uc'), ('vb', 'vc'), ('wb', 'wc'))
    parameters = (*PARAMETERS, 'i', 'N', 'ub', 'uc', 'vb', 'vc', 'wb', 'wc', 'u', 'v', 'w')
    body = _intro(*parameters, 'hs', 'hdu', 'hsv', 'hdv', 'hsvv', 'hdw', 'hsw')
    body += _call('beta_sum_pointwise_mod_add', 'p', 'ub', 'uc', 'vb', 'vc', 'wb', 'wc', 'N', 'u', 'v', 'w')
    body += ('exact hsv', 'exact hsvv', 'exact hsw')
    body += _intro('j', 'a', 'b', 'c', 'hj', 'ha', 'hb', 'hc')
    body += _call('polynomial_diagonal_term_' + side + '_add_congruent',
                  *PARAMETERS, 'i', 'j', 'a', 'b', 'c') + ('exact hs',)
    for (code, scale), (table_code, table_scale), value, diagonal_hypothesis, entry_hypothesis in zip(
        OPERANDS, tables, ('a', 'b', 'c'), ('hdu', 'hdv', 'hdw'), ('ha', 'hb', 'hc'), strict=True,
    ):
        body += _call('polynomial_diagonal_prefix_entry', *_factors(side, code, scale),
                      'i', table_code, table_scale, 'N', 'j', value)
        body += ('exact ' + diagonal_hypothesis, 'exact hj', 'exact ' + entry_hypothesis)
    premises = [_add('p', *PARAMETERS[1:8], 'diagonal_add_' + side + '_source')]
    for (code, scale), (table_code, table_scale), value in zip(OPERANDS, tables, ('u', 'v', 'w'), strict=True):
        premises.extend((
            _diagonal(*_factors(side, code, scale), 'i', table_code, table_scale, 'N',
                      'diagonal_add_' + side + '_' + value),
            _sum(table_code, table_scale, 'N', value, 'diagonal_add_' + side + '_sum_' + value),
        ))
    return spec(
        'polynomial_diagonal_sum_' + side + '_add_congruent',
        _contract(parameters, tuple(premises), _mod('p', 'u+v', 'w', 'diagonal_add_' + side + '_result')),
        ('beta_sum_pointwise_mod_add', 'polynomial_diagonal_term_' + side + '_add_congruent',
         'polynomial_diagonal_prefix_entry'), body,
        'The three independently beta-coded actual antidiagonal sums obey ' + side + ' additive congruence, including empty sum prefixes and with no raw-code equality.',
    )


def _coefficient_add_row(spec: Callable[..., Any], side: str) -> Any:
    parameters = (*PARAMETERS, 'i', 'u', 'v', 'w')
    body = _intro(*parameters, 'hs', 'hu', 'hv', 'hw')
    for hypothesis in ('hu', 'hv', 'hw'):
        body += tuple('cases ' + hypothesis + '_witness' * index for index in range(3))
        body += _parts(hypothesis + '_witness_witness_witness', 3)
    body += (f"have hsum : {_mod('p','x2+x5','x8','coefficient_add_'+side+'_sum')}",)
    body += _call('polynomial_diagonal_sum_' + side + '_add_congruent',
                  *PARAMETERS, 'i', 'S i', 'x', 'x1', 'x3', 'x4', 'x6', 'x7', 'x2', 'x5', 'x8')
    body += ('exact hs',)
    for hypothesis in ('hu', 'hv', 'hw'):
        body += ('exact ' + hypothesis + '_witness_witness_witness_left',
                 'exact ' + hypothesis + '_witness_witness_witness_right_left')
    for hypothesis in ('hu', 'hv', 'hw'):
        body += ('cases ' + hypothesis + '_witness_witness_witness_right_right',)
    body += (f"have hraw : {_mod('p','x2+x5','w','coefficient_add_'+side+'_raw')}",)
    body += _call('mod_eq_trans', 'p', 'x2+x5', 'x8', 'w')
    body += ('exact hsum', 'exact hw_witness_witness_witness_right_right_right')
    body += ('split', 'exact hu_witness_witness_witness_right_right_left',
             'split', 'exact hv_witness_witness_witness_right_right_left',
             'split', 'exact hw_witness_witness_witness_right_right_left')
    body += _call('mod_eq_trans', 'p', 'u+v', 'x2+x5', 'w')
    body += _call('mod_eq_symm', 'p', 'x2+x5', 'u+v')
    body += _call('mod_eq_add', 'p', 'x2', 'u', 'x5', 'v')
    body += ('exact hu_witness_witness_witness_right_right_right',
             'exact hv_witness_witness_witness_right_right_right', 'exact hraw')
    return spec(
        'prime_field_convolution_coefficient_' + side + '_add',
        _contract(parameters, (
            _add('p', *PARAMETERS[1:8], 'coefficient_add_' + side + '_source'),
            *(_coefficient('p', *_factors(side, code, scale), 'i', value,
                           'coefficient_add_' + side + '_' + value)
              for (code, scale), value in zip(OPERANDS, ('u', 'v', 'w'), strict=True)),
        ), _field_add('p', 'u', 'v', 'w', 'coefficient_add_' + side + '_result')),
        ('polynomial_diagonal_sum_' + side + '_add_congruent',
         'mod_eq_trans', 'mod_eq_symm', 'mod_eq_add'), body,
        'Three genuine convolution coefficients satisfy actual canonical field addition under ' + side + ' distributivity, proved from their independently witnessed natural sums and residues.',
    )


OUTPUTS = (('ub', 'uc'), ('vb', 'vc'), ('wb', 'wc'))
OUTPUT_PARAMETERS = ('ub', 'uc', 'vb', 'vc', 'wb', 'wc', 'N')


def _prefix_add_row(spec: Callable[..., Any], side: str) -> Any:
    parameters = (*PARAMETERS, *OUTPUT_PARAMETERS)
    body = _intro(*parameters, 'hs', 'hu', 'hv', 'hw', 'i', 'hi')
    for (code, scale), (output_code, output_scale), hypothesis, chosen in zip(
        OPERANDS, OUTPUTS, ('hu', 'hv', 'hw'), ('hcu', 'hcv', 'hcw'), strict=True,
    ):
        graph = _and(_at(output_code, output_scale, 'i', 'r', 'prefix_add_' + side + '_' + chosen),
                     _coefficient('p', *_factors(side, code, scale), 'i', 'r',
                                  'prefix_add_' + side + '_value_' + chosen))
        body += (f'have {chosen} : exists r. {graph}',)
        body += _call(hypothesis, 'i') + ('exact hi', 'cases ' + chosen, 'cases ' + chosen + '_witness')
    body += ('exists x', 'exists x1', 'exists x2', 'split', 'exact hcu_witness_left',
             'split', 'exact hcv_witness_left', 'split', 'exact hcw_witness_left')
    body += _call('prime_field_convolution_coefficient_' + side + '_add',
                  *PARAMETERS, 'i', 'x', 'x1', 'x2')
    body += ('exact hs', 'exact hcu_witness_right', 'exact hcv_witness_right', 'exact hcw_witness_right')
    return spec(
        'prime_field_convolution_prefix_' + side + '_add',
        _contract(parameters, (
            _add('p', *PARAMETERS[1:8], 'prefix_add_' + side + '_source'),
            *(_prefix('p', *_factors(side, code, scale), output_code, output_scale, 'N',
                      'prefix_add_' + side + '_' + output_code)
              for (code, scale), (output_code, output_scale) in zip(OPERANDS, OUTPUTS, strict=True)),
        ), _add('p', *OUTPUT_PARAMETERS, 'prefix_add_' + side + '_result')),
        ('prime_field_convolution_coefficient_' + side + '_add',), body,
        'Every requested ambient output prefix of the three actual ' + side + ' products satisfies actual coefficientwise addition, including N=0 and prefixes extending past product support.',
    )


def _prefix_subtract_row(spec: Callable[..., Any], side: str) -> Any:
    parameters = (*PARAMETERS, *OUTPUT_PARAMETERS)
    body = _intro(*parameters, 'hs', 'hu', 'hv', 'hw')
    body += _call('prime_field_polynomial_subtract_from_add', 'p', *OUTPUT_PARAMETERS)
    body += _call('prime_field_convolution_prefix_' + side + '_add',
                  'p', 'bb', 'bc', 'cb', 'cc', 'ab', 'ac', 'L', 'db', 'dc', 'M',
                  'vb', 'vc', 'wb', 'wc', 'ub', 'uc', 'N')
    body += _call('prime_field_polynomial_subtract_recover_add', 'p', *PARAMETERS[1:8])
    body += ('exact hs', 'exact hv', 'exact hw', 'exact hu')
    return spec(
        'prime_field_convolution_prefix_' + side + '_subtract',
        _contract(parameters, (
            _subtract('p', *PARAMETERS[1:8], 'prefix_subtract_' + side + '_source'),
            *(_prefix('p', *_factors(side, code, scale), output_code, output_scale, 'N',
                      'prefix_subtract_' + side + '_' + output_code)
              for (code, scale), (output_code, output_scale) in zip(OPERANDS, OUTPUTS, strict=True)),
        ), _subtract('p', *OUTPUT_PARAMETERS, 'prefix_subtract_' + side + '_result')),
        ('prime_field_polynomial_subtract_from_add', 'prime_field_convolution_prefix_' + side + '_add',
         'prime_field_polynomial_subtract_recover_add'), body,
        'The three genuine ' + side + ' convolution prefixes preserve actual field subtraction coefficient by coefficient, with characteristic two and arbitrary beta reencodings included.',
    )


def _proper_law_row(spec: Callable[..., Any], side: str, operation: str) -> Any:
    graph = _add if operation == 'add' else _subtract
    parameters = (*PARAMETERS, *OUTPUT_PARAMETERS)
    body = _intro(*parameters, 'hs', 'hu', 'hv', 'hw')
    for hypothesis in ('hu', 'hv', 'hw'):
        body += _parts(hypothesis, 4)
    body += _call('prime_field_convolution_prefix_' + side + '_' + operation, *parameters)
    body += ('exact hs', 'exact hu_right_right_right', 'exact hv_right_right_right',
             'exact hw_right_right_right')
    return spec(
        'prime_field_polynomial_convolution_' + side + '_' + operation,
        _contract(parameters, (
            graph('p', *PARAMETERS[1:8], 'proper_' + side + '_' + operation + '_source'),
            *(_convolution('p', *_factors(side, code, scale), output_code, output_scale, 'N',
                           'proper_' + side + '_' + operation + '_' + output_code)
              for (code, scale), (output_code, output_scale) in zip(OPERANDS, OUTPUTS, strict=True)),
        ), graph('p', *OUTPUT_PARAMETERS, 'proper_' + side + '_' + operation + '_result')),
        ('prime_field_convolution_prefix_' + side + '_' + operation,), body,
        'The existing proper-length convolution graphs obey actual ' + side + ' ' + operation + ' distributivity; this is a formal coefficient law, not an evaluation test.',
    )


def _products_exists_row(spec: Callable[..., Any], side: str) -> Any:
    lengths = ('M', 'L') if side == 'left' else ('L', 'M')
    body = _intro(*PARAMETERS, 'hp', 'hd', 'hs')
    body += (f"have hlength : exists N. {_length(*lengths,'N','products_'+side+'_length')}",)
    body += _call('polynomial_product_length_exists', *lengths) + ('cases hlength',)
    bounds = _and(*(_coeff('p', code, scale, 'L', 'products_' + side + '_bounded_' + code)
                    for code, scale in OPERANDS))
    body += ('have hbounds : ' + bounds,)
    body += _call('prime_field_polynomial_add_bounded', 'p', *PARAMETERS[1:8])
    body += ('exact hs',) + _parts('hbounds', 3)
    for index, ((code, scale), hypothesis) in enumerate(zip(OPERANDS, ('hu', 'hv', 'hw'), strict=True)):
        product = _convolution('p', *_factors(side, code, scale), 'ub', 'uc', 'x',
                               'products_' + side + '_' + hypothesis)
        body += (f'have {hypothesis} : exists ub uc. {product}',)
        body += _call('prime_field_polynomial_convolution_at_length_exists',
                      'p', *_factors(side, code, scale), 'x')
        body += ('exact hp',)
        bound_hypothesis = _part('hbounds', 3, index)
        body += (('exact hd', 'exact ' + bound_hypothesis) if side == 'left'
                 else ('exact ' + bound_hypothesis, 'exact hd'))
        body += ('exact hlength_witness', 'cases ' + hypothesis, 'cases ' + hypothesis + '_witness')
    body += tuple('exists ' + value for value in ('x', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6'))
    body += ('split', 'exact hu_witness_witness', 'split', 'exact hv_witness_witness',
             'split', 'exact hw_witness_witness')
    body += _call('prime_field_polynomial_convolution_' + side + '_add',
                  *PARAMETERS, 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x')
    body += ('exact hs', 'exact hu_witness_witness', 'exact hv_witness_witness', 'exact hw_witness_witness')
    result = 'exists N ub uc vb vc wb wc. ' + _and(
        *(_convolution('p', *_factors(side, code, scale), output_code, output_scale, 'N',
                       'products_' + side + '_result_' + output_code)
          for (code, scale), (output_code, output_scale) in zip(OPERANDS, OUTPUTS, strict=True)),
        _add('p', *OUTPUT_PARAMETERS, 'products_' + side + '_addition'),
    )
    return spec(
        'prime_field_polynomial_' + side + '_distributive_products_exists',
        _contract(PARAMETERS, (
            '~(p=0)', _coeff('p', 'db', 'dc', 'M', 'products_' + side + '_fixed_input'),
            _add('p', *PARAMETERS[1:8], 'products_' + side + '_input_addition'),
        ), result),
        ('polynomial_product_length_exists', 'prime_field_polynomial_add_bounded',
         'prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_convolution_' + side + '_add'), body,
        'Construct all three genuine proper-length ' + side + ' products and then prove their coefficient-addition identity; the product witnesses and the distributive conclusion are outputs, never input assumptions.',
    )


def make_prime_field_polynomial_distributivity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (
        _sum_add_row(spec), _padded_add_row(spec),
        *(_term_add_row(spec, side) for side in ('left', 'right')),
        *(_diagonal_add_row(spec, side) for side in ('left', 'right')),
        *(_coefficient_add_row(spec, side) for side in ('left', 'right')),
        *(_prefix_add_row(spec, side) for side in ('left', 'right')),
        *(_prefix_subtract_row(spec, side) for side in ('left', 'right')),
        *(_proper_law_row(spec, side, operation)
          for operation in ('add', 'subtract') for side in ('left', 'right')),
        *(_products_exists_row(spec, side) for side in ('left', 'right')),
    )


__all__ = ['make_prime_field_polynomial_distributivity_candidate_theorems']
