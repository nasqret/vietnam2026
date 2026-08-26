# Constructive finite-list Chinese remainder fold, v1

## Exact result and honest boundary

The 27 isolated, dependency-ordered candidates in
`peano-lab/py/peano_lab/library/generalized_crt_fold_candidate.py` prove:

1. Every arbitrary beta-coded finite list of natural moduli has a unique
   universal-property list lcm, including repeated, noncoprime, and zero
   entries; the empty-list lcm is one.
2. Two existing simultaneous solutions of *any* finite list belong to exactly
   the same congruence class modulo that list lcm.
3. For a nonzero list lcm, every existing solution has a unique representative
   strictly below the lcm.
4. Every arbitrary finite list of **positive pairwise-coprime** moduli and
   arbitrary actually decoded residues has its genuine lcm and a unique
   bounded simultaneous solution.

This is a real ordinary-induction fold, not a host-language enumeration, a
supplied simultaneous solution, or the special family of beta coding moduli.
It uses the existing checked binary CRT on the accumulated finite product,
proves that product coprime to each next decoded modulus, preserves every
previous congruence, and proves that the product is the exact universal-property
list lcm.

Campaign goal **G011 remains open**. Its hypothesis permits pairwise
gcd-compatible **noncoprime** positive moduli. Closing that stronger target
requires an additional constructive theorem transporting all pairwise
compatibilities to compatibility with the gcd of the next modulus and the
accumulated list lcm. Equivalently, one must prove the relevant constructive
finite gcd/lcm distributivity bridge. The present candidate neither assumes
nor silently renames that missing theorem. For example, the compatible system
with moduli `(6,10,15)` and residues `(1,7,7)` lies outside the proved
pairwise-coprime constructor.

## Five conservative hygienic relations

Each authoring relation returns an expanded first-order formula over exactly
`0, S, +, *, =`. Binder tags are alpha-invariant, untrusted fragments and
generated-binder capture are rejected, and no parser or kernel primitive is
introduced.

| Concept | Parameters | Actual mathematical expansion | Prerequisites |
| --- | --- | --- | --- |
| `CRTPositiveModuliPrefix` | `(b,c,l)` | Every decoded modulus at `i<l` is nonzero. | `Beta`, `Lt` |
| `CRTPairwiseCoprimePrefix` | `(b,c,l)` | Decoded moduli at distinct indices below `l` are coprime. | `Beta`, `Lt`, `Coprime` |
| `CRTPrefixSolution` | `(r,s,b,c,l,x)` | Every actual decoded pair `(a,m)` satisfies `x ≡ a (mod m)`. | `Beta`, `Lt`, `ModEq` |
| `CRTPrefixLCM` | `(b,c,l,M)` | Every listed modulus divides `M`, and `M` divides every common multiple. | `Beta`, `Lt`, `Dvd` |
| `CRTCanonicalPrefixSolution` | `(r,s,b,c,l,x,M)` | `CRTPrefixLCM(b,c,l,M)`, `x<M`, and `CRTPrefixSolution(r,s,b,c,l,x)`. | `CRTPrefixLCM`, `Lt`, `CRTPrefixSolution` |

The pairwise relation deliberately reuses the exact already-checked formula
of `beta_pairwise_coprime_product_divides_common_multiple`; it does not
substitute an unequivalent convenient notion of coprimality.

## Ordered original-kernel ladder

```text
crt_positive_moduli_prefix_empty
crt_positive_moduli_prefix_drop_last
crt_positive_moduli_prefix_last_nonzero
crt_pairwise_coprime_prefix_drop_last
crt_prefix_solution_empty
crt_prefix_solution_drop_last
crt_prefix_solution_last
crt_prefix_solution_successor_intro
crt_pairwise_coprime_prefix_last
crt_positive_moduli_prefix_product_nonzero
crt_prefix_product_common_multiple
crt_pairwise_coprime_prefix_product_is_lcm
crt_prefix_lcm_unique
crt_prefix_lcm_empty
crt_prefix_lcm_successor_intro
crt_prefix_lcm_exists_unique
crt_pairwise_coprime_prefix_lcm_exists_unique
crt_pairwise_coprime_prefix_product_coprime_last
crt_pairwise_coprime_prefix_solution_exists
crt_prefix_solutions_pointwise_congruent
crt_prefix_solution_transport_common_multiple
crt_prefix_ordered_solutions_gap_multiple
crt_prefix_solutions_congruent_lcm
crt_prefix_solution_class_iff_lcm
crt_prefix_solution_canonical_remainder
crt_canonical_prefix_solution_unique
crt_pairwise_coprime_prefix_canonical_exists_unique
```

The ordered newline-joined theorem-name digest is
`1d18c793f8521e3b08ec2ea1c2e8e5d9e4e824c58b5366a00415316af6f6b240`.
The tranche has exactly **27 theorem bodies**, **83 ordered direct dependency
edges**, **1,106 original tactic commands**, and **1,860 independently
kernel-checked body proof nodes**. The largest body has 169 nodes; the maximum
body proof depth is 55. There are no axioms, admitted gaps, `DNE` nodes,
classical decisions, new proof rules, or host-calculation evidence.

Principal immutable statement digests:

| Theorem | SHA-256 |
| --- | --- |
| `crt_prefix_lcm_exists_unique` | `09fa610c42ac069677f4fb90f00c6e0780d2b1de843380599e725a9cf19e1175` |
| `crt_pairwise_coprime_prefix_solution_exists` | `6e61d9a848010dc5857fdacbc8efc3973e160a997a421a17100a867e1c501e68` |
| `crt_prefix_solutions_congruent_lcm` | `0a5243850c7ffde41b00fb3680cf48610aa2f9e285e33f40e19c59c282814fea` |
| `crt_prefix_solution_class_iff_lcm` | `a943495e7c8817cf917f4cc282502ad316a2a3ce9892c5d6bb3ba2ab0fbd6488` |
| `crt_canonical_prefix_solution_unique` | `3631285d003a8cedeb954757d88ea8043cc2f79acb657e582b27018a0f0f003c` |
| `crt_pairwise_coprime_prefix_canonical_exists_unique` | `6d3913cdbd73b6a2662e31aea220a19ab75f0d1995e3fadf0c583c58d270e01f` |

The focused executable audit is
`peano-lab/py/tests/test_generalized_crt_fold_candidate.py`. It checks all
unchanged-kernel bodies, exact dependency ordering and receipt metrics,
conservative definition hygiene, exact compatibility with the existing
pairwise relation, forged conclusions, truncated proof bodies, removed
dependencies, actual canonical examples, arbitrary noncoprime/zero-modulus lcm
examples, and the explicit still-open G011 boundary. Host examples are
demonstrations only; the kernel-checked original tactic bodies are the
mathematical authority.
