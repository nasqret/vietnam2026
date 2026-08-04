# RFC HA-M5-GCRT-1: constructive generalized-CRT foundation

**Status:** eight-row congruence foundation, seven-row M5a nonzero
sufficiency ladder, four-row M5b zero-boundary ladder, four-row M5c
relational-LCM classification ladder, three-row M5d canonical boundary,
two-row M5e executable boundary, and one-row M5f raw-input total decision
closed from the empty context; 28 rows are new and one exact existing support
row is reused; all 29 remain isolated and unadmitted

**Scope:** M5 binary generalized Chinese remainder theorem over possibly
noncoprime natural moduli

**Object language:** first-order HA over \(\{0,S,+,\times,=\}\)

**Kernel change:** none

This RFC records the first seven checked layers for generalized CRT. They prove
the congruence algebra, the necessary gcd-compatibility condition and its
obstruction corollary, and the converse construction when both input moduli
are nonzero. The third layer handles either zero modulus directly, without
calling division at modulus zero, and dispatches the three constructive
zero/nonzero cases. The fourth layer proves that congruence modulo a supplied
relational LCM is exactly congruence modulo both input moduli and classifies
every solution relative to one fixed solution. The fifth layer turns that
classification into exact uniqueness at LCM zero and a unique bounded
representative at nonzero LCM, then packages the correct case constructively.
The sixth decides compatibility at every modulus and returns either a
compatible system with a solution or an incompatible system with a proof of
unsolvability when a relational gcd witness is supplied. The seventh starts
from raw inputs `m,n,a,b`, constructs an existential relational gcd, and then
returns the same compatible-solution or incompatible-obstruction result.
Thus binary solvability, the complete solution class, the honest canonical
boundary, and executable obstruction output are closed-checked for all
natural moduli. Admission and finite-system lifting remain separate.

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

## 6. Exact four-row M5c relational-LCM classification

The fourth isolated factory is
[`ha_generalized_crt_classification_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_classification_candidate.py).
It is subtraction-free: total order exposes a directed gap, congruence makes
that gap a multiple of each modulus, and `is_lcm_least` makes it a multiple
of the relational LCM.

| Order | Theorem | Surface meaning | Ordered direct dependencies |
|---:|---|---|---|
| 1 | `mod_eq_ordered_gap_multiple` | `k+x=y` and `ModEq(d,x,y)` imply `d|k` | `add_comm`, `add_assoc`, `add_left_cancel`, `factor_difference` |
| 2 | `mod_eq_lcm_merge` | `IsLCM(l,m,n)`, `ModEq(m,x,y)`, and `ModEq(n,x,y)` imply `ModEq(l,x,y)` | `le_total`, `mod_eq_symm`, row 1, `is_lcm_least`, `mul_comm`, `remainder_decomposition_to_mod_eq` |
| 3 | `mod_eq_lcm_iff_pair` | under `IsLCM(l,m,n)`, congruence modulo `l` is equivalent to congruence modulo both `m` and `n` | public LCM projections, `mod_eq_of_mod_eq_multiple`, row 2 |
| 4 | `crt_solution_class_iff_lcm` | relative to a fixed solution `x`, `y` is a solution iff `ModEq(l,y,x)` | `crt_solution_pair_congruent`, row 3, `mod_eq_trans` |

The final orientation is deliberate. The forward implication compares the
candidate `y` to the fixed solution `x`, obtaining `y == x` modulo each input
before merging. The reverse implication composes `y == x` with the fixed
facts `x == a (mod m)` and `x == b (mod n)`.

Dependency-curried body receipts are ordered as
`(dependencies, commands, nodes, depth, objects, edges, reused)`; closed
receipts are ordered as
`(nodes, depth, objects, edges, reused, Cuts, DNE, certificate SHA-256)`:

| Theorem | Body receipt | Empty-context receipt |
|---|---|---|
| `mod_eq_ordered_gap_multiple` | `(4, 31, 44, 21, 44, 43, 0)` | `(558, 30, 310, 325, 16, 13, 0, 6a30012cfc1213bf167be2de794e05cdae2893ab075cfc24abf9b181bde9be67)` |
| `mod_eq_lcm_merge` | `(6, 113, 127, 26, 127, 126, 0)` | `(1315, 33, 653, 685, 33, 25, 0, 46cd67f69ccf0c669de283fca6a74a0a85cf18d54f248f1a6f428122196a331b)` |
| `mod_eq_lcm_iff_pair` | `(4, 46, 56, 21, 56, 55, 0)` | `(1570, 37, 864, 908, 45, 32, 0, 855d5745c1613304fc0a5f26c70fe9f795ed3ebcff4a7276e3745681d41fc91a)` |
| `crt_solution_class_iff_lcm` | `(3, 62, 79, 27, 79, 78, 0)` | `(2208, 39, 1055, 1104, 50, 40, 0, 305a913aaca1c3e307d8ca77bb90c063dd67f3fa9f9bdd69e28cf4064cdff7b3)` |

The theorem is uniform at `l=0`. There `ModEq(0,y,x)` is exactly `y=x`, so
the class theorem becomes exact uniqueness; it does not invoke division or
claim a remainder below zero. The focused audit checks the ordinary
intuitionistic entry point, two cold closures, mutations, and bounded
semantics. All four certificates contain zero `DNE` nodes and fit the
existing limits. The campaign now has 116 isolated candidate references and
141 exact receipts, while the public registry and catalog remain 409 and 410.

## 7. Exact three-row M5d canonical boundary

The fifth isolated factory is
[`ha_generalized_crt_canonical_boundary_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_canonical_boundary_candidate.py).
It uses the conservative surface

```text
Below(r,l) := exists h. h + S r = l
```

and deliberately separates the zero and nonzero LCM cases.

| Order | Theorem | Surface meaning | Ordered direct dependencies |
|---:|---|---|---|
| 1 | `crt_solution_unique_lcm_zero` | `l=0`, `IsLCM(l,m,n)`, and a fixed solution `x` imply every solution `y` equals `x` | `crt_solution_class_iff_lcm`, `mod_eq_zero_iff_eq` |
| 2 | `crt_solution_canonical_remainder_nonzero` | if `l!=0`, every fixed solution has a unique congruent solution `r<l` | `division_remainder_exists`, `mul_comm`, `remainder_decomposition_to_mod_eq`, `mod_eq_symm`, `crt_solution_class_iff_lcm`, `mod_eq_bounded_unique` |
| 3 | `generalized_binary_crt_canonical_boundary` | compatibility returns either an exactly unique zero-LCM solution or a unique bounded nonzero-LCM solution | `eq_decidable`, `generalized_binary_crt_sufficient`, rows 1--2 |

Row 2 retains the useful auxiliary fact `ModEq(l,r,x)`. Row 3 intentionally
hides it and exports only the canonical mathematical boundary. It first uses
total M5b sufficiency to construct a fixed solution and then decides `l=0`
constructively. No zero branch states `Below(r,0)`.

Body receipts are ordered as
`(dependencies, commands, nodes, depth, objects, edges, reused)` and closed
receipts as
`(nodes, depth, objects, edges, reused, Cuts, DNE, certificate SHA-256)`:

| Theorem | Body receipt | Empty-context receipt |
|---|---|---|
| `crt_solution_unique_lcm_zero` | `(2, 33, 37, 28, 37, 36, 0)` | `(2300, 40, 1126, 1176, 51, 43, 0, 2afc46ac88613c95400eb37f80b1fbda095b18a7f6a774255426b48c35aed9ac)` |
| `crt_solution_canonical_remainder_nonzero` | `(6, 83, 141, 39, 141, 140, 0)` | `(4086, 65, 1668, 1746, 79, 64, 0, 091e8f2b1ba7e4665b87071fcd924ea1098880d65a97bcdd264ed544e33ff0e4)` |
| `generalized_binary_crt_canonical_boundary` | `(4, 66, 76, 33, 76, 75, 0)` | `(17750, 80, 4239, 4426, 188, 193, 0, c704a17f6feed83142b160bbeafcc14764d5ae6590999187eed5455c3ad03bd7)` |

The focused audit checks two cold closures, exact identities, false endpoint
mutations, hygiene of `Below`, and 4,021 compatible bounded systems: 611
zero-LCM exact-uniqueness cases and 3,410 nonzero-LCM canonical-remainder
cases. All three certificates contain zero `DNE`, fit unchanged limits, and
remain unadmitted. Campaign evidence is now 119 isolated candidate references
and 144 exact receipts; the public registry and catalog remain 409 and 410.

## 8. Exact two-row M5e executable boundary

The sixth isolated factory is
[`ha_generalized_crt_decision_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_decision_candidate.py).
It exposes a total constructive decision without introducing `%`, a gcd
function, or classical excluded middle.

| Order | Theorem | Surface meaning | Ordered direct dependencies |
|---:|---|---|---|
| 1 | `mod_eq_decidable` | `ModEq(d,a,b) \/ ~ModEq(d,a,b)` for every natural modulus, including zero | `eq_decidable`, `mod_eq_zero_iff_eq`, `mod_eq_decidable_nonzero` |
| 2 | `generalized_binary_crt_solution_or_obstruction` | under `IsGCD(g,m,n)`, return either `ModEq(g,a,b)` with a solution or `~ModEq(g,a,b)` with a proof that no solution exists | row 1, `generalized_binary_crt_sufficient`, `crt_incompatibility_obstructs_solution` |

The zero branch of row 1 decides `a=b` and transports through
`mod_eq_zero_iff_eq`; its two modulus occurrences are rewritten separately.
The nonzero branch reuses the public remainder-based decision theorem. Row 2
preserves the decided compatibility proposition in both outputs. It is
therefore stronger and more inspectable than a bare decidability proposition.

| Theorem | Body receipt | Empty-context receipt |
|---|---|---|
| `mod_eq_decidable` | `(3, 35, 47, 16, 47, 46, 0)` | `(2339, 70, 1217, 1278, 62, 44, 0, 298e2b18fff84bcf3a2ec69dbc464454f958d4155b7afb687f0bab2fd95efe7e)` |
| `generalized_binary_crt_solution_or_obstruction` | `(3, 36, 43, 22, 43, 42, 0)` | `(14182, 80, 3909, 4090, 182, 182, 0, 16e7cb1c430fa4e17ea878adc72d34c92e0bc3f135c4a3cf24cb2a296b38e525)` |

Two cold closures agree, nearby false endpoints fail, and both certificates
contain zero `DNE` within unchanged limits. The retained audit covers 847
all-modulus congruence cases and 5,929 generalized CRT systems: 4,021 take the
compatible/solution branch and 1,908 take the incompatible/unsolvable branch.
At gcd zero, 11 systems are compatible and 110 are incompatible. Campaign
evidence is now 121 private candidates and 146 receipts; the public registry
and catalog remain 409 and 410.

## 9. Exact one-row M5f raw-input total decision

The seventh isolated factory is
[`ha_generalized_crt_total_decision_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_total_decision_candidate.py).
It removes the supplied-gcd precondition from the executable interface while
keeping gcd relational and explicit in the result.

| Theorem | Surface meaning | Ordered direct dependencies |
|---|---|---|
| `generalized_binary_crt_total_decision` | for raw inputs `m,n,a,b`, construct `g` with `IsGCD(g,m,n)` and return either compatibility plus a CRT solution or incompatibility plus a proof that no CRT solution exists | `gcd_exists_relational`, `generalized_binary_crt_solution_or_obstruction` |

The theorem constructs an existential witness `g`; it does not introduce a
primitive gcd function. It also does not choose a canonical bounded solution.
That distinct zero/nonzero boundary remains the role of M5d.

The exact statement SHA-256 is
`42d29bf501421be60c1a2b14fa858a14abf230eee2f7669503db019d6b014151`.
Its body receipt
`(dependencies, commands, nodes, depth, objects, edges, reused)` is
`(2, 17, 42, 25, 42, 41, 0)`. Its empty-context receipt
`(nodes, depth, objects, edges, reused, Cuts, DNE, certificate SHA-256)` is
`(15492, 82, 4052, 4240, 189, 192, 0, c2d915d2eb60ccbb2dac9f31e9e1f9c310c28264b74483ec97ae33a1a0d965ee)`.

The focused audit in
[`test_ha_generalized_crt_total_decision_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_total_decision_candidate.py)
pins the exact statement and dependency surface, replays the body and two cold
closures, checks mutation rejection and bounded raw-input semantics, and
confirms zero `DNE` within unchanged limits. Campaign evidence is now 122
private candidates and 147 exact receipts across 27 candidate modules and 30
focused test paths. The generalized-CRT stack contains 29 rows: 28 new rows
and one exact reused support row. The public registry and catalog remain 409
and 410.

## 10. Dependency route

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

ModEq(m,x,y) and ModEq(n,x,y)
  -> both moduli divide the directed gap
  -> IsLCM leastness makes l divide the gap
  -> ModEq(l,x,y)

LCM projections + congruence descent
  -> ModEq(l,x,y) iff ModEq(m,x,y) and ModEq(n,x,y)
  -> CRTSolution(y) iff ModEq(l,y,x), for a fixed solution x

l=0 + zero-modulus congruence is equality
  -> every solution equals the fixed solution

l!=0 + division of the fixed solution by l
  -> a remainder r with Below(r,l) and ModEq(l,r,x)
  -> M5c transports r into the solution class
  -> bounded congruence uniqueness makes r canonical

total M5b sufficiency + eq_decidable(l,0)
  -> exact-unique zero-LCM branch / bounded-unique nonzero-LCM branch

eq_decidable + zero congruence equality + nonzero congruence decision
  -> ModEq(d,a,b) or not ModEq(d,a,b), for every d
  -> compatibility gives a solution by M5b
  -> incompatibility gives unsolvability by the obstruction theorem

gcd_exists_relational(m,n)
  -> exists g. IsGCD(g,m,n)
  -> invoke the supplied-g decision boundary
  -> return compatible+solution or incompatible+unsolvable from raw inputs
```

The newly public universal `IsLCM` interface is now the checked solution-class
boundary. No primitive lcm function is introduced.

## 11. Honest remaining work

Binary existence, relational-LCM classification, and the zero/nonzero
canonical, executable, and raw-input decision boundaries are now closed for
all natural moduli. The remaining generalized-CRT work is:

1. admit only a reviewed minimal public surface after cold replay, mutation,
   resource, registry, catalog, and generated-artifact gates pass;
2. complete the K3 finite-data substrate, then lift the binary theorem to a
   finite-system fold.

The M5d split remains part of the frozen interface: `l=0` gives exact
uniqueness, while only `l!=0` admits a bounded remainder.

## 12. Repository anchors

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
- classification implementation:
  [`ha_generalized_crt_classification_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_classification_candidate.py)
- classification audit:
  [`test_ha_generalized_crt_classification_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_classification_candidate.py)
- canonical-boundary implementation:
  [`ha_generalized_crt_canonical_boundary_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_canonical_boundary_candidate.py)
- canonical-boundary audit:
  [`test_ha_generalized_crt_canonical_boundary_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_canonical_boundary_candidate.py)
- executable-boundary implementation:
  [`ha_generalized_crt_decision_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_decision_candidate.py)
- executable-boundary audit:
  [`test_ha_generalized_crt_decision_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_decision_candidate.py)
- raw-input decision implementation:
  [`ha_generalized_crt_total_decision_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_total_decision_candidate.py)
- raw-input decision audit:
  [`test_ha_generalized_crt_total_decision_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_total_decision_candidate.py)
- admitted gcd/LCM interface:
  [`ha-canonical-gcd-lcm-rfc-v1.md`](ha-canonical-gcd-lcm-rfc-v1.md)
- campaign plan:
  [`PLAN/12_ha_number_theory_campaign.md`](../../PLAN/12_ha_number_theory_campaign.md)
