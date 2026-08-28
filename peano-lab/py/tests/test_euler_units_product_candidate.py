"""Independent contracts and bounded original-HA product candidate replay."""

from __future__ import annotations

from functools import lru_cache
import json
from math import gcd, prod
from pathlib import Path
import resource
import sys

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names
from peano_lab.library import euler_units_product_candidate as candidate
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_euler_units_residue_candidate import (
    assert_family_profile, capture_cases, check_body as base_check, core,
    isolated_body, reference_at, reference_coprime, reference_mod, rows as residue_rows,
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_euler_units_product_candidate_theorems(TheoremSpec)


BODY_PROFILES = dict(zip((row.name for row in rows()), (
    (17,8,17), (28,13,28), (28,13,28), (35,14,35), (25,16,25),
    (65,25,65), (31,18,31), (25,17,25), (41,21,41), (91,32,91),
    (45,27,45), (51,30,51), (44,30,44), (189,39,189),
), strict=True))


def check_body(name, mutation="none"):
    return base_check(name, mutation, rows())


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_original_kernel_body_in_fresh_process(name):
    receipt = isolated_body(name, driver=Path(__file__).resolve())
    assert receipt["name"] == name
    assert receipt["proof_nodes"] > 0 and receipt["proof_depth"] <= 256
    assert (receipt["proof_nodes"],receipt["proof_depth"],receipt["proof_objects"]) == BODY_PROFILES[name]


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
@pytest.mark.parametrize("mutation", ("false_conclusion", "truncated_body"))
def test_negative_proof_mutations(name, mutation):
    assert isolated_body(name, mutation, driver=Path(__file__).resolve())["rejected"] is True


@pytest.mark.parametrize("name", tuple(row.name for row in rows() if row.dependencies))
@pytest.mark.parametrize("mutation", ("removed_dependency", "corrupt_dependency"))
def test_dependency_authority_mutations(name, mutation):
    assert isolated_body(name, mutation, driver=Path(__file__).resolve())["rejected"] is True


def test_additive_inventory_and_all_local_formulas():
    available = set(core()) | {row.name for row in residue_rows()}
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


def reference_factor(m, i, v):
    predicate = reference_coprime(i,m)
    return f"((({predicate}) /\\ ({v})=({i})) \\/ (~({predicate}) /\\ ({v})=1))"


def reference_factors(m, b, c, l):
    return f"forall ref_index. (exists ref_gap. ref_gap+S ref_index=({l})) -> exists ref_value. " \
        f"({reference_at(b,c,'ref_index','ref_value',tag='weighted')}) /\\ ({reference_factor(m,'ref_index','ref_value')})"


def reference_scale(a, m, b, c, d, e, l):
    predicate = reference_coprime("ref_index",m)
    return f"forall ref_index ref_source ref_target. (exists ref_gap. ref_gap+S ref_index=({l})) -> " \
        f"({reference_at(b,c,'ref_index','ref_source',tag='scale_source')}) -> " \
        f"({reference_at(d,e,'ref_index','ref_target',tag='scale_target')}) -> " \
        f"((({predicate}) -> ({reference_mod(m,f'({a})*ref_source','ref_target')})) /\\ " \
        f"(~({predicate}) -> ({reference_mod(m,'ref_source','ref_target')})))"


PUBLIC_CASES = (
    (candidate.unit_product_factor_relation,reference_factor,("m","i","v"),("m+2","i*i+1","v+1000003")),
    (candidate.unit_product_prefix_relation,reference_factors,("m","b","c","l"),("m+1","b+1000003","S c","l+l")),
    (candidate.unit_scaled_prefix_relation,reference_scale,("a","m","b","c","d","e","l"),("a*a","S m","b+c","S c","d+1","e+1","S l")),
)


@pytest.mark.parametrize("builder,reference,arguments,compound", PUBLIC_CASES)
def test_public_graphs_match_independent_primitives_for_compound_and_large_terms(builder, reference, arguments, compound):
    context = (*arguments,"unused_context_variable")
    for terms in (arguments,compound):
        actual = builder(*terms,tag="actual",variables=context)
        assert parse_formula_in_context(actual,list(context)) == parse_formula_in_context(reference(*terms),list(context))
        assert parse_formula_in_context(actual,list(context)) == parse_formula_in_context(builder(*terms,tag="renamed",variables=context),list(context))
    assert parse_formula_in_context(builder(*arguments,tag="legacy"),list(context)) == parse_formula_in_context(builder(*arguments,tag="explicit",variables=context),list(context))


@pytest.mark.parametrize("builder,arguments,binder", capture_cases(PUBLIC_CASES))
def test_every_generated_binder_rejects_an_unused_declared_context_name(builder, arguments, binder):
    with pytest.raises(ValueError,match="captures"):
        builder(*arguments,tag="capture",variables=(*arguments,binder))


@pytest.mark.parametrize("builder,reference,arguments,compound", PUBLIC_CASES)
@pytest.mark.parametrize("context", ((), [], ("a","a"), ("S",), ("bad variable",), "a"))
def test_public_context_rejections(builder, reference, arguments, compound, context):
    with pytest.raises(ValueError):
        builder(*arguments,tag="test",variables=context)


@pytest.mark.parametrize("builder,reference,arguments,compound", PUBLIC_CASES)
@pytest.mark.parametrize("bad", ("", "forall x. x", "S", "unknown", "a+", "(a", "a) /\\ false", "-1", "a/b"))
def test_public_term_rejections(builder, reference, arguments, compound, bad):
    with pytest.raises(ValueError):
        builder(bad,*arguments[1:],tag="test",variables=arguments)


@pytest.mark.parametrize("builder,reference,arguments,compound", PUBLIC_CASES)
@pytest.mark.parametrize("tag", ("", "S", "forall", "bad tag", "t+x", "t;false"))
def test_public_tag_rejections(builder, reference, arguments, compound, tag):
    with pytest.raises(ValueError):
        builder(*arguments,tag=tag,variables=arguments)


def test_factor_graph_uses_the_index_not_its_successor_and_nonunits_contribute_one():
    actual = candidate.unit_product_factor_relation("m","i","v",tag="exact")
    assert _closed_formula("forall m i v. "+actual) == _closed_formula("forall m i v. "+reference_factor("m","i","v"))
    assert _closed_formula("forall m i v. "+actual) != _closed_formula("forall m i v. "+reference_factor("m","S i","v"))
    assert "Pow" not in actual and "Phi" not in actual


@pytest.mark.parametrize("m", range(1,25))
def test_independent_weighted_product_and_unit_count_prefix_balance_reference(m):
    source = [i if gcd(i,m)==1 else 1 for i in range(m)]
    assert gcd(prod(source),m)==1
    for a in range(2*m+2):
        if gcd(a,m)!=1:
            continue
        target = [source[(a*i) % m] for i in range(m)]
        assert prod(target)==prod(source)
        for l in range(m+1):
            t = sum(gcd(i,m)==1 for i in range(l))
            assert (pow(a,t)*prod(source[:l])-prod(target[:l])) % m==0
    if m==1:
        assert source==[0] and gcd(0,1)==1


def test_literal_product_family_profile():
    assert_family_profile(rows(),BODY_PROFILES,(14,29,430,715,39))


if __name__ == "__main__":
    assert sys.argv[1] == "--body"
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")))
