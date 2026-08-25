"""Static contracts for the Peano Lab staging and deployment targets.

These tests deliberately use ``make -n``: CI must verify the exact assembled
tree and destinations without touching the faculty server.
"""

from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
from urllib.parse import parse_qs, urljoin, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]
FRONTIER = ROOT / "book" / "_static" / "constructive-frontier-explorer"
CANONICAL_HTML_REVISION = "f1c3d3fba013"
FRONTIER_FAMILIES = (
    "supplementary-laws",
    "kummer",
    "two-squares",
    "four-squares",
    "lucas",
    "pythagorean-fermat-four",
)
FRONTIER_TAG_PREFIXES = {
    "supplementary-laws": "SL",
    "kummer": "KU",
    "two-squares": "TS",
    "four-squares": "FS",
    "lucas": "LU",
    "pythagorean-fermat-four": "PF",
}
CANONICAL_FRONTIER_ASSETS = (
    ("defined-explorer.css", "defined/assets/explorer.css"),
    ("defined-explorer.js", "defined/assets/explorer.js"),
    ("exact-explorer.css", "assets/explorer.css"),
    ("exact-explorer.js", "assets/explorer.js"),
)


def _dry_run(target: str) -> str:
    result = subprocess.run(
        ["make", "-n", target],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _versioned_frontier_asset(filename: str, prefix: str) -> str:
    digest = sha256((FRONTIER / "assets" / filename).read_bytes()).hexdigest()[:12]
    return f"{prefix}/{filename}?v={digest}"


def test_peano_production_deploy_uses_an_isolated_staging_tree() -> None:
    output = _dry_run("deploy-peano")

    assert 'peano-lab/index.html "_deploy/peano-lab/index.html"' in output
    assert 'peano-lab/.htaccess  "_deploy/peano-lab/.htaccess"' in output
    assert 'peano-lab/worker.js "_deploy/peano-lab/releases/a-' in output
    assert 'peano-lab/APP_MANIFEST.sha256 "_deploy/peano-lab/releases/a-' in output
    assert 'peano-lab/py/ "_deploy/peano-lab/releases/a-' in output
    assert "research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json" in output
    assert "/proof-artifacts/quadratic-reciprocity-proof-bundle-v1.json" in output
    for filename in (
        "supplementary-laws-proof-bundle-v1.json",
        "lucas-proof-bundle-v1.json",
        "kummer-proof-bundle-v1.json",
        "bertrand-proof-bundle-v1.json",
        "four-square-proof-bundle-v1.json",
        "two-square-proof-bundle-v1.json",
        "alpha-v19-residual-proof-bundle-v1.json",
        "alpha-v19-campaign-frontier-proof-bundle-v1.json",
    ):
        assert f"research/arithmetic-library/artifacts/{filename}" in output
        assert f"/proof-artifacts/{filename}" in output
    assert 'peano-lab/vendor/ "_deploy/peano-lab/vendor/"' in output
    assert "bash scripts/verify_peano_vendor_manifest.sh" in output
    assert "bash scripts/update_peano_app_manifest.sh --check" in output
    assert "--exclude '/tests/***'" in output
    assert "--include '*.py' --exclude '*'" in output
    assert 'grep -Fq \'const APP_ROOT="releases/a-' in output
    assets = output.index('"_deploy/peano-lab/releases"')
    index = output.index('"_deploy/peano-lab/index.html" lts-faculty')
    assert assets < index
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/peano-lab/" in output
    assert "rsync -avz --delete" not in output


def test_peano_next_differs_only_in_remote_destination() -> None:
    production = _dry_run("deploy-peano")
    staging = _dry_run("deploy-peano-next")

    staging_assembly = staging.split("rsync -avz", maxsplit=1)[0]
    production_assembly = production.split("rsync -avz", maxsplit=1)[0]
    assert staging_assembly == production_assembly
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/peano-lab-next/" in staging
    assert staging.index('"_deploy/peano-lab/releases"') < staging.index(
        '"_deploy/peano-lab/index.html" lts-faculty'
    )


def test_peano_stage_path_cannot_be_overridden_to_a_broader_delete_target() -> None:
    result = subprocess.run(
        ["make", "-n", "STAGEPEANO=/tmp/unsafe", "stage-peano"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "/tmp/unsafe" not in result.stdout
    assert 'rm -rf "_deploy/peano-lab"' in result.stdout


def test_peano_remote_targets_cannot_be_overridden() -> None:
    production = subprocess.run(
        ["make", "-n", "PEANO=~/public_html", "deploy-peano"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    staging = subprocess.run(
        ["make", "-n", "PEANONEXT=~/public_html", "deploy-peano-next"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/peano-lab/" in production
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/peano-lab-next/" in staging
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/\n" not in production
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/\n" not in staging


def test_local_peano_server_serves_the_staged_release_tree() -> None:
    output = _dry_run("peano-serve")

    assert 'cd "_deploy/peano-lab" && python3 -m http.server 8002' in output
    assert "cd peano-lab && python3 -m http.server 8002" not in output


def test_proof_explorer_deploy_uses_an_isolated_staging_tree() -> None:
    output = _dry_run("deploy-proofs")

    assert 'rm -rf "_deploy/proofs"' in output
    assert "python3 scripts/build_bertrand_defined_explorer.py" in output
    assert "book/_static/pa-proof-explorer/" in output
    assert "book/_static/bertrand-proof-explorer/" in output
    assert '"_deploy/proofs/quadratic-reciprocity/explorer/"' in output
    assert '"_deploy/proofs/bertrand-postulate/explorer/"' in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/proofs/" in output
    assert "rsync -avz --delete \"_deploy/proofs/\"" in output


def test_all_constructive_frontier_families_stage_without_remote_deployment() -> None:
    output = _dry_run("stage-proofs")

    assert "python3 scripts/build_constructive_frontier_explorer.py" in output
    assert "book/_static/constructive-frontier-explorer/assets/" in output
    for family in FRONTIER_FAMILIES:
        assert f"book/_static/constructive-frontier-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_grand_campaign_and_complete_proof_artifacts_stage_with_the_hub() -> None:
    output = _dry_run("stage-proofs")
    page = (ROOT / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")

    assert "scripts/sync_constructive_grand_campaign.py --check" in output
    assert "book/_static/constructive-grand-campaign/" in output
    assert '"_deploy/proofs/grand-campaign/"' in output
    assert '"_deploy/proofs/artifacts/quadratic-reciprocity-proof-bundle-v1.json"' in output
    assert '"_deploy/proofs/artifacts/quadratic-reciprocity-closure-receipt.md"' in output
    assert f'href="grand-campaign/?v={CANONICAL_HTML_REVISION}"' in page
    assert 'href="artifacts/quadratic-reciprocity-proof-bundle-v1.json"' in page
    for filename in (
        "supplementary-laws-proof-bundle-v1.json",
        "lucas-proof-bundle-v1.json",
        "kummer-proof-bundle-v1.json",
        "bertrand-proof-bundle-v1.json",
        "four-square-proof-bundle-v1.json",
        "two-square-proof-bundle-v1.json",
    ):
        assert f'"_deploy/proofs/artifacts/{filename}"' in output
        assert f'href="artifacts/{filename}"' in page


def test_proof_explorer_stage_installs_only_the_proof_site_cache_policy() -> None:
    output = _dry_run("stage-proofs")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert 'cp deploy/proofs/.htaccess "_deploy/proofs/.htaccess"' in output
    assert 'cp deploy/site.htaccess "_deploy/proofs/.htaccess"' not in output
    assert "cp deploy/site.htaccess $(STAGE)/.htaccess" in makefile


def test_proof_site_cache_headers_preserve_https_and_stay_extension_scoped() -> None:
    proof_policy = (ROOT / "deploy" / "proofs" / ".htaccess").read_text(
        encoding="utf-8"
    )
    main_site_policy = (ROOT / "deploy" / "site.htaccess").read_text(
        encoding="utf-8"
    )

    html_policy = (
        '  <FilesMatch "\\.(?:html?)$">\n'
        '    Header always set Cache-Control "no-store, no-cache, '
        'must-revalidate, max-age=0"\n'
        '    Header always set Pragma "no-cache"\n'
        '    Header always set Expires "0"\n'
        "  </FilesMatch>"
    )
    asset_policy = (
        '  <FilesMatch "\\.(?:css|js|json)$">\n'
        '    Header always set Cache-Control "no-cache, must-revalidate, '
        'max-age=0"\n'
        "  </FilesMatch>"
    )

    assert main_site_policy.strip() in proof_policy
    assert '<IfModule mod_headers.c>\n' in proof_policy
    assert html_policy in proof_policy
    assert asset_policy in proof_policy
    assert proof_policy.count("Header always set Cache-Control") == 2
    assert "Cache-Control" not in main_site_policy


@pytest.mark.parametrize(("filename", "canonical_relative"), CANONICAL_FRONTIER_ASSETS)
def test_frontier_assets_are_identical_to_original_proof_explorer_assets(
    filename: str, canonical_relative: str
) -> None:
    canonical = ROOT / "book" / "_static" / "pa-proof-explorer" / canonical_relative

    assert (FRONTIER / "assets" / filename).read_bytes() == canonical.read_bytes()


@pytest.mark.parametrize("family", FRONTIER_FAMILIES)
def test_frontier_family_page_matches_original_proof_family_layout(family: str) -> None:
    page = (FRONTIER / family / "index.html").read_text(encoding="utf-8")
    established_layout = (
        f'<link rel="stylesheet" href="../assets/proofs.css?v={CANONICAL_HTML_REVISION}">',
        '<header class="family-hero">',
        '<div class="shell">',
        '<nav class="crumbs">',
        '<div class="hero-actions">',
        '<main class="shell family-main">',
        '<section class="view-grid">',
        '<article class="view-card featured">',
        '<section class="release-note">',
    )

    assert f'<body class="family-page {family}-page">' in page
    for marker in established_layout:
        assert marker in page
    assert page.count('<article class="view-card') == 3
    assert f'href="explorer/defined/?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="explorer/?v={CANONICAL_HTML_REVISION}"' in page
    assert 'href="explorer/defined/graph.html?target=' in page
    assert f'&amp;v={CANONICAL_HTML_REVISION}"' in page
    assert 'href="explorer/defined/tag/' in page
    assert f'.html?v={CANONICAL_HTML_REVISION}"' in page
    assert "dependency-curried kernel-checked theorem body" in page
    assert "Independently verified Alpha v19 checked-use theorem family" in page
    assert "not Stable" in page
    assert "frontier-hero" not in page
    assert "Independent closure experiments" not in page
    assert "<progress" not in page


@pytest.mark.parametrize("family", FRONTIER_FAMILIES)
def test_frontier_family_preserves_original_nested_explorer_routes(family: str) -> None:
    family_directory = FRONTIER / family
    exact_edition = family_directory / "explorer" / "index.html"
    defined_library = family_directory / "explorer" / "defined" / "index.html"
    defined_graph = family_directory / "explorer" / "defined" / "graph.html"

    assert (family_directory / "api" / "corpus.json").is_file()
    assert exact_edition.is_file()
    assert defined_library.is_file()
    assert defined_graph.is_file()

    with exact_edition.open(encoding="utf-8") as stream:
        exact_header = stream.read(16_384)
    with defined_graph.open(encoding="utf-8") as stream:
        graph_header = stream.read(16_384)

    exact_stylesheet = _versioned_frontier_asset("exact-explorer.css", "../../assets")
    exact_script = _versioned_frontier_asset("exact-explorer.js", "../../assets")
    defined_stylesheet = _versioned_frontier_asset(
        "defined-explorer.css", "../../../assets"
    )
    defined_script = _versioned_frontier_asset(
        "defined-explorer.js", "../../../assets"
    )

    assert f'href="{exact_stylesheet}"' in exact_header
    assert f'src="{exact_script}"' in exact_header
    assert '<body class="pa-proof-site" data-page="index"' in exact_header
    assert "data-proof-dashboard" in exact_header
    assert f'href="defined/?v={CANONICAL_HTML_REVISION}"' in exact_header
    assert f'href="{defined_stylesheet}"' in graph_header
    assert f'src="{defined_script}"' in graph_header
    assert '<body class="pa-defined-proof-site" data-page="graph"' in graph_header
    assert f'data-family="{family}"' in exact_header
    assert f'data-family="{family}"' in graph_header


@pytest.mark.parametrize("family", FRONTIER_FAMILIES)
def test_frontier_graph_restores_original_definition_aware_controls(family: str) -> None:
    graph = FRONTIER / family / "explorer" / "defined" / "graph.html"
    with graph.open(encoding="utf-8") as stream:
        header = stream.read(16_384)

    for marker in (
        'class="pd-graph-page" data-defined-graph',
        'class="pd-graph-controls" data-graph-form',
        "data-graph-target",
        "data-graph-view",
        "data-graph-definitions",
        "data-graph-edges",
        "data-graph-svg",
        "data-graph-open",
        "data-example-form",
        "window.PA_DEFINED_GRAPH=",
    ):
        assert marker in header


@pytest.mark.parametrize("family", FRONTIER_FAMILIES)
def test_frontier_theorems_and_definitions_have_dedicated_canonical_pages(
    family: str,
) -> None:
    explorer = FRONTIER / family / "explorer"
    exact_tags = {page.name for page in (explorer / "tag").glob("*.html")}
    defined_tags = {page.name for page in (explorer / "defined" / "tag").glob("*.html")}
    definitions = tuple((explorer / "defined" / "definition").glob("*.html"))

    assert exact_tags
    assert exact_tags == defined_tags
    assert all(tag.startswith(FRONTIER_TAG_PREFIXES[family]) for tag in exact_tags)
    assert definitions

    first_tag = min(exact_tags)
    exact_theorem = (explorer / "tag" / first_tag).read_text(encoding="utf-8")
    defined_theorem = (explorer / "defined" / "tag" / first_tag).read_text(
        encoding="utf-8"
    )
    definition = definitions[0].read_text(encoding="utf-8")
    defined_index = (explorer / "defined" / "index.html").read_text(encoding="utf-8")
    exact_index = (explorer / "index.html").read_text(encoding="utf-8")

    assert '<body class="pa-proof-site" data-page="theorem"' in exact_theorem
    assert (
        f'href="{_versioned_frontier_asset("exact-explorer.css", "../../../assets")}"'
        in exact_theorem
    )
    assert '<body class="pa-defined-proof-site" data-page="theorem"' in defined_theorem
    assert (
        f'href="{_versioned_frontier_asset("defined-explorer.css", "../../../../assets")}"'
        in defined_theorem
    )
    assert '<body class="pa-defined-proof-site" data-page="definition"' in definition
    assert f'href="tag/{first_tag}?v={CANONICAL_HTML_REVISION}"' in exact_index
    assert f'href="tag/{first_tag}?v={CANONICAL_HTML_REVISION}"' in defined_index
    assert (
        f'href="definition/{definitions[0].name}?v={CANONICAL_HTML_REVISION}"'
        in defined_index
    )


@pytest.mark.parametrize("family", FRONTIER_FAMILIES)
def test_frontier_defined_library_restores_original_searchable_reading_surface(
    family: str,
) -> None:
    page = (FRONTIER / family / "explorer" / "defined" / "index.html").read_text(
        encoding="utf-8"
    )

    stylesheet = _versioned_frontier_asset("defined-explorer.css", "../../../assets")
    script = _versioned_frontier_asset("defined-explorer.js", "../../../assets")

    assert f'href="{stylesheet}"' in page
    assert f'src="{script}"' in page
    assert '<body class="pa-defined-proof-site" data-page="index"' in page
    assert '<header class="pd-header pd-hero">' in page
    assert '<main data-defined-dashboard>' in page
    assert '<section class="pd-controls">' in page
    assert '<section class="pd-results">' in page
    assert "data-search" in page
    assert "data-kind" in page
    assert "data-clear" in page
    assert "data-count" in page
    assert 'data-entry data-kind="definition"' in page
    assert 'data-entry data-kind="theorem"' in page
    assert 'href="graph.html?target=' in page
    assert "conservative definition · not a theorem" in page
    if family == "pythagorean-fermat-four":
        assert "checked-use authorized; not Stable" in page
        assert "no checked-use authority" not in page
    else:
        assert "no checked-use authority" in page


def test_public_proof_hub_keeps_original_cards_without_experiment_progress() -> None:
    page = (ROOT / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")

    assert '<header class="hero">' in page
    assert '<section class="family-grid" aria-label="Proof families">' in page
    assert f'href="assets/proofs.css?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="quadratic-reciprocity/?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="bertrand-postulate/?v={CANONICAL_HTML_REVISION}"' in page
    for family in FRONTIER_FAMILIES:
        assert f'href="{family}/?v={CANONICAL_HTML_REVISION}"' in page
    assert "candidate-progress" not in page
    assert "33/44" not in page
    assert "80/196" not in page


def test_public_proof_hub_links_every_family_to_the_multiscale_campaign() -> None:
    page = (ROOT / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")

    assert f'href="grand-campaign/?v={CANONICAL_HTML_REVISION}"' in page
    for family in ("F02", "F03", "F04", "F05", "F07", "F08"):
        assert (
            f'href="grand-campaign/?view=family&amp;focus={family}'
            f'&amp;v={CANONICAL_HTML_REVISION}"'
        ) in page
    for milestone in ("A02", "A08", "G033", "G034", "G043", "G044", "G061", "G064"):
        assert (
            f'href="grand-campaign/?view=goal&amp;focus={milestone}'
            f'&amp;v={CANONICAL_HTML_REVISION}"'
        ) in page
    assert "These are research targets, not claims of completed proofs" in page
    assert "definition-to-definition arrows" in page


@pytest.mark.parametrize(
    ("landing", "family", "milestone", "root_tag"),
    (
        ("quadratic-reciprocity.html", "F05", "G043", "PA00FW"),
        ("bertrand-postulate.html", "F03", "A02", "BT0127"),
    ),
)
def test_flagship_landings_preserve_design_and_expose_all_research_scales(
    landing: str, family: str, milestone: str, root_tag: str
) -> None:
    page = (ROOT / "deploy" / "proofs" / landing).read_text(encoding="utf-8")

    assert '<header class="family-hero">' in page
    assert '<section class="view-grid">' in page
    assert f'view=family&amp;focus={family}&amp;v={CANONICAL_HTML_REVISION}' in page
    assert f'view=goal&amp;focus={milestone}&amp;v={CANONICAL_HTML_REVISION}' in page
    assert (
        f'explorer/defined/graph.html?target={root_tag}'
        '&amp;view=neighborhood&amp;definitions=visible&amp;edges=focus'
    ) in page
    assert f'href="../?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="explorer/defined/?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="explorer/?v={CANONICAL_HTML_REVISION}"' in page
    assert (
        f'href="explorer/defined/tag/{root_tag}.html?'
        f'v={CANONICAL_HTML_REVISION}"'
    ) in page
    assert f'&amp;v={CANONICAL_HTML_REVISION}"' in page
    assert "Zoom between mathematical scales" in page


def test_html_navigation_cache_revision_tracks_current_alpha_catalog_not_asset() -> None:
    catalog = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v19.json"
    asset = (
        ROOT / "book" / "_static" / "pa-proof-explorer" / "defined" / "assets"
        / "explorer.js"
    )

    assert sha256(catalog.read_bytes()).hexdigest()[:12] == CANONICAL_HTML_REVISION
    assert sha256(asset.read_bytes()).hexdigest()[:12] == "1b95ce228950"
    assert sha256(asset.read_bytes()).hexdigest()[:12] != CANONICAL_HTML_REVISION


@pytest.mark.parametrize(
    ("route", "source", "tag", "family", "milestone"),
    (
        (
            "quadratic-reciprocity",
            "pa-proof-explorer",
            "PA00FW",
            "F05",
            "G043",
        ),
        ("bertrand-postulate", "bertrand-proof-explorer", "BT0127", "F03", "A02"),
    ),
)
def test_flagship_campaign_links_resolve_after_deployment_at_every_depth(
    route: str, source: str, tag: str, family: str, milestone: str
) -> None:
    class Anchors(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.links: list[str] = []

        def handle_starttag(self, element: str, attrs) -> None:
            href = dict(attrs).get("href")
            if element == "a" and href and "grand-campaign/" in href:
                self.links.append(href)

    campaign_path = (
        ROOT / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
    )
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    assert (campaign_path.parent / "index.html").is_file()
    family_ids = {item["id"] for item in campaign["families"]}
    goal_ids = {item["id"] for item in campaign["nodes"]}
    root = ROOT / "book" / "_static" / source
    relatives = (
        "index.html",
        "graph.html",
        f"tag/{tag}.html",
        "defined/index.html",
        "defined/graph.html",
        f"defined/tag/{tag}.html",
        "defined/definition/PD0004.html",
    )

    for relative in relatives:
        parser = Anchors()
        parser.feed((root / relative).read_text(encoding="utf-8"))
        assert parser.links, (source, relative)
        views = set()
        deployed_page = (
            "https://bnaskrecki.faculty.wmi.amu.edu.pl"
            f"/proofs/{route}/explorer/{relative}"
        )
        for href in parser.links:
            target = urlsplit(urljoin(deployed_page, href))
            assert target.path == "/proofs/grand-campaign/", (relative, href)
            query = parse_qs(target.query)
            assert query.get("v") == [CANONICAL_HTML_REVISION], (relative, href)
            view = query.get("view", ["global"])[0]
            focus = query.get("focus", [None])[0]
            views.add(view)
            if view == "family":
                assert focus == family and focus in family_ids
            elif view == "goal":
                assert focus == milestone and focus in goal_ids
            elif view == "domain":
                assert focus == "D02"
            elif view == "definition":
                assert focus in campaign["definitions"]
            else:
                assert view == "global" and focus is None
        assert {"global", "domain", "family", "goal"}.issubset(views)
        if relative.endswith("definition/PD0004.html"):
            assert "definition" in views


def test_proof_explorer_deploy_paths_cannot_be_overridden() -> None:
    output = subprocess.run(
        [
            "make",
            "-n",
            "PROOFS=~/public_html",
            "STAGEPROOFS=/tmp/unsafe",
            "deploy-proofs",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    assert "/tmp/unsafe" not in output
    assert 'rm -rf "_deploy/proofs"' in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/proofs/" in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/\n" not in output


def test_shared_vendor_fetch_creates_matching_local_trees() -> None:
    script = (ROOT / "scripts" / "fetch_vendor.sh").read_text(encoding="utf-8")

    assert "V=lab-lambda/vendor" in script
    assert "PEANO_V=peano-lab/vendor" in script
    assert "PEANO_VENDOR_ID=v-85fb3352e49c" in script
    assert "LC_ALL=C sort -k2" in script
    assert 'rsync -a --delete --exclude MANIFEST.sha256 "$V/" "$PEANO_V/$PEANO_VENDOR_ID/"' in script
    assert '"v-$VENDOR_DIGEST" != "$PEANO_VENDOR_ID"' in script
    assert 'rm -rf "$PEANO_V"' not in script
    assert "MANIFEST.sha256" in script
    assert "urllib.request" not in script
    assert '["curl", "-fsSL", "--retry", "3", url' in script
    assert 'GF_CSS="$(mktemp)"' in script
    assert "trap 'rm -f \"$GF_CSS\"' EXIT" in script


def test_release_verifiers_are_canonical_and_shell_valid() -> None:
    app = ROOT / "scripts" / "update_peano_app_manifest.sh"
    vendor = ROOT / "scripts" / "verify_peano_vendor_manifest.sh"
    delivery = ROOT / "scripts" / "verify_peano_delivery.sh"

    assert "LC_ALL=C sort -k2" in app.read_text(encoding="utf-8")
    assert "LC_ALL=C sort -k2" in vendor.read_text(encoding="utf-8")
    delivery_source = delivery.read_text(encoding="utf-8")
    assert "%{size_download}" in delivery_source
    assert "size < 3000000" in delivery_source
    assert "APP_PIDS" in delivery_source
    for script in (app, vendor, delivery):
        result = subprocess.run(
            ["bash", "-n", str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
