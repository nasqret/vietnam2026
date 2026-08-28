"""Original-kernel checks and independent exact G014 boundary regressions."""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import json
from math import gcd
from pathlib import Path
import resource
import sys

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import euler_units_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.euler_totient_count_candidate import totient_relation, unit_count_relation
from peano_lab.library.finite_fold_surface import power_relation, product_relation
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_euler_units_product_candidate import reference_scale, rows as product_rows
from test_euler_units_residue_candidate import (
    assert_family_profile, check_body as base_check, core, isolated_body,
    reference_coprime, reference_mod, reference_unit, rows as residue_rows,
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_euler_units_candidate_theorems(TheoremSpec)


BODY_PROFILES = dict(zip((row.name for row in rows()), (
    (29,17,29), (379,61,375), (137,44,137),
    (28,20,28), (54,27,54), (38,22,38),
), strict=True))

PRINCIPAL_STATEMENTS = {
    "euler_unit_count_product_balance": "a3514f1c5b92ba0b29541eb681b313f98d01a910aa26f25044e29fc13ebc6fbd",
    "euler_coprime_totient_power_value": "62401bc3ae6050ed789b54eb3028512546c4c3f927f19bda5ca6ce77dc293f55",
    "euler_coprime_totient_power": "4f3533b3d207055a1f56ca77655cf26a381735fa3999f34a0a2c7935a21497e4",
    "euler_modular_unit_totient_power": "9640b53a89a7ed7e2e15db573380a9a7133af60e7ebed2215390034354b4a4d6",
    "euler_theorem_for_units": "fcfb262cc347ec2cd7624dffba31f9ed519292b3ba5f1669682cee308cbac39d",
}


def expected_power_result(exponent="t"):
    power = _power_terms("a",exponent,"w",tag="independent_euler_power")
    return f"exists w. ({power}) /\\ ({reference_mod('m','w','1')})"


def expected_exact_endpoint(unit=None, exponent="t"):
    unit = reference_unit("a","m") if unit is None else unit
    phi = totient_relation("m","t",tag="independent_phi")
    return f"forall a m t. ((exists h. h+S 1=m) /\\ (({unit}) /\\ ({phi}))) -> ({expected_power_result(exponent)})"


def altered_boundary(name, mutation):
    table = core() | {row.name:row for row in (*residue_rows(),*product_rows(),*rows())}
    row = table[name]
    if mutation == "nonzero_residue_not_unit":
        statement = expected_exact_endpoint("~(a=0) /\\ (exists h. h+S a=m)")
    elif mutation == "wrong_successor_exponent":
        statement = expected_exact_endpoint(exponent="S t")
    elif mutation == "no_coprimality":
        statement = f"forall a m t. ~(m=0) -> ({totient_relation('m','t',tag='mutation_phi')}) -> ({expected_power_result()})"
    elif mutation == "canonical_one_at_modulus_one":
        statement = f"forall a m t. ~(m=0) -> ({reference_coprime('a','m')}) -> ({totient_relation('m','t',tag='mutation_phi')}) -> " \
            f"exists w. ({power_relation('a','t','w',tag='mutation_power')}) /\\ ((exists q. w=m*q+1) /\\ (exists h. h+S 1=m))"
    elif mutation == "unjustified_count_oracle":
        count = candidate._count("m","l","t",tag="eu_balance_count")
        assert row.statement.count(count)==1
        statement = row.statement.replace(count,"t=t")
    else:
        raise ValueError("unknown Euler boundary mutation")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=table)
    return {"mutation":mutation,"rejected":True}


def modulus_one_specialization():
    """A temporary specialization check, not a new library row/admission."""
    table = core() | {row.name:row for row in (*residue_rows(),*product_rows(),*rows())}
    row = TheoremSpec(
        "test_euler_modulus_one_specialization",
        f"forall a. exists w. ({_power_terms('a','1','w',tag='test_one_power')}) /\\ ({reference_mod('1','w','1')})",
        ("euler_coprime_totient_power","succ_ne_zero","coprime_one_right","totient_one_value"),
        ("intro a","specialize euler_coprime_totient_power a","specialize euler_coprime_totient_power 1","specialize euler_coprime_totient_power 1","apply euler_coprime_totient_power",
         "specialize succ_ne_zero 0","exact succ_ne_zero","specialize coprime_one_right a","apply coprime_one_right","exact totient_one_value"),
        "Temporary exact modulus-one specialization regression, not a library row.",
    )
    return asdict(replay_candidate_bodies((row,),core=table)[0])


def check_body(name, mutation="none"):
    if name == "test_euler_modulus_one_specialization":
        return modulus_one_specialization()
    if mutation in {"nonzero_residue_not_unit","wrong_successor_exponent","no_coprimality","canonical_one_at_modulus_one","unjustified_count_oracle"}:
        return altered_boundary(name,mutation)
    return base_check(name, mutation, (*product_rows(), *rows()))


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_original_kernel_body_in_fresh_process(name):
    receipt = isolated_body(name, driver=Path(__file__).resolve())
    assert receipt["name"] == name
    assert receipt["proof_nodes"] > 0 and receipt["proof_depth"] <= 256
    assert (receipt["proof_nodes"],receipt["proof_depth"],receipt["proof_objects"]) == BODY_PROFILES[name]


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
@pytest.mark.parametrize("mutation", ("false_conclusion", "truncated_body", "removed_dependency", "corrupt_dependency"))
def test_negative_body_and_dependency_mutations(name, mutation):
    assert isolated_body(name, mutation, driver=Path(__file__).resolve())["rejected"] is True


@pytest.mark.parametrize("name", ("euler_unit_count_product_balance", "euler_modular_unit_totient_power"))
def test_reused_parent_dependencies_are_actually_checked(name):
    assert isolated_body(name, "corrupt_reused_parent_dependency", driver=Path(__file__).resolve())["rejected"] is True


@pytest.mark.parametrize("removed,parent,statement,consumers", (
    (
        "euler_modulus_above_one_nonzero", "binary_modulus_nontrivial_nonzero",
        "forall m. (exists h. h+S 1=m) -> ~(m=0)",
        ("euler_coprime_modular_unit", "euler_modular_unit_totient_power"),
    ),
    (
        "euler_product_scale_shuffle", "mul_shuffle_four",
        "forall w a P v. (w*a)*(P*v)=(w*P)*(a*v)",
        ("euler_unit_count_product_balance",),
    ),
))
def test_duplicate_scalar_claims_reuse_exact_parent_theorems(removed, parent, statement, consumers):
    assert _closed_formula(core()[parent].statement) == _closed_formula(statement)
    frontier = {row.name: row for row in (*residue_rows(), *product_rows(), *rows())}
    assert removed not in frontier
    for row in frontier.values():
        assert removed not in row.dependencies
        assert all(removed not in command for command in row.script)
    for name in consumers:
        row = frontier[name]
        assert parent in row.dependencies
        assert any(command.startswith("specialize " + parent + " ") for command in row.script)


def test_additive_inventory_and_all_local_formulas():
    available = set(core()) | {row.name for row in (*residue_rows(), *product_rows())}
    for row in rows():
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


def test_exact_G014_uses_actual_bounded_inverse_independent_phi_and_constructed_power():
    statement = next(row.statement for row in rows() if row.name=="euler_theorem_for_units")
    assert _closed_formula(statement) == _closed_formula(expected_exact_endpoint())


def test_stronger_coprime_root_includes_modulus_one_but_not_modulus_zero():
    statement = next(row.statement for row in rows() if row.name=="euler_coprime_totient_power")
    expected = f"forall a m t. ~(m=0) -> ({reference_coprime('a','m')}) -> ({totient_relation('m','t',tag='reference')}) -> ({expected_power_result()})"
    assert _closed_formula(statement) == _closed_formula(expected)


def test_count_prefix_induction_is_about_real_count_product_and_power_graphs():
    statement = next(row.statement for row in rows() if row.name=="euler_unit_count_product_balance")
    expected = f"forall l a m b c d e t P Q w. ({unit_count_relation('m','l','t',tag='independent_count')}) -> " \
        f"({reference_scale('a','m','b','c','d','e','l')}) -> ({product_relation('b','c','l','P',tag='independent_source')}) -> " \
        f"({product_relation('d','e','l','Q',tag='independent_target')}) -> ({power_relation('a','t','w',tag='independent_power')}) -> " \
        f"({reference_mod('m','w*P','Q')})"
    assert _closed_formula(statement) == _closed_formula(expected)


@pytest.mark.parametrize("name,digest", tuple(PRINCIPAL_STATEMENTS.items()))
def test_principal_statement_sha_pins(name,digest):
    assert sha256(next(row.statement for row in rows() if row.name==name).encode()).hexdigest()==digest


@pytest.mark.parametrize("name,mutation", (
    ("euler_theorem_for_units","nonzero_residue_not_unit"),
    ("euler_theorem_for_units","wrong_successor_exponent"),
    ("euler_coprime_totient_power","no_coprimality"),
    ("euler_coprime_totient_power","canonical_one_at_modulus_one"),
    ("euler_unit_count_product_balance","unjustified_count_oracle"),
))
def test_exact_hypothesis_and_count_boundaries_fail_closed(name,mutation):
    assert isolated_body(name,mutation,driver=Path(__file__).resolve())["rejected"] is True


def test_modulus_one_specialization_is_genuinely_original_kernel_checked():
    receipt = isolated_body("test_euler_modulus_one_specialization",driver=Path(__file__).resolve())
    assert receipt["proof_nodes"]>0


@pytest.mark.parametrize("m", range(1,49))
def test_independent_euler_numerical_reference_includes_unbounded_representatives(m):
    t=sum(gcd(i,m)==1 for i in range(m))
    for a in (0,1,2,3,m-1,m+1,2*m+3,1000003):
        if gcd(a,m)==1:
            assert (pow(a,t,m)-1)%m==0
    if m==1:
        assert t==1 and pow(7,t,m)==0


def test_invalid_weakenings_have_concrete_counterexamples_not_proof_authority():
    assert 0<2<4 and gcd(2,4)!=1 and pow(2,2,4)!=1
    assert gcd(2,5)==1 and pow(2,4,5)==1 and pow(2,5,5)!=1
    assert not 1<1  # the stronger m=1 result is congruence, not remainder one


def test_literal_endpoint_and_combined_inventory_profiles():
    assert_family_profile(rows(),BODY_PROFILES,(6,33,397,665,61))
    all_rows=(*residue_rows(),*product_rows(),*rows())
    assert len(all_rows)==32
    assert sum(len(row.dependencies) for row in all_rows)==91
    assert sum(len(row.script) for row in all_rows)==1203
    assert sha256("\n".join(row.name for row in all_rows).encode()).hexdigest()=="cd20126240c0f26016e1e6952a491db20eaf6759ecb4b795908db05635d30bd3"
    # Exact pre-dedup statements, without the two already-proved parent aliases.
    statements = json.dumps([(row.name, row.statement) for row in all_rows], ensure_ascii=False,
                            sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    assert sha256(statements).hexdigest()=="7b3957933ea7a0f6d0c6651734a94b70f8a9d4b8f082de0cc18dd6c47560363a"


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
