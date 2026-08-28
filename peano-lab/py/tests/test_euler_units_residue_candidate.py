"""Exact v30-based body checks for the constructive Euler unit permutation."""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import json
from math import gcd
import os
from pathlib import Path
import re
import resource
import subprocess
import sys

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names
from peano_lab.library import euler_units_residue_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.finite_fold_surface import _beta_at_term
from peano_lab.library.finite_permutation_theorems import permutation_prefix
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT_SHA256 = "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"


@lru_cache(maxsize=1)
def rows():
    return candidate.make_euler_units_residue_candidate_theorems(TheoremSpec)


BODY_PROFILES = dict(zip((row.name for row in rows()), (
    (34,17,34), (49,20,49), (37,21,37), (30,19,30),
    (33,17,33), (26,17,26), (63,27,63), (45,22,45), (42,22,42),
    (95,36,95), (65,22,65), (30,19,30),
), strict=True))


@lru_cache(maxsize=1)
def core():
    payload = (ROOT / "artifacts/peano-library/alpha/catalog-v30.json").read_bytes()
    assert sha256(payload).hexdigest() == PARENT_SHA256
    document = json.loads(payload)
    assert document["theorem_count"] == document["checked_use_count"] == 3222
    assert document["stable_count"] == 432
    assert all(row["checked_use"] is True for row in document["theorems"])
    return {row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row.get("summary", "")) for row in document["theorems"]}


def check_body(name: str, mutation: str = "none", extra=()):
    table = core() | {row.name: row for row in (*rows(), *extra)}
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
    elif mutation == "corrupt_reused_parent_dependency":
        dependency = {
            "euler_coprime_modular_unit": "binary_modulus_nontrivial_nonzero",
            "euler_unit_count_product_balance": "mul_shuffle_four",
            "euler_modular_unit_totient_power": "binary_modulus_nontrivial_nonzero",
        }[row.name]
        assert dependency in row.dependencies
        table = table | {dependency: replace(table[dependency], statement="0=0")}
    elif mutation != "none":
        raise ValueError("unknown Euler proof mutation")
    if mutation != "none":
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,), core=table)
        return {"mutation": mutation, "rejected": True}
    return asdict(replay_candidate_bodies((row,), core=table)[0])


def isolated_body(name: str, mutation: str = "none", *, driver: Path | None = None):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "peano-lab/py"), str(ROOT / "scripts")))
    checked = subprocess.run([sys.executable, str(driver or Path(__file__).resolve()), "--body", name, mutation], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=60)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    return json.loads(checked.stdout)


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_original_kernel_body_in_fresh_process(name):
    receipt = isolated_body(name)
    assert receipt["name"] == name
    assert receipt["proof_nodes"] > 0 and receipt["proof_depth"] <= 256
    assert 0 < receipt["proof_objects"] <= receipt["proof_nodes"]
    assert (receipt["proof_nodes"], receipt["proof_depth"], receipt["proof_objects"]) == BODY_PROFILES[name]


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
@pytest.mark.parametrize("mutation", ("false_conclusion", "truncated_body", "removed_dependency", "corrupt_dependency"))
def test_negative_body_and_dependency_mutations(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


def test_reused_parent_nonzero_modulus_dependency_is_actually_checked():
    assert isolated_body("euler_coprime_modular_unit", "corrupt_reused_parent_dependency")["rejected"] is True


def test_additive_topological_inventory_and_all_local_formulas():
    available = set(core())
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


def reference_coprime(a, m):
    return f"forall ref_divisor. (exists ref_left. ({a})=ref_divisor*ref_left) -> (exists ref_right. ({m})=ref_divisor*ref_right) -> ref_divisor=1"


def reference_mod(m, a, b):
    return f"exists ref_mod_left ref_mod_right. ({a})+({m})*ref_mod_left=({b})+({m})*ref_mod_right"


def reference_at(b, c, i, v, *, tag):
    return _beta_at_term(f"({b})",f"({c})",f"({i})",f"({v})",tag="eu_reference_"+tag,avoid=())


def reference_unit(a, m):
    return f"(exists ref_gap. ref_gap+S 1=({m})) /\\ exists ref_inverse. " \
        f"(exists ref_inverse_gap. ref_inverse_gap+S ref_inverse=({m})) /\\ " \
        f"({reference_mod(m,f'({a})*ref_inverse','1')})"


def reference_map(a, m, b, c, l):
    return f"forall ref_index. (exists ref_index_gap. ref_index_gap+S ref_index=({l})) -> exists ref_residue. " \
        f"({reference_at(b,c,'ref_index','ref_residue',tag='map')}) /\\ " \
        f"((exists ref_bound. ref_bound+S ref_residue=({m})) /\\ ({reference_mod(m,f'({a})*ref_index','ref_residue')}))"


PUBLIC_CASES = (
    (candidate.modular_unit_relation, reference_unit, ("a","m"), ("a+1000003","S (m*m)")),
    (candidate.unit_multiplier_prefix_relation, reference_map, ("a","m","b","c","l"), ("a+1","S m","b+c","S c","l+1")),
)


def test_unit_matches_exact_blueprint_bounded_inverse_not_nonzero_residue():
    expected = "(exists h. h+S 1=m) /\\ exists b. (exists h. h+S b=m) /\\ exists u v. a*b+m*u=1+m*v"
    actual = candidate.modular_unit_relation("a", "m", tag="independent")
    assert _closed_formula("forall a m. " + actual) == _closed_formula("forall a m. " + expected)


@pytest.mark.parametrize("builder,reference,arguments,compound", PUBLIC_CASES)
def test_public_relations_match_independent_primitive_graphs(builder, reference, arguments, compound):
    context = (*arguments,"unused_context_variable")
    for terms in (arguments,compound):
        actual = builder(*terms,tag="actual",variables=context)
        expected = reference(*terms)
        assert parse_formula_in_context(actual,list(context)) == parse_formula_in_context(expected,list(context))
        assert parse_formula_in_context(actual,list(context)) == parse_formula_in_context(builder(*terms,tag="renamed",variables=context),list(context))
    assert parse_formula_in_context(builder(*arguments,tag="legacy"),list(context)) == parse_formula_in_context(builder(*arguments,tag="explicit",variables=context),list(context))


def capture_cases(public_cases):
    return tuple((builder, arguments, binder) for builder,_,arguments,_ in public_cases
                 for binder in sorted({name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.",builder(*arguments,tag="capture")) for name in clause.split()}))


@pytest.mark.parametrize("builder,arguments,binder", capture_cases(PUBLIC_CASES))
def test_every_generated_binder_rejects_capture_of_even_an_unused_context_variable(builder, arguments, binder):
    with pytest.raises(ValueError, match="captures"):
        builder(*arguments,tag="capture",variables=(*arguments,binder))


@pytest.mark.parametrize("builder,reference,arguments,compound", PUBLIC_CASES)
@pytest.mark.parametrize("context", ((), [], ("a","a"), ("S",), ("bad variable",), "a"))
def test_public_contexts_reject_empty_malformed_duplicate_or_reserved_names(builder, reference, arguments, compound, context):
    with pytest.raises(ValueError):
        builder(*arguments,tag="test",variables=context)


@pytest.mark.parametrize("builder,reference,arguments,compound", PUBLIC_CASES)
@pytest.mark.parametrize("bad", ("", "forall x. x", "S", "unknown", "a+", "(a", "a) /\\ false", "-1", "a/b"))
def test_public_terms_reject_undeclared_variables_and_formula_injection(builder, reference, arguments, compound, bad):
    with pytest.raises(ValueError):
        builder(bad,*arguments[1:],tag="test",variables=arguments)


@pytest.mark.parametrize("builder,reference,arguments,compound", PUBLIC_CASES)
@pytest.mark.parametrize("tag", ("", "S", "forall", "bad tag", "t+x", "t;false"))
def test_public_tags_reject_unsafe_fragments(builder, reference, arguments, compound, tag):
    with pytest.raises(ValueError):
        builder(*arguments,tag=tag,variables=arguments)


def test_ground_unit_arguments_are_allowed_in_an_explicit_unused_context():
    actual = candidate.modular_unit_relation("3","8",tag="ground",variables=("unused",))
    assert parse_formula_in_context(actual,["unused"]) == parse_formula_in_context(reference_unit("3","8"),["unused"])


def test_multiplier_permutation_endpoint_constructs_all_three_actual_properties():
    statement = next(row.statement for row in rows() if row.name == "euler_multiplier_permutation_exists")
    expected = f"forall a m. ~(m=0) -> ({reference_coprime('a','m')}) -> exists b c. " \
        f"({reference_map('a','m','b','c','m')}) /\\ ({permutation_prefix('b','c','m',tag='reference')})"
    assert _closed_formula(statement) == _closed_formula(expected)
    assert sha256(statement.encode()).hexdigest() == "ee049e3a4d625ec0da3ab6d4ecff22da14d26fb3d4297031b23b2ece92c14fec"


@pytest.mark.parametrize("m", range(1,33))
def test_independent_multiplier_permutation_reference_including_modulus_one(m):
    for a in range(2*m+2):
        if gcd(a,m) != 1:
            continue
        images = [(a*i) % m for i in range(m)]
        assert sorted(images) == list(range(m))
        assert all((gcd(i,m)==1)==(gcd(images[i],m)==1) for i in range(m))
    if m == 1:
        assert [0 % m] == [0]


def assert_family_profile(ordered, profiles, expected):
    assert len(ordered) == expected[0]
    assert sum(len(row.dependencies) for row in ordered) == expected[1]
    assert sum(len(row.script) for row in ordered) == expected[2]
    assert sum(value[0] for value in profiles.values()) == expected[3]
    assert max(value[1] for value in profiles.values()) == expected[4]


def test_literal_residue_family_profile():
    assert_family_profile(rows(),BODY_PROFILES,(12,29,376,549,36))


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
