# Foundational arithmetic research corpus

This directory is the planning and provenance source for Peano Lab's general
arithmetic library. Start with:

The current runtime/catalog boundary is 189 checked Peano entries (23
baseline, 154 general foundational, and twelve fixed modular) inside a
196-node catalog. Exact shared-certificate totals are reproduced in the
generated snapshot: 242,629 proof nodes, 6,895 self-contained Cuts, and 149
Cut-bearing certificates. `bounded_beta_crt_for_existing_code` is largest
at 25,545 nodes and 755 Cuts; `prime_divisor_exists` sets the snapshot-wide
maximum depth at 80.
The latest tranches establish full additive/multiplicative balanced-congruence
compatibility, bounded representative uniqueness, both remainder/congruence
directions, expanded β decoding equivalent to bound plus congruence,
constructive binary CRT, conditional β-modulus coprimality when an ordered
index gap divides `c`, its two-position β-code client, and bounded
nonzero common multiples. Unconditional pairwise coprimality is false. The
bounded-prefix form, coprime-product closure, modulus descent, and the combined
accumulated-product/decoded-congruence prefix invariant are now checked. Its
wrapper is restricted to residues already decoded from a supplied `BetaAt`
code and is not arbitrary finite-sequence coding. Genuine prefix-product
recurrence and bounds, β finite-prefix recoding, greatest-prime descent, and
native FTA remain open.

- [`catalog.json`](catalog.json): 196 dependency-ordered facts — 23
  `checked_existing`, 166 `checked_m20`, three `planned_expressible`, and four
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
