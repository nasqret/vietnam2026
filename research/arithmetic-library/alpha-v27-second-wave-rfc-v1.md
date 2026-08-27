# Alpha v27: complete named second-wave targets

Date: 2026-08-27. Mathematical implementation and complete original-kernel /
compiled-Lean bundle checks have passed. Local publication is a separate gate;
this contract does not authorize a remote deployment or a Stable promotion.

## Exact scope and additive inventory

This release implements the seven explicitly named completion targets in
§7.2 of `PLAN/14_constructive_number_theory_grand_campaign.md`. It does not
automatically close the broader Jacobi, Tonelli–Shanks, primitive-root, Pell,
valuation-lifting, or Gaussian-arithmetic roadmap bullets.

| Target | New theorems | Exact completion |
| --- | ---: | --- |
| T13 | 182 | Unrestricted signed determinant evaluation, unique rectangular determinantal rank, signed-representation invariance, actual integer spans, and positive absolute-determinant/full-rank matrix data. |
| G011 | 24 | Every finite pairwise gcd-compatible congruence system has an actual simultaneous solution and unique normalized representative, including empty lists and zero moduli. |
| G095 | 40 | Actual integer-polynomial simple roots lift uniquely and canonically at every positive prime power; the inverse is derived from derivative nonvanishing. |
| G035 | 19 | Every actual finite multinomial coefficient has a constructed prime valuation equal to its witnessed sequential quotient-column carry count. |
| G027 | 55 | The exact two Chebyshev inequalities `N<=8*k*ell` and `k*ell<=8*N` for every `N>=2`, actual `BitLen(N,ell)`, and actual `PrimeCount(N,k)`. |
| G107 | 30 | Every prime congruent to one modulo four has an actual first-stop Cornacchia execution proving `p=R*R+T*T`. |
| G051 | 72 | Actual nonempty finite prime-field sets satisfy the sharp Cauchy–Davenport bound; the sumset code and its exact cardinality are also constructed. |
| Total | 422 | Every new row has a complete dependency-closed ordinary HA proof. |

The immutable parent is Alpha v26 with 2,138 checked-use entries. The additive
result contains 2,560 checked-use entries and 8,196 direct theorem edges in
53 layers. Stable remains the separate default 432-theorem edition; all
2,128 remaining entries are Alpha-only. No theorem is enrolled merely by
matching a statement hash, recording a candidate receipt, or adding a graph
edge.

```text
parent catalogue: 969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534
parent edition:   8573945e4bdfe0a8d9414b499828ced67eff3b886e5adde50a0fcff81cfbdc19
parent enrollment:cdf2cd0adfef8f1becd6f1f62d4d1d5d7a1891838e16b52a4d1cdaca98c496f2
new-name order:   e925d4355f63aad9874fac92a3ec05362162793ec1fc2eea909ac1e1ede8f01b
v27 edition:      5c5935ed524b63827068cba37da222fc78b458de6c5af2e07cf572bb9fab7d05
v27 enrollment:   20866c3865baec2bc6cee3c8e54bcb2f55e95a7b1a7fc85c103e3c9b055ecf4e
```

The factory order is explicit and frozen in
`peano_lab.library.campaign_second_wave_closure.FACTORIES`: the nine matrix
providers (including the span provider before the quotient/data extensions),
three Hensel providers, generalized CRT, multinomial Kummer, Chebyshev,
Cornacchia, and the two finite-set/Cauchy–Davenport providers. The provider
sources, focused executable tests, and individual mathematical RFCs remain
separately bound in the additive release evidence.

## Mathematical boundary checks

Determinants are actual finite acyclic cofactor evaluations with strictly
earlier genuine minor nodes. A supplied table of cofactor numbers is not
accepted as a determinant. Rank constructs complete finite selector-code
boxes, searches actual bounded injective selectors, witnesses a nonzero
minor, and proves that every higher-order minor vanishes. Integer equality
is equality of signed differences, not equality of chosen positive/negative
components. The positive determinant data is exactly the intended
nondegenerate integral square-matrix/absolute-determinant data; lattice-index
or geometric-covolume equality, independent-basis theorems, determinant
multiplicativity, normal forms, and lattice reduction remain separate goals.

CRT has no dominating-last or supplied compatible-prefix premise. For a
positive LCM, normalization is the usual strict bound; at zero LCM the exact
congruences have an exact unique solution and no impossible `x<0` condition.

Hensel uses the actual signed polynomial and actual derivative evaluation.
The ordinary nonzero-derivative condition constructs a prime-field inverse.
The strongest endpoint supplies all power and canonical-root witnesses,
allows unrestricted starting representatives, and covers every positive
precision, not only one preselected lifting step.

The multinomial carry relation contains no valuation or coefficient. It
codes genuine binary quotient-column additions of successive parts and sums
their carry counts. Empty lists and zero parts are included; positivity of
the coefficient is proved. A separate simultaneous-column-grid or
permutation-invariance theorem is not claimed.

Chebyshev counts the entire primality mask through N. The exact constant-8
bounds are proved by finite integer arithmetic using genuine central-binomial
and primorial estimates. Final Bertrand-window/chain roots are related
results, not falsely inserted prerequisites.

Cornacchia includes the actual root of minus one, every Euclidean quotient
and remainder transition, the coefficient invariant, and the first stopping
state. The representation equation is a theorem conclusion, not part of the
trace premise. The general `x*x+d*y*y` problem is outside this release.

Cauchy–Davenport uses actual characteristic-bit sets, exact witnessed counts,
genuine translations and union/intersection constructors, a first-exit orbit
argument, and the cardinality-preserving Dyson transform with strict descent.
Its final inequality is `p<=m OR k+l<=m+1`. No polynomial-method or finite-choice
oracle is assumed; the earlier proposed polynomial route is retained only
as a conceptual connection.

## Proof authority and resource contract

The one self-contained artifact contains 1,223 actual theorem bodies: 422 new
and 801 inherited. Its 43 maximal endpoints are packaged by one balanced
conjunction node, which is not a library theorem. Every one of the resulting
1,224 nodes is checked by the unchanged original intuitionistic kernel and
by the separately compiled Lean bundle verifier. The artifact contains no
trusted theorem-name or receipt leaves.

Standalone assembly reads the SHA-pinned v26 catalogue only as exact
specifications and provider locators. Reused ordinary bodies must match both
their complete target and ordered prerequisite targets. Every reused body
is then checked again in the final self-contained graph. Missing bodies are
reconstructed in ordinary authoring microbatches under the unchanged limits
of 16 rows, 125,000 proof occurrences, and 25,000 proof objects; the release
was assembled with one row per microbatch.

Browser verification does not need historical provider files or a source-tree
catalogue: it receives the exact v26 specification tuple and the mounted
self-contained v27 artifact. The supplied tuple is authenticated against an
exact streaming inventory pin. The short `/lab/peano_lab/library/` import
layout is regression-tested. No kernel rules, axioms, classical inference,
replay limits, or proof budgets are relaxed.

## Conservative notation and public reading contract

The 131 historical reviewed definitions are retained as the identical
objects/IDs. Sixty-seven new definitions (`ND0075`–`ND0141`) give 198 reviewed
definitions and 388 direct notation edges. The finite modular set/count
relation is exactly the existing `BitCount` definition and reuses that
identity instead of creating another primitive or duplicate macro.

Every statement and every local tactic proposition has an exact parsed-AST
roundtrip check. Each definition page expands only through its prerequisites.
Proof arrows, theorem-to-definition uses, and definition-to-definition arrows
are separate; only actual theorem arrows determine proof reachability.
Opaque planning symbols with different arities remain separate. In
particular, the three-argument planning `Sum` is not the reviewed
four-argument beta sum, whose existing `BetaSum` display alias is retained.

Seven local family snapshots reuse the canonical Quadratic Reciprocity
landing renderer and its exact original CSS/JS assets. Every branch has exact
and definition-aware theorem directories, local proposition links, a mixed
interactive DAG, definition pages, and links to the full campaign atlas.
The displayed current authority is v27; historical branches retain their
original first-admission versions and exact original certificates.

## Historical source dispositions

All 535 inherited v26 evidence records and all historical catalogues and
proof bundles retain their exact bindings. Five tracked, clean audit/source
files had already been revised by earlier commits; their current bytes do
not equal the older versions named by inherited records:

- `peano-lab/py/tests/test_library_editions_v19_admission.py`
- `peano-lab/py/tests/test_linear_congruence_complete_candidate.py`
- `research/arithmetic-library/ha-bertrand-b6-release-tranche-rfc-v1.md`
- `research/arithmetic-library/linear-congruence-complete-rfc-v1.md`
- `research/arithmetic-library/wmi-qr-replay.md`

This campaign does not restore or rewrite them. The publisher explicitly pins
their already checked-in later hashes and reports the distinction; it does
not describe them as unchanged historical file bytes. No proof artifact,
kernel source, theorem specification, or new v27 evidence document receives
this historical-audit-file treatment. Exact ordinary proof bodies, not these
audit documents or their hashes, remain mathematical authority.
