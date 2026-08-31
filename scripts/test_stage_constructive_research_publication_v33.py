"""Literal delivery diagnostics; no fixture grants proof authority."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import stage_constructive_research_publication_v33 as stage


def registration():
    pin = {"bytes": 1, "sha256": "a" * 64}
    return {"catalog": dict(pin), "channels": dict(pin), "receipt": dict(pin),
        "readers": {phase: dict(pin) for phase in ("polynomial", "research", "completed", "historical")},
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


@pytest.mark.parametrize("field", ("polynomial", "research", "completed", "historical"))
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
    assert stage.STAGE == stage.ROOT / "_deploy/proofs-v33"
    assert stage.PARENT_STAGE == stage.ROOT / "_deploy/proofs-v32"
    assert stage.STAGE != stage.PARENT_STAGE
    assert stage.CPU_LIMITS == (170, 175) and stage.WALL_SECONDS == 180
    assert stage.MAX_RSS == 1536 * 1024 * 1024 and stage.MAX_FILES == 20000


@pytest.mark.parametrize("name", ("constructive_research_publication_v32.py",
                                  "constructive_alpha_v32_publication_process.py"))
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
    path = stage.ROOT / "book/_static/constructive-research-campaign-v32/index.html"
    raw = path.read_bytes()
    # A literal parent HTML fixture, not a current-release or proof claim.
    raw = raw.replace(b'../constructive-research-explorer-v32/index.html?v=41b9f387d88a" data-proof-home',
                      b'../constructive-research-explorer-v33/index.html?v=41b9f387d88a" data-proof-home', 1)
    revision = "41b9f387d88a"
    before = ('<a href="../constructive-research-explorer-v33/index.html?v='
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
    anchor = ('<a href="../constructive-research-explorer-v33/index.html?v='
              + revision + '" data-proof-home>').encode()
    raw = b"<html>" + anchor + b"Home</a></html>"
    if fault == "absent": raw = b"<html></html>"
    elif fault == "duplicate": raw += anchor
    elif fault == "stale": raw = raw.replace(revision.encode(), b"b" * 12)
    elif fault == "already_public": raw += ('<a href="../index.html?v=' + revision + '" data-proof-home>').encode()
    else: revision = "../unsafe"
    with pytest.raises(stage.DeliveryError):
        stage._public_atlas_html(raw, revision)
