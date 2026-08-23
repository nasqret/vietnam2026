"""Static contracts for the Peano Lab staging and deployment targets.

These tests deliberately use ``make -n``: CI must verify the exact assembled
tree and destinations without touching the faculty server.
"""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]


def _dry_run(target: str) -> str:
    result = subprocess.run(
        ["make", "-n", target],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_peano_production_deploy_uses_an_isolated_staging_tree() -> None:
    output = _dry_run("deploy-peano")

    assert 'peano-lab/index.html "_deploy/peano-lab/index.html"' in output
    assert 'peano-lab/.htaccess  "_deploy/peano-lab/.htaccess"' in output
    assert 'peano-lab/worker.js "_deploy/peano-lab/releases/a-' in output
    assert 'peano-lab/APP_MANIFEST.sha256 "_deploy/peano-lab/releases/a-' in output
    assert 'peano-lab/py/ "_deploy/peano-lab/releases/a-' in output
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
    for family in (
        "supplementary-laws",
        "kummer",
        "two-squares",
        "four-squares",
        "lucas",
    ):
        assert f"book/_static/constructive-frontier-explorer/{family}/" in output
        assert f'"_deploy/proofs/{family}/"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


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
