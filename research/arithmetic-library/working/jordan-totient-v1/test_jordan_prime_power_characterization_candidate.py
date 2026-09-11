"""Independent contracts and beta-tuple models; native replay needs a slot."""
from dataclasses import replace
from functools import lru_cache
import importlib.util
from itertools import product
from pathlib import Path

import pytest
from peano_lab.library.prime_valuation_support_candidate import make_prime_valuation_support_candidate_theorems
from peano_lab.library.bertrand_power_growth_candidate import make_bertrand_power_growth_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula

HERE = Path(__file__).resolve().parent


def load(name, filename):
    loader = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


base = load('_independent_jordan_power_base', 'test_jordan_totient_candidate.py')
source = load('_independent_jordan_power_candidate', 'jordan_prime_power_characterization_candidate.py')


def Prime(p):
    return f'~({p}=1) /\\ forall pp_a pp_b. {p}=pp_a*pp_b -> pp_a=1 \\/ pp_b=1'


def Pow(p, e, n):
    repeat = (f'forall pp_i. ({base.Lt("pp_i", e)}) -> '
              f'({base.At("pp_B", "pp_C", "pp_i", p)})')
    step = (f'forall pp_i. ({base.Lt("pp_i", e)}) -> exists pp_a pp_r pp_s. '
            + base.And(base.At('pp_B', 'pp_C', 'pp_i', 'pp_a'),
                       base.At('pp_U', 'pp_V', 'pp_i', 'pp_r'),
                       base.At('pp_U', 'pp_V', 'S pp_i', 'pp_s'), 'pp_s=pp_r*pp_a'))
    folded = 'exists pp_U pp_V. ' + base.And(
        base.At('pp_U', 'pp_V', '0', '1'), base.At('pp_U', 'pp_V', e, n), step)
    return 'exists pp_B pp_C. ' + base.And(repeat, folded)


@lru_cache(None)
def rows():
    return source.make_jordan_prime_power_characterization_candidate_theorems(TheoremSpec)


def contracts():
    prim = base.Primitive('n', 'b', 'c', 'k')
    not_all = '~(' + base.AllDvd('p', 'b', 'c', 'k') + ')'
    return (
        base.Contract('p n b c k', [Prime('p'), base.Dvd('p', 'n'), prim], not_all),
        base.Contract('p e n b c k', [Prime('p'), Pow('p', 'e', 'n'), not_all], prim),
        base.Contract('p h n b c k', [Prime('p'), Pow('p', 'S h', 'n')],
                      base.And('(' + prim + ') -> (' + not_all + ')',
                               '(' + not_all + ') -> (' + prim + ')')),
        base.Contract('p h j m n b c k', [Prime('p'), Pow('p', 'S h', 'm'),
                      Pow('p', 'S j', 'n'), base.Primitive('m', 'b', 'c', 'k')], prim),
    )


@pytest.mark.parametrize('index', range(4))
def test_independent_full_statement_with_no_supplied_characterization(index):
    assert _closed_formula(rows()[index].statement) == _closed_formula(contracts()[index])


@lru_cache(None)
def inherited_core():
    core = dict(base.body_core())
    parents = (make_bertrand_power_growth_candidate_theorems(TheoremSpec)
               + make_prime_valuation_support_candidate_theorems(TheoremSpec))
    for row in parents:
        if row.name in core:
            assert _closed_formula(core[row.name].statement) == _closed_formula(row.statement)
        else:
            core[row.name] = row
    return core


def test_real_topological_dependencies_and_no_definition_or_count_change():
    known = dict(inherited_core())
    for row in rows():
        assert row.name not in known
        assert set(row.dependencies) <= known.keys()
        assert len(row.dependencies) == len(set(row.dependencies))
        assert row.script and 'DNE' not in row.script
        known[row.name] = row
    assert not any('count' in row.name or 'jordan_totient' in row.name for row in rows())


@pytest.mark.parametrize('p,e,k', [(2, 1, 0), (2, 1, 1), (2, 2, 2), (3, 1, 2), (3, 2, 1), (5, 1, 1)])
def test_actual_beta_tuples_characterization_including_empty_width_and_recoding(p, e, k):
    for values in product(range(p ** e + 1), repeat=k):
        primitive = base.primitive(p ** e, values)
        expected = not all(a % p == 0 for a in values)
        assert primitive == expected
        for multiplier in (1, 2):
            code, scale = base.encode(values, multiplier)
            decoded = base.decoded(code, scale, k)
            assert decoded == values
            assert base.primitive(p ** (e + 1), decoded) == primitive


def test_prime_and_positive_exponent_are_necessary_for_the_equivalence():
    assert not base.primitive(4, (2,)) and 2 % 4 != 0
    assert base.primitive(1, (0,)) and 0 % 2 == 0


@lru_cache(None)
def body_core():
    return inherited_core() | {row.name: row for row in rows()}


@pytest.mark.parametrize('index', range(4))
def test_native_body(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    row = rows()[index]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name and receipt.command_count == len(row.script)


@pytest.mark.parametrize('index', range(4))
def test_native_false_conclusion_rejected(index):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement='0=1'),), core=body_core())


@pytest.mark.parametrize('index,dependency', [(i, d) for i, row in enumerate(rows()) for d in row.dependencies])
def test_native_removed_dependency_rejected(index, dependency):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    row = rows()[index]
    damaged = replace(row, dependencies=tuple(d for d in row.dependencies if d != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((damaged,), core=body_core())
