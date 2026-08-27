"""Independent unit-count semantics and fresh-process original HA body checks.

The frozen v28 catalogue supplies only curried body hypotheses here. These
tests do not admit the new rows or replace whole-cone HA/Lean verification.
"""

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

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import euler_totient_count_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.fermat_residue_product_candidate import coprime
from peano_lab.library.finite_fold_surface import beta_at, sum_relation
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT_SHA256 = "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9"


@lru_cache(maxsize=1)
def rows():
    return candidate.make_euler_totient_count_candidate_theorems(TheoremSpec)


BODY_PROFILES = dict(zip((row.name for row in rows()), (
    (47,19,47), (17,8,17), (76,19,76), (25,16,25), (25,17,25),
    (41,21,41), (67,26,67), (31,18,31), (25,14,25), (97,42,97),
    (21,12,21), (117,42,117), (57,32,57), (31,18,31), (60,26,60),
    (88,26,88), (31,14,31), (55,18,55), (11,7,11), (43,25,43),
    (27,16,27), (13,8,13), (22,13,22), (23,11,23), (22,15,22),
), strict=True))


@lru_cache(maxsize=1)
def core():
    payload = (ROOT / "artifacts/peano-library/alpha/catalog-v28.json").read_bytes()
    assert sha256(payload).hexdigest() == PARENT_SHA256
    document = json.loads(payload)
    assert document["theorem_count"] == document["checked_use_count"] == 2764
    assert document["stable_count"] == 432
    assert all(row["checked_use"] is True for row in document["theorems"])
    return {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row.get("summary", ""))
        for row in document["theorems"]
    }


def check_body(name: str, mutation: str = "none"):
    table = core() | {row.name: row for row in rows()}
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
    assert receipt["proof_objects"] <= receipt["proof_nodes"]
    assert (receipt["proof_nodes"], receipt["proof_depth"], receipt["proof_objects"]) == BODY_PROFILES[name]


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
@pytest.mark.parametrize("mutation", ("false_conclusion", "truncated_body"))
def test_negative_proof_mutation_in_fresh_process(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


@pytest.mark.parametrize("name", tuple(row.name for row in rows() if row.dependencies))
@pytest.mark.parametrize("mutation", ("removed_dependency", "corrupt_dependency"))
def test_dependency_authority_mutation_in_fresh_process(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


def test_inventory_is_additive_closed_and_constructive():
    available = set(core())
    names = tuple(row.name for row in rows())
    assert len(names) == len(set(names)) == 25
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert not parse_formula_with_names(row.statement)[1]
        for command in row.script:
            assert not command.startswith("use ")
            assert not any(marker in command for marker in ("DNE", "sorry", "admit", "oracle", "axiom"))
        available.add(row.name)


def assert_family_contract(ordered, previous, expected):
    """Exact additive inventory plus ordinary HA syntax for every local claim."""
    assert len(ordered) == expected[0]
    assert sum(len(row.dependencies) for row in ordered) == expected[1]
    assert sum(len(row.script) for row in ordered) == expected[2]
    assert sha256("\n".join(row.name for row in ordered).encode()).hexdigest() == expected[3]
    available = set(core()) | {row.name for row in previous}
    for row in ordered:
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        assert not parse_formula_with_names(row.statement)[1]
        for command in row.script:
            assert not command.startswith("use ")
            assert not any(marker in command for marker in ("DNE", "sorry", "admit", "oracle", "axiom"))
            if command.startswith("have "):
                parse_formula_with_names(command.split(" : ", 1)[1])
        available.add(row.name)


def test_exact_family_profile_and_all_local_formulas():
    assert_family_contract(rows(), (), (25, 48, 617, "55033603f911d408bcb2279da85153470e12ce259ec96fa5d12d172dadc98e0d"))


@pytest.mark.parametrize("name,digest", (
    ("totient_one_value", "c25486aebde25c7405e66abd7d4018c19e607f1c9400ae0b5b15123a6e7b2b17"),
    ("totient_exists_unique", "949c4af14495d74cb45019f5e068fbb45580968e2abf1527f27b80146db77013"),
))
def test_principal_unit_count_statement_hashes(name, digest):
    statement = next(row.statement for row in rows() if row.name == name)
    assert sha256(statement.encode()).hexdigest() == digest


def expected_mask():
    predicate = coprime("i", "n", tag="reference_coprime")
    return (
        "forall i. (exists h. h+S i=l) -> exists e. "
        f"({beta_at('b','c','i','e',tag='reference_entry')}) /\\ "
        f"((({predicate}) /\\ e=1) \\/ (~({predicate}) /\\ e=0))"
    )


def expected_count():
    return f"exists b c. ({expected_mask()}) /\\ ({sum_relation('b','c','l','t',tag='reference_sum')})"


def test_mask_is_the_actual_coprimality_indicator_not_a_product_formula():
    actual = candidate.unit_bit_prefix_relation("n", "b", "c", "l", tag="actual")
    assert _closed_formula("forall n b c l. " + actual) == _closed_formula("forall n b c l. " + expected_mask())
    assert set(parse_formula_with_names(actual)[1]) == {"n", "b", "c", "l"}


def test_unit_count_is_an_actual_sum_of_independently_decided_bits():
    actual = candidate.unit_count_relation("n", "l", "t", tag="actual")
    expected = expected_count()
    assert _closed_formula("forall n l t. " + actual) == _closed_formula("forall n l t. " + expected)
    assert set(parse_formula_with_names(actual)[1]) == {"n", "l", "t"}


def test_phi_keeps_positive_domain_and_the_zero_based_canonical_interval():
    actual = candidate.totient_relation("n", "t", tag="actual")
    count = candidate.unit_count_relation("n", "n", "t", tag="independent")
    assert _closed_formula("forall n t. " + actual) == _closed_formula(f"forall n t. ~(n=0) /\\ ({count})")
    assert set(parse_formula_with_names(actual)[1]) == {"n", "t"}
    zero = candidate._phi("0", "t", tag="zero_boundary")
    statement = next(row.statement for row in rows() if row.name == "totient_zero_excluded")
    assert _closed_formula(statement) == _closed_formula(f"forall t. ~({zero})")


def test_definition_tag_renaming_preserves_every_free_parameter():
    for builder, arguments in (
        (candidate.unit_bit_prefix_relation, ("n", "b", "c", "l")),
        (candidate.unit_count_relation, ("n", "l", "t")),
        (candidate.totient_relation, ("n", "t")),
    ):
        prefix = "forall " + " ".join(arguments) + ". "
        assert _closed_formula(prefix + builder(*arguments, tag="first")) == _closed_formula(prefix + builder(*arguments, tag="second"))


@pytest.mark.parametrize("n", range(1, 33))
def test_independent_residue_interval_reference_includes_phi_one(n):
    zero_based = [i for i in range(n) if gcd(i, n) == 1]
    positive_interval = [i for i in range(1, n + 1) if gcd(i, n) == 1]
    assert len(zero_based) == len(positive_interval)
    assert 1 <= len(zero_based) <= n
    if n == 1:
        assert zero_based == [0] and positive_interval == [1]
    else:
        assert 0 not in zero_based and n not in positive_interval


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "n+t", "a b", "x;y", "eut_code_actual", "fs_u_actual", "ff_h_actual"))
@pytest.mark.parametrize("position", (0, 1))
def test_public_phi_arguments_reject_unsafe_or_capturing_names(bad, position):
    arguments = ["n", "t"]
    arguments[position] = bad
    with pytest.raises(ValueError):
        candidate.totient_relation(*arguments, tag="actual")


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "tag+x", "x;y"))
def test_public_definition_tags_reject_unsafe_fragments(bad):
    with pytest.raises(ValueError):
        candidate.totient_relation("n", "t", tag=bad)


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
