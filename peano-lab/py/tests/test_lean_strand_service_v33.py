"""V32/v33 file discovery and navigation, never theorem proof acceptance.

Temporary transport fixtures use the real literal v30 base and pinned prior
metadata, but DELIBERATELY EMPTY, FALSE delta rows.  They authenticate files
and routes only.  No successful proof stub, live release capability, worker,
network listener or catalogue-row decoder is supplied.  Actual output cases
are separate and require the genuinely published v33 trees.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest

from tests.test_lean_strand_service import ROOT, non_listening_review_server, service
import peano_catalog_shards as old_codec
import peano_catalog_shards_v32 as codec32
import peano_catalog_shards_v33 as codec33


VERSIONS = ("v32", "v33")
PACKAGES = (
    "constructive-research-explorer-v32", "constructive-completed-lower-explorer-v32",
    "constructive-historical-explorers-v32", "constructive-polynomial-euclidean-explorer-v33",
    "constructive-research-explorer-v33", "constructive-completed-lower-explorer-v33",
    "constructive-historical-explorers-v33",
)
ASSET_ROOT = ROOT / "book/_static"
BASE_SHA = "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"


def _json(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


@pytest.fixture(scope="module")
def owned_base(tmp_path_factory):
    # Later per-case links point only to this owned COPY.  Tamper tests replace
    # links before editing; no repository or other fixture byte is changed.
    path = tmp_path_factory.mktemp("v33-service-parent").resolve() / "catalog-v30.json"
    shutil.copyfile(ROOT / "artifacts/peano-library/alpha/catalog-v30.json", path)
    assert path.stat().st_size == 66503303
    return path


@pytest.fixture(scope="module")
def old_manifest():
    raw = (ROOT / "artifacts/peano-library/alpha/catalog-v32.json").read_bytes()
    assert len(raw) == 603900
    assert sha256(raw).hexdigest() == "41b9f387d88a5a4f0fe5ee2bd5578f37a27a4657b0a80f1a1a2cb5109f69a623"
    return json.loads(raw)


def _install_transport(root, version, old, base):
    codec = codec32 if version == "v32" else codec33
    directory = root / "artifacts/peano-library/alpha"
    directory.mkdir(parents=True, exist_ok=True)
    if not (directory / "catalog-v30.json").exists():
        (directory / "catalog-v30.json").hardlink_to(base)
    metadata = deepcopy(old["metadata"])
    if version == "v33":
        metadata.update(schema=codec.LOGICAL_SCHEMA, theorem_count=4092, checked_use_count=4092,
            alpha_only_count=3660, frontier_v33_campaign_counts={"polynomial-euclidean-division": 121},
            frontier_v33_ordered_names_sha256="80db0f58a3e58fa9edd5a8b2cc4a11314e262cdeb52a79955a63967e9dc674cc",
            parent_alpha_v32={"fixture_notice": "transport only; no admission"},
            alpha_v33_research_promotion={"fixture_notice": "NOT AN ACTUAL PROOF REPORT"})
    delta = _json({"schema": codec.DELTA_SCHEMA, "theorems": [],
                   "fixture_notice": "DELIBERATELY FALSE ROWS; navigation transport only"})
    _write(directory / codec.DELTA_BASENAME, delta)
    manifest = {"schema": codec.TRANSPORT_SCHEMA, "metadata": metadata,
        "parent": deepcopy(old["parent"]), "previous_v31_metadata": deepcopy(old["previous_v31_metadata"]),
        "delta": {"path": codec.DELTA_BASENAME, "schema": codec.DELTA_SCHEMA,
            "row_count": codec.DELTA_ROW_COUNT, "bytes": len(delta), "sha256": sha256(delta).hexdigest()}}
    if version == "v33": manifest["previous_v32_metadata"] = deepcopy(old["metadata"])
    payload = _json(manifest)
    path = directory / ("catalog-" + version + ".json")
    _write(path, payload)
    digest = sha256(payload).hexdigest()
    identity, count = metadata["edition_identity_sha256"], metadata["theorem_count"]
    channel = root / "artifacts/peano-library" / ("channels-" + version + ".json")
    _write(channel, _json({"schema": "peano-library-channels-" + version, "default_channel": "stable",
        "fixture_notice": "consistent file identity, NOT proof authority",
        "channels": {"alpha": {"artifact_path": "artifacts/peano-library/alpha/" + path.name,
            "artifact_sha256": digest, "edition_identity_sha256": identity,
            "theorem_count": count, "checked_use_count": count}}}))
    campaign = root / "book/_static" / ("constructive-research-campaign-" + version) / "campaign.json"
    _write(campaign, _json({"schema": "constructive-grand-campaign-v1",
        "fixture_notice": "file authentication only, no theorem acceptance",
        "meta": {"current_alpha_version": version, "current_alpha_checked_use_count": count},
        "ambitious_boundaries": {"alpha_" + version + "_edition": {"role": "current_immutable_release",
            "catalog_sha256": digest, "identity_sha256": identity,
            "theorem_count": count, "checked_use_count": count}}}))
    return SimpleNamespace(root=root, static=root / "book/_static", directory=directory,
        version=version, codec=codec, digest=digest, identity=identity, count=count,
        channel=channel, campaign=campaign, catalog=path,
        server=non_listening_review_server(root))


@pytest.fixture(params=VERSIONS)
def release(request, tmp_path, owned_base, old_manifest, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(service, "ROOT", root)
    return _install_transport(root, request.param, old_manifest, owned_base)


def _current(release):
    return release.server._current_constructive_release(release.static, owner=os.getuid())


def _mutate(path, change, *, same_time=False):
    info = path.stat()
    raw = path.read_bytes()
    data = json.loads(raw)
    change(data)
    altered = _json(data)
    if same_time: assert len(altered) == len(raw)
    path.write_bytes(altered)
    if same_time: os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))


def _install_package(release, package):
    phase = service.CONSTRUCTIVE_MODERN_PHASES[package]
    version = service.CONSTRUCTIVE_PUBLICATIONS[package].current_version
    directory = release.static / package
    if phase == "polynomial":
        from build_constructive_polynomial_euclidean_explorer_v33 import family_metadata
        metadata = family_metadata()
        original = {"families": [metadata], "files": {}}
    else:
        prior = "constructive-" + {"research": "research-explorer", "completed": "completed-lower-explorer",
                                   "historical": "historical-explorers"}[phase] + "-v32"
        original = json.loads((ASSET_ROOT / prior / "manifest.json").read_bytes())
    manifest = deepcopy(original)
    counts = service.CONSTRUCTIVE_MODERN_COUNTS[phase]
    manifest.update(schema="peano-lab-alpha-" + version + "-canonical-publication-v1-manifest",
        phase=phase, publication_scope="alpha_checked_use_publication", alpha_edition_version=version,
        alpha_first_enrolled_version=service.CONSTRUCTIVE_PUBLICATIONS[package].first_enrolled_version,
        alpha_edition_checked_use_count={"v32": 3971, "v33": 4092}[version], stable_edition_count=432,
        theorem_count=counts[0], checked_use_count=counts[1], stable_count=counts[2],
        catalog_sha256=release.digest, edition_identity_sha256=release.identity,
        current_G009_multiplicative_closure_proved=True, current_G091_prime_power_fields_proved=False,
        fixture_notice="navigation metadata only; no output or proof authority")
    for item in manifest["families"]: item["package"] = package
    if package in service.CONSTRUCTIVE_MODERN_PARENTS:
        old_name, size, digest = service.CONSTRUCTIVE_MODERN_PARENTS[package]
        raw = (ASSET_ROOT / old_name / "manifest.json").read_bytes()
        assert len(raw) == size and sha256(raw).hexdigest() == digest
        relative = "historical/" + old_name + "/manifest.json"
        _write(directory / relative, raw)
        manifest["historical_parent"] = {"directory": old_name, "bytes": size, "sha256": digest}
        manifest["files"][relative] = {"bytes": size, "sha256": digest}
    else:
        manifest.pop("historical_parent", None)
    if phase == "historical":
        for item in manifest["families"]:
            pin = item["first_admission"]["per_theorem_records"]
            raw = (ASSET_ROOT / "constructive-historical-explorers-v32" / pin["path"]).read_bytes()
            assert len(raw) == pin["bytes"] and sha256(raw).hexdigest() == pin["sha256"]
            _write(directory / pin["path"], raw)
    path = directory / "manifest.json"
    _write(path, _json(manifest))
    return directory, path, manifest


def test_exact_new_discovery_and_package_policies_keep_all_original_limits():
    assert tuple(service.CONSTRUCTIVE_RESEARCH_CAMPAIGNS.items()) == (
        ("constructive-research-campaign-v33", "v33"), ("constructive-research-campaign-v32", "v32"))
    assert service.CONSTRUCTIVE_CAMPAIGN_SUCCESSORS == ("constructive-completed-lower-campaign-v31",
        "constructive-gaussian-campaign", "constructive-priority-campaign", "constructive-grand-campaign")
    assert set(service.CONSTRUCTIVE_MODERN_PHASES) == set(PACKAGES)
    assert service.CONSTRUCTIVE_CATALOG_CODECS == {"v31": "peano_catalog_shards", "v32": "peano_catalog_shards_v32", "v33": "peano_catalog_shards_v33"}
    assert service.MAX_EXPLORER_CATALOG_BYTES == 64 * 1024 * 1024
    assert service.MAX_EXPLORER_CAMPAIGN_BYTES == 8 * 1024 * 1024
    assert service.MAX_EXPLORER_MANIFEST_BYTES == 2 * 1024 * 1024
    assert service.MAX_EXPLORER_FAMILIES == 512
    assert service.DEFAULT_STRAND_NODES == 1024
    assert sum(service.COMPLETED_LOWER_V31_FAMILIES.values()) == 574
    assert len(service.HISTORICAL_V31_FIRST_ADMISSIONS) == 44


def test_real_three_file_navigation_never_decodes_or_accepts_false_delta(release, monkeypatch):
    decoded, authenticated = [], []
    original_decode = old_codec._decode
    original_verify = release.codec.verify_catalog_bindings
    def observe_decode(raw, label):
        assert label == release.version + " manifest"
        decoded.append(label)
        return original_decode(raw, label)
    def observe_verify(path, **kwargs):
        authenticated.append(path)
        return original_verify(path, **kwargs)
    def no_logical_load(*_args, **_kwargs):
        pytest.fail("navigation attempted to load theorem rows")
    monkeypatch.setattr(old_codec, "_decode", observe_decode)
    monkeypatch.setattr(release.codec, "verify_catalog_bindings", observe_verify)
    monkeypatch.setattr(release.codec, "load_catalog", no_logical_load)
    assert _current(release) == _current(release) == (release.version, release.digest, release.identity)
    assert authenticated == [release.catalog]
    assert decoded and set(decoded) == {release.version + " manifest"}
    fingerprint = next(iter(release.server._constructive_release_cache))[3]
    assert tuple(Path(row.path).name for row in fingerprint) == (
        "catalog-" + release.version + ".json", "catalog-v30.json", "catalog-" + release.version + "-delta.json")
    delta = json.loads((release.directory / release.codec.DELTA_BASENAME).read_bytes())
    assert delta["theorems"] == [] and "FALSE" in delta["fixture_notice"]
    assert all(type(value) is tuple and len(value) == 3 for value in release.server._constructive_release_cache.values())


@pytest.mark.parametrize("role", ("manifest", "parent", "delta"))
def test_each_real_catalog_document_invalidates_warm_cache_after_same_size_mtime_change(release, role):
    assert _current(release)[0] == release.version
    path = {"manifest": release.catalog, "parent": release.directory / "catalog-v30.json",
            "delta": release.directory / release.codec.DELTA_BASENAME}[role]
    before = path.stat()
    # Replace the per-case parent link before any write, preserving its shared
    # module fixture and the repository's original bytes.
    if role == "parent":
        replacement = path.with_suffix(".private")
        shutil.copyfile(path, replacement)
        replacement.replace(path)
    with path.open("r+b") as stream:
        old = stream.read(1)
        stream.seek(0)
        stream.write(b" " if old != b" " else b"\n")
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert path.stat().st_size == before.st_size and path.stat().st_mtime_ns == before.st_mtime_ns
    with pytest.raises(service.ServiceError): _current(release)


@pytest.mark.parametrize("role", ("manifest", "parent", "delta"))
@pytest.mark.parametrize("mutation", ("absent", "symlink", "directory", "oversized"))
def test_each_catalog_input_stays_regular_present_and_bounded_on_warm_cache(release, role, mutation):
    assert _current(release)[0] == release.version
    path = {"manifest": release.catalog, "parent": release.directory / "catalog-v30.json",
            "delta": release.directory / release.codec.DELTA_BASENAME}[role]
    original = path.with_suffix(".owned")
    path.rename(original)
    if mutation == "symlink": path.symlink_to(original)
    elif mutation == "directory": path.mkdir()
    elif mutation == "oversized":
        with path.open("wb") as stream: stream.truncate(service.MAX_EXPLORER_CATALOG_BYTES + 1)
    with pytest.raises(service.ServiceError): _current(release)


@pytest.mark.parametrize("which", ("campaign", "channel"))
def test_same_size_same_mtime_control_change_invalidates_warm_cache(release, which):
    assert _current(release)[0] == release.version
    path = getattr(release, which)
    if which == "campaign":
        change = lambda value: value["ambitious_boundaries"]["alpha_" + release.version + "_edition"].update(identity_sha256="f" * 64)
    else:
        change = lambda value: value["channels"]["alpha"].update(edition_identity_sha256="f" * 64)
    _mutate(path, change, same_time=True)
    with pytest.raises(service.ServiceError): _current(release)


@pytest.mark.parametrize("mutation", ("missing", "broken_json", "wrong_version", "downgrade_v31", "wrong_schema", "not_directory", "symlink"))
def test_present_newest_campaign_never_falls_back_to_older_valid_release(tmp_path, old_manifest, owned_base, monkeypatch, mutation):
    root = tmp_path.resolve()
    monkeypatch.setattr(service, "ROOT", root)
    older = _install_transport(root, "v32", old_manifest, owned_base)
    assert _current(older)[0] == "v32"
    directory = older.static / "constructive-research-campaign-v33"
    if mutation == "not_directory": directory.write_bytes(b"not a directory")
    elif mutation == "symlink": directory.symlink_to(older.campaign.parent, target_is_directory=True)
    else:
        directory.mkdir()
        if mutation != "missing":
            raw = json.loads(older.campaign.read_bytes())
            if mutation == "broken_json": _write(directory / "campaign.json", b"{")
            else:
                if mutation == "downgrade_v31": raw["meta"]["current_alpha_version"] = "v31"
                elif mutation == "wrong_schema": raw["schema"] = "wrong"
                # The wrong_version case deliberately claims v32 in v33.
                _write(directory / "campaign.json", _json(raw))
    # The unchanged strict JSON reader raises JSONDecodeError (ValueError)
    # directly; the public family-review boundary catches it and fails closed.
    with pytest.raises(ValueError): _current(older)


def test_valid_v33_precedes_a_coexisting_valid_v32_transport(tmp_path, old_manifest, owned_base, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(service, "ROOT", root)
    old = _install_transport(root, "v32", old_manifest, owned_base)
    assert _current(old)[0] == "v32"
    current = _install_transport(root, "v33", old_manifest, owned_base)
    assert _current(old) == _current(current) == ("v33", current.digest, current.identity)


@pytest.mark.parametrize("version", ("v30", "v31", "v33", "v032", True, None))
def test_v32_named_campaign_cannot_claim_another_release(release, version):
    _mutate(release.campaign, lambda value: value["meta"].update(current_alpha_version=version))
    if version == release.version:
        assert _current(release)[0] == release.version
    else:
        with pytest.raises(service.ServiceError): _current(release)


def test_modern_default_channel_remains_stable(release):
    assert _current(release)[0] == release.version
    _mutate(release.channel, lambda value: value.update(default_channel="alpha"))
    with pytest.raises(service.ServiceError): _current(release)


@pytest.mark.parametrize("package", PACKAGES)
def test_all_seven_exact_package_policies_preserve_first_admission_and_routes(tmp_path, old_manifest, owned_base, monkeypatch, package):
    root = tmp_path.resolve()
    monkeypatch.setattr(service, "ROOT", root)
    version = service.CONSTRUCTIVE_PUBLICATIONS[package].current_version
    release = _install_transport(root, version, old_manifest, owned_base)
    directory, path, manifest = _install_package(release, package)
    before = sha256(path.read_bytes()).hexdigest()
    assert all(release.server.reviewed_constructive_family(directory, row["slug"]) for row in manifest["families"])
    assert sha256(path.read_bytes()).hexdigest() == before
    assert not release.server.reviewed_constructive_family(directory, "foreign-family")
    if service.CONSTRUCTIVE_MODERN_PHASES[package] == "historical":
        assert manifest["alpha_first_enrolled_version"] == "mixed_preserved"
        assert manifest["stable_count"] == 443  # repeated historical records, not a changed global Stable432.
    assert "first_enrollment_catalog_sha256" not in manifest


@pytest.mark.parametrize("field,value", (
    ("phase", "historical"), ("alpha_edition_version", "v31"), ("alpha_first_enrolled_version", "v31"),
    ("first_enrollment_catalog_sha256", "0" * 64), ("publication_scope", "local-only-checkpoint"),
    ("theorem_count", 174), ("checked_use_count", True), ("stable_count", 1),
    ("alpha_edition_checked_use_count", 3970), ("stable_edition_count", 433),
    ("current_G009_multiplicative_closure_proved", False), ("current_G091_prime_power_fields_proved", True),
))
def test_modern_manifest_mutations_reject_even_after_warm_family_cache(release, field, value):
    package = "constructive-research-explorer-" + release.version
    directory, path, _manifest = _install_package(release, package)
    assert release.server.reviewed_constructive_family(directory, "multiplicative-convolution")
    _mutate(path, lambda item: item.update({field: value}))
    assert not release.server.reviewed_constructive_family(directory, "multiplicative-convolution")


@pytest.mark.parametrize("attack", ("missing", "repeated", "unknown", "unhashable_slug", "count", "checked_bool",
                                    "first", "package", "stable", "name", "tag", "tag_type", "tag_missing"))
def test_modern_family_metadata_and_tag_identity_cannot_drift(release, attack):
    package = "constructive-research-explorer-" + release.version
    directory, path, _manifest = _install_package(release, package)
    assert release.server.reviewed_constructive_family(directory, "multiplicative-convolution")
    def change(value):
        rows = value["families"]
        if attack == "missing": rows.pop()
        elif attack == "repeated": rows[1] = deepcopy(rows[0])
        elif attack == "unknown": rows[0]["slug"] = "unknown-family"
        elif attack == "unhashable_slug": rows[0]["slug"] = []
        elif attack == "count": rows[0]["theorem_count"] -= 1
        elif attack == "checked_bool": rows[0]["checked_use_count"] = True
        elif attack == "first": rows[0]["first_admitted_version"] = "v31"
        elif attack == "package": rows[0]["package"] += "-foreign"
        elif attack == "stable": rows[0]["stable_count"] = 1
        else:
            tags = rows[0]["tags"]
            name = next(iter(tags))
            if attack == "name": tags["not_a_new_theorem"] = tags.pop(name)
            elif attack == "tag": tags[name] = "PX0001"
            elif attack == "tag_type": tags[name] = []
            elif attack == "tag_missing": tags.pop(name)
    _mutate(path, change)
    assert not release.server.reviewed_constructive_family(directory, "multiplicative-convolution")


@pytest.mark.parametrize("package", tuple(service.CONSTRUCTIVE_MODERN_PARENTS))
@pytest.mark.parametrize("attack", ("parent_record", "parent_bytes", "parent_symlink", "parent_route", "old_family_field"))
def test_literal_history_parent_remains_checked_on_every_warm_request(tmp_path, old_manifest, owned_base, monkeypatch, package, attack):
    root = tmp_path.resolve()
    monkeypatch.setattr(service, "ROOT", root)
    release = _install_transport(root, service.CONSTRUCTIVE_PUBLICATIONS[package].current_version, old_manifest, owned_base)
    directory, path, manifest = _install_package(release, package)
    slug = manifest["families"][0]["slug"]
    assert release.server.reviewed_constructive_family(directory, slug)
    parent = directory / "historical" / service.CONSTRUCTIVE_MODERN_PARENTS[package][0] / "manifest.json"
    if attack == "parent_record": _mutate(path, lambda value: value["historical_parent"].update(sha256="0" * 64))
    elif attack == "parent_bytes":
        raw = parent.read_bytes()
        parent.write_bytes(b" " + raw[1:])
    elif attack == "parent_symlink":
        original = parent.with_suffix(".owned")
        parent.rename(original)
        parent.symlink_to(original)
    elif attack == "parent_route":
        original = parent.parent.with_name(parent.parent.name + "-owned")
        parent.parent.rename(original)
        parent.parent.symlink_to(original, target_is_directory=True)
    elif attack == "old_family_field": _mutate(path, lambda value: value["families"][0].update(title="rewritten history"))
    assert not release.server.reviewed_constructive_family(directory, slug)


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("attack", ("descriptor", "sidecar", "unrelated_sidecar", "mixed_scalar"))
def test_all44_historical_descriptors_and_full_sidecars_stay_literal(tmp_path, old_manifest, owned_base, monkeypatch, version, attack):
    root = tmp_path.resolve()
    monkeypatch.setattr(service, "ROOT", root)
    release = _install_transport(root, version, old_manifest, owned_base)
    directory, path, manifest = _install_package(release, "constructive-historical-explorers-" + version)
    assert release.server.reviewed_constructive_family(directory, "quadratic-reciprocity")
    if attack == "descriptor": _mutate(path, lambda value: value["families"][0]["first_admission"].update(policy="infer current"))
    elif attack == "mixed_scalar": _mutate(path, lambda value: value.update(first_enrollment_catalog_sha256=release.digest))
    else:
        item = manifest["families"][0 if attack == "sidecar" else -1]
        sidecar = directory / item["first_admission"]["per_theorem_records"]["path"]
        raw = sidecar.read_bytes()
        sidecar.write_bytes(b" " + raw[1:])
    assert not release.server.reviewed_constructive_family(directory, "quadratic-reciprocity")


@pytest.mark.parametrize("segment", ("constructive-research-explorer-v033", "constructive-research-explorer-V33",
    "constructive-polynomial-euclidean-explorer-v33-extra", "constructive-polynomial-euclidean-explorer-v34",
    "constructive-historical-explorers-v32-extra", "constructive-completed-lower-explorer-v032"))
def test_unregistered_modern_spellings_never_inherit_a_policy(segment):
    assert service._constructive_explorer_candidate(segment)
    assert not service._constructive_explorer_segment(segment)


def test_legacy_first_admission_logic_and_service_limits_are_not_rewritten():
    assert service.CONSTRUCTIVE_PUBLICATIONS["constructive-completed-lower-explorer-v31"].current_version == "v31"
    assert service.CONSTRUCTIVE_PUBLICATIONS["constructive-completed-lower-explorer-v31"].first_enrolled_version == "v31"
    assert service.CONSTRUCTIVE_PUBLICATIONS["constructive-historical-explorers-v31"].first_enrolled_version == "mixed_preserved"
    source = inspect.getsource(service.LeanStrandServer._historical_v31_provenance)
    assert "HISTORICAL_V31_FIRST_ADMISSIONS" in source and "records[\"bytes\"] + 1" in source
    assert "sha256(raw).hexdigest() != records[\"sha256\"]" in source
    source = inspect.getsource(service.LeanStrandServer._current_constructive_release)
    assert "catalog_input_fingerprint" in source and "verify_catalog_bindings" in source
    assert "load_catalog(" not in source and "decode_proof_bundle" not in source


@pytest.mark.parametrize("name,expected", (
    ("ServiceLimits", "428b56ea839a86f9d4f7f5461490e0d3ca6737dc3f9f77c5c852718fcd1b19ff"),
    ("JobManager", "9f441b34441012aea13b8a719171245e5b7dc94bb0bd372c309c59156c4bb9ef"),
    ("LeanStrandHandler", "5818dd03bc7b1254a0a88428bda28484df670a16333b952ce06ab3c7157acfb7"),
))
def test_original_limits_proof_worker_and_http_handler_asts_remain_exact(name, expected):
    tree = ast.parse(Path(service.__file__).read_text())
    source = next(row for row in tree.body if isinstance(row, ast.ClassDef) and row.name == name)
    assert sha256(ast.dump(source, include_attributes=False).encode()).hexdigest() == expected


def test_the_three_old_actual_cases_only_move_current_observation_not_first_v31_identity():
    path = ROOT / "peano-lab/py/tests/test_lean_strand_service_v31.py"
    tree = ast.parse(path.read_text())
    actual = {row.name: ast.unparse(row) for row in tree.body if isinstance(row, ast.FunctionDef)
              and row.name.startswith("test_actual_current_v31_")}
    assert len(actual) == 2
    pages = actual["test_actual_current_v31_publications_and_principal_panels_pass_read_only_service_review"]
    assert "'-v33'" in pages and "original_manifest['alpha_edition_version'] == 'v31'" in pages
    assert "original_manifest['first_enrollment_catalog_sha256'] == original_manifest['catalog_sha256']" in pages
    files = actual["test_actual_current_v31_uses_three_unchanged_bound_documents_and_preserves_old_catalog"]
    assert "bindings.delta.row_count == 574" in files and "current.delta.row_count == 870" in files
    assert "pytest.skip" not in "\n".join(actual.values()) and "xfail" not in "\n".join(actual.values())


def test_source_only_registration_does_not_import_an_alpha_edition():
    before = {name: module for name, module in sys.modules.items() if name.startswith("peano_lab.library.editions")}
    assert all(service._constructive_explorer_segment(name) for name in PACKAGES)
    assert {name: module for name, module in sys.modules.items() if name.startswith("peano_lab.library.editions")} == before


@pytest.mark.parametrize("package", tuple(name for name in PACKAGES if name.endswith("v33")))
def test_actual_v33_current_packages_and_new_principals_are_reviewed_read_only(package):
    directory = ASSET_ROOT / package
    path = directory / "manifest.json"
    assert path.is_file(), "requires actual fresh v33 publication; never a fixture receipt"
    before = path.read_bytes()
    manifest = json.loads(before)
    server = non_listening_review_server(ROOT)
    assert server._current_constructive_release(ASSET_ROOT, owner=os.getuid())[0] == "v33"
    assert all(server.reviewed_constructive_family(directory, row["slug"]) for row in manifest["families"])
    if package == "constructive-polynomial-euclidean-explorer-v33":
        from build_constructive_polynomial_euclidean_explorer_v33 import PRINCIPAL_ROOTS
        handler = object.__new__(service.LeanStrandHandler)
        handler.server = server
        tags = manifest["families"][0]["tags"]
        for name in PRINCIPAL_ROOTS:
            for prefix in ("explorer/tag", "explorer/defined/tag"):
                page = directory / "polynomial-euclidean-division" / prefix / (tags[name] + ".html")
                raw = page.read_bytes()
                shown = handler._inject_selector(page, page.relative_to(ROOT).parts)
                assert shown is not None and b"lean-selector.js" in shown and b"lean-selector.css" in shown
                assert page.read_bytes() == raw
    assert path.read_bytes() == before
