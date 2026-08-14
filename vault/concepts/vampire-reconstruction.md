---
title: Vampire reconstruction
tags: [peano-lab, vampire, symbolic-search, proof-reconstruction]
---

# Vampire reconstruction

**Vampire reconstruction** is the A3 use of the classical first-order prover
as an untrusted search head inside [[peano-hydra]]. The first executable slice
now emits deterministic TPTP FOF for one closed primitive-PA goal and an
explicitly allowed premise subset, retains a source-symbol map, and parses
bounded SZS output as inert evidence. Reconstruction v3 emits ordinary public
commands only for top-level reflexivity, one selected PA axiom, one selected
public theorem, or a top-level conjunction with exactly two selected PA axioms
in branch order. These become `refl`, `apply NAME`, `use NAME; apply NAME`, or
`split; apply NAME1; apply NAME2`; every other multi-premise case is
commandless. Swapped and irrelevant plans fail transactionally.

A raw SZS status, unsatisfiability result, clausified proof, or foreign symbol
has no theorem authority. Counted success requires a complete
[[proof-certificate]] checked against the original Peano formula by the
[[trusted-kernel]]. Exact translator, symbol map, binary, options, transcript,
premises, limits, and reconstruction trace belong to the evidence bundle.

Tests use fake executables to exercise the copied-and-rehashed direct-binary,
timeout, output, parser, rollback, and fresh-kernel boundaries reproducibly.
A3.1 also ran the official Vampire 5.0.1 binary directly, then performed
offline reconstruction. The temporary macOS ARM64 ZIP/executable SHA-256
values were `8c92e649fe7bc622a70000afbdf5a5c51007b384e2d8b8235c95474cc7a68f35`
and `b5168c690e0293cdac78f16d8418d7eeabcd6708f90a60cd2bf45313b6d98699`;
neither was vendored or installed. The `PA3` diagnostic for `0 + 0 = 0`
returned inert `SZS Theorem`, reconstructed `apply PA3`, and kernel-checked a
2-node/depth-2 proof term
(`encode_proof` SHA-256
`25b6f555180e9737fe4aeb0e51f1f9e97911ed9ffc41c6a80ef97088930711cd`;
complete `peano-lab-v2` artifact SHA-256
`3c65761490733d3382932780f26ff2fb382f82eb536a45af41840b172be7efca`).
The `PA3`, `PA5` conjunction TPTP hash was
`60b2666d452d253bd982170cc8c3d586c2be836ee72355a4fc108d313d403f96`;
inert `SZS Theorem` reconstructed `split; apply PA3; apply PA5`, which
kernel-checked at 5 nodes/depth 3 with proof-term
`encode_proof` SHA-256
`3d47f7636f578cbcaf638006942e19c8ff9c565359967d44b32d20668ef5f812`
and complete `peano-lab-v2` artifact SHA-256
`cc520fd2f72148dc05450c414151a55cca4a18ce528e15bb150d9ea89e493d68`.
The one-shot `scripts/peano_hydra_vampire_assist.py` preview exposes the same
offline path as canonical JSON with no default file write; its H0/live and all
eligibility flags remain false.

WMI's pinned x86-64 binary hash was
`81532e088c4ee1238d7ea1d8e868a2dccf8d358ad4d2126d257b4dda7f2e6bd9`;
real `--mode vampire` returned `SZS Theorem` on that conjunction while Vampire
reported 0.001 seconds and 8 MB. This is diagnostic evidence only—there is no
capability comparison or production integration. Frozen H0 `Dispatch` still
allows one process: a source broker plus a separate Vampire binary needs a
reviewed protocol amendment or one self-contained executable before it can be
registered live.

## Related

[[critical-proof-frontier]] · [[peano-logic-profiles]] ·
[[matched-compute-proof-evaluation]] · [[peano-authoring-assistant]]
