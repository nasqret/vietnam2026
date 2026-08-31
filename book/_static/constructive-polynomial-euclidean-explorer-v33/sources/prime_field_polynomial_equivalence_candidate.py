"""Formal polynomial equivalence and actual aligned coefficient operations.

The converse of leading-zero invariance constructs a genuine padded prefix
and identifies its decoded entries with the supplied equivalent prefix.
Addition and subtraction similarly construct the missing output padding;
their congruence conclusions are never assumed as constructor premises.

All coefficient orders are highest-degree-first.  Equality concerns bounded
decoded values, not beta-code numbers, unused entries, or field evaluations.
This working source neither registers an edition nor proves a gcd theorem.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _call, _intro, _prime
from peano_lab.library.prime_field_polynomial_candidate import _add, _equal
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent, _left_pad
from peano_lab.library.prime_field_polynomial_subtraction_candidate import _subtract
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, result)
    )


def _padding_converse_row(spec: Callable[..., Any]) -> Any:
    parameters = ('b', 'c', 'L', 't', 'd', 'e')
    premise = _equivalent('b', 'c', 'L', 'd', 'e', 't+L', 'converse_input')
    result = _left_pad('b', 'c', 'L', 't', 'd', 'e', 'converse_result')
    body = _intro(*parameters, 'he')
    body += (f"have hp : exists B C. ({_left_pad('b','c','L','t','B','C','converse_constructed')})",)
    body += _call('prime_field_polynomial_left_pad_exists', 'b', 'c', 't', 'L')
    body += ('cases hp', 'cases hp_witness',
             f"have hs : {_equivalent('b','c','L','x','x1','t+L','converse_source')}")
    body += _call('prime_field_polynomial_left_pad_equivalent', 'b', 'c', 'L', 't', 'x', 'x1')
    body += ('exact hp_witness_witness',
             f"have hr : {_equivalent('x','x1','t+L','b','c','L','converse_reverse')}")
    body += _call('prime_field_polynomial_equivalent_symmetric', 'b', 'c', 'L', 'x', 'x1', 't+L')
    body += ('exact hs',
             f"have ht : {_equivalent('x','x1','t+L','d','e','t+L','converse_target')}")
    body += _call('prime_field_polynomial_equivalent_transitive',
                  'x', 'x1', 't+L', 'b', 'c', 'L', 'd', 'e', 't+L')
    body += ('exact hr', 'exact he',
             f"have hv : {_equal('x','x1','d','e','t+L','converse_values')}")
    body += _call('prime_field_polynomial_equivalent_implies_equal_same_length', 'x', 'x1', 'd', 'e', 't+L')
    body += ('exact ht',)
    body += _call('prime_field_polynomial_left_pad_transport',
                  'b', 'c', 'b', 'c', 'L', 't', 'x', 'x1', 'd', 'e')
    body += _intro('i', 'a', 'hi', 'ha') + ('exact ha', 'exact hv', 'exact hp_witness_witness')
    return spec(
        'prime_field_polynomial_equivalent_implies_left_pad',
        _contract(parameters, (premise,), result),
        ('prime_field_polynomial_left_pad_exists', 'prime_field_polynomial_left_pad_equivalent',
         'prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_equivalent_transitive',
         'prime_field_polynomial_equivalent_implies_equal_same_length', 'prime_field_polynomial_left_pad_transport'),
        body,
        'Formal equivalence to a prefix of length t+L forces its actual leading-zero block and every copied source coefficient; construct a real padding and transport it by decoded equality, with no prime assumption.',
    )


def _output_padding_row(spec: Callable[..., Any], kind: str) -> Any:
    operation = _add if kind == 'add' else _subtract
    parameters = ('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', 't',
                  'AB', 'AC', 'BB', 'BC', 'CB', 'CC')
    original = operation('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', kind+'_output_original')
    padded = operation('p', 'AB', 'AC', 'BB', 'BC', 'CB', 'CC', 't+L', kind+'_output_padded')
    left = _left_pad('ab', 'ac', 'L', 't', 'AB', 'AC', kind+'_output_left')
    right = _left_pad('bb', 'bc', 'L', 't', 'BB', 'BC', kind+'_output_right')
    result = _left_pad('cb', 'cc', 'L', 't', 'CB', 'CC', kind+'_output_result')
    body = _intro(*parameters, 'hp', 'ho', 'hA', 'hB', 'hn')
    body += (f"have hd : exists db dc. ({_left_pad('cb','cc','L','t','db','dc',kind+'_output_constructed')})",)
    body += _call('prime_field_polynomial_left_pad_exists', 'cb', 'cc', 't', 'L')
    body += ('cases hd', 'cases hd_witness',
             f"have hm : {operation('p','AB','AC','BB','BC','x','x1','t+L',kind+'_output_middle')}")
    body += _call('prime_field_polynomial_'+kind+'_left_pad_transport',
                  'p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', 't',
                  'AB', 'AC', 'BB', 'BC', 'x', 'x1')
    body += ('exact hp', 'exact ho', 'exact hA', 'exact hB', 'exact hd_witness_witness',
             f"have he : {_equal('x','x1','CB','CC','t+L',kind+'_output_values')}")
    body += _call('prime_field_polynomial_'+kind+'_functional',
                  'p', 'AB', 'AC', 'BB', 'BC', 'x', 'x1', 'CB', 'CC', 't+L')
    body += ('exact hm', 'exact hn')
    body += _call('prime_field_polynomial_left_pad_transport',
                  'cb', 'cc', 'cb', 'cc', 'L', 't', 'x', 'x1', 'CB', 'CC')
    body += _intro('i', 'a', 'hi', 'ha') + ('exact ha', 'exact he', 'exact hd_witness_witness')
    return spec(
        'prime_field_polynomial_'+kind+'_left_pad_output',
        _contract(parameters, (_prime('p', kind+'_output_prime'), original, left, right, padded), result),
        ('prime_field_polynomial_left_pad_exists', 'prime_field_polynomial_'+kind+'_left_pad_transport',
         'prime_field_polynomial_'+kind+'_functional', 'prime_field_polynomial_left_pad_transport'),
        body,
        'Actual '+kind+' outputs inherit the genuine common leading-zero padding of their inputs: construct a padded original output, prove its operation, then identify the supplied output by functionality.',
    )


def _congruence_row(spec: Callable[..., Any], kind: str) -> Any:
    operation = _add if kind == 'add' else _subtract
    parameters = ('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L',
                  'AB', 'AC', 'BB', 'BC', 'CB', 'CC', 'K')
    first = _equivalent('ab', 'ac', 'L', 'AB', 'AC', 'K', kind+'_congruent_first')
    second = _equivalent('bb', 'bc', 'L', 'BB', 'BC', 'K', kind+'_congruent_second')
    original = operation('p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', kind+'_congruent_original')
    other = operation('p', 'AB', 'AC', 'BB', 'BC', 'CB', 'CC', 'K', kind+'_congruent_other')
    result = _equivalent('cb', 'cc', 'L', 'CB', 'CC', 'K', kind+'_congruent_result')
    body = _intro(*parameters, 'hp', 'hA', 'hB', 'ho', 'hn')
    body += ('have horder : L<=K \\/ K<=L',) + _call('le_total', 'L', 'K')
    body += ('cases horder', 'cases horder_left')
    for formula, hypothesis in ((first, 'hA'), (second, 'hB'), (other, 'hn')):
        body += _rewrite_all('<- horder_left_witness', formula, 'K', hypothesis)
    body += _rewrite_all('<- horder_left_witness', result, 'K')
    for code, scale, target_code, target_scale, hypothesis, name in (
        ('ab', 'ac', 'AB', 'AC', 'hA', 'hpadA'),
        ('bb', 'bc', 'BB', 'BC', 'hB', 'hpadB'),
    ):
        body += (f"have {name} : {_left_pad(code,scale,'L','x',target_code,target_scale,kind+'_congruent_forward_'+name)}",)
        body += _call('prime_field_polynomial_equivalent_implies_left_pad',
                      code, scale, 'L', 'x', target_code, target_scale) + ('exact '+hypothesis,)
    body += _call('prime_field_polynomial_left_pad_equivalent', 'cb', 'cc', 'L', 'x', 'CB', 'CC')
    body += _call('prime_field_polynomial_'+kind+'_left_pad_output',
                  'p', 'ab', 'ac', 'bb', 'bc', 'cb', 'cc', 'L', 'x',
                  'AB', 'AC', 'BB', 'BC', 'CB', 'CC')
    body += ('exact hp', 'exact ho', 'exact hpadA', 'exact hpadB', 'exact hn', 'cases horder_right')
    for formula, hypothesis in ((first, 'hA'), (second, 'hB'), (original, 'ho')):
        body += _rewrite_all('<- horder_right_witness', formula, 'L', hypothesis)
    body += _rewrite_all('<- horder_right_witness', result, 'L')
    for code, scale, target_code, target_scale, hypothesis, name in (
        ('AB', 'AC', 'ab', 'ac', 'hA', 'hpadA'),
        ('BB', 'BC', 'bb', 'bc', 'hB', 'hpadB'),
    ):
        body += (f"have {name} : {_left_pad(code,scale,'K','x',target_code,target_scale,kind+'_congruent_reverse_'+name)}",)
        body += _call('prime_field_polynomial_equivalent_implies_left_pad',
                      code, scale, 'K', 'x', target_code, target_scale)
        body += _call('prime_field_polynomial_equivalent_symmetric',
                      target_code, target_scale, 'x+K', code, scale, 'K') + ('exact '+hypothesis,)
    body += _call('prime_field_polynomial_equivalent_symmetric', 'CB', 'CC', 'K', 'cb', 'cc', 'x+K')
    body += _call('prime_field_polynomial_left_pad_equivalent', 'CB', 'CC', 'K', 'x', 'cb', 'cc')
    body += _call('prime_field_polynomial_'+kind+'_left_pad_output',
                  'p', 'AB', 'AC', 'BB', 'BC', 'CB', 'CC', 'K', 'x',
                  'ab', 'ac', 'bb', 'bc', 'cb', 'cc')
    body += ('exact hp', 'exact hn', 'exact hpadA', 'exact hpadB', 'exact ho')
    return spec(
        'prime_field_polynomial_'+kind+'_equivalent_congruent',
        _contract(parameters, (_prime('p', kind+'_congruent_prime'), first, second, original, other), result),
        ('le_total', 'prime_field_polynomial_equivalent_implies_left_pad',
         'prime_field_polynomial_'+kind+'_left_pad_output', 'prime_field_polynomial_left_pad_equivalent',
         'prime_field_polynomial_equivalent_symmetric'),
        body,
        'Pairwise formal-equivalent inputs give formal-equivalent actual '+kind+' outputs at either ordering of the two aligned lengths, including empty prefixes; no output equivalence or raw-code equality is assumed.',
    )


def make_prime_field_polynomial_equivalence_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_padding_converse_row(spec),
            *(_output_padding_row(spec, kind) for kind in ('add', 'subtract')),
            *(_congruence_row(spec, kind) for kind in ('add', 'subtract')))


__all__ = ['make_prime_field_polynomial_equivalence_candidate_theorems']
