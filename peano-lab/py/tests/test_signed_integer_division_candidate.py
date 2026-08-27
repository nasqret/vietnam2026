"""Non-admitting signed-floor body checks against the exact sealed v27 basis."""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import signed_integer_division_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts/peano-library/alpha/catalog-v27.json"
PARENT_SHA256 = "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
NAMES = ("natural_mul_swap_right_tail","signed_integer_floor_exists","signed_integer_floor_quotient_transport","signed_integer_canonical_floor_exists","signed_code_floor_exists")


@lru_cache(maxsize=1)
def core():
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 2560
    assert catalog["stable_count"] == 432
    return {row["name"]: TheoremSpec(row["name"],row["statement"],tuple(row["dependencies"]),tuple(row["script"]),row["summary"]) for row in catalog["theorems"]}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_integer_division_candidate_theorems(TheoremSpec)


def test_original_kernel_bodies():
    receipts = replay_candidate_bodies(rows(),core=core())
    assert tuple(row.name for row in receipts) == NAMES
    assert tuple(row.proof_nodes for row in receipts) == (21,73,172,47,36)
    assert tuple(row.proof_depth for row in receipts) == (11,27,49,29,21)
    assert sum(row.proof_nodes for row in receipts) == 349


def test_actual_substrate_is_additive_and_acyclic():
    available = set(core())
    assert sum(len(row.dependencies) for row in rows()) == 17
    assert sum(len(row.script) for row in rows()) == 129
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert all(re.search(r"(?<![\w'])"+re.escape(dep)+r"(?![\w'])","\n".join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(("use ","ring","admit","sorry","DNE")) for command in row.script)
        assert not any("eisenstein" in dep or "gaussian" in dep for dep in row.dependencies)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize("row",rows(),ids=lambda row:row.name)
def test_forged_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,script=("exact nonexistent_division_oracle",)),),core={**core(),**{x.name:x for x in rows()}})


def test_nonzero_divisor_guard_is_required_by_the_actual_proof():
    row = rows()[1]
    changed = replace(row,statement=row.statement.replace("~(m = 0) -> ","",1))
    assert changed.statement != row.statement
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core())


def test_term_based_floor_matches_independent_expansion_with_compound_terms():
    variables = ("xp","xn","m","qp","qn","r")
    expected = "(xp+1)+(m+1)*(qn+xn)=((xn*xn)+(m+1)*(qp+xp))+(r+r) /\\ exists gap. gap+S(r+r)=m+1"
    actual = candidate.signed_integer_floor_relation("xp+1","xn*xn","m+1","qp+xp","qn+xn","r+r",tag="first",variables=variables)
    second = candidate.signed_integer_floor_relation("xp+1","xn*xn","m+1","qp+xp","qn+xn","r+r",tag="second",variables=variables)
    assert parse_formula_in_context(actual,list(variables)) == parse_formula_in_context(expected,list(variables))
    assert parse_formula_in_context(actual,list(variables)) == parse_formula_in_context(second,list(variables))


@pytest.mark.parametrize("bad",("","unknown","xp-xn","xp / xn","exists k. k","xp = xn",None))
def test_term_builder_rejects_foreign_or_ill_scoped_terms(bad):
    with pytest.raises((ValueError,TypeError)):
        candidate.signed_integer_floor_relation(bad,"xn","m","qp","qn","r",tag="audit",variables=("xp","xn","m","qp","qn","r"))


@pytest.mark.parametrize("context",((),("x","x"),("forall",),("x",[]),["x"]))
def test_term_builder_context_is_explicit_and_hygienic(context):
    with pytest.raises((ValueError,TypeError)):
        candidate.signed_integer_floor_relation("0","0","1","0","0","0",tag="audit",variables=context)


def test_floor_gap_binder_cannot_capture_a_context_variable():
    with pytest.raises(ValueError,match="captures"):
        candidate.signed_integer_floor_relation("x","x","x","x","x","x",tag="audit",variables=("x","sif_gap_audit"))


@pytest.mark.parametrize("argument",range(4))
def test_canonical_floor_binders_cannot_capture_any_argument(argument):
    args = ["input","m","quotient","r"]
    args[argument] = "sif_positive_audit"
    with pytest.raises(ValueError,match="captures"):
        candidate.signed_code_floor_relation(*args,tag="audit")


def _decode(code):
    return (code//2,0) if code%2==0 else (0,code//2+1)


def test_actual_single_division_algorithm_and_canonical_codes_cover_all_signs():
    for xp in range(12):
        for xn in range(12):
            for m in range(1,12):
                qp,r = divmod(xp+(m-1)*xn,m)
                qn = xn
                assert xp+m*qn == xn+m*qp+r
                assert 0 <= r < m
                q = qp-qn
                code = 2*q if q>=0 else 2*(-q-1)+1
                p,n = _decode(code)
                assert xp+m*n == xn+m*p+r
                assert p==0 or n==0
                assert q == (xp-xn)//m
