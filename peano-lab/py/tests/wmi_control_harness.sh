#!/usr/bin/env bash
set -euo pipefail

repo_root="${1:?repository root required}"
scratch="${2:?scratch directory required}"
fake_bin="$scratch/bin"
ssh_log="$scratch/ssh.log"
mkdir -p "$fake_bin"

cat > "$fake_bin/ssh" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "${WMI_TEST_SSH_LOG:?}"
FAKE
chmod +x "$fake_bin/ssh"
export PATH="$fake_bin:$PATH"
export WMI_TEST_SSH_LOG="$ssh_log"
cd "$repo_root"

if scripts/wmi_submit_job.sh --submit \
  slurm/peano_wmi_prepare_training.sbatch >/dev/null 2>&1; then
  echo "unguarded WMI submit succeeded" >&2
  exit 1
fi
if scripts/wmi_submit_job.sh --test-only \
  slurm/peano_wmi_train_qwen3_1_7b.sbatch >/dev/null 2>&1; then
  echo "dependency-free WMI training succeeded" >&2
  exit 1
fi
if scripts/wmi_submit_job.sh --test-only --afterok 12 \
  slurm/peano_wmi_prepare_training.sbatch >/dev/null 2>&1; then
  echo "dependent WMI preparation succeeded" >&2
  exit 1
fi
if scripts/wmi_submit_job.sh --test-only ../bad.sbatch >/dev/null 2>&1; then
  echo "unsafe WMI script succeeded" >&2
  exit 1
fi

scripts/wmi_submit_job.sh --test-only \
  slurm/peano_wmi_prepare_training.sbatch >/dev/null
grep -F -- \
  "--test-only slurm/peano_wmi_prepare_training.sbatch" "$ssh_log" >/dev/null

scripts/wmi_submit_job.sh --submit --confirm PEANO-LAB-WMI-TRAINING \
  --afterok 12345 slurm/peano_wmi_train_qwen3_1_7b.sbatch >/dev/null
grep -F -- \
  "--submit --confirm PEANO-LAB-WMI-TRAINING --afterok 12345 slurm/peano_wmi_train_qwen3_1_7b.sbatch" \
  "$ssh_log" >/dev/null

scripts/wmi_submit_job.sh --test-only \
  slurm/peano_wmi_prepare_v2_training.sbatch >/dev/null
grep -F -- \
  "--test-only slurm/peano_wmi_prepare_v2_training.sbatch" "$ssh_log" >/dev/null

scripts/wmi_submit_job.sh --submit --confirm PEANO-LAB-WMI-TRAINING \
  --afterok 23456 slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch >/dev/null
grep -F -- \
  "--submit --confirm PEANO-LAB-WMI-TRAINING --afterok 23456 slurm/peano_wmi_train_qwen3_1_7b_v2.sbatch" \
  "$ssh_log" >/dev/null

if scripts/wmi_prove_theorem.sh --test-only \
  --theorem 'forall n. n = n' --sample --k 2 >/dev/null 2>&1; then
  echo "legacy rollout flag entered the kernel-guided one-shot path" >&2
  exit 1
fi

scripts/wmi_prove_theorem.sh --test-only \
  --theorem 'forall n. n = n' --sample \
  --max-new-tokens 48 \
  --max-steps 12 \
  --search-beam-width 3 \
  --search-candidates-per-state 2 \
  --search-max-model-calls 24 \
  --search-max-states 96 >/dev/null
grep -E -- \
  '--request-id [0-9a-f]{64} slurm/peano_wmi_prove_theorem.sbatch' \
  "$ssh_log" >/dev/null
grep -E -- \
  'peano_policy_proof_request.py receive --request-id [0-9a-f]{64}' \
  "$ssh_log" >/dev/null

printf '%s\n' 'WMI local control harness: OK'
