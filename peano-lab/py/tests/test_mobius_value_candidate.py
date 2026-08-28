"""Non-admitting Möbius body and definition checks over exact frozen v30 data."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from math import isqrt
from pathlib import Path
import re

import pytest

from peano_lab.library import mobius_value_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.foundation_saturation_candidate import _factorization
from peano_lab.library.squarefree_decomposition_candidate import _squarefree
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts/peano-library/alpha/catalog-v30.json"
PARENT_SHA256 = "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"


@lru_cache(maxsize=1)
def core():
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 3222
    assert catalog["stable_count"] == 432
    # These are curried-body hypotheses, not a reconstructed closed certificate.
    return {row["name"]: TheoremSpec(
        row["name"], row["statement"], tuple(row["dependencies"]),
        tuple(row["script"]), row["summary"]
    ) for row in catalog["theorems"]}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_mobius_value_candidate_theorems(TheoremSpec)


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_original_kernel_body(row):
    try:
        checked = replay_candidate_bodies((row,), core=core() | {r.name: r for r in rows()})[0]
        assert checked.name == row.name
        assert checked.proof_depth <= 256
        assert checked.proof_objects <= checked.proof_nodes
        print(f"{row.name}: {checked.proof_nodes}/{checked.proof_depth}/{checked.proof_objects}")
    finally:
        gc.collect()


def test_additive_topology_and_native_commands():
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        assert all(re.search(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", "\n".join(row.script))
                   for name in row.dependencies)
        assert not any(command.startswith(("use ", "admit", "sorry", "DNE", "ring")) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def _expected_sign(n, z):
    return f"((exists k. ({n}) = 2 * k) /\\ ({z}) = 2) \\/ ((exists j. ({n}) = 2 * j + 1) /\\ ({z}) = 1)"


def _expected_mu(n, z):
    squared = f"exists p. (~(p = 1) /\\ forall a b. p = a * b -> a = 1 \\/ b = 1) /\\ exists q. ({n}) = (p * p) * q"
    factor_sign = (
        f"exists b c l. ({_factorization(n,'b','c','l','independent_mv_factor')}) /\\ "
        f"({_expected_sign('l',z)})"
    )
    return (
        f"~(({n}) = 0) /\\ ((({squared}) /\\ ({z}) = 0) \\/ "
        f"(({_squarefree(n,'independent_mv_sf')}) /\\ ({factor_sign})))"
    )


def test_mobius_definition_is_independent_factor_data_not_sum_cancellation():
    actual = candidate.mobius_value_relation('n','z',tag='independent',variables=('n','z'))
    assert _closed_formula('forall n z. '+actual) == _closed_formula('forall n z. '+_expected_mu('n','z'))
    expected = 'forall n. ~(n=0) -> exists z. ('+_expected_mu('n','z')+')'
    row = next(row for row in rows() if row.name == 'mobius_value_exists')
    assert _closed_formula(row.statement) == _closed_formula(expected)


@pytest.mark.parametrize('n,z', [('n+1','z'), ('n*n','z+z'), ('0','2'), ('12345678901234567890','z')])
def test_public_mobius_accepts_real_compound_terms(n,z):
    actual = candidate.mobius_value_relation(n,z,tag='terms',variables=('n','z'))
    assert _closed_formula('forall n z. '+actual) == _closed_formula('forall n z. '+_expected_mu(n,z))


@pytest.mark.parametrize('n,z', [('n','z'),('n+1','z*z'),('0','2')])
def test_public_factor_sign_is_real_factorization_and_parity(n,z):
    actual = candidate.prime_factor_parity_sign_relation(n,z,tag='parity',variables=('n','z'))
    expected = f"exists b c l. ({_factorization(n,'b','c','l','independent_factor_sign')}) /\\ ({_expected_sign('l',z)})"
    assert _closed_formula('forall n z. '+actual) == _closed_formula('forall n z. '+expected)


@pytest.mark.parametrize('builder,args', [
    (candidate.mobius_value_relation,('n','z')),
    (candidate.alternating_signed_unit_relation,('n','z')),
    (candidate.has_prime_square_divisor_relation,('n',)),
    (candidate.prime_factor_parity_sign_relation,('n','z')),
])
def test_all_generated_binders_are_checked_against_full_context(builder,args):
    source = builder(*args,tag='capture',variables=('n','z'))
    binders = set()
    for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source):
        binders.update(group.split())
    assert binders
    for binder in sorted(binders):
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=('n','z',binder))


@pytest.mark.parametrize('tag,variables,n,z', [
    ('bad tag',('n','z'),'n','z'), ('valid',(), '0','0'),
    ('valid',('n','n'),'n','n'), ('valid',('n','z'),'missing','z'),
    ('valid',('n','z'),'n -> n','z'),
    ('test',('mv_square_prime_testsquare','z'),'mv_square_prime_testsquare','z'),
    ('test',('mv_factor_code_testfactors','z'),'mv_factor_code_testfactors','z'),
    ('test',('mv_even_half_testfactorsparityeven','z'),'mv_even_half_testfactorsparityeven','z'),
])
def test_public_mobius_rejects_bad_terms_and_generated_capture(tag,variables,n,z):
    with pytest.raises(ValueError):
        candidate.mobius_value_relation(n,z,tag=tag,variables=variables)


@pytest.mark.parametrize('name', ('mobius_value_exists','mobius_value_functional','mobius_one'))
def test_poisoned_principal_statement_is_rejected(name):
    row = next(row for row in rows() if row.name == name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0 = 1'),),core=core() | {r.name:r for r in rows()})


def test_positive_domain_guard_cannot_be_removed():
    row = next(row for row in rows() if row.name == 'mobius_value_exists')
    poisoned = replace(row,statement='forall n. exists z. ('+_expected_mu('n','z')+')')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((poisoned,),core=core() | {r.name:r for r in rows()})


def _integer_mu(n):
    if n < 1:
        raise ValueError('Möbius here is defined only at positive inputs')
    count = 0
    p = 2
    while p <= isqrt(n):
        if n % p == 0:
            n //= p
            count += 1
            if n % p == 0:
                return 0
        p += 1
    if n != 1:
        count += 1
    return (-1) ** count


@pytest.mark.parametrize('n,value', [(1,1),(2,-1),(3,-1),(4,0),(6,1),(12,0),(30,-1),(210,1),(2310,-1),(99991,-1)])
def test_independent_integer_boundary_examples(n,value):
    assert _integer_mu(n) == value


def test_zero_has_no_model_value():
    with pytest.raises(ValueError):
        _integer_mu(0)


if __name__ == '__main__':
    import argparse
    import resource
    import signal
    import sys
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument('--body')
    arguments = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started = time.monotonic()
    selected = tuple(row for row in rows() if arguments.body is None or row.name == arguments.body)
    if not selected:
        raise SystemExit('unknown theorem body')
    for row in selected:
        report = replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        print(json.dumps({'name':row.name,'proof_nodes':report.proof_nodes,'proof_depth':report.proof_depth,
                          'proof_objects':report.proof_objects}),flush=True)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
    assert peak <= 1536 * 1024 * 1024
    print(json.dumps({'body_count':len(selected),'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
