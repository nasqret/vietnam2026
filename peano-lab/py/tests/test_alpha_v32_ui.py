"""Current v32 selectors: genuine metadata, unchanged proof algorithms and limits.

These tests do not certify mathematical bodies. Every positive UI/CLI metadata
path is guarded by always-failing proof-provider/replay sentinels. Mathematical
admission is independently exercised by the provider/edition and fresh15 suites.
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
from peano_lab.library import campaign_research_v32_closure as research, lean_proof_strand, theorems
from peano_lab.ui import data_library

ROOT = Path(__file__).resolve().parents[3]
PRINCIPALS = (
    ("signed_support_reindex_sum_equal", "3077d5330886460850c4a16cd0e57026c138813c128d9e013c61e428ec2c56cc"),
    ("signed_cartesian_product_sums_exists", "112d93e7f0c1b600a57b30c7b06341d249f529c30dfaf907ceeae9f8614b51c7"),
    ("coprime_divisor_factor_pair_exists_unique", "629b845a1c30abee52ebb49d4f59dea2b06bc00dab3403512507e737112c4d12"),
    ("dirichlet_convolution_multiplicative_values", "7a5bfcd97f2feacc1e3c49a520bbf41370e09c940f6d35f16b54ca27a4b84868"),
    ("dirichlet_convolution_multiplicative_table", "c5f3035ecf2a9e90fc3e56118bb17769ddc68feb1a32a95aa48619cf7c4b8889"),
    ("dirichlet_convolution_multiplicative_exists_unique", "957aa567b3f1547a98478a195178e8d5a7e88cf6a01af0b67f94413191d56970"),
    ("prime_field_polynomial_subtract_exists", "e6a46edf32d7a565ab18ccc9406cec320dbeefc6f0094b7169f28a1080d6a965"),
    ("prime_field_polynomial_trim_exists_unique", "9d2f9bdd9da63a0f151a5b0b8c0918506ee25f3868bcd3138b2810c94691caa3"),
    ("prime_field_polynomial_monic_normalization_exists_unique", "8e2fc07b075ca8acacefcd2ba4ac6ef42511e463f64745b2875a498484eedcb5"),
    ("prime_field_polynomial_synthetic_exists_unique", "a9ca5a2a94437641e4cc683ef0dcdabb5eef4bbb4a181620e6760f1ff285ad7b"),
    ("prime_field_polynomial_synthetic_represented_degree", "c8b3b71ec31e34582c37aa3037efa57961699f87f9dfc242316db5bb5e951392"),
    ("prime_field_polynomial_synthetic_zero_remainder_iff", "817632388315e7ec579bf1788ae68f75200a7cee737a17f46779150cf4c45441"),
)
PARENT_SOURCE_PINS = {
    "editions_v31.py": "24fedcd8a492578f9a1e32bdd984693bd8e27216105000f719188a3a38200870",
    "alpha_enrollment_v31.py": "7106c15b7196ca70d4bd62a4708696bd38e9b4eee07a127844c2d8398cd6e81b",
    "campaign_completed_lower_closure.py": "9aec583406e6b890fdd626cb60ecf8de4271581e20e86e1aa8499a4b1701dab3",
}


@pytest.fixture(scope="module")
def alpha():
    from peano_lab.library import editions_v32
    return editions_v32


@pytest.fixture(scope="module")
def exporter():
    spec = importlib.util.spec_from_file_location("peano_v32_ui_exporter", ROOT / "scripts/export_peano_lean.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _forbid_proofs(monkeypatch, alpha):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("a metadata selector tried to load or replay a proof")
    for module, provider in ((alpha, "research"), (alpha.v31, "completed_lower"),
                             (alpha.v31.v30, "gaussian_factorization"),
                             (alpha.v31.v30.v29, "priority_layer"),
                             (alpha.v31.v30.v29.v28, "lower_layer")):
        for name in ("replay", "_checked_" + provider + "_bundle", "checked_" + provider + "_bundle"):
            monkeypatch.setattr(module, name, forbidden)
    for name in ("read_research_bundle_bytes", "check_research_proof_bundle", "research_plan", "research_specs"):
        monkeypatch.setattr(research, name, forbidden)
    for name in ("replay", "lean_export", "export_checked_theorem"):
        monkeypatch.setattr(data_library, name, forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)


def test_exact_current_inventory_and_all_three_selectors_preserve_parent_and_stable(alpha, exporter, monkeypatch):
    _forbid_proofs(monkeypatch, alpha)
    assert len(alpha.ALPHA_ENTRIES) == 3971 and len(alpha.FRONTIER_NEW_NAMES) == 175
    assert len(alpha.v31.ALPHA_ENTRIES) == 3796 and len(alpha.v31.FRONTIER_NEW_NAMES) == 574
    assert alpha.STABLE_ENTRIES is alpha.v31.STABLE_ENTRIES and len(alpha.STABLE_ENTRIES) == 432
    assert alpha.STABLE_EDITION is alpha.v31.STABLE_EDITION
    assert all(a is b for a, b in zip(alpha.ALPHA_ENTRIES, alpha.v31.ALPHA_ENTRIES))
    assert data_library._alpha_edition() is alpha
    assert lean_proof_strand._edition_view("alpha") == (alpha.ALPHA_EDITION, "v32")
    assert lean_proof_strand._edition_view("stable") == (alpha.STABLE_EDITION, "stable")
    output = driver.LabSession().run("pa lib alpha")
    for expected in ("immutable Alpha v32", "Enrolled statements: 3,971", "Stable closed: 432",
                     "Alpha closed: 3,539", "Previously added Alpha v31 campaign results: 574",
                     "New constructive campaign results: 175", alpha.ALPHA_V32_IDENTITY_SHA256):
        assert expected in output
    assert "Independent empty-context kernel check: PASS" not in output
    assert "432 scripted theorems" in driver.LabSession().run("pa lib")
    for name, expected in PRINCIPALS:
        item = alpha.entry(name, edition="alpha")
        assert item.checked_use and alpha.v31.entry(name, edition="alpha") is None
        assert alpha.entry(name, edition="stable") is None and theorems.get(name) is None
        assert sha256(item.spec.statement.encode()).hexdigest() == expected
        spec, selected = exporter._load_selected_specification(SimpleNamespace(edition="alpha", theorem=name))
        assert selected is alpha and spec is item.spec


@pytest.mark.parametrize("name,digest", PRINCIPALS)
def test_twelve_current_principal_cards_are_exact_without_loading_proofs(alpha, monkeypatch, name, digest):
    _forbid_proofs(monkeypatch, alpha)
    output = driver.LabSession().run("pa lib alpha " + name)
    item = alpha.entry(name, edition="alpha")
    assert name + " — Alpha v32 theorem evidence" in output
    assert "Release evidence: alpha_closed" in output and "Release membership: alpha_only" in output
    assert "Checked-use authority: YES" in output
    assert "This evidence card does not itself replay a proof." in output
    assert item.spec.summary in output and sha256(item.spec.statement.encode()).hexdigest() == digest
    assert "Independent empty-context kernel check: PASS" not in output


@pytest.mark.parametrize("name,digest", PRINCIPALS)
@pytest.mark.parametrize("command", ("pa proof alpha", "pa lean alpha exact", "pa lean alpha tactics"))
def test_twelve_new_root_previews_keep_actual_source_and_original_browser_limits(alpha, monkeypatch, name, digest, command):
    _forbid_proofs(monkeypatch, alpha)
    output = driver.LabSession().run(command + " " + name)
    assert name in output and "Release edition: Alpha v32." in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Checked-use authority: YES." in output and "Independent Lean compilation: NOT RUN" in output
    assert "--edition alpha" in output and "--verify" in output
    assert "--proof-bundle" not in output and len(output.encode()) <= 15360
    assert sha256(alpha.entry(name, edition="alpha").spec.statement.encode()).hexdigest() == digest
    expected = ("Fresh Peano proof replay: NOT RUN" if command.startswith("pa proof") else
                "Fresh independent empty-context Peano kernel replay: NOT RUN")
    assert expected in output


@pytest.mark.parametrize("name,digest", PRINCIPALS)
def test_twelve_actual_strand_plans_keep_new_version_and_literal_specification(alpha, monkeypatch, name, digest):
    _forbid_proofs(monkeypatch, alpha)
    plan = lean_proof_strand.plan_proof_strand(name, edition="alpha")
    spec = alpha.entry(name, edition="alpha").spec
    assert plan.root == name and plan.edition_version == "v32"
    assert plan.edition_identity_sha256 == alpha.ALPHA_V32_IDENTITY_SHA256
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


@pytest.mark.parametrize("slug", ("multiplicative-convolution", "polynomial-division-prerequisites"))
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
    monkeypatch.setattr(alpha, "EXPECTED_ALPHA_V32_COUNT", 0)
    monkeypatch.setattr(alpha.v31, "entry", lambda *_a, **_k: pytest.fail("unsealed current fell back to historical v31"))
    output = driver.LabSession().run(command)
    assert "Alpha v32 is not sealed for checked use" in output and "Checked-use authority: YES" not in output
    assert "432 scripted theorems" in driver.LabSession().run("pa lib")


def test_bad_historical_parent_still_blocks_the_new_current_seal(alpha, exporter, monkeypatch):
    _forbid_proofs(monkeypatch, alpha)
    monkeypatch.setattr(alpha.v31, "EXPECTED_ALPHA_V31_COUNT", 0)
    with pytest.raises(alpha.EditionV32Error, match="parent is not sealed"):
        data_library._alpha_edition()
    with pytest.raises(lean_proof_strand.ProofStrandError, match="parent is not sealed"):
        lean_proof_strand._edition_view("alpha")
    with pytest.raises(ValueError, match="parent is not sealed"):
        exporter._load_selected_specification(SimpleNamespace(edition="alpha", theorem=PRINCIPALS[0][0]))
    assert lean_proof_strand._edition_view("stable")[0] is alpha.STABLE_EDITION


@pytest.mark.parametrize("command", ("pa lib alpha check", "pa lean alpha full"))
@pytest.mark.parametrize("name", ("dirichlet_convolution_multiplicative_exists_unique",
                                  "prime_field_polynomial_synthetic_zero_remainder_iff"))
def test_new_roots_keep_the_original_browser_budget_and_reject_replay_failures(alpha, monkeypatch, command, name):
    _forbid_proofs(monkeypatch, alpha)
    spec = alpha.entry(name, edition="alpha").spec
    count = data_library._lean_full_dependency_count(spec, edition="alpha", alpha_module=alpha)
    expected = 129 if name == "dirichlet_convolution_multiplicative_exists_unique" else 126
    assert count == expected
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


def test_v18_flagship_route_traverses_current_v32_then_unchanged_v31(alpha, monkeypatch):
    _forbid_proofs(monkeypatch, alpha)
    spec = alpha.entry("bertrand_strict", edition="alpha").spec
    assert data_library._lean_flagship_bundle_argument(spec, edition="alpha") == (
        " --proof-bundle research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json")
    assert data_library._lean_flagship_bundle_argument(spec, edition="stable") == ""
    assert data_library._lean_flagship_bundle_argument(alpha.entry(PRINCIPALS[-1][0], edition="alpha").spec, edition="alpha") == ""


@pytest.mark.parametrize("filename,expected", tuple(PARENT_SOURCE_PINS.items()))
def test_old_v31_runtime_admission_sources_are_still_literal(filename, expected):
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
                node.value = node.value.replace("Alpha v32", "Alpha v31").replace("Alpha-v32", "Alpha-v31")
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
