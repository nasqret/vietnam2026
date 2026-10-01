"""Statement, notation, source-closure and guard tests; no proof execution."""
import ast
from hashlib import sha256

import pytest

import sqrt2_power_rational_foundations as foundations
from sqrt2_power_definitions import DEFINITIONS, parse_named
from sqrt2_power_native import BASIS_NAMES, Basis, closed_formula
from sqrt2_power_pilot_contracts import canonical
from peano_lab.kernel.formulas import Eq, parse_formula_in_context
from peano_lab.kernel.terms import Mul, Var, Zero
from peano_lab.library import defined_syntax
from peano_lab.library.proof_bundle import encode_formula


def _eq(p, m, d, q, n, e):
    return f"(~({d}=0) /\\ (~({e}=0) /\\ ({p}*{e}+{n}*{d}={m}*{e}+{q}*{d})))"


EXPANDED = {
    "irat_eq_reflexive": "forall p m d. ~(d=0) -> " + _eq("p", "m", "d", "p", "m", "d"),
    "irat_eq_symmetric": "forall p m d q n e. " + _eq("p", "m", "d", "q", "n", "e")
        + " -> " + _eq("q", "n", "e", "p", "m", "d"),
    "irat_eq_transitive": "forall p m d q n e r s f. " + _eq("p", "m", "d", "q", "n", "e")
        + " -> " + _eq("q", "n", "e", "r", "s", "f") + " -> " + _eq("p", "m", "d", "r", "s", "f"),
    "irat_eq_scale_nonzero": "forall p m d k. ~(d=0) -> ~(k=0) -> "
        + _eq("p", "m", "d", "(p*k)", "(m*k)", "(d*k)"),
    "irat_eq_numerator_shift": "forall p m d h. ~(d=0) -> "
        + _eq("p", "m", "d", "(p+h)", "(m+h)", "d"),
    "irat_eq_negation_compatible": "forall p m d q n e. " + _eq("p", "m", "d", "q", "n", "e")
        + " -> " + _eq("m", "p", "d", "n", "q", "e"),
}


@pytest.mark.parametrize("name", tuple(EXPANDED))
def test_named_statements_expand_to_independent_exact_ha_sources(name):
    assert foundations.foundation_target(name) == closed_formula(EXPANDED[name])


def test_manifest_records_exact_sources_hashes_and_unfinished_authority(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("manifest cannot regenerate native proofs")
    monkeypatch.setattr(foundations.RationalBasis, "get", forbidden)
    manifest = foundations.foundation_manifest()
    assert len(manifest["rows"]) == 6
    for row in manifest["rows"]:
        target = foundations.foundation_target(row["name"])
        assert row["expanded_ast"] == encode_formula(target)
        assert row["expanded_ast_sha256"] == sha256(canonical(encode_formula(target))).hexdigest()
        assert row["named_source_sha256"] == sha256(row["named_source"].encode()).hexdigest()
        assert row["expanded_source_sha256"] == sha256(row["expanded_source"].encode()).hexdigest()
        assert row["closes_IR001"] is False
        assert row["independent_lean_checked"] is False
        assert row["library_admissions"] == 0
    assert manifest["IR001_closed"] is False
    assert manifest["requires_fresh_ordinary_HA_replay"] is True
    assert manifest["requires_independent_Lean"] is True


def test_local_literal_allowlist_is_exact_dependency_closed_and_nonmutating():
    before = frozenset(BASIS_NAMES)
    original_get = Basis.get
    local = foundations.RationalBasis()
    assert len(local.specs) == 19
    assert set(local.specs) == before | foundations.EXTRA_LAWS
    earlier = set()
    for name, row in local.specs.items():
        assert set(row[2]) <= earlier
        earlier.add(name)
    assert local.checked == {}
    assert BASIS_NAMES == before and len(BASIS_NAMES) == 15
    assert Basis.get is original_get


def test_local_cancellation_statements_keep_nonzero_premises():
    specs = foundations.RationalBasis().specs
    assert specs["mul_right_cancel_nonzero"][1] == "forall a b c. ~(c = 0) -> a * c = b * c -> a = b"
    assert specs["mul_left_cancel_nonzero"][1] == "forall a b c. ~(a = 0) -> a * b = a * c -> b = c"
    assert specs["add_right_cancel"][1] == "forall a b c. a + c = b + c -> a = b"


@pytest.mark.parametrize("name", ("excluded_fact", "add_left_cancel", "__class__", 1))
def test_unknown_local_arithmetic_requests_are_rejected_before_proving(name):
    with pytest.raises(foundations.FoundationError, match="non-allowlisted"):
        foundations.RationalBasis().get(name)


def test_missing_named_law_is_rejected_instead_of_ambient_lookup():
    raw = foundations.SOURCE.read_bytes()
    changed = raw.replace(b'"mul_right_cancel_nonzero",', b'"unlisted_cancellation",', 1)
    assert raw != changed
    with pytest.raises(foundations.FoundationError, match="nineteen-law"):
        foundations._load_literal_specs(changed)


def test_forward_or_unknown_dependency_is_rejected():
    raw = foundations.SOURCE.read_bytes()
    changed = raw.replace(b'("mul_comm", "mul_left_cancel_nonzero"),',
                          b'("mul_comm", "unknown_dependency"),', 1)
    assert raw != changed
    with pytest.raises(foundations.FoundationError, match="earlier local closed cone"):
        foundations._load_literal_specs(changed)


def test_definition_registry_is_local_immutable_and_does_not_shadow_global_names():
    original = dict(defined_syntax.DEFINITIONS_BY_NAME)
    assert not set(DEFINITIONS) & original.keys()
    foundations.foundation_manifest()
    assert dict(defined_syntax.DEFINITIONS_BY_NAME) == original
    with pytest.raises(TypeError):
        DEFINITIONS["Fake"] = object()


@pytest.mark.parametrize("source,names", (
    ("IRatEq(p,m,d,p,m)", ("p", "m", "d")),
    ("IRatValid(p,m,d,1)", ("p", "m", "d")),
    ("Unknown(p)", ("p",)),
    ("IRatValid(p,m,unbound)", ("p", "m", "d")),
    ("IRatValid(p,m,d)", ("p", "p", "d")),
    ("IRatValid(p,m,d)", ("p", "m", "bad name")),
))
def test_scoped_definition_parser_rejects_name_arity_and_binder_errors(source, names):
    with pytest.raises(ValueError):
        parse_named(source, names)


def test_existential_gap_does_not_capture_actual_argument():
    names = ("gap", "p", "m", "P", "M", "D")
    named = parse_named("IRatLt(p,m,gap,P,M,D)", names)
    expanded = parse_formula_in_context(
        "~(gap=0) /\\ (~(D=0) /\\ (exists witness. p*D+M*gap+S witness=m*D+P*gap))", list(names))
    assert named == expanded


def test_named_source_binds_every_free_name():
    for _, name, source, _, _ in foundations.FOUNDATIONS:
        assert parse_named(source) == foundations.foundation_target(name)
    with pytest.raises(ValueError):
        parse_named("forall p m. IRatValid(p,m,d)")


def test_ring_preflight_refuses_large_degree_and_foreign_variables():
    fourth_power = Mul(Mul(Var(0), Var(0)), Mul(Var(0), Var(0)))
    with pytest.raises(foundations.FoundationError, match="degree three"):
        foundations._preflight_ring(Eq(fourth_power, fourth_power))
    with pytest.raises(foundations.FoundationError, match="nine-binder"):
        foundations._preflight_ring(Eq(Var(9), Zero()))
    with pytest.raises(foundations.FoundationError, match="exact equation"):
        foundations._preflight_ring(object())


def test_no_full_theorem_registry_import_or_original_allowlist_assignment():
    tree = ast.parse(foundations.Path(foundations.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module != "peano_lab.library.theorems"
        if isinstance(node, ast.Import):
            assert all(alias.name != "peano_lab.library.theorems" for alias in node.names)
        if isinstance(node, ast.Assign):
            assert not any(isinstance(target, ast.Name) and target.id == "BASIS_NAMES" for target in node.targets)


@pytest.mark.parametrize("name", ("IR001", "irat_eq_transitive_weakened", None, 1))
def test_unknown_foundation_does_not_accept_a_replacement_formula(name):
    with pytest.raises(foundations.FoundationError):
        foundations.foundation_target(name)
