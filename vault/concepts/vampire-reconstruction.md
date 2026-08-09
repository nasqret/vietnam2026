---
title: Vampire reconstruction
tags: [peano-lab, vampire, symbolic-search, proof-reconstruction]
---

# Vampire reconstruction

**Vampire reconstruction** is the A3 use of the classical first-order prover
as an untrusted search head inside [[peano-hydra]]. The first executable slice
now emits deterministic TPTP FOF for one closed primitive-PA goal and an
explicitly allowed premise subset, retains a source-symbol map, and parses
bounded SZS output as inert evidence. Its only reconstruction case is a
top-level reflexive equality to the ordinary public command `refl`; every
other solver success is commandless.

A raw SZS status, unsatisfiability result, clausified proof, or foreign symbol
has no theorem authority. Counted success requires a complete
[[proof-certificate]] checked against the original Peano formula by the
[[trusted-kernel]]. Exact translator, symbol map, binary, options, transcript,
premises, limits, and reconstruction trace belong to the evidence bundle.

The current tests use fake executables to exercise the real copied-and-rehashed
direct-binary, timeout, output, parser, rollback, and fresh-kernel boundaries.
No Vampire binary has been installed or run, so there is no solver-capability
result. Frozen H0 `Dispatch` also allows one process: a source broker plus a
separate Vampire binary needs a reviewed protocol amendment or one
self-contained executable before it can be registered.

## Related

[[critical-proof-frontier]] · [[peano-logic-profiles]] ·
[[matched-compute-proof-evaluation]] · [[peano-authoring-assistant]]
