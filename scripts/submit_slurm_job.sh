#!/usr/bin/env bash
# Run from the project checkout on Helios. Test-only is the safe default.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=helios_common.sh
source "$script_dir/helios_common.sh"

usage() {
  echo "usage: $0 [--test-only] [--afterok JOB_ID] slurm/job.sbatch" >&2
  echo "       $0 --submit --confirm $PEANO_HELIOS_CONFIRM_TOKEN [--afterok JOB_ID] slurm/job.sbatch" >&2
}

mode="--test-only"
confirmation=""
afterok=""
job_script=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only)
      mode="--test-only"
      shift
      ;;
    --submit)
      mode="--submit"
      shift
      ;;
    --confirm)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      confirmation="$2"
      shift 2
      ;;
    --afterok)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      [ -z "$afterok" ] || { echo "--afterok may appear only once" >&2; exit 2; }
      afterok="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --*)
      printf 'unknown option: %s\n' "$1" >&2
      usage
      exit 2
      ;;
    *)
      [ -z "$job_script" ] || { echo "only one job script is allowed" >&2; exit 2; }
      job_script="$1"
      shift
      ;;
  esac
done

[ -n "$job_script" ] || { usage; exit 2; }
peano_helios_validate_script_name "$job_script"
[ -z "$afterok" ] || peano_helios_validate_single_job_id "$afterok" || {
  printf 'invalid --afterok job id: %s\n' "$afterok" >&2
  exit 2
}

repo_root="$(cd "$script_dir/.." && pwd -P)"
cd "$repo_root"
[ -f "$job_script" ] || { printf 'missing sbatch script: %s\n' "$job_script" >&2; exit 2; }
[ ! -L "$job_script" ] || { printf 'job script must not be a symlink: %s\n' "$job_script" >&2; exit 2; }

slurm_root="$(cd slurm && pwd -P)"
job_dir="$(cd "$(dirname "$job_script")" && pwd -P)"
case "$job_dir/$(basename "$job_script")" in
  "$slurm_root"/*) ;;
  *)
    printf 'job script resolves outside slurm/: %s\n' "$job_script" >&2
    exit 2
    ;;
esac

if [ "$mode" = "--test-only" ]; then
  [ -z "$confirmation" ] || { echo "--confirm is only valid with --submit" >&2; exit 2; }
  sbatch_args=(--test-only)
  [ -z "$afterok" ] || sbatch_args+=("--dependency=afterok:$afterok")
  exec sbatch "${sbatch_args[@]}" "$job_script"
fi

if [ "$confirmation" != "$PEANO_HELIOS_CONFIRM_TOKEN" ]; then
  echo "real submission requires: --submit --confirm $PEANO_HELIOS_CONFIRM_TOKEN" >&2
  exit 2
fi
if peano_helios_requires_dependency "$job_script" && [ -z "$afterok" ]; then
  echo "training and evaluation submissions require --afterok JOB_ID" >&2
  exit 2
fi

timestamp="$(date -Is)"
source_provenance="$repo_root/.peano-source-provenance.tsv"
if [ -f "$source_provenance" ]; then
  IFS=$'\t' read -r commit git_dirty sync_timestamp extra < "$source_provenance"
  if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]] || \
     [[ "$git_dirty" != true && "$git_dirty" != false ]] || \
     [[ ! "$sync_timestamp" =~ ^[0-9TZ:-]+$ ]] || [ -n "${extra:-}" ]; then
    echo "source provenance is malformed: $source_provenance" >&2
    exit 1
  fi
elif git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  commit="$(git -C "$repo_root" rev-parse HEAD)"
  if [ -n "$(git -C "$repo_root" status --porcelain --untracked-files=all)" ]; then
    git_dirty=true
  else
    git_dirty=false
  fi
  sync_timestamp="-"
else
  echo "missing source provenance and git metadata" >&2
  exit 1
fi
if command -v sha256sum >/dev/null 2>&1; then
  script_sha256="$(sha256sum "$job_script" | awk '{print $1}')"
else
  script_sha256="$(shasum -a 256 "$job_script" | awk '{print $1}')"
fi
manifest="logs/submissions.tsv"
umask 077
mkdir -p logs
header='timestamp	job_id	script	dependency_job_id	workdir	git_commit	git_dirty	sync_timestamp	script_sha256'
if [ ! -f "$manifest" ]; then
  printf '%b\n' "$header" > "$manifest"
elif [ "$(sed -n '1p' "$manifest")" != "$(printf '%b' "$header")" ]; then
  echo "submission manifest has an incompatible header: $manifest" >&2
  exit 1
fi
[ -w "$manifest" ] || { printf 'submission manifest is not writable: %s\n' "$manifest" >&2; exit 1; }

# Alpha GPU jobs must depend on their exact reviewed predecessor from the same
# clean source, project, sync epoch, and immutable script—not an arbitrary
# successful Slurm allocation owned by the same account.
expected_predecessor="$(peano_helios_expected_predecessor "$job_script" || true)"
if [ -n "$expected_predecessor" ]; then
  if [ "$git_dirty" != false ]; then
    printf '%s\n' 'Hydra GPU submission requires an explicitly clean source' >&2
    exit 1
  fi
  if [ ! -f "$expected_predecessor" ] || [ -L "$expected_predecessor" ]; then
    printf 'missing regular Hydra predecessor script: %s\n' "$expected_predecessor" >&2
    exit 1
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    predecessor_hash="$(sha256sum "$expected_predecessor" | awk '{print $1}')"
  else
    predecessor_hash="$(shasum -a 256 "$expected_predecessor" | awk '{print $1}')"
  fi
  if ! predecessor_record="$(
    awk -F '\t' -v wanted="$afterok" '
      NR > 1 && $2 == wanted {
        count += 1
        row = $3 "\t" $5 "\t" $6 "\t" $7 "\t" $8 "\t" $9
      }
      END {
        if (count != 1) exit 1
        print row
      }
    ' "$manifest"
  )"; then
    printf 'Hydra predecessor has no unique submission record: %s\n' "$afterok" >&2
    exit 1
  fi
  IFS=$'\t' read -r predecessor_script predecessor_workdir predecessor_commit \
    predecessor_dirty predecessor_synced predecessor_recorded_hash predecessor_extra \
    <<< "$predecessor_record"
  if [ "$predecessor_script" != "$expected_predecessor" ] || \
     [ "$predecessor_workdir" != "$repo_root" ] || \
     [ "$predecessor_commit" != "$commit" ] || \
     [ "$predecessor_dirty" != false ] || \
     [ "$predecessor_synced" != "$sync_timestamp" ] || \
     [ "$predecessor_recorded_hash" != "$predecessor_hash" ] || \
     [ -n "${predecessor_extra:-}" ]; then
    printf '%s\n' 'Hydra predecessor is not the exact same-source reviewed job' >&2
    exit 1
  fi
fi

sbatch_args=(--parsable)
[ -z "$afterok" ] || sbatch_args+=("--dependency=afterok:$afterok")
submission="$(sbatch "${sbatch_args[@]}" "$job_script")"
job_id="${submission%%;*}"
if [[ ! "$job_id" =~ ^[0-9]+$ ]]; then
  printf 'sbatch returned an invalid job id: %s\n' "$submission" >&2
  exit 1
fi

printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "$timestamp" "$job_id" "$job_script" "$afterok" "$repo_root" "$commit" \
  "$git_dirty" "$sync_timestamp" "$script_sha256" >> "$manifest"
printf 'submitted job_id=%s\n' "$job_id"
printf 'manifest=%s\n' "$manifest"
