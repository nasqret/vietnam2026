"""Pure navigation/transport regressions, NOT proof acceptance.

Synthetic pages and private filesystem transactions below never manufacture
a LiveReleaseContext.  The public rejection tests use its actual guard; the
unchanged same-live reader suites still run during every real publication.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import inspect
import json
from pathlib import Path
import resource
import signal
import sys
import time
from types import FunctionType

import pytest

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "scripts", ROOT / "peano-lab/py"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import publish_constructive_completed_lower_v31 as correction


publication = correction.publication
original = correction.original
CATALOG = "123456789abc" + "d" * 52
OLD = "../grand-campaign/?v=" + CATALOG[:12]
NEW = OLD[3:]
LABEL = b'{"presentation_fixture_only":true,"proofs_verified":false}\n'


def _page(anchor=None, *, prefix="", suffix=""):
    if anchor is None:
        anchor = '<a href="' + OLD + '">Grand campaign</a>'
    return ('<!doctype html><html><head><title>Presentation fixture, no proof verified</title></head>'
            '<body>' + prefix + '<header class="hero"><nav>' + anchor + '</nav></header>'
            + suffix + '</body></html>').encode()


def _files(index=None):
    values = {"index.html": _page() if index is None else index,
              "publication.json": LABEL, "family/index.html": b"literal family bytes; no proof authority\n",
              "assets/proofs.js": b"/* literal synthetic asset */\n"}
    manifest = {
        "schema": publication.SCHEMA + "-manifest", "alpha_edition_version": "v31",
        "alpha_first_enrolled_version": "v31", "catalog_sha256": CATALOG,
        "first_enrollment_catalog_sha256": CATALOG, "html_revision": CATALOG[:12],
        "theorem_count": 574, "checked_use_count": 574, "stable_count": 0,
        "families": [{"fixture_notice": "pure metadata; no theorem accepted"}],
        "file_count_excluding_manifest": len(values), "files": {name: original._pin(raw) for name, raw in values.items()},
    }
    values["manifest.json"] = publication.json_bytes(manifest)
    return values


def _mutate_manifest(files, mutation):
    value = publication.strict_json(files["manifest.json"])
    mutation(value)
    files["manifest.json"] = publication.json_bytes(value)


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "presentation-source.py"
    path.write_bytes(b"# labeled pure presentation fixture\n")
    pin = correction._observe_source(tmp_path, path.name)
    return correction.SourceBinding(tmp_path, (pin,))


def _correct(files, source, catalog=CATALOG):
    return correction._correct_completed_files(files, catalog_sha256=catalog, sources=source)


def test_only_aggregate_href_and_its_manifest_change(source):
    files = _files()
    before = deepcopy(files)
    result = _correct(files, source)
    assert files == before and set(result) == set(files)
    assert result["index.html"] == files["index.html"].replace(OLD.encode(), NEW.encode(), 1)
    assert len(result["index.html"]) == len(files["index.html"]) - 3
    for name in set(files) - {"index.html", "manifest.json"}:
        assert result[name] is files[name]
    old = publication.strict_json(files["manifest.json"])
    new = publication.strict_json(result["manifest.json"])
    assert result["manifest.json"] == publication.json_bytes(new)
    record = new.pop("presentation_correction")
    assert record == {
        "schema": correction.CORRECTION_SCHEMA,
        "scope": "one_navigation_href_only_not_proof_evidence", "path": "index.html",
        "old_href": OLD, "new_href": NEW,
        "original_manifest": original._pin(files["manifest.json"]),
        "original_index": original._pin(files["index.html"]),
        "sources": source.descriptor(),
        "source_binding_sha256": publication.digest(original._canonical(source.descriptor())),
    }
    assert new["files"]["index.html"] == original._pin(result["index.html"])
    new["files"]["index.html"] = old["files"]["index.html"]
    assert new == old


@pytest.mark.parametrize("protected", [
    '<script>const untouched = \'<a href="' + OLD + '">data</a>\';</script>',
    '<script type="application/json">{"link":"' + OLD + '"}</script>',
    '<pre><a href="' + OLD + '">literal proof text</a></pre>',
    '<code><a href="' + OLD + '">literal formula</a></code>',
    '<!-- <a href="' + OLD + '">comment</a> -->',
    '<style>/* ' + OLD + ' */</style>',
])
def test_protected_content_is_literal(protected, source):
    raw = _page(prefix=protected, suffix=protected)
    result = _correct(_files(raw), source)["index.html"]
    assert result.count(protected.encode()) == 2
    assert result.count(NEW.encode()) == raw.count(NEW.encode())
    assert result == raw.replace(('<nav><a href="' + OLD).encode(), ('<nav><a href="' + NEW).encode(), 1)


def test_multiline_unicode_and_entities_are_not_reserialized(source):
    raw = _page(prefix="\n<p>μ · ę &amp; &#x2260; -&gt;</p>\r\n")
    result = _correct(_files(raw), source)["index.html"]
    assert result == raw.replace(OLD.encode(), NEW.encode(), 1)


def test_exact_frozen_html_adapter_output_is_correctable(source):
    # Calls only the real pure HTML adapter, not a proof builder or capability.
    from build_constructive_completed_lower_explorer_v31 import _CurrentHTML
    raw = _CurrentHTML("index.html", CATALOG[:12], portable_script="<script>/* unchanged */</script>\n").finish(_page())
    result = _correct(_files(raw), source)["index.html"]
    assert result == raw.replace(OLD.encode(), NEW.encode(), 1)
    assert b'<meta name="proof-publication-scope"' in raw


@pytest.mark.parametrize("raw", [
    _page(""),
    _page('<a href="' + OLD + '">one</a><a href="' + OLD + '">two</a>'),
    _page().replace(b'class="hero"', b'class="elsewhere"'),
    _page().replace(b"<nav>", b"<div>").replace(b"</nav>", b"</div>"),
    _page().replace(OLD.encode(), NEW.encode()),
    _page().replace(CATALOG[:12].encode(), b"aaaaaaaaaaaa"),
    _page('<a href="' + OLD + '" href="elsewhere">duplicate</a>'),
    _page('<a class="unexpected" href="' + OLD + '">changed markup</a>'),
    _page().replace(b"</nav>", b"</article>"),
    _page().replace(b"<nav>", b"<nav/>"),
    _page().replace(b"</html>", b""),
    _page(prefix='<a href="' + OLD + '">outside header</a>'),
    _page() + b"\xff",
])
def test_wrong_or_ambiguous_html_is_rejected(raw, source):
    with pytest.raises((ValueError, UnicodeError)):
        _correct(_files(raw), source)


@pytest.mark.parametrize("value", [None, (), [], b"", "not files", {}, {"index.html": b"x"}])
def test_non_file_mapping_is_rejected(value, source):
    with pytest.raises(ValueError):
        _correct(value, source)


@pytest.mark.parametrize("catalog", [None, True, "0" * 63, "G" * 64, CATALOG.upper(), "0" * 64])
def test_wrong_catalog_identity_is_rejected(catalog, source):
    with pytest.raises(ValueError):
        _correct(_files(), source, catalog)


@pytest.mark.parametrize(("key", "value"), [
    ("schema", "foreign"), ("alpha_edition_version", "v30"), ("alpha_first_enrolled_version", "v30"),
    ("catalog_sha256", "0" * 64), ("first_enrollment_catalog_sha256", "0" * 64),
    ("html_revision", "0" * 12), ("presentation_correction", {}),
    ("files", []), ("file_count_excluding_manifest", True), ("file_count_excluding_manifest", 0),
])
def test_changed_manifest_contract_is_rejected(key, value, source):
    files = _files()
    _mutate_manifest(files, lambda manifest: manifest.__setitem__(key, value))
    with pytest.raises(ValueError):
        _correct(files, source)


@pytest.mark.parametrize("mutation", [
    lambda raw: raw.rstrip(),
    lambda raw: b" " + raw,
    lambda raw: raw.replace(b"\n", b"\r\n"),
    lambda raw: raw.replace(b'"schema":', b'"schema": "duplicate", "schema":', 1),
    lambda raw: raw.replace(b'"stable_count": 0', b'"stable_count": NaN'),
    lambda raw: b"[]\n",
])
def test_manifest_must_be_strict_canonical_bytes(mutation, source):
    files = _files()
    files["manifest.json"] = mutation(files["manifest.json"])
    with pytest.raises(ValueError):
        _correct(files, source)


@pytest.mark.parametrize("name", ["index.html", "publication.json", "family/index.html", "assets/proofs.js"])
def test_every_original_pin_is_checked_even_same_length(name, source):
    files = _files()
    files[name] = b"!" + files[name][1:]
    with pytest.raises(ValueError, match="manifest pin"):
        _correct(files, source)


@pytest.mark.parametrize("bad", [None, b"", "not bytes", bytearray(b"x")])
def test_nonliteral_or_empty_file_is_rejected(bad, source):
    files = _files()
    files["assets/proofs.js"] = bad
    with pytest.raises(ValueError):
        _correct(files, source)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "a//b", "a/./b", "a\\b", "a\x00b"])
def test_unexpected_paths_are_not_projected(name, source):
    files = _files()
    files[name] = b"not an allowed generated path"
    with pytest.raises(ValueError):
        _correct(files, source)


@pytest.mark.parametrize("kind", ["missing", "extra", "self", "boolean_size", "wrong_size", "wrong_sha", "extra_pin_key"])
def test_hostile_manifest_inventory_rejected(kind, source):
    files = _files()
    def change(value):
        pins = value["files"]
        if kind == "missing": del pins["publication.json"]
        elif kind == "extra": pins["extra.json"] = original._pin(LABEL)
        elif kind == "self": pins["manifest.json"] = original._pin(LABEL)
        elif kind == "boolean_size": pins["index.html"]["bytes"] = True
        elif kind == "wrong_size": pins["index.html"]["bytes"] += 1
        elif kind == "wrong_sha": pins["index.html"]["sha256"] = "0" * 64
        else: pins["index.html"]["authority"] = "not allowed"
    _mutate_manifest(files, change)
    with pytest.raises(ValueError):
        _correct(files, source)


def test_already_corrected_manifest_is_not_reinterpreted(source):
    first = _correct(_files(), source)
    with pytest.raises(ValueError):
        _correct(first, source)


@pytest.mark.parametrize("kind", ["same_length", "missing", "symlink", "directory"])
def test_literal_source_binding_fails_closed(kind, source):
    path = source.root / source.pins[0][0]
    if kind == "same_length": path.write_bytes(b"!" + path.read_bytes()[1:])
    else:
        path.unlink()
        if kind == "symlink": path.symlink_to(Path(__file__))
        elif kind == "directory": path.mkdir()
    with pytest.raises(ValueError):
        source.require_unchanged()
    with pytest.raises(ValueError):
        correction._process_namespace(source)


@pytest.mark.parametrize("kind", ["empty", "directory", "symlink", "ancestor_symlink", "oversized", "unsafe"])
def test_initial_source_observation_is_bounded_and_regular(kind, tmp_path, monkeypatch):
    name = "source.py"
    if kind == "empty": (tmp_path / name).write_bytes(b"")
    elif kind == "directory": (tmp_path / name).mkdir()
    elif kind == "symlink": (tmp_path / name).symlink_to(Path(__file__))
    elif kind == "ancestor_symlink":
        (tmp_path / "link").symlink_to(Path(__file__).parent, target_is_directory=True)
        name = "link/" + Path(__file__).name
    elif kind == "oversized":
        (tmp_path / name).write_bytes(b"x" * 17)
        monkeypatch.setattr(original, "MAX_FILE_BYTES", 16)
    else: name = "../outside.py"
    with pytest.raises(ValueError):
        correction._observe_source(tmp_path, name)


def test_real_source_inventory_is_exact_and_unchanged():
    correction._SOURCES.require_unchanged()
    assert correction._SOURCES.pins[:10] == correction.FROZEN_SOURCES
    assert tuple(pin[0] for pin in correction._SOURCES.pins[-2:]) == (correction.SOURCE, correction.TEST)
    assert len(set(pin[0] for pin in correction._SOURCES.pins)) == 12


def _underlying(function):
    return inspect.getclosurevars(function).nonlocals.get("function", function)


def test_every_original_function_gets_private_globals_and_defaults(source):
    before = dict(vars(original))
    namespace = correction._process_namespace(source)
    guarded = {"_fork_phase", "_run_phase_tests", "_validate_tree", "_rss_bytes"}
    for name, function in before.items():
        if isinstance(function, FunctionType) and function.__module__ == original.__name__:
            if name == "_phase_entries":
                assert namespace[name] is not function
                continue
            actual = _underlying(namespace[name]) if name in guarded else namespace[name]
            assert actual is not function and actual.__code__ is function.__code__
            assert actual.__globals__ is namespace
            assert actual.__defaults__ == function.__defaults__
            assert actual.__kwdefaults__ == function.__kwdefaults__
            assert actual.__annotations__ == function.__annotations__
    assert namespace["OUTPUTS"] == original.OUTPUTS and namespace["OUTPUTS"] is not original.OUTPUTS
    assert namespace["TESTS"] == original.TESTS and namespace["TESTS"] is not original.TESTS
    assert set(vars(original)) == set(before)
    assert all(vars(original)[name] is value for name, value in before.items())


def test_no_limits_or_live_test_selection_changed(source):
    namespace = correction._process_namespace(source)
    assert namespace["CPU_LIMITS"] == (170, 175)
    assert namespace["WALL_SECONDS"] == 180 and namespace["TIMEOUT_SECONDS"] == 185
    assert namespace["MAX_RSS_BYTES"] == 1536 * 1024 * 1024
    assert namespace["MAX_MESSAGE_BYTES"] == 8192
    assert namespace["MAX_INVENTORY_BYTES"] == 2 * 1024 * 1024
    assert namespace["PHASES"] == ("completed", "historical", "atlas")
    assert namespace["TESTS"] == {
        "completed": ("peano-lab/py/tests/test_constructive_completed_lower_explorer_v31.py", "not atlas"),
        "historical": ("peano-lab/py/tests/test_constructive_historical_publication_v31.py", None),
        "atlas": ("peano-lab/py/tests/test_constructive_completed_lower_explorer_v31.py", "atlas"),
    }
    assert inspect.signature(correction.publish_from_live_context).parameters.keys() == {"context", "check"}


@pytest.mark.parametrize("value", [None, {}, {"verified": True}, object(), LABEL])
def test_public_api_rejects_non_live_context_with_actual_guard(value):
    with pytest.raises(ValueError, match="live v31 verification capability"):
        correction.publish_from_live_context(value, check=False)


@pytest.mark.parametrize("phase", original.PHASES)
def test_private_phase_still_calls_actual_rejecting_builder(phase, source):
    namespace = correction._process_namespace(source)
    with pytest.raises(ValueError, match="live v31 verification capability"):
        tuple(namespace["_phase_entries"](object(), phase))


@pytest.mark.parametrize("name", ["_fork_phase", "_run_phase_tests", "_validate_tree", "_rss_bytes"])
def test_changed_sources_rejected_at_each_boundary_before_action(name, source):
    namespace = correction._process_namespace(source)
    path = source.root / source.pins[0][0]
    path.write_bytes(b"!" + path.read_bytes()[1:])
    with pytest.raises(ValueError, match="pinned presentation input changed"):
        namespace[name]()  # Must reject before argument-dependent work.


def _private_results(tmp_path, namespace):
    result = []
    output = tmp_path / "output"
    output.mkdir()
    namespace["OUTPUTS"] = {phase: output / phase for phase in original.PHASES}
    for phase in original.PHASES:
        tree = tmp_path / ("private-" + phase)
        tree.mkdir()
        (tree / "fixture.json").write_bytes(LABEL)
        inventory = {"files": {"fixture.json": original._pin(LABEL)}, "file_count": 1,
                     "html_count": 0, "total_bytes": len(LABEL)}
        result.append(original.PhaseResult(phase, tree, inventory,
                      publication.digest(original._canonical(inventory)), 1, 0.1))
    return tuple(result)


@pytest.mark.parametrize("after_move", [1, 3])
def test_mid_install_source_change_rolls_back_only_owned_trees(after_move, source, tmp_path):
    namespace = correction._process_namespace(source)
    results = _private_results(tmp_path, namespace)
    rename = namespace["_rename_new"]
    moves = []
    def changing_rename(source_path, destination):
        rename(source_path, destination)
        moves.append((source_path, destination))
        if len(moves) == after_move:
            path = source.root / source.pins[0][0]
            path.write_bytes(b"!" + path.read_bytes()[1:])
    namespace["_rename_new"] = changing_rename
    with pytest.raises(ValueError, match="pinned presentation input changed"):
        namespace["_install_results"](results, check=False)
    assert len(moves) == after_move * 2
    assert all(not target.exists() for target in namespace["OUTPUTS"].values())
    assert all((row.directory / "fixture.json").read_bytes() == LABEL for row in results)


def test_changed_inventory_rejected_before_any_install(source, tmp_path):
    namespace = correction._process_namespace(source)
    results = _private_results(tmp_path, namespace)
    altered = deepcopy(results[0].inventory)
    altered["files"]["fixture.json"] = original._pin(b"X" + LABEL[1:])
    (results[0].directory / "fixture.json").write_bytes(b"X" + LABEL[1:])
    results = (replace(results[0], inventory=altered), *results[1:])
    with pytest.raises(ValueError, match="inventory changed"):
        namespace["_install_results"](results, check=False)
    assert all(not target.exists() for target in namespace["OUTPUTS"].values())


@pytest.mark.parametrize("args", [["--create-release", "--check"], ["--test"], ["--skip-proof"], ["--receipt", "old.json"]])
def test_cli_has_no_ambiguous_or_proof_bypass_modes(args):
    with pytest.raises(SystemExit) as result:
        correction.main(args)
    assert result.value.code == 2


def test_cli_uses_one_fresh_audit_for_each_mode_and_original_schedule():
    text = inspect.getsource(correction.main)
    assert "payloads, audit = build_payloads()" in text
    assert "check_or_write(payloads, check=False)" in text
    assert "context = context_from_live_audit(audit)" in text
    assert "context = verify_for_publication()" in text
    assert "_publish_bound(context, args.check, _SOURCES)" in text
    assert "jobs * proof_audit.PARENT_TIMEOUT_SECONDS + 4 * proof_audit.WALL_SECONDS" in text
    assert "resource.setrlimit(resource.RLIMIT_CPU, proof_audit.CPU_LIMITS)" in text


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    result = int(pytest.main([__file__, "-q", "--tb=short", *sys.argv[1:]]))
    print(json.dumps({"exit_code": result, "elapsed_seconds": time.monotonic() - started,
                      "peak_rss_bytes": original._rss_bytes(), "proofs_verified": False,
                      "scope": "pure presentation correction and private transport regressions"}), flush=True)
    raise SystemExit(result)
