"""Actual trailing-zero shift preserves formal polynomial equivalence.

This working-only bridge uses the existing PolynomialShift expansion: actual
prefix equality followed by an actual zero coefficient.  It does not register
a definition, select an Alpha edition, or assume equality of either output.
Representation lengths, beta codes and values beyond the prefixes are free.
No modulus, primality or coefficient-bound assumption is needed.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _and, _call, _intro
from peano_lab.library.prime_field_polynomial_candidate import _at, _equal
from peano_lab.library.prime_field_polynomial_representation_candidate import (
    _equivalent, _power_coefficient,
)
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _shift(b: str, c: str, length: str, d: str, e: str, tag: str) -> str:
    return _and(_equal(b, c, d, e, length, tag + 'prefix'),
                _at(d, e, length, '0', tag + 'last'))


PARAMETERS = ('b', 'c', 'L', 'd', 'e', 'M', 'ub', 'uc', 'vb', 'vc')


def _row(spec: Callable[..., Any]) -> Any:
    equivalent = _equivalent('b', 'c', 'L', 'd', 'e', 'M', 'shift_congruent_input')
    left_shift = _shift('b', 'c', 'L', 'ub', 'uc', 'shift_congruent_left')
    right_shift = _shift('d', 'e', 'M', 'vb', 'vc', 'shift_congruent_right')
    result = _equivalent('ub', 'uc', 'S L', 'vb', 'vc', 'S M', 'shift_congruent_result')
    left = _power_coefficient('ub', 'uc', 'S L', 'k', 'a', 'shift_congruent_left_value')
    right = _power_coefficient('vb', 'vc', 'S M', 'k', 'r', 'shift_congruent_right_value')
    body = _intro(*PARAMETERS, 'he', 'hu', 'hv', 'k', 'a', 'r', 'hleft', 'hright')
    body += ('have hcases : k=0 \\/ exists j. k=S j',) + _call('zero_or_succ', 'k')
    body += ('cases hcases',)

    # Constant coefficients of both actual shifts are genuinely zero.
    body += _rewrite_all('hcases_left', left, 'k', 'hleft')
    body += _rewrite_all('hcases_left', right, 'k', 'hright')
    body += (f"have hleft_zero : {_power_coefficient('ub','uc','S L','0','0','shift_congruent_left_zero')}",)
    body += _call('prime_field_polynomial_shift_power_zero', 'b', 'c', 'L', 'ub', 'uc') + ('exact hu',)
    body += (f"have hright_zero : {_power_coefficient('vb','vc','S M','0','0','shift_congruent_right_zero')}",)
    body += _call('prime_field_polynomial_shift_power_zero', 'd', 'e', 'M', 'vb', 'vc') + ('exact hv',)
    body += ('have hleft_value : a=0',)
    body += _call('prime_field_polynomial_power_coefficient_functional', 'ub', 'uc', 'S L', '0', 'a', '0')
    body += ('exact hleft', 'exact hleft_zero', 'have hright_value : 0=r')
    body += _call('prime_field_polynomial_power_coefficient_functional', 'vb', 'vc', 'S M', '0', '0', 'r')
    body += ('exact hright_zero', 'exact hright', 'trans 0', 'exact hleft_value', 'exact hright_value')

    # At a successor power, obtain actual source coefficients, transport them
    # through the actual shifts, and use only the given source equivalence.
    body += ('cases hcases_right',)
    body += _rewrite_all('hcases_right_witness', left, 'k', 'hleft')
    body += _rewrite_all('hcases_right_witness', right, 'k', 'hright')
    body += (f"have hleft_previous : exists s. ({_power_coefficient('b','c','L','x','s','shift_congruent_previous_left')})",)
    body += _call('prime_field_polynomial_power_coefficient_exists', 'b', 'c', 'L', 'x')
    body += ('cases hleft_previous',)
    body += (f"have hright_previous : exists s. ({_power_coefficient('d','e','M','x','s','shift_congruent_previous_right')})",)
    body += _call('prime_field_polynomial_power_coefficient_exists', 'd', 'e', 'M', 'x')
    body += ('cases hright_previous',)
    body += (f"have hleft_shifted : {_power_coefficient('ub','uc','S L','S x','x1','shift_congruent_shifted_left')}",)
    body += _call('prime_field_polynomial_shift_power_successor', 'b', 'c', 'L', 'ub', 'uc', 'x', 'x1')
    body += ('exact hu', 'exact hleft_previous_witness')
    body += (f"have hright_shifted : {_power_coefficient('vb','vc','S M','S x','x2','shift_congruent_shifted_right')}",)
    body += _call('prime_field_polynomial_shift_power_successor', 'd', 'e', 'M', 'vb', 'vc', 'x', 'x2')
    body += ('exact hv', 'exact hright_previous_witness', 'have hleft_value : a=x1')
    body += _call('prime_field_polynomial_power_coefficient_functional', 'ub', 'uc', 'S L', 'S x', 'a', 'x1')
    body += ('exact hleft', 'exact hleft_shifted', 'have hright_value : x2=r')
    body += _call('prime_field_polynomial_power_coefficient_functional', 'vb', 'vc', 'S M', 'S x', 'x2', 'r')
    body += ('exact hright_shifted', 'exact hright', 'have hprevious_equal : x1=x2')
    body += _call('he', 'x', 'x1', 'x2') + ('exact hleft_previous_witness', 'exact hright_previous_witness')
    body += ('trans x1', 'exact hleft_value', 'trans x2', 'exact hprevious_equal', 'exact hright_value')
    return spec(
        'prime_field_polynomial_shift_equivalent_congruent',
        'forall ' + ' '.join(PARAMETERS) + '. ' + ' -> '.join(
            '(' + clause + ')' for clause in (equivalent, left_shift, right_shift, result)),
        ('zero_or_succ', 'prime_field_polynomial_shift_power_zero',
         'prime_field_polynomial_shift_power_successor', 'prime_field_polynomial_power_coefficient_exists',
         'prime_field_polynomial_power_coefficient_functional'),
        body,
        'Two actual trailing-zero shifts preserve formal coefficient equivalence across arbitrary represented lengths, including empty prefixes. The proof obtains actual predecessor-power coefficients and compares decoded values, without any modulus, primality, coefficient-bound, raw-code identity, or evaluation-equality assumption.',
    )


def make_prime_field_polynomial_shift_equivalence_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_row(spec),)


__all__ = ['make_prime_field_polynomial_shift_equivalence_candidate_theorems']
