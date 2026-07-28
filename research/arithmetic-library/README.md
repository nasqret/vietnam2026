# Foundational arithmetic research corpus

This directory is the planning and provenance source for Peano Lab's general
arithmetic library. Start with:

The current runtime/catalog boundary is 164 checked Peano entries (23
baseline, 129 general foundational, and twelve fixed modular) inside a
171-node catalog. Exact shared-certificate totals are reproduced in the
generated snapshot: 79,763 proof nodes, 2,138 self-contained Cuts, and 124
Cut-bearing certificates. `euclid_prime_dvd_product` remains largest at 5,382
nodes and 159 Cuts; `prime_divisor_exists` sets the snapshot-wide maximum
depth at 80.
The latest tranches establish full additive/multiplicative balanced-congruence
compatibility, bounded representative uniqueness, both remainder/congruence
directions, and expanded β decoding equivalent to bound plus congruence.
β-modulus coprimality, binary/bounded CRT, finite-prefix extension and
products, greatest-prime descent, and native FTA remain open.

- [`catalog.json`](catalog.json): 171 dependency-ordered facts — 23
  `checked_existing`, 141 `checked_m20`, three `planned_expressible`, and four
  `blocked_by_language` — with exact source IDs, Peano statements where
  expressible, and blockers where not;
- [`source-register.json`](source-register.json): pinned revisions, licenses,
  resources, and reuse modes;
- [`finite-factorization-encoding.md`](finite-factorization-encoding.md): the
  selected conservative Gödel-β factor-sequence and prefix-product design,
  its checked decoded-value foundation, exact FTA endpoints, and remaining
  CRT/product dependency spine;
- [`gcd-bezout-roadmap.md`](gcd-bezout-roadmap.md): the checked relational API,
  Euclidean-invariance ladder, simultaneous bounded gcd/Bézout construction,
  Gauss cancellation, Euclid's lemma, and the constructive factor-search and
  prime-divisor milestone;
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
