# Peano Lab WebAssembly shadow wrapper

This dependency-free `cdylib` exposes the existing
`peano-kernel-shadow` checker to a dedicated browser worker.  It is a
diagnostic second implementation only.  The authoritative Python kernel must
first accept the certificate against the original stated goal; no return value
from this module may publish QED.

## Pinned raw ABI (version 1)

The `wasm32-unknown-unknown` module exports its linear memory and four
functions:

| Export | WebAssembly signature | Meaning |
| --- | --- | --- |
| `peano_shadow_abi_version` | `() -> i32` | Returns `1`. |
| `peano_shadow_max_input_bytes` | `() -> i32` | Returns `16 * 1024 * 1024`. |
| `peano_shadow_prepare` | `(i32 length) -> i32` | Replaces the one-shot buffer and returns its nonzero memory offset, or zero on failure. |
| `peano_shadow_check` | `(i32 length, i32 logic) -> i32` | Consumes the buffer and returns a verdict. |
| `peano_shadow_reset` | `() -> i32` | Discards a buffer; returns `1` or internal error `4`. |

After `prepare`, JavaScript must create a **fresh** view of `exports.memory.buffer`
(allocation may grow memory), copy exactly `length` canonical
`peano-lab-v2` bytes at the returned offset, and invoke `check` once.  A second
`prepare`, `check`, or `reset` invalidates the old offset.  The wrapper owns the
allocation; there is no exported `free` and no caller pointer is dereferenced
by Rust.

Logic values are `0` for HA and `1` for the explicitly labeled PA+DNE mode.
Other values are ABI errors.  Verdicts are:

1. accepted by the requested shadow checker;
2. decoded but logically rejected (including insufficient fuel or a free
   original target);
3. malformed or rejected by a codec/resource limit;
4. bad ABI call or internal failure.

Every `check` path consumes the input, including wrong lengths and wrong logic
flags.  Browser traps are also fail-closed and should cause the dedicated
worker to be replaced.

The fixed browser envelope is 16 MiB, 1,000,000 decoded nodes, syntax depth
192, and 64,000,000 checker invocations.  Although the canonical codec permits
wire naturals through `u32::MAX`, this wrapper rejects every term-variable or
hypothesis index above `u32::MAX - 256`.  That fixed-width reserve covers all
checker-side binder shifts admitted by the depth bound and keeps native/WASM
decisions aligned.  The linker caps linear memory at 256 MiB.  There are no
threads, shared memory, JavaScript imports, tactics, or proof-search
dependencies.

The production module also reserves a 2 MiB stack and enables integer
overflow checks.  A panic aborts the one-shot worker; the main page reports
the shadow as unavailable while preserving the earlier Python QED.

## Reproducible build

The crate pins Rust 1.95.0 and `wasm32-unknown-unknown`.  From this directory:

```text
cargo test --locked
cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings
cargo build --locked --release --target wasm32-unknown-unknown
```

The production artifact is
`target/wasm32-unknown-unknown/release/peano_kernel_shadow_wasm.wasm`.
Release builds use one codegen unit, fat LTO, size optimization, stripped
symbols, disabled incremental compilation, and abort-on-panic.  Rust 2024
requires `#[unsafe(no_mangle)]` on exported symbols; the wrapper contains no
unsafe block, unsafe function, raw-pointer dereference, or caller-owned memory.
