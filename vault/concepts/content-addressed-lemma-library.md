---
title: Content-addressed lemma library
tags: [peano-lab, theorem-library, llm, provenance, evaluation]
---

# Content-addressed lemma library

A **content-addressed lemma library** freezes more than a list of names. For every theorem it binds
the canonical closed statement, direct dependencies, source revision, authored proof-script hash,
independently checked certificate-representation hash, node count, and depth. Administrative
normalization preserves [[self-contained-proof-sharing|self-contained Cuts]], so the representation
version and root digest must distinguish shared certificates from earlier expanded trees. One digest
of the ordered snapshot then enters policy prompts, datasets, training manifests, evaluator reports,
and proof requests.

This matters because a command/theorem-name capability hash cannot distinguish two libraries that
reuse a name for different statements. The [[trusted-kernel]] still protects soundness, but the
scientific identity of a trained policy would be ambiguous. Adding or changing any lemma therefore
creates `model-v3`, never a silent widening of `model-v2`.

Content addressing is provenance, not proof authority. No hash is stored as an admissible theorem
reference inside Cut; the full formula and proof branches remain present and are checked.

The owner authorized the compatibility-checked 26-record candidate for
publication. The retained source commit, catalog hash, MIT notice, proof
hashes, node counts, and depths make the import auditable. After reconciliation
with the M20 [[theorem-ladder]], fourteen records overlap exactly and twelve
were new, yielding the earlier 63-theorem content-addressed runtime snapshot.
The subsequent native division/order extension yields a new 104-theorem root;
the gcd/coprimality API yields a further 119-theorem root, and checked
Euclidean gcd invariance yields the current 125-theorem root. Each must receive a
distinct registered policy-library identity. Model-v1
remains frozen, and no model may silently inherit either mutable catalog.

Library visibility and benchmark visibility are different. If a theorem is importable, closing its
exact statement with `use`, `apply`, and `exact` measures retrieval and application, not discovery.
Sealed evaluation roots and descendants must remain outside training, retrieval, and development.

## Related

[[checked-theorem-reuse]] · [[kernel-guided-policy-training]] ·
[[self-contained-proof-sharing]] · [[genealogy-safe-proof-data-split]] ·
[[kernel-judged-evaluation]]
