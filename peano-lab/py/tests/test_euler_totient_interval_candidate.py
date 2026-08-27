"""Fresh-process tests for actual unit interval balance and periodicity."""

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

from peano_lab.library import euler_totient_interval_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec
from test_euler_totient_count_candidate import ROOT, core, rows as count_rows, assert_family_contract


@lru_cache(maxsize=1)
def rows():
    return candidate.make_euler_totient_interval_candidate_theorems(TheoremSpec)


BODY_PROFILES = dict(zip((row.name for row in rows()), (
    (27,15,27), (17,11,17), (21,12,21), (91,27,91), (205,48,203),
    (121,37,121), (68,31,68), (85,26,85), (87,29,86), (17,11,17),
    (16,10,16), (41,20,41),
), strict=True))


def check_body(name: str, mutation: str = "none"):
    table = core() | {row.name: row for row in (*count_rows(), *rows())}
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
    assert_family_contract(rows(), count_rows(), (12, 32, 458, "8cd6e1d627572f34f7e1e61531ac2165092c14e2ea467195d00afe3afca30cf2"))


@pytest.mark.parametrize("n", range(17))
@pytest.mark.parametrize("k", (0, 1, 2, 5))
def test_independent_actual_count_of_complete_periods(n, k):
    actual = sum(gcd(i, n) == 1 for i in range(n * k))
    canonical = sum(gcd(i, n) == 1 for i in range(n))
    assert actual == k * canonical


@pytest.mark.parametrize("n", range(1, 13))
@pytest.mark.parametrize("a,b,length", ((0, 0, 0), (0, 1, 7), (1, 4, 11), (4, 2, 5)))
def test_independent_interval_balance_on_shifted_full_periods(n, a, b, length):
    first, second = n * a, n * b
    assert all((gcd(first+i,n) == 1) == (gcd(second+i,n) == 1) for i in range(length))
    count = lambda length: sum(gcd(i,n) == 1 for i in range(length))
    assert count(first+length)+count(second) == count(second+length)+count(first)


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
