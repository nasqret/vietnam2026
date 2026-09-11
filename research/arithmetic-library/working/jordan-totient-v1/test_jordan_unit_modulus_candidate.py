"""Independent contracts, actual singleton models and original HA judgments."""
from dataclasses import replace
from functools import lru_cache
import pytest

from peano_lab.library.theorems import TheoremSpec, _closed_formula
from peano_lab.library.candidate_validation import replay_candidate_bodies, CandidateBodyError
import jordan_unit_modulus_candidate as source
import test_jordan_totient_candidate as model
import test_jordan_count_uniqueness_candidate as count


@lru_cache(None)
def rows():
    return source.make_jordan_unit_modulus_candidate_theorems(TheoremSpec)


@lru_cache(None)
def core():
    return count.core() | {r.name: r for r in rows()}


def contracts():
    C, B, E = model.Contract, model.Bounded, model.Equal
    return (
        C('b c k i a', [B('b', 'c', 'k', '1'), model.Lt('i', 'k'),
            model.At('b', 'c', 'i', 'a')], 'a=0'),
        C('k', [], B('0', '0', 'k', '1')),
        C('b c d e k', [B('b', 'c', 'k', '1'), B('d', 'e', 'k', '1')],
            E('b', 'c', 'd', 'e', 'k')),
        C('k', [], model.Enum('k', '1', '0', '0', '0', '0', '1')),
        C('k', ['~(k=0)'], model.Jordan('k', '1', '1')),
        C('k j', [model.Jordan('k', '1', 'j')], 'j=1'),
    )


@pytest.mark.parametrize('index', range(6))
def test_exact_contract(index):
    assert _closed_formula(rows()[index].statement) == _closed_formula(contracts()[index])


def test_dependency_order_and_existing_definitions():
    previous = dict(count.core())
    for row in rows():
        assert row.name not in previous
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= previous.keys()
        previous[row.name] = row


@pytest.mark.parametrize('k', range(5))
def test_literal_singleton_represents_all_canonical_tuples(k):
    # The one outer entry decodes to (inner code, inner scale) = (0, 0).
    assert model.decode(0, 0, 0) == 0
    assert tuple(model.decode(0, 0, i) for i in range(k)) == (0,) * k
    assert model.universe(1, k) == [(0,) * k]


def test_rank_zero_is_still_excluded_from_jordan_count():
    statement = contracts()[4]
    assert '~(k=0)' in statement
    assert _closed_formula(statement) != _closed_formula(
        model.Contract('k', [], model.Jordan('k', '1', '1')))


@pytest.mark.parametrize('index', range(6))
def test_native_body(index):
    row = rows()[index]
    receipt, = replay_candidate_bodies((row,), core=core())
    assert receipt.name == row.name and receipt.command_count == len(row.script)


@pytest.mark.parametrize('index', range(6))
def test_native_false_conclusion(index):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement='0=1'),), core=core())


@pytest.mark.parametrize('index,dependency', [
    (i, d) for i, row in enumerate(rows()) for d in row.dependencies])
def test_native_missing_dependency(index, dependency):
    row = rows()[index]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,
            dependencies=tuple(d for d in row.dependencies if d != dependency)),), core=core())
