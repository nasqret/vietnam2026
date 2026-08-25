# Complete constructive Alpha-v18 residual closure

The canonical artifact
`research/arithmetic-library/artifacts/alpha-v19-residual-proof-bundle-v1.json`
contains complete, ordinary, independently kernel-checked proof data for every
one of the **84** theorems that remained `body_checked` in immutable Alpha v18.
It is evidence for a separately authorized subsequent admission; constructing
the artifact alone never changes Alpha v18, Stable, theorem membership, the
intuitionistic kernel, or the proof grammar.

| Quantity | Exact value |
|---|---:|
| Alpha-v18 theorem count | 1,673 |
| Alpha-v18 checked-use count | 1,589 |
| Alpha-v18 residual body-only count | 84 |
| K3C cell/list interface rows | 17 |
| Auxiliary Bertrand arithmetic rows | 67 |
| Joint transitive enrolled theorem rows | 474 |
| Stable parent rows in that closure | 189 |
| Already checked Alpha parent rows in that closure | 201 |
| Exact real dependency edges | 1,412 |
| Maximal residual endpoints | 40 |
| Synthetic balanced-conjunction nodes | 1 |
| Complete canonical proof-bundle nodes | 475 |
| Complete canonical proof-bundle edges | 1,452 |
| Independently checked ordinary body-proof nodes | 38,688 |
| Independently checked original-kernel calls | 475 |
| Exact canonical payload bytes | 4,176,537 |

The frozen Alpha-v18 parent identity is
`f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66`.
Its immutable ordered-enrollment root is
`44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175`.
The exact ordered 84-row evidence frontier hashes to
`0fd3159925c12b2e7249edb5d536f3be600e466e5a6695350a22c38e81d4f69e`.
The complete ordered 474-row theorem surface hashes to
`410ae78fa82fc7a4fc6e2653dbe7cd9668b26cafc1d43ab20b4ba93a3686ca69`;
its full identity, including enrollment indices, statement digests,
dependencies, original evidence, origins, and actual body sources, hashes to
`343566c94dbb8e3c8aaab71655981b03bb59df87aeb737f1708a548e3464e9d5`.

The canonical artifact SHA-256 is
`e69112c5e3b8c21bc452ad35838474f2af2e297152ff73fbdc62bfd935ffdebb`.
Hashes are provenance and mutation diagnostics only: reading the artifact
rechecks every complete dependency-curried proof body using the existing
original intuitionistic kernel.

## Exact proof-body provenance

The complete, independently checked Bertrand artifact supplies **361** ordinary
proof bodies. Its frozen SHA-256 is
`84078d40d2df7b072938975191fb70c95731059ced716a12050df4376e2d4883`.
The independently checked quadratic-reciprocity artifact supplies the two
remaining available parent bodies, `pow_mul_exp` and `beta_repeat_sum_exact`;
its frozen SHA-256 is
`3cd040d145f1004d07d277c66a3ffbcb355cd9c4b21938d79a6ec51b4258709c`.

The remaining **111** ordinary proof bodies are freshly reconstructed from the
exact immutable Alpha-v18 theorem specifications. They comprise all **84**
previously body-only rows and **27** previously checked cell/list parent rows
whose exact curried bodies are absent from the existing flagship artifacts.
Their ordered name digest is
`d6cc4d0df58e4adce37a1e318cf48cc0aa642526955516c485d895d12c576e17`.

Construction proceeds through **14** proof microbatches, each containing at
most **8** bodies and respecting the unchanged hard ceilings of **16** bodies,
**125,000** structural proof nodes, **25,000** proof objects, and **256**
combined proof-envelope depth. Pending rows occupy the eight exact
dependency-ready waves `50, 19, 6, 4, 2, 1, 1, 1`.

### Frozen proof-only power-seven normalization

The immutable enrolled script of `pow_two_seven_exact` contains **243** tactic
commands. Its original proof checks, but two arithmetic blocks rewriting
`32 * 2` and `64 * 2` using PA3--PA6 exceed the unchanged canonical
proof-bundle depth limit. The constructive evidence generator replaces only
the two exact frozen command intervals `(31, 101)` and `(108, 242)` with the
existing independently kernel-checked `norm_num` tactic. Its authoring-only
term-inspection limit accommodates the already-enrolled unary numeral 128;
the resulting actual proof has **1,557** structural nodes, **1,557** proof
objects, proof depth **142**, and combined envelope depth **203**.

The original enrolled statement, exact dependency list, original 243-command
ledger script, all kernel rules, proof constructors, codec limits, 256-depth
envelope limit, and release identities remain unchanged. No axiom, classical
principle, oracle, unchecked reference, trusted digest, or implicit theorem
authority is added.

## Maximal exact residual theorem endpoints

The forty endpoints are:

1. `cell_list_valid_nil`
2. `cell_list_valid_cell_intro`
3. `cell_list_valid_cell_elim`
4. `list_member_implies_cell_list_valid`
5. `list_member_nil_false`
6. `list_member_cell_iff`
7. `list_member_pointwise_transport`
8. `list_at_exists_unique`
9. `cell_list_nonempty_iff_head_exists`
10. `cell_list_code_eq_iff_pointwise`
11. `cell_list_decompose_unique`
12. `bounded_prime_interval_decidable`
13. `prime_power_valuation_exists`
14. `prime_power_valuation_functional`
15. `bertrand_guard_six_step_transport`
16. `ceil_div_six_exists_unique`
17. `floor_sqrt_exists_unique`
18. `factorial_valuation_functional`
19. `prime_factorial_valuation_succ_invert`
20. `floor_sqrt_threshold_sixty_four`
21. `bertrand_guard_base_residue`
22. `bertrand_hj_base_window_from_total`
23. `central_binom_functional`
24. `primorial_prime_divides_iff_le`
25. `primorial_le_monotone`
26. `primorial_interval_exists`
27. `primorial_interval_functional`
28. `beta_distinct_empty`
29. `beta_distinct_succ_intro`
30. `beta_distinct_transport`
31. `beta_distinct_bounded_prime_product_le_primorial`
32. `beta_sum_uniform_le_mul`
33. `division_double_quotient_lower`
34. `central_binom_prime_valuation_le_double`
35. `prime_contribution_product_functional`
36. `no_bertrand_central_contribution_prefix_ranges`
37. `prime_contribution_interval_exists`
38. `prime_contribution_interval_functional`
39. `prime_contribution_three_range_split`
40. `add_remainder_lift`

The synthetic artifact root is a balanced conjunction of these exact forty
already proved statements. Its proof uses only ordinary `ImpIntro`, `Hyp`,
and `AndIntro`; it is not an enrolled theorem and grants no additional
logical principle. Every other residual theorem belongs to the transitive
closure of at least one listed exact endpoint.

## Independent original-kernel and Lean verification

The existing Python proof-bundle verifier independently accepted all **475**
ordinary dependency-curried bodies from the empty context. The existing,
separately compiled Lean verifier independently accepted the same unchanged
canonical artifact:

```text
ACCEPT  research/arithmetic-library/artifacts/alpha-v19-residual-proof-bundle-v1.json  nodes=475  root=474
```

The resulting API is
`peano_lab.library.campaign_residual_closure.residual_closure_plan()`,
`checked_residual_proof_bundle()`, `check_residual_proof_bundle(...)`, and
`replay_residual_closed_theorem(name)`. Ordinary exact-root replay compiles
only the requested transitive subgraph under the unchanged layered-proof
limits and asks the unchanged intuitionistic kernel to check the resulting
empty-context proof. Alpha v18 still rejects checked use of these rows until
an independently sealed subsequent release explicitly admits them.
