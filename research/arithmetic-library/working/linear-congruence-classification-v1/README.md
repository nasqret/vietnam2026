# Exact natural linear-congruence solution classes

Working-only extension: eleven new ordinary HA scripts and the **unchanged**
`fermat_little_all_inputs` specification extracted from its original canonical
factory. All twelve bodies passed actual original-kernel conditional checks.
The frozen focused suite passes **393 distinct cases / 1,179 actual phases**:
188 independent contract/source/arithmetic-model cases, twelve native bodies,
36 false/missing/truncated bodies, 61 removed and 61 poisoned dependencies,
and 35 removed input clauses. The separate dependency-complete verification
described below also passed. Neither kind of observation grants admission.

## Exact mathematical scope

Write `ME(m,x,y)` for the existing balanced natural relation
`exists u v. x+m*u=y+m*v`. For `m≠0`, an actual relational gcd `IsGCD(g,a,m)`
and actual cofactor equations `a=g*A`, `m=g*M`, the new cancellation theorem
proves `ME(m,a*x,a*y)` iff `ME(M,x,y)`. No quotient function, inverse oracle,
or unproved cofactor-coprimality premise is introduced.

If `g` divides `b`, the standalone endpoint
`linear_congruence_exact_bounded_enumeration_exists` **constructs** a natural
`r<M` solving `a*r≡b (mod m)`. For every natural `x`, it proves

```text
x<m and a*x≡b (mod m)  iff  exists t<g. x=r+M*t.
```

The progression is injective on `t<g`; the separate parameter theorem proves
uniqueness even without the redundant parameter bounds. Thus the result is
an actual bijection with the natural interval below `g`, witnessing exactly
`g` bounded solutions. It does not claim to have constructed a beta-coded
enumeration or assumed a counting predicate. The class theorem also describes
all unbounded natural solutions relative to any actual solution.

Modulus zero is treated separately: congruence is equality; a nonzero
coefficient has at most one solution, while coefficient zero has every
natural solution precisely when the target is zero. There is no false bound
below zero. For modulus one, the unique bounded solution is zero, for all
coefficients and targets. The imported Fermat endpoint covers every natural
base, including zero and multiples of the prime.

## Frozen source and observations

- Source `linear_congruence_classification_candidate.py`: 18,128 bytes,
  SHA256 `12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47`.
- Test `test_linear_congruence_classification_candidate.py`: 13,751 bytes,
  SHA256 `97bb95b1f388fe947eba41f443265a30d5b8f3fa216df4a1abd688d95db5da35`.
- Twelve rows, 61 declared edges, 658 commands; sorted-key compact JSON of
  their five specification fields has SHA256
  `ee5a8f02bd360e7e164e25172af6460cb770881f4470ea6acbc2e04b944c75ec`.
- [Final focused accounting](conditional-verification-observations-v1.json)
  reconciles fresh collection with the six raw window records and 73 actual
  unchanged input files. Largest clean window: 5.316 seconds and 55,377,920
  bytes RSS. Earlier diagnostics are not counted twice.
- [Development observations](development-observations-v1.json) preserve one
  rejected enumeration draft: its four-clause conjunction was left-associated
  while its projections expected right association. The source and independent
  expected contract now explicitly right-associate it. This rejected attempt
  receives zero success credit; the final source was replayed in the focused
  positive window.

The original CPU 170/175-second, wall 180-second, RSS 1,536-MiB and depth-256
gates are unchanged. No Alpha import, complete-cone verification, Lean job,
catalogue promotion, commit or deployment was performed by these focused
tests. Saved observations are accounting only, never proof capabilities.

## Dependency-complete checkpoint

The exact source cone contains 202 inherited canonical theorems and these
twelve local rows. Its original assembler order is **not** source DFS order.
[Final source inventory](final-source-inventory-v1.json) reconciles all 214
actual artifact targets and ordered dependency IDs against the source rows.
It records both serializations explicitly: the original twelve-row streaming
specification digest is `b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8`;
the artifact-ordered complete streaming digest is
`8d2b30a02f7103507dba33c635d3f3728e6aedd7451b0ec6a7c78b67111d8094`.

The unchanged original assembler freshly checked all 1,224 bodies in the
authentic v27 second-wave seed, retained the 202 exact inherited bodies,
constructed the twelve local bodies, and checked the resulting complete
[artifact](artifacts/working-linear-congruence-prefix-12-proof-bundle-v1.json):
542,092 bytes, SHA256
`983051afddc637a4e033546b8f3ddb8dc0ac22aa996b4e28b3822be8895576ad`,
215 nodes, 647 edges and 13,079 body nodes including packaging.
Authoring took 37.767 seconds, peak 840,024,064 bytes RSS.

[Six final fresh gates](final-verification-observations-v1.json) passed:
whole original HA plus independent compiled Lean on the same authenticated
payload, then five separate ordinary empty-context original-HA checks for
the enumeration endpoint, both modulus-zero endpoints, the modulus-one
endpoint and all-input Fermat. Every gate preserves the original limits and
the same final source binding. The 51 source/control guards also passed;
their post-registration repeat is not additional test coverage.

These are local mathematical results only. Global current-catalogue novelty,
Alpha/Stable enrollment, publication and deployment remain separate release
operations. No saved report can substitute for fresh verification. The
parametrization requires nonzero modulus (hence positive `g` and `M`); when
`g=0` an interval `t<g` is empty, but that impossible nonzero-modulus branch
is never used to claim a finite modulus-zero solution count. Composite and
even moduli are included; the prime hypothesis occurs only in Fermat.
