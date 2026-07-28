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
creates a new versioned authority, never a silent widening of an existing one.

The public [[theorem-ladder]] now contains 63 items: the original 23, 14 compatibility-audited
general-arithmetic additions, and the 26-entry modular extension. Retained source and audited-merge
commits, catalog roots, license notices, proof hashes, node counts, and depths make both integrations
auditable. Model-v1 remains frozen. Every training authority likewise binds one exact snapshot;
adding these lemmas does not silently widen an earlier authority.

The current ordered public root is
`d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`.
Model-v2 has four benchmark goals but seven excluded imports: the four roots `le_trans`,
`le_antisymm`, `le_total`, and `mul_eq_zero`, plus the reverse-dependency descendants
`mul_ne_zero`, `two_large_factors_impossible`, and `prime_two`. It permits the remaining 56 entries.
Its complete independently replayed identity is
`3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439` (SHA-256), distinct from the
smaller name/statement projection shown to the policy.

Library visibility and benchmark visibility are different. If a theorem is importable, closing its
exact statement with `use`, `apply`, and `exact` measures retrieval and application, not discovery.
Sealed evaluation roots and descendants must remain outside training imports, retrieval, and
development data, even though only the four roots are evaluation goals.

## Related

[[checked-theorem-reuse]] · [[kernel-guided-policy-training]] ·
[[genealogy-safe-proof-data-split]] · [[kernel-judged-evaluation]]
