"""Current v33 selectors: genuine metadata, unchanged proof algorithms and limits.

These tests do not certify mathematical bodies. Every positive UI/CLI metadata
path is guarded by always-failing proof-provider/replay sentinels. Mathematical
admission is independently exercised by the provider/edition and fresh10 suites.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import resource
import signal
import sys
import time
from types import SimpleNamespace

_BOUNDED_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest
import driver
from peano_lab.library import campaign_research_v33_closure as research, lean_proof_strand, theorems
from peano_lab.ui import data_library

ROOT = Path(__file__).resolve().parents[3]
PRINCIPALS = (
    ("prime_field_polynomial_division_execution_functional", "b14ad2149cd34386887dcac50cb06b7df7014500b1ab918fac7967976b6042fe"),
    ("prime_field_polynomial_division_execution_exists_unique", "0ac4c1f5ca519e7db039365ff2a703f8772e22e58376d4c55a3f7777e08565fc"),
    ("prime_field_polynomial_convolution_both_left_paddings_equivalent", "fbefa6c478ac7028d2c60d742799660f05d010578ce4ed30b0f72f6f0af237d6"),
    ("prime_field_polynomial_convolution_both_left_paddings_exists", "b79ee5e0362c752f6b0189437e25cacc49e7060037adf8837f3105db832f8ffd"),
    ("prime_field_polynomial_equivalent_implies_left_pad", "e9b137b8b2e2d502cb4f5405a4cb90a0abcbb50de9a0df45ff51d5127761a25c"),
    ("prime_field_polynomial_add_equivalent_congruent", "847a60b511d446febdc15c56231f1368a7993172939945b7b99ab297cb65c4fb"),
    ("prime_field_polynomial_subtract_equivalent_congruent", "b073daede7886ec70b68c11665fc2f70154db2696cd613e542d1e22900e5f2a3"),
    ("prime_field_polynomial_convolution_equivalent_congruent", "d984fe3c378d4d4b02941d6f3a126324a2c7c26bf47f4d8ee7c37b2e55404446"),
)
PARENT_SOURCE_PINS = {
    "editions_v32.py": "69707c34aed369163cc0cce95db7e6078302fe639df75210176e9b53ab719785",
    "alpha_enrollment_v32.py": "81003d179548d50417ef093e1e7c6fc1006ec72ff06f39d1e0a47e56335172c6",
    "campaign_research_v32_closure.py": "cdbc803669fc35c0d8b91e06f5f79d1470ffc2355e041fc12c205ec21dfb3ea0",
}


@pytest.fixture(scope="module")
def alpha():
    from peano_lab.library import editions_v33
    return editions_v33


@pytest.fixture(scope="module")
def exporter():
    spec = importlib.util.spec_from_file_location("peano_v33_ui_exporter", ROOT / "scripts/export_peano_lean.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _forbid_proofs(monkeypatch, alpha):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("a metadata selector tried to load or replay a proof")
    for module, provider in ((alpha, "research"), (alpha.v32, "research"), (alpha.v32.v31, "completed_lower"),
                             (alpha.v32.v31.v30, "gaussian_factorization"),
                             (alpha.v32.v31.v30.v29, "priority_layer"),
                             (alpha.v32.v31.v30.v29.v28, "lower_layer")):
        for name in ("replay", "_checked_" + provider + "_bundle", "checked_" + provider + "_bundle"):
            monkeypatch.setattr(module, name, forbidden)
    for name in ("read_research_bundle_bytes", "check_research_proof_bundle", "research_plan", "research_specs"):
        monkeypatch.setattr(research, name, forbidden)
    for name in ("replay", "lean_export", "export_checked_theorem"):
        monkeypatch.setattr(data_library, name, forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)


def test_exact_current_inventory_and_all_three_selectors_preserve_parent_and_stable(alpha, exporter, monkeypatch):
    _forbid_proofs(monkeypatch, alpha)
    assert len(alpha.ALPHA_ENTRIES) == 4092 and len(alpha.FRONTIER_NEW_NAMES) == 121
    assert len(alpha.v32.ALPHA_ENTRIES) == 3971 and len(alpha.v32.FRONTIER_NEW_NAMES) == 175
    assert alpha.STABLE_ENTRIES is alpha.v32.STABLE_ENTRIES and len(alpha.STABLE_ENTRIES) == 432
    assert alpha.STABLE_EDITION is alpha.v32.STABLE_EDITION
    assert all(a is b for a, b in zip(alpha.ALPHA_ENTRIES, alpha.v32.ALPHA_ENTRIES))
    assert data_library._alpha_edition() is alpha
    assert lean_proof_strand._edition_view("alpha") == (alpha.ALPHA_EDITION, "v33")
    assert lean_proof_strand._edition_view("stable") == (alpha.STABLE_EDITION, "stable")
    output = driver.LabSession().run("pa lib alpha")
    for expected in ("immutable Alpha v33", "Enrolled statements: 4,092", "Stable closed: 432",
                     "Alpha closed: 3,660", "Previously added Alpha v32 campaign results: 175",
                     "New constructive campaign results: 121", alpha.ALPHA_V33_IDENTITY_SHA256):
        assert expected in output
    assert "Independent empty-context kernel check: PASS" not in output
    assert "432 scripted theorems" in driver.LabSession().run("pa lib")
    for name, expected in PRINCIPALS:
        item = alpha.entry(name, edition="alpha")
        assert item.checked_use and alpha.v32.entry(name, edition="alpha") is None
        assert alpha.entry(name, edition="stable") is None and theorems.get(name) is None
        assert sha256(item.spec.statement.encode()).hexdigest() == expected
        spec, selected = exporter._load_selected_specification(SimpleNamespace(edition="alpha", theorem=name))
        assert selected is alpha and spec is item.spec


@pytest.mark.parametrize("name,digest", PRINCIPALS)
def test_eight_current_principal_cards_are_exact_without_loading_proofs(alpha, monkeypatch, name, digest):
    _forbid_proofs(monkeypatch, alpha)
    output = driver.LabSession().run("pa lib alpha " + name)
    item = alpha.entry(name, edition="alpha")
    assert name + " — Alpha v33 theorem evidence" in output
    assert "Release evidence: alpha_closed" in output and "Release membership: alpha_only" in output
    assert "Checked-use authority: YES" in output
    assert "This evidence card does not itself replay a proof." in output
    assert item.spec.summary in output and sha256(item.spec.statement.encode()).hexdigest() == digest
    assert "Independent empty-context kernel check: PASS" not in output


@pytest.mark.parametrize("name,digest", PRINCIPALS)
@pytest.mark.parametrize("command", ("pa proof alpha", "pa lean alpha exact", "pa lean alpha tactics"))
def test_eight_new_root_previews_keep_actual_source_and_original_browser_limits(alpha, monkeypatch, name, digest, command):
    _forbid_proofs(monkeypatch, alpha)
    output = driver.LabSession().run(command + " " + name)
    assert name in output and "Release edition: Alpha v33." in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Checked-use authority: YES." in output and "Independent Lean compilation: NOT RUN" in output
    assert "--edition alpha" in output and "--verify" in output
    assert "--proof-bundle" not in output and len(output.encode()) <= 15360
    assert sha256(alpha.entry(name, edition="alpha").spec.statement.encode()).hexdigest() == digest
    expected = ("Fresh Peano proof replay: NOT RUN" if command.startswith("pa proof") else
                "Fresh independent empty-context Peano kernel replay: NOT RUN")
    assert expected in output


@pytest.mark.parametrize("name,digest", PRINCIPALS)
def test_eight_actual_strand_plans_keep_new_version_and_literal_specification(alpha, monkeypatch, name, digest):
    _forbid_proofs(monkeypatch, alpha)
    plan = lean_proof_strand.plan_proof_strand(name, edition="alpha")
    spec = alpha.entry(name, edition="alpha").spec
    assert plan.root == name and plan.edition_version == "v33"
    assert plan.edition_identity_sha256 == alpha.ALPHA_V33_IDENTITY_SHA256
    assert sha256(plan.root_node.statement.encode()).hexdigest() == digest
    assert plan.root_node.dependencies == spec.dependencies and plan.root_node.script == spec.script
    assert plan.root_node.evidence == "alpha_closed" and plan.root_node.membership == "alpha_only"
    assert plan.root_node.source_path == alpha.entry(name, edition="alpha").source_module


@pytest.mark.parametrize("name,digest", PRINCIPALS)
def test_cli_selection_is_the_same_entry_and_does_not_open_an_artifact(alpha, exporter, monkeypatch, name, digest):
    _forbid_proofs(monkeypatch, alpha)
    monkeypatch.setattr(Path, "read_bytes", lambda *_a, **_k: pytest.fail("selection read an artifact"))
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("selection opened an artifact"))
    spec, selected = exporter._load_selected_specification(SimpleNamespace(edition="alpha", theorem=name))
    assert selected is alpha and spec is alpha.entry(name, edition="alpha").spec
    assert sha256(spec.statement.encode()).hexdigest() == digest


@pytest.mark.parametrize("slug", ("polynomial-euclidean-division",))
def test_either_unsealed_new_family_blocks_all_current_selectors_without_fallback(alpha, exporter, monkeypatch, slug):
    _forbid_proofs(monkeypatch, alpha)
    changed = tuple(replace(family, artifact_bytes=0) if family.slug == slug else family for family in research.FAMILIES)
    monkeypatch.setattr(research, "FAMILIES", changed)
    monkeypatch.setattr(research, "RESEARCH_FAMILIES", changed)
    name = PRINCIPALS[-1][0]
    for command in ("pa lib alpha", "pa lib alpha " + name, "pa proof alpha " + name, "pa lean alpha " + name):
        text = driver.LabSession().run(command)
        assert "not sealed" in text and "Checked-use authority: YES" not in text
    with pytest.raises(lean_proof_strand.ProofStrandError, match="not sealed"):
        lean_proof_strand._edition_view("alpha")
    with pytest.raises(ValueError, match="not sealed"):
        exporter._load_selected_specification(SimpleNamespace(edition="alpha", theorem=name))
    assert "432 scripted theorems" in driver.LabSession().run("pa lib")


@pytest.mark.parametrize("command", ("pa lib alpha", "pa lib alpha " + PRINCIPALS[0][0],
                                    "pa proof alpha " + PRINCIPALS[0][0], "pa lean alpha " + PRINCIPALS[-1][0]))
def test_zero_current_count_has_no_old_alpha_fallback(alpha, monkeypatch, command):
    _forbid_proofs(monkeypatch, alpha)
    monkeypatch.setattr(alpha, "EXPECTED_ALPHA_V33_COUNT", 0)
    monkeypatch.setattr(alpha.v32, "entry", lambda *_a, **_k: pytest.fail("unsealed current fell back to historical v32"))
    output = driver.LabSession().run(command)
    assert "Alpha v33 is not sealed for checked use" in output and "Checked-use authority: YES" not in output
    assert "432 scripted theorems" in driver.LabSession().run("pa lib")


def test_bad_historical_parent_still_blocks_the_new_current_seal(alpha, exporter, monkeypatch):
    _forbid_proofs(monkeypatch, alpha)
    monkeypatch.setattr(alpha.v32, "EXPECTED_ALPHA_V32_COUNT", 0)
    with pytest.raises(alpha.EditionV33Error, match="parent is not sealed"):
        data_library._alpha_edition()
    with pytest.raises(lean_proof_strand.ProofStrandError, match="parent is not sealed"):
        lean_proof_strand._edition_view("alpha")
    with pytest.raises(ValueError, match="parent is not sealed"):
        exporter._load_selected_specification(SimpleNamespace(edition="alpha", theorem=PRINCIPALS[0][0]))
    assert lean_proof_strand._edition_view("stable")[0] is alpha.STABLE_EDITION


@pytest.mark.parametrize("command", ("pa lib alpha check", "pa lean alpha full"))
@pytest.mark.parametrize("name,_digest", PRINCIPALS)
def test_new_roots_keep_original_browser_budget_and_reject_replay_failures(alpha, monkeypatch, command, name, _digest):
    _forbid_proofs(monkeypatch, alpha)
    spec = alpha.entry(name, edition="alpha").spec
    count = data_library._lean_full_dependency_count(spec, edition="alpha", alpha_module=alpha)
    assert count > 0
    attempted = []
    rejection = "intentionally rejected real replay request; no proof accepted"
    def reject(actual_name, *, edition):
        assert actual_name == name and edition == "alpha"
        attempted.append((actual_name, edition))
        raise RuntimeError(rejection)
    monkeypatch.setattr(alpha, "replay", reject)
    output = driver.LabSession().run(command + " " + name)
    if count > data_library._LEAN_FULL_BROWSER_DEPENDENCY_LIMIT:
        assert attempted == [] and "no proof certificate was loaded" in output.lower()
    else:
        assert attempted == [(name, "alpha")] and rejection in output
    assert "kernel check: PASS" not in output


def test_v18_flagship_route_traverses_current_v33_then_unchanged_v32(alpha, monkeypatch):
    _forbid_proofs(monkeypatch, alpha)
    spec = alpha.entry("bertrand_strict", edition="alpha").spec
    assert data_library._lean_flagship_bundle_argument(spec, edition="alpha") == (
        " --proof-bundle research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json")
    assert data_library._lean_flagship_bundle_argument(spec, edition="stable") == ""
    assert data_library._lean_flagship_bundle_argument(alpha.entry(PRINCIPALS[-1][0], edition="alpha").spec, edition="alpha") == ""


@pytest.mark.parametrize("filename,expected", tuple(PARENT_SOURCE_PINS.items()))
def test_old_v32_runtime_admission_sources_are_still_literal(filename, expected):
    path = ROOT / "peano-lab/py/peano_lab/library" / filename
    assert sha256(path.read_bytes()).hexdigest() == expected


@pytest.mark.parametrize("path,excluded,expected", (
    ("peano-lab/py/peano_lab/library/lean_proof_strand.py", "_edition_view",
     "d13fae68888beebeea4b15961bfcb6290d9397bf301b503494ca2a927a6e7be8"),
    ("scripts/export_peano_lean.py", "_load_selected_specification",
     "6155f0366cca96c4b32eb46bc84b797212e7372b383e38c9101238caaffc7c16"),
))
def test_every_nonselector_export_and_strand_callable_has_the_exact_original_ast(path, excluded, expected):
    tree = ast.parse((ROOT / path).read_text())
    tree.body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                 and node.name != excluded]
    assert sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest() == expected


def test_all_other_ui_callable_algorithms_are_original_after_only_current_label_normalization():
    class Labels(ast.NodeTransformer):
        def visit_Constant(self, node):
            if type(node.value) is str:
                node.value = node.value.replace("Alpha v33", "Alpha v31").replace("Alpha-v33", "Alpha-v31")
            return node
    tree = ast.parse((ROOT / "peano-lab/py/peano_lab/ui/data_library.py").read_text())
    tree.body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                 and node.name not in {"_alpha_edition", "render_alpha_index", "_lean_flagship_bundle_argument"}]
    tree = Labels().visit(tree)
    assert sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest() == (
        "2a6d60294ae5295e27105455d441c158ad8f368554d8cb769f6e66c84f4d1e99")


def test_all_original_ui_and_strand_resource_limits_are_unchanged():
    assert (data_library._LEAN_BROWSER_LIMIT, data_library._LEAN_FULL_BROWSER_DEPENDENCY_LIMIT) == (15360, 128)
    assert (data_library._PROOF_STRAND_STATEMENT_LIMIT, data_library._PROOF_STRAND_SCRIPT_LINES,
            data_library._PROOF_STRAND_DIRECT_DEPENDENCIES) == (4096, 48, 16)
    assert (lean_proof_strand.MAX_STRAND_NODES, lean_proof_strand.MAX_STRAND_EDGES,
            lean_proof_strand.MAX_STRAND_DEPTH) == (4096, 65536, 256)
    assert lean_proof_strand.MAX_TOTAL_SPECIFICATION_BYTES == 64 * 1024 * 1024


def _main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pytest-select", default="")
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    if args.case_start < 0 or args.case_count is not None and args.case_count <= 0:
        parser.error("a positive exact test window is required")

    class Window:
        def __init__(self):
            self.selected, self.passed, self.bad = [], set(), []
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            chosen = items[args.case_start:None if args.case_count is None else args.case_start + args.case_count]
            if not chosen or args.case_count is not None and len(chosen) != args.case_count:
                raise ValueError("the exact requested case window is unavailable")
            ids = {item.nodeid for item in chosen}
            config.hook.pytest_deselected(items=[item for item in items if item.nodeid not in ids])
            items[:] = chosen
            self.selected = [item.nodeid for item in chosen]
        def pytest_runtest_logreport(self, report):
            if report.when == "call" and report.passed:
                self.passed.add(report.nodeid)
            elif report.failed or report.skipped or getattr(report, "wasxfail", None):
                self.bad.append(report.nodeid)

    plugin = Window()
    options = [str(Path(__file__).resolve()), "-q", "--disable-warnings", "-k", args.pytest_select]
    if args.collect_only:
        options.append("--collect-only")
    status = pytest.main(options, plugins=[plugin])
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    if not 0 < peak <= 1536 * 1024 * 1024:
        raise RuntimeError("the original observed RSS bound was exceeded")
    if not args.collect_only and (plugin.bad or plugin.passed != set(plugin.selected)):
        status = status or 1
    print(json.dumps({"selected": len(plugin.selected), "passed": len(plugin.passed),
        "pytest_exit_code": int(status), "collect_only": args.collect_only,
        "elapsed_seconds": time.monotonic() - _BOUNDED_STARTED, "peak_rss_bytes": peak,
        "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)), "wall_seconds": 180}, sort_keys=True), flush=True)
    return int(status)


if __name__ == "__main__":
    raise SystemExit(_main())
