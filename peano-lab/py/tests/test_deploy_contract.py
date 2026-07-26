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
    assert 'peano-lab/worker.js  "_deploy/peano-lab/worker.js"' in output
    assert 'peano-lab/.htaccess  "_deploy/peano-lab/.htaccess"' in output
    assert 'peano-lab/py/ "_deploy/peano-lab/py/"' in output
    assert 'peano-lab/vendor/ "_deploy/peano-lab/vendor/"' in output
    assert "shasum -a 256 -c MANIFEST.sha256" in output
    assert (
        '"_deploy/peano-lab/" '
        "lts-faculty.wmi.amu.edu.pl:~/public_html/peano-lab/"
    ) in output


def test_peano_next_differs_only_in_remote_destination() -> None:
    production = _dry_run("deploy-peano")
    staging = _dry_run("deploy-peano-next")

    production_assembly = production.split("rsync -avz --delete", maxsplit=1)[0]
    staging_assembly = staging.split("rsync -avz --delete", maxsplit=1)[0]
    assert staging_assembly == production_assembly
    assert (
        '"_deploy/peano-lab/" '
        "lts-faculty.wmi.amu.edu.pl:~/public_html/peano-lab-next/"
    ) in staging


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


def test_peano_remote_delete_targets_cannot_be_overridden() -> None:
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


def test_shared_vendor_fetch_creates_matching_local_trees() -> None:
    script = (ROOT / "scripts" / "fetch_vendor.sh").read_text(encoding="utf-8")

    assert "V=lab-lambda/vendor" in script
    assert "PEANO_V=peano-lab/vendor" in script
    assert 'rsync -a --delete "$V/" "$PEANO_V/"' in script
    assert "MANIFEST.sha256" in script
    assert "urllib.request" not in script
    assert '["curl", "-fsSL", "--retry", "3", url' in script
    assert 'GF_CSS="$(mktemp)"' in script
    assert "trap 'rm -f \"$GF_CSS\"' EXIT" in script
