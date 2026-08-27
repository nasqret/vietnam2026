"""Exact HA body, dependency, definition, and multinomial boundary checks."""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from math import comb, factorial
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.multinomial_kummer_candidate import (
    _choose, _val, beta_valuation_prefix, binary_column_carry_count,
    carry_count_many, make_multinomial_kummer_candidate_theorems, multinomial,
    multinomial_binomial_prefix, multinomial_carry_prefix,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT_CATALOG_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
EXPECTED_NAMES = (
    "beta_valuation_prefix_empty", "beta_valuation_prefix_drop_last",
    "beta_valuation_prefix_last", "beta_valuation_prefix_extend", "beta_valuation_prefix_exists",
    "beta_prime_product_valuation_eq_sum", "beta_prime_product_valuation_from_sum",
    "multinomial_binomial_prefix_empty", "multinomial_binomial_prefix_drop_last",
    "multinomial_binomial_prefix_extend", "multinomial_binomial_prefix_exists",
    "multinomial_binomial_prefix_nonzero", "multinomial_exists_of_sum", "multinomial_exists",
    "multinomial_nonzero", "multinomial_valuations_give_carry_prefix",
    "multinomial_kummer_carry_valuation", "multinomial_empty_values", "multinomial_empty_carry_count",
)
EXPECTED_NODES = (27, 27, 150, 82, 46, 375, 158, 28, 28, 103, 57, 60, 35, 21, 86, 124, 97, 64, 47)
ROOT_STATEMENT_SHA256 = "f69d92599b4eaa9e893e3a4c0e8ab998234bbce6223fbbde949433c1ee7c8266"


@lru_cache(maxsize=1)
def _rows():
    return make_multinomial_kummer_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core():
    # A low-memory hypothesis surface, NOT proof authority. Full closure later
    # checks the actual historical bodies, not these hashes or catalog rows.
    raw = (ROOT / "artifacts/peano-library/alpha/catalog-v26.json").read_bytes()
    assert sha256(raw).hexdigest() == PARENT_CATALOG_SHA256
    catalog = json.loads(raw)
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 2138
    return {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row["summary"])
        for row in catalog["theorems"]
    }


@lru_cache(maxsize=1)
def _receipts():
    core = _core() | {row.name: row for row in _rows()}
    # One theorem per call; no retained live proof certificates.
    return tuple(replay_candidate_bodies((row,), core=core)[0] for row in _rows())


def _row(name):
    return next(row for row in _rows() if row.name == name)


def test_inventory_and_actual_dependency_order():
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == "7733a3cb6bbd7327a9d443eea98082fd75d3556d69467f856fee8d48894f73ce"
    assert sum(len(row.dependencies) for row in _rows()) == 55
    assert sum(len(row.script) for row in _rows()) == 841
    available = set(_core())
    for row in _rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert _closed_formula(row.statement)
        assert all(command not in {"sorry", "admit"} and not command.startswith("use ") and "DNE" not in command for command in row.script)
        available.add(row.name)


def test_every_body_is_accepted_by_the_original_intuitionistic_kernel():
    assert tuple(receipt.name for receipt in _receipts()) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in _receipts()) == EXPECTED_NODES
    assert max(receipt.proof_nodes for receipt in _receipts()) <= 375
    assert max(receipt.proof_depth for receipt in _receipts()) <= 64


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_conclusions_are_rejected(name):
    row = _row(name)
    forged = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {item.name: item for item in _rows()})


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_bodies_are_rejected(name):
    row = _row(name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_core() | {item.name: item for item in _rows()})


@pytest.mark.parametrize(("name", "dependency"), tuple((row.name, dependency) for row in _rows() for dependency in row.dependencies))
def test_every_claimed_dependency_is_actually_needed(name, dependency):
    row = _row(name)
    forged = replace(row, dependencies=tuple(item for item in row.dependencies if item != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {item.name: item for item in _rows()})


def test_full_multinomial_endpoint_has_only_prime_and_actual_multinomial_premises():
    row = _row("multinomial_kummer_carry_valuation")
    assert sha256(row.statement.encode()).hexdigest() == ROOT_STATEMENT_SHA256
    expected = (
        "forall p b c l n z. "
        f"({prime('p', tag='audit_prime')}) -> ({multinomial('b', 'c', 'l', 'n', 'z', tag='audit_multinomial')}) -> "
        f"exists e. ({_val('p', 'z', 'e', tag='audit_value')}) /\\ ({carry_count_many('p', 'b', 'c', 'l', 'e', tag='audit_carries')})"
    )
    assert _closed_formula(row.statement) == _closed_formula(expected)
    formula = _closed_formula(row.statement)
    for _ in range(6):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp) and isinstance(formula.right, Imp)
    result = formula.right.right
    assert isinstance(result, Exists) and isinstance(result.body, And)


def test_binary_carry_definition_is_exactly_the_existing_full_kummer_conclusion():
    expected = (
        "forall p a b C v. "
        f"({prime('p', tag='binary_prime')}) -> ({_choose('a + b', 'a', 'C', tag='binary_choose')}) -> "
        f"({_val('p', 'C', 'v', tag='binary_value')}) -> ({binary_column_carry_count('p', 'a', 'b', 'v', tag='binary_count')})"
    )
    assert _closed_formula(expected) == _closed_formula(_core()["kummer_binomial_carry_bit_count"].statement)


DEFINITIONS = (
    (beta_valuation_prefix, ("p", "b", "c", "vb", "vc", "l")),
    (multinomial_binomial_prefix, ("b", "c", "sb", "sc", "cb", "cc", "l")),
    (multinomial, ("b", "c", "l", "n", "z")),
    (binary_column_carry_count, ("p", "a", "b", "e")),
    (multinomial_carry_prefix, ("p", "b", "c", "sb", "sc", "vb", "vc", "l")),
    (carry_count_many, ("p", "b", "c", "l", "e")),
)


@pytest.mark.parametrize(("builder", "arguments"), DEFINITIONS)
def test_definition_tags_do_not_change_native_formulas(builder, arguments):
    first, names = parse_formula_with_names(builder(*arguments, tag="audit_first"))
    second, others = parse_formula_with_names(builder(*arguments, tag="audit_second"))
    assert first == second and names == others
    assert set(names) == set(arguments)


@pytest.mark.parametrize(("builder", "arguments"), DEFINITIONS)
@pytest.mark.parametrize("invalid", ("S", "a b", "x -> false", "", 7))
def test_definition_arguments_cannot_inject_syntax(builder, arguments, invalid):
    with pytest.raises((TypeError, ValueError)):
        builder(invalid, *arguments[1:], tag="audit")


@pytest.mark.parametrize(("builder", "arguments"), DEFINITIONS)
def test_definition_binder_capture_is_rejected(builder, arguments):
    with pytest.raises(ValueError):
        builder("mkm_index_audit", *arguments[1:], tag="audit")


def _coefficient(parts):
    partial, coefficient = 0, 1
    for value in parts:
        coefficient *= comb(partial + value, partial)
        partial += value
    return partial, coefficient


def _carry_rows(base, parts):
    partial, rows = 0, []
    for value in parts:
        power, bits = base, []
        for _ in range(partial + value):
            bit = (partial + value) // power - partial // power - value // power
            assert bit in {0, 1}
            bits.append(bit)
            power *= base
        rows.append(tuple(bits))
        partial += value
    return tuple(rows)


def _valuation(base, value):
    assert value > 0
    exponent = 0
    while value % base == 0:
        value //= base
        exponent += 1
    return exponent


@pytest.mark.parametrize("base", (2, 3, 5, 7))
def test_constructed_carry_examples_cover_every_small_part_list(base):
    # Examples are regressions; the quantified HA body above is the proof.
    for length in range(5):
        for parts in product(range(4), repeat=length):
            total, coefficient = _coefficient(parts)
            denominator = 1
            for value in parts:
                denominator *= factorial(value)
            assert coefficient * denominator == factorial(total)
            count = sum(sum(row) for row in _carry_rows(base, parts))
            assert count == _valuation(base, coefficient)
            power, simultaneous = base, 0
            for _ in range(total):
                simultaneous += total // power - sum(value // power for value in parts)
                power *= base
            assert count == simultaneous


def test_zero_empty_and_multiple_carries_are_not_silently_excluded():
    assert _coefficient(()) == (0, 1)
    assert _coefficient((0, 0, 0)) == (0, 1)
    assert _coefficient((7,)) == (7, 1)
    assert sum(sum(row) for row in _carry_rows(2, (1, 1, 1, 1))) == 3
    assert sum(sum(row) for row in _carry_rows(3, (2, 2, 2))) == 2
    assert _valuation(2, 24) == 3
