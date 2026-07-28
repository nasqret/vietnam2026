---
title: Content-addressed lemma library
tags: [peano-lab, theorem-library, llm, provenance, evaluation]
---

# Content-addressed lemma library

A **content-addressed lemma library** freezes more than a list of names. For every theorem it binds
the canonical closed statement, direct dependencies, source revision, authored proof-script hash,
independently checked cut-normal certificate hash, node count, and depth. One digest of the ordered
snapshot then enters policy prompts, datasets, training manifests, evaluator reports, and proof
requests.

This matters because a command/theorem-name capability hash cannot distinguish two libraries that
reuse a name for different statements. The [[trusted-kernel]] still protects soundness, but the
scientific identity of a trained policy would be ambiguous. Adding or changing any lemma therefore
creates `model-v3`, never a silent widening of `model-v2`.

The owner authorized the compatibility-checked 26-record candidate for
publication. The retained source commit, catalog hash, MIT notice, proof
hashes, node counts, and depths make the import auditable. After reconciliation
with the M20 [[theorem-ladder]], fourteen records overlap exactly and twelve
are new, yielding a 63-theorem content-addressed runtime snapshot. Model-v1
remains frozen; model-v2 must bind this exact combined snapshot rather than
silently inheriting a mutable catalog.

Library visibility and benchmark visibility are different. If a theorem is importable, closing its
exact statement with `use`, `apply`, and `exact` measures retrieval and application, not discovery.
Sealed evaluation roots and descendants must remain outside training, retrieval, and development.

## Related

[[checked-theorem-reuse]] · [[kernel-guided-policy-training]] ·
[[genealogy-safe-proof-data-split]] · [[kernel-judged-evaluation]]
