"""Fresh original-kernel checks of prime powers and true multiplicativity."""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import json
from math import gcd
import os
from pathlib import Path
import resource
import subprocess
import sys

import pytest

from peano_lab.library import euler_totient_algebra_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from peano_lab.library.fermat_residue_product_candidate import coprime
from test_euler_totient_count_candidate import ROOT, core, rows as count_rows, assert_family_contract
from test_euler_totient_interval_candidate import rows as interval_rows
from test_euler_totient_prime_step_candidate import rows as step_rows


@lru_cache(maxsize=1)
def rows():
    return candidate.make_euler_totient_algebra_candidate_theorems(TheoremSpec)


BODY_PROFILES = dict(zip((row.name for row in rows()), (
    (53,23,53), (60,28,60), (80,38,80), (150,33,150), (79,32,79),
    (23,14,23), (203,39,203), (239,50,239), (41,25,41),
), strict=True))


def check_body(name: str, mutation: str = "none"):
    table = core() | {row.name: row for row in (*count_rows(), *interval_rows(), *step_rows(), *rows())}
    row = table[name]
    if mutation == "false_conclusion":
        row = replace(row, statement=f"({row.statement}) /\\ false")
    elif mutation == "truncated_body":
        row = replace(row, script=row.script[:-1])
    elif mutation == "removed_dependency":
        row = replace(row, dependencies=row.dependencies[:-1])
    elif mutation == "corrupt_dependency":
        dependency = row.dependencies[0]
        table = table | {dependency: replace(table[dependency], statement="0=0")}
    if mutation != "none":
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,), core=table)
        return {"mutation": mutation, "rejected": True}
    return asdict(replay_candidate_bodies((row,), core=table)[0])


def isolated_body(name: str, mutation: str = "none"):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "peano-lab/py"), str(ROOT / "scripts")))
    checked = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--body", name, mutation],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=60,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    return json.loads(checked.stdout)


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_original_kernel_body_in_fresh_process(name):
    receipt = isolated_body(name)
    assert receipt["name"] == name
    assert receipt["proof_nodes"] > 0 and receipt["proof_depth"] <= 256
    assert (receipt["proof_nodes"], receipt["proof_depth"], receipt["proof_objects"]) == BODY_PROFILES[name]


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
@pytest.mark.parametrize("mutation", ("false_conclusion", "truncated_body"))
def test_negative_proof_mutation_in_fresh_process(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


@pytest.mark.parametrize("name", tuple(row.name for row in rows() if row.dependencies))
@pytest.mark.parametrize("mutation", ("removed_dependency", "corrupt_dependency"))
def test_dependency_authority_mutation_in_fresh_process(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


def test_exact_family_profile_and_all_local_formulas():
    assert_family_contract(rows(), (*count_rows(), *interval_rows(), *step_rows()), (9, 65, 570, "6a65c75747200de093be5b28a661ff0ac104431965b64b16e98aa53469478638"))


@pytest.mark.parametrize("name,digest", (
    ("totient_prime_power_value", "5a77436d23c80965981715a3196f5669122f4184a3201c19955d7fdfcdfb10f0"),
    ("totient_coprime_multiplicative", "13319c5d902961834ee8b29318cc2bee30c5e5c77bee7443756e7fe40a832e11"),
))
def test_principal_algebra_statement_hashes(name, digest):
    assert sha256(next(row.statement for row in rows() if row.name == name).encode()).hexdigest() == digest


def test_unconditional_multiplicativity_has_no_supplied_factor_list_or_crt_trace():
    from peano_lab.library.euler_totient_count_candidate import totient_relation
    actual = next(row.statement for row in rows() if row.name == "totient_coprime_multiplicative")
    expected = (
        f"forall a b u v. ({totient_relation('a','u',tag='first')}) -> ({totient_relation('b','v',tag='second')}) -> "
        f"({coprime('a','b',tag='coprime')}) -> ({candidate._phi('a*b','u*v',tag='product')})"
    )
    assert _closed_formula(actual) == _closed_formula(expected)


@pytest.mark.parametrize("a", range(1, 14))
@pytest.mark.parametrize("b", range(1, 14))
def test_independent_multiplicativity_numeric_reference(a, b):
    phi = lambda n: sum(gcd(i,n) == 1 for i in range(n))
    if gcd(a,b) == 1:
        assert phi(a*b) == phi(a)*phi(b)
    elif (a,b) == (2,2):
        assert phi(a*b) != phi(a)*phi(b)


@pytest.mark.parametrize("p", (2, 3, 5, 7))
@pytest.mark.parametrize("e", (1, 2, 3, 4))
def test_independent_positive_prime_power_count(p, e):
    assert sum(gcd(i,p**e) == 1 for i in range(p**e)) == p**(e-1)*(p-1)


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
