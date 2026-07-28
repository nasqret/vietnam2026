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

A separately maintained candidate library passed its private compatibility gate against Peano Lab.
Neither its source nor identifying validation metadata enters the public repository until the owner
chooses a visibility boundary. A private snapshot can still be content-addressed for training
without silently widening the public theorem catalog.

Library visibility and benchmark visibility are different. If a theorem is importable, closing its
exact statement with `use`, `apply`, and `exact` measures retrieval and application, not discovery.
Sealed evaluation roots and descendants must remain outside training, retrieval, and development.

## Related

[[checked-theorem-reuse]] · [[kernel-guided-policy-training]] ·
[[genealogy-safe-proof-data-split]] · [[kernel-judged-evaluation]]
