#!/usr/bin/env bash
# Read-only report of the account, filesystems, grants, and scheduler surface.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=helios_common.sh
source "$script_dir/helios_common.sh"

ssh_target="$(peano_helios_ssh_target)"

ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" 'bash -l -s' <<'REMOTE'
set -euo pipefail
project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"

echo "== identity =="
date -Is
hostname
whoami
id
printf 'HOME=%s\n' "${HOME:-}"
printf 'SCRATCH=%s\n' "${SCRATCH:-}"
printf 'project_root=%s\n' "$project_root"

echo
echo "== filesystem (read only) =="
for path in "${HOME:-}" "${SCRATCH:-}" "$project_root"; do
  if [ -n "$path" ]; then
    ls -ld -- "$path" 2>&1 || true
  fi
done

echo
echo "== grants =="
hpc-grants || true

echo
echo "== storage =="
hpc-fs || true

echo
echo "== slurm =="
command -v sbatch || true
command -v squeue || true
command -v sacct || true
sinfo -o "%P %a %l %D %C" | head -40 || true
REMOTE
