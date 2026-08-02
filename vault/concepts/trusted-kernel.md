---
title: Trusted kernel
tags: [kernel, soundness, de-bruijn-criterion]
---

A **trusted kernel** is the small component whose correctness determines whether the prover can
accept a false theorem. Peano Lab's kernel contains only syntax, capture-safe substitution, inert
proof-term constructors, and an independent structural checker. It imports nothing from tactics or
the browser UI.

Its proof grammar includes [[self-contained-proof-sharing|self-contained Cut]]. For
`Cut(A,B,lemma,body)`, the checker verifies `lemma : A` once in the ambient context and verifies
`body : B` under a new hypothesis `A`. This genuinely enlarges the trusted checker, but adds no
object-language symbol, PA axiom, theorem name, hash lookup, or classical principle.

Every QED is checked against the *original* stated goal. Search, simplification, library replay,
engine-only local-cut compilation, trusted-Cut erasure, and Lean export all remain outside this
boundary. Their bugs can cause failure or misleading presentation, but cannot make the checker
return true for an invalid [[proof-certificate]]. The untrusted normalizer preserves trusted Cuts;
the kernel checks their embedded branches directly.

This applies the De Bruijn criterion: a proof assistant should emit a certificate checkable by a
small, independently understandable program.

## Lean metaverification

The separate
[`nasqret/peano-lab-lean`](https://github.com/nasqret/peano-lab-lean)
formalization proves the chain `check → Derives → standard-Nat truth`, including
`Artifact.check_sound` for canonical inert bytes. The theorem is relative to
Lean's kernel and reported standard axioms. Python correspondence is supported
by source mirroring and differential tests rather than an exhaustive CPython
equivalence theorem.

WMI job `211445` is the immutable receipt for the historical cut-free v1
snapshot. Cut-aware `peano-lab-v2` source
[`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
passed pinned Lean 4.31/WMI job
[`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358)
in `00:03:03` with exit `0:0`. It verified Git tree
`c4eccf6bc0037c4b1f5f2752747277db0220b1c3` and the 307,200-byte source
archive SHA-256
`da4d6e7c30343e11042e659ae1578ace0168e66bde5b1b07505f535aee873c7b`.
Readable predicates such as `Prime`, `Dvd`, or `BetaAt` remain outside both
kernels: they expand hygienically to ordinary formulas before checking.

## Related

[[peano-lab]] · [[proof-certificate]] · [[self-contained-proof-sharing]] ·
[[substitution]] · [[natural-deduction]]
