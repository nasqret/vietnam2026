"""Pure syntax/protocol and reject-only polynomial checkpoint regressions.

No test here accepts a mocked proof checker or imports the large Alpha
edition.  Synthetic messages explicitly say ``proofs_verified=False`` and
exercise only the bounded transport codec.  Genuine whole-bundle, compiled
Lean and ordinary-root verification remain the separate eight-worker gate.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


def tracked_editions():
    return {name: module for name, module in sys.modules.items()
            if name.startswith("peano_lab.library.editions")}


BEFORE_IMPORTS = tracked_editions()

import constructive_polynomial_division_support as support
import constructive_polynomial_division_checkpoints as checkpoints
import check_constructive_polynomial_division as driver
import export_constructive_polynomial_division as exporter
from peano_lab.library.theorems import TheoremSpec


def assert_same_modules(before):
    after = tracked_editions()
    assert after.keys() == before.keys()
    assert all(after[name] is module for name, module in before.items())


assert_same_modules(BEFORE_IMPORTS)


@pytest.fixture(autouse=True)
def preserve_authority_module_identities():
    before = tracked_editions()
    yield
    assert_same_modules(before)


FACTORIES = (
    ("prime_field_polynomial_subtraction_candidate", 26),
    ("prime_field_polynomial_trim_candidate", 22),
    ("prime_field_polynomial_monic_candidate", 20),
    ("prime_field_polynomial_synthetic_candidate", 17),
)
PRINCIPALS = (
    "prime_field_polynomial_subtract_exists",
    "prime_field_polynomial_trim_exists_unique",
    "prime_field_polynomial_monic_normalization_exists_unique",
    "prime_field_polynomial_synthetic_exists_unique",
    "prime_field_polynomial_synthetic_represented_degree",
    "prime_field_polynomial_synthetic_zero_remainder_iff",
)
EXPECTED_SPECS_SHA256 = "93663cc10d2d034fb933a60a914f1656fd0beb8d715bbbab8d8e1359c780ab11"
NONCE, BINDING = "ab" * 32, "cd" * 32


class Stopped(RuntimeError):
    """An always-rejecting sentinel, never synthetic proof acceptance."""


def reject(*args, **kwargs):
    raise Stopped("no proof authority in this pure test")


@pytest.fixture(scope="module")
def actual_syntax():
    state = support.load_candidate_state(final=False)
    assert len(state.rows) == 85
    return state


def test_exact_four_families_sources_specification_and_six_principal_inventory(actual_syntax):
    assert tuple((item.module, item.count) for item in support.FACTORIES) == FACTORIES
    assert support.EXPECTED_NEW_COUNT == 85
    assert support.PRIOR_RESEARCH_COUNT == 90
    assert support.PARENT_COUNT == 3796 and support.PARENT_STABLE_COUNT == 432
    assert tuple(pin.path for pin in actual_syntax.sources) == tuple(item.path for item in support.FACTORIES)
    assert actual_syntax.sources == support.MATH_SOURCE_PINS
    assert actual_syntax.specs_sha256 == support.NEW_SPECS_SHA256 == EXPECTED_SPECS_SHA256
    assert len(set(row.name for row in actual_syntax.rows)) == 85
    assert checkpoints.PRINCIPAL_ROOTS == PRINCIPALS
    assert set(PRINCIPALS) <= {row.name for row in actual_syntax.rows}
    assert len(PRINCIPALS) == len(set(PRINCIPALS)) == 6
    for pin in actual_syntax.sources:
        raw = (support.ROOT / pin.path).read_bytes()
        assert len(raw) == pin.bytes and sha256(raw).hexdigest() == pin.sha256


def test_current_polynomial_dependencies_are_topological_and_not_relabelled_g009(actual_syntax):
    current = {row.name for row in actual_syntax.rows}
    previous = set()
    for row in actual_syntax.rows:
        assert set(row.dependencies) & current <= previous
        assert len(row.dependencies) == len(set(row.dependencies))
        assert not any(name.startswith(("dirichlet_", "signed_support_reindex_", "signed_cartesian_product_"))
                       for name in row.dependencies)
        previous.add(row.name)
    assert support.select_support is support.inherited.select_support
    assert support.dependency_cone is support.inherited.dependency_cone
    assert support.current_parent_specs is support.inherited.current_parent_specs
    assert support.parent_seed_paths is support.inherited.parent_seed_paths
    assert support.closure is support.inherited.closure


def test_actual_registered_bundle_is_data_only_with_the_exact_complete_counts():
    pin = checkpoints.FINAL_ARTIFACT
    assert type(pin) is checkpoints.ArtifactPin
    assert (pin.nodes, pin.edges, pin.body_nodes) == (293, 740, 17412)
    assert pin.nodes == 207 + 85 + 1
    assert pin.bytes == 1060637
    assert pin.sha256 == "fec8cf768ef2b94430d58d947daa0affada315bbc5160a03991dc4d2550dd0e9"
    support.check_pin(support.FilePin(pin.path, pin.bytes, pin.sha256), support.ROOT,
                      support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    assert set(pin.__dataclass_fields__) == {"path", "bytes", "sha256", "nodes", "edges", "body_nodes"}


def syntax_row(name, dependencies=(), statement="0=0"):
    return TheoremSpec(name, statement, dependencies, ("refl",), "syntax-only fixture, not a checked theorem")


def test_actual_pure_dependency_selector_preserves_owned_cross_and_parent_roles():
    parent = (syntax_row("syntax_parent"), syntax_row("unused_parent"))
    cross = syntax_row("syntax_cross", ("syntax_parent",))
    owned = syntax_row("syntax_owned", ("syntax_cross",))
    new = (cross, owned, syntax_row("unused_new"))
    selected = support.dependency_cone(parent, new, ("syntax_owned",))
    assert selected == (parent[0], cross, owned)
    roles = support.SupportSelection((owned,), (cross.name,), (parent[0].name,),
                                     (cross, owned), SimpleNamespace(), selected)
    assert roles.role(owned.name) == "new_owned_theorem"
    assert roles.role(cross.name) == "new_cross_track_support"
    assert roles.role(parent[0].name) == "inherited_alpha_v31"
    with pytest.raises(support.PolynomialDivisionError):
        roles.role("unused_parent")


@pytest.mark.parametrize("mode", ("missing", "forward", "self_cycle", "duplicate", "shadow_parent", "duplicate_edge", "foreign_owner", "duplicate_owner", "empty_owner", "list_owner", "list_parent", "list_new"))
def test_actual_pure_selector_rejects_malformed_ownership_and_topology(mode):
    parent = (syntax_row("syntax_parent"),)
    first, second = syntax_row("syntax_first", ("syntax_parent",)), syntax_row("syntax_second", ("syntax_first",))
    new, owners = (first, second), (second.name,)
    if mode == "missing": new = (replace(first, dependencies=("missing",)), second)
    elif mode == "forward": new = (replace(first, dependencies=(second.name,)), second)
    elif mode == "self_cycle": new = (first, replace(second, dependencies=(second.name,)))
    elif mode == "duplicate": new = (first, first)
    elif mode == "shadow_parent": new = (replace(first, name="syntax_parent"),)
    elif mode == "duplicate_edge": new = (replace(first, dependencies=("syntax_parent", "syntax_parent")), second)
    elif mode == "foreign_owner": owners = ("syntax_parent",)
    elif mode == "duplicate_owner": owners = (second.name, second.name)
    elif mode == "empty_owner": owners = ()
    elif mode == "list_owner": owners = [second.name]
    elif mode == "list_parent": parent = list(parent)
    elif mode == "list_new": new = list(new)
    with pytest.raises(support.PolynomialDivisionError):
        support.dependency_cone(parent, new, owners)


@pytest.mark.parametrize("mutation", ("statement", "dependencies", "script", "summary", "order"))
def test_exact_specification_digest_binds_every_semantic_and_script_field(actual_syntax, mutation):
    values = list(actual_syntax.rows)
    if mutation == "order": values[0], values[1] = values[1], values[0]
    else:
        row = values[0]
        changes = {"statement": "0=0", "dependencies": row.dependencies + ("unexpected_dependency",),
                   "script": row.script + ("refl",), "summary": row.summary + " changed"}
        values[0] = replace(row, **{mutation: changes[mutation]})
    assert support.closure._specs_digest(tuple(values)) != actual_syntax.specs_sha256


@pytest.mark.parametrize("bad", (None, 0, 1, "true", [], {}))
def test_source_loader_requires_an_exact_boolean_final_mode(bad):
    with pytest.raises(support.PolynomialDivisionError, match="Boolean"):
        support.load_candidate_state(final=bad)


@pytest.mark.parametrize("change", ("missing_family", "wrong_count", "duplicate_family"))
def test_actual_source_loader_rejects_partial_or_changed_source_inventory(monkeypatch, change):
    factories = support.FACTORIES
    if change == "missing_family": factories = factories[:-1]
    elif change == "wrong_count": factories = (replace(factories[0], count=factories[0].count - 1), *factories[1:])
    else: factories = (*factories[:-1], factories[0])
    monkeypatch.setattr(support, "FACTORIES", factories)
    with pytest.raises((support.PolynomialDivisionError, support.closure.BottomLayerClosureError)):
        support.load_candidate_state(final=False)


@pytest.mark.parametrize("entrypoint", ("inventory", "bundle", "principal", "binding", "all"))
def test_unregistered_final_artifact_fails_before_any_proof_work(monkeypatch, entrypoint):
    monkeypatch.setattr(checkpoints, "FINAL_ARTIFACT", None)
    monkeypatch.setattr(support, "select_support", reject)
    monkeypatch.setattr(driver, "run_worker", reject)
    call = {
        "inventory": checkpoints.require_final_inventory,
        "bundle": checkpoints.verify_checkpoint,
        "principal": lambda: checkpoints.verify_principal_root(PRINCIPALS[0]),
        "binding": driver.binding,
        "all": driver.verify_in_fresh_windows,
    }[entrypoint]
    with pytest.raises(support.PolynomialDivisionError, match="registered"):
        call()


@pytest.mark.parametrize("field,value", (
    ("bytes", 0), ("bytes", True), ("bytes", 64 * 1024 * 1024 + 1),
    ("nodes", 0), ("nodes", False), ("edges", 0), ("edges", -1),
    ("body_nodes", "17412"), ("body_nodes", 0),
    ("path", "/tmp/untrusted.json"), ("path", "../untrusted.json"),
    ("sha256", "F" * 64), ("sha256", "0" * 63),
))
def test_malformed_final_artifact_registration_is_fail_closed(monkeypatch, field, value):
    monkeypatch.setattr(checkpoints, "FINAL_ARTIFACT", replace(checkpoints.FINAL_ARTIFACT, **{field: value}))
    with pytest.raises(support.PolynomialDivisionError):
        checkpoints.require_final_inventory()


@pytest.mark.parametrize("name", (None, 0, True, "", "all", "unknown", "prime_field_polynomial_monic_leading_value"))
def test_only_the_six_exact_ordinary_principals_are_replayable(name):
    with pytest.raises(support.PolynomialDivisionError, match="principal"):
        checkpoints.verify_principal_root(name)
    with pytest.raises(support.PolynomialDivisionError, match="principal"):
        checkpoints.expected_root_report(None, None, name)


@pytest.mark.parametrize("count,cross", ((0, ()), (1, ()), (84, ()), (86, ()), (85, ("foreign_cross",))))
def test_partial_owned_inventory_never_reaches_the_whole_checker(count, cross):
    selected = SimpleNamespace(owned=(None,) * count, current_support=cross, plan=SimpleNamespace())
    with pytest.raises(support.PolynomialDivisionError, match="partial"):
        checkpoints._shape(None, selected, None, None)


def message_fixture(kind="bundle"):
    """Non-authorizing transport bytes, never a live checkpoint report."""
    expected = {"transport_only": True, "proofs_verified": False,
                "name": "syntax_only", "statement_sha256": "ef" * 32,
                "dependencies": ["syntax_parent"], "owned_count": 85}
    root = None
    if kind == "root":
        root = PRINCIPALS[2]
        expected["principal_roots"] = [{"name": root, "node_id": 17,
            "statement_sha256": "ef" * 32, "complete_ordinary_ha_checked": False}]
    report = deepcopy(expected)
    if kind == "root": report["principal_roots"][0]["ordinary_certificate_nodes"] = 42
    envelope = {"schema": driver.SCHEMA, "kind": kind, "slug": checkpoints.SLUG,
        "root": root, "nonce": NONCE, "binding_sha256": BINDING,
        "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024},
        "peak_rss_bytes": 42, "report": report}
    keywords = {"kind": kind, "root": root, "nonce": NONCE, "source_binding": BINDING, "expected": expected}
    return envelope, keywords


@pytest.mark.parametrize("kind", ("bundle", "novelty", "root"))
def test_exact_synthetic_protocol_message_preserves_its_explicit_non_authority(kind):
    envelope, keywords = message_fixture(kind)
    result, peak = driver.validate_message(driver.canonical_message(envelope), **keywords)
    assert result == envelope["report"] and peak == 42
    assert result["transport_only"] is True and result["proofs_verified"] is False
    if kind == "root": assert result["principal_roots"][0]["complete_ordinary_ha_checked"] is False


@pytest.mark.parametrize("field,value", (
    ("schema", "foreign"), ("kind", "foreign"), ("slug", "foreign"), ("root", PRINCIPALS[0]),
    ("nonce", ""), ("nonce", "AB" * 32), ("nonce", "ab" * 31), ("nonce", None), ("nonce", 0),
    ("binding_sha256", "ef" * 32), ("binding_sha256", True),
    ("peak_rss_bytes", 0), ("peak_rss_bytes", -1), ("peak_rss_bytes", True),
    ("peak_rss_bytes", "42"), ("peak_rss_bytes", 1536 * 1024 * 1024 + 1),
))
def test_foreign_nonce_binding_identity_or_rss_report_is_rejected(field, value):
    envelope, keywords = message_fixture()
    envelope[field] = value
    with pytest.raises((support.PolynomialDivisionError, driver.transport.AuditWorkerError)):
        driver.validate_message(driver.canonical_message(envelope), **keywords)


@pytest.mark.parametrize("field,value", (
    ("cpu", [171, 175]), ("cpu", [170, 176]), ("cpu", [True, 175]), ("cpu", [170]),
    ("wall_seconds", 181), ("wall_seconds", True),
    ("max_rss_bytes", 1536 * 1024 * 1024 + 1), ("max_rss_bytes", "1610612736"),
))
def test_worker_cannot_weaken_or_change_any_original_resource_limit(field, value):
    envelope, keywords = message_fixture()
    envelope["limits"][field] = value
    with pytest.raises(support.PolynomialDivisionError):
        driver.validate_message(driver.canonical_message(envelope), **keywords)


@pytest.mark.parametrize("field,value", (
    ("name", "other"), ("statement_sha256", "00" * 32), ("dependencies", []),
    ("dependencies", ["syntax_parent", "extra"]), ("owned_count", 84),
    ("owned_count", True), ("proofs_verified", True),
))
def test_worker_statement_dependencies_inventory_and_authority_bits_are_exact(field, value):
    envelope, keywords = message_fixture()
    envelope["report"][field] = value
    with pytest.raises(driver.transport.AuditWorkerError):
        driver.validate_message(driver.canonical_message(envelope), **keywords)


@pytest.mark.parametrize("action", ("missing_envelope_field", "extra_envelope_field", "missing_report_field", "extra_report_field"))
def test_worker_protocol_rejects_missing_or_extra_fields(action):
    envelope, keywords = message_fixture()
    if action == "missing_envelope_field": del envelope["root"]
    elif action == "extra_envelope_field": envelope["stored_receipt"] = {}
    elif action == "missing_report_field": del envelope["report"]["dependencies"]
    else: envelope["report"]["stored_success"] = True
    with pytest.raises((support.PolynomialDivisionError, driver.transport.AuditWorkerError)):
        driver.validate_message(driver.canonical_message(envelope), **keywords)


@pytest.mark.parametrize("payload", (None, "{}", b"", b"{}", b"{}\n", b"[]\n", b"null\n", b"\xff\n",
                                     b'{"a":1,"a":1}\n', b'{"a":NaN}\n', b'{"a":Infinity}\n', b" " * (128 * 1024 + 1)))
def test_noncanonical_duplicate_nonfinite_or_oversized_json_is_rejected(payload):
    _, keywords = message_fixture()
    with pytest.raises((support.PolynomialDivisionError, driver.transport.AuditWorkerError)):
        driver.validate_message(payload, **keywords)


@pytest.mark.parametrize("form", ("no_newline", "double_newline", "spaces", "duplicate_nonce"))
def test_even_equivalent_json_must_use_the_exact_unambiguous_wire_encoding(form):
    envelope, keywords = message_fixture()
    payload = driver.canonical_message(envelope)
    if form == "no_newline": payload = payload[:-1]
    elif form == "double_newline": payload += b"\n"
    elif form == "spaces": payload = json.dumps(envelope, sort_keys=True, indent=2).encode() + b"\n"
    else: payload = b'{"nonce":"' + NONCE.encode() + b'",' + payload[1:]
    with pytest.raises(driver.transport.AuditWorkerError):
        driver.validate_message(payload, **keywords)


@pytest.mark.parametrize("value", (None, 0, 1, True, "42", -1, 10**15))
def test_ordinary_certificate_size_is_a_strict_bounded_observation(value):
    envelope, keywords = message_fixture("root")
    envelope["report"]["principal_roots"][0]["ordinary_certificate_nodes"] = value
    with pytest.raises(driver.transport.AuditWorkerError):
        driver.validate_message(driver.canonical_message(envelope), **keywords)


@pytest.mark.parametrize("action", ("missing", "additional", "wrong_name", "wrong_statement", "wrong_node", "false_to_true"))
def test_principal_transport_needs_the_exact_root_inventory_and_identity(action):
    envelope, keywords = message_fixture("root")
    roots = envelope["report"]["principal_roots"]
    if action == "missing": roots.clear()
    elif action == "additional": roots.append(deepcopy(roots[0]))
    elif action == "wrong_name": roots[0]["name"] = PRINCIPALS[0]
    elif action == "wrong_statement": roots[0]["statement_sha256"] = "00" * 32
    elif action == "wrong_node": roots[0]["node_id"] += 1
    else: roots[0]["complete_ordinary_ha_checked"] = True
    with pytest.raises(driver.transport.AuditWorkerError):
        driver.validate_message(driver.canonical_message(envelope), **keywords)


@pytest.mark.parametrize("nonce,binding", (("", BINDING), (NONCE, ""), ("g" * 64, BINDING),
                                          (NONCE, "0" * 63), (None, BINDING)))
def test_bad_worker_invocation_rejects_before_binding_or_any_checker(monkeypatch, nonce, binding):
    events = []
    monkeypatch.setattr(driver, "resource", SimpleNamespace(RLIMIT_CPU=0, setrlimit=lambda kind, value: events.append((kind, value))))
    monkeypatch.setattr(driver, "signal", SimpleNamespace(alarm=lambda value: events.append(("alarm", value))))
    monkeypatch.setattr(driver, "binding", reject)
    monkeypatch.setattr(checkpoints, "verify_checkpoint", reject)
    monkeypatch.setattr(checkpoints, "verify_principal_root", reject)
    with pytest.raises(support.PolynomialDivisionError, match="nonce or binding"):
        driver.worker("bundle", None, nonce, binding)
    assert events == [(0, (170, 175)), ("alarm", 180)]


@pytest.mark.parametrize("collector", (0, 1, True, "receipt.json", {}, []))
def test_invalid_syntax_collector_is_rejected_before_any_live_work(monkeypatch, collector):
    monkeypatch.setattr(driver, "binding", reject)
    with pytest.raises(support.PolynomialDivisionError, match="callable"):
        driver.verify_in_fresh_windows(syntax_collector=collector)


@pytest.mark.parametrize("report", (None, {}, "{}", bytearray(b"{}")))
def test_one_way_syntax_transport_requires_immutable_bytes_before_calling_callback(report):
    with pytest.raises(support.PolynomialDivisionError, match="callback"):
        driver._collect_verified_syntax(reject, None, None, report, BINDING)


def test_callback_exception_propagates_and_cannot_be_converted_into_success(monkeypatch):
    monkeypatch.setattr(driver, "binding", lambda: pytest.fail("post-callback binding must not run after an exception"))
    with pytest.raises(Stopped):
        driver._collect_verified_syntax(reject, None, None, b"transport-only\n", BINDING)


def test_callback_return_value_cannot_replace_the_mandatory_post_binding(monkeypatch):
    seen = []
    payload = b"transport-only; no proof authority\n"
    def collector(state, selected, report):
        seen.append((state, selected, report))
        return {"pretend_success": True}
    monkeypatch.setattr(driver, "binding", reject)
    with pytest.raises(Stopped):
        driver._collect_verified_syntax(collector, None, None, payload, BINDING)
    assert seen == [(None, None, payload)]


@pytest.mark.parametrize("args", (
    ["--receipt", "saved.json"], ["--through", "1"], ["--seed-only"], ["--skip-lean"],
    ["--root", PRINCIPALS[0]], ["--nonce", NONCE], ["--binding", BINDING],
    ["--worker", "bundle"], ["--worker", "root", "--nonce", NONCE, "--binding", BINDING],
    ["--worker", "bundle", "--root", PRINCIPALS[0], "--nonce", NONCE, "--binding", BINDING],
))
def test_final_cli_has_no_receipt_partial_or_unbound_worker_acceptance(args, monkeypatch):
    monkeypatch.setattr(driver, "worker", reject)
    monkeypatch.setattr(driver, "verify_in_fresh_windows", reject)
    with pytest.raises(SystemExit) as caught:
        driver.main(args)
    assert caught.value.code == 2


@pytest.mark.parametrize("method,kwargs", ((driver.verify_in_fresh_windows, {"receipt": {"success": True}}),
                                           (checkpoints.verify_checkpoint, {"receipt": b"ACCEPT"}),
                                           (checkpoints.verify_checkpoint, {"through": 1})))
def test_public_final_apis_do_not_accept_stored_receipts_or_authoring_prefixes(method, kwargs):
    with pytest.raises(TypeError):
        method(**kwargs)


@pytest.mark.parametrize("options", ({"seed_only": 1}, {"seed_only": None}, {"seed_bundles": []}, {"seed_only": True}))
def test_authoring_seed_options_are_exact_and_seed_only_needs_real_explicit_data(options, monkeypatch):
    monkeypatch.setattr(support, "load_candidate_state", reject)
    with pytest.raises(support.PolynomialDivisionError, match="seed"):
        exporter.export_authoring_bundle(("syntax_only",), "ignored.json", **options)


@pytest.mark.parametrize("mode", ("outside", "existing", "symlink"))
def test_authoring_output_scope_and_no_overwrite_are_checked_before_any_proof_work(tmp_path, monkeypatch, mode):
    # Only disposable fixture paths are written; no repository artifact changes.
    root = tmp_path.resolve()
    allowed = root / "research/arithmetic-library/artifacts"
    allowed.mkdir(parents=True)
    destination = allowed / "draft.json"
    if mode == "outside": destination = root / "outside.json"
    elif mode == "existing": destination.write_bytes(b"owned fixture")
    else: destination.symlink_to(root / "missing-target.json")
    monkeypatch.setattr(support, "ROOT", root)
    monkeypatch.setattr(support, "load_candidate_state", reject)
    with pytest.raises(support.PolynomialDivisionError):
        exporter.export_authoring_bundle(("syntax_only",), destination)
    if mode == "existing": assert destination.read_bytes() == b"owned fixture"
    elif mode == "symlink": assert destination.is_symlink()
    else: assert not destination.exists()


def call_names(function):
    tree = ast.parse(inspect.getsource(function))
    return [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]


def test_final_success_path_contains_all_actual_original_checkers_and_no_receipt_loader():
    assert "support.closure.check_bottom_layer_bundle" in call_names(checkpoints._shape)
    assert "_shape" in call_names(checkpoints.verify_checkpoint)
    assert "independent._lean_check" in call_names(checkpoints.verify_checkpoint)
    roots = call_names(checkpoints.verify_principal_root)
    assert "support.closure.replay_bottom_layer_theorem" in roots and "check" in roots and "_closed_formula" in roots
    verify = inspect.getsource(driver.verify_in_fresh_windows)
    assert "run_worker('novelty'" in verify and "run_worker('bundle'" in verify
    assert "for name in checkpoints.PRINCIPAL_ROOTS" in verify and "run_worker('root'" in verify
    assert verify.index("run_worker('root'") < verify.index("if binding() != source_binding") < verify.index("_collect_verified_syntax(")
    assert "return result" in verify and "receipt" not in inspect.signature(driver.verify_in_fresh_windows).parameters


def test_source_binding_covers_new_controls_prior_providers_math_and_exact_binary():
    source = inspect.getsource(support.state_binding)
    assert "inherited.state_binding(state,final=False)" in source
    for path in ("constructive_polynomial_division_support.py", "export_constructive_polynomial_division.py",
                 "constructive_polynomial_division_checkpoints.py", "check_constructive_polynomial_division.py"):
        assert repr(path) in source
    for key in ("sources", "specs_sha256", "factories", "frozen_math_pins", "frozen_specs_sha256", "prior_research_count"):
        assert repr(key) in source
    binding = inspect.getsource(driver.binding)
    assert "independent._check_lean_binary()" in binding
    assert "support.state_binding(state,final=True)" in binding
    assert "pin.body_nodes" in binding and "PRINCIPAL_ROOTS" in binding
    novelty = inspect.getsource(support.statement_duplicates)
    assert "inherited.statement_duplicates(new_rows)" in novelty
    assert "inherited.all_new_rows(final=True)" in novelty


def test_all_original_worker_proof_transport_and_scheduler_limits_are_preserved():
    assert driver.CPU_LIMITS == exporter.CPU_LIMITS == (170, 175)
    assert driver.WALL_SECONDS == exporter.WALL_SECONDS == 180
    assert driver.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert driver.PARENT_TIMEOUT_SECONDS == 185
    assert driver.MAX_STDOUT_BYTES == 128 * 1024 and driver.MAX_STDERR_BYTES == 8 * 1024
    assert driver.CONTROLLER_WALL_SECONDS == 8 * 185 + 180 == 1660
    assert driver.canonical_message is driver.transport._canonical
    run = inspect.getsource(driver.run_worker)
    assert "transport._capture_bounded(command,environment)" in run
    assert "PYTHONMALLOC='pymalloc'" in run
    assert "secrets.token_hex(32)" in run
    assert "resource.setrlimit(resource.RLIMIT_CPU,CPU_LIMITS)" in inspect.getsource(driver.worker)
    assert "signal.alarm(WALL_SECONDS)" in inspect.getsource(driver.worker)
    assert "checkpoints.peak_rss_bytes()" in inspect.getsource(driver.worker)


def test_authoring_checks_the_real_complete_bundle_and_never_claims_final_admission():
    source = inspect.getsource(exporter.export_authoring_bundle)
    assert "closure.assemble_bottom_layer_bundle" in source and "seed_bundles=" in source
    assert "support.parent_seed_paths()" in source
    assert source.index("support.state_binding(final_state)") < source.index("destination.open('xb')")
    assert source.count("authoring_rss_bytes()") >= 4
    for key in ("independent_lean_checked", "final_complete_inventory_acceptance", "alpha_admission_performed", "stable_admission_performed"):
        assert repr(key) + ":False" in source
    assert "'draft_proof_data_only':True" in source
