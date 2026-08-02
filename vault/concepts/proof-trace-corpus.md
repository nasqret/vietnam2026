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

The corpus rebuilt against the 247-theorem runtime has fingerprint
`6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`.
Its focused library smoke has 494 sessions, 9,235 raw/9,232 unique
transitions, and 247 kernel-checked QED endpoints.

A trace row is not a complete [[proof-certificate]] or standalone proof-state snapshot. It is a
supervised transition example. The source session and the independent [[trusted-kernel]] remain
the authority for whether the complete trajectory proves its original theorem.

Model-v3 has two separately identifiable sources: 247 predecessor-prefix library sessions with
8,494 transitions and a 32,600-session, 70,000-transition root-balanced synthetic population.
Historical WMI job `172729` generated both sources, continuation `173040` independently replayed
and audited them, and job `213641` published the exact fifteen-file immutable, non-replacing seal
with content SHA-256
`7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b`. A completed release is not
“whatever is under `data/`”: it is this content-addressed object. Current training retains all
library transitions and chooses only complete synthetic sessions under its audited ceiling. The
first selected-curriculum audit, job `214264`, measured 73,446,475 train tokens and failed closed
against the 70,000,000-token linear ceiling before runtime smoke or model loading. Its reviewed
retry raised only that ceiling to 74,000,000. Job `217123` then passed the complete token audit for
the same selection: 415,247,631,205 squared train tokens, maximum sequence length 29,111, and
maximum supervised completion 936. Its later saved-policy smoke admission failed on a retained
Accelerate forward wrapper, so production training remains pending.

## Related

- [[kernel-judged-evaluation]]
- [[pass-at-k]]
- [[genealogy-safe-proof-data-split]]
- [[kernel-guided-policy-training]]
- [[tactical]]
- [[peano-lab]]
