---
title: Trusted kernel
tags: [kernel, soundness, de-bruijn-criterion]
---

A **trusted kernel** is the small component whose correctness determines whether the prover can
accept a false theorem. Peano Lab's kernel contains only syntax, capture-safe substitution, inert
proof-term constructors, and an independent structural checker. It imports nothing from tactics or
the browser UI.

Every QED is checked against the *original* stated goal. Search, simplification, library replay,
proof-term cut elimination, and Lean export all remain outside this boundary. Their bugs can cause
failure or misleading presentation, but cannot make the checker return true for an invalid
[[proof-certificate]].

This applies the De Bruijn criterion: a proof assistant should emit a certificate checkable by a
small, independently understandable program.

## Related

[[peano-lab]] · [[proof-certificate]] · [[substitution]] · [[natural-deduction]]
