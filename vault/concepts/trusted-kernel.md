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

## Related

[[peano-lab]] · [[proof-certificate]] · [[self-contained-proof-sharing]] ·
[[substitution]] · [[natural-deduction]]
