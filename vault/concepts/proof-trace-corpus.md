---
title: Proof-trace corpus
tags: [peano-lab, llm, dataset, tactics]
---

# Proof-trace corpus

Peano Lab records tactic applications as version-1 JSONL transitions: canonical goals before,
the selected focus and tactic text, canonical goals after, and an honest success or error result.
A footer records whether the session reached checked QED, its theorem, certificate size, and tactic
count.

The M9 corpus exporter validates complete sessions, removes duplicate learning transitions, and
splits theorem/session groups deterministically. Failed attempts are retained because learning
which actions do not apply is part of learning the tactic language.

The corpus rebuilt against the 183-theorem runtime has run fingerprint
`d0649a05ab1a88396d2d3046bc10a814e374cb3cf5ad8df225c9e15e91ff0df6`.
Its focused library smoke contains 366 sessions, 4,992 raw transitions, 4,989
unique transitions, and 183 kernel-checked QED endpoints.

A trace row is not a complete [[proof-certificate]] or standalone proof-state snapshot. It is a
supervised transition example. The source session and the independent [[trusted-kernel]] remain
the authority for whether the complete trajectory proves its original theorem.

## Related

- [[kernel-judged-evaluation]]
- [[pass-at-k]]
- [[genealogy-safe-proof-data-split]]
- [[kernel-guided-policy-training]]
- [[tactical]]
- [[peano-lab]]
