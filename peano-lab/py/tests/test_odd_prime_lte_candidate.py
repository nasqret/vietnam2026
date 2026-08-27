"""Unsealed original-kernel authoring checks, not Alpha admission receipts."""

from dataclasses import asdict, replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import odd_prime_lte_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.prime_valuation_support_candidate import make_prime_valuation_support_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts/peano-library/alpha/catalog-v28.json"
PARENT_SHA256 = "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9"


@lru_cache(maxsize=1)
def core():
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 2764
    assert catalog["stable_count"] == 432
    inherited = {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row["summary"])
        for row in catalog["theorems"]
    }
    return inherited | {row.name: row for row in make_prime_valuation_support_candidate_theorems(TheoremSpec)}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_odd_prime_lte_candidate_theorems(TheoremSpec)


def check_body(name, mutation="none"):
    table = core() | {item.name: item for item in rows()}
    row = table[name]
    if mutation == "forged_body":
        row = replace(row, script=("exact invented_lte_oracle",))
    elif mutation == "false_conclusion":
        row = replace(row, statement=f"({row.statement}) /\\ false")
    elif mutation == "truncated_body":
        row = replace(row, script=row.script[:-1])
    elif mutation == "removed_dependency":
        row = replace(row, dependencies=row.dependencies[:-1])
    elif mutation == "corrupt_dependency":
        dependency = row.dependencies[0]
        table[dependency] = replace(table[dependency], statement="0 = 0")
    elif mutation != "none":
        raise ValueError("unknown LTE test mutation")
    try:
        if mutation != "none":
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((row,), core=table)
            return {"mutation": mutation, "rejected": True}
        return asdict(replay_candidate_bodies((row,), core=table)[0])
    finally:
        gc.collect()


def isolated_body(name, mutation="none"):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "peano-lab/py"), str(ROOT / "scripts")))
    checked = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--body", name, mutation],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=60,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    return json.loads(checked.stdout)


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_actual_ha_candidate_body(name):
    receipt = isolated_body(name)
    assert receipt["name"] == name
    assert receipt["proof_depth"] <= 256
    assert receipt["proof_objects"] <= receipt["proof_nodes"]
    print(f"{name}: {receipt['proof_nodes']}/{receipt['proof_depth']}/{receipt['proof_objects']}")


def test_additive_acyclic_exact_dependencies():
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        assert all(re.search(r"(?<![\w'])" + re.escape(dep) + r"(?![\w'])", "\n".join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(("use ", "ring", "admit", "sorry", "DNE")) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
@pytest.mark.parametrize("mutation", ("forged_body", "false_conclusion", "truncated_body"))
def test_forged_proof_body_is_rejected(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


@pytest.mark.parametrize("name", (
    "lte_odd_prime_power_step", "lte_coprime_exponent_step", "lte_prime_power_iteration",
    "lte_positive_exponent_exact", "odd_prime_lifting_the_exponent", "odd_prime_lifting_the_exponent_value",
))
@pytest.mark.parametrize("mutation", ("removed_dependency", "corrupt_dependency"))
def test_principal_dependency_authority_is_checked(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


def test_difference_definition_is_alpha_invariant_and_not_a_valuation_oracle():
    arguments = ("a", "b", "n", "A", "B", "d", "q")
    first = candidate.power_difference_quotient_relation(*arguments, tag="first", variables=arguments)
    second = candidate.power_difference_quotient_relation(*arguments, tag="second", variables=arguments)
    assert parse_formula_in_context(first, list(arguments)) == parse_formula_in_context(second, list(arguments))
    assert "valuation" not in first and "Prime" not in first and "LTE" not in first
    assert "(a) = (b) + (d)" in first and "(A) = (B) + (d) * (q)" in first


@pytest.mark.parametrize("bad", ("", "foreign", "a-b", "a/b", "exists x. x", None))
def test_difference_definition_rejects_foreign_or_ill_scoped_terms(bad):
    with pytest.raises((ValueError, TypeError)):
        candidate.power_difference_quotient_relation(bad, "b", "n", "A", "B", "d", "q", tag="audit", variables=("a", "b", "n", "A", "B", "d", "q"))


@pytest.mark.parametrize("name", ("olte_forged", "pa_b_auditfirst"))
def test_difference_definition_rejects_generated_binder_capture(name):
    with pytest.raises(ValueError, match="captures"):
        candidate.power_difference_quotient_relation(name, "b", "n", "A", "B", "d", "q", tag="audit", variables=(name, "b", "n", "A", "B", "d", "q"))


PUBLIC_RELATIONS = (
    (candidate.power_difference_quotient_relation, ("a", "b", "n", "A", "B", "d", "q")),
    (candidate.power_difference_second_order_relation, ("a", "b", "d", "k", "A", "B", "R", "T", "Q", "C", "H")),
    (candidate.lifted_power_difference_relation, ("p", "a", "b", "n", "e", "A", "B", "D")),
)


@pytest.mark.parametrize("builder,arguments", PUBLIC_RELATIONS, ids=lambda value: getattr(value, "__name__", "arguments"))
def test_all_public_relations_are_hygienic_ast_abbreviations(builder, arguments):
    first = builder(*arguments, tag="first", variables=arguments)
    second = builder(*arguments, tag="second", variables=arguments)
    assert parse_formula_in_context(first, list(arguments)) == parse_formula_in_context(second, list(arguments))
    binders = {name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", first) for name in clause.split()}
    assert binders and not binders.intersection(arguments)
    for binder in sorted(binders):
        with pytest.raises(ValueError, match="captures"):
            builder(*arguments, tag="first", variables=arguments + (binder,))
    compound = (arguments[0] + " + 1",) + arguments[1:]
    parse_formula_in_context(builder(*compound, tag="compound", variables=arguments), list(arguments))


@pytest.mark.parametrize("builder,arguments", PUBLIC_RELATIONS, ids=lambda value: getattr(value, "__name__", "arguments"))
@pytest.mark.parametrize("bad", ("foreign", "x-y", "x/y", "forall x. x=x", "a +"))
def test_all_public_relations_reject_nonterms(builder, arguments, bad):
    with pytest.raises((ValueError, TypeError)):
        builder(bad, *arguments[1:], tag="bad", variables=arguments)


def test_full_endpoint_retains_every_blueprint_domain_guard():
    table = {row.name: row for row in rows()}
    result = table["odd_prime_lifting_the_exponent"]
    assert result.statement.startswith("forall p x y d n a b.")
    assert "S (2) = (p)" in result.statement
    assert "S (y) = (x)" in result.statement
    assert "~(y = 0) -> ~(n = 0) -> x = y + d" in result.statement
    assert "(d) = (p) * olte_factor_public_lte_divisor" in result.statement
    assert "~(exists olte_factor_public_lte_units. (x * y) = (p) *" in result.statement
    assert "exists X Y D." in result.statement
    # The independently proved iteration and extensional value interfaces are mandatory.
    assert "lte_positive_exponent_exact" in result.dependencies
    assert "odd_prime_lifting_the_exponent" in table["odd_prime_lifting_the_exponent_value"].dependencies
    assert "lte_power_difference_functional" in table["odd_prime_lifting_the_exponent_value"].dependencies


def test_shared_foundation_remains_exactly_frozen():
    source = ROOT / "peano-lab/py/peano_lab/library/prime_valuation_support_candidate.py"
    assert sha256(source.read_bytes()).hexdigest() == "bbd6e661a575f6a39f7a71424611da36a16d34cb6704cbae2b918387cc0f66d2"
    assert len(make_prime_valuation_support_candidate_theorems(TheoremSpec)) == 20


def _integer_valuation(p, n):
    """External regression examples only; never used to create HA certificates."""
    if p <= 1 or n <= 0:
        raise ValueError("positive valuation domain required")
    result = 0
    while n % p == 0:
        n //= p
        result += 1
    return result


def test_small_positive_odd_prime_lte_examples():
    checked = 0
    for p in (3, 5, 7, 11):
        for y in range(1, 13):
            for multiple in range(1, 4):
                x = y + p * multiple
                if (x * y) % p == 0:
                    continue
                for n in range(1, 10):
                    assert _integer_valuation(p, x**n - y**n) == _integer_valuation(p, x-y) + _integer_valuation(p, n)
                    checked += 1
    assert checked == 1080


def test_binary_and_composite_counterexamples_explain_prime_guards():
    assert _integer_valuation(2, 3**2 - 1) != _integer_valuation(2, 3-1) + _integer_valuation(2, 2)
    assert _integer_valuation(9, 28**3 - 1) != _integer_valuation(9, 28-1) + _integer_valuation(9, 3)
    with pytest.raises(ValueError):
        _integer_valuation(3, 0)


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
