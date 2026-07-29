# Foundational arithmetic research corpus

This directory is the planning and provenance source for Peano Lab's general
arithmetic library. Start with:

The current runtime contains 247 checked entries and the factorization tranche
is fully synchronized. The exact native β-coded endpoints are checked
from the empty context:

| Endpoint | Nodes | Depth | Cuts |
|---|---:|---:|---:|
| `prime_factorization_existence` | 43,973 | 98 | 1,328 |
| `prime_factorization_uniqueness` | 29,789 | 82 | 854 |
| `fundamental_theorem_of_arithmetic` | 73,767 | 99 | 2,184 |

The exact FTA certificate has SHA-256
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It passes the full prove/use/exact/QED route under the current 100,000-node,
depth-256 cap. The certificate uses only PA1–PA6 and induction, contains no
DNE, and has passed dependency, hypothesis, PA-rule, and semantic mutation
audits.

The constructive prime endpoint is checked as well. `prime_unbounded` takes a
nonzero common multiple through the supplied bound, chooses a prime divisor of
its successor, and proves it cannot lie at or below the bound: otherwise it
would divide both consecutive numbers and hence one. Its exact certificate is
4,595 nodes/depth 82/146 Cuts with SHA-256
`8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
It uses PA1–PA6 only, contains no DNE, and passes exact dependency, PA,
hypothesis, and live-use audits.

This is a native PA result in the selected conservative encoding, not a claim
that Peano Lab has gained primitive lists. Factors and prefix products are
Gödel-β coded; uniqueness proves equal lengths and equality of every decoded
bounded entry. It deliberately does not equate raw codes, because distinct
codes may represent the same finite prefix. Runtime/catalog synchronization is
complete.

- [`catalog.json`](catalog.json): the dependency-ordered theorem and planning
  register, including exact Peano statements, source IDs, blockers, and the
  factorization integration tranche;
- [`source-register.json`](source-register.json): pinned revisions, licenses,
  resources, and reuse modes;
- [`finite-factorization-encoding.md`](finite-factorization-encoding.md): the
  selected conservative Gödel-β factor-sequence and prefix-product design,
  its checked decoded-value, recoding, product, canonical-factorization, and
  exact FTA endpoints;
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
companion; that conventional list theorem remains independent of the native
β-coded certificate and never supplies Peano theorem authority. The catalog
has no remaining planned entry. Conventional integer-coefficient Bézout is not
available in the natural-only term language, while the checked balanced
four-natural relation supplies the native replacement.
