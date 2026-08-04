# RFC HA-M5-GCRT-1: constructive generalized-CRT foundation

**Status:** eight-row foundation closed from the empty context; seven rows are
new and one exact existing support row is reused; all eight remain isolated
and unadmitted

**Scope:** M5 binary generalized Chinese remainder theorem over possibly
noncoprime natural moduli

**Object language:** first-order HA over \(\{0,S,+,\times,=\}\)

**Kernel change:** none

This RFC records the first checked layer for generalized CRT. It proves the
congruence algebra needed to state the theorem cleanly, proves that every
common CRT solution forces compatibility modulo a relational gcd, and turns
incompatibility into a formal obstruction. It does **not** yet claim the
converse construction or a complete generalized CRT.

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

## 4. Dependency route

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
```

The newly public universal `IsLCM` interface and `gcd_lcm_product` theorem are
the intended downstream solution-class boundary: after existence is proved,
solutions should be compared modulo an `IsLCM(l,m,n)` witness rather than by
introducing a primitive lcm function.

## 5. Honest remaining work

The full binary generalized CRT still requires, in dependency order:

1. derive coprime cofactors from `IsGCD(g,m,n)` together with factor witnesses
   `m=g*M` and `n=g*N`;
2. construct a common solution from the compatibility premise
   `ModEq(g,a,b)` using balanced Bezout or the checked coprime CRT route;
3. combine necessity and construction into the exact solvability iff;
4. prove that any two solutions are congruent modulo every relational LCM
   witness, and conversely describe the complete solution class;
5. canonicalize a solution with the remainder interface when the LCM is
   nonzero, while treating zero-modulus and `(0,0)` cases explicitly;
6. admit only a reviewed minimal public surface after cold replay, mutation,
   resource, registry, catalog, and generated-artifact gates pass;
7. lift the binary theorem to finite families only after the independent
   finite-data substrate is available.

Thus the campaign has proved the generalized theorem's necessary condition
and obstruction certificate, but not sufficiency, existence, canonical
uniqueness, or the finite generalized CRT.

## 6. Repository anchors

- implementation:
  [`ha_generalized_crt_congruence_candidate.py`](../../peano-lab/py/peano_lab/library/ha_generalized_crt_congruence_candidate.py)
- focused audit:
  [`test_ha_generalized_crt_congruence_candidate.py`](../../peano-lab/py/tests/test_ha_generalized_crt_congruence_candidate.py)
- admitted gcd/LCM interface:
  [`ha-canonical-gcd-lcm-rfc-v1.md`](ha-canonical-gcd-lcm-rfc-v1.md)
- campaign plan:
  [`PLAN/12_ha_number_theory_campaign.md`](../../PLAN/12_ha_number_theory_campaign.md)
