#!/usr/bin/env bash
# Copy the exact completed morning adapter from WMI and publish it atomically.

set -euo pipefail

readonly repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
readonly remote_host="wmicluster"
readonly adapter_name="qwen3-1.7b-lora-v3-morning-diagnostic-20260731-r1"
readonly remote_adapter="/work/bnaskrecki/peano-lab-training/results/peano-policy/diagnostics/$adapter_name"
readonly results_root="$repository_root/results"
readonly policy_root="$results_root/peano-policy"
readonly destination_parent="$policy_root/diagnostics"
readonly destination="$destination_parent/$adapter_name"

for command_name in ssh rsync python3 mktemp mv; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'required command is unavailable: %s\n' "$command_name" >&2
    exit 1
  fi
done
if [ -e "$destination" ] || [ -L "$destination" ]; then
  printf 'refusing to replace existing adapter destination: %s\n' "$destination" >&2
  exit 1
fi

# Do not allow a pre-existing symlink to redirect publication outside results/.
for directory in "$results_root" "$policy_root" "$destination_parent"; do
  if [ -L "$directory" ]; then
    printf 'refusing symlinked adapter destination parent: %s\n' "$directory" >&2
    exit 1
  fi
  mkdir -p "$directory"
  if [ ! -d "$directory" ] || [ -L "$directory" ]; then
    printf 'adapter destination parent is unsafe: %s\n' "$directory" >&2
    exit 1
  fi
done

ssh "$remote_host" \
  "test -d '$remote_adapter' && test ! -L '$remote_adapter'"

staging="$(mktemp -d "$destination_parent/.${adapter_name}.incoming.XXXXXX")"
published=false
cleanup() {
  if [ "$published" = false ] && [ -n "${staging:-}" ] && [ -d "$staging" ]; then
    case "$staging" in
      "$destination_parent/.${adapter_name}.incoming."*) rm -rf -- "$staging" ;;
      *) printf 'refusing to clean unexpected staging path: %s\n' "$staging" >&2 ;;
    esac
  fi
}
trap cleanup EXIT

# The source path is a hard-coded safe token.  Keep flags within the smaller
# option surface implemented by macOS openrsync.
rsync -a --safe-links \
  "$remote_host:$remote_adapter/" \
  "$staging/"

cd "$repository_root"
python3 scripts/verify_peano_morning_adapter.py "$staging"

# Apple mv(1) -n is no-clobber.  Recheck both before and after it so a racing
# destination cannot turn a successful transfer into an overwrite or nesting.
if [ -e "$destination" ] || [ -L "$destination" ]; then
  printf 'adapter destination appeared during verification: %s\n' "$destination" >&2
  exit 1
fi
mv -n "$staging" "$destination"
if [ -e "$staging" ] || [ -L "$staging" ] || [ ! -d "$destination" ]; then
  printf 'no-clobber adapter publication did not complete\n' >&2
  exit 1
fi
published=true
python3 scripts/verify_peano_morning_adapter.py "$destination"
printf 'PEANO_MORNING_ADAPTER=%s\n' "$destination"
