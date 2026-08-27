"""Exact, bounded kernel checks for the first-prime enumeration campaign."""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.prime_enumeration_candidate import (
    initial_prime_chain_relation, make_prime_enumeration_candidate_theorems,
    next_prime_relation, prime_list_relation,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT_SHA256 = "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
ROWS = make_prime_enumeration_candidate_theorems(TheoremSpec)
NAMES_SHA256 = "e825e8c48261a136f77575ec7505919456ec3badd0796dbbadb59f64e56eeec9"
ROOT_SHA256 = "b69363aca6a0a887d3baba0ca6ddd13a550496075f15ec2cb4199e7c73054676"
EXPECTED_NODES = (78, 30, 67, 35, 31, 35, 115, 42, 82, 155, 81, 120, 193, 12, 104, 115, 120, 31)


@lru_cache(maxsize=1)
def _hypotheses():
    payload = (ROOT / "artifacts/peano-library/alpha/catalog-v27.json").read_bytes()
    assert sha256(payload).hexdigest() == PARENT_SHA256
    catalog = json.loads(payload)
    assert catalog["checked_use_count"] == 2560
    return {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row["summary"])
        for row in catalog["theorems"]
    } | {row.name: row for row in ROWS}


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.name)
def test_candidate_body(row):
    receipt, = replay_candidate_bodies((row,), core=_hypotheses())
    assert receipt.name == row.name
    assert receipt.proof_nodes == EXPECTED_NODES[ROWS.index(row)]
    assert receipt.proof_depth <= 57


def test_actual_topological_inventory():
    assert len(ROWS) == 18
    assert sha256("\n".join(row.name for row in ROWS).encode()).hexdigest() == NAMES_SHA256
    assert sum(len(row.dependencies) for row in ROWS) == 74
    assert sum(len(row.script) for row in ROWS) == 802
    assert sum(EXPECTED_NODES) == 1446
    available = set(_hypotheses()) - {row.name for row in ROWS}
    for row in ROWS:
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert _closed_formula(row.statement)
        assert not any(command in {"sorry", "admit"} or command.startswith("use ") or "DNE" in command for command in row.script)
        available.add(row.name)


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.name)
def test_false_strengthening_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=f"({row.statement}) /\\ false"),), core=_hypotheses())


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.name)
def test_truncated_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_hypotheses())


@pytest.mark.parametrize(("row", "dependency"), tuple((row, dep) for row in ROWS for dep in row.dependencies), ids=lambda item: item.name if type(item) is TheoremSpec else item)
def test_every_declared_dependency_is_used(row, dependency):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, dependencies=tuple(dep for dep in row.dependencies if dep != dependency)),), core=_hypotheses())


DEFINITIONS = ((next_prime_relation, ("a", "p")), (initial_prime_chain_relation, ("b", "c", "k")), (prime_list_relation, ("b", "c", "k")))


@pytest.mark.parametrize(("builder", "arguments"), DEFINITIONS)
def test_definitions_are_alpha_invariant_and_have_exact_free_parameters(builder, arguments):
    left, names = parse_formula_with_names(builder(*arguments, tag="audit_left"))
    right, other = parse_formula_with_names(builder(*arguments, tag="audit_right"))
    assert left == right and names == other
    assert set(names) == set(arguments)


@pytest.mark.parametrize(("builder", "arguments"), DEFINITIONS)
@pytest.mark.parametrize("invalid", ("", "S", "x y", "x -> false", 3, "pen_index_audit"))
def test_definition_boundary_rejects_capture_and_syntax_injection(builder, arguments, invalid):
    with pytest.raises((ValueError, TypeError)):
        builder(invalid, *arguments[1:], tag="audit")


def test_G022_constructs_both_powers_and_an_exhaustive_prime_list():
    row = next(row for row in ROWS if row.name == "first_primes_double_exponential_bound")
    assert sha256(row.statement.encode()).hexdigest() == ROOT_SHA256
    formula = _closed_formula(row.statement)
    assert isinstance(formula, Forall)
    assert isinstance(formula.body, Imp)
    witnesses = formula.body.right
    for _ in range(6):
        assert isinstance(witnesses, Exists)
        witnesses = witnesses.body
    # The sole premise is k != 0. Neither the list nor any exponentiation
    # value nor an unproved next-prime oracle is supplied as an assumption.
    assert _closed_formula("forall k. ~(k = 0)").body == formula.body.left


def _is_prime(n):
    return n >= 2 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def test_small_exhaustive_lists_and_effective_bound_examples():
    # Finite illustrations, not proof authority. Never materialize an
    # unbounded double-exponential numeral in the host checker.
    values = [n for n in range(2, 750) if _is_prime(n)][:128]
    assert len(values) == 128
    for k, p in enumerate(values, start=1):
        assert values[:k] == [q for q in range(2, p + 1) if _is_prime(q)]
        assert p < 2 ** (k + 1)
        assert k + 1 <= 2 ** k
        if k <= 10:
            assert p < 2 ** (2 ** k)


@pytest.mark.parametrize("bad_list", ([2, 5], [2, 3, 3], [2, 3, 9], [3], [2, 5, 7]))
def test_skipped_repeated_composite_and_wrong_initial_examples_are_not_prime_lists(bad_list):
    expected = [p for p in range(2, max(bad_list) + 1) if _is_prime(p)]
    assert bad_list != expected
