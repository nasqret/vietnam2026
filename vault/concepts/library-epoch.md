---
title: Library epoch
tags: [peano-lab, theorem-library, provenance, evaluation]
---

# Library epoch

A **library epoch** is an immutable ordered view of the checked theorem
library used by one evaluation campaign. Its root commits to each theorem's
canonical statement, ordered dependencies, source/script/certificate hashes,
proof nodes and depth, declaration order, and logic profile.

In [[peano-hydra]], the initial epoch $L_0$ contains at least the current 247
checked runtime theorems. Training may use eligible $L_0$ material, but a
[[sealed-theorem-benchmark]] must be lineage-disjoint. Mathematics added after
the freeze belongs to $L_1$ or later and cannot enter the active campaign's
prompts, retrieval index, imports, or headline test.

An epoch hash records identity; it does not grant theorem authority. Each
certificate still passes the [[trusted-kernel]].

## Related

- [[content-addressed-lemma-library]]
- [[lemma-dependency-dag]]
- [[genealogy-safe-proof-data-split]]
- [[arithmetic-library-moc]]
- [[peano-lab-moc]]
