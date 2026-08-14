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
until restart. Its three-file pack remains a provenance-only protocol fixture.

A separate subordinate candidate replay pack now carries all 384 canonical
`peano-lab-v2` artifacts. Replay-pack schema v1 has semantic digest
`d60b07fe68aa4ba023c9bb873e2df4190752f70252caca21da7e76dcd393f02d`;
the pack has manifest root
`fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d`
and fresh-worker recomputed theorem replay root
`88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba`.
A fresh `python -I -S -X pycache_prefix=<fresh-dir>` worker blocks the living
library, tactic engine, UI, training package, and model stacks, binds each
decoded target to its original closed statement, and asks the [[trusted-kernel]]
to check all 384 proofs from the empty context. The committed acceptance test
reproduces its retained report byte-for-byte.

H1.1a adds a candidate-only metadata readiness ledger above that transport.
Schema v1 has semantic digest
`71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c`;
the canonical 5,880,054-byte ledger has root
`b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279`.
It binds all 384 source locators and 1,038 declared publication edges. Atlas
and vault receipts cover every theorem, but the two proof explorers and the
theorem-level definition edition cover only 240 rows. The other 144 rows are
missing, not stale. All 317 additional explorer names are disjoint non-$L_0$
provenance; the full 557-row corpora cannot become epoch retrieval, training,
or evaluation context.

This closes the replay-transport subgate, not H1.1. The pack is schema-labeled
`candidate` and evaluation-ineligible. It still lacks independently verified
readable/optimized dependency views and publication union, 144 complete
definition/documentation receipts, human review, best-known comparison,
lineage masks, reviewed source-state and owner deposit, and the sealed
benchmark. The production owner-receipt registry remains empty, so it is not
frozen production $L_0$.

## Related

- [[content-addressed-lemma-library]]
- [[lemma-dependency-dag]]
- [[genealogy-safe-proof-data-split]]
- [[arithmetic-library-moc]]
- [[peano-lab-moc]]
