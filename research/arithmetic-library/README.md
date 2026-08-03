# Foundational arithmetic research corpus

This directory is the planning and provenance source for Peano Lab's general
arithmetic library. Start with:

- [`ha-number-theory-formalization-campaign-blueprint.md`](ha-number-theory-formalization-campaign-blueprint.md):
  the byte-frozen controlling blueprint for the strict-HA number-theory
  campaign;
- [`ha-number-theory-campaign.json`](ha-number-theory-campaign.json): the
  executable K0--K6/M1--M5 layer status, dependency, and validation-gate
  manifest;
- [`ha-definition-representation-freeze-v1.md`](ha-definition-representation-freeze-v1.md)
  and its [machine companion](ha-definition-representation-freeze-v1.json):
  the first exact definition boundary, including the K3 quarantine on using
  beta/CRT coding as foundational list infrastructure;
- [`ha-canonical-signed-natural-rfc-v1.md`](ha-canonical-signed-natural-rfc-v1.md):
  the selected parity-interleaved canonical signed-natural representation,
  eight exact expanded predicates, dependency prohibitions, and proof DAG;
- [`../../PLAN/12_ha_number_theory_campaign.md`](../../PLAN/12_ha_number_theory_campaign.md):
  the repository execution plan and first canonical-interface tranche.

Run `make ha-number-theory-check` from the repository root for the fast
campaign-manifest, 44-theorem definition-API replay, candidate-body, and
empty-context receipt checks. The campaign manifest carries 38 statement
hashes and exact closure receipts: nine deliberately admitted tranche-01
theorems, three isolated canonical-gcd candidates, and 26 isolated signed
parity, decoder, code-extensionality, balance-normalization, and negation
candidates. Passing the candidate gate alone never enrolls a theorem in the
public registry.

The current runtime contains 393 checked entries. The factorization tranche
is fully synchronized. The exact native β-coded endpoints are checked
from the empty context:

| Endpoint | Nodes | Depth | Cuts |
|---|---:|---:|---:|
| `prime_factorization_existence` | 43,973 | 98 | 1,328 |
| `prime_factorization_uniqueness` | 29,789 | 82 | 854 |
| `fundamental_theorem_of_arithmetic` | 73,767 | 99 | 2,184 |

The exact FTA certificate has SHA-256
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It passes the full prove/use/exact/QED route under the current
500,000-occurrence, 100,000-object, depth-256 cap. The certificate uses only
PA1–PA6 and induction, contains no
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

The 137-entry quadratic-reciprocity public checkpoint remains intact, followed
by the nine public canonical remainder/congruence/modular-inverse interfaces
from strict-HA tranche 01. The reciprocity
checkpoint: parity and modulo-four facts, constructive quadratic-residue
decision, constant and interval prefixes, relational powers, β-coded finite
sums, constructive finite permutation completeness, replacement balance, and
exact swap-last product invariance. Beyond that admitted checkpoint, the exact
quadratic-reciprocity route is now body-green through arbitrary Euler and
Gauss, the signed-count/floor-sum parity bridge, native Eisenstein Fubini,
`Q+U=h*k`, both QRes truth cases, and the optimized combined endpoint. This is
a genuine dependency-curried PA body, not a public admission. The exact
557-spec/1,787-edge graph has 45 layers, 241 public nodes, 316 candidate nodes,
and 191,648 theorem occurrences under
recursive expansion; a rigorous 731,423-node lower bound rules that compiler
out under the current policy. Layered WMI closure, mutation, capacity,
browser, and separate pinned-admission receipts are still mandatory. The
unchanged-kernel compiler accepts an exact-topology distinct-marker surrogate
at 19,066 nodes/depth 74. One dependency Cut/Hyp check per curried premise
forces every real projection ID/direction and dependency order; no real QR
target or body occurs in that test.

- [`catalog.json`](catalog.json): the dependency-ordered theorem and planning
  register, including exact Peano statements, source IDs, blockers, and the
  factorization integration tranche;
- [`source-register.json`](source-register.json): pinned revisions, licenses,
  resources, and reuse modes;
- [`finite-factorization-encoding.md`](finite-factorization-encoding.md): the
  selected conservative Gödel-β factor-sequence and prefix-product design,
  its checked decoded-value, recoding, product, canonical-factorization, and
  exact FTA endpoints;
- [`product-permutation-invariance.md`](product-permutation-invariance.md):
  the active conservative statement, fixed-last/simultaneous-swap induction
  architecture, and admission gates for general β-coded product reindexing;
- [`fermat-wilson-next-tranche.md`](fermat-wilson-next-tranche.md): the exact
  Fermat-first residue-product ladder, the separate Wilson involution gate,
  and their roles in the Euler/Gauss/Eisenstein route to reciprocity;
- [`pair-order-encoding.md`](pair-order-encoding.md): the nine-candidate
  constructive two-entry extension layer for Wilson inverse orbits, its
  reusable generic core, the corrected fifteen-candidate bounded-state and
  terminal-coverage follow-on, paired-history iteration, successor lift,
  product-one endpoint, canonical nonendpoint product transport, endpoint
  restoration, and the body-green exact Wilson congruence;
- [`euler-scaled-inverse.md`](euler-scaled-inverse.md): the ten-candidate
  bounded scaled-inverse relation, functionality, involution, fixed-point
  characterization, full beta-prefix/extensional layers, the generic adjacent-
  target product fold, both branches and the arbitrary-unit packaging of
  Euler's criterion, and the representation-correct shifted one-orbit
  PairOrder entrance;
- [`gauss-signed-prefix-design.md`](gauss-signed-prefix-design.md): the
  isolated two-code signed-half prefix representation, seven-candidate body
  ladder, focused WMI audit, and exact magnitude-permutation boundary;
- [`gauss-magnitude-permutation.md`](gauss-magnitude-permutation.md): the
  eleven-candidate magnitude range/injectivity/predecessor-permutation
  endpoint, its focused WMI design, body-valid sign/pointwise recodings, and
  the composed constructive cancellation at the heart of Gauss's lemma;
- [`eisenstein-division-prefix.md`](eisenstein-division-prefix.md): the native
  beta-coded quotient/remainder prefix relation, exact scaled sources,
  constructive cell orientation, nested semantic row/rectangle counts, and
  the quotient threshold, sound distinct-prime remainder-nonzero layer and
  odd-half quotient bound, exact initial-segment `BitCount` ladder, generic
  pointwise beta-sum transport, row-count identification, native nested
  transpose/Fubini, the exact two-orientation quotient identity, and terminal
  parity cancellation;
- [`quadratic-reciprocity-surface.md`](quadratic-reciprocity-surface.md): the
  frozen code-free theorem formulas, representation choices, body-green
  Gauss--Eisenstein route, and explicit admission boundary;
- [`finite-fold-surface.md`](finite-fold-surface.md): the reusable native
  `Pow`, `Sum`, `Count`, range, permutation, and product interfaces underlying
  the reciprocity proof;
- [`quadratic-reciprocity-capacity.md`](quadratic-reciprocity-capacity.md):
  structural/object/depth policy, FTA baseline, QR lower bound, and the
  measured scaffold evidence for the selected compiler;
- [`quadratic-reciprocity-closure-hotspots.md`](quadratic-reciprocity-closure-hotspots.md):
  the exact recursive-closure recurrence, hotspot audit, and rigorous
  731,423-node lower bound against the 500,000-node policy;
- [`layered-cut-bundle.md`](layered-cut-bundle.md): the preferred unchanged-
  kernel compiler, using 45 balanced conjunction packages, 45 ordinary Cuts,
  and short existing conjunction projections so every modular body appears
  once;
- [`quadratic-reciprocity-admission-path.md`](quadratic-reciprocity-admission-path.md):
  the post-WMI public migration design, including the injection-based registry
  refactor, exact 316-ancestor-plus-root enrollment, replay strategy, catalog,
  UI, and Pyodide gates;
- [`quadratic-reciprocity-test-migration.md`](quadratic-reciprocity-test-migration.md):
  the exact `rg` audit of candidate tests that assume non-registration, the
  317-enrolled/29-omitted partition, and the safe modular-body/public-replay
  migration recipe;
- [`pa-proof-explorer.md`](pa-proof-explorer.md): the Stacks-style permanent
  tag policy, LeanBlueprint-style dependency/status model, tactic-line linking
  rules, informal-proof overlay, foundations atlas, and deterministic release
  gates for the 557-node QR proof explorer;
- [`curation-policy.md`](curation-policy.md): the conservative P0/P1/P2
  definition tiers, relation API matrix, paired-edition identity gates, and
  release checklist for the next native library edition;
- [`closed-proof-dag.md`](closed-proof-dag.md): the explicitly secondary
  bundle-checker design, retained only if the ordinary layered certificate
  fails a measured resource or browser gate;
- [`wmi-qr-replay.md`](wmi-qr-replay.md): content-addressed WMI replay policy,
  Slurm provenance, resource receipts, and the evidence required before an
  isolated quadratic-reciprocity candidate may enter the public registry;
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
