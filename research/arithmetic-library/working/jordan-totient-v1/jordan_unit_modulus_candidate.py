"""The empty-product base case for Jordan counts, with an actual singleton list.

Reuse the existing primitive-tuple and enumeration relations. The literal
outer beta streams (0,0),(0,0) enumerate the all-zero inner tuple (0,0).
These additive candidates do not change release membership or prior sources.
"""
import jordan_totient_candidate as base

_and, _at, _lt = base._and, base._at, base._lt
_bounded, _equal = base._bounded, base._equal
_intro, _call = base._intro, base._call


def _contract(args, premises, result):
    return 'forall ' + ' '.join(args) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, result))


def _below_one_zero(term, hypothesis):
    # These proofs occur beneath EqTrans, whose operands must synthesize.
    # Bare applications infer their parameters from the equality/bound goal;
    # specialization would put an introduction redex in an operand instead.
    return ('apply le_zero', 'apply le_of_succ_le_succ', 'exact ' + hypothesis)


def make_jordan_unit_modulus_candidate_theorems(spec):
    rows = []
    args = ('b', 'c', 'k', 'i', 'a')
    body = _intro(*args, 'hBound', 'hi', 'ha') + (
        'have hValue : exists z. ' + _and(
            _at('b', 'c', 'i', 'z', 'unit_value'), _lt('z', '1', 'unit_bound')),)
    body += _call('hBound', 'i') + ('exact hi', 'cases hValue',
        'cases hValue_witness', 'trans x')
    body += _call('beta_at_unique', 'b', 'c', 'i', 'a', 'x') + (
        'exact ha', 'exact hValue_witness_left',)
    body += _below_one_zero('x', 'hValue_witness_right')
    rows.append(spec('jordan_tuple_bounded_one_entry_zero', _contract(args, (
        _bounded('b', 'c', 'k', '1', 'unit_tuple'),
        _lt('i', 'k', 'unit_index'), _at('b', 'c', 'i', 'a', 'unit_entry')), 'a=0'),
        ('beta_at_unique', 'le_zero', 'le_of_succ_le_succ'), body,
        'Every decoded coordinate in a tuple bounded by one equals zero.'))

    body = _intro('k', 'i', 'hi') + ('exists 0', 'split',)
    body += _call('finite_beta_zero_code', 'i') + ('exists 0', 'simp')
    rows.append(spec('jordan_zero_tuple_bounded_one', _contract(('k',), (),
        _bounded('0', '0', 'k', '1', 'unit_zero_tuple')),
        ('finite_beta_zero_code',), body,
        'The literal beta tuple (0,0) has every coordinate below one, at every length.'))

    args = ('b', 'c', 'd', 'e', 'k')
    body = _intro(*args, 'hLeft', 'hRight', 'i', 'a', 'z', 'hi', 'ha', 'hz') + ('trans 0',)
    body += ('apply jordan_tuple_bounded_one_entry_zero',
        'exact hLeft', 'exact hi', 'exact ha', 'symm')
    body += ('apply jordan_tuple_bounded_one_entry_zero',
        'exact hRight', 'exact hi', 'exact hz')
    rows.append(spec('jordan_tuples_bounded_one_equal', _contract(args, (
        _bounded('b', 'c', 'k', '1', 'unit_left'),
        _bounded('d', 'e', 'k', '1', 'unit_right')),
        _equal('b', 'c', 'd', 'e', 'k', 'unit_equal')),
        ('jordan_tuple_bounded_one_entry_zero',), body,
        'Any two canonical tuples modulo one represent the same coordinate tuple.'))

    body = _intro('k') + ('split',) + _intro('i', 'hi') + (
        'exists 0', 'exists 0', 'split', 'split')
    body += _call('finite_beta_zero_code', 'i') + _call('finite_beta_zero_code', 'i')
    body += ('split',) + _call('jordan_zero_tuple_bounded_one', 'k')
    body += _call('jordan_primitive_tuple_modulus_one', '0', '0', 'k')
    body += ('split',) + _intro('b', 'c', 'hBound', 'hPrimitive') + (
        'exists 0', 'exists 0', 'exists 0', 'split', 'exists 0', 'simp', 'split', 'split')
    body += _call('finite_beta_zero_code', '0') + _call('finite_beta_zero_code', '0')
    body += _call('jordan_tuples_bounded_one_equal', 'b', 'c', '0', '0', 'k') + ('exact hBound',)
    body += _call('jordan_zero_tuple_bounded_one', 'k')
    body += _intro('i', 'h', 'b', 'c', 'd', 'e', 'hi', 'hh', 'hFirst', 'hSecond', 'hEqual')
    body += ('trans 0',) + _below_one_zero('i', 'hi') + ('symm',) + _below_one_zero('h', 'hh')
    rows.append(spec('jordan_unit_modulus_singleton_enumeration', _contract(('k',), (),
        base._enumeration('k', '1', '0', '0', '0', '0', '1', 'unit_enumeration')),
        ('finite_beta_zero_code', 'jordan_zero_tuple_bounded_one',
         'jordan_primitive_tuple_modulus_one', 'jordan_tuples_bounded_one_equal',
         'le_zero', 'le_of_succ_le_succ'), body,
        'An actual one-position beta list is sound, complete and duplicate-free for primitive tuples modulo one.'))

    body = _intro('k', 'hk') + ('split', 'exact hk', 'split',)
    body += _call('succ_ne_zero', '0') + ('exists 0',) * 4
    body += _call('jordan_unit_modulus_singleton_enumeration', 'k')
    rows.append(spec('jordan_totient_at_one', _contract(('k',), ('~(k=0)',),
        base._jordan('k', '1', '1', 'unit_count')),
        ('succ_ne_zero', 'jordan_unit_modulus_singleton_enumeration'), body,
        'For every positive rank k, J_k(1)=1, proved by the explicit singleton enumeration.'))

    body = _intro('k', 'j', 'hCount') + ('have hPositive : ~(k=0)', 'cases hCount',
        'exact hCount_left',)
    body += _call('jordan_totient_count_unique', 'k', '1', 'j', '1') + ('exact hCount',)
    body += _call('jordan_totient_at_one', 'k') + ('exact hPositive',)
    rows.append(spec('jordan_totient_at_one_unique', _contract(('k', 'j'), (
        base._jordan('k', '1', 'j', 'unit_arbitrary_count'),), 'j=1'),
        ('jordan_totient_count_unique', 'jordan_totient_at_one'), body,
        'Every genuine Jordan count modulo one equals one, independently of its beta encoding.'))
    return tuple(rows)
