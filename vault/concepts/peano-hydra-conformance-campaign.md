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

The retained H0 run passed from clean commit
`26c2503b36c6884bfbfa6dabd1494bbda49d8926`. Its two cold roots are both
`fae19fad55c416ae7b695107390c1c733d6740fe63d10cf0efed127f5801b9d2`.
Lean agreed on all 2,058 original/wrong-target/mutation artifact cases. Rust
agreed on 2,047 portable cases and classified eleven outside its registered
envelope; WASM agreed on 1,790 portable cases and classified 268 outside its
envelope. No implementation disagreed in-envelope. The report also retains
seven macro fixtures, accept/rollback traces, Dispatch hash preimages with a
fresh original-goal kernel check, and 110 focused macro tests. The canonical
report is `artifacts/peano-hydra/h0-validation-v2.json`, SHA-256
`55c60502b2229f4420bd4557058842bebb582f491739e82a6dae06de5b803fdb`.
Report v1 is provisional H0.1/H0.2 evidence only.

## Related

- [[peano-hydra]]
- [[peano-hydra-result-evidence]]
- [[peano-hydra-semantic-profile]]
- [[macro-proof-action]]
- [[library-epoch]]
- [[trusted-kernel]]
