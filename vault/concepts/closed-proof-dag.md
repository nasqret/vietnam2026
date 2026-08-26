---
title: Self-contained closed-proof DAG
tags: [peano-lab, proof-certificate, proof-dag, cut, quadratic-reciprocity, trust]
---

A **self-contained closed-proof DAG** is the fallback design for repeated
recursive [[self-contained-proof-sharing|contextual Cut]] closure when many
theorems reuse the same closed dependencies. The first-choice QR experiment
is now the [[layered-cut-bundle]], because it removes recursive duplication
while leaving the production proof grammar and checker unchanged.

Each node contains a closed PA target, ordered local dependency IDs, and an
ordinary proof of the dependency-curried target. The existing
[[trusted-kernel]] checks that body exactly once from the empty context. A
topological induction justifies discharging its premises with already checked
closed nodes. IDs are local to the complete bundle: theorem names, hashes,
catalog entries, Python identities, and earlier receipts grant no authority.

The candidate rule is called `ClosedCut`, but it is not an ordinary proof
constructor and does not change contextual `Cut`. It is currently only an
experimental fallback. Promotion is considered only if the layered ordinary
certificate fails a measured object, formula, depth, memory, or Pyodide gate;
it would then require cycle/dangling/target/mutation rejection, exact resource
gates, a canonical streaming codec, WMI replay, and cold Pyodide validation.

Full design and soundness argument:
[closed-proof-dag.md](../../research/arithmetic-library/closed-proof-dag.md).

## Related

[[proof-certificate]] · [[trusted-kernel]] · [[lemma-dependency-dag]] ·
[[self-contained-proof-sharing]] · [[checked-theorem-reuse]] ·
[[browser-proof-runtime]]
