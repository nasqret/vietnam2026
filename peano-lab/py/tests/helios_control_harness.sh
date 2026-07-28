#!/usr/bin/env bash
# Behavioral checks for the local/remote submission gates; never uses a network.
set -euo pipefail

repo_root="${1:?repository root required}"
test_root="${2:?temporary directory required}"
fake_bin="$test_root/bin"
ssh_log="$test_root/ssh.log"
sbatch_log="$test_root/sbatch.log"
mkdir -p "$fake_bin"
: > "$ssh_log"
: > "$sbatch_log"

cat > "$fake_bin/ssh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${PEANO_TEST_SSH_LOG:?}"
cat >/dev/null
SH

cat > "$fake_bin/sbatch" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${PEANO_TEST_SBATCH_LOG:?}"
if [ "${1:-}" = "--parsable" ]; then
  printf '424242;helios\n'
fi
SH
chmod +x "$fake_bin/ssh" "$fake_bin/sbatch"

export PATH="$fake_bin:$PATH"
export PEANO_TEST_SSH_LOG="$ssh_log"
export PEANO_TEST_SBATCH_LOG="$sbatch_log"
cd "$repo_root"

# Real submission must fail locally, before ssh, unless both gates are present.
if scripts/helios_submit_job.sh --submit slurm/peano_cpu_smoke.sbatch >/dev/null 2>&1; then
  echo "submit unexpectedly accepted no confirmation" >&2
  exit 1
fi
[ ! -s "$ssh_log" ]

if scripts/helios_submit_job.sh --submit --confirm WRONG slurm/peano_cpu_smoke.sbatch >/dev/null 2>&1; then
  echo "submit unexpectedly accepted a wrong confirmation" >&2
  exit 1
fi
[ ! -s "$ssh_log" ]

if scripts/helios_submit_job.sh --test-only ../outside.sbatch >/dev/null 2>&1; then
  echo "test unexpectedly accepted path traversal" >&2
  exit 1
fi
[ ! -s "$ssh_log" ]

if scripts/helios_submit_job.sh --test-only --afterok '12;touch_bad' \
  slurm/peano_cpu_smoke.sbatch >/dev/null 2>&1; then
  echo "test unexpectedly accepted an unsafe dependency" >&2
  exit 1
fi
[ ! -s "$ssh_log" ]

scripts/helios_submit_job.sh --test-only slurm/peano_cpu_smoke.sbatch >/dev/null
grep -F -- "--test-only slurm/peano_cpu_smoke.sbatch" "$ssh_log" >/dev/null

: > "$ssh_log"
scripts/helios_submit_job.sh --test-only --afterok 12345 \
  slurm/peano_cpu_smoke.sbatch >/dev/null
grep -F -- "--test-only --afterok 12345 slurm/peano_cpu_smoke.sbatch" \
  "$ssh_log" >/dev/null

: > "$ssh_log"
scripts/helios_submit_job.sh --submit --confirm PEANO-LAB-TRAINING \
  slurm/peano_gpu_gh200_smoke.sbatch >/dev/null
grep -F -- "--submit --confirm PEANO-LAB-TRAINING slurm/peano_gpu_gh200_smoke.sbatch" \
  "$ssh_log" >/dev/null

: > "$ssh_log"
if scripts/helios_submit_job.sh --submit --confirm PEANO-LAB-TRAINING \
  slurm/peano_train_qwen3_1_7b.sbatch >/dev/null 2>&1; then
  echo "training unexpectedly accepted no dependency" >&2
  exit 1
fi
[ ! -s "$ssh_log" ]

scripts/helios_submit_job.sh --submit --confirm PEANO-LAB-TRAINING \
  --afterok 12345 slurm/peano_train_qwen3_1_7b.sbatch >/dev/null
grep -F -- \
  "--submit --confirm PEANO-LAB-TRAINING --afterok 12345 slurm/peano_train_qwen3_1_7b.sbatch" \
  "$ssh_log" >/dev/null

# The remote-side wrapper independently enforces the same confirmation gate.
if scripts/submit_slurm_job.sh --submit slurm/peano_cpu_smoke.sbatch >/dev/null 2>&1; then
  echo "remote wrapper unexpectedly accepted no confirmation" >&2
  exit 1
fi
[ ! -s "$sbatch_log" ]

if scripts/submit_slurm_job.sh --submit --confirm PEANO-LAB-TRAINING \
  slurm/peano_train_qwen3_1_7b.sbatch >/dev/null 2>&1; then
  echo "remote training unexpectedly accepted no dependency" >&2
  exit 1
fi
[ ! -s "$sbatch_log" ]

scripts/submit_slurm_job.sh --test-only slurm/peano_cpu_smoke.sbatch >/dev/null
grep -Fx -- "--test-only slurm/peano_cpu_smoke.sbatch" "$sbatch_log" >/dev/null

: > "$sbatch_log"
scripts/submit_slurm_job.sh --test-only --afterok 12345 \
  slurm/peano_cpu_smoke.sbatch >/dev/null
grep -Fx -- \
  "--test-only --dependency=afterok:12345 slurm/peano_cpu_smoke.sbatch" \
  "$sbatch_log" >/dev/null

# Queue input is validated before the ssh boundary.
: > "$ssh_log"
if scripts/helios_queue_report.sh '12;touch_bad' >/dev/null 2>&1; then
  echo "queue report unexpectedly accepted unsafe input" >&2
  exit 1
fi
[ ! -s "$ssh_log" ]

printf 'Helios control harness: OK\n'
