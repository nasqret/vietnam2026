"""Static contracts for the Peano Lab staging and deployment targets.

These tests deliberately use ``make -n``: CI must verify the exact assembled
tree and destinations without touching the faculty server.
"""

from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import ast
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
from urllib.parse import parse_qs, urljoin, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]
FRONTIER = ROOT / "book" / "_static" / "constructive-frontier-explorer"
CURRENT_CAMPAIGN = json.loads(
    (ROOT / "book" / "_static" / "constructive-gaussian-campaign" / "campaign.json").read_bytes()
)
CURRENT_ALPHA_VERSION = CURRENT_CAMPAIGN["meta"]["current_alpha_version"]
CURRENT_ALPHA_CHANNEL = json.loads(
    (ROOT / "artifacts" / "peano-library" / f"channels-{CURRENT_ALPHA_VERSION}.json").read_bytes()
)["channels"]["alpha"]
CURRENT_ALPHA_CATALOG = (
    ROOT / "artifacts" / "peano-library" / "alpha" / f"catalog-{CURRENT_ALPHA_VERSION}.json"
)
CANONICAL_HTML_REVISION = CURRENT_ALPHA_CHANNEL["artifact_sha256"][:12]
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
NEXT_LAYER_FAMILIES = (
    "polynomial-horner",
    "matrix-dot-product",
    "bertrand-prime-chains",
    "continued-fractions",
)
ADVANCED_LAYER_FAMILIES = (
    "matrix-coded-products",
    "euclidean-complexity",
    "binary-modular-exponentiation",
)
TRANSPORT_LAYER_FAMILIES = (
    "binary-length",
    "euclidean-gcd-transport",
    "binary-modular-execution",
)
MILESTONE_CLOSURE_FAMILIES = (
    "euclidean-logarithmic-bound",
    "binary-digit-extraction",
    "primes-three-mod-four",
)
RESEARCH_LAYER_FAMILIES = (
    "matrix-determinant-minors",
    "polynomial-hensel",
    "generalized-crt-fold",
)
BREAKTHROUGH_LAYER_FAMILIES = (
    "matrix-cofactor-expansion",
    "polynomial-taylor-hensel",
    "generalized-crt-compatibility",
)
SECOND_WAVE_FAMILIES = (
    "integer-linear-algebra",
    "hensel-lifting",
    "generalized-crt",
    "multinomial-kummer",
    "prime-count-chebyshev",
    "cornacchia",
    "cauchy-davenport",
)
LOWER_LAYER_FAMILIES = (
    "arithmetic-foundations", "prime-enumeration", "gaussian-integers", "eisenstein-integers",
)
PRIORITY_LAYER_FAMILIES = (
    "prime-valuation-support", "best-approximation", "totient-products",
    "squarefree-kernels", "exponent-lifting",
)
GAUSSIAN_FACTORIZATION_FAMILIES = ("gaussian-factorization",)
CURRENT_PUBLICATION_DIRECTORIES = (
    "constructive-frontier-explorer", "constructive-next-layer-explorer",
    "constructive-advanced-layer-explorer", "constructive-transport-layer-explorer",
    "constructive-milestone-closure-explorer", "constructive-research-layer-explorer",
    "constructive-breakthrough-layer-explorer", "constructive-second-wave-explorer-v30",
    "constructive-lower-layer-explorer-v30", "constructive-priority-layer-explorer-v30",
    "constructive-gaussian-factorization-explorer",
)
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


def test_every_constructive_manifest_and_family_follow_the_actual_sealed_alpha_release() -> None:
    release = CURRENT_CAMPAIGN["ambitious_boundaries"][
        f"alpha_{CURRENT_ALPHA_VERSION}_edition"
    ]
    catalog_digest = sha256(CURRENT_ALPHA_CATALOG.read_bytes()).hexdigest()
    static = ROOT / "book" / "_static"
    historical_manifest = static / "constructive-second-wave-explorer/manifest.json"
    historical = json.loads(historical_manifest.read_bytes())
    assert historical["alpha_edition_version"] == historical["alpha_first_enrolled_version"] == "v27"
    assert historical["catalog_sha256"] == "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
    # Every historical snapshot stays frozen. Only explicitly current
    # successors are staged; a historical directory cannot be relabeled.
    manifests = tuple(static / name / "manifest.json" for name in CURRENT_PUBLICATION_DIRECTORIES)
    routes: set[str] = set()

    assert release["role"] == "current_immutable_release"
    assert release["catalog_sha256"] == CURRENT_ALPHA_CHANNEL["artifact_sha256"] == catalog_digest
    assert release["identity_sha256"] == CURRENT_ALPHA_CHANNEL["edition_identity_sha256"]
    assert release["theorem_count"] == CURRENT_ALPHA_CHANNEL["theorem_count"]
    for path in manifests:
        manifest = json.loads(path.read_bytes())
        assert manifest["alpha_edition_version"] == CURRENT_ALPHA_VERSION, path
        assert manifest.get("catalog_sha256", manifest.get("alpha_catalog_sha256")) == catalog_digest, path
        assert manifest.get(
            "edition_identity_sha256", manifest.get("alpha_edition_identity_sha256")
        ) == CURRENT_ALPHA_CHANNEL["edition_identity_sha256"], path
        for family in manifest["families"]:
            slug = family["slug"]
            assert slug not in routes, f"duplicate constructive campaign route: {slug}"
            assert family.get("alpha_checked_use_node_count", family.get("theorem_count", 0)) > 0
            assert (path.parent / slug / "explorer" / "defined" / "graph.html").is_file()
            routes.add(slug)

    known_routes = (
        set(FRONTIER_FAMILIES)
        | set(NEXT_LAYER_FAMILIES)
        | set(ADVANCED_LAYER_FAMILIES)
        | set(TRANSPORT_LAYER_FAMILIES)
        | set(MILESTONE_CLOSURE_FAMILIES)
        | set(RESEARCH_LAYER_FAMILIES)
        | set(BREAKTHROUGH_LAYER_FAMILIES)
        | set(SECOND_WAVE_FAMILIES)
        | set(LOWER_LAYER_FAMILIES)
        | set(PRIORITY_LAYER_FAMILIES)
        | set(GAUSSIAN_FACTORIZATION_FAMILIES)
    )
    assert known_routes <= routes
    assert len(routes) == 42
    hub = (ROOT / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")
    assert all(f'href="{slug}/?v={CANONICAL_HTML_REVISION}"' in hub for slug in routes)


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
        "alpha-v20-next-layer-proof-bundle-v1.json",
        "alpha-v21-advanced-layer-proof-bundle-v1.json",
        "alpha-v22-transport-layer-proof-bundle-v1.json",
        "alpha-v23-milestone-closure-proof-bundle-v1.json",
        "alpha-v24-research-layer-proof-bundle-v1.json",
        "alpha-v25-breakthrough-layer-proof-bundle-v1.json",
        "alpha-v26-first-wave-proof-bundle-v1.json",
        "alpha-v27-second-wave-proof-bundle-v1.json",
        "alpha-v28-lower-layer-proof-bundle-v1.json",
        "alpha-v29-priority-layer-proof-bundle-v1.json",
        "alpha-v30-gaussian-factorization-proof-bundle-v1.json",
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
    assert "python3 scripts/build_constructive_next_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_transport_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_milestone_closure_explorer.py" in output
    assert "python3 scripts/build_constructive_research_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_breakthrough_layer_explorer.py" in output
    assert "python3 scripts/upgrade_constructive_priority_layer_publication_v30.py" in output
    assert "python3 scripts/build_constructive_gaussian_factorization_explorer.py" in output
    assert "scripts/extend_constructive_gaussian_factorization_campaign.py" in output
    assert "book/_static/constructive-frontier-explorer/assets/" in output
    assert "book/_static/constructive-next-layer-explorer/assets/" in output
    assert "book/_static/constructive-advanced-layer-explorer/assets/" in output
    assert "book/_static/constructive-transport-layer-explorer/assets/" in output
    assert "book/_static/constructive-milestone-closure-explorer/assets/" in output
    assert "book/_static/constructive-research-layer-explorer/assets/" in output
    assert "book/_static/constructive-breakthrough-layer-explorer/assets/" in output
    assert "book/_static/constructive-second-wave-explorer-v30/assets/" in output
    assert "book/_static/constructive-lower-layer-explorer-v30/assets/" in output
    assert "book/_static/constructive-priority-layer-explorer-v30/assets/" in output
    assert "book/_static/constructive-gaussian-factorization-explorer/assets/" in output
    for family in FRONTIER_FAMILIES:
        assert f"book/_static/constructive-frontier-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in NEXT_LAYER_FAMILIES:
        assert f"book/_static/constructive-next-layer-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in ADVANCED_LAYER_FAMILIES:
        assert f"book/_static/constructive-advanced-layer-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in TRANSPORT_LAYER_FAMILIES:
        assert f"book/_static/constructive-transport-layer-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in MILESTONE_CLOSURE_FAMILIES:
        assert f"book/_static/constructive-milestone-closure-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in RESEARCH_LAYER_FAMILIES:
        assert f"book/_static/constructive-research-layer-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in BREAKTHROUGH_LAYER_FAMILIES:
        assert f"book/_static/constructive-breakthrough-layer-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in SECOND_WAVE_FAMILIES:
        assert f"book/_static/constructive-second-wave-explorer-v30/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in LOWER_LAYER_FAMILIES:
        assert f"book/_static/constructive-lower-layer-explorer-v30/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in PRIORITY_LAYER_FAMILIES:
        assert f"book/_static/constructive-priority-layer-explorer-v30/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    for family in GAUSSIAN_FACTORIZATION_FAMILIES:
        assert f"book/_static/constructive-gaussian-factorization-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_v27_check_replays_every_actual_source_suite_serially_and_both_verifiers() -> None:
    output = _dry_run("peano-library-alpha-v27-check")
    source = (ROOT / "peano-lab/py/peano_lab/library/campaign_second_wave_closure.py").read_text()
    parsed = ast.parse(source)
    factory_assignment = next(
        node for node in parsed.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "FACTORIES" for target in node.targets)
    )
    assert isinstance(factory_assignment.value, ast.Tuple)
    modules = tuple(ast.literal_eval(call.args[1]) for call in factory_assignment.value.elts)
    assert len(modules) == len(set(modules)) == 18
    loop = output.split("for suite in", 1)[1].split("done", 1)[0]
    for module in modules:
        assert module in loop
        assert (ROOT / f"peano-lab/py/tests/test_{module}.py").is_file()
    assert 'python3 -m pytest -q --tb=line "tests/test_${suite}.py"' in loop
    assert "|| exit $?" in loop
    assert "scripts/build_peano_library_channels_v27.py --check" in output
    assert "scripts/verify_peano_library_channels_v27.py --verify-roots" in output
    assert "scripts/test_verify_peano_library_channels_v27.py" in output
    assert "tests/test_library_editions_v27_admission.py" in output
    assert "tests/test_campaign_second_wave_closure.py" in output
    assert "tests/test_constructive_campaign_dag.py" in output
    assert "tests/test_constructive_definition_graph.py" in output
    assert "tests/test_constructive_grand_campaign.py" in output
    assert "tests/test_constructive_second_wave_explorer.py" in output
    assert "scripts/upgrade_constructive_second_wave_publication_v28.py --check-historical" in output
    assert "bash scripts/update_peano_app_manifest.sh --check" in output
    assert "peano_lab_bundle_verify" in output
    assert "artifacts/alpha-v27-second-wave-proof-bundle-v1.json" in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_v27_channel_aliases_and_canonical_explorer_build_do_not_deploy() -> None:
    build = _dry_run("peano-library-alpha-v27")
    assert build == _dry_run("peano-library-channels-v27")
    assert _dry_run("peano-library-alpha-v27-check") == _dry_run("peano-library-channels-v27-check")
    assert "scripts/build_peano_library_channels_v27.py" in build
    canonical = _dry_run("book-constructive-second-wave-explorer")
    assert canonical.strip() == "python3 scripts/upgrade_constructive_second_wave_publication_v28.py --check-historical"
    assert "rsync" not in build + canonical


def test_v28_checks_each_math_suite_in_isolation_and_keeps_all_independent_gates() -> None:
    output = _dry_run("peano-library-alpha-v28-check")
    source = (ROOT / "peano-lab/py/peano_lab/library/campaign_lower_layer_closure.py").read_text()
    assignment = next(node for node in ast.parse(source).body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "FACTORIES" for target in node.targets))
    modules = tuple(ast.literal_eval(call.args[1]) for call in assignment.value.elts)
    assert len(modules) == len(set(modules)) == 6
    loop = output.split("for suite in", 1)[1].split("done", 1)[0]
    assert 'python3 -m pytest -q --tb=line "tests/test_${suite}.py"' in loop and "|| exit $?" in loop
    assert all(module in loop for module in modules)
    for gate in (
        "scripts/build_peano_library_channels_v28.py --check",
        "scripts/verify_peano_library_channels_v28.py --verify-roots",
        "scripts/test_verify_peano_library_channels_v28.py",
        "tests/test_library_editions_v28_admission.py", "tests/test_campaign_lower_layer_closure.py",
        "tests/test_constructive_lower_layer_definitions.py", "tests/test_constructive_lower_layer_explorer.py",
        "tests/test_constructive_second_wave_publication_v28.py", "tests/test_constructive_second_wave_explorer.py",
        "tests/test_alpha_v28_ui.py", "tests/test_book_arithmetic_part.py",
        "scripts/extend_constructive_lower_layer_campaign.py --check",
        "scripts/build_constructive_lower_layer_explorer.py --check",
        "scripts/upgrade_constructive_second_wave_publication_v28.py --check-historical",
        "scripts/upgrade_constructive_second_wave_publication_v28.py --check",
        "bash scripts/update_peano_app_manifest.sh --check", "peano_lab_bundle_verify",
        "artifacts/alpha-v28-lower-layer-proof-bundle-v1.json",
    ):
        assert gate in output
    assert output == _dry_run("peano-library-channels-v28-check")
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_v28_build_and_v30_current_publication_targets_never_deploy_implicitly() -> None:
    build = _dry_run("peano-library-alpha-v28")
    assert build == _dry_run("peano-library-channels-v28")
    publication = _dry_run("book-constructive-second-wave-current-explorer")
    lower = _dry_run("book-constructive-lower-layer-explorer")
    assert "scripts/extend_constructive_gaussian_factorization_campaign.py" in publication
    assert "python3 scripts/upgrade_constructive_priority_layer_publication_v30.py" in publication
    assert "rsync" not in publication and "ssh" not in publication
    assert lower.strip() == "python3 scripts/build_constructive_lower_layer_explorer.py --check"
    assert "rsync" not in build + publication + lower


def test_grand_campaign_and_complete_proof_artifacts_stage_with_the_hub() -> None:
    output = _dry_run("stage-proofs")
    page = (ROOT / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")

    assert "scripts/sync_constructive_grand_campaign.py --check" in output
    assert "book/_static/constructive-gaussian-campaign/" in output
    assert "rsync -a --delete book/_static/constructive-grand-campaign/" not in output
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
        "alpha-v20-next-layer-proof-bundle-v1.json",
        "alpha-v21-advanced-layer-proof-bundle-v1.json",
        "alpha-v22-transport-layer-proof-bundle-v1.json",
        "alpha-v23-milestone-closure-proof-bundle-v1.json",
        "alpha-v24-research-layer-proof-bundle-v1.json",
        "alpha-v25-breakthrough-layer-proof-bundle-v1.json",
        "alpha-v26-first-wave-proof-bundle-v1.json",
        "alpha-v27-second-wave-proof-bundle-v1.json",
        "alpha-v28-lower-layer-proof-bundle-v1.json",
        "alpha-v29-priority-layer-proof-bundle-v1.json",
        "alpha-v30-gaussian-factorization-proof-bundle-v1.json",
    ):
        assert f'"_deploy/proofs/artifacts/{filename}"' in output
        assert f'href="artifacts/{filename}"' in page
    assert '"_deploy/proofs/artifacts/alpha-v26-first-wave-receipt.md"' in output
    assert 'href="artifacts/alpha-v26-first-wave-receipt.md"' in page
    assert '"_deploy/proofs/artifacts/alpha-v27-second-wave-receipt.md"' in output
    assert 'href="artifacts/alpha-v27-second-wave-receipt.md"' in page
    assert '"_deploy/proofs/artifacts/alpha-v28-lower-layer-receipt.md"' in output
    assert 'href="artifacts/alpha-v28-lower-layer-receipt.md"' in page
    for stem in ("alpha-v29-priority-layer", "alpha-v30-gaussian-factorization"):
        assert f'"_deploy/proofs/artifacts/{stem}-receipt.md"' in output
        assert f'href="artifacts/{stem}-receipt.md"' in page


def test_proof_explorer_stage_installs_only_the_proof_site_cache_policy() -> None:
    output = _dry_run("stage-proofs")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert 'cp deploy/proofs/.htaccess "_deploy/proofs/.htaccess"' in output
    assert 'cp deploy/site.htaccess "_deploy/proofs/.htaccess"' not in output
    assert "cp deploy/site.htaccess $(STAGE)/.htaccess" in makefile


def test_legacy_book_redirect_is_limited_to_five_real_chapters() -> None:
    policy = (ROOT / "deploy/proofs/.htaccess").read_text(encoding="utf-8")
    rules = [line.strip().split() for line in policy.splitlines()
             if line.strip().startswith("RewriteRule ^arithmetic-library/")]
    assert len(rules) == 1
    directive, pattern, destination, flags = rules[0]
    assert directive == "RewriteRule" and flags == "[R=302,L]"
    assert destination == (
        "https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026/book/arithmetic-library/$1.html"
    )
    allowed = ("quadratic-reciprocity", "defined-proof-explorer", "cell-history-and-lookup",
               "library-editions", "bertrand-campaign")
    assert pattern == "^arithmetic-library/(" + "|".join(allowed) + r")\.html$"
    expression = re.compile(pattern)
    for chapter in allowed:
        match = expression.fullmatch("arithmetic-library/" + chapter + ".html")
        assert match is not None and match.group(1) == chapter
        assert (ROOT / "book/arithmetic-library" / (chapter + ".md")).is_file()
        assert destination.replace("$1", match.group(1)).endswith("/" + chapter + ".html")
    for path in ("arithmetic-library/other.html", "arithmetic-library/quadratic-reciprocity.html/extra",
                 "arithmetic-library/quadratic-reciprocityXhtml", "arithmetic-library/library-editions.html.bak",
                 "assets/explorer.js", "gaussian-factorization/explorer/defined/index.html",
                 "peano-lab/index.html", "api/lean-strands/config", "../arithmetic-library/library-editions.html"):
        assert expression.fullmatch(path) is None


def test_legacy_book_links_also_work_on_static_hosts_without_rewrite_support() -> None:
    chapters = ("quadratic-reciprocity", "defined-proof-explorer", "cell-history-and-lookup",
                "library-editions", "bertrand-campaign")
    directory = ROOT / "deploy/proofs/arithmetic-library"
    assert {path.name for path in directory.iterdir()} == {name + ".html" for name in chapters}
    output = _dry_run("stage-proofs")
    assert 'rsync -a --delete deploy/proofs/arithmetic-library/ "_deploy/proofs/arithmetic-library/"' in output

    class RedirectPage(HTMLParser):
        def __init__(self, source: str) -> None:
            super().__init__(convert_charrefs=True)
            self.elements = []
            self.scripts = []
            self.script = None
            self.feed(source)

        def handle_starttag(self, tag, attrs):
            self.elements.append((tag, dict(attrs)))
            if tag == "script":
                assert self.script is None
                self.script = ""

        def handle_endtag(self, tag):
            if tag == "script":
                self.scripts.append(self.script)
                self.script = None

        def handle_data(self, data):
            if self.script is not None:
                self.script += data

    cases = []
    expected = []
    for chapter in chapters:
        page = RedirectPage((directory / (chapter + ".html")).read_text(encoding="utf-8"))
        target = "https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026/book/arithmetic-library/" + chapter + ".html"
        assert len(page.scripts) == 1
        assert [(tag, attrs) for tag, attrs in page.elements if tag == "link"] == [
            ("link", {"rel": "canonical", "href": target})]
        assert [attrs["href"] for tag, attrs in page.elements if tag == "a"] == [target]
        assert any(tag == "noscript" for tag, _ in page.elements)
        assert any(tag == "meta" and attrs.get("http-equiv") == "refresh"
                   and attrs.get("content") == "0;url=" + target for tag, attrs in page.elements)
        for query, fragment in (("", ""), ("?v=" + CANONICAL_HTML_REVISION, "#theorem-section"),
                                ("?url=https%3A%2F%2Fexample.invalid&x=a%2Fb", "#%CE%A9")):
            cases.append({"source": page.scripts[0], "search": query, "hash": fragment})
            expected.append([target + query + fragment])
    program = r'''
const vm = require("node:vm");
const cases = JSON.parse(process.argv[1]);
const results = cases.map(item => {
  const calls = [];
  const location = {search:item.search, hash:item.hash, replace:value => calls.push(value)};
  Object.defineProperty(location, "href", {get:() => "https://example.invalid/old"});
  new vm.Script(item.source).runInNewContext({window:{location}}, {timeout:1000});
  return calls;
});
process.stdout.write(JSON.stringify(results));
'''
    result = subprocess.run(["node", "-e", program, json.dumps(cases)],
                            check=True, capture_output=True, text=True, timeout=10)
    assert json.loads(result.stdout) == expected


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
    assert f"Independently verified Alpha {CURRENT_ALPHA_VERSION} checked-use theorem family" in page
    assert "not Stable" in page
    assert "frontier-hero" not in page
    assert "Independent closure experiments" not in page
    assert "<progress" not in page


@pytest.mark.parametrize("family", TRANSPORT_LAYER_FAMILIES)
def test_transport_family_page_uses_the_exact_quadratic_reciprocity_design(
    family: str,
) -> None:
    root = ROOT / "book" / "_static" / "constructive-transport-layer-explorer"
    page = (root / family / "index.html").read_text(encoding="utf-8")
    original = (ROOT / "deploy" / "proofs" / "quadratic-reciprocity.html").read_text(
        encoding="utf-8"
    )

    shared_landmarks = (
        '<header class="family-hero">',
        '<div class="shell">',
        '<nav class="crumbs">',
        '<p class="formula">',
        '<p class="lede">',
        '<div class="hero-actions">',
        '<main class="shell family-main">',
        '<section class="view-grid">',
        '<article class="view-card featured">',
        '<section class="release-note">',
    )
    for landmark in shared_landmarks:
        assert landmark in original
        assert landmark in page

    assert f'<body class="family-page {family}-page">' in page
    assert page.count('<article class="view-card') == 3
    assert f'href="../assets/proofs.css?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="explorer/defined/?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="explorer/?v={CANONICAL_HTML_REVISION}"' in page
    assert 'href="explorer/defined/graph.html?target=' in page
    assert "&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus" in page
    assert "&amp;view=prerequisites&amp;definitions=selected&amp;edges=focus" in page
    assert "first admitted v22" in page
    assert f"Independently verified Alpha {CURRENT_ALPHA_VERSION} checked-use theorem family" in page
    assert "independently accept all 240 bundle nodes" in page
    assert "not Stable" in page
    assert 'class="proof-home' not in page
    assert 'class="proof-hero"' not in page
    assert 'class="proof-card"' not in page


@pytest.mark.parametrize(
    ("family", "generation", "first_admitted", "bundle_nodes"),
    tuple(
        (family, "constructive-next-layer-explorer", "v20", 590)
        for family in NEXT_LAYER_FAMILIES
    )
    + tuple(
        (family, "constructive-advanced-layer-explorer", "v21", 209)
        for family in ADVANCED_LAYER_FAMILIES
    ),
)
def test_historical_intermediate_pages_also_share_the_canonical_family_design(
    family: str, generation: str, first_admitted: str, bundle_nodes: int
) -> None:
    page = (ROOT / "book" / "_static" / generation / family / "index.html").read_text(
        encoding="utf-8"
    )

    assert f'<body class="family-page {family}-page">' in page
    assert '<header class="family-hero">' in page
    assert '<nav class="crumbs">' in page
    assert '<main class="shell family-main">' in page
    assert '<section class="view-grid">' in page
    assert page.count('<article class="view-card') == 3
    assert f'href="../assets/proofs.css?v={CANONICAL_HTML_REVISION}"' in page
    assert f"first admitted {first_admitted}" in page
    assert f"Independently verified Alpha {CURRENT_ALPHA_VERSION} checked-use theorem family" in page
    assert f"independently accept all {bundle_nodes} bundle nodes" in page
    assert 'class="proof-hero"' not in page
    assert 'class="proof-card"' not in page


@pytest.mark.parametrize(
    ("family", "root_tag"),
    (
        ("euclidean-logarithmic-bound", "EL0010"),
        ("binary-digit-extraction", "BD0018"),
        ("primes-three-mod-four", "TF0012"),
    ),
)
def test_closed_milestone_page_uses_the_exact_quadratic_reciprocity_design(
    family: str, root_tag: str
) -> None:
    root = ROOT / "book" / "_static" / "constructive-milestone-closure-explorer"
    page = (root / family / "index.html").read_text(encoding="utf-8")
    original = (ROOT / "deploy" / "proofs" / "quadratic-reciprocity.html").read_text(
        encoding="utf-8"
    )

    for landmark in (
        '<header class="family-hero">',
        '<div class="shell">',
        '<nav class="crumbs">',
        '<p class="formula">',
        '<p class="lede">',
        '<div class="hero-actions">',
        '<main class="shell family-main">',
        '<section class="view-grid">',
        '<article class="view-card featured">',
        '<section class="release-note">',
    ):
        assert landmark in original
        assert landmark in page

    assert f'<body class="family-page {family}-page">' in page
    assert page.count('<article class="view-card') == 3
    assert f'href="../assets/proofs.css?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="explorer/defined/?v={CANONICAL_HTML_REVISION}"' in page
    assert f'href="explorer/?v={CANONICAL_HTML_REVISION}"' in page
    assert f"explorer/defined/tag/{root_tag}.html" in page
    assert "&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus" in page
    assert "&amp;view=prerequisites&amp;definitions=selected&amp;edges=focus" in page
    assert "first admitted v23" in page
    assert f"Independently verified Alpha {CURRENT_ALPHA_VERSION} checked-use theorem family" in page
    assert "independently accept all 617 bundle nodes" in page
    assert "not Stable" in page
    assert 'class="proof-hero"' not in page


def test_quadratic_reciprocity_explorer_skill_is_versioned_and_reuses_real_template() -> None:
    skill = ROOT / "skills" / "constructive-proof-explorer"
    entrypoint = (skill / "SKILL.md").read_text(encoding="utf-8")
    reference = (skill / "references" / "quadratic-reciprocity-model.md").read_text(
        encoding="utf-8"
    )
    interface = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert "name: constructive-proof-explorer" in entrypoint
    assert "references/quadratic-reciprocity-model.md" in entrypoint
    assert "scripts/constructive_proof_explorer_template.py" in reference
    assert "deploy/proofs/quadratic-reciprocity.html" in reference
    assert "render_canonical_family_landing" in reference
    assert "$constructive-proof-explorer" in interface
    assert (ROOT / "scripts" / "constructive_proof_explorer_template.py").is_file()


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
    for family in NEXT_LAYER_FAMILIES:
        assert f'href="{family}/?v={CANONICAL_HTML_REVISION}"' in page
    for family in ADVANCED_LAYER_FAMILIES:
        assert f'href="{family}/?v={CANONICAL_HTML_REVISION}"' in page
    for family in TRANSPORT_LAYER_FAMILIES:
        assert f'href="{family}/?v={CANONICAL_HTML_REVISION}"' in page
    for family in MILESTONE_CLOSURE_FAMILIES:
        assert f'href="{family}/?v={CANONICAL_HTML_REVISION}"' in page
    for family in RESEARCH_LAYER_FAMILIES:
        assert f'href="{family}/?v={CANONICAL_HTML_REVISION}"' in page
    for family in BREAKTHROUGH_LAYER_FAMILIES:
        assert f'href="{family}/?v={CANONICAL_HTML_REVISION}"' in page
    assert f"All {CURRENT_ALPHA_CHANNEL['theorem_count']:,} theorems have checked-use authority" in page
    assert "432 unchanged Stable theorems" in page
    assert "arbitrary signed multiplication is now proved" in page
    assert "candidate-progress" not in page
    assert "33/44" not in page
    assert "80/196" not in page


def test_public_proof_hub_links_every_family_to_the_multiscale_campaign() -> None:
    page = (ROOT / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")

    assert f'href="grand-campaign/?v={CANONICAL_HTML_REVISION}"' in page
    for family in ("F02", "F03", "F04", "F05", "F07", "F08", "F11", "F12"):
        assert (
            f'href="grand-campaign/?view=family&amp;focus={family}'
            f'&amp;v={CANONICAL_HTML_REVISION}"'
        ) in page
    for milestone in (
        "A02", "A08", "T12", "T13", "G023", "G024", "G025", "G033", "G034",
        "G043", "G044", "G061", "G064", "G071", "G101", "G102",
    ):
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
    catalog = CURRENT_ALPHA_CATALOG
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
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    edition = manifest["alpha_edition_version"]
    catalog = ROOT / "artifacts" / "peano-library" / "alpha" / f"catalog-{edition}.json"
    source_html_revision = sha256(catalog.read_bytes()).hexdigest()[:12]
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
            assert query.get("v") == [source_html_revision], (relative, href)
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



@pytest.mark.parametrize("version,stem,count", (("v29", "priority_layer", 11), ("v30", "gaussian_factorization", 7)))
def test_new_release_targets_replay_all_factories_and_both_independent_verifiers(version, stem, count):
    from importlib import import_module
    closure = import_module("peano_lab.library.campaign_" + stem + "_closure")
    output = _dry_run("peano-library-alpha-" + version + "-check")
    assert output == _dry_run("peano-library-channels-" + version + "-check")
    assert len(closure.FACTORIES) == count
    loop = output.split("for suite in", 1)[1].split("done", 1)[0]
    for factory in closure.FACTORIES:
        assert factory.module in loop
        assert (ROOT / f"peano-lab/py/tests/test_{factory.module}.py").is_file()
    assert 'python3 -m pytest -q --tb=line "tests/test_${suite}.py"' in loop
    assert "|| exit $?" in loop
    for gate in (
        f"scripts/build_peano_library_channels_{version}.py --check",
        f"scripts/verify_peano_library_channels_{version}.py --verify-roots",
        f"scripts/test_verify_peano_library_channels_{version}.py",
        f"tests/test_library_editions_{version}_admission.py",
        f"tests/test_campaign_{stem}_closure.py",
        f"tests/test_constructive_{stem}_definitions.py",
        f"scripts/extend_constructive_{stem}_campaign.py --check",
        f"scripts/build_constructive_{stem}_explorer.py --check",
        "peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify",
        f"alpha-{version}-{stem.replace('_', '-')}-proof-bundle-v1.json",
    ):
        assert gate in output
    if version == "v30":
        assert "tests/test_lean_certified_export.py" in output
        assert "tests/test_lean_proof_strand_cli.py" in output
        assert "tests/test_lean_presentation_cli.py" in output
        assert "tests/test_constructive_exact_graph_navigation.py" in output
        assert "tests/test_constructive_publication_json_encoding.py" in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_current_atlas_is_separate_and_all_historical_atlases_are_preserved():
    output = _dry_run("stage-proofs")
    assert 'rsync -a --delete book/_static/constructive-gaussian-campaign/' in output
    assert '"_deploy/proofs/grand-campaign/"' in output
    assert "scripts/extend_constructive_gaussian_factorization_campaign.py --check" in output
    assert "scripts/sync_constructive_grand_campaign.py --check" in output
    for directory in ("constructive-grand-campaign", "constructive-priority-campaign"):
        assert (ROOT / "book/_static" / directory / "campaign.json").is_file()
    assert "deploy-peano" not in output


def test_current_publication_never_rewrites_the_frozen_flagship_or_lower_layer_trees():
    output = _dry_run("stage-proofs")
    for name in ("bertrand_proof", "bertrand_defined", "pa_proof", "pa_defined"):
        command = f"python3 scripts/build_{name}_explorer.py --check"
        assert command in output
        assert all(line.endswith("--check") for line in output.splitlines()
                   if f"scripts/build_{name}_explorer.py" in line)
    assert _dry_run("book-constructive-lower-layer-explorer").strip().endswith(
        "scripts/build_constructive_lower_layer_explorer.py --check"
    )


def test_v30_gates_cover_all_current_presentations_and_immutable_app_bytes():
    output = _dry_run("peano-library-alpha-v30-check")
    layers = ("frontier", "next_layer", "advanced_layer", "transport_layer",
              "milestone_closure", "research_layer", "breakthrough_layer")
    loop = output.split("for layer in", 1)[1].split("done", 1)[0]
    assert loop.split(";", 1)[0].split() == list(layers)
    assert 'python3 "scripts/build_constructive_${layer}_explorer.py" --check || exit $?' in loop
    tests = output.rsplit("for suite in", 1)[1].split("done", 1)[0]
    expected = [f"constructive_{name}_explorer" for name in layers]
    expected.extend(("constructive_next_layer_public_site",
                     "constructive_research_publication_v24",
                     "constructive_breakthrough_publication_v25"))
    assert set(tests.split(";", 1)[0].replace("\\", " ").split()) == set(expected)
    assert 'python3 -m pytest -q --tb=line "tests/test_${suite}.py"' in tests
    assert "|| exit $?" in tests
    assert "bash scripts/update_peano_app_manifest.sh --check" in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def _collected_release_windows(suite: str, selections: list[str]) -> dict:
    # Collect once, with no fixture/proof execution, and use pytest's own
    # keyword matcher for every actual Make selector. Separate executions
    # retain fresh-process isolation without repeating expensive collection.
    program = '''import json, sys, pytest
from _pytest.mark import KeywordMatcher
from _pytest.mark.expression import Expression
selections = json.loads(sys.argv[1])
class Coverage:
    def pytest_collection_finish(self, session):
        items = session.items
        windows = [[item.nodeid for item in items
                    if Expression.compile(selection).evaluate(KeywordMatcher.from_item(item))]
                   for selection in selections]
        print("PEANO_WINDOWS=" + json.dumps({"complete": [item.nodeid for item in items], "windows": windows}))
raise SystemExit(pytest.main(["--collect-only", "-q", sys.argv[2]], plugins=[Coverage()]))
'''
    result = subprocess.run([sys.executable, "-c", program, json.dumps(selections), suite],
                            cwd=ROOT / "peano-lab/py", text=True, capture_output=True,
                            timeout=45, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    records = [line.removeprefix("PEANO_WINDOWS=") for line in result.stdout.splitlines()
               if line.startswith("PEANO_WINDOWS=")]
    assert len(records) == 1
    return json.loads(records[0])


def test_next_layer_release_windows_cover_every_collected_case_exactly_once() -> None:
    output = _dry_run("peano-library-alpha-v30-check")
    header = output.split("for selection in", 1)[1].split("; do", 1)[0]
    selections = shlex.split(header.replace("\\\n", ""))
    assert len(selections) == len(set(selections)) == 7
    suite = "tests/test_constructive_next_layer_explorer.py"
    coverage = _collected_release_windows(suite, selections)
    complete, windows = coverage["complete"], coverage["windows"]
    assert len(complete) == len(set(complete))
    assert all(node.startswith(suite + "::") for node in complete)
    assert len(complete) == 261
    assert tuple(map(len, windows)) == (133, 58, 4, 1, 12, 52, 1)
    assert Counter(node for window in windows for node in window) == Counter(complete)
    assert '-k "${selection}"' in output and "|| exit $?" in output


@pytest.mark.parametrize("layer,count", (("research", 108), ("breakthrough", 129)))
def test_large_current_catalog_negatives_have_complete_fresh_process_windows(layer, count) -> None:
    output = _dry_run("peano-library-alpha-v30-check")
    condition = ('elif test "${suite}" = constructive_research_layer_explorer || '
                 'test "${suite}" = constructive_breakthrough_layer_explorer; then')
    branch = output.split(condition, 1)[1].split("else", 1)[0]
    header = branch.split("for selection in", 1)[1].split("; do", 1)[0]
    selections = shlex.split(header.replace("\\\n", ""))
    assert selections == ["current_authority_corruption", "not current_authority_corruption"]
    assert 'PYTHONMALLOC=pymalloc python3 -m pytest' in branch
    assert '-k "${selection}"' in branch and "|| exit $?" in branch
    suite = f"tests/test_constructive_{layer}_layer_explorer.py"
    coverage = _collected_release_windows(suite, selections)
    complete, windows = coverage["complete"], coverage["windows"]
    assert len(complete) == len(set(complete)) == count
    assert all(node.startswith(suite + "::") for node in complete)
    assert tuple(map(len, windows)) == (30, count - 30)
    assert Counter(node for window in windows for node in window) == Counter(complete)


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
