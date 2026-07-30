"""Executable contracts for the one-time WMI model-v3 corpus-seal job."""

from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
JOB = REPOSITORY_ROOT / "slurm" / "peano_wmi_seal_v3_corpus.sbatch"
CLI = REPOSITORY_ROOT / "scripts" / "seal_peano_v3_corpus.py"
MODULE = REPOSITORY_ROOT / "training" / "peano_policy" / "corpus_seal.py"
COMMON = REPOSITORY_ROOT / "scripts" / "wmi_common.sh"
REMOTE_SUBMIT = REPOSITORY_ROOT / "scripts" / "submit_wmi_slurm_job.sh"
SYNC = REPOSITORY_ROOT / "scripts" / "wmi_sync_project.sh"
HEREDOC = "PEANO_CORPUS_SEAL_LAUNCHER"
CORPUS_FIXTURE_TEST = Path(__file__).with_name("test_peano_policy_corpus_seal.py")
EXPECTED_ARTIFACT_HASHES = {
    "balanced-raw-traces.jsonl": "a44ddce9a31130a45d355e1fb50eb27856e226ab53ac756508e4411abb388897",
    "balanced-session-metadata.jsonl": "8cba2105b623aa745041b30ecab549596d214a28588f8dbb5dbb9c99e61f7289",
    "balanced-source-manifest.json": "77aa015c9428b7f34895d8df1176d6601e6d853d248fbc8d2e3da398ecbd9082",
    "combined-metadata-manifest.json": "306c7e195ebd4e6a5047794fed1a9aad9fcf73ea463e1ea41bd8397bb37ec036",
    "library-raw-traces.jsonl": "89a67806ba6a074db8008754f2c1446308829f3f3fc664f6d7c9b4b40bda529a",
    "library-session-metadata.jsonl": "b0fbf0b83162c4fbe941895bab74bf4291ab4e7837f2caad8b908f3467c53241",
    "library-source-manifest.json": "56fd066324542bf519d60717cd3c207edf1d3f41878f1ea304778d63d9b27d7e",
    "manifest.json": "ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983",
    "session-metadata.jsonl": "b56cffb1fcc32212de04bdb6762087c9761177853d765933d6edb7b529858b73",
    "test.jsonl": "c4477c38124457880cdf7883782fa28213f0a6414e1194c182713ecafd8925cc",
    "train.jsonl": "626bcf4456efd98eae80828efceb9b89386e6ef83be463251fc1d07b3c2ff15e",
    "val.jsonl": "784512bbcb15b3d46fc7333fd3f917fa440d5d1d263385b7d2c16e9a40f0dd27",
}
EXPECTED_DATASET_ATTESTATION_SHA256 = (
    "4e1cf0d00725a739d6f371062ff2079cfb9bc3e36daf4f4219cbbe1399a68a12"
)
EXPECTED_TOKEN_AUDIT_SHA256 = (
    "c290b285eabcf9d39ab13b4d6f0f194588541484390d35c00681041979e2f8d8"
)
EXPECTED_RUNTIME_SMOKE_SHA256 = (
    "86cc35bfcf2d5ff51931c140f3eb7168e3f641e1f80d54a3984dba9e49e40749"
)


def _load_corpus_fixture_module():
    specification = importlib.util.spec_from_file_location(
        "_peano_corpus_seal_fixture_support",
        CORPUS_FIXTURE_TEST,
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


CORPUS_FIXTURES = _load_corpus_fixture_module()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _launcher_source() -> str:
    source = JOB.read_text(encoding="utf-8")
    opening = f"<<'{HEREDOC}'\n"
    closing = f"\n{HEREDOC}\n"
    assert source.count(opening) == 1
    before, separator, remainder = source.partition(opening)
    assert separator and before
    launcher, separator, _after = remainder.partition(closing)
    assert separator
    assert "# PEANO_CORPUS_SEAL_LAUNCHER_BEGIN" in launcher
    assert "# PEANO_CORPUS_SEAL_LAUNCHER_END" in launcher
    return launcher + "\n"


def _exact_stage(tmp_path: Path) -> tuple[Path, Path, Path, str, str]:
    root = tmp_path / "bootstrap"
    cli = root / "scripts" / CLI.name
    module = root / "training" / "peano_policy" / MODULE.name
    cli.parent.mkdir(parents=True)
    module.parent.mkdir(parents=True)
    shutil.copyfile(CLI, cli)
    shutil.copyfile(MODULE, module)
    return root, cli, module, _sha256(cli), _sha256(module)


def _run_launcher(
    root: Path,
    cli_sha256: str,
    module_sha256: str,
    *arguments: str,
    isolated: bool = True,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if isolated:
        command.extend(("-I", "-B", "-S"))
    command.extend(("-", str(root), cli_sha256, module_sha256, *arguments))
    return subprocess.run(
        command,
        input=_launcher_source(),
        cwd=root.parent,
        check=False,
        capture_output=True,
        text=True,
    )


def _run_launcher_raw(
    *arguments: str,
    isolated: bool = True,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if isolated:
        command.extend(("-I", "-B", "-S"))
    command.extend(("-", *arguments))
    return subprocess.run(
        command,
        input=_launcher_source(),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _anchor_arguments(
    manifest_sha256: str,
    data_sha256s: dict[str, str],
    report_sha256s: dict[str, str],
) -> list[str]:
    arguments = [
        "--dataset-manifest-sha256",
        manifest_sha256,
        "--dataset-attestation-sha256",
        report_sha256s["dataset_attestation"],
        "--token-audit-sha256",
        report_sha256s["token_audit"],
        "--runtime-smoke-sha256",
        report_sha256s["runtime_smoke"],
    ]
    for name in sorted(data_sha256s):
        arguments.extend(("--artifact-sha256", f"{name}={data_sha256s[name]}"))
    return arguments


def test_job_pins_historical_inputs_and_current_two_source_program() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert "#SBATCH --partition=cpu" in source
    assert "#SBATCH --gpus" not in source
    assert "#SBATCH --cpus-per-task=2" in source
    assert "#SBATCH --mem=16G" in source
    assert "#SBATCH --time=04:00:00" in source
    assert (
        "readonly historical_source_commit="
        "5faa3d27cbaf522198ffa1bdcd11fa9d57341658"
    ) in source
    assert "readonly historical_prepare_job=173040" in source
    assert (
        "readonly destination="
        "checkpoints/corpora/peano-policy-v3-173040"
    ) in source
    assert f"readonly expected_cli_sha256={_sha256(CLI)}" in source
    assert f"readonly expected_module_sha256={_sha256(MODULE)}" in source
    assert (
        "readonly expected_manifest_sha256="
        + EXPECTED_ARTIFACT_HASHES["manifest.json"]
    ) in source
    names_block = source.split("readonly -a artifact_names=(\n", 1)[1].split(
        "\n)", 1
    )[0]
    hashes_block = source.split("readonly -a artifact_hashes=(\n", 1)[1].split(
        "\n)", 1
    )[0]
    names = [line.strip() for line in names_block.splitlines()]
    hashes = [line.strip() for line in hashes_block.splitlines()]
    assert dict(zip(names, hashes, strict=True)) == EXPECTED_ARTIFACT_HASHES
    assert (
        "readonly expected_dataset_attestation_sha256="
        + EXPECTED_DATASET_ATTESTATION_SHA256
    ) in source
    assert (
        "readonly expected_token_audit_sha256="
        + EXPECTED_TOKEN_AUDIT_SHA256
    ) in source
    assert (
        "readonly expected_runtime_smoke_sha256="
        + EXPECTED_RUNTIME_SMOKE_SHA256
    ) in source
    assert "PENDING_AFTER_173040_DATASET_ATTESTATION_SHA256" not in source
    assert "PENDING_AFTER_173040_TOKEN_AUDIT_SHA256" not in source
    assert "PENDING_AFTER_173040_RUNTIME_SMOKE_SHA256" not in source
    assert source.index("require_sha256_anchor dataset_attestation") < source.index(
        'cd "$project_root"'
    )
    assert "sacct -n -X -j \"$historical_prepare_job\"" in source
    assert "historical_state\" != COMPLETED" in source
    for stem in (
        "dataset-attestation",
        "token-audit",
        "prepare-runtime",
    ):
        assert f"peano-wmi-v3-{stem}-${{historical_prepare_job}}.json" in source


def test_all_report_hashes_are_admitted_before_any_wmi_operation() -> None:
    source = JOB.read_text(encoding="utf-8")
    first_wmi_operation = source.index('cd "$project_root"')
    for role in ("dataset_attestation", "token_audit", "runtime_smoke"):
        assert source.index(f"require_sha256_anchor {role}") < first_wmi_operation
    assert "PENDING_AFTER_173040" not in source


def test_job_retains_bootstrap_and_has_create_or_report_recovery_lanes() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert "mktemp -d" in source
    assert "mktemp -u" not in source
    assert "peano-v3-seal-bootstrap-${SLURM_JOB_ID}.XXXXXX" in source
    assert 'test "$(cd "$project_root/tmp" && pwd -P)" = "$project_root/tmp"' in source
    assert source.count("install -m 0444") == 2
    assert '"$bootstrap_root/scripts/seal_peano_v3_corpus.py"' in source
    assert '"$bootstrap_root/training/peano_policy/corpus_seal.py"' in source
    assert "__init__.py" not in source
    assert "__pycache__" not in source
    assert "rm -rf" not in source
    assert "retained bootstrap:" in source
    assert 'chmod 0555 \\\n  "$bootstrap_root/scripts"' in source
    assert 'destination_exists=false' in source
    assert 'if [ "$destination_exists" = false ]; then' in source
    destination_classification = source.index("destination_exists=false")
    creation_input_guard = source.index(
        'if [ "$destination_exists" = false ]; then',
        destination_classification,
    )
    assert destination_classification < source.index(
        'for report in "$dataset_attestation" "$token_audit" "$runtime_smoke"',
        creation_input_guard,
    )
    assert creation_input_guard < source.index(
        "mapfile -t observed_artifacts", creation_input_guard
    )
    assert "Recovery is deliberately\n# verify-only" in source
    assert source.index("run_seal_cli create") < source.index("run_seal_cli verify")
    assert source.index("run_seal_cli verify") < source.index("run_seal_cli report")
    assert "publish the one-line operator report" not in source
    assert "preflight_recovery_publication.py run" in source
    assert source.count("preflight_recovery_publication.py verify") == 2
    assert source.index("preflight_recovery_publication.py") < source.index(
        "run_seal_cli create"
    )
    assert 'stat -c \'%d\' "$project_root/checkpoints/corpora"' in source
    assert 'stat -c \'%d\' "$project_root/logs"' in source
    assert 'if [ "$seal_parent_device" != "$report_parent_device" ]; then' in source


def test_job_embeds_isolated_stable_read_then_in_memory_execution() -> None:
    source = JOB.read_text(encoding="utf-8")
    launcher = _launcher_source()
    assert '"$wmi_python" -I -B -S -' in source
    assert 'wmi_python="$(peano_wmi_current_python)"' in source
    assert "python3 -I -B -S -" not in source
    assert "O_NOFOLLOW" in launcher
    assert "before.st_nlink != 1" in launcher
    assert "identity(before) != identity(opened)" in launcher
    assert "identity(opened) != identity(after_open)" in launcher
    assert "identity(after_open) != identity(after_path)" in launcher
    assert "hashlib.sha256(cli_source).hexdigest()" in launcher
    assert "compile(\n    cli_source" in launcher
    assert "exec(code, namespace)" in launcher
    assert '"__name__": "__main__"' in launcher
    assert '"--standalone-root"' in launcher
    assert '"--standalone-cli-sha256"' in launcher
    assert '"--standalone-module-sha256"' in launcher


def test_actual_launcher_reaches_real_cli_without_executing_its_path(
    tmp_path: Path,
) -> None:
    root, _cli, _module, cli_sha256, module_sha256 = _exact_stage(tmp_path)
    completed = _run_launcher(
        root,
        cli_sha256,
        module_sha256,
        "verify",
        "--seal",
        str(root / "missing-seal"),
    )
    assert completed.returncode == 2
    assert "Peano v3 corpus seal failed" in completed.stderr
    assert "missing-seal" in completed.stderr
    assert not list(root.rglob("__pycache__"))


def test_launcher_creates_then_freshly_verifies_and_recovers_report(
    tmp_path: Path,
) -> None:
    bundle = CORPUS_FIXTURES._fixture_bundle(tmp_path / "fixture")
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    manifest_sha256, data_sha256s, report_sha256s = CORPUS_FIXTURES._hash_anchors(
        bundle
    )
    anchors = _anchor_arguments(manifest_sha256, data_sha256s, report_sha256s)
    root, _cli, _module, cli_sha256, module_sha256 = _exact_stage(
        tmp_path / "stage"
    )
    report = tmp_path / "fixture" / "logs" / "seal-report-100.json"
    try:
        created = _run_launcher(
            root,
            cli_sha256,
            module_sha256,
            "create",
            "--artifact-dir",
            str(bundle["artifact_dir"]),
            "--dataset-attestation",
            str(bundle["dataset_attestation"]),
            "--token-audit",
            str(bundle["token_audit"]),
            "--runtime-smoke",
            str(bundle["runtime_smoke"]),
            "--destination",
            str(destination),
            "--source-commit",
            str(bundle["source_commit"]),
            "--prepare-job-id",
            str(bundle["prepare_job_id"]),
            "--publication-profile",
            "native-no-replace-rename-v1",
            *anchors,
        )
        assert created.returncode == 0, created.stderr
        assert destination.is_dir()
        assert not report.exists()  # crash window after irreversible seal rename

        # A true recovery may run after mutable historical inputs have been
        # retired.  Only the sealed copies plus literal anchors remain needed.
        artifact_dir = bundle["artifact_dir"]
        assert isinstance(artifact_dir, Path)
        artifact_dir.rename(artifact_dir.with_name("retired-artifacts"))
        for key in ("dataset_attestation", "token_audit", "runtime_smoke"):
            original_report = bundle[key]
            assert isinstance(original_report, Path)
            original_report.rename(original_report.with_suffix(".retired"))

        verified = _run_launcher(
            root,
            cli_sha256,
            module_sha256,
            "verify",
            "--seal",
            str(destination),
            "--source-commit",
            str(bundle["source_commit"]),
            "--prepare-job-id",
            str(bundle["prepare_job_id"]),
            *anchors,
        )
        assert verified.returncode == 0, verified.stderr
        assert "verified" in verified.stdout

        recovered = _run_launcher(
            root,
            cli_sha256,
            module_sha256,
            "report",
            "--seal",
            str(destination),
            "--report",
            str(report),
            "--source-commit",
            str(bundle["source_commit"]),
            "--prepare-job-id",
            str(bundle["prepare_job_id"]),
            "--publisher-job-id",
            "100",
            "--publication-profile",
            "native-no-replace-rename-v1",
            *anchors,
        )
        assert recovered.returncode == 0, recovered.stderr
        assert b'"job_id":"100"' in report.read_bytes()
        before = (report.stat().st_ino, report.read_bytes())
        repeated = _run_launcher(
            root,
            cli_sha256,
            module_sha256,
            "report",
            "--seal",
            str(destination),
            "--report",
            str(report),
            "--source-commit",
            str(bundle["source_commit"]),
            "--prepare-job-id",
            str(bundle["prepare_job_id"]),
            "--publisher-job-id",
            "100",
            "--publication-profile",
            "native-no-replace-rename-v1",
            *anchors,
        )
        assert repeated.returncode == 0, repeated.stderr
        assert (report.stat().st_ino, report.read_bytes()) == before
    finally:
        if report.exists():
            os.chmod(report, 0o600)
        CORPUS_FIXTURES._unlock_tree(destination)


def test_launcher_rejects_missing_isolation_before_cli_execution(
    tmp_path: Path,
) -> None:
    root, _cli, _module, cli_sha256, module_sha256 = _exact_stage(tmp_path)
    completed = _run_launcher(
        root,
        cli_sha256,
        module_sha256,
        "verify",
        "--seal",
        str(root / "missing-seal"),
        isolated=False,
    )
    assert completed.returncode != 0
    assert "requires python -I -B -S" in completed.stderr
    assert "Peano v3 corpus seal failed" not in completed.stderr


def test_launcher_rejects_missing_arguments_and_malformed_hash(
    tmp_path: Path,
) -> None:
    missing = _run_launcher_raw(cwd=tmp_path)
    assert missing.returncode != 0
    assert "requires ROOT CLI_SHA256 MODULE_SHA256 and a CLI command" in missing.stderr

    root, _cli, _module, _cli_sha256, module_sha256 = _exact_stage(tmp_path)
    malformed = _run_launcher_raw(
        str(root),
        "ABC",
        module_sha256,
        "verify",
        cwd=tmp_path,
    )
    assert malformed.returncode != 0
    assert "CLI digest must be one lowercase SHA-256 value" in malformed.stderr


def test_launcher_rejects_digest_mismatch_before_cli_execution(
    tmp_path: Path,
) -> None:
    root = tmp_path / "bootstrap"
    cli = root / "scripts" / CLI.name
    cli.parent.mkdir(parents=True)
    marker = tmp_path / "executed"
    cli.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('bad', encoding='utf-8')\n",
        encoding="utf-8",
    )
    completed = _run_launcher(root, "0" * 64, "1" * 64, "verify")
    assert completed.returncode != 0
    assert "staged CLI digest mismatch" in completed.stderr
    assert not marker.exists()


@pytest.mark.parametrize("link_kind", ("symlink", "hardlink"))
def test_launcher_rejects_linked_cli(tmp_path: Path, link_kind: str) -> None:
    root = tmp_path / "bootstrap"
    cli = root / "scripts" / CLI.name
    cli.parent.mkdir(parents=True)
    source = tmp_path / "aliased-cli.py"
    source.write_text("print('must not execute')\n", encoding="utf-8")
    if link_kind == "symlink":
        cli.symlink_to(source)
    else:
        os.link(source, cli)
    completed = _run_launcher(root, _sha256(source), "1" * 64, "verify")
    assert completed.returncode != 0
    assert "staged CLI" in completed.stderr
    assert "must not execute" not in completed.stdout


def test_real_cli_rejects_extra_bootstrap_inventory_via_launcher(
    tmp_path: Path,
) -> None:
    root, _cli, _module, cli_sha256, module_sha256 = _exact_stage(tmp_path)
    (root / "unexpected.py").write_text("raise SystemExit('bad')\n", encoding="utf-8")
    completed = _run_launcher(
        root,
        cli_sha256,
        module_sha256,
        "verify",
        "--seal",
        str(root / "missing-seal"),
    )
    assert completed.returncode == 2
    assert "inventory differs from the reviewed two-file program" in completed.stderr
    assert "bad" not in completed.stderr


def test_launcher_executes_reviewed_bytes_after_they_replace_their_path(
    tmp_path: Path,
) -> None:
    root = tmp_path / "bootstrap"
    cli = root / "scripts" / CLI.name
    cli.parent.mkdir(parents=True)
    replacement_marker = tmp_path / "replacement-executed"
    replacement_source = (
        "from pathlib import Path\n"
        f"Path({str(replacement_marker)!r}).write_text('bad', encoding='utf-8')\n"
    ).encode("utf-8")
    reviewed_source = (
        "from pathlib import Path\n"
        "import os\n"
        "path = Path(__file__)\n"
        "replacement = path.with_name(path.name + '.replacement')\n"
        f"replacement.write_bytes({replacement_source!r})\n"
        "os.replace(replacement, path)\n"
        "print('REVIEWED_BYTES_EXECUTED')\n"
    ).encode("utf-8")
    cli.write_bytes(reviewed_source)
    reviewed_sha256 = hashlib.sha256(reviewed_source).hexdigest()

    first = _run_launcher(root, reviewed_sha256, "1" * 64, "verify")
    assert first.returncode == 0
    assert first.stdout.strip() == "REVIEWED_BYTES_EXECUTED"
    assert cli.read_bytes() == replacement_source
    assert not replacement_marker.exists()

    second = _run_launcher(root, reviewed_sha256, "1" * 64, "verify")
    assert second.returncode != 0
    assert "staged CLI digest mismatch" in second.stderr
    assert "REVIEWED_BYTES_EXECUTED" not in second.stdout
    assert not replacement_marker.exists()


def test_seal_job_is_allowlisted_without_a_same_source_predecessor() -> None:
    relative = "slurm/peano_wmi_seal_v3_corpus.sbatch"
    completed = subprocess.run(
        [
            "bash",
            "-c",
            (
                f"source {COMMON!s}; "
                f"peano_wmi_validate_script_name {relative}; "
                f"if peano_wmi_expected_predecessor {relative}; then exit 19; fi"
            ),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "peano-wmi-v3-seal" in REMOTE_SUBMIT.read_text(encoding="utf-8")
    assert "peano-wmi-v3-seal" in SYNC.read_text(encoding="utf-8")
