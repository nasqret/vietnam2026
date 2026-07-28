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

The corpus rebuilt against the 176-theorem runtime has run fingerprint
`f44b6eb716116063bd24b849d737345f0c9c23240fa8536d1ed25fdc1ae05d56`.
Its focused library smoke contains 352 sessions, 4,729 raw transitions, 4,726
unique transitions, and 176 kernel-checked QED endpoints.

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
