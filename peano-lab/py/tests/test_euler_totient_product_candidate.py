"""Actual arithmetic Euler-factor and complete prime-support product proofs."""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import json
from math import gcd, prod
import os
from pathlib import Path
import re
import resource
import subprocess
import sys

import pytest

from peano_lab.library import euler_totient_product_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.prime_valuation_support_candidate import make_prime_valuation_support_candidate_theorems
from peano_lab.library.prime_valuation_support_candidate import prime_valuation_support_relation
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.finite_fold_surface import beta_at, product_relation, power_relation
from peano_lab.library.foundation_saturation_candidate import prime_factor_list_relation
from peano_lab.library.euler_totient_count_candidate import totient_relation
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from peano_lab.kernel.formulas import parse_formula_with_names
from test_euler_totient_count_candidate import ROOT, core, rows as count_rows, assert_family_contract
from test_euler_totient_interval_candidate import rows as interval_rows
from test_euler_totient_prime_step_candidate import rows as step_rows
from test_euler_totient_algebra_candidate import rows as algebra_rows


@lru_cache(maxsize=1)
def rows():
    return candidate.make_euler_totient_product_candidate_theorems(TheoremSpec)


BODY_PROFILES = dict(zip((row.name for row in rows()), (
    (42,20,42), (74,26,74), (37,19,37), (80,33,80), (120,35,120),
    (119,40,119), (179,48,179), (28,19,28), (28,20,28), (103,39,103),
    (104,37,104), (81,44,81), (166,73,166), (89,47,89), (59,28,59),
    (44,21,44), (39,15,39), (29,12,29), (72,30,72), (21,13,21), (32,19,32),
), strict=True))


@lru_cache(maxsize=1)
def support_rows():
    payload=(ROOT / "peano-lab/py/peano_lab/library/prime_valuation_support_candidate.py").read_bytes()
    assert sha256(payload).hexdigest() == "bbd6e661a575f6a39f7a71424611da36a16d34cb6704cbae2b918387cc0f66d2"
    return make_prime_valuation_support_candidate_theorems(TheoremSpec)


def check_body(name: str, mutation: str = "none"):
    table = core() | {row.name: row for row in (*count_rows(), *interval_rows(), *step_rows(), *algebra_rows(), *support_rows(), *rows())}
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
    elif mutation == "missing_positive_domain":
        assert row.statement.startswith("forall n. ~(n=0) -> ")
        row = replace(row, statement=row.statement.replace("~(n=0) -> ", "", 1))
    elif mutation == "fake_zero_modulus_product":
        assert row.name == "totient_euler_product_one"
        row = replace(row, statement=candidate._euler("0", "1", "invalid_zero"))
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
    assert_family_contract(rows(), (*count_rows(), *interval_rows(), *step_rows(), *algebra_rows(), *support_rows()),
                           (21, 62, 939, "4a45c95daed9f5de9a28172cd9aa5049a4b165d4aa1086273420ad04eaa82ace"))


ROOT_PINS = {
    "totient_euler_product_exists": "825e79f251c91fc4664ef8f304b143c67aa4c6dae03a2c029ac5be3082efc128",
    "totient_euler_product_iff": "1d37df29457d21f2f36c8fc9a652a0dfcde15bde5a730c8a3ae789fcf98eb176",
    "totient_euler_product_one": "5650edfce8b3712b3658545e921b60eeabc9f895078d4f2a756be5d19a698d45",
    "totient_euler_product_zero_excluded": "4f75707ef4318b5d242df321a53288e3f0d62bbd69acd9b487bfbe4d9a0484a4",
    "totient_euler_product_formula": "30f159a663418d13fe52b39acca9de20a67d44219cc28eb965c36f352ddcf2a2",
}


@pytest.mark.parametrize("name,digest", ROOT_PINS.items())
def test_principal_product_statement_hashes(name, digest):
    assert sha256(next(row.statement for row in rows() if row.name == name).encode()).hexdigest() == digest


def expected_factor(p="p", e="e", c="c"):
    return (
        f"({prime(p,tag='independent_factor_prime')}) /\\ (~({e}=0) /\\ "
        f"exists h d Q. {p}=S h /\\ ({e}=S d /\\ "
        f"(({power_relation(p,'d','Q',tag='independent_factor_power')}) /\\ {c}=Q*h)))"
    )


def expected_prefix():
    return (
        f"forall i. (exists gap. gap+S i=l) -> exists p e c. "
        f"({beta_at('pb','pc','i','p',tag='independent_prime')}) /\\ "
        f"(({beta_at('eb','ec','i','e',tag='independent_exponent')}) /\\ "
        f"(({beta_at('fb','fc','i','c',tag='independent_factor')}) /\\ ({expected_factor()})))"
    )


def expected_euler():
    support = prime_valuation_support_relation(
        "n","pb","pc","eb","ec","vb","vc","l",tag="independent_complete_support",
        variables=("n","pb","pc","eb","ec","vb","vc","l"),
    )
    return (
        f"exists pb pc eb ec vb vc l fb fc. ({support}) /\\ "
        f"(({expected_prefix()}) /\\ ({product_relation('fb','fc','l','t',tag='independent_euler_product')}))"
    )


def test_euler_factor_is_independent_predecessor_power_arithmetic():
    actual = candidate.totient_prime_power_factor_relation("p","e","c",tag="actual")
    assert _closed_formula("forall p e c. "+actual) == _closed_formula("forall p e c. "+expected_factor())
    assert set(parse_formula_with_names(actual)[1]) == {"p","e","c"}
    assert "_phi" not in candidate._factor.__code__.co_names
    assert "_count" not in candidate._factor.__code__.co_names


def test_euler_factor_prefix_uses_the_same_actual_prime_and_exponent_indices():
    actual = candidate.totient_euler_factor_prefix_relation("pb","pc","eb","ec","fb","fc","l",tag="actual")
    universal = "forall pb pc eb ec fb fc l. "
    assert _closed_formula(universal+actual) == _closed_formula(universal+expected_prefix())


def test_euler_product_has_complete_distinct_valuation_support_and_actual_product_not_phi():
    actual = candidate.totient_euler_product_relation("n","t",tag="actual")
    assert _closed_formula("forall n t. "+actual) == _closed_formula("forall n t. "+expected_euler())
    assert set(parse_formula_with_names(actual)[1]) == {"n","t"}
    assert "_phi" not in candidate._euler.__code__.co_names
    assert "_count" not in candidate._euler.__code__.co_names


def test_full_g006_contract_constructs_all_witnesses_from_only_positive_n():
    expected = (
        "forall n. ~(n=0) -> exists f g l t. "
        f"({prime_factor_list_relation('n','f','g','l',tag='independent_factor_list')}) /\\ "
        f"(({totient_relation('n','t',tag='independent_unit_count')}) /\\ ({expected_euler()}))"
    )
    actual = next(row.statement for row in rows() if row.name == "totient_euler_product_formula")
    assert _closed_formula(actual) == _closed_formula(expected)


def test_iff_is_literal_independent_product_iff_independent_unit_count():
    phi = totient_relation("n","t",tag="independent_phi")
    euler = expected_euler()
    expected = f"forall n t. (({phi}) -> ({euler})) /\\ (({euler}) -> ({phi}))"
    actual = next(row.statement for row in rows() if row.name == "totient_euler_product_iff")
    assert _closed_formula(actual) == _closed_formula(expected)


def test_explicit_one_endpoint_chooses_empty_lists_and_does_not_insert_a_fake_prime():
    row = next(row for row in rows() if row.name == "totient_euler_product_one")
    assert row.script[:9] == ("exists 0",)*9
    assert row.dependencies == ("prime_valuation_support_one", "totient_euler_factor_prefix_empty")
    assert _closed_formula(row.statement) == _closed_formula(candidate._euler("1","1","reference_one"))


@pytest.mark.parametrize("name", ("totient_euler_product_exists", "totient_euler_product_formula"))
def test_omitting_positive_domain_is_rejected_by_original_kernel_body(name):
    assert isolated_body(name, "missing_positive_domain")["rejected"] is True


def test_empty_product_does_not_manufacture_zero_modulus_support():
    assert isolated_body("totient_euler_product_one", "fake_zero_modulus_product")["rejected"] is True


PUBLIC_BUILDERS = (
    (candidate.totient_prime_power_factor_relation, ("p","e","c")),
    (candidate.totient_euler_factor_prefix_relation, ("pb","pc","eb","ec","fb","fc","l")),
    (candidate.totient_euler_product_relation, ("n","t")),
)


@pytest.mark.parametrize("builder,arguments", PUBLIC_BUILDERS)
def test_public_definition_tags_are_alpha_equivalent_and_keep_every_parameter(builder, arguments):
    universal = "forall "+" ".join(arguments)+". "
    first, second = builder(*arguments,tag="first"), builder(*arguments,tag="second")
    assert _closed_formula(universal+first) == _closed_formula(universal+second)
    assert set(parse_formula_with_names(first)[1]) == set(arguments)


@pytest.mark.parametrize("builder,arguments", PUBLIC_BUILDERS)
@pytest.mark.parametrize("bad", ("", "S", "forall", "1", "a+b", "x y", "x;y", "x)"))
def test_public_definition_arguments_reject_formula_injection(builder, arguments, bad):
    for position in range(len(arguments)):
        changed = list(arguments)
        changed[position] = bad
        with pytest.raises(ValueError):
            builder(*changed,tag="actual")


@pytest.mark.parametrize("builder,arguments", PUBLIC_BUILDERS)
@pytest.mark.parametrize("bad", ("", "S", "forall", "1", "a+b", "x;y"))
def test_public_definition_tags_reject_formula_injection(builder, arguments, bad):
    with pytest.raises(ValueError):
        builder(*arguments,tag=bad)


@pytest.mark.parametrize("builder,arguments", PUBLIC_BUILDERS)
def test_public_definitions_reject_capture_of_any_generated_binder_family(builder, arguments):
    formula = builder(*arguments,tag="actual")
    binders = sorted({name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.",formula) for name in clause.split()})
    representatives = {}
    for name in binders:
        representatives.setdefault(name.split("_",1)[0],name)
    assert representatives
    for name in representatives.values():
        changed=(name,*arguments[1:])
        with pytest.raises(ValueError):
            builder(*changed,tag="actual")


def numerical_factorization(n):
    remaining, divisor, factors = n, 2, []
    while divisor * divisor <= remaining:
        exponent = 0
        while remaining % divisor == 0:
            exponent += 1
            remaining //= divisor
        if exponent:
            factors.append((divisor,exponent))
        divisor += 1
    if remaining > 1:
        factors.append((remaining,1))
    return factors


@pytest.mark.parametrize("n", range(1, 129))
def test_independent_finite_prime_support_euler_product_reference(n):
    support = numerical_factorization(n)
    assert len({p for p,e in support}) == len(support)
    assert all(e > 0 and p > 1 for p,e in support)
    assert prod(p**e for p,e in support) == n
    assert all(n % (p**e) == 0 and n % (p**(e+1)) != 0 for p,e in support)
    actual_count = sum(gcd(i,n) == 1 for i in range(n))
    assert prod(p**(e-1)*(p-1) for p,e in support) == actual_count
    if n == 1:
        assert support == [] and actual_count == 1


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
