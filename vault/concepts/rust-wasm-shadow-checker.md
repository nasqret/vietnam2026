---
title: Rust/WASM shadow checker
tags: [kernel, rust, wasm, browser, differential-testing]
---

The **Rust/WASM shadow checker** is an independent diagnostic implementation
of Peano Lab's [[trusted-kernel]] judgment. It consumes canonical
[[proof-certificate]] bytes only after the authoritative Python kernel has
checked the proof owner's original theorem and published QED.

It runs in a separate one-shot Web Worker with bounded bytes, decoded nodes,
depth, checker work, linear memory, and wall time. Its outcomes are *shadow
agreement*, *shadow disagreement*, or *shadow unavailable*. None grants or
retracts QED. HA and the explicit classical DNE extension remain separate
logic modes.

The raw WebAssembly wrapper has no third-party dependency or imported host
function. It owns the input allocation and never dereferences a caller-owned
pointer. The underlying Rust core forbids unsafe code. Fixed-width index
headroom prevents native 64-bit and wasm32 arithmetic from disagreeing near
the wire boundary.

This is cross-implementation evidence under the [[de-bruijn-criterion]], not
a second theorem authority. Traps and timeouts are isolated availability
failures in the [[browser-proof-runtime]].

## Related

[[trusted-kernel]] · [[proof-certificate]] · [[browser-proof-runtime]] ·
[[peano-lab]] · [[de-bruijn-criterion]]
