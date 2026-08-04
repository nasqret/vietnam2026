# RFC HA-M5-GCRT-1: constructive generalized-CRT foundation

**Status:** eight-row congruence foundation, seven-row M5a nonzero
sufficiency ladder, and four-row M5b zero-boundary ladder closed from the
empty context; 18 rows are new and one exact existing support row is reused;
all 19 remain isolated and unadmitted

**Scope:** M5 binary generalized Chinese remainder theorem over possibly
noncoprime natural moduli

**Object language:** first-order HA over \(\{0,S,+,\times,=\}\)

**Kernel change:** none

This RFC records the first three checked layers for generalized CRT. They prove
the congruence algebra, the necessary gcd-compatibility condition and its
obstruction corollary, and the converse construction when both input moduli
are nonzero. The third layer handles either zero modulus directly, without
calling division at modulus zero, and dispatches the three constructive
zero/nonzero cases. Thus the binary solvability criterion is closed-checked
for all natural moduli. Classification modulo relational LCM and the
finite-system theorem remain separate obligations.

## 1. Conservative surfaces

Balanced congruence is authoring notation for

```text
ModEq(d,a,b) := exists u v. a + d*u = b + d*v
```

and a binary CRT solution is

```text
CRTSolution(x,m,n,a,b) := ModEq(m,x,a) /\ ModEq(n,x,b).
```

Both surfaces expand hygienically before parsing. The kernel receives no
`ModEq`, `CRTSolution`, subtraction, quotient, remainder, gcd function, or CRT
primitive.

The gcd premise uses the existing result-first relational convention
`IsGCD(g,m,n)`. In particular, compatibility means `ModEq(g,a,b)`; it is not
host-language divisibility or an external `%` computation.

## 2. Exact eight-row foundation

The ordered stack begins with the exact pre-existing
`mod_eq_add_cancel_left` specification from
[`finite_sum_pointwise_mod_candidate.py`](../../peano-lab/py/peano_lab/library/finite_sum_pointwise_mod_candidate.py).
The generalized-CRT factory returns that specification unchanged instead of
copying either its statement or proof. The following seven rows are new:

| Order | Theorem | Surface meaning | Ordered direct dependencies |
|---:|---|---|---|
| 1 | `mod_eq_add_cancel_left` | `ModEq(d,c+a,c+b) -> ModEq(d,a,b)` | exact reused support row |
| 2 | `mod_eq_zero_iff_eq` | `ModEq(0,a,b) <-> a=b` | `mul_zero_left` |
| 3 | `mod_eq_add_cancel_right` | `ModEq(d,a+c,b+c) -> ModEq(d,a,b)` | `mod_eq_add_cancel_left`, `add_comm` |
| 4 | `mod_eq_scale` | `ModEq(m,a,b) -> ModEq(k*m,k*a,k*b)` | `mul_add`, `mul_assoc` |
| 5 | `mod_eq_unscale_nonzero` | `k!=0 -> ModEq(k*m,k*a,k*b) -> ModEq(m,a,b)` | `mul_add`, `mul_assoc`, `mul_left_cancel_nonzero` |
| 6 | `crt_solution_pair_congruent` | two solutions are congruent modulo each input modulus | `mod_eq_symm`, `mod_eq_trans` |
| 7 | `crt_common_solution_implies_gcd_compatible` | `IsGCD(g,m,n) -> CRTSolution(x,m,n,a,b) -> ModEq(g,a,b)` | `is_gcd_dvd_left`, `is_gcd_dvd_right`, `mod_eq_of_mod_eq_multiple`, `mod_eq_symm`, `mod_eq_trans` |
| 8 | `crt_incompatibility_obstructs_solution` | `IsGCD(g,m,n) -> ~ModEq(g,a,b) -> ~(exists x. CRTSolution(x,m,n,a,b))` | `crt_common_solution_implies_gcd_compatible` |

Rows 7 and 8 are respectively the necessity theorem and its constructive
obstruction corollary. Row 8 does not extract a counterexample through
classical negation: it maps any alleged solution to the compatibility proof
forbidden by its premise.

## 3. Checked receipts

Exact empty-context receipts are ordered as
`(nodes, depth, objects, edges, reused, Cuts, certificate SHA-256)`:

| Theorem | Receipt |
|---|---|
| `mod_eq_add_cancel_left` | `(215, 24, 204, 214, 11, 6, 0f197213f155b2280177b684b0142d907b6181cdd10f0233f49bbbcb2c4323f7)` |
| `mod_eq_zero_iff_eq` | `(55, 13, 55, 54, 0, 1, c81d939dd0cdf3b015a50b0d7ca2525670030a44bc07dcc94e53ff3c0d5dc17e)` |
| `mod_eq_add_cancel_right` | `(310, 25, 226, 237, 12, 8, 7c15168b44f390704973446c454be047adf535ff7be5703842313144a84c0ff1)` |
| `mod_eq_scale` | `(235, 21, 146, 158, 13, 4, b8a575b14dcef4b063f1973469551f1e1d4bacf5d5e41a85f4c6f45d985735ce)` |
| `mod_eq_unscale_nonzero` | `(466, 26, 330, 343, 14, 11, 32e9b748fdce30ff2be9724b7b4c2e1831ef49abd4134958f82908ead5d3ae8e)` |
| `crt_solution_pair_congruent` | `(307, 31, 259, 274, 16, 8, d4ea11bc6a4450bb6d3fb397defb18f8fcaa53292fcc3bbf6039a4ff9ee1ad1a)` |
| `crt_common_solution_implies_gcd_compatible` | `(518, 34, 388, 409, 22, 13, cc5e4988e40ab3710be18c861261101d09b05604a9fb02ce9cbd583aa1c1cecc)` |
| `crt_incompatibility_obstructs_solution` | `(560, 35, 430, 451, 22, 14, 67f6acd82739752aa50cdbb33e3f02c3542d32de006ef45189f355a236b4b473)` |

The focused audit in
[`test_ha_generalized_crt_congruence_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_congruence_candidate.py)
replays two cold closures, pins exact statements, dependencies, body and
certificate receipts, rejects nearby false endpoints, and checks bounded
semantics. All eight certificates check through the normal intuitionistic
entry point and contain zero `DNE` nodes. This is candidate evidence, not
public admission.

## 4. Exact seven-row M5a sufficiency ladder

The second isolated factory is
[`ha_generalized_crt_sufficiency_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_sufficiency_candidate.py).
Its ordered rows are:

| Order | Theorem | Surface meaning | Ordered direct dependencies |
|---:|---|---|---|
| 1 | `factor_nonzero_right` | `n!=0 -> n=c*d -> d!=0` | `factor_nonzero_left`, `mul_comm` |
| 2 | `is_gcd_quotients_coprime_nonzero` | nonzero `g` and `IsGCD(g,m,n)` make cofactors in `m=g*M`, `n=g*N` coprime | `is_gcd_greatest`, `mul_assoc`, `mul_one`, `mul_left_cancel_nonzero`, `divisor_one` |
| 3 | `is_gcd_nonzero_coprime_quotients` | package nonzero `g,M,N`, the two factor equations, and `Coprime(M,N)` | gcd projections, the two preceding factor/cofactor rows |
| 4 | `mod_eq_common_remainder_decomposition` | `g!=0` and `ModEq(g,a,b)` give `a=g*A+r`, `b=g*B+r`, `r<g` | division/remainder existence, congruence conversion, symmetry/transitivity, `mul_comm` |
| 5 | `crt_scaled_common_remainder_lift` | solve the coprime cofactor CRT, scale by `g`, then add the shared `r` | `binary_crt`, `mod_eq_scale`, `mod_eq_refl`, `mod_eq_add` |
| 6 | `generalized_binary_crt_sufficient_nonzero` | compatible residues have a common solution when `m,n` are nonzero | gcd projections, cofactor coprimality, shared remainder, scaled lift |
| 7 | `generalized_binary_crt_solvable_iff_nonzero` | for nonzero `m,n`, solvability is equivalent to `ModEq(g,a,b)` | necessity theorem, sufficiency theorem |

The key quotient argument uses only the universal property of `IsGCD`:

\[
d\mid M,\ d\mid N
\Longrightarrow gd\mid m,\ gd\mid n
\Longrightarrow gd\mid g
\Longrightarrow g=g(dw)
\Longrightarrow 1=dw
\Longrightarrow d=1.
\]

The cancellation step is constructive and uses the explicit premise
`g != 0`. No excluded middle or negative-witness extraction occurs.

Exact empty-context receipts are ordered as
`(nodes, depth, objects, edges, reused, Cuts, certificate SHA-256)`:

| Theorem | Receipt |
|---|---|
| `factor_nonzero_right` | `(290, 26, 247, 269, 23, 9, fa36c22be01d8493018a0a520e57b4d55bb6a49606ca66b593d627a3bca93e3c)` |
| `is_gcd_quotients_coprime_nonzero` | `(660, 33, 562, 595, 34, 18, b20e99453775b46993595aa0c53a4e8facc56e037ef7d138d3005098d1bf973d)` |
| `is_gcd_nonzero_coprime_quotients` | `(1120, 38, 876, 931, 56, 32, bac838b1489a5285b36e24d437fb4cb5f5f452d31cb3340b9f88818ee05fb8a2)` |
| `mod_eq_common_remainder_decomposition` | `(2894, 69, 1075, 1138, 64, 43, 7615686f1fb9c23b0b53a4cc46a1da5349bd6fd6b808d8ef0203b45a213fd6fc)` |
| `crt_scaled_common_remainder_lift` | `(5745, 52, 2062, 2174, 113, 92, 188a46f051c74f8a3f53c3945a3760fff3be12df5d89c2b468e94cf201166674)` |
| `generalized_binary_crt_sufficient_nonzero` | `(9482, 74, 3147, 3302, 156, 141, 9c1ad09a4bfb2ee8e273320069d6ef6f9e50c0229aa023bb45cf887ddd9c2a1b)` |
| `generalized_binary_crt_solvable_iff_nonzero` | `(10073, 76, 3316, 3476, 161, 149, 8956a66d8f72d512f840464d2749e43258a2b74b3828dde58f2c206d53af0234)` |

The focused audit performs two cold closures, pins statement and script
hashes, checks bounded semantics, and rejects nearby false endpoints. Every
certificate contains zero `DNE` nodes. The largest closed theorem is only
10,073 proof occurrences at depth 76, so no kernel-limit increase is needed.

## 5. Exact four-row M5b zero-inclusive closure

The third isolated factory is
[`ha_generalized_crt_zero_boundary_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_zero_boundary_candidate.py).
It does not send a zero modulus through the remainder theorem. Instead it
uses the public uniqueness of relational gcds to identify
`IsGCD(g,0,n)` with `g=n` and `IsGCD(g,m,0)` with `g=m`.

| Order | Theorem | Surface meaning | Ordered direct dependencies |
|---:|---|---|---|
| 1 | `generalized_binary_crt_sufficient_zero_left` | `IsGCD(g,0,n)` and compatibility construct a solution by choosing `x=a` | `is_gcd_symm`, `is_gcd_zero_right`, `is_gcd_unique`, `mod_eq_refl` |
| 2 | `generalized_binary_crt_sufficient_zero_right` | `IsGCD(g,m,0)` and compatibility construct a solution by choosing `x=b` | `is_gcd_zero_right`, `is_gcd_unique`, `mod_eq_symm`, `mod_eq_refl` |
| 3 | `generalized_binary_crt_sufficient` | compatibility constructs a solution for arbitrary natural `m,n` | `eq_decidable`, the two zero-boundary rows, `generalized_binary_crt_sufficient_nonzero` |
| 4 | `generalized_binary_crt_solvable_iff` | for arbitrary natural `m,n`, solvability is equivalent to `ModEq(g,a,b)` | necessity theorem, total sufficiency theorem |

The first row already contains the `(0,0)` case. There compatibility forces
the two residues to be equal, and choosing the left residue satisfies both
zero-modulus equations. The total row uses the constructive theorem
`eq_decidable` to split on `m=0` and then `n=0`; the final branch is exactly
the M5a nonzero construction. No residual private canonical-gcd convenience
row is a proof dependency.

Exact empty-context receipts are ordered as
`(nodes, depth, objects, edges, reused, Cuts, DNE, certificate SHA-256)`:

| Theorem | Receipt |
|---|---|
| `generalized_binary_crt_sufficient_zero_left` | `(834, 37, 682, 717, 36, 26, 0, 074f07df173308477693b6e3bbfd3a3a4123078d8f7f5eaac9077666d3cbc763)` |
| `generalized_binary_crt_sufficient_zero_right` | `(805, 36, 653, 688, 36, 26, 0, da2d830f65077816dfeecd1503a787cf8ba0f5ec99e93d13b5456e4ba772e2f6)` |
| `generalized_binary_crt_sufficient` | `(11240, 78, 3495, 3662, 168, 160, 0, 931fbcc775154507996c768cb1de1cc8479c3ed805ce0d1a95fffb530e8b56c4)` |
| `generalized_binary_crt_solvable_iff` | `(11825, 80, 3658, 3830, 173, 168, 0, 3f1d82f0f06df9e0d2a5c746405ee46406db71c57e4bbf32f68792be07af8b0c)` |

All four rows replay through the ordinary intuitionistic checker, contain
zero `DNE` nodes, and fit the existing formula, proof-occurrence, proof-DAG,
and depth limits. No limit or kernel rule was changed. These are still
candidate receipts: the public registry and research catalog are unchanged.

## 6. Dependency route

```text
balanced congruence algebra
  |-- zero modulus is equality
  |-- additive cancellation
  `-- scale / nonzero unscale
             |
public relational gcd projections
             |
             v
common CRT solution
  -> congruence modulo m and n
  -> transport to congruence modulo gcd(m,n)
  -> compatibility is necessary
  -> incompatibility obstructs every solution

IsGCD(g,m,n), m!=0, n!=0
  -> m=g*M, n=g*N with g,M,N nonzero
  -> Coprime(M,N)

ModEq(g,a,b), g!=0
  -> a=g*A+r and b=g*B+r with r<g

Coprime(M,N)
  -> binary_crt(M,N,A,B)
  -> scale the two congruences by g
  -> add r
  -> CRTSolution(x,m,n,a,b)

necessity + sufficiency
  -> solvability iff gcd compatibility for m,n nonzero

public gcd uniqueness + zero gcd boundary
  -> left-zero solution by x=a
  -> right-zero solution by x=b

eq_decidable(m,0), eq_decidable(n,0)
  -> left-zero / right-zero / nonzero dispatch
  -> solvability iff gcd compatibility for all natural m,n
```

The newly public universal `IsLCM` interface and `gcd_lcm_product` theorem are
the intended downstream solution-class boundary: after existence is proved,
solutions should be compared modulo an `IsLCM(l,m,n)` witness rather than by
introducing a primitive lcm function.

## 7. Honest remaining work

The binary existence criterion is now closed for all natural moduli. The
remaining generalized-CRT work is, in dependency order:

1. prove that any two solutions are congruent modulo every relational LCM
   witness, and conversely describe the complete solution class;
2. canonicalize a solution with the remainder interface when the LCM is
   nonzero, while treating zero-modulus and `(0,0)` cases explicitly;
3. add an all-modulus congruence decision wrapper and return either a solution
   or an explicit incompatibility certificate;
4. admit only a reviewed minimal public surface after cold replay, mutation,
   resource, registry, catalog, and generated-artifact gates pass;
5. lift the binary theorem to finite families only after the independent
   finite-data substrate is available.

Thus the campaign has proved both directions and actual existence for the
complete binary natural-modulus case. It has not yet proved canonical
classification, executable compatibility decision, or finite generalized
CRT.

## 8. Repository anchors

- implementation:
  [`ha_generalized_crt_congruence_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_congruence_candidate.py)
- focused audit:
  [`test_ha_generalized_crt_congruence_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_congruence_candidate.py)
- sufficiency implementation:
  [`ha_generalized_crt_sufficiency_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_sufficiency_candidate.py)
- sufficiency audit:
  [`test_ha_generalized_crt_sufficiency_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_sufficiency_candidate.py)
- zero-boundary implementation:
  [`ha_generalized_crt_zero_boundary_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_zero_boundary_candidate.py)
- zero-boundary audit:
  [`test_ha_generalized_crt_zero_boundary_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_zero_boundary_candidate.py)
- admitted gcd/LCM interface:
  [`ha-canonical-gcd-lcm-rfc-v1.md`](ha-canonical-gcd-lcm-rfc-v1.md)
- campaign plan:
  [`PLAN/12_ha_number_theory_campaign.md`](../../PLAN/12_ha_number_theory_campaign.md)
