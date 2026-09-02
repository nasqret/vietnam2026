"""Literal delivery diagnostics; no fixture grants proof authority."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import stage_constructive_research_publication_v34 as stage


def _count_original_html_parses(monkeypatch):
    original, calls = stage.legacy._HTML, []

    def parse(raw):
        calls.append(raw)
        return original(raw)

    monkeypatch.setattr(stage.legacy, "_HTML", parse)
    return calls


@pytest.mark.parametrize("sample", ("synthetic", "historical_hub", "current_hub"))
def test_shared_parser_matches_all_original_fields_on_actual_html(sample):
    if sample == "synthetic":
        raw = b'<html><head></head><body><a class="primary-action" href="a/?v=x" id="z">A</a><img src="x.png"></body></html>'
    else:
        path = stage.legacy.PARENT_HUB if sample == "historical_hub" else stage.PARENT_STAGE / "index.html"
        raw = stage._read(path)
    original = stage.legacy._HTML
    expected = original(raw)
    with stage._shared_legacy_html_cache() as cache:
        for _ in range(2):
            actual = stage.legacy._HTML(raw)
            assert (actual.ids, actual.links, actual.primary, actual.heads) == (
                expected.ids, expected.links, expected.primary, expected.heads)
            assert type(actual.ids) is set and type(actual.links) is list and type(actual.primary) is list
        assert len(cache.entries) == 1
        if sample == "historical_hub":
            assert stage.legacy._family_links(actual) == stage.legacy._family_links(expected)
            assert actual.heads == 1
    assert stage.legacy._HTML is original


def test_shared_parser_returns_fresh_mutable_copies_without_poisoning_cache():
    raw = b'<head></head><a class="primary-action" href="a/" id="z">A</a>'
    with stage._shared_legacy_html_cache():
        first = stage.legacy._HTML(raw)
        first.ids.clear()
        first.links.append(("base", "href", "foreign/"))
        first.primary.clear()
        first.heads = 99
        second = stage.legacy._HTML(raw)
        assert second.ids == {"z"} and second.links == [("a", "href", "a/")]
        assert second.primary == ["a/"] and second.heads == 1
        assert first.ids is not second.ids and first.links is not second.links and first.primary is not second.primary


@pytest.mark.parametrize("raw", (b'<p id="x" id="y">bad</p>',
    b'<p id="x"></p><p id="x"></p>', b'<base href="https://example.invalid/">', b'\xff'))
def test_shared_parser_preserves_original_rejections_without_caching_errors(raw):
    original = stage.legacy._HTML
    with pytest.raises(Exception) as expected:
        original(raw)
    with stage._shared_legacy_html_cache() as cache:
        for _ in range(2):
            with pytest.raises(type(expected.value)) as actual:
                stage.legacy._HTML(raw)
            assert str(actual.value) == str(expected.value)
        assert not cache.entries and cache.retained_input_bytes == 0
    assert stage.legacy._HTML is original


@pytest.mark.parametrize("raw", (bytearray(b'<p id="x">A</p>'), memoryview(b'<p>A</p>'), None, '<p>A</p>'))
def test_shared_parser_preserves_uncached_non_exact_byte_input_behavior(raw):
    original = stage.legacy._HTML
    try:
        expected = original(raw)
    except Exception as error:
        with stage._shared_legacy_html_cache() as cache:
            with pytest.raises(type(error)) as actual:
                stage.legacy._HTML(raw)
            assert str(actual.value) == str(error) and not cache.entries
    else:
        with stage._shared_legacy_html_cache() as cache:
            actual = stage.legacy._HTML(raw)
            assert (actual.ids, actual.links, actual.primary, actual.heads) == (
                expected.ids, expected.links, expected.primary, expected.heads)
            assert not cache.entries


@pytest.mark.parametrize("fault", ("bytes", "symlink", "ancestor"))
def test_shared_warm_parser_does_not_bypass_real_original_safe_reads(tmp_path, fault):
    root = tmp_path.resolve()
    folder = root / "files"
    folder.mkdir()
    path = folder / "x.html"
    raw = b'<p id="x">Not proof evidence</p>'
    path.write_bytes(raw)
    pin = stage.legacy.Pin(len(raw), stage.sha256(raw).hexdigest())
    original = stage.legacy._HTML
    with stage._shared_legacy_html_cache():
        assert stage.legacy._HTML(stage.legacy._pinned(path, pin, base=root)).ids == {"x"}
        if fault == "bytes":
            path.write_bytes(raw.replace(b'id="x"', b'id="y"'))
        elif fault == "symlink":
            target = root / "target.html"
            target.write_bytes(raw)
            path.unlink()
            path.symlink_to(target)
        else:
            moved = root / "moved"
            folder.rename(moved)
            folder.symlink_to(moved, target_is_directory=True)
        with pytest.raises(stage.legacy.DeliveryError):
            stage.legacy._HTML(stage.legacy._pinned(path, pin, base=root))
    assert stage.legacy._HTML is original


def test_shared_parser_keeps_old_relative_links_and_namespace_checks(monkeypatch):
    old = stage.previous
    raw = b'<a href="target.html#x">A</a>'
    target = b'<p id="x">Target</p>'
    files = {"a/index.html": old._inline(raw), "b/index.html": old._inline(raw),
        "a/target.html": old._inline(target, current=False),
        "b/target.html": old._inline(target, current=False)}
    with stage._shared_legacy_html_cache() as cache:
        assert old.check_links(files) == {"local_links": 2, "local_fragments": 2}
        assert len(cache.entries) == 2
        del files["b/target.html"]
        with pytest.raises(old.DeliveryError, match="b/index.html -> b/target.html"):
            old.check_links(files)
        files["b/target.html"] = old._inline(b'<p id="y">Target</p>', current=False)
        with pytest.raises(old.DeliveryError, match="fragment"):
            old.check_links(files)


def test_shared_parser_entry_and_byte_eviction_keep_original_small_bounds(monkeypatch):
    assert stage.HTML_CACHE_ENTRIES == 64 and stage.HTML_CACHE_INPUT_BYTES == 8 * 1024 * 1024
    with stage._shared_legacy_html_cache() as cache:
        for i in range(65):
            stage.legacy._HTML(('<p id="x%d">A</p>' % i).encode())
        assert len(cache.entries) == 64
        assert cache.retained_input_bytes == sum(key[0] for key in cache.entries)
    monkeypatch.setattr(stage, "HTML_CACHE_INPUT_BYTES", 64)
    with stage._shared_legacy_html_cache() as cache:
        for i in range(3):
            stage.legacy._HTML(('<p id="x%d">%s</p>' % (i, 'x' * 20)).encode())
        assert len(cache.entries) == 1 and cache.retained_input_bytes <= 64
        before = tuple(cache.entries)
        stage.legacy._HTML(b'<p>' + b'x' * 65 + b'</p>')
        assert tuple(cache.entries) == before


def test_shared_parser_nested_scope_rejects_without_disturbing_owner():
    original = stage.legacy._HTML
    with stage._shared_legacy_html_cache():
        owned = stage.legacy._HTML
        with pytest.raises(stage.DeliveryError, match="nested or foreign"):
            with stage._shared_legacy_html_cache():
                pytest.fail("nested cache entered")
        assert stage.legacy._HTML is owned
    assert stage.legacy._HTML is original


def test_shared_parser_restores_original_after_body_exception():
    original = stage.legacy._HTML
    with pytest.raises(RuntimeError, match="deliberate transport-only error"):
        with stage._shared_legacy_html_cache():
            raise RuntimeError("deliberate transport-only error")
    assert stage.legacy._HTML is original


def test_shared_parser_rejects_foreign_entry_without_clobbering_it(monkeypatch):
    foreign = object()
    monkeypatch.setattr(stage.legacy, "_HTML", foreign)
    with pytest.raises(stage.DeliveryError, match="nested or foreign"):
        with stage._shared_legacy_html_cache():
            pytest.fail("foreign parser accepted")
    assert stage.legacy._HTML is foreign


def test_shared_parser_detects_replacement_and_never_overwrites_foreign_owner():
    original, foreign = stage.legacy._HTML, object()
    try:
        with pytest.raises(stage.DeliveryError, match="changed during owned cache"):
            with stage._shared_legacy_html_cache():
                stage.legacy._HTML = foreign
        assert stage.legacy._HTML is foreign
    finally:
        # This test owns the foreign object; production never discards it.
        stage.legacy._HTML = original


def test_shared_scope_keeps_all_old_validation_and_clocks_source_exact():
    import ast
    source = ast.parse(Path(stage.__file__).read_text())
    inventory = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "source_inventory")
    scopes = [n for n in ast.walk(inventory) if isinstance(n, ast.With)
              and any(ast.unparse(x.context_expr) == "_shared_legacy_html_cache()" for x in n.items)]
    assert len(scopes) == 1
    assert ast.unparse(scopes[0].body[0]) == "previous.stage(check=True, api_url=api_url)"
    helper = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "_shared_legacy_html_cache")
    text = ast.unparse(helper)
    assert "signal.alarm" not in text and "setrlimit" not in text and "previous.stage =" not in text
    assert stage.CPU_LIMITS == (170, 175) and stage.WALL_SECONDS == 180 and stage.MAX_RSS == 1536 * 1024 * 1024


@pytest.mark.parametrize("fault", ("same_size_change", "replacement", "symlink", "directory"))
def test_warm_summary_never_bypasses_actual_safe_file_read(tmp_path, monkeypatch, fault):
    monkeypatch.setattr(stage, "ROOT", tmp_path)
    path = tmp_path / "page.html"
    raw = b'<p id="old">Unissued display fixture</p>'
    path.write_bytes(raw)
    item = stage.File(stage._pin(raw), source=path)
    cache = stage._HTMLSummaryCache()
    assert cache.read(item).ids == frozenset({"old"})
    if fault == "same_size_change":
        path.write_bytes(raw.replace(b'old', b'new'))
    elif fault == "replacement":
        other = tmp_path / "other.html"
        other.write_bytes(raw + b'!')
        other.replace(path)
    elif fault == "symlink":
        other = tmp_path / "other.html"
        other.write_bytes(raw)
        path.unlink()
        path.symlink_to(other)
    else:
        path.unlink()
        path.mkdir()
    with pytest.raises((stage.DeliveryError, stage.legacy.DeliveryError)):
        cache.read(item)


def test_warm_summary_authenticates_unchanged_bytes_on_every_use(monkeypatch):
    original, reads = stage._bytes, []
    def read(item):
        reads.append(item)
        return original(item)
    monkeypatch.setattr(stage, "_bytes", read)
    calls = _count_original_html_parses(monkeypatch)
    item = stage._inline(b'<p id="x">Not evidence</p>')
    cache = stage._HTMLSummaryCache()
    first = cache.read(item)
    assert cache.read(item) is first
    assert reads == [item, item] and calls == [item.content]
    assert type(first.ids) is frozenset and type(first.links) is tuple
    with pytest.raises(AttributeError):
        first.ids = frozenset()


def test_identical_bytes_at_different_paths_resolve_relative_links_fresh(monkeypatch):
    calls = _count_original_html_parses(monkeypatch)
    raw = b'<a href="target.html#x">Transport only</a>'
    target = b'<p id="x">Target</p>'
    files = {"a/index.html": stage._inline(raw), "b/index.html": stage._inline(raw),
        "a/target.html": stage._inline(target, current=False),
        "b/target.html": stage._inline(target, current=False)}
    assert stage.check_links(files) == {"local_links": 2, "local_fragments": 2}
    assert calls.count(raw) == calls.count(target) == 1
    del files["b/target.html"]
    with pytest.raises(stage.DeliveryError, match="b/index.html -> b/target.html"):
        stage.check_links(files)
    # Each new invocation reparses; neither a parse cache nor success escapes.
    assert calls.count(raw) == 2


def test_same_page_bytes_cannot_reuse_success_in_changed_fragment_namespace():
    raw = b'<a href="target.html#x">Transport only</a>'
    files = {"index.html": stage._inline(raw),
        "target.html": stage._inline(b'<p id="x">Target</p>', current=False)}
    assert stage.check_links(files)["local_fragments"] == 1
    files["target.html"] = stage._inline(b'<p id="y">Target</p>', current=False)
    with pytest.raises(stage.DeliveryError, match="missing exact public fragment"):
        stage.check_links(files)


def test_forward_fragment_target_parses_once_and_still_checks_outgoing_links(monkeypatch):
    calls = _count_original_html_parses(monkeypatch)
    first = b'<a href="z.html#x">Forward</a>'
    last = b'<p id="x"><a href="target.txt">Outgoing</a></p>'
    files = {"a.html": stage._inline(first), "z.html": stage._inline(last),
        "target.txt": stage._inline(b'Not evidence')}
    assert stage.check_links(files) == {"local_links": 2, "local_fragments": 1}
    assert calls == [first, last]
    del files["target.txt"]
    with pytest.raises(stage.DeliveryError, match="z.html -> target.txt"):
        stage.check_links(files)


def test_summary_lru_entry_eviction_is_bounded_and_refreshes_hits(monkeypatch):
    assert stage.HTML_CACHE_ENTRIES == 64
    assert stage.HTML_CACHE_INPUT_BYTES == 8 * 1024 * 1024
    calls = _count_original_html_parses(monkeypatch)
    items = [stage._inline(('<p id="x%d">Not evidence</p>' % i).encode()) for i in range(65)]
    cache = stage._HTMLSummaryCache()
    for item in items[:64]:
        cache.read(item)
    cache.read(items[0])
    cache.read(items[64])
    assert len(cache.entries) == 64 and len(calls) == 65
    cache.read(items[0])
    assert len(calls) == 65
    cache.read(items[1])
    assert len(calls) == 66 and len(cache.entries) == 64
    assert cache.retained_input_bytes == sum(key[0] for key in cache.entries)


def test_summary_byte_budget_evicts_and_oversized_pages_are_not_retained(monkeypatch):
    monkeypatch.setattr(stage, "HTML_CACHE_INPUT_BYTES", 64)
    calls = _count_original_html_parses(monkeypatch)
    cache = stage._HTMLSummaryCache()
    items = [stage._inline(('<p id="x%d">%s</p>' % (i, 'x' * 20)).encode()) for i in range(3)]
    for item in items:
        cache.read(item)
        assert cache.retained_input_bytes <= 64
    assert len(cache.entries) == 1
    big = stage._inline(b'<p>' + b'x' * 65 + b'</p>')
    cache.read(big)
    cache.read(big)
    assert calls.count(big.content) == 2 and len(cache.entries) == 1
    assert cache.retained_input_bytes == len(items[-1].content)


@pytest.mark.parametrize("raw", (b'<p id="x" id="y">bad</p>',
    b'<p id="x"></p><p id="x"></p>', b'<base href="https://example.invalid/">'))
def test_summary_cache_retains_every_original_parser_rejection(raw):
    with pytest.raises(stage.legacy.DeliveryError):
        stage._HTMLSummaryCache().read(stage._inline(raw))


def registration():
    pin = {"bytes": 1, "sha256": "a" * 64}
    return {"catalog": dict(pin), "channels": dict(pin), "receipt": dict(pin),
        "readers": {phase: dict(pin) for phase in ("gcd-congruence", "polynomial", "research", "completed", "historical")},
        "atlas": {name: dict(pin) for name in stage.ATLAS_FILES}}


@pytest.mark.parametrize("bad", (None, {}, [], True, 1, "stored receipt"))
def test_missing_real_delivery_registration_stops_before_old_stage_or_any_write(monkeypatch, bad):
    monkeypatch.setattr(stage, "REGISTRATION", bad)
    monkeypatch.setattr(stage.previous, "stage", lambda *a, **k: pytest.fail("old stage reached before registration"))
    with pytest.raises(stage.DeliveryError):
        stage.source_inventory()


@pytest.mark.parametrize("field", ("catalog", "channels", "receipt", "readers", "atlas"))
def test_all_registered_release_components_are_mandatory(monkeypatch, field):
    value = registration()
    value.pop(field)
    monkeypatch.setattr(stage, "REGISTRATION", value)
    with pytest.raises(stage.DeliveryError):
        stage.require_registration()


@pytest.mark.parametrize("field", ("gcd-congruence", "polynomial", "research", "completed", "historical"))
def test_all_current_reader_packages_are_mandatory(monkeypatch, field):
    value = registration()
    value["readers"].pop(field)
    monkeypatch.setattr(stage, "REGISTRATION", value)
    with pytest.raises(stage.DeliveryError):
        stage.require_registration()


@pytest.mark.parametrize("field", stage.ATLAS_FILES)
def test_all_current_atlas_files_are_mandatory(monkeypatch, field):
    value = registration()
    value["atlas"].pop(field)
    monkeypatch.setattr(stage, "REGISTRATION", value)
    with pytest.raises(stage.DeliveryError):
        stage.require_registration()


@pytest.mark.parametrize("field,value", (("bytes", 0), ("bytes", True), ("bytes", 1.0),
    ("bytes", 64 * 1024 * 1024 + 1), ("sha256", "A" * 64), ("sha256", "a" * 63), ("sha256", None)))
def test_literal_delivery_pins_use_exact_types_and_unchanged_limits(field, value):
    pin = {"bytes": 1, "sha256": "a" * 64}
    pin[field] = value
    with pytest.raises(stage.DeliveryError):
        stage._valid_pin(pin)


@pytest.mark.parametrize("mode", ("changed", "mutable", "two_sources", "missing_source", "wrong_type"))
def test_inline_file_records_cannot_change_after_identity(mode):
    raw = b"synthetic delivery bytes; not proof evidence"
    item = stage._inline(raw)
    assert stage._bytes(item) == raw
    if mode == "changed": item = stage.File(item.pin, content=raw + b"!")
    elif mode == "mutable": item = stage.File(item.pin, content=bytearray(raw))
    elif mode == "two_sources": item = stage.File(item.pin, source=Path("unread"), content=raw)
    elif mode == "missing_source": item = stage.File(item.pin)
    else: item = SimpleNamespace(pin=item.pin, content=raw)
    with pytest.raises(stage.DeliveryError):
        stage._bytes(item)


def test_original_selector_is_inserted_once_into_actual_supported_html():
    folder = stage.ROOT / "book/_static/constructive-polynomial-division-explorer/polynomial-division-prerequisites/explorer/defined/tag"
    path = sorted(folder.glob("*.html"))[0]
    raw = path.read_bytes()
    name = "polynomial-division-prerequisites/explorer/defined/tag/" + path.name
    insertion = stage.selector._overlay("")
    actual = stage._selector_bytes(name, raw, insertion)
    assert actual.count(b"/proofs/assets/lean-selector.js") == 1
    assert actual.replace(insertion, b"", 1) == raw
    assert stage._selector_bytes(name, actual, insertion) == actual
    assert stage._selector_bytes("checkpoints/old/explorer/defined/tag/TEST.html", raw, insertion) == raw


@pytest.mark.parametrize("fault", ("duplicate", "foreign_config", "missing_panel", "missing_head"))
def test_selector_rejects_unsupported_or_ambiguous_delivery(fault):
    insertion = stage.selector._overlay("")
    marker = stage.selector.THEOREM_PANELS[0]
    raw = b"<html><head></head><body>" + marker + b"</body></html>"
    if fault == "duplicate": raw = raw.replace(b"</head>", insertion + insertion + b"</head>")
    elif fault == "foreign_config": raw = raw.replace(b"</head>", b'<script src="/proofs/assets/lean-selector.js"></script></head>')
    elif fault == "missing_panel": raw = b"<html><head></head><body></body></html>"
    else: raw = raw.replace(b"</head>", b"")
    with pytest.raises(stage.DeliveryError):
        stage._selector_bytes("family/explorer/tag/AB0001.html", raw, insertion)


def test_current_links_and_fragments_are_checked_against_retained_exact_routes():
    files = {
        "index.html": stage._inline(b'<html><head></head><body><a href="old.html#kept">Read</a></body></html>'),
        "old.html": stage._inline(b'<html><head></head><body><p id="kept">Historical</p></body></html>', current=False),
    }
    assert stage.check_links(files) == {"local_links": 1, "local_fragments": 1}
    files["old.html"] = stage._inline(b'<html><head></head><body></body></html>', current=False)
    with pytest.raises(stage.DeliveryError, match="fragment"):
        stage.check_links(files)
    files.pop("old.html")
    with pytest.raises(stage.DeliveryError, match="target"):
        stage.check_links(files)


@pytest.mark.parametrize("check", (None, 0, 1, "yes", [], {}))
def test_staging_mode_is_strict_before_any_external_action(check):
    with pytest.raises(stage.DeliveryError, match="Boolean"):
        stage.stage(check=check)


def test_stage_is_a_new_fixed_tree_and_original_gates_are_unchanged():
    assert stage.STAGE == stage.ROOT / "_deploy/proofs-v34"
    assert stage.PARENT_STAGE == stage.ROOT / "_deploy/proofs-v33"
    assert stage.STAGE != stage.PARENT_STAGE
    assert stage.CPU_LIMITS == (170, 175) and stage.WALL_SECONDS == 180
    assert stage.MAX_RSS == 1536 * 1024 * 1024 and stage.MAX_FILES == 20000


@pytest.mark.parametrize("name", ("constructive_research_publication_v33.py",
                                  "constructive_alpha_v33_publication_process.py"))
def test_nested_parent_presentation_sources_remain_bound_through_final_copy(name):
    path = stage.ROOT / "scripts" / name
    sources = stage._stage_source_paths()
    assert path in sources and len(sources) == len(set(sources))
    pin = stage._pin(stage._read(path))
    assert stage._read(path, pin) == path.read_bytes()
    with pytest.raises(stage.DeliveryError, match="registered delivery bytes changed"):
        stage._read(path, {**pin, "sha256": "0" * 64})


@pytest.mark.parametrize("platform,raw,expected", (("darwin", 1024, 1024), ("linux", 1024, 1048576)))
def test_rss_observations_are_normalized_to_bytes(monkeypatch, platform, raw, expected):
    monkeypatch.setattr(stage.sys, "platform", platform)
    monkeypatch.setattr(stage.resource, "getrusage", lambda _: SimpleNamespace(ru_maxrss=raw))
    assert stage._rss_bytes() == expected


@pytest.mark.parametrize("platform,raw", (("darwin", 0), ("darwin", 1610612737),
                                         ("linux", 0), ("linux", 1572865)))
def test_rss_original_byte_ceiling_cannot_be_bypassed(monkeypatch, platform, raw):
    monkeypatch.setattr(stage.sys, "platform", platform)
    monkeypatch.setattr(stage.resource, "getrusage", lambda _: SimpleNamespace(ru_maxrss=raw))
    with pytest.raises(stage.DeliveryError):
        stage._rss_bytes()


@pytest.mark.parametrize("kind", ("catalog.json", "channels.json", "original-hub.html", "selector.js", "converted-source.html"))
def test_input_binding_rechecks_sources_even_when_output_is_inline(tmp_path, monkeypatch, kind):
    root = tmp_path.resolve()
    monkeypatch.setattr(stage, "ROOT", root)
    path = root / kind
    raw = b"unissued UI source fixture"
    path.write_bytes(raw)
    binding = ({path: stage._pin(raw)}, {root: {kind}})
    stage._rebind_inputs(binding)
    path.write_bytes(b"changed UI source fixture")
    with pytest.raises(ValueError):
        stage._rebind_inputs(binding)


def test_input_binding_rejects_new_tree_entries_without_changing_old_bytes(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(stage, "ROOT", root)
    path = root / "index.html"
    raw = b"<title>Transport-only fixture</title>"
    path.write_bytes(raw)
    binding = ({path: stage._pin(raw)}, {root: {"index.html"}})
    stage._rebind_inputs(binding)
    (root / "late.txt").write_bytes(b"late unrelated entry")
    with pytest.raises(stage.DeliveryError, match="gained or lost"):
        stage._rebind_inputs(binding)


def test_pinned_parent_atlas_relocation_changes_only_its_initial_home_anchor():
    path = stage.ROOT / "book/_static/constructive-research-campaign-v33/index.html"
    raw = path.read_bytes()
    # A literal parent HTML fixture, not a current-release or proof claim.
    raw = raw.replace(b'../constructive-research-explorer-v33/index.html?v=6be052da195a" data-proof-home',
                      b'../constructive-research-explorer-v34/index.html?v=6be052da195a" data-proof-home', 1)
    revision = "6be052da195a"
    before = ('<a href="../constructive-research-explorer-v34/index.html?v='
              + revision + '" data-proof-home>').encode()
    after = ('<a href="../index.html?v=' + revision + '" data-proof-home>').encode()
    actual = stage._public_atlas_html(raw, revision)
    assert raw.count(before) == actual.count(after) == 1
    assert actual.replace(after, before, 1) == raw
    original_scripts = stage.re.findall(rb"<script\b[^>]*>.*?</script>", raw, stage.re.S)
    assert original_scripts
    assert stage.re.findall(rb"<script\b[^>]*>.*?</script>", actual, stage.re.S) == original_scripts
    assert stage.legacy._link_target("grand-campaign/index.html", "../index.html?v=" + revision) == ("index.html", "")


@pytest.mark.parametrize("fault", ("absent", "duplicate", "stale", "already_public", "bad_revision"))
def test_atlas_relocation_rejects_missing_ambiguous_or_foreign_home(fault):
    revision = "a" * 12
    anchor = ('<a href="../constructive-research-explorer-v34/index.html?v='
              + revision + '" data-proof-home>').encode()
    raw = b"<html>" + anchor + b"Home</a></html>"
    if fault == "absent": raw = b"<html></html>"
    elif fault == "duplicate": raw += anchor
    elif fault == "stale": raw = raw.replace(revision.encode(), b"b" * 12)
    elif fault == "already_public": raw += ('<a href="../index.html?v=' + revision + '" data-proof-home>').encode()
    else: revision = "../unsafe"
    with pytest.raises(stage.DeliveryError):
        stage._public_atlas_html(raw, revision)
