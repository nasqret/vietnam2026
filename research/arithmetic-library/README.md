# Foundational arithmetic research corpus

This directory is the planning and provenance source for Peano Lab's general
arithmetic library. Start with:

The current runtime/catalog boundary is 137 checked Peano entries (23
baseline, 102 general foundational, and twelve fixed modular) inside a
148-node catalog. Exact shared-certificate totals are reproduced in the
generated snapshot: 52,433 proof nodes, 1,345 Cuts, and 98 Cut-bearing
certificates. `euclid_prime_dvd_product` is largest at 5,382 nodes and 159
Cuts; the snapshot-wide maximum depth is 57.

- [`catalog.json`](catalog.json): 148 dependency-ordered facts — 23
  `checked_existing`, 114 `checked_m20`, seven `planned_expressible`, and four
  `blocked_by_language` — with exact source IDs, Peano statements where
  expressible, and blockers where not;
- [`source-register.json`](source-register.json): pinned revisions, licenses,
  resources, and reuse modes;
- [`finite-factorization-encoding.md`](finite-factorization-encoding.md): the
  selected conservative Gödel-β factor-sequence and prefix-product design,
  its exact FTA endpoints, and its Peano proof dependency spine;
- [`gcd-bezout-roadmap.md`](gcd-bezout-roadmap.md): the checked relational API,
  Euclidean-invariance ladder, simultaneous bounded gcd/Bézout construction,
  Gauss cancellation, and Euclid's lemma;
- [`proof-sharing-design.md`](proof-sharing-design.md): the reviewed
  self-contained Cut rule, trust boundary, structural integration, and honest
  erasure limitation;
- [`foundational-sources.md`](foundational-sources.md): clean-room workflow and
  the cross-source dependency architecture;
- [`nng4-map.md`](nng4-map.md): complete Natural Number Game 4 coverage and
  exclusions;
- [`math2001-map.md`](math2001-map.md): Macbeth curriculum mapping and
  reference-only boundary;
- [`illustrated-number-theory-map.md`](illustrated-number-theory-map.md):
  Weissman notebook/application roadmap and GPL boundary.

Validate the strict JSON, source links, DAG order, current-language formulas,
and exact checked-runtime coverage with:

```bash
python3 scripts/verify_arithmetic_knowledge_base.py
```

The catalog is not theorem authority. Only entries whose replayed,
self-contained certificates pass Peano Lab's independent kernel from the empty
context appear as checked. Dependency Cuts embed complete proof branches and
never grant names or hashes authority. Planned and
language-blocked nodes make the roadmap precise without overstating the
current implementation. The catalog separately binds one checked Lean FTA
companion; companion status never counts as Peano runtime coverage.
