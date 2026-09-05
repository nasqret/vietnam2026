"""Regression: release banners must not steal the wide theorem-grid column."""
from html.parser import HTMLParser
from pathlib import Path
import json
import pytest

from proof_explorer_layout import LayoutError, NOTICE_STYLE, repair_release_notices
import stage_proof_explorer_layout as stage

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("layout", ("pd-theorem-layout", "pa-proof-layout", "pd-definition-page", ""))
@pytest.mark.parametrize("version", ("v31", "v32", "v33", "v34", "v35"))
def test_notice_gets_one_full_width_row_without_moving_proof_or_sidebar(layout, version):
    raw = ('<!doctype html><html><head></head><body><main class="' + layout + '">'
        '<p class="pa-callout pd-callout" data-current-release="' + version + '">Release</p>'
        '<div><section><h2>Proof</h2><pre><code>intro p\nexact hp</code></pre></section></div>'
        '<aside>Receipt</aside></main></body></html>').encode()
    fixed, notices, changes = repair_release_notices(raw)
    assert notices == changes == 1
    assert fixed.replace((' style="' + NOTICE_STYLE + '"').encode(), b"", 1) == raw
    assert repair_release_notices(fixed) == (fixed, 1, 0)
    assert NOTICE_STYLE == "grid-column: 1 / -1;"  # spans the explicit grid, including its single mobile track


def test_inline_javascript_proof_strings_comments_and_nested_notices_are_byte_identical():
    raw = b'''<html><head><script>var x = '<p data-current-release="v34">not markup</p>';</script></head>
<body><main><!-- <p data-current-release="v34">comment</p> -->
<p data-current-release="v34">Actual notice</p><div><p data-current-release="v34">Nested example</p>
<pre><code>&lt;p data-current-release="v34"&gt;literal proof data&lt;/p&gt;</code></pre></div>
<svg><defs><marker><path d="M 0 0 L 1 1"/></marker></defs></svg></main></body></html>'''
    fixed, notices, changes = repair_release_notices(raw)
    expected = raw.replace(b'<p data-current-release="v34">Actual notice',
        b'<p data-current-release="v34" style="grid-column: 1 / -1;">Actual notice', 1)
    assert fixed == expected and notices == changes == 1


def test_unicode_crlf_and_original_attribute_spelling_are_preserved():
    raw = '<html>\r\n<body><main>∀ p\r\n<p DATA-current-release=\'v34\'>α → β</p></main></body></html>'.encode()
    fixed, notices, changes = repair_release_notices(raw)
    assert fixed.replace(b' style="grid-column: 1 / -1;"', b'', 1) == raw
    assert notices == changes == 1


@pytest.mark.parametrize("tag", (
    '<p data-current-release="v34" style="grid-column:2">x</p>',
    '<p data-current-release="v34" data-current-release="v33">x</p>',
    '<p data-current-release="v34"/>',
    '<p data-current-release="v34">x</div>',
))
def test_unexpected_or_ambiguous_notice_markup_fails_closed(tag):
    with pytest.raises(LayoutError):
        repair_release_notices(('<html><body><main>' + tag + '</main></body></html>').encode())


@pytest.mark.parametrize("slug", ("quadratic-reciprocity", "bertrand-postulate", "two-squares", "four-squares", "lucas"))
@pytest.mark.parametrize("edition", ("", "defined/"))
def test_actual_flagship_and_campaign_pages_keep_all_original_proof_bytes(slug, edition):
    folder = ROOT / 'book/_static/constructive-historical-explorers-v34' / slug / 'explorer' / edition / 'tag'
    page = folder / 'PA00A7.html' if slug == 'quadratic-reciprocity' else next(iter(sorted(folder.glob('*.html'))))
    raw = page.read_bytes()
    fixed, notices, changed = repair_release_notices(raw)
    assert notices == changed == 1
    assert fixed.replace(b' style="grid-column: 1 / -1;"', b'', 1) == raw
    assert repair_release_notices(fixed) == (fixed, 1, 0)


def fixture_base(tmp_path):
    base = tmp_path / 'proofs-v34'
    base.mkdir()
    pages = {
        'family/explorer/defined/tag/T.html': b'<html><head></head><body><main class="pd-theorem-layout"><p data-current-release="v34">Release</p><div>Proof</div><aside>Receipt</aside></main></body></html>',
        'family/api/proof.json': b'{"proof":"untouched"}\n',
        'assets/defined-explorer.css': b'.pd-theorem-layout { display: grid; }\n',
        'assets/defined-explorer.js': b'"use strict";\n',
    }
    for name, raw in pages.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    manifest = dict(schema='peano-lab-alpha-v34-public-delivery-v1', delivery_metadata_only=True,
        alpha_admission_performed=False, stable_admission_performed=False,
        current_files={name: stage.pin(raw) for name, raw in pages.items()})
    path = base / stage.BASE_MANIFEST
    path.parent.mkdir()
    path.write_bytes(stage.canonical(manifest))
    return base, stage.sha256(path.read_bytes()).hexdigest()


def test_staging_preserves_base_proofs_and_original_assets_and_is_recheckable(tmp_path):
    base, digest = fixture_base(tmp_path)
    before = stage.inventory(base)
    output = tmp_path / 'proofs-layout-v1'
    result = stage.stage(base, output, accepted_sha256=digest)
    assert result['changed_pages'] == result['notices'] == 1
    assert stage.inventory(base) == before
    for name in ('family/api/proof.json', 'assets/defined-explorer.css', 'assets/defined-explorer.js', stage.BASE_MANIFEST):
        assert (output / name).read_bytes() == (base / name).read_bytes()
    assert stage.stage(base, output, check=True, accepted_sha256=digest)['manifest_sha256'] == result['manifest_sha256']
    with pytest.raises(LayoutError, match='already exists'):
        stage.stage(base, output, accepted_sha256=digest)


@pytest.mark.parametrize("fault", ("proof", "manifest", "extra-output", "symlink", "same-root"))
def test_delivery_cannot_launder_modified_proofs_or_overwrite_its_base(tmp_path, fault):
    base, digest = fixture_base(tmp_path)
    output = tmp_path / 'proofs-layout-v1'
    if fault == 'proof':
        (base / 'family/api/proof.json').write_bytes(b'{"proof":"changed"}')
    elif fault == 'manifest':
        digest = '0' * 64
    elif fault == 'symlink':
        (base / 'linked.html').symlink_to(base / 'family/explorer/defined/tag/T.html')
    elif fault == 'same-root':
        output = base
    else:
        stage.stage(base, output, accepted_sha256=digest)
        (output / 'unexpected.txt').write_text('no')
    with pytest.raises(LayoutError):
        stage.stage(base, output, check=(fault == 'extra-output'), accepted_sha256=digest)
