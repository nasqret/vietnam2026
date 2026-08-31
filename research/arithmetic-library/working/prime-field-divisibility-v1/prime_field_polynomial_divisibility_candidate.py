"""Working right-factor divisibility with real quotient/product witnesses.

The divisor is on the right: A is formally equivalent to Q*D. The target
prefix is canonical, and the actual convolution supplies canonical divisor
and quotient prefixes. No equality of raw codes or field evaluations is used.
These unregistered source candidates grant no proof or admission authority.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _parts, _prime, _public,
)
from peano_lab.library.prime_field_polynomial_candidate import _coeff
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution, _length
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent


def _right_divides(p: str, db: str, dc: str, D: str,
                  ab: str, ac: str, L: str, tag: str) -> str:
    qb, qc, Q, pb, pc, P = tuple('pfrd_' + role + '_' + tag
                                for role in ('qb', 'qc', 'qlen', 'pb', 'pc', 'plen'))
    product = _convolution(p, qb, qc, Q, db, dc, D, pb, pc, P, tag + '_product')
    equivalent = _equivalent(pb, pc, P, ab, ac, L, tag + '_target')
    witnesses = f'exists {qb} {qc} {Q} {pb} {pc} {P}. ' + _and(product, equivalent)
    return _and(_coeff(p, ab, ac, L, tag + '_canonical'), witnesses)


def prime_field_polynomial_right_divides_relation(p: str, db: str, dc: str, D: str,
        ab: str, ac: str, L: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Canonical A and an actual quotient Q with actual Q*D formally equal to A."""
    return _public(_right_divides, (p, db, dc, D, ab, ac, L), tag=tag, variables=variables)


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + part + ')' for part in (*premises, result))


def _destruct(name: str) -> tuple[tuple[str, ...], str]:
    graph = name + '_right' + '_witness' * 6
    commands = ('cases ' + name,)
    commands += tuple('cases ' + name + '_right' + '_witness' * i for i in range(6))
    return commands + ('cases ' + graph,), graph


D = ('db', 'dc', 'D')
A = ('ab', 'ac', 'L')
B = ('bb', 'bc', 'M')
E = ('eb', 'ec', 'E')
Q = ('qb', 'qc', 'Q')
P = ('pb', 'pc', 'P')


def _introduction_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *D, *A, *Q, *P)
    body = _intro(*parameters, 'hA', 'hproduct', 'hequivalent')
    body += ('split', 'exact hA') + tuple('exists ' + term for term in (*Q, *P))
    body += ('split', 'exact hproduct', 'exact hequivalent')
    return spec(
        'prime_field_polynomial_right_divides_from_product',
        _contract(parameters, (
            _coeff('p', *A, 'right_divides_intro_bound'),
            _convolution('p', *Q, *D, *P, 'right_divides_intro_product'),
            _equivalent(*P, *A, 'right_divides_intro_equivalent'),
        ), _right_divides('p', *D, *A, 'right_divides_intro_result')),
        (), body,
        'A genuine proper-length Q*D and formal equivalence to a canonical target give actual right-factor divisibility, with the quotient and output witnesses retained.',
    )


def _bounded_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    parameters = ('p', *D, *A)
    commands, graph = _destruct('h')
    divisor = spec(
        'prime_field_polynomial_right_divides_divisor_bounded',
        _contract(parameters, (_right_divides('p', *D, *A, 'right_divisor_bound_source'),),
                  _coeff('p', *D, 'right_divisor_bound_result')),
        (), _intro(*parameters, 'h') + commands + _parts(graph + '_left', 4)
        + ('exact ' + graph + '_left_right_left',),
        'The actual witnessed convolution supplies a canonical divisor prefix, including zero-length divisors.',
    )
    dividend = spec(
        'prime_field_polynomial_right_divides_dividend_bounded',
        _contract(parameters, (_right_divides('p', *D, *A, 'right_dividend_bound_source'),),
                  _coeff('p', *A, 'right_dividend_bound_result')),
        (), _intro(*parameters, 'h') + ('cases h', 'exact h_left'),
        'Right-factor divisibility is a relation on canonical target prefixes, not on arbitrary unbounded coefficient encodings.',
    )
    return divisor, dividend


def _target_transport_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *D, *A, *B)
    body = _intro(*parameters, 'hB', 'hdivides', 'hequivalent')
    commands, graph = _destruct('hdivides')
    body += commands
    body += _call('prime_field_polynomial_right_divides_from_product',
                  'p', *D, *B, 'x', 'x1', 'x2', 'x3', 'x4', 'x5')
    body += ('exact hB', 'exact ' + graph + '_left')
    body += _call('prime_field_polynomial_equivalent_transitive', 'x3', 'x4', 'x5', *A, *B)
    body += ('exact ' + graph + '_right', 'exact hequivalent')
    return spec(
        'prime_field_polynomial_right_divides_equivalent_target',
        _contract(parameters, (
            _coeff('p', *B, 'right_target_bound'),
            _right_divides('p', *D, *A, 'right_target_source'),
            _equivalent(*A, *B, 'right_target_equivalent'),
        ), _right_divides('p', *D, *B, 'right_target_result')),
        ('prime_field_polynomial_right_divides_from_product',
         'prime_field_polynomial_equivalent_transitive'), body,
        'Changing the canonical target by all-power formal coefficient equivalence preserves the same genuine quotient/product witnesses, independently of representation length.',
    )


def _empty_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *D, 'ab', 'ac')
    empty = ('ab', 'ac', '0')
    body = _intro(*parameters, 'hD')
    body += _call('prime_field_polynomial_right_divides_from_product',
                  'p', *D, *empty, '0', '0', '0', *empty)
    body += _call('matrix_rank_bounded_prefix_empty', 'ab', 'ac', 'p')
    body += _call('prime_field_polynomial_convolution_empty',
                  'p', '0', '0', '0', *D, 'ab', 'ac')
    body += _call('matrix_rank_bounded_prefix_empty', '0', '0', 'p')
    body += ('exact hD', 'left', 'refl')
    body += _intro('k', 'a', 'r', 'ha', 'hr')
    body += _call('prime_field_polynomial_power_coefficient_functional', *empty, 'k', 'a', 'r')
    body += ('exact ha', 'exact hr')
    return spec(
        'prime_field_polynomial_right_divides_empty',
        _contract(parameters, (_coeff('p', *D, 'right_empty_divisor'),),
                  _right_divides('p', *D, *empty, 'right_empty_result')),
        ('prime_field_polynomial_right_divides_from_product',
         'matrix_rank_bounded_prefix_empty', 'prime_field_polynomial_convolution_empty',
         'prime_field_polynomial_power_coefficient_functional'), body,
        'Every canonical divisor divides every encoding of the empty polynomial, using an actual empty quotient and actual empty product. No prime, nonzero modulus or nonempty divisor assumption is needed.',
    )


def _make_product(label: str, left: tuple[str, ...], right: tuple[str, ...],
                  fresh: tuple[str, str, str], left_bound: str,
                  right_bound: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    length, code, scale = fresh
    length_hypothesis = label + '_length'
    product_hypothesis = label + '_product'
    body = ('have ' + length_hypothesis + ' : exists n. ('
            + _length(left[2], right[2], 'n', label + '_length_graph') + ')',)
    body += _call('polynomial_product_length_exists', left[2], right[2])
    body += ('cases ' + length_hypothesis,)
    body += ('have ' + product_hypothesis + ' : exists b c. ('
             + _convolution('p', *left, *right, 'b', 'c', length, label + '_graph') + ')',)
    body += _call('prime_field_polynomial_convolution_at_length_exists',
                  'p', *left, *right, length)
    body += ('exact hp0', 'exact ' + left_bound, 'exact ' + right_bound,
             'exact ' + length_hypothesis + '_witness',
             'cases ' + product_hypothesis, 'cases ' + product_hypothesis + '_witness')
    return body, (code, scale, length), product_hypothesis + '_witness_witness'


def _divisor_transport_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *D, *A, *E)
    body = _intro(*parameters, 'hp0', 'hE', 'hequivalent', 'hdivides')
    commands, graph = _destruct('hdivides')
    body += commands
    quotient, product = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5')
    body += ('have hsource : ' + _convolution('p', *quotient, *D, *product,
                                               'right_divisor_source_copy'),
             'exact ' + graph + '_left') + _parts('hsource', 4)
    commands, replacement, actual = _make_product('hnew', quotient, E,
        ('x6', 'x7', 'x8'), 'hsource_left', 'hE')
    body += commands
    body += _call('prime_field_polynomial_right_divides_from_product',
                  'p', *E, *A, *quotient, *replacement)
    body += ('exact hdivides_left', 'exact ' + actual)
    body += _call('prime_field_polynomial_equivalent_transitive', *replacement, *product, *A)
    body += _call('prime_field_polynomial_equivalent_symmetric', *product, *replacement)
    body += _call('prime_field_polynomial_convolution_equivalent_congruent_right',
                  'p', *quotient, *D, *product, *E, *replacement)
    body += ('exact hp0', 'exact hequivalent', 'exact ' + graph + '_left',
             'exact ' + actual, 'exact ' + graph + '_right')
    return spec(
        'prime_field_polynomial_right_divides_equivalent_divisor',
        _contract(parameters, (
            '~(p=0)', _coeff('p', *E, 'right_divisor_replacement_bound'),
            _equivalent(*D, *E, 'right_divisor_equivalent'),
            _right_divides('p', *D, *A, 'right_divisor_source'),
        ), _right_divides('p', *E, *A, 'right_divisor_result')),
        ('polynomial_product_length_exists', 'prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_right_divides_from_product',
         'prime_field_polynomial_equivalent_transitive', 'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_convolution_equivalent_congruent_right'), body,
        'An equivalent canonical right divisor preserves divisibility by constructing the quotient times the replacement at its own actual proper length. Formal output congruence, not a supplied output identity, gives the new witness.',
    )


def _transitive_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *D, *A, *B)
    body = _intro(*parameters, 'hp', 'hDA', 'hAB')
    body += ('have hp0 : ~(p=0)', 'intro hz')
    body += _call('prime_nonzero', 'p') + ('exact hp', 'exact hz')
    first_commands, first = _destruct('hDA')
    second_commands, second = _destruct('hAB')
    body += first_commands + second_commands
    quotient1, product1 = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5')
    quotient2, product2 = ('x6', 'x7', 'x8'), ('x9', 'x10', 'x11')
    for label, quotient, divisor, product, graph in (
        ('hfirst', quotient1, D, product1, first),
        ('hsecond', quotient2, A, product2, second),
    ):
        body += ('have ' + label + ' : ' + _convolution('p', *quotient, *divisor, *product,
                                                       'right_transitive_' + label),
                 'exact ' + graph + '_left') + _parts(label, 4)
    body += ('have hPbound : ' + _coeff('p', *product1, 'right_transitive_P_bound'),)
    body += _call('prime_field_polynomial_convolution_bounded', 'p', *quotient1, *D, *product1)
    body += ('exact ' + first + '_left',)
    commands, composite, composite_actual = _make_product('hcomposite', quotient2, quotient1,
        ('x12', 'x13', 'x14'), 'hsecond_left', 'hfirst_left')
    body += commands
    body += ('have hQbound : ' + _coeff('p', *composite, 'right_transitive_Q_bound'),)
    body += _call('prime_field_polynomial_convolution_bounded',
                  'p', *quotient2, *quotient1, *composite)
    body += ('exact ' + composite_actual,)
    commands, result, result_actual = _make_product('hresult', composite, D,
        ('x15', 'x16', 'x17'), 'hQbound', 'hfirst_right_left')
    body += commands
    commands, mixed, mixed_actual = _make_product('hmixed', quotient2, product1,
        ('x18', 'x19', 'x20'), 'hsecond_left', 'hPbound')
    body += commands
    # Discharge this comparison before specializing transitivity again. The
    # local branch preserves the universal theorem for the outer comparison.
    body += ('have htarget_equivalent : ' + _equivalent(*mixed, *B, 'right_transitive_target'),)
    body += _call('prime_field_polynomial_equivalent_transitive', *mixed, *product2, *B)
    body += _call('prime_field_polynomial_convolution_equivalent_congruent_right',
                  'p', *quotient2, *product1, *mixed, *A, *product2)
    body += ('exact hp0', 'exact ' + first + '_right', 'exact ' + mixed_actual,
             'exact ' + second + '_left', 'exact ' + second + '_right')
    body += _call('prime_field_polynomial_right_divides_from_product',
                  'p', *D, *B, *composite, *result)
    body += ('exact hAB_left', 'exact ' + result_actual)
    body += _call('prime_field_polynomial_equivalent_transitive', *result, *mixed, *B)
    body += _call('prime_field_polynomial_convolution_associative_equivalent',
                  'p', *quotient2, *quotient1, *composite, *D, *product1, *result, *mixed)
    body += ('exact hp', 'exact ' + composite_actual, 'exact ' + first + '_left',
             'exact ' + result_actual, 'exact ' + mixed_actual)
    body += ('exact htarget_equivalent',)
    return spec(
        'prime_field_polynomial_right_divides_transitive',
        _contract(parameters, (
            _prime('p', 'right_transitive_prime'),
            _right_divides('p', *D, *A, 'right_transitive_first'),
            _right_divides('p', *A, *B, 'right_transitive_second'),
        ), _right_divides('p', *D, *B, 'right_transitive_result')),
        ('prime_nonzero', 'prime_field_polynomial_convolution_bounded',
         'polynomial_product_length_exists', 'prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_right_divides_from_product',
         'prime_field_polynomial_equivalent_transitive',
         'prime_field_polynomial_convolution_associative_equivalent',
         'prime_field_polynomial_convolution_equivalent_congruent_right'), body,
        'Actual Q1*D equivalent to A and Q2*A equivalent to B give the actual composite quotient Q2*Q1. Three genuine intermediate products, formal associativity and right-input congruence prove its product with D equivalent to B. No commutativity, fixed representation lengths or raw-code identities are assumed.',
    )


def make_prime_field_polynomial_divisibility_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_introduction_row(spec), *_bounded_rows(spec), _target_transport_row(spec),
            _empty_row(spec), _divisor_transport_row(spec), _transitive_row(spec))


__all__ = ['make_prime_field_polynomial_divisibility_candidate_theorems',
           'prime_field_polynomial_right_divides_relation']
