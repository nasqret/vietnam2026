# Constructive noncoprime finite CRT compatibility, v1

## Exact proved boundary

The 24 dependency-ordered candidates in
`peano-lab/py/peano_lab/library/generalized_crt_compatibility_candidate.py`
are actual first-order proofs checked by the unchanged intuitionistic kernel.
They establish:

1. Every simultaneous solution implies exact pairwise residue compatibility
   modulo the relational gcd of its decoded moduli, including zero moduli.
2. Every arbitrary-length beta-coded list satisfying its exact predecessor-LCM
   merge compatibility invariant has an actual simultaneous solution. This
   ordinary-induction constructor allows repeated, noncoprime, and zero moduli.
3. For positive merge-compatible lists there exist the genuine universal-
   property list LCM and exactly one simultaneous solution strictly below it.
4. If the list LCM is zero, simultaneous solutions are literally unique.
5. Exact merge compatibility implies pairwise gcd compatibility; the opposite
   implication is neither postulated nor hidden in an authoring definition.
6. If the last modulus is an actual common multiple of all previous moduli,
   pairwise compatibility alone makes its last residue a simultaneous solution,
   including zero moduli. Positive such lists have a unique bounded canonical
   solution and their actual list LCM, without a coprimality hypothesis.
7. A genuine subtraction-free gcd lattice substrate proves unconditional gcd
   scaling, coprime-factor removal, gcd of coprime products, gcd/LCM cofactor
   factorization, gcd monotonicity, and gcd/LCM distributivity whenever one
   modulus divides the other.

These are not host-computed examples, trusted new primitives, supplied list
solutions, or binary facts rebranded as list theorems.

Campaign goal **G011 remains open**. Its full target requires arbitrary
positive pairwise-gcd-compatible noncoprime modulus lists. The missing bridge
is the constructive implication

```text
CRTPairwiseCompatiblePrefix => CRTMergeCompatiblePrefix
```

for unrestricted lists, or a suitable proof of the unrestricted lattice law

```text
gcd(lcm(a,b), n) = lcm(gcd(a,n), gcd(b,n)).
```

The present `crt_gcd_lcm_distributes_divisibility` explicitly assumes that one
input divides the other. For instance, moduli `(6,10,15)` with residues
`(1,7,7)` are pairwise gcd-compatible but do not meet the dominating-last
condition. They cannot be cited as evidence that G011 is closed.

## Conservative definition DAG

Exactly two new hygienic reviewed concepts are introduced. Both are expanded
first-order formulas over the unchanged `0,S,+,*,=` language; binder tags are
alpha-invariant, arguments are distinct, and capture/injection are rejected.

| Concept | Parameters | Exact content | Reviewed dependencies |
| --- | --- | --- | --- |
| `CRTPairwiseCompatiblePrefix` | `(r,s,b,c,l)` | Every two actual decoded residue/modulus pairs below `l` are congruent modulo their exact relational gcd. | `Beta`, `Lt`, `IsGCD`, `ModEq` |
| `CRTMergeCompatiblePrefix` | `(r,s,b,c,l)` | At every index below `l`, every actual predecessor-prefix solution is congruent to the next decoded residue modulo the gcd of its exact predecessor-list LCM and actual next modulus. | `Beta`, `Lt`, `CRTPrefixLCM`, `CRTPrefixSolution`, `IsGCD`, `ModEq` |

Previously reviewed `CRTPositiveModuliPrefix`, `CRTPrefixSolution`,
`CRTPrefixLCM`, and `CRTCanonicalPrefixSolution` are reused exactly. In
particular, pairwise compatibility is never strengthened by silently
substituting the operational merge invariant.

## Ordered unchanged-kernel ladder

```text
crt_mod_one_universal
crt_coprime_divisor_pair
crt_pairwise_compatible_prefix_empty
crt_pairwise_compatible_prefix_drop_last
crt_prefix_solution_implies_pairwise_compatible
crt_pairwise_compatible_prefix_last
crt_merge_compatible_prefix_drop_last
generalized_binary_crt_merge_step
crt_merge_compatible_prefix_solution_exists
crt_positive_prefix_lcm_nonzero
crt_prefix_zero_lcm_solution_unique
crt_merge_compatible_prefix_canonical_exists_unique
crt_balanced_bezout_scale
crt_is_gcd_scale
crt_is_gcd_coprime_factor_remove
crt_product_witness
crt_is_gcd_coprime_product
crt_lcm_gcd_cofactor_product
crt_gcd_scaled_coprime_component
crt_gcd_monotone_under_divisibility
crt_gcd_lcm_distributes_divisibility
crt_merge_compatible_prefix_implies_pairwise_compatible
crt_pairwise_compatible_dominating_last_solution
crt_pairwise_compatible_dominating_last_canonical_exists_unique
```

The exact tranche contains **24 candidate theorems**, **90 direct dependency
edges**, **1,097 original tactic commands**, and **1,718 independent body
proof nodes**; its maximum body has 155 nodes and maximum depth is 48. The
newline-joined ordered-name SHA-256 is
`221fc9b2ca61c816f10bd6f8a1db48b053ff8676b8babece9d02a29dda9c5758`.

Principal exact statement hashes:

| Theorem | SHA-256 |
| --- | --- |
| `crt_merge_compatible_prefix_solution_exists` | `1e30822d43996807abe877aa76d88026a59c293dfe440ed00461e6a4eb17acc9` |
| `crt_prefix_zero_lcm_solution_unique` | `51282f3aa0c88577dd418755a7353937f00de77d97096e749e46b89390d9c4b9` |
| `crt_merge_compatible_prefix_canonical_exists_unique` | `9e3d68192e707b5953b2fd3c9e4716e9fe90317f63be49734bbed00e3492b927` |
| `crt_is_gcd_scale` | `abe947735d13b946283776bfb832f7f0e8dc17861fbd0850c5b7b51827d68f77` |
| `crt_is_gcd_coprime_product` | `e3b28cbcdf65cdad1e51c834812bf2efb8a45cb534bb8a5daa1e4245b4d0a347` |
| `crt_gcd_lcm_distributes_divisibility` | `0ac6861e424c4c961810fe6565850227601a3c79438256678a50f8df25a544dd` |
| `crt_pairwise_compatible_dominating_last_solution` | `97517c25a69447aa29949b2fc108933aea824e514eda2880c492c704094f5679` |
| `crt_pairwise_compatible_dominating_last_canonical_exists_unique` | `f249f7835eb127e8d5f15e74b3d4344d5d98503d8b01394d608bf2e677823fb0` |

The executable focused audit is
`peano-lab/py/tests/test_generalized_crt_compatibility_candidate.py`. It
validates original-kernel bodies, exact ordered graph and receipt seals,
definition hygiene, forged conclusions, truncated proofs, removed
dependencies, positive/noncoprime/zero-modulus examples, actual gcd lattice
identities, and the explicit remaining G011 boundary. Host calculations are
illustrative only; the immutable original-kernel proof bodies are the sole
mathematical evidence.
