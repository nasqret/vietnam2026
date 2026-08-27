"""Fresh-process checks for prime adjunction in actual finite unit counts."""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
import json
from math import gcd
import os
from pathlib import Path
import resource
import subprocess
import sys

import pytest

from peano_lab.library import euler_totient_prime_step_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec
from test_euler_totient_count_candidate import ROOT, core, rows as count_rows, assert_family_contract
from test_euler_totient_interval_candidate import rows as interval_rows


@lru_cache(maxsize=1)
def rows():
    return candidate.make_euler_totient_prime_step_candidate_theorems(TheoremSpec)


BODY_PROFILES = dict(zip((row.name for row in rows()), (
    (17,9,17), (41,24,41), (78,22,78), (56,20,56), (33,16,33),
    (38,17,38), (35,20,35), (54,29,54), (91,42,91), (44,22,44),
    (48,22,48), (28,12,28), (114,40,103), (211,46,208), (162,45,161),
    (70,32,70), (41,26,41),
), strict=True))


def check_body(name: str, mutation: str = "none"):
    table = core() | {row.name: row for row in (*count_rows(), *interval_rows(), *rows())}
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
    assert_family_contract(rows(), (*count_rows(), *interval_rows()), (17, 59, 622, "80d145d2e972209bf26dba18d2d93b0733472d634428aa98f14667b906c9148a"))


@pytest.mark.parametrize("p", (2, 3, 5, 7, 11))
@pytest.mark.parametrize("n", range(1, 25))
def test_independent_prime_step_including_repeated_factors_and_one(p, n):
    old = sum(gcd(i,n) == 1 for i in range(n))
    new = sum(gcd(i,n*p) == 1 for i in range(n*p))
    assert new == (p if n % p == 0 else p-1) * old
    if n % p != 0:
        assert new + old == p * old
        for j in range(n):
            first = sum(gcd(i,n) == 1 for i in range(p*j,p*(j+1)))
            second = sum(gcd(i,n*p) == 1 for i in range(p*j,p*(j+1)))
            assert first == second + (gcd(j,n) == 1)


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
