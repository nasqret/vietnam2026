#!/usr/bin/env bash
# Reproducibly build and install/check the dependency-free Peano WASM shadow.
# Usage: scripts/build_peano_shadow_wasm.sh [--check]
set -euo pipefail

PEANO_WASM_CHECK=false
if [[ ${1:-} == "--check" && $# -eq 1 ]]; then
  PEANO_WASM_CHECK=true
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--check]" >&2
  exit 2
fi

cd "$(dirname "$0")/.."
PEANO_SOURCE_ROOT="$(pwd -P)"
PEANO_WASM_CRATE="peano-lab/rust/peano-kernel-shadow-wasm"
PEANO_WASM_DESTINATION="peano-lab/peano_kernel_shadow.wasm"
PEANO_RUSTUP="${PEANO_RUSTUP:-$(command -v rustup || true)}"
if [[ -z "$PEANO_RUSTUP" && -x /opt/homebrew/opt/rustup/bin/rustup ]]; then
  PEANO_RUSTUP=/opt/homebrew/opt/rustup/bin/rustup
fi
if [[ -z "$PEANO_RUSTUP" || ! -x "$PEANO_RUSTUP" ]]; then
  echo "rustup is required to build the pinned Peano WASM shadow" >&2
  exit 1
fi

PEANO_TOOLCHAIN=1.95.0
PEANO_RUSTC="$($PEANO_RUSTUP which rustc --toolchain "$PEANO_TOOLCHAIN")"
PEANO_TOOLCHAIN_BIN="$(dirname "$PEANO_RUSTC")"
PEANO_CARGO="$PEANO_TOOLCHAIN_BIN/cargo"
PEANO_REPRODUCIBLE_RUSTFLAGS="--remap-path-prefix=$PEANO_SOURCE_ROOT=/peano-lab-src"
if ! "$PEANO_RUSTUP" target list --installed --toolchain "$PEANO_TOOLCHAIN" \
  | grep -Fxq wasm32-unknown-unknown; then
  echo "the pinned $PEANO_TOOLCHAIN wasm32-unknown-unknown target is not installed" >&2
  exit 1
fi

PEANO_WASM_TMP="$(mktemp -d)"
trap 'rm -rf -- "$PEANO_WASM_TMP"' EXIT

build_once() {
  local destination="$1"
  RUSTFLAGS="$PEANO_REPRODUCIBLE_RUSTFLAGS" "$PEANO_CARGO" \
    --config "build.rustc=\"$PEANO_RUSTC\"" \
    build \
    --locked \
    --manifest-path "$PEANO_WASM_CRATE/Cargo.toml" \
    --release \
    --target wasm32-unknown-unknown \
    --target-dir "$destination" >/dev/null
}

build_once "$PEANO_WASM_TMP/first"
build_once "$PEANO_WASM_TMP/second"
PEANO_WASM_FIRST="$PEANO_WASM_TMP/first/wasm32-unknown-unknown/release/peano_kernel_shadow_wasm.wasm"
PEANO_WASM_SECOND="$PEANO_WASM_TMP/second/wasm32-unknown-unknown/release/peano_kernel_shadow_wasm.wasm"
if ! cmp -s "$PEANO_WASM_FIRST" "$PEANO_WASM_SECOND"; then
  echo "two clean Peano WASM builds were not byte-identical" >&2
  exit 1
fi

if $PEANO_WASM_CHECK; then
  if [[ ! -f "$PEANO_WASM_DESTINATION" ]] \
    || ! cmp -s "$PEANO_WASM_FIRST" "$PEANO_WASM_DESTINATION"; then
    echo "Peano WASM shadow is missing or stale; regenerate it with $0" >&2
    if [[ -f "$PEANO_WASM_DESTINATION" ]]; then
      printf 'rebuilt:   %s\ncommitted: %s\n' \
        "$(shasum -a 256 "$PEANO_WASM_FIRST" | awk '{print $1}')" \
        "$(shasum -a 256 "$PEANO_WASM_DESTINATION" | awk '{print $1}')" >&2
    fi
    exit 1
  fi
else
  install -m 0644 "$PEANO_WASM_FIRST" "$PEANO_WASM_DESTINATION"
fi

printf 'Peano WASM shadow: %s  %s\n' \
  "$(shasum -a 256 "$PEANO_WASM_FIRST" | awk '{print $1}')" \
  "$PEANO_WASM_DESTINATION"
