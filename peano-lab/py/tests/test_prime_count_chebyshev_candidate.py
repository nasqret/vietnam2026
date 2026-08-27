"""Original-kernel checks for the additive exact prime-count candidates."""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from itertools import product
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Forall, Imp, parse_formula_with_names
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.prime_count_chebyshev_candidate import (
    _le, _length, cutoff_bit_prefix, make_prime_count_chebyshev_candidate_theorems,
    prime_bit_prefix, prime_count,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
ROWS = make_prime_count_chebyshev_candidate_theorems(TheoremSpec)
NAMES_SHA256 = "ae973727c4ad4e3157e353a19d4d4c2c2dacca967d154f83914bf8ebc813e9fb"
ROOT_SHA256 = "38a80957c2e9e9545cf57e1a036768d506a64edd891be2d0125ffd499fab7428"
EXPECTED_NODES = (
    15, 24, 24, 40, 72, 27, 24, 19, 52, 106, 53, 280, 285, 25, 27, 27,
    55, 75, 39, 188, 106, 33, 33, 129, 97, 40, 44, 53, 105, 125, 106, 111,
    63, 48, 76, 50, 66, 210, 38, 109, 210, 297, 38, 65, 93, 160, 274,
    77, 47, 75, 84, 114, 30, 73, 19,
)


@lru_cache(maxsize=1)
def _hypotheses():
    # Pinned source statements are only authoring hypotheses. Admission needs
    # actual dependency-closed bodies and independent kernel/Lean acceptance.
    raw = (ROOT / "artifacts/peano-library/alpha/catalog-v26.json").read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["checked_use_count"] == 2138
    return {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row["summary"])
        for row in catalog["theorems"]
    } | {row.name: row for row in ROWS}


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.name)
def test_candidate_body(row):
    receipt, = replay_candidate_bodies((row,), core=_hypotheses())
    assert receipt.name == row.name
    assert receipt.proof_nodes == EXPECTED_NODES[ROWS.index(row)]
    assert receipt.proof_depth <= 64


def test_inventory_and_actual_topological_dependencies():
    assert len(ROWS) == 55
    assert sha256("\n".join(row.name for row in ROWS).encode()).hexdigest() == NAMES_SHA256
    assert sum(len(row.dependencies) for row in ROWS) == 239
    assert sum(len(row.script) for row in ROWS) == 2621
    assert sum(EXPECTED_NODES) == 4755
    available = set(_hypotheses()) - {row.name for row in ROWS}
    for row in ROWS:
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert _closed_formula(row.statement)
        assert all(command not in {"sorry", "admit"} and not command.startswith("use ") and "DNE" not in command for command in row.script)
        available.add(row.name)


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.name)
def test_altered_conclusion_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=f"({row.statement}) /\\ false"),), core=_hypotheses())


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.name)
def test_truncated_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_hypotheses())


@pytest.mark.parametrize(("name", "dependency"), tuple((row.name, dependency) for row in ROWS for dependency in row.dependencies))
def test_every_declared_dependency_is_needed(name, dependency):
    row = next(row for row in ROWS if row.name == name)
    forged = replace(row, dependencies=tuple(item for item in row.dependencies if item != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_hypotheses())


def test_exact_G027_formula_has_no_extra_premises_or_valuation_or_power_oracle():
    root = next(row for row in ROWS if row.name == "prime_count_chebyshev_bounds")
    assert sha256(root.statement.encode()).hexdigest() == ROOT_SHA256
    expected = (
        f"forall N ell k. ({_le('2','N',tag='audit_positive')}) -> "
        f"({_length('N','ell',tag='audit_length')}) -> ({prime_count('N','k',tag='audit_count')}) -> "
        f"({_le('N','8 * k * ell',tag='audit_lower')}) /\\ ({_le('k * ell','8 * N',tag='audit_upper')})"
    )
    assert _closed_formula(root.statement) == _closed_formula(expected)
    formula = _closed_formula(root.statement)
    for _ in range(3):
        assert isinstance(formula, Forall)
        formula = formula.body
    for _ in range(3):
        assert isinstance(formula, Imp)
        formula = formula.right
    assert isinstance(formula, And)


DEFINITIONS = (
    (prime_bit_prefix, ("b", "c", "l")),
    (prime_count, ("N", "k")),
    (cutoff_bit_prefix, ("u", "b", "c", "d", "f", "l")),
)


@pytest.mark.parametrize(("builder", "arguments"), DEFINITIONS)
def test_definition_alpha_renaming_and_exact_free_variables(builder, arguments):
    first, names = parse_formula_with_names(builder(*arguments, tag="audit_first"))
    second, others = parse_formula_with_names(builder(*arguments, tag="audit_second"))
    assert first == second and names == others
    assert set(names) == set(arguments)


@pytest.mark.parametrize(("builder", "arguments"), DEFINITIONS)
@pytest.mark.parametrize("invalid", ("S", "x y", "x -> false", "", 7))
def test_definition_arguments_reject_syntax_injection(builder, arguments, invalid):
    with pytest.raises((ValueError, TypeError)):
        builder(invalid, *arguments[1:], tag="audit")


@pytest.mark.parametrize(("builder", "arguments"), DEFINITIONS)
def test_definition_arguments_reject_binder_capture(builder, arguments):
    with pytest.raises(ValueError):
        builder("pc_index_audit", *arguments[1:], tag="audit")


def _sieve(n):
    prime = [True] * (n + 1)
    prime[:2] = [False, False]
    for p in range(2, n + 1):
        if prime[p]:
            for multiple in range(p * p, n + 1, p):
                prime[multiple] = False
    return prime


def test_exact_numerical_boundaries_and_power_thresholds():
    # Examples, not theorem evidence. The quantified result is checked above.
    primes = _sieve(10000)
    count = 0
    for n, is_prime in enumerate(primes):
        count += is_prime
        if n < 2:
            assert count == 0
            continue
        ell = n.bit_length()
        assert n <= 8 * count * ell
        assert count * ell <= 8 * n
        if ell >= 5:
            h = (ell - 1) // 2
            threshold = 2 ** h
            large = sum(primes[threshold + 1:n + 1])
            assert h >= 2 and threshold * threshold <= n
            assert ell <= 2 * threshold and ell <= 3 * h
            assert count <= threshold + large
            assert h * large <= 2 * n


def test_zero_base_and_empty_bit_weighted_product_boundaries():
    for length in range(6):
        for bits in product((0, 1), repeat=length):
            for base in (0, 1, 2, 3):
                upper = 1
                lower = 1
                for bit in bits:
                    upper *= base if bit else 1
                    lower *= base + 1 if bit else 2
                assert upper <= base ** sum(bits)
                assert base ** sum(bits) <= lower
