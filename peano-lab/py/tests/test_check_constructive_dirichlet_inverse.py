"""Bounded audit protocol tests, with one genuinely checked family worker.

Protocol fixtures below test transport and exact metadata only; they confer no
proof status. The positive live-worker fixture runs the original complete HA,
the actual pinned Lean binary and all three dirichlet-signed-units empty-context roots. No proof
checker is replaced by a mocked accepting implementation.
"""

from copy import deepcopy
from dataclasses import fields, replace
from hashlib import sha256
import ast
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import check_constructive_dirichlet_inverse as cli


NONCE = "1" * 64
BINDING = "2" * 64


def _transport_family_metadata(item, *, with_selection=False):
    """Scheduler protocol data only: no HA or Lean acceptance is asserted."""
    report = {
        "transport_only": True, "slug": item.slug, "bundle": {"sha256": "0" * 64},
        "principal_roots": [{"name": name, "complete_ordinary_ha_checked": False}
                            for name in item.principal_roots],
    }
    selection = SimpleNamespace(transport_only=True, slug=item.slug)
    return (report, selection) if with_selection else report


@pytest.fixture(scope="module")
def metadata():
    return cli._expected_family_report(cli.checkpoints.CHECKPOINTS[0])


def _message(metadata):
    report = deepcopy(metadata)
    return {
        "schema": cli.WORKER_SCHEMA, "kind": "family", "slug": "dirichlet-signed-units",
        "nonce": NONCE, "binding_sha256": BINDING,
        "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024},
        "peak_rss_bytes": 100, "report": report,
    }


def _validate(payload, metadata):
    return cli._validate_message(payload, kind="family", slug="dirichlet-signed-units",
                                 nonce=NONCE, binding=BINDING, expected=metadata)


def test_exact_protocol_shape_does_not_change_report(metadata):
    envelope = _message(metadata)
    report, peak = _validate(cli._canonical(envelope), metadata)
    assert report == envelope["report"] and peak == 100
    assert cli.MAX_STDOUT_BYTES == 128 * 1024
    assert cli.MAX_STDERR_BYTES == 8 * 1024
    assert cli.CPU_LIMITS == (170, 175) and cli.WALL_SECONDS == 180
    assert cli.PARENT_TIMEOUT_SECONDS == 185
    assert cli.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert cli.ORDINARY_ROOTS_PER_FAMILY == 3
    assert cli.CONTROLLER_WALL_SECONDS == 13 * 185 + 180


@pytest.mark.parametrize("path,value", (
    (("nonce",), "3" * 64), (("binding_sha256",), "4" * 64),
    (("kind",), "novelty"), (("slug",), "dirichlet-inverses"), (("schema",), "old"),
    (("limits", "cpu"), [171, 175]), (("limits", "wall_seconds"), 181),
    (("limits", "max_rss_bytes"), 2**31), (("peak_rss_bytes",), 2**31),
    (("peak_rss_bytes",), True), (("peak_rss_bytes",), 0),
    (("report", "slug"), "dirichlet-inverses"),
    (("report", "new_theorem_count"), 13),
    (("report", "new_specs_sha256"), "0" * 64),
    (("report", "complete_non_alpha_specs_sha256"), "0" * 64),
    (("report", "sources", 0, "sha256"), "0" * 64),
    (("report", "sources", 0, "factory"), "other_factory"),
    (("report", "support", "alpha_v30_count"), 0),
    (("report", "support", "prior_lower_continuation_count"), -1),
    (("report", "support", "prior_dirichlet_count"), -1),
    (("report", "support", "prior_dirichlet_theorems"), ["foreign-prior-dirichlet-theorem"]),
    (("report", "support", "local_non_admitted_count"), -1),
    (("report", "support", "prior_lower_continuation_theorems"), ["not-a-real-prerequisite"]),
    (("report", "support", "counted_as_new_owned_theorems"), True),
    (("report", "bundle", "sha256"), "0" * 64),
    (("report", "bundle", "body_proof_nodes"), 1),
    (("report", "bundle", "original_ha_checked"), False),
    (("report", "bundle", "independent_lean_checked"), False),
    (("report", "admitted_to_alpha"), True),
    (("report", "stable_member"), True),
    (("report", "principal_roots", 0, "name"), "other_theorem"),
    (("report", "principal_roots", 0, "node_id"), 0),
    (("report", "principal_roots", 0, "statement_sha256"), "0" * 64),
    (("report", "principal_roots", 0, "complete_ordinary_ha_checked"), True),
    (("report", "principal_roots", 0, "complete_ordinary_ha_checked"), 1),
    (("report", "principal_roots", 0, "ordinary_certificate_nodes"), True),
    (("report", "principal_roots", 0, "ordinary_certificate_nodes"), 1),
    (("report", "principal_roots", 0, "ordinary_certificate_nodes"), 500001),
))
def test_stale_foreign_relabelled_or_incomplete_worker_reports_fail_closed(metadata, path, value):
    message = _message(metadata)
    target = message
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(cli.AuditWorkerError):
        _validate(cli._canonical(message), metadata)


@pytest.mark.parametrize("mutation", ("missing_envelope", "extra_envelope", "missing_root", "extra_root", "reordered_roots", "extra_report"))
def test_missing_additional_or_reordered_protocol_fields_rejected(metadata, mutation):
    message = _message(metadata)
    if mutation == "missing_envelope": del message["limits"]
    elif mutation == "extra_envelope": message["accepted_from_saved_receipt"] = True
    elif mutation == "missing_root": message["report"]["principal_roots"].pop()
    elif mutation == "extra_root": message["report"]["principal_roots"].append(deepcopy(message["report"]["principal_roots"][0]))
    elif mutation == "reordered_roots": message["report"]["principal_roots"].reverse()
    else: message["report"]["other_authority"] = True
    with pytest.raises(cli.AuditWorkerError):
        _validate(cli._canonical(message), metadata)


@pytest.mark.parametrize("change", (None, "duplicates", "new_theorems", "prior_theorems",
                                   "ordered_specs_sha256", "exact_ast_novelty_checked"))
def test_whole_tranche_novelty_result_is_exact_and_cannot_skip_prior_generations(change):
    expected = cli._expected_novelty_report()
    message = {
        "schema": cli.WORKER_SCHEMA, "kind": "novelty", "slug": "all",
        "nonce": NONCE, "binding_sha256": BINDING,
        "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024},
        "peak_rss_bytes": 100, "report": deepcopy(expected),
    }
    if change is not None:
        message["report"][change] = {
            "duplicates": [["new_name", "old_name"]], "new_theorems": 39,
            "prior_theorems": 3643, "ordered_specs_sha256": "0" * 64,
            "exact_ast_novelty_checked": False,
        }[change]
    arguments = dict(kind="novelty", slug="all", nonce=NONCE, binding=BINDING, expected=expected)
    if change is None:
        assert cli._validate_message(cli._canonical(message), **arguments) == (expected, 100)
    else:
        with pytest.raises(cli.AuditWorkerError):
            cli._validate_message(cli._canonical(message), **arguments)


@pytest.mark.parametrize("payload", (
    b"", b"{}\r\n", b"{}", b"[]\n", b"\xff\n", b'{"a":1,"a":2}\n',
    b'{"a":NaN}\n', b'{"a":Infinity}\n', b'{"a":-Infinity}\n',
    b"{}\n{}\n", b"banner\n{}\n", b" " + b"x" * (128 * 1024),
))
def test_worker_json_is_strict_canonical_duplicate_free_and_byte_bounded(payload):
    with pytest.raises(cli.AuditWorkerError):
        cli._decode_message(payload)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "reordered", "wrong_count", "foreign"))
def test_exact_registry_guard_rejects_before_loading_any_rows(monkeypatch, mutation):
    items = cli.checkpoints.CHECKPOINTS
    if mutation == "missing": changed = items[:-1]
    elif mutation == "duplicate": changed = (*items, items[0])
    elif mutation == "reordered": changed = tuple(reversed(items))
    elif mutation == "wrong_count": changed = (replace(items[0], frontier_count=13), *items[1:])
    else: changed = (replace(items[0], slug="foreign"), *items[1:])
    monkeypatch.setattr(cli.checkpoints, "CHECKPOINTS", changed)
    def forbidden():
        raise AssertionError("invalid registry reached source loading")
    monkeypatch.setattr(cli.checkpoints, "all_new_rows", forbidden)
    with pytest.raises(cli.AuditWorkerError, match="inventory"):
        cli._inventory()


def test_actual_source_and_cached_factory_output_are_authenticated(monkeypatch):
    item = cli.checkpoints.CHECKPOINTS[0]
    original = cli.checkpoints.load_rows(item)
    module = sys.modules["peano_lab.library." + item.modules[0].module]
    monkeypatch.setattr(module, item.modules[0].factory,
                        lambda _: (replace(original[0], script=("refl",)), *original[1:]))
    with pytest.raises(cli.checkpoints.CheckpointError, match="specifications"):
        cli._binding()


def test_actual_parent_digest_is_rechecked_even_if_snapshot_was_cached(monkeypatch):
    cli.checkpoints.closure.parent_snapshot()
    monkeypatch.setattr(cli.checkpoints.closure, "PARENT_CATALOG_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="bytes changed"):
        cli._binding()


def test_real_bounded_pipe_transport_accepts_only_clean_success():
    command = [sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'{}\\n')"]
    assert cli._capture_bounded(command, os.environ.copy(), timeout=5) == b"{}\n"


@pytest.mark.parametrize("program,match", (
    ("import sys;sys.exit(7)", "status 7"),
    ("import os,signal;os.kill(os.getpid(),signal.SIGTERM)", "status"),
    ("import sys;sys.stderr.write('warning')", "status 0"),
    ("import sys;sys.stdout.buffer.write(b'x'*131073)", "byte bound"),
    ("import sys;sys.stderr.buffer.write(b'x'*8193)", "byte bound"),
))
def test_real_nonzero_signal_and_oversized_pipe_processes_are_rejected(program, match):
    with pytest.raises(cli.AuditWorkerError, match=match):
        cli._capture_bounded([sys.executable, "-c", program], os.environ.copy(), timeout=5)


def test_real_timeout_is_terminated_without_reading_unbounded_output():
    with pytest.raises(cli.AuditWorkerError, match="timeout"):
        cli._capture_bounded([sys.executable, "-c", "import time;time.sleep(2)"],
                             os.environ.copy(), timeout=0.1)


def test_worker_command_is_exact_shell_free_and_pinned_to_this_workspace(metadata, monkeypatch):
    monkeypatch.setattr(cli.secrets, "token_hex", lambda count: NONCE if count == 32 else None)
    observed = []
    def transport(command, environment):
        observed.append((command, environment))
        return cli._canonical(_message(metadata))
    monkeypatch.setattr(cli, "_capture_bounded", transport)
    cli._run_worker("family", "dirichlet-signed-units", BINDING, metadata)
    command, environment = observed[0]
    assert command == [sys.executable, str(cli.SCRIPT), "--worker", "family", "--slug",
                       "dirichlet-signed-units", "--nonce", NONCE, "--binding", BINDING]
    assert environment["PYTHONPATH"] == os.pathsep.join((str(ROOT/"peano-lab/py"), str(ROOT/"scripts")))
    assert environment["PYTHONMALLOC"] == "malloc" and environment["PYTHONNOUSERSITE"] == "1"


def test_fresh_jobs_are_sequential_and_every_family_required_before_aggregation(monkeypatch):
    observed = []
    monkeypatch.setattr(cli, "_binding", lambda: BINDING)
    monkeypatch.setattr(cli, "_expected_novelty_report", lambda: {})
    monkeypatch.setattr(cli, "_expected_family_report", _transport_family_metadata)
    def worker(kind, slug, binding, expected, *, root=None):
        observed.append((kind, slug, root))
        if kind == "family" and slug == "dirichlet-inverses":
            raise cli.AuditWorkerError("deliberate worker failure")
        return expected, 1
    def aggregate(_):
        raise AssertionError("failed worker reached success aggregation")
    monkeypatch.setattr(cli, "_run_worker", worker)
    monkeypatch.setattr(cli.checkpoints, "_aggregate_reports", aggregate)
    with pytest.raises(cli.AuditWorkerError, match="deliberate"):
        cli.verify_in_fresh_windows()
    wanted=[("novelty","all",None)]
    for item in cli.checkpoints.CHECKPOINTS[:2]:
        wanted.append(("family",item.slug,None))
        wanted.extend(("root",item.slug,name) for name in item.principal_roots)
    wanted.append(("family","dirichlet-inverses",None))
    assert observed == wanted


@pytest.mark.parametrize("arguments", (
    ("--worker", "family", "--write"), ("--worker", "novelty", "--check"),
    ("--slug", "dirichlet-signed-units"), ("--nonce", NONCE), ("--binding", BINDING),
    ("--worker", "family"), ("--check", "--write"),
    ("--root", "some_theorem"), ("--worker", "root", "--write"),
    ("--worker", "root", "--slug", "dirichlet-signed-units", "--nonce", NONCE, "--binding", BINDING),
    ("--worker", "family", "--slug", "dirichlet-signed-units", "--nonce", NONCE, "--binding", BINDING, "--root", "some_theorem"),
))
def test_private_workers_cannot_read_write_or_impersonate_complete_audits(arguments):
    with pytest.raises(SystemExit) as error:
        cli.main(list(arguments))
    assert error.value.code == 2


@pytest.mark.parametrize("mode", ("--check", "--write"))
def test_failure_prevents_receipt_read_or_write_even_when_old_success_file_exists(tmp_path, monkeypatch, mode):
    receipt = tmp_path/"audit.json"
    if mode == "--check": receipt.write_bytes(b"old success is not authority\n")
    monkeypatch.setattr(cli, "RECEIPT", receipt)
    monkeypatch.setattr(cli.resource, "setrlimit", lambda *_: None)
    monkeypatch.setattr(cli.signal, "alarm", lambda *_: None)
    def reject():
        raise cli.AuditWorkerError("fresh checks failed")
    monkeypatch.setattr(cli, "verify_in_fresh_windows", reject)
    def forbidden(*_):
        raise AssertionError("failed proofs reached saved-receipt comparison")
    monkeypatch.setattr(cli, "check_receipt_bytes", forbidden)
    with pytest.raises(cli.AuditWorkerError, match="fresh checks"):
        cli.main([mode])
    assert receipt.read_bytes() == b"old success is not authority\n" if mode == "--check" else not receipt.exists()


def test_worker_and_controller_limits_and_exclusive_write_are_explicit():
    tree = ast.parse(cli.SCRIPT.read_text())
    worker = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_worker")
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    worker_text = ast.unparse(worker)
    assert "resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)" in worker_text
    assert "signal.alarm(WALL_SECONDS)" in worker_text
    assert "ordinary_roots=False" in worker_text
    assert "checkpoints.verify_principal_root(selected[0], root)" in worker_text
    assert worker_text.count("_binding()") == 2
    assert "statement_duplicates(_inventory())" in worker_text
    main_text = ast.unparse(main)
    assert "signal.alarm(CONTROLLER_WALL_SECONDS)" in main_text
    assert "RECEIPT.open('x', encoding='utf-8')" in main_text
    assert main_text.index("verify_in_fresh_windows()") < main_text.index("check_receipt_bytes(")
    assert main_text.count("authoring_rss_bytes()") == 2


def test_original_proof_verifier_function_is_byte_identical_to_reviewed_baseline():
    path = ROOT/"scripts/constructive_lower_continuation_checkpoints.py"
    source = path.read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "verify_checkpoint")
    assert sha256(ast.get_source_segment(source, node).encode()).hexdigest() == (
        "735571e190a7b88678294f3208ecab84d83375b855e994b8e404f0b276a1267c"
    )


def test_actual_fresh_family_worker_checks_complete_ha_and_real_lean(metadata):
    before = cli.RECEIPT.read_bytes() if cli.RECEIPT.exists() else None
    binding = cli._binding()
    report, peak = cli._run_worker("family", "dirichlet-signed-units", binding, metadata)
    assert report["new_theorem_count"] == 9
    assert report["bundle"]["original_ha_checked"] is report["bundle"]["independent_lean_checked"] is True
    assert [row["name"] for row in report["principal_roots"]] == list(cli.checkpoints.CHECKPOINTS[0].principal_roots)
    assert all(row["complete_ordinary_ha_checked"] is False and "ordinary_certificate_nodes" not in row
               for row in report["principal_roots"])
    assert 0 < peak <= 1536 * 1024 * 1024
    after = cli.RECEIPT.read_bytes() if cli.RECEIPT.exists() else None
    assert after == before, "a family worker must neither create nor change the final audit"


@pytest.mark.parametrize("name",cli.checkpoints.CHECKPOINTS[0].principal_roots)
def test_actual_fresh_ordinary_worker_checks_one_exact_principal(metadata,name):
    before=cli.RECEIPT.read_bytes() if cli.RECEIPT.exists() else None
    binding=cli._binding()
    expected=cli._expected_root_report(metadata,name)
    checked,peak=cli._run_worker("root","dirichlet-signed-units",binding,expected,root=name)
    assert checked["bundle_sha256"]==metadata["bundle"]["sha256"]
    assert checked["principal_roots"][0]["name"]==name
    assert checked["principal_roots"][0]["complete_ordinary_ha_checked"] is True
    assert checked["principal_roots"][0]["ordinary_certificate_nodes"]>1
    assert 0<peak<=1536*1024*1024
    after=cli.RECEIPT.read_bytes() if cli.RECEIPT.exists() else None
    assert after==before,"an ordinary-root worker must neither create nor change the final audit"


def test_pure_transport_helpers_are_reused_without_patching_historical_globals():
    assert cli._capture_bounded is cli.transport._capture_bounded
    assert cli._decode_message is cli.transport._decode_message
    assert cli._validate_report is cli.transport._validate_report
    assert cli.transport.SCRIPT != cli.SCRIPT
    assert cli.transport.WORKER_SCHEMA != cli.WORKER_SCHEMA
    assert cli.transport.EXPECTED_INVENTORY == (("divisor-involutions",12),("mobius-divisor-cancellation",28),("rectangular-sums",32),("polynomial-products",53))


def _root_message(metadata):
    name=metadata["principal_roots"][0]["name"]
    expected=cli._expected_root_report(metadata,name)
    message=_message(metadata)
    message["kind"]="root"
    message["report"]=deepcopy(expected)
    # A bounded count is only protocol test data, never proof authority.
    message["report"]["principal_roots"][0]["ordinary_certificate_nodes"]=10
    return message,expected


@pytest.mark.parametrize("path,value",(
    (("slug",),"dirichlet-triangular"),(("bundle_sha256",),"0"*64),
    (("principal_roots",0,"name"),"other_theorem"),
    (("principal_roots",0,"node_id"),0),
    (("principal_roots",0,"statement_sha256"),"0"*64),
    (("principal_roots",0,"complete_ordinary_ha_checked"),False),
    (("principal_roots",0,"ordinary_certificate_nodes"),True),
    (("principal_roots",0,"ordinary_certificate_nodes"),1),
    (("principal_roots",0,"ordinary_certificate_nodes"),500001),
))
def test_principal_messages_are_bound_to_exact_family_bundle_and_statement(metadata,path,value):
    message,expected=_root_message(metadata)
    target=message["report"]
    for key in path[:-1]:target=target[key]
    target[path[-1]]=value
    with pytest.raises(cli.AuditWorkerError):
        cli._validate_message(cli._canonical(message),kind="root",slug="dirichlet-signed-units",nonce=NONCE,binding=BINDING,expected=expected)


def test_exact_root_protocol_cannot_be_misread_as_family_evidence(metadata):
    message,expected=_root_message(metadata)
    assert cli._validate_message(cli._canonical(message),kind="root",slug="dirichlet-signed-units",nonce=NONCE,binding=BINDING,expected=expected)==(message["report"],100)
    with pytest.raises(cli.AuditWorkerError):
        _validate(cli._canonical(message),metadata)


def test_root_worker_command_contains_the_exact_registered_principal(metadata,monkeypatch):
    message,expected=_root_message(metadata)
    name=expected["principal_roots"][0]["name"]
    monkeypatch.setattr(cli.secrets,"token_hex",lambda count:NONCE if count==32 else None)
    observed=[]
    def capture(command,environment):
        observed.append(command)
        return cli._canonical(message)
    monkeypatch.setattr(cli,"_capture_bounded",capture)
    cli._run_worker("root","dirichlet-signed-units",BINDING,expected,root=name)
    assert observed==[[sys.executable,str(cli.SCRIPT),"--worker","root","--slug","dirichlet-signed-units",
                      "--nonce",NONCE,"--binding",BINDING,"--root",name]]


def test_one_missing_root_prevents_any_aggregate_success(monkeypatch):
    monkeypatch.setattr(cli,"_binding",lambda:BINDING)
    monkeypatch.setattr(cli,"_expected_novelty_report",lambda:{})
    monkeypatch.setattr(cli,"_expected_family_report",_transport_family_metadata)
    first=cli.checkpoints.CHECKPOINTS[0]
    calls=[]
    def worker(kind,slug,binding,expected,*,root=None):
        calls.append((kind,slug,root))
        if root==first.principal_roots[1]:raise cli.AuditWorkerError("required ordinary root rejected")
        return expected,1
    monkeypatch.setattr(cli,"_run_worker",worker)
    monkeypatch.setattr(cli.checkpoints,"_aggregate_reports",lambda _:pytest.fail("missing root reached aggregate"))
    with pytest.raises(cli.AuditWorkerError,match="required ordinary"):
        cli.verify_in_fresh_windows()
    assert calls[-1]==("root",first.slug,first.principal_roots[1])


def test_retained_selection_is_only_source_syntax_and_default_metadata_is_unchanged(metadata):
    checkpoint = cli.checkpoints.CHECKPOINTS[0]
    report, selection = cli._expected_family_report(checkpoint, with_selection=True)
    assert cli._canonical(report) == cli._canonical(metadata)
    assert type(selection) is cli.support.SupportSelection
    assert {field.name for field in fields(selection)} == {
        "owned", "frontier", "bottom_support", "lower_support", "continuation_support",
        "dirichlet_support", "current_support", "plan",
    }
    assert tuple(row.name for row in selection.owned) == tuple(
        row.name for row in cli.checkpoints.load_rows(checkpoint))
    assert selection.plan.frontier_specs_sha256 == metadata["complete_non_alpha_specs_sha256"]
    assert list(selection.plan.root_names) == metadata["all_maximal_owned_roots"]
    syntax_types = (
        cli.support.SupportSelection, cli.support.TheoremSpec,
        cli.checkpoints.closure.BottomLayerPlan, cli.checkpoints.closure.BottomLayerRow,
    )

    def syntax_only(value):
        if type(value) in (str, int, bool, type(None)):
            return
        if type(value) is tuple:
            for item in value:
                syntax_only(item)
            return
        assert type(value) in syntax_types, "retained syntax contains a proof, receipt, or opaque object"
        for field in fields(value):
            syntax_only(getattr(value, field.name))

    syntax_only(selection)
    assert all(row["complete_ordinary_ha_checked"] is False for row in report["principal_roots"])


@pytest.mark.parametrize("flag", (None, 0, 1, "true", (), []))
def test_selection_flag_is_strict_boolean_before_any_source_read(monkeypatch, flag):
    monkeypatch.setattr(cli, "_inventory", lambda: pytest.fail("invalid flag read sources"))
    with pytest.raises(cli.AuditWorkerError, match="Boolean"):
        cli._expected_family_report(cli.checkpoints.CHECKPOINTS[0], with_selection=flag)


@pytest.mark.parametrize("collector", (False, True, 0, "callback", (), [], {}))
def test_noncallable_syntax_collector_is_rejected_before_binding(monkeypatch, collector):
    monkeypatch.setattr(cli, "_binding", lambda: pytest.fail("invalid collector read source bindings"))
    with pytest.raises(cli.AuditWorkerError, match="callable"):
        cli.verify_in_fresh_windows(syntax_collector=collector)


@pytest.fixture
def collector_protocol(monkeypatch):
    """Exercise scheduling only, without mocking a proof checker to accept.

    The returned aggregate is deliberately labelled NOT proof-verified and is
    never passed to rendering, a receipt writer, or an admission interface.
    """
    state = SimpleNamespace(events=[], workers=[], selections={}, metadata={})

    def binding():
        state.events.append(("binding",))
        return BINDING

    def expected(item, *, with_selection=False):
        report, selected = _transport_family_metadata(item, with_selection=True)
        state.events.append(("metadata", item.slug, with_selection))
        state.metadata[item.slug] = deepcopy(report)
        state.selections[item.slug] = selected
        return (report, selected) if with_selection else report

    def worker(kind, slug, binding, expected, *, root=None):
        assert binding == BINDING
        state.events.append(("worker", kind, slug, root))
        state.workers.append((kind, slug, root))
        return deepcopy(expected), 100

    def aggregate(reports):
        state.events.append(("aggregate",))
        assert [report["slug"] for report in reports] == [item.slug for item in cli.checkpoints.CHECKPOINTS]
        return {"transport_only": True, "proofs_verified": False}

    def rss():
        state.events.append(("rss",))
        return 100

    monkeypatch.setattr(cli, "_binding", binding)
    monkeypatch.setattr(cli, "_expected_novelty_report", lambda: {"transport_only": True})
    monkeypatch.setattr(cli, "_expected_family_report", expected)
    monkeypatch.setattr(cli, "_run_worker", worker)
    monkeypatch.setattr(cli.checkpoints, "_aggregate_reports", aggregate)
    monkeypatch.setattr(cli, "authoring_rss_bytes", rss)
    return state


def test_collector_receives_immutable_syntax_metadata_only_after_all_fresh_gates(collector_protocol):
    state = collector_protocol
    collected = []

    def collect(checkpoint, selection, expected_bytes):
        state.events.append(("collect", checkpoint.slug))
        assert len(state.workers) == 13
        assert ("aggregate",) in state.events
        assert state.events[-2] == ("rss",) if not collected else state.events[-2][0] == "collect"
        assert type(expected_bytes) is bytes
        assert json.loads(expected_bytes) == state.metadata[checkpoint.slug]
        assert expected_bytes == cli._canonical(state.metadata[checkpoint.slug])
        assert selection is state.selections[checkpoint.slug]
        collected.append(checkpoint.slug)

    result, peak = cli.verify_in_fresh_windows(syntax_collector=collect)
    assert result == {"transport_only": True, "proofs_verified": False} and peak == 100
    assert collected == [item.slug for item in cli.checkpoints.CHECKPOINTS]
    wanted = [("novelty", "all", None)]
    for item in cli.checkpoints.CHECKPOINTS:
        wanted.append(("family", item.slug, None))
        wanted.extend(("root", item.slug, name) for name in item.principal_roots)
    assert state.workers == wanted
    assert state.events.count(("binding",)) == 2
    assert state.events[-1] == ("rss",)
    assert all(event[2] is True for event in state.events if event[0] == "metadata")


def test_absent_collector_preserves_the_original_nonretaining_scheduler(collector_protocol):
    result, peak = cli.verify_in_fresh_windows()
    assert result == {"transport_only": True, "proofs_verified": False} and peak == 100
    assert len(collector_protocol.workers) == 13
    assert all(event[2] is False for event in collector_protocol.events if event[0] == "metadata")
    assert not any(event[0] == "collect" for event in collector_protocol.events)


@pytest.mark.parametrize("failed_job", range(13))
def test_no_collector_callback_after_any_failed_fresh_worker(collector_protocol, monkeypatch, failed_job):
    original = cli._run_worker
    callbacks = []

    def reject(kind, slug, binding, expected, *, root=None):
        if len(collector_protocol.workers) == failed_job:
            raise cli.AuditWorkerError("deliberate fresh job rejection")
        return original(kind, slug, binding, expected, root=root)

    monkeypatch.setattr(cli, "_run_worker", reject)
    with pytest.raises(cli.AuditWorkerError, match="fresh job rejection"):
        cli.verify_in_fresh_windows(syntax_collector=lambda *args: callbacks.append(args))
    assert callbacks == []
    assert ("aggregate",) not in collector_protocol.events


@pytest.mark.parametrize("gate", ("initial_binding", "metadata", "final_binding", "aggregate", "rss"))
def test_no_collector_callback_after_binding_metadata_aggregate_or_resource_failure(collector_protocol, monkeypatch, gate):
    callbacks = []

    def rejected(*args, **kwargs):
        raise cli.AuditWorkerError("deliberate " + gate + " rejection")

    if gate == "initial_binding":
        monkeypatch.setattr(cli, "_binding", rejected)
    elif gate == "metadata":
        monkeypatch.setattr(cli, "_expected_family_report", rejected)
    elif gate == "final_binding":
        bindings = iter((BINDING, "f" * 64))
        monkeypatch.setattr(cli, "_binding", lambda: next(bindings))
    elif gate == "aggregate":
        monkeypatch.setattr(cli.checkpoints, "_aggregate_reports", rejected)
    else:
        monkeypatch.setattr(cli, "authoring_rss_bytes", rejected)
    with pytest.raises(cli.AuditWorkerError):
        cli.verify_in_fresh_windows(syntax_collector=lambda *args: callbacks.append(args))
    assert callbacks == []


@pytest.mark.parametrize("failed_callback", (0, 1, 2))
def test_collector_exception_propagates_without_returning_a_success(collector_protocol, failed_callback):
    callbacks = []

    def collect(checkpoint, *unused):
        callbacks.append(checkpoint.slug)
        if len(callbacks) == failed_callback + 1:
            raise RuntimeError("deliberate syntax consumer rejection")

    with pytest.raises(RuntimeError, match="syntax consumer rejection"):
        cli.verify_in_fresh_windows(syntax_collector=collect)
    assert len(collector_protocol.workers) == 13
    assert callbacks == [item.slug for item in cli.checkpoints.CHECKPOINTS[:failed_callback + 1]]


def test_post_collector_rss_failure_cannot_return_an_aggregate(collector_protocol, monkeypatch):
    calls = []
    callbacks = []

    def rss():
        calls.append(None)
        if len(calls) == 2:
            raise cli.AuditWorkerError("post-collector RSS rejection")
        return 100

    monkeypatch.setattr(cli, "authoring_rss_bytes", rss)
    with pytest.raises(cli.AuditWorkerError, match="post-collector RSS"):
        cli.verify_in_fresh_windows(syntax_collector=lambda *args: callbacks.append(args))
    assert len(callbacks) == 3 and len(calls) == 2


def test_four_exact_historical_generations_and_all_sixteen_seeds_are_bound():
    generations = (cli.prior_bottom.CHECKPOINTS, cli.prior_lower.CHECKPOINTS,
                   cli.prior_continuation.CHECKPOINTS, cli.prior_dirichlet.CHECKPOINTS)
    assert [sum(item.frontier_count for item in rows) for rows in generations] == [170, 126, 125, 113]
    assert cli._prior_checkpoints() == tuple(item for rows in generations for item in rows)
    assert len(cli._prior_checkpoints()) == 16
    assert len(cli.support.previous_rows()) == 534
    assert len({item.artifact for item in cli._prior_checkpoints()}) == 16


@pytest.mark.parametrize("checkpoint", cli.checkpoints.CHECKPOINTS, ids=lambda item: item.slug)
def test_retained_syntax_and_report_keep_both_local_generations_separate(checkpoint):
    report, selected = cli._expected_family_report(checkpoint, with_selection=True)
    expected_local_counts = {
        "dirichlet-signed-units": (0, 0),
        "dirichlet-triangular": (0, 17),
        "dirichlet-inverses": (30, 74),
    }
    assert tuple(report["support"]["prior_lower_continuation_theorems"]) == selected.continuation_support
    assert tuple(report["support"]["prior_dirichlet_theorems"]) == selected.dirichlet_support
    assert selected.local_support == (*selected.continuation_support, *selected.dirichlet_support)
    assert report["support"]["local_non_admitted_count"] == (
        report["support"]["prior_lower_continuation_count"] + report["support"]["prior_dirichlet_count"])
    assert report["support"]["published_non_admitted_count"] == len(selected.published_support)
    assert not (set(selected.continuation_support) & set(selected.dirichlet_support))
    assert (report["support"]["prior_lower_continuation_count"],
            report["support"]["prior_dirichlet_count"]) == expected_local_counts[checkpoint.slug]


def test_current_control_binding_adds_new_controls_without_discarding_prior_dirichlet_sources():
    expected = {
        "scripts/check_constructive_dirichlet_inverse.py",
        "scripts/constructive_dirichlet_inverse_checkpoints.py",
        "scripts/constructive_dirichlet_inverse_support.py",
        "scripts/export_constructive_dirichlet_inverse.py",
        "scripts/check_constructive_dirichlet.py",
        "scripts/constructive_dirichlet_checkpoints.py",
        "scripts/constructive_dirichlet_support.py",
        "scripts/export_constructive_dirichlet.py",
    }
    assert expected <= set(cli.CONTROL_SOURCES)
    assert len(cli.CONTROL_SOURCES) == len(set(cli.CONTROL_SOURCES))
    tree = ast.parse(cli.SCRIPT.read_text())
    binding = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_binding")
    text = ast.unparse(binding)
    assert "_prior_checkpoints()" in text
    assert "len(previous) != 534" in text
    assert "checkpoints.original._check_lean_binary()" in text
