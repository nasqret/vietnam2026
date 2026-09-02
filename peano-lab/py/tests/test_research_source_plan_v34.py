"""Canonical source/ownership guards; no parent catalogue or proof workers."""
import ast
import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import ModuleType
import sys

import pytest

from peano_lab.library import research_source_plan_v34 as source
from peano_lab.library.campaign_lower_layer_closure import _specs_digest
from peano_lab.library.theorems import TheoremSpec


@pytest.fixture(scope="module", autouse=True)
def source_file_preservation():
    paths = [Path(source.__file__), Path(__file__)]
    paths.extend(source.HERE/(record[0]+".py") for record in (
        *source.GCD_CANONICAL_PROVIDERS, *source.CONGRUENCE_CANONICAL_PROVIDERS,
        *source.GCD_OWNED_PROVIDERS, *source.CONGRUENCE_OWNED_PROVIDERS))
    paths.append(source.HERE/"theorems.py")
    def snapshot():
        return [[str(path), len(raw), sha256(raw).hexdigest()]
                for path in sorted(set(paths)) for raw in (path.read_bytes(),)]
    before = snapshot()
    yield
    after = snapshot()
    assert before == after
    print("SOURCE_INPUT_PINS_OBSERVATION "+json.dumps({"before": before, "after": after}, sort_keys=True))


@pytest.fixture(scope="module")
def gcd_cone():
    return source.source_cone("polynomial-gcd-bezout")


def test_actual_canonical_gcd_cone_preserves_every_spec_and_root(gcd_cone):
    cone = gcd_cone
    assert (len(cone.specs), len(cone.canonical), len(cone.owned), len(cone.root_names)) == (492, 373, 119, 13)
    assert sum(len(row.dependencies) for row in cone.specs) == 1565
    assert _specs_digest(cone.specs) == "453f7dc94a9ed2fb6c89730024af97e6aaec9168c30c106450d57d2cea8db0eb"
    assert _specs_digest(cone.owned) == "72701944f71e8d93c55bcf29d27fc92ac616452801ab75c3e478df4d77df4c38"
    assert sha256("\n".join(row.name for row in cone.specs).encode()).hexdigest() == "608ac8f64143e60628e49875efd3b3ef3c5389eff2f17ecabe98f96770a9e93f"
    seen = set()
    for row in cone.specs:
        assert type(row) is TheoremSpec and row.name not in seen
        assert set(row.dependencies) <= seen
        seen.add(row.name)
    used = {name for row in cone.specs for name in row.dependencies}
    assert cone.root_names == tuple(row.name for row in cone.owned if row.name not in used)
    assert "prime_field_polynomial_normalized_gcd_bezout_exists" in cone.root_names
    assert "prime_field_polynomial_normalized_gcd_equivalent_unique" in cone.root_names
    assert "prime_field_polynomial_bezout_is_right_gcd" in {row.name for row in cone.owned}
    assert "prime_field_polynomial_bezout_is_right_gcd" not in cone.root_names


def test_source_dfs_has_no_artifact_positions_or_acceptance_capability(gcd_cone):
    assert not hasattr(gcd_cone, "positions")
    assert not hasattr(gcd_cone, "require_unchanged")
    assert not hasattr(gcd_cone, "checked")
    contract = source.GCD_CONTRACT
    assert contract.dfs_names_sha256 != contract.original_names_sha256
    assert contract.original_frontier_count == 325 != len(gcd_cone.owned)
    assert contract.original_frontier_specs_sha256 == "7751feff227a4b298a2c484f83bf85c2a5db730ed9e4e2f62b095b1f5866252a"
    assert contract.original_names_sha256 == "37f749a11c76fd6d38d4a328dfd450fd8a0ea3e79ffac8f22ad4874239f29e25"
    assert contract.original_specs_sha256 == "ae797cbf373142f63f7dd86af1f5ddad0909f4f1df755af6ad523a9c6c7e1d5d"


def test_actual_congruence_source_cone_extracts_only_the_unchanged_fermat_row():
    cone = source.source_cone("congruence-arithmetic")
    assert (len(cone.specs), len(cone.canonical), len(cone.owned), len(cone.root_names)) == (214, 202, 12, 5)
    assert sum(len(row.dependencies) for row in cone.specs) == 642
    assert _specs_digest(cone.specs) == "61c20f122d4281a6177865d1d39cd3a5b3939584c852ca028647e0bcf46cc157"
    assert _specs_digest(cone.owned) == "b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8"
    assert cone.owned[-1].name == "fermat_little_all_inputs"
    assert "fermat_little_all_inputs" not in {row.name for row in cone.canonical}
    record = next(r for r in source.CONGRUENCE_CANONICAL_PROVIDERS if r[0] == "fermat_endpoints_candidate")
    original = next(row for row in source._module_factory(record) if row.name == "fermat_little_all_inputs")
    assert original == cone.owned[-1]


def test_modified_extracted_fermat_row_is_not_an_allowed_overlap(monkeypatch):
    original = source._module_factory
    def changed(record):
        result = original(record)
        if record[0] == "fermat_endpoints_candidate":
            return tuple(replace(row, summary="different canonical Fermat")
                         if row.name == "fermat_little_all_inputs" else row for row in result)
        return result
    monkeypatch.setattr(source, "_module_factory", changed)
    with pytest.raises(source.SourcePlanError, match="extracted Fermat"):
        source.source_cone("congruence-arithmetic")


def test_every_explicit_canonical_pin_matches_installed_bytes():
    assert len(source.GCD_CANONICAL_PROVIDERS) == 26
    assert len(source.CONGRUENCE_CANONICAL_PROVIDERS) == 11
    assert len(source.GCD_OWNED_PROVIDERS) == 20
    for record in (*source.GCD_CANONICAL_PROVIDERS, *source.CONGRUENCE_CANONICAL_PROVIDERS,
                   *source.GCD_OWNED_PROVIDERS):
        module, _factory, size, digest = record[:4]
        raw = (source.HERE/(module+".py")).read_bytes()
        assert len(raw) == size and sha256(raw).hexdigest() == digest
    factories = {r[0]: r[1] for r in (*source.GCD_CANONICAL_PROVIDERS,
                                     *source.CONGRUENCE_CANONICAL_PROVIDERS)}
    assert factories["bertrand_power_valuation_laws_candidate"] == "make_bertrand_power_valuation_law_candidate_theorems"
    assert factories["fermat_endpoints_candidate"] == "make_fermat_endpoint_candidate_theorems"
    assert factories["finite_product_reindex_candidate"] == "make_finite_product_reindex_candidate"


@pytest.mark.parametrize("slug", [None, True, "", "../polynomial-gcd-bezout", "unknown"])
def test_invalid_family_rejects_before_imports(slug, monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail("invalid family imported a source")
    monkeypatch.setattr(source, "import_module", forbidden)
    with pytest.raises(source.SourcePlanError): source.source_cone(slug)


def test_unregistered_congruence_contract_remains_explicitly_fail_closed(monkeypatch):
    monkeypatch.setattr(source, "CONGRUENCE_CONTRACT", None)
    with pytest.raises(source.SourcePlanError, match="not registered"):
        source.source_cone("congruence-arithmetic")


@pytest.mark.parametrize("module,size,digest", [("../theorems", 1, "0"*64), ("theorems", True, "0"*64),
    ("theorems", 2097153, "0"*64), ("theorems", 0, "0"*64),
    ("theorems", 536011, "A"*64), ("theorems", 536011, None)])
def test_source_pin_types_paths_and_original_source_budget(module, size, digest):
    with pytest.raises(source.SourcePlanError): source._read_source(module, size, digest)


def test_source_symlink_rejects_even_with_exact_matching_target(tmp_path, monkeypatch):
    payload = b"# source only\n"
    target = tmp_path/"actual.py"
    target.write_bytes(payload)
    (tmp_path/"fixture.py").symlink_to(target)
    monkeypatch.setattr(source, "HERE", tmp_path)
    with pytest.raises(source.SourcePlanError):
        source._read_source("fixture", len(payload), sha256(payload).hexdigest())


def test_same_length_changed_source_rejects(tmp_path, monkeypatch):
    (tmp_path/"fixture.py").write_bytes(b"second\n")
    monkeypatch.setattr(source, "HERE", tmp_path)
    with pytest.raises(source.SourcePlanError, match="digest"):
        source._read_source("fixture", 7, sha256(b"first!\n").hexdigest())


def test_foreign_cached_module_owner_is_rejected_and_preserved(monkeypatch):
    record = source.GCD_CANONICAL_PROVIDERS[0]
    fullname = "peano_lab.library."+record[0]
    foreign = ModuleType(fullname)
    foreign.__file__ = "/foreign/owner.py"
    monkeypatch.setitem(sys.modules, fullname, foreign)
    with pytest.raises(source.SourcePlanError, match="foreign canonical module"):
        source._module_factory(record)
    assert sys.modules[fullname] is foreign


def test_foreign_factory_owner_is_rejected(monkeypatch):
    record = source.GCD_CANONICAL_PROVIDERS[0]
    module = source.import_module("."+record[0], package="peano_lab.library")
    monkeypatch.setattr(module, record[1], lambda _type: pytest.fail("foreign factory executed"))
    with pytest.raises(source.SourcePlanError, match="foreign canonical factory"):
        source._module_factory(record)


def test_different_canonical_overlap_rejects_and_equal_overlap_preserves_identity(gcd_cone):
    row = gcd_cone.canonical[0]
    table = {row.name: row}
    source._merge(table, (replace(row),))
    assert table[row.name] is row
    with pytest.raises(source.SourcePlanError, match="different exact specifications"):
        source._merge(table, (replace(row, summary=row.summary+" changed"),))


def test_owned_spec_mutation_rejects_without_any_parent_or_proof(monkeypatch):
    original = source._module_factory
    target = source.GCD_OWNED_PROVIDERS[0][0]
    def changed(record):
        result = original(record)
        if record[0] == target:
            result = (replace(result[0], summary=result[0].summary+" changed"), *result[1:])
        return result
    monkeypatch.setattr(source, "_module_factory", changed)
    with pytest.raises(source.SourcePlanError, match="owned factory exact"):
        source.source_cone()


def test_provider_metadata_owner_mutation_rejects(monkeypatch):
    from peano_lab.library import campaign_research_v34_closure as provider
    old = provider.FACTORIES
    monkeypatch.setattr(provider, "FACTORIES", (replace(old[0], source_bytes=old[0].source_bytes+1), *old[1:]))
    with pytest.raises(source.SourcePlanError, match="owner records differ"):
        source.source_cone()


def test_pure_cone_never_opens_old_parent_or_proofs(monkeypatch):
    from peano_lab.library import campaign_bottom_layer_closure as original
    def forbidden(*args, **kwargs): pytest.fail("pure source cone opened an old parent/proof")
    monkeypatch.setattr(original, "parent_snapshot", forbidden)
    monkeypatch.setattr(original, "bottom_layer_plan", forbidden)
    result = source.source_cone()
    assert len(result.specs) == 492
    assert not any(name.startswith("peano_lab.library.editions") for name in sys.modules)


def test_original_plan_seam_is_unsubstituted_and_frontier_overlap_checked_first():
    tree = ast.parse(Path(source.__file__).read_text())
    selected = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "source_selection")
    calls = [ast.unparse(n.func) for n in ast.walk(selected) if isinstance(n, ast.Call)]
    assert calls.count("original.parent_snapshot") == 1
    assert calls.count("original.bottom_layer_plan") == 1
    lines = {ast.unparse(n.func): n.lineno for n in ast.walk(selected) if isinstance(n, ast.Call)}
    overlap = next(n.lineno for n in ast.walk(selected) if isinstance(n, ast.Constant)
                   and n.value == "original v30 overlap differs")
    assert overlap < lines["original.bottom_layer_plan"]
    text = Path(source.__file__).read_text()
    assert "working_gcd_closure_support" not in text
    assert "working_euclidean_closure_support" not in text
    forbidden = {"check", "check_proof_bundle", "replay", "decode_proof_bundle", "subprocess.run"}
    assert not forbidden.intersection(ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call))
