#!/usr/bin/env bash
set -euo pipefail

repo_root="${1:?repository root required}"
scratch="${2:?scratch directory required}"
project="$scratch/remote-project"
fake_bin="$scratch/bin"
mkdir -p "$project/scripts" "$project/slurm" "$project/logs" "$fake_bin"

for path in \
  scripts/submit_wmi_slurm_job.sh \
  scripts/wmi_common.sh \
  scripts/verify_wmi_submission_predecessor.py \
  scripts/wmi_job_environment.sh \
  slurm/peano_wmi_prepare_training.sbatch \
  slurm/peano_wmi_train_qwen3_1_7b.sbatch \
  slurm/peano_wmi_eval_qwen3_1_7b.sbatch; do
  cp "$repo_root/$path" "$project/$path"
done
project="$(cd "$project" && pwd -P)"

# Production keeps its fixed /work scope.  Only this private copied fixture is
# rewritten, after proving that the reviewed assignment occurs exactly once.
python3 - "$project/scripts/wmi_common.sh" "$project" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
root = sys.argv[2]
source = path.read_text(encoding="utf-8")
old = 'readonly PEANO_WMI_PROJECT_ROOT="/work/bnaskrecki/peano-lab-training"'
if source.count(old) != 1:
    raise SystemExit("fixture cannot identify the unique fixed WMI project root")
path.write_text(
    source.replace(old, f'readonly PEANO_WMI_PROJECT_ROOT="{root}"'),
    encoding="utf-8",
)
PY

scheduler_log="$scratch/scheduler.log"
sacct_responses="$scratch/sacct.responses"
sacct_count="$scratch/sacct.count"
export WMI_REMOTE_TEST_LOG="$scheduler_log"
export WMI_REMOTE_TEST_SACCT_RESPONSES="$sacct_responses"
export WMI_REMOTE_TEST_SACCT_COUNT="$sacct_count"

cat > "$fake_bin/sacct" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
printf 'sacct' >> "${WMI_REMOTE_TEST_LOG:?}"
printf ' <%s>' "$@" >> "$WMI_REMOTE_TEST_LOG"
printf '\n' >> "$WMI_REMOTE_TEST_LOG"
count=0
if [ -f "${WMI_REMOTE_TEST_SACCT_COUNT:?}" ]; then
  count="$(sed -n '1p' "$WMI_REMOTE_TEST_SACCT_COUNT")"
fi
count=$((count + 1))
printf '%s\n' "$count" > "$WMI_REMOTE_TEST_SACCT_COUNT"
record="$(sed -n "${count}p" "${WMI_REMOTE_TEST_SACCT_RESPONSES:?}")"
[ "$record" = __EMPTY__ ] || printf '%s\n' "$record"
FAKE

cat > "$fake_bin/squeue" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
printf 'squeue' >> "${WMI_REMOTE_TEST_LOG:?}"
printf ' <%s>' "$@" >> "$WMI_REMOTE_TEST_LOG"
printf '\n' >> "$WMI_REMOTE_TEST_LOG"
FAKE

cat > "$fake_bin/sbatch" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
printf 'sbatch' >> "${WMI_REMOTE_TEST_LOG:?}"
printf ' <%s>' "$@" >> "$WMI_REMOTE_TEST_LOG"
printf '\n' >> "$WMI_REMOTE_TEST_LOG"
case " $* " in
  *' --hold '*) printf '%s\n' 990001 ;;
  *) printf '%s\n' 'test-only accepted' ;;
esac
FAKE

for command in flock scontrol scancel sync; do
  cat > "$fake_bin/$command" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
name="${0##*/}"
printf '%s' "$name" >> "${WMI_REMOTE_TEST_LOG:?}"
printf ' <%s>' "$@" >> "$WMI_REMOTE_TEST_LOG"
printf '\n' >> "$WMI_REMOTE_TEST_LOG"
FAKE
done
cat > "$fake_bin/date" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
[ "$#" -eq 1 ] && [ "$1" = -Is ]
printf '%s\n' 2026-08-01T00:00:02Z
FAKE
chmod +x "$fake_bin"/*
export PATH="$fake_bin:$PATH"

reset_scheduler() {
  : > "$scheduler_log"
  printf '%s\n' 0 > "$sacct_count"
  printf '%s\n' "$@" > "$sacct_responses"
}

cd "$project"

reset_scheduler '217768|COMPLETED|0:0|0:0'
scripts/submit_wmi_slurm_job.sh --test-only \
  --completed-predecessor 217768 \
  slurm/peano_wmi_train_qwen3_1_7b.sbatch >/dev/null
grep -F -- '<--export=ALL,PEANO_PREPARE_JOB_ID=217768>' "$scheduler_log" >/dev/null
if grep -F -- '--dependency=' "$scheduler_log" >/dev/null; then
  echo "completed predecessor emitted a scheduler dependency" >&2
  exit 1
fi

reset_scheduler '217768|RUNNING|0:0|0:0'
scripts/submit_wmi_slurm_job.sh --test-only --afterok 217768 \
  slurm/peano_wmi_eval_qwen3_1_7b.sbatch >/dev/null
grep -F -- '<--export=ALL,PEANO_TRAIN_JOB_ID=217768>' "$scheduler_log" >/dev/null
grep -F -- '<--dependency=afterok:217768>' "$scheduler_log" >/dev/null

for invocation in \
  'afterok|217768|COMPLETED|0:0|0:0|slurm/peano_wmi_eval_qwen3_1_7b.sbatch' \
  'completed-predecessor|217768|RUNNING|0:0|0:0|slurm/peano_wmi_eval_qwen3_1_7b.sbatch' \
  'completed-predecessor|217768|FAILED|1:0|1:0|slurm/peano_wmi_train_qwen3_1_7b.sbatch'; do
  IFS='|' read -r option job_id state exit_code derived_exit_code script \
    <<< "$invocation"
  reset_scheduler "$job_id|$state|$exit_code|$derived_exit_code"
  if scripts/submit_wmi_slurm_job.sh --test-only "--$option" "$job_id" \
      "$script" >/dev/null 2>&1; then
    echo "inadmissible predecessor reached sbatch: $invocation" >&2
    exit 1
  fi
  if grep -F -- 'sbatch' "$scheduler_log" >/dev/null; then
    echo "rejected predecessor still invoked sbatch: $invocation" >&2
    exit 1
  fi
done

commit=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
synced_at=2026-08-01T00:00:00Z
printf '%s\tfalse\t%s\n' "$commit" "$synced_at" > .peano-source-provenance.tsv
header='timestamp\tjob_id\tscript\tdependency_job_id\tworkdir\tgit_commit\tgit_dirty\tsync_timestamp\tscript_sha256'
prepare_hash="$(sha256sum slurm/peano_wmi_prepare_training.sbatch | awk '{print $1}')"
support_hash="$(sha256sum scripts/wmi_job_environment.sh | awk '{print $1}')"
prepare_composite="$({
  printf '%s\n' "$prepare_hash"
  printf '%s\n' "$support_hash"
} | sha256sum | awk '{print $1}')"
printf '%b\n' "$header" > logs/submissions.tsv
printf '%s\t%s\t%s\t\t%s\t%s\tfalse\t%s\t%s\n' \
  2026-08-01T00:00:01Z 217768 \
  slurm/peano_wmi_prepare_training.sbatch "$project" "$commit" \
  "$synced_at" "$prepare_composite" >> logs/submissions.tsv
printf '%s\n' \
  '{"format":"peano-policy-wmi-a100-smoke","job":{"job_id":"217768"},"status":"passed"}' \
  > logs/peano-wmi-prepare-runtime-217768.json
printf '%s\n' '{}' > logs/peano-wmi-dataset-attestation-217768.json

reset_scheduler \
  '217768|COMPLETED|0:0|0:0' \
  '217768|COMPLETED|0:0|0:0'
scripts/submit_wmi_slurm_job.sh --submit \
  --confirm PEANO-LAB-WMI-TRAINING \
  --completed-predecessor 217768 \
  slurm/peano_wmi_train_qwen3_1_7b.sbatch >/dev/null
[ "$(grep -c '^sacct' "$scheduler_log")" -eq 2 ]
grep -F -- 'sbatch <--hold> <--parsable>' "$scheduler_log" >/dev/null
grep -F -- '<--export=ALL,PEANO_PREPARE_JOB_ID=217768>' "$scheduler_log" >/dev/null
if grep -F -- '--dependency=' "$scheduler_log" >/dev/null; then
  echo "real completed handoff emitted a scheduler dependency" >&2
  exit 1
fi
grep -F -- 'sync <-f> <logs/submissions.tsv>' "$scheduler_log" >/dev/null
grep -F -- 'scontrol <release> <990001>' "$scheduler_log" >/dev/null
python3 - logs/submissions.tsv "$project" <<'PY'
from pathlib import Path
import sys

rows = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
fields = rows[-1].split("\t")
assert len(fields) == 9
assert fields[1] == "990001"
assert fields[2] == "slurm/peano_wmi_train_qwen3_1_7b.sbatch"
assert fields[3] == "217768"
assert fields[4] == sys.argv[2]
PY

# The first live check is not enough: if the producer completes before the
# held submit, the second check rejects instead of silently dropping afterok.
reset_scheduler \
  '990001|RUNNING|0:0|0:0' \
  '990001|COMPLETED|0:0|0:0'
if scripts/submit_wmi_slurm_job.sh --submit \
    --confirm PEANO-LAB-WMI-TRAINING --afterok 990001 \
    slurm/peano_wmi_eval_qwen3_1_7b.sbatch >/dev/null 2>&1; then
  echo "live-to-completed predecessor transition reached submission" >&2
  exit 1
fi
[ "$(grep -c '^sacct' "$scheduler_log")" -eq 2 ]
if grep -E '^(sbatch|scontrol)' "$scheduler_log" >/dev/null; then
  echo "failed final predecessor recheck mutated scheduler state" >&2
  exit 1
fi

printf '%s\n' 'WMI remote submission harness: OK'
