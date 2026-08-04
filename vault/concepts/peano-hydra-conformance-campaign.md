---
title: Peano Hydra conformance campaign
tags: [peano-lab, peano-hydra, conformance, reproducibility]
---

# Peano Hydra conformance campaign

The **Peano Hydra conformance campaign** is H0's executable test that different
implementations mean the same thing before training or benchmarking begins.

Its candidate-L0 corpus replays all 384 dependency-ordered public theorems and
adds 640 deterministic reflexive theorems, yielding 1,024 distinct positives.
Every accepted certificate is reused against one different target and must be
rejected. This is a certificate/target mutation, not a certified non-theorem.

Targeted mutations cover proof constructors, binder scope, equality
substitution, induction motive and step, DNE under intuitionistic logic,
artifact decoding, unregistered translation, and forbidden negative evidence.
The authoritative Python [[trusted-kernel]] and an exactly source-pinned Lean
reference must agree on every in-scope case. Native Rust and browser WASM are
diagnostic shadows with explicit depth, wire, index, and checker-fuel
envelopes.

Two fresh Python processes replay the complete public catalog from empty
caches. Their ordered rows and root must be identical and 100% green. The
retained controller also runs kernel-import, original-goal, and transactional
history regressions; binds all loaded implementation sources and independent
verifier identities; and checks the source tree again at the end.

This is H0 semantic evidence, not H1's immutable [[library-epoch]] or sealed
benchmark. H1 still owns genealogy, masks, and evaluation partitions.

## Related

- [[peano-hydra]]
- [[peano-hydra-result-evidence]]
- [[peano-hydra-semantic-profile]]
- [[macro-proof-action]]
- [[library-epoch]]
- [[trusted-kernel]]
