"""Static and no-network checks for the WMI A100 control layer."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import os
import re
import subprocess

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 test host
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE = REPO_ROOT / "slurm" / "peano_wmi_a100_probe.sbatch"
SCRIPTS = REPO_ROOT / "scripts"
SLURM = REPO_ROOT / "slurm"
TRAINING = REPO_ROOT / "training" / "peano_policy"
WMI_SHELL_FILES = (
    SCRIPTS / "wmi_common.sh",
    SCRIPTS / "wmi_job_environment.sh",
    SCRIPTS / "wmi_sync_project.sh",
    SCRIPTS / "wmi_submit_job.sh",
    SCRIPTS / "wmi_prove_theorem.sh",
    SCRIPTS / "submit_wmi_slurm_job.sh",
    SCRIPTS / "wmi_queue_report.sh",
    PROBE,
    SLURM / "peano_wmi_prepare_training.sbatch",
    SLURM / "peano_wmi_train_qwen3_1_7b.sbatch",
    SLURM / "peano_wmi_eval_qwen3_1_7b.sbatch",
    SLURM / "peano_wmi_prepare_v2_training.sbatch",
    SLURM / "peano_wmi_train_qwen3_1_7b_v2.sbatch",
    SLURM / "peano_wmi_eval_qwen3_1_7b_v2.sbatch",
    SLURM / "peano_wmi_prepare_v3_training.sbatch",
    SLURM / "peano_wmi_prepare_v3_sealed_training.sbatch",
    SLURM / "peano_wmi_train_qwen3_1_7b_v3.sbatch",
    SLURM / "peano_wmi_eval_qwen3_1_7b_v3.sbatch",
    SLURM / "peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch",
    SLURM / "peano_wmi_prove_theorem.sbatch",
)


def _source() -> str:
    return PROBE.read_text(encoding="utf-8")


def test_wmi_shell_sources_parse_as_bash() -> None:
    for path in WMI_SHELL_FILES:
        subprocess.run(["bash", "-n", str(path)], check=True)


def test_wmi_probe_requests_one_nonpreemptible_a100_briefly() -> None:
    source = _source()
    assert "#SBATCH --partition=gpu_csi" in source
    assert "#SBATCH --gpus=nvidia_a100:1" in source
    assert "#SBATCH --constraint=vram80g" in source
    assert "#SBATCH --time=00:05:00" in source
    assert "#SBATCH --mem=8G" in source
    assert "gpu_spot" not in source


def test_wmi_probe_is_read_only_and_records_decisive_runtime_facts() -> None:
    source = _source()
    assert "installs nothing" in source
    assert "pip install" not in source
    assert "conda create" not in source
    assert "nvidia-smi" in source
    assert "driver_version" in source
    assert "compute_cap" in source
    assert "torch.cuda.is_bf16_supported()" in source
    assert 'torch.__version__ == "2.5.1"' in source
    assert 'torch.version.cuda == "12.4"' in source
    assert "torch.cuda.device_count() == 1" in source
    assert "loss.backward()" in source
    assert "anaconda/2025.12-1" in source
    assert "conda activate pytorch-gpu" in source
    assert "set +u\nsource " in source
    assert "conda activate pytorch-gpu\nset -u" in source
    assert "module -t spider anaconda" in source
    assert "pypi.org/simple/torch/" in source
    assert "Qwen/Qwen3-1.7B-Base" in source
    assert "Peano WMI A100 probe: OK" in source
    assert "unset PYTHONOPTIMIZE" in source


def test_wmi_sync_and_submission_controls_fix_scope_and_preserve_outputs() -> None:
    common = (SCRIPTS / "wmi_common.sh").read_text(encoding="utf-8")
    sync = (SCRIPTS / "wmi_sync_project.sh").read_text(encoding="utf-8")
    local_submit = (SCRIPTS / "wmi_submit_job.sh").read_text(encoding="utf-8")
    remote_submit = (SCRIPTS / "submit_wmi_slurm_job.sh").read_text(encoding="utf-8")
    combined = "\n".join((common, sync, local_submit, remote_submit))
    assert '"/work/bnaskrecki/peano-lab-training"' in common
    assert '"wmicluster"' in common
    assert '"PEANO-LAB-WMI-TRAINING"' in common
    assert "WMI synchronization requires a clean committed worktree" in sync
    for protected in (
        "/.venv-wmi/***",
        "/.cache/huggingface/***",
        "/data/peano-policy-v3/***",
        "/checkpoints/***",
        "/results/***",
        "/logs/***",
    ):
        assert f"protect {protected}" in sync
    data_filter = "/data/peano-policy-v3/***"
    assert sync.count(f"--filter='protect {data_filter}'") == 1
    assert sync.count(f"--exclude='{data_filter}'") == 1
    assert "--delete-delay" in sync
    assert "git_dirty" in remote_submit
    assert "[ \"$git_dirty\" != false ]" in remote_submit
    assert "sbatch --hold --parsable" in remote_submit
    assert remote_submit.index("sbatch --hold --parsable") < remote_submit.index(
        "sync -f \"$manifest\""
    ) < remote_submit.index("scontrol release \"$held_job\"")
    assert "scancel \"$held_job\"" in remote_submit
    assert "WMI dependency is absent or belongs to a different chain" in remote_submit
    assert not any(line.lstrip().startswith("eval ") for line in combined.splitlines())


def test_wmi_sync_publishes_only_a_verified_git_tree_under_exclusive_lock() -> None:
    source = (SCRIPTS / "wmi_sync_project.sh").read_text(encoding="utf-8")
    assert "git -C \"$repo_root\" archive --format=tar HEAD" in source
    assert "local_tree=\"$(git -C \"$repo_root\" rev-parse 'HEAD^{tree}')\"" in source
    assert "observed_tree=\"$(git -C \"$stage\" write-tree)\"" in source
    assert '[ "$observed_tree" != "$tree" ]' in source
    assert 'exec 8>"$project_root/.deployment.lock"' in source
    assert "flock -n -x 8" in source
    assert "cannot verify the WMI scheduler before source mutation" in source

    invalidate = 'mv -- "$provenance" "$project_root/logs/source-provenance-before-$synced_at.tsv"'
    publish_tree = "rsync -a --delete-delay"
    publish_provenance = 'mv -- "$provenance_stage" "$provenance"'
    assert source.index(invalidate) < source.index(publish_tree) < source.index(
        publish_provenance
    )
    assert source.index("flock -n -x 8") < source.index(invalidate)
    assert source.index("observed_tree=\"") < source.index(invalidate)


def test_wmi_submission_and_jobs_share_source_lock_and_queue_gate() -> None:
    submit = (SCRIPTS / "submit_wmi_slurm_job.sh").read_text(encoding="utf-8")
    assert "exec 8>.deployment.lock" in submit
    assert "flock -s 8" in submit
    assert 'if ! queue="$(squeue -h --me -o \'%A|%j|%T\')"; then' in submit
    assert "cannot verify active WMI jobs; refusing submission" in submit
    for name in (
        "peano-wmi-prepare",
        "peano-wmi-qwen17",
        "peano-wmi-qwen17-eval",
        "peano-wmi-v2-prepare",
        "peano-wmi-qwen17-v2",
        "peano-wmi-qwen17-v2-eval",
        "peano-wmi-v3-prepare",
        "peano-wmi-v3-sealprep",
        "peano-wmi-qwen17-v3",
        "peano-wmi-qwen17-v3-eval",
        "peano-wmi-qwen17-v3-base",
        "peano-wmi-prove",
        "peano-wmi-probe",
    ):
        assert name in submit
        assert name in (SCRIPTS / "wmi_sync_project.sh").read_text(encoding="utf-8")
    assert submit.index("flock -s 8") < submit.index("squeue -h --me")
    assert submit.index("squeue -h --me") < submit.index("sbatch --hold --parsable")

    for path in (
        SLURM / "peano_wmi_prepare_training.sbatch",
        SLURM / "peano_wmi_train_qwen3_1_7b.sbatch",
        SLURM / "peano_wmi_eval_qwen3_1_7b.sbatch",
        SLURM / "peano_wmi_prepare_v2_training.sbatch",
        SLURM / "peano_wmi_train_qwen3_1_7b_v2.sbatch",
        SLURM / "peano_wmi_eval_qwen3_1_7b_v2.sbatch",
        SLURM / "peano_wmi_prepare_v3_training.sbatch",
        SLURM / "peano_wmi_prepare_v3_sealed_training.sbatch",
        SLURM / "peano_wmi_train_qwen3_1_7b_v3.sbatch",
        SLURM / "peano_wmi_eval_qwen3_1_7b_v3.sbatch",
        SLURM / "peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch",
        SLURM / "peano_wmi_prove_theorem.sbatch",
    ):
        source = path.read_text(encoding="utf-8")
        lock = "exec 8>/work/bnaskrecki/peano-lab-training/.deployment.lock"
        hash_helper = (
            'export PEANO_JOB_ENV_SHA256="$(sha256sum '
            '"$peano_wmi_job_env" | awk \'{print $1}\')"'
        )
        source_helper = 'source "$peano_wmi_job_env"'
        assert lock in source
        assert "flock -s 8" in source
        assert "export PEANO_JOB_ENV_SCRIPT=scripts/wmi_job_environment.sh" in source
        assert hash_helper in source
        assert source_helper in source
        assert (
            source.index(lock)
            < source.index("flock -s 8")
            < source.index(hash_helper)
            < source.index(source_helper)
        )


def test_wmi_submission_ledger_hash_composes_job_and_support_helper() -> None:
    source = (SCRIPTS / "submit_wmi_slurm_job.sh").read_text(encoding="utf-8")
    assert "support_script=scripts/wmi_job_environment.sh" in source
    assert 'job_file_sha256="$(sha256sum "$job_script"' in source
    assert 'support_sha256="$(sha256sum "$support_script"' in source
    composite = 'script_sha256="$({\n  printf \'%s\\n\' "$job_file_sha256"\n  printf \'%s\\n\' "$support_sha256"\n} | sha256sum'
    assert composite in source
    assert '"$sync_timestamp" "$script_sha256" >> "$manifest"' in source

    # A dependent job must reproduce the same composite for its predecessor,
    # rather than trusting a ledger hash of the Slurm file alone.
    assert 'support_hash="$(sha256sum scripts/wmi_job_environment.sh' in source
    predecessor_composite = 'expected_predecessor_hash="$({\n    printf \'%s\\n\' "$expected_predecessor_hash"\n    printf \'%s\\n\' "$support_hash"\n  } | sha256sum'
    assert predecessor_composite in source
    assert "scripts/verify_wmi_submission_predecessor.py" in source


def test_wmi_predecessor_parser_preserves_empty_dependency_column(
    tmp_path: Path,
) -> None:
    verifier = SCRIPTS / "verify_wmi_submission_predecessor.py"
    header = "\t".join(
        (
            "timestamp",
            "job_id",
            "script",
            "dependency_job_id",
            "workdir",
            "git_commit",
            "git_dirty",
            "sync_timestamp",
            "script_sha256",
        )
    )
    values = (
        "2026-07-28T08:42:34+02:00",
        "171395",
        "slurm/peano_wmi_prepare_training.sbatch",
        "",
        "/work/bnaskrecki/peano-lab-training",
        "9" * 40,
        "false",
        "2026-07-28T06:41:45Z",
        "e" * 64,
    )
    ledger = tmp_path / "submissions.tsv"
    ledger.write_text(header + "\n" + "\t".join(values) + "\n", encoding="utf-8")
    command = [
        "python3",
        str(verifier),
        str(ledger),
        values[1],
        values[2],
        values[4],
        values[5],
        values[7],
        values[8],
    ]
    subprocess.run(command, check=True)

    ledger.write_text(
        header + "\n" + "\t".join(values) + "\n" + "\t".join(values) + "\n",
        encoding="utf-8",
    )
    rejected = subprocess.run(command, capture_output=True, text=True)
    assert rejected.returncode == 1
    assert "absent or duplicated" in rejected.stderr


def test_wmi_jobs_request_typed_a100_and_keep_training_offline() -> None:
    prepare = (SLURM / "peano_wmi_prepare_training.sbatch").read_text(encoding="utf-8")
    train = (SLURM / "peano_wmi_train_qwen3_1_7b.sbatch").read_text(encoding="utf-8")
    evaluate = (SLURM / "peano_wmi_eval_qwen3_1_7b.sbatch").read_text(encoding="utf-8")
    prove = (SLURM / "peano_wmi_prove_theorem.sbatch").read_text(encoding="utf-8")
    for source in (prepare, train, evaluate, prove):
        assert "#SBATCH --partition=gpu_csi" in source
        assert "#SBATCH --gpus=nvidia_a100:1" in source
        assert "#SBATCH --constraint=vram80g" in source
        assert "#SBATCH --account=" not in source
        assert "wmi_job_environment.sh" in source
    assert "--require-hashes" in prepare
    assert "--system-site-packages" in prepare
    assert "training.peano_policy.attest" in prepare
    assert "training.peano_policy.smoke" in prepare
    assert "--expected-machine x86_64" in prepare
    assert "--minimum-cuda-capability 8.0" in prepare
    for source in (train, evaluate, prove):
        assert "HF_HUB_OFFLINE=1" in source
        assert "TRANSFORMERS_OFFLINE=1" in source
    assert "--resume-from-checkpoint NEVER" in train
    assert "#SBATCH --requeue" not in train
    assert "heldout-k4.json" in evaluate
    assert "PEANO_PROOF_REQUEST_ID" in prove
    assert "peano_policy_proof_request.py run" in prove


def test_wmi_heavy_v2_chain_is_allowlisted_attested_and_one_shot() -> None:
    common = (SCRIPTS / "wmi_common.sh").read_text(encoding="utf-8")
    submit = (SCRIPTS / "submit_wmi_slurm_job.sh").read_text(encoding="utf-8")
    prepare = (SLURM / "peano_wmi_prepare_v2_training.sbatch").read_text(
        encoding="utf-8"
    )
    train = (SLURM / "peano_wmi_train_qwen3_1_7b_v2.sbatch").read_text(
        encoding="utf-8"
    )
    evaluate = (SLURM / "peano_wmi_eval_qwen3_1_7b_v2.sbatch").read_text(
        encoding="utf-8"
    )
    for source in (prepare, train, evaluate):
        assert "#SBATCH --partition=gpu_csi" in source
        assert "#SBATCH --gpus=nvidia_a100:1" in source
        assert "#SBATCH --constraint=vram80g" in source
        assert "wmi_job_environment.sh" in source
    assert "PEANO_POLICY_ROWS=100000" in prepare
    assert "PEANO_POLICY_DIR=data/peano-policy-v2" in prepare
    assert "peano-policy-v2-data" in prepare
    assert "training.peano_policy.token_audit" in prepare
    assert "peano-policy-wmi-a100-v2-smoke" in prepare
    assert "qwen3_1_7b_v2_heavy.toml" in train
    assert "--resume-from-checkpoint NEVER" in train
    assert "qwen3-1.7b-lora-v2-heavy" in evaluate
    assert "--max-steps 32" in evaluate
    for name in (
        "slurm/peano_wmi_prepare_v2_training.sbatch",
        "slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch",
        "slurm/peano_wmi_eval_qwen3_1_7b_v2.sbatch",
    ):
        assert name in common
    assert "peano-wmi-v2-prepare" in submit
    assert "peano-wmi-qwen17-v2" in submit
    assert "peano-wmi-qwen17-v2-eval" in submit


def test_wmi_v3_chain_prepares_trains_and_evaluates_on_a100() -> None:
    common = (SCRIPTS / "wmi_common.sh").read_text(encoding="utf-8")
    submit = (SCRIPTS / "submit_wmi_slurm_job.sh").read_text(encoding="utf-8")
    historical_prepare = (SLURM / "peano_wmi_prepare_v3_training.sbatch").read_text(
        encoding="utf-8"
    )
    prepare = (SLURM / "peano_wmi_prepare_v3_sealed_training.sbatch").read_text(
        encoding="utf-8"
    )
    train = (SLURM / "peano_wmi_train_qwen3_1_7b_v3.sbatch").read_text(
        encoding="utf-8"
    )
    evaluate = (SLURM / "peano_wmi_eval_qwen3_1_7b_v3.sbatch").read_text(
        encoding="utf-8"
    )
    baseline = (
        SLURM / "peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch"
    ).read_text(encoding="utf-8")

    # The continuation consumes the exact already-built output of 172729. It
    # closes that tree and never invokes any first-pass producer again.
    for forbidden in (
        "generate_peano_library_policy_corpus.py",
        "generate_peano_v3_balanced_corpus.py",
        "combine_peano_v3_corpus_metadata.py",
        "build_peano_policy_dataset.py",
    ):
        assert forbidden not in historical_prepare
    assert (
        "expected_manifest_sha256="
        "ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983"
        in historical_prepare
    )
    expected_files_match = re.search(
        r"expected_files=\(\n(?P<body>.*?)\n\)",
        historical_prepare,
        flags=re.DOTALL,
    )
    assert expected_files_match is not None
    expected_files = tuple(
        line.strip()
        for line in expected_files_match.group("body").splitlines()
        if line.strip()
    )
    assert expected_files == (
        "balanced-raw-traces.jsonl",
        "balanced-session-metadata.jsonl",
        "balanced-source-manifest.json",
        "combined-metadata-manifest.json",
        "library-raw-traces.jsonl",
        "library-session-metadata.jsonl",
        "library-source-manifest.json",
        "manifest.json",
        "session-metadata.jsonl",
        "test.jsonl",
        "train.jsonl",
        "val.jsonl",
    )
    for required in (
        "find \"$data_dir\" -mindepth 1 -maxdepth 1",
        '"${#observed_files[@]}" -ne "${#expected_files[@]}"',
        'test -f "$data_dir/$expected"',
        'test ! -L "$data_dir/$expected"',
        'sha256sum "$data_dir/manifest.json"',
        "never regenerates or rewrites corpus data",
    ):
        assert required in historical_prepare
    assert 'mkdir -p "$data_dir"' not in historical_prepare
    assert '--output "$data_dir' not in historical_prepare
    assert 'rm -rf -- "$data_dir"' not in historical_prepare
    attestation = '"$wmi_python" -m training.peano_policy.attest'
    token_audit = '"$wmi_python" -m training.peano_policy.token_audit'
    smoke = '"$wmi_python" -m training.peano_policy.smoke'
    assert historical_prepare.index(attestation) < historical_prepare.index(
        token_audit
    ) < historical_prepare.index(smoke)
    for report in (
        'peano-wmi-v3-dataset-attestation-${SLURM_JOB_ID:?}.json',
        'peano-wmi-v3-token-audit-${SLURM_JOB_ID}.json',
        'peano-wmi-v3-prepare-runtime-${SLURM_JOB_ID}.json',
    ):
        assert report in historical_prepare

    # New source revisions verify and reuse the immutable seal.  They do not
    # regenerate the corpus or repeat its multi-hour independent proof replay.
    assert "#SBATCH --partition=gpu_csi" in prepare
    assert "#SBATCH --gpus=nvidia_a100:1" in prepare
    assert "#SBATCH --constraint=vram80g" in prepare
    assert "#SBATCH --time=08:00:00" in prepare
    assert "#SBATCH --job-name=peano-wmi-v3-sealprep" in prepare
    assert "nvidia-smi" in prepare
    assert "verify_peano_v3_corpus_eligibility.py" in prepare
    assert "training.peano_policy.token_audit" in prepare
    assert "training.peano_policy.smoke" in prepare
    assert "peano-policy-wmi-a100-v3-smoke" in prepare
    assert "verify_wmi_v3_sealed_preparation.py" in prepare
    assert "generate_peano_v3_balanced_corpus.py" not in prepare
    assert "generate_peano_library_policy_corpus.py" not in prepare
    assert "build_peano_policy_dataset.py" not in prepare
    assert "training.peano_policy.attest" not in prepare
    assert "peano_wmi_assert_runtime" in prepare
    assert "HF_HUB_OFFLINE=1" in prepare
    assert "TRANSFORMERS_OFFLINE=1" in prepare

    for source in (train, evaluate, baseline):
        assert "#SBATCH --partition=gpu_csi" in source
        assert "#SBATCH --gpus=nvidia_a100:1" in source
        assert "#SBATCH --constraint=vram80g" in source
        assert "peano_wmi_assert_runtime" in source
        assert "HF_HUB_OFFLINE=1" in source
        assert "TRANSFORMERS_OFFLINE=1" in source
    for source in (prepare, train, evaluate, baseline):
        assert "export PYTHONHASHSEED=20260729" in source
    assert "qwen3_1_7b_v3_library.toml" in train
    assert "#SBATCH --time=36:00:00" in train
    assert "verify_wmi_v3_sealed_preparation.py" in train
    assert "peano-wmi-v3-sealed-eligibility-" in train
    assert "--preparation-eligibility-report" in train
    assert "--preparation-token-audit-report" in train
    assert "--preparation-runtime-smoke-report" in train
    assert "--prepare-job-id" in train
    assert "--resume-from-checkpoint NEVER" in train
    assert "qwen3-1.7b-lora-v3-library" in evaluate
    assert "#SBATCH --time=12:00:00" in evaluate
    assert "--mode search" in evaluate
    assert "--max-new-tokens 256" in evaluate
    assert "4,194,304" in evaluate
    assert "independent kernel checker" in evaluate
    assert "scripts/eval_pretrained_peano_policy.py" in baseline
    assert "pretrained-base-heldout-search-wmi-b16-c8-d32.json" in baseline
    assert "adapter_attached" not in baseline
    assert "--mode" not in baseline
    assert "--goal" not in baseline

    for name in (
        "slurm/peano_wmi_prepare_v3_sealed_training.sbatch",
        "slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch",
        "slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch",
        "slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch",
    ):
        assert name in common
    assert "slurm/peano_wmi_prepare_v3_training.sbatch" not in common
    for name in (
        "peano-wmi-v3-prepare",
        "peano-wmi-v3-sealprep",
        "peano-wmi-qwen17-v3",
        "peano-wmi-qwen17-v3-eval",
        "peano-wmi-qwen17-v3-base",
    ):
        assert name in submit
        assert name in (SCRIPTS / "wmi_sync_project.sh").read_text(
            encoding="utf-8"
        )
    assert "verify_wmi_v3_sealed_preparation.py" in submit
    assert "peano-wmi-v3-sealed-eligibility-" in submit
    assert 'environment_pointer=.venv-wmi/current' in submit
    assert 'verifier_python=".venv-wmi/releases/$environment_id/bin/python"' in submit
    assert (
        "printf '%s\\n' slurm/peano_wmi_prepare_v3_sealed_training.sbatch"
        in common
    )
    baseline_case = common.split(
        "slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch)", 1
    )[1]
    assert (
        "printf '%s\\n' slurm/peano_wmi_train_qwen3_1_7b_v3.sbatch"
        in baseline_case
    )
    assert "PEANO_TRAIN_JOB_ID=$afterok" in submit


def test_wmi_proof_request_is_file_backed_allowlisted_and_ledgered() -> None:
    common = (SCRIPTS / "wmi_common.sh").read_text(encoding="utf-8")
    local = (SCRIPTS / "wmi_prove_theorem.sh").read_text(encoding="utf-8")
    submit = (SCRIPTS / "submit_wmi_slurm_job.sh").read_text(encoding="utf-8")
    job = (SLURM / "peano_wmi_prove_theorem.sbatch").read_text(encoding="utf-8")
    assert "slurm/peano_wmi_prove_theorem.sbatch" in common
    assert "peano_wmi_validate_request_id" in common
    assert "peano_policy_proof_request.py receive" in local
    assert "flock -s .deployment.lock" in local
    assert "PEANO_PROOF_REQUEST_ID=$request_id" in submit
    assert 'proof_manifest=logs/proof-requests.tsv' in submit
    assert 'request_path="results/peano-policy/requests/$request_id.json"' in submit
    assert "peano_policy_proof_request.py verify" in submit
    assert "max_new_tokens=96" in local
    assert "max_steps=32" in local
    assert "search_beam_width=4" in local
    assert "search_candidates_per_state=4" in local
    assert "search_max_model_calls=128" in local
    assert "search_max_states=2048" in local
    assert "qwen3-1.7b-lora-v3-library" in job
    assert submit.index("sbatch --hold --parsable") < submit.index(
        '"$request_id" "$request_sha256" >> "$proof_manifest"'
    ) < submit.index("scontrol release \"$held_job\"")


def test_wmi_base_manifest_is_canonical_and_pins_entire_central_runtime() -> None:
    path = TRAINING / "wmi-base-v1.json"
    raw = path.read_text(encoding="utf-8")
    manifest = json.loads(raw)
    assert raw == json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    assert manifest == {
        "base_environment": "pytorch-gpu",
        "central_prefix": (
            "/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu"
        ),
        "ensurepip": "25.0.1",
        "machine": "x86_64",
        "module": "anaconda/2025.12-1",
        "packages": {
            "Jinja2": "3.1.6",
            "MarkupSafe": "3.0.3",
            "Pillow": "12.0.0",
            "PyYAML": "6.0.3",
            "certifi": "2025.11.12",
            "charset-normalizer": "3.4.4",
            "filelock": "3.20.1",
            "idna": "3.11",
            "mpmath": "1.3.0",
            "networkx": "3.6.1",
            "numpy": "2.3.5",
            "packaging": "25.0",
            "pip": "25.3",
            "psutil": "7.1.3",
            "requests": "2.32.5",
            "setuptools": "80.9.0",
            "sympy": "1.14.0",
            "torch": "2.5.1",
            "torchaudio": "2.5.1",
            "torchvision": "0.20.1",
            "triton": "3.1.0",
            "typing-extensions": "4.15.0",
            "urllib3": "2.6.2",
        },
        "python": "3.12.12",
        "torch_cuda": "12.4",
        "v": 1,
    }


def test_wmi_helper_checks_all_base_and_overlay_paths_and_pointer_identity() -> None:
    source = (SCRIPTS / "wmi_job_environment.sh").read_text(encoding="utf-8")
    assert "unset PYTHONOPTIMIZE" in source
    runtime_gate = source.split("peano_wmi_assert_runtime()", 1)[1]
    assert "assert " not in runtime_gate
    assert "def require(condition, message):" in runtime_gate
    assert '"ensurepip": ensurepip.version()' in source
    assert "for requested, expected_version in packages.items():" in source
    assert "distribution = importlib.metadata.distribution(requested)" in source
    assert 'location = Path(distribution.locate_file("")).resolve()' in source
    assert "if not location.is_relative_to(central):" in source

    match = re.search(
        r"expected_overlay = (\{.*?\n\})\nfor name, version in "
        r"expected_overlay\.items\(\):",
        source,
        flags=re.DOTALL,
    )
    assert match is not None
    embedded_overlay = ast.literal_eval(match.group(1))
    locked_overlay = {
        name: version
        for name, (version, _digest) in _locked_packages(
            TRAINING / "requirements-wmi-overlay.lock"
        ).items()
    }
    assert embedded_overlay == locked_overlay
    assert "distribution = importlib.metadata.distribution(name)" in source
    assert "require(location.is_relative_to(release), (name, location))" in source

    assert 'printf \'%s\\n\' "peano-wmi-environment-v2"' in source
    assert "peano_wmi_verify_base_manifest >/dev/null || return 1" in source
    assert 'base_record="$(sha256sum "$PEANO_WMI_BASE_MANIFEST")" || return 1' in source
    assert 'overlay_record="$(sha256sum "$PEANO_WMI_REQUIREMENTS_LOCK")" || return 1' in source
    assert 'sha256sum "$PEANO_WMI_BASE_MANIFEST"' in source
    assert 'sha256sum "$PEANO_WMI_REQUIREMENTS_LOCK"' in source
    assert 'expected_environment_id="$(peano_wmi_environment_id)"' in source
    assert '[ "$environment_id" != "$expected_environment_id" ]' in source
    assert 'release="$PEANO_WMI_PROJECT_ROOT/.venv-wmi/releases/$environment_id"' in source


def test_wmi_environment_id_propagates_base_verification_failure() -> None:
    helper = SCRIPTS / "wmi_job_environment.sh"
    program = f'''
set -euo pipefail
source "{helper}"
peano_wmi_verify_base_manifest() {{ return 23; }}
if value="$(peano_wmi_environment_id)"; then
  printf 'unexpected environment id: %s\\n' "$value" >&2
  exit 1
fi
'''
    subprocess.run(["bash", "-c", program], check=True)


def test_wmi_readonly_constants_are_exported_under_distinct_child_names(
    tmp_path: Path,
) -> None:
    helper = SCRIPTS / "wmi_job_environment.sh"
    release = tmp_path / "release"
    fake_python = release / "bin" / "python"
    fake_python.parent.mkdir(parents=True)
    fake_python.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
test "${PEANO_WMI_EXPECTED_CENTRAL_PREFIX:-}" = \
  /projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu
if [ -n "${PEANO_WMI_EXPECTED_PREFIX:-}" ]; then
  expected_release="$(cd "$(dirname "$0")/.." && pwd -P)"
  test "$PEANO_WMI_EXPECTED_PREFIX" = "$expected_release"
fi
""",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    program = r'''
set -euo pipefail
helper="$1"
fake_python="$2"
release="$3"
source "$helper"
python() { "$fake_python"; }
peano_wmi_verify_base_manifest
peano_wmi_assert_runtime "$fake_python"
'''
    subprocess.run(
        ["bash", "-c", program, "wmi-prefix-test", str(helper), str(fake_python), str(release)],
        check=True,
    )


def test_wmi_structured_runtime_records_driver_and_full_gpu_identity() -> None:
    source = (TRAINING / "runtime.py").read_text(encoding="utf-8")
    assert '"--query-gpu=driver_version"' in source
    assert 'accelerator["nvidia_driver"]' in source
    assert 'accelerator["total_memory"]' in source
    assert "device_capability" in source
    assert "bf16_supported" in source


def test_wmi_prepare_publishes_reviewed_pointer_only_after_full_smoke() -> None:
    source = (SLURM / "peano_wmi_prepare_training.sbatch").read_text(
        encoding="utf-8"
    )
    smoke = '"$wmi_python" -m training.peano_policy.smoke'
    stage = 'pointer_stage="$(mktemp "$PEANO_WMI_PROJECT_ROOT/.venv-wmi/current.XXXXXX")"'
    write_id = 'printf \'%s\\n\' "$environment_id" > "$pointer_stage"'
    publish = 'mv -f -- "$pointer_stage" "$PEANO_WMI_PROJECT_ROOT/.venv-wmi/current"'
    verify = 'test "$(peano_wmi_current_python)" = "$wmi_python"'
    assert source.index(smoke) < source.index(stage) < source.index(write_id)
    assert source.index(write_id) < source.index(publish) < source.index(verify)


def _locked_packages(path: Path) -> dict[str, tuple[str, str]]:
    logical: list[str] = []
    pending = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pending += line[:-1].rstrip() + " " if line.endswith("\\") else line
        if not line.endswith("\\"):
            logical.append(pending.strip())
            pending = ""
    assert not pending
    result: dict[str, tuple[str, str]] = {}
    pattern = re.compile(
        r"([A-Za-z0-9._-]+)==([^ ]+) +--hash=sha256:([0-9a-f]{64})"
    )
    for line in logical:
        match = pattern.fullmatch(line)
        assert match is not None, line
        name, version, digest = match.groups()
        normalized = name.lower().replace("_", "-")
        assert normalized not in result
        result[normalized] = (version, digest)
    return result


def test_wmi_overlay_is_hash_pinned_and_never_replaces_managed_numeric_stack() -> None:
    packages = _locked_packages(TRAINING / "requirements-wmi-overlay.lock")
    assert packages == {
        "accelerate": (
            "1.8.1",
            "c47b8994498875a2b1286e945bd4d20e476956056c7941d512334f4eb44ff991",
        ),
        "fsspec": (
            "2025.5.1",
            "24d3a2e663d5fc735ab256263c4075f374a174c3410c0b25e5bd1970bceaa462",
        ),
        "hf-xet": (
            "1.1.5",
            "fc874b5c843e642f45fd85cda1ce599e123308ad2901ead23d3510a47ff506d1",
        ),
        "huggingface-hub": (
            "0.33.4",
            "09f9f4e7ca62547c70f8b82767eefadd2667f4e116acba2e3e62a5a81815a7bb",
        ),
        "peft": (
            "0.16.0",
            "b5a2e08c053d12ddd0cf16ac7a320b2737e111943fc294d41173e72f780eeaef",
        ),
        "pip": (
            "25.2",
            "6d67a2b4e7f14d8b31b8b52648866fa717f45a1eb70e83002f4331d07e953717",
        ),
        "regex": (
            "2024.11.6",
            "70b7fa6606c2881c1db9479b0eaa11ed5dfa11c8d60a474ff0e095099f39d98e",
        ),
        "safetensors": (
            "0.5.3",
            "cead1fa41fc54b1e61089fa57452e8834f798cb1dc7a09ba3524f1eb08e0317a",
        ),
        "sympy": (
            "1.13.1",
            "db36cdc64bf61b9b24578b6f7bab1ecdd2452cf008f34faa33776680c26d66f8",
        ),
        "tokenizers": (
            "0.21.2",
            "fed9a4d51c395103ad24f8e7eb976811c57fbec2af9f133df471afcd922e5020",
        ),
        "tqdm": (
            "4.67.1",
            "26445eca388f82e72884e0d580d5464cd801a3ea01e63e5601bdff9ba6a48de2",
        ),
        "transformers": (
            "4.53.3",
            "5aba81c92095806b6baf12df35d756cf23b66c356975fb2a7fa9e536138d7c75",
        ),
    }
    assert not set(packages) & {
        "numpy",
        "torch",
        "torchaudio",
        "torchvision",
        "triton",
    }


def test_wmi_config_preserves_budget_but_forbids_unsafe_resume() -> None:
    helios = tomllib.loads(
        (TRAINING / "configs" / "qwen3_1_7b_smoke.toml").read_text(encoding="utf-8")
    )
    wmi = tomllib.loads(
        (TRAINING / "configs" / "qwen3_1_7b_wmi_smoke.toml").read_text(encoding="utf-8")
    )
    for section in ("model", "data", "lora", "trainer", "generation"):
        assert wmi[section] == helios[section]
    for key in ("seed", "max_train_samples", "max_eval_samples"):
        assert wmi["run"][key] == helios["run"][key]
    assert wmi["run"]["resume"] == "never"
    assert "wmi" in wmi["run"]["name"]
    assert "wmi" in wmi["run"]["output_dir"]


def test_wmi_local_submission_behavioral_harness(tmp_path: Path) -> None:
    harness = Path(__file__).with_name("wmi_control_harness.sh")
    environment = os.environ.copy()
    environment.pop("WMI_SSH_TARGET", None)
    completed = subprocess.run(
        ["bash", str(harness), str(REPO_ROOT), str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert completed.stdout == "WMI local control harness: OK\n"
