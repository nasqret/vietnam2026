---
title: Library epoch
tags: [peano-lab, theorem-library, provenance, evaluation]
---

# Library epoch

A **library epoch** is an immutable ordered view of the checked theorem
library used by one evaluation campaign. Its root commits to each theorem's
canonical statement, ordered dependencies, source/script/certificate hashes,
proof metrics, readable and optimized proof identities, documentation receipts,
declaration order, and logic profile.

In [[peano-hydra]], the 384-theorem H0 replay corpus is only the minimum
candidate for $L_0$; H1 has not frozen it yet. The
[[peano-authoring-assistant]] in `authoring-live` mode may follow reviewed
library HEAD continuously. A research
epoch is instead physically copied and content-addressed, with no path that
resolves back to the living catalog. Training may use eligible frozen material,
but a [[sealed-theorem-benchmark]] must be lineage-disjoint. Mathematics added
after the freeze belongs to $L_1$ or later and cannot enter the active
campaign's prompts, retrieval index, imports, documentation context, or
headline test.

An epoch hash records identity; it does not grant theorem authority. Each
certificate still passes the [[trusted-kernel]].

Epoch-protocol schema v1 has digest
`f4695013ee4aeb660abf3a1e57a6334d86c990a8904c4435d94628694a2e875b`.
Its living candidate revalidates HEAD and all 384 theorems, uses type-exact
roots/versions, bounded no-follow reads, and rejects source drift after import
until restart. Its current three-file pack is only a protocol fixture: it has
catalog/profile/H0 provenance but no formula/certificate bytes. The production
owner-receipt registry is empty, so the 38 focused tests do not constitute an
$L_0$ freeze. H1.1 closes only after an isolated replay-complete pack exists.

## Related

- [[content-addressed-lemma-library]]
- [[lemma-dependency-dag]]
- [[genealogy-safe-proof-data-split]]
- [[arithmetic-library-moc]]
- [[peano-lab-moc]]
